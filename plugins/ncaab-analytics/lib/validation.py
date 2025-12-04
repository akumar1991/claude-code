"""
Validation Module

Implements rigorous validation techniques for NCAAB predictions:
- Walk-Forward Validation: Time series cross-validation preventing lookahead
- Probabilistic Forecasting: Quantile regression for probability distributions
- Hierarchical Validation: Accounting for dependent observations
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Callable
import math
import random
from collections import defaultdict

from .modeling import BaseModel, Prediction, StackingEnsemble


# ============================================================================
# Walk-Forward (Time Series) Validation
# ============================================================================


@dataclass
class ValidationFold:
    """Results from a single validation fold."""

    train_start: date
    train_end: date
    test_start: date
    test_end: date
    n_train: int
    n_test: int
    predictions: list[float]
    actuals: list[float]
    game_ids: list[str]

    # Metrics
    mae: float = 0.0  # Mean Absolute Error
    rmse: float = 0.0  # Root Mean Squared Error
    mape: float = 0.0  # Mean Absolute Percentage Error
    coverage: float = 0.0  # % of actuals within confidence interval


@dataclass
class ValidationResult:
    """Complete validation results."""

    folds: list[ValidationFold]
    overall_mae: float
    overall_rmse: float
    overall_coverage: float
    by_month: dict[str, dict[str, float]] = field(default_factory=dict)
    by_conference: dict[str, dict[str, float]] = field(default_factory=dict)


class WalkForwardValidator:
    """
    Time series cross-validation that prevents looking into the future.

    Instead of random shuffling, this validates on temporal splits:
    - Train on Nov-Jan, test on Feb
    - Train on Nov-Feb, test on March
    - Etc.

    This simulates real-world forecasting conditions.
    """

    def __init__(
        self,
        min_train_days: int = 60,
        test_window_days: int = 14,
        step_days: int = 7,
    ):
        """
        Initialize walk-forward validator.

        Args:
            min_train_days: Minimum training period before first test
            test_window_days: Size of each test window
            step_days: How far to advance between folds
        """
        self.min_train_days = min_train_days
        self.test_window_days = test_window_days
        self.step_days = step_days

    def _calculate_metrics(
        self,
        predictions: list[float],
        actuals: list[float],
        intervals: list[tuple[float, float]] | None = None,
    ) -> dict[str, float]:
        """Calculate validation metrics."""
        n = len(predictions)
        if n == 0:
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0, "coverage": 0.0}

        # MAE
        mae = sum(abs(p - a) for p, a in zip(predictions, actuals)) / n

        # RMSE
        mse = sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / n
        rmse = math.sqrt(mse)

        # MAPE (avoiding division by zero)
        mape_sum = 0.0
        mape_count = 0
        for p, a in zip(predictions, actuals):
            if abs(a) > 0.1:  # Avoid near-zero actuals
                mape_sum += abs((p - a) / a)
                mape_count += 1
        mape = (mape_sum / mape_count * 100) if mape_count > 0 else 0.0

        # Coverage (if intervals provided)
        coverage = 0.0
        if intervals:
            in_interval = sum(
                1 for (lo, hi), a in zip(intervals, actuals)
                if lo <= a <= hi
            )
            coverage = in_interval / n * 100

        return {
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "coverage": coverage,
        }

    def create_folds(
        self,
        data: list[dict[str, Any]],
        date_key: str = "_game_date",
    ) -> list[tuple[list[dict], list[dict]]]:
        """
        Create walk-forward validation folds.

        Args:
            data: List of feature dictionaries with dates
            date_key: Key containing the game date

        Returns:
            List of (train_data, test_data) tuples
        """
        # Sort by date
        sorted_data = sorted(
            data,
            key=lambda x: x.get(date_key, ""),
        )

        if not sorted_data:
            return []

        # Parse dates
        def parse_date(d: dict) -> date:
            date_str = d.get(date_key, "")
            if isinstance(date_str, date):
                return date_str
            return date.fromisoformat(date_str)

        first_date = parse_date(sorted_data[0])
        last_date = parse_date(sorted_data[-1])

        folds = []
        current_test_start = first_date + timedelta(days=self.min_train_days)

        while current_test_start + timedelta(days=self.test_window_days) <= last_date:
            test_end = current_test_start + timedelta(days=self.test_window_days)

            # Split data
            train_data = [
                d for d in sorted_data
                if parse_date(d) < current_test_start
            ]
            test_data = [
                d for d in sorted_data
                if current_test_start <= parse_date(d) < test_end
            ]

            if train_data and test_data:
                folds.append((train_data, test_data))

            current_test_start += timedelta(days=self.step_days)

        return folds

    def validate(
        self,
        model: BaseModel | StackingEnsemble,
        data: list[dict[str, Any]],
        target_key: str = "target_spread",
        date_key: str = "_game_date",
        game_id_key: str = "_game_id",
    ) -> ValidationResult:
        """
        Perform walk-forward validation.

        Args:
            model: Model to validate
            data: Complete dataset with features and targets
            target_key: Key for target variable
            date_key: Key for game date
            game_id_key: Key for game identifier

        Returns:
            ValidationResult with metrics for each fold
        """
        folds = self.create_folds(data, date_key)
        fold_results = []

        all_predictions = []
        all_actuals = []
        all_intervals = []

        for train_data, test_data in folds:
            # Prepare training data
            train_X = [
                {k: v for k, v in d.items()
                 if not k.startswith("_") and not k.startswith("target_")}
                for d in train_data
            ]
            train_y = [d.get(target_key, 0.0) for d in train_data]

            # Prepare test data
            test_X = [
                {k: v for k, v in d.items()
                 if not k.startswith("_") and not k.startswith("target_")}
                for d in test_data
            ]
            test_y = [d.get(target_key, 0.0) for d in test_data]
            game_ids = [d.get(game_id_key, "") for d in test_data]

            # Train and predict
            if isinstance(model, StackingEnsemble):
                model.fit(train_X, train_y)
            else:
                model.fit(train_X, train_y)

            predictions = model.predict(test_X)

            # Extract predictions and intervals
            pred_values = [p.point_estimate for p in predictions]
            intervals = [(p.lower_bound, p.upper_bound) for p in predictions]

            # Calculate metrics
            metrics = self._calculate_metrics(pred_values, test_y, intervals)

            # Parse dates for fold info
            def parse_date(d: dict) -> date:
                date_str = d.get(date_key, "")
                if isinstance(date_str, date):
                    return date_str
                return date.fromisoformat(date_str)

            train_dates = [parse_date(d) for d in train_data]
            test_dates = [parse_date(d) for d in test_data]

            fold_result = ValidationFold(
                train_start=min(train_dates),
                train_end=max(train_dates),
                test_start=min(test_dates),
                test_end=max(test_dates),
                n_train=len(train_data),
                n_test=len(test_data),
                predictions=pred_values,
                actuals=test_y,
                game_ids=game_ids,
                mae=metrics["mae"],
                rmse=metrics["rmse"],
                mape=metrics["mape"],
                coverage=metrics["coverage"],
            )
            fold_results.append(fold_result)

            # Accumulate for overall metrics
            all_predictions.extend(pred_values)
            all_actuals.extend(test_y)
            all_intervals.extend(intervals)

        # Calculate overall metrics
        overall = self._calculate_metrics(all_predictions, all_actuals, all_intervals)

        return ValidationResult(
            folds=fold_results,
            overall_mae=overall["mae"],
            overall_rmse=overall["rmse"],
            overall_coverage=overall["coverage"],
        )

    def generate_report(self, result: ValidationResult) -> str:
        """Generate a human-readable validation report."""
        lines = []
        lines.append("=" * 60)
        lines.append("WALK-FORWARD VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append("")
        lines.append("OVERALL METRICS:")
        lines.append(f"  MAE:      {result.overall_mae:.3f}")
        lines.append(f"  RMSE:     {result.overall_rmse:.3f}")
        lines.append(f"  Coverage: {result.overall_coverage:.1f}%")
        lines.append("")
        lines.append("FOLD DETAILS:")
        lines.append("-" * 60)

        for i, fold in enumerate(result.folds, 1):
            lines.append(f"Fold {i}:")
            lines.append(f"  Train: {fold.train_start} to {fold.train_end} ({fold.n_train} games)")
            lines.append(f"  Test:  {fold.test_start} to {fold.test_end} ({fold.n_test} games)")
            lines.append(f"  MAE: {fold.mae:.3f}, RMSE: {fold.rmse:.3f}, Coverage: {fold.coverage:.1f}%")
            lines.append("")

        return "\n".join(lines)


# ============================================================================
# Probabilistic Forecasting
# ============================================================================


@dataclass
class QuantilePrediction:
    """Prediction with multiple quantiles for full distribution."""

    median: float
    quantiles: dict[float, float]  # quantile level -> value
    mean: float | None = None
    std_dev: float | None = None

    def get_interval(self, level: float = 0.90) -> tuple[float, float]:
        """Get prediction interval at specified level."""
        lower_q = (1 - level) / 2
        upper_q = 1 - lower_q
        return (
            self.quantiles.get(lower_q, self.median - 10),
            self.quantiles.get(upper_q, self.median + 10),
        )

    def prob_over(self, threshold: float) -> float:
        """Estimate probability of exceeding threshold."""
        # Simple interpolation between quantiles
        sorted_qs = sorted(self.quantiles.items())
        for i, (q, val) in enumerate(sorted_qs):
            if val >= threshold:
                if i == 0:
                    return 1.0 - q
                prev_q, prev_val = sorted_qs[i - 1]
                # Linear interpolation
                if val == prev_val:
                    return 1.0 - q
                frac = (threshold - prev_val) / (val - prev_val)
                interp_q = prev_q + frac * (q - prev_q)
                return 1.0 - interp_q
        return 0.0

    def prob_under(self, threshold: float) -> float:
        """Estimate probability of being under threshold."""
        return 1.0 - self.prob_over(threshold)


class ProbabilisticForecaster:
    """
    Outputs probability distributions instead of point predictions.

    Uses quantile regression to estimate the full conditional distribution,
    allowing statements like "90% chance this player scores between 15-25 points."
    """

    def __init__(
        self,
        quantiles: list[float] | None = None,
        base_model_factory: Callable[[], BaseModel] | None = None,
    ):
        """
        Initialize probabilistic forecaster.

        Args:
            quantiles: Quantile levels to estimate (default: deciles)
            base_model_factory: Factory for creating quantile models
        """
        self.quantiles = quantiles or [0.1, 0.25, 0.5, 0.75, 0.9]
        self._quantile_models: dict[float, BaseModel] = {}
        self._factory = base_model_factory

    def _pinball_loss(
        self,
        y_true: float,
        y_pred: float,
        quantile: float,
    ) -> float:
        """Calculate pinball (quantile) loss."""
        error = y_true - y_pred
        if error >= 0:
            return quantile * error
        else:
            return (quantile - 1) * error

    def fit(
        self,
        X: list[dict[str, float]],
        y: list[float],
    ) -> None:
        """
        Fit quantile regression models for each quantile level.

        This is a simplified implementation that adjusts predictions
        based on residual distributions. Production would use proper
        quantile regression (e.g., LightGBM with quantile objective).
        """
        from .modeling import GlobalForecastingModel

        # Fit a base model first
        base_model = GlobalForecastingModel(n_estimators=50, max_depth=4)
        base_model.fit(X, y)

        # Get residuals
        base_preds = base_model.predict(X)
        residuals = [yi - p.point_estimate for yi, p in zip(y, base_preds)]

        # Calculate empirical quantiles of residuals
        sorted_residuals = sorted(residuals)
        n = len(sorted_residuals)

        self._residual_quantiles: dict[float, float] = {}
        for q in self.quantiles:
            idx = int(q * n)
            idx = min(idx, n - 1)
            self._residual_quantiles[q] = sorted_residuals[idx]

        self._base_model = base_model

    def predict(self, X: list[dict[str, float]]) -> list[QuantilePrediction]:
        """
        Generate probabilistic predictions.

        Args:
            X: Feature dictionaries

        Returns:
            List of QuantilePrediction objects with full distributions
        """
        base_preds = self._base_model.predict(X)
        predictions = []

        for base_pred in base_preds:
            point = base_pred.point_estimate

            # Compute quantiles by adjusting base prediction
            quantiles = {}
            for q in self.quantiles:
                adjustment = self._residual_quantiles.get(q, 0.0)
                quantiles[q] = point + adjustment

            predictions.append(
                QuantilePrediction(
                    median=quantiles.get(0.5, point),
                    quantiles=quantiles,
                    mean=point,
                    std_dev=base_pred.std_dev,
                )
            )

        return predictions

    def predict_with_threshold(
        self,
        X: list[dict[str, float]],
        threshold: float,
        direction: str = "over",
    ) -> list[dict[str, Any]]:
        """
        Predict probability of exceeding/falling under a threshold.

        Useful for betting line analysis.

        Args:
            X: Feature dictionaries
            threshold: Line to evaluate against
            direction: "over" or "under"

        Returns:
            List of dicts with prediction and probability
        """
        predictions = self.predict(X)
        results = []

        for pred in predictions:
            if direction == "over":
                prob = pred.prob_over(threshold)
            else:
                prob = pred.prob_under(threshold)

            results.append({
                "threshold": threshold,
                "direction": direction,
                "probability": prob,
                "median": pred.median,
                "interval_90": pred.get_interval(0.90),
                "edge": prob - 0.5,  # Distance from coin flip
            })

        return results


# ============================================================================
# Hierarchical Validation
# ============================================================================


class HierarchicalValidator:
    """
    Accounts for dependent data points when validating.

    Avoids pseudoreplication by recognizing that multiple props from
    the same game are not independent samples. Uses clustered standard
    errors and hierarchical model adjustments.
    """

    def __init__(self, cluster_key: str = "_game_id"):
        """
        Initialize hierarchical validator.

        Args:
            cluster_key: Key identifying the cluster (e.g., game_id)
        """
        self.cluster_key = cluster_key

    def calculate_clustered_se(
        self,
        predictions: list[float],
        actuals: list[float],
        clusters: list[str],
    ) -> dict[str, float]:
        """
        Calculate standard errors with cluster adjustment.

        Args:
            predictions: Model predictions
            actuals: Actual values
            clusters: Cluster identifiers for each observation

        Returns:
            Dictionary with naive and clustered standard errors
        """
        n = len(predictions)
        if n == 0:
            return {"naive_se": 0.0, "clustered_se": 0.0, "deff": 1.0}

        # Calculate residuals
        residuals = [p - a for p, a in zip(predictions, actuals)]

        # Naive SE (treating all as independent)
        mean_res = sum(residuals) / n
        naive_var = sum((r - mean_res) ** 2 for r in residuals) / (n - 1)
        naive_se = math.sqrt(naive_var / n)

        # Cluster residuals
        cluster_residuals: dict[str, list[float]] = defaultdict(list)
        for res, cluster in zip(residuals, clusters):
            cluster_residuals[cluster].append(res)

        # Calculate cluster means
        cluster_means = {
            c: sum(rs) / len(rs)
            for c, rs in cluster_residuals.items()
        }

        # Between-cluster variance
        n_clusters = len(cluster_means)
        if n_clusters < 2:
            return {"naive_se": naive_se, "clustered_se": naive_se, "deff": 1.0}

        grand_mean = sum(cluster_means.values()) / n_clusters
        between_var = sum(
            (m - grand_mean) ** 2 for m in cluster_means.values()
        ) / (n_clusters - 1)

        # Design effect (simplified)
        avg_cluster_size = n / n_clusters
        icc = between_var / (naive_var + 0.0001)  # Intraclass correlation
        deff = 1 + (avg_cluster_size - 1) * icc  # Design effect

        # Clustered SE
        clustered_se = naive_se * math.sqrt(deff)

        return {
            "naive_se": naive_se,
            "clustered_se": clustered_se,
            "deff": deff,
            "n_clusters": n_clusters,
            "avg_cluster_size": avg_cluster_size,
            "icc": icc,
        }

    def validate_with_clustering(
        self,
        model: BaseModel,
        data: list[dict[str, Any]],
        target_key: str = "target_spread",
    ) -> dict[str, Any]:
        """
        Validate model with cluster-adjusted standard errors.

        Args:
            model: Trained model
            data: Data with cluster identifiers
            target_key: Target variable key

        Returns:
            Validation results with cluster adjustments
        """
        # Prepare data
        X = [
            {k: v for k, v in d.items()
             if not k.startswith("_") and not k.startswith("target_")}
            for d in data
        ]
        y = [d.get(target_key, 0.0) for d in data]
        clusters = [d.get(self.cluster_key, str(i)) for i, d in enumerate(data)]

        # Get predictions
        predictions = model.predict(X)
        pred_values = [p.point_estimate for p in predictions]

        # Calculate metrics
        n = len(pred_values)
        mae = sum(abs(p - a) for p, a in zip(pred_values, y)) / n
        mse = sum((p - a) ** 2 for p, a in zip(pred_values, y)) / n
        rmse = math.sqrt(mse)

        # Get clustered SE
        se_results = self.calculate_clustered_se(pred_values, y, clusters)

        return {
            "n_observations": n,
            "mae": mae,
            "rmse": rmse,
            **se_results,
            "warning": (
                "Clustered SE is significantly larger than naive SE"
                if se_results["deff"] > 1.5 else None
            ),
        }

    def block_bootstrap_ci(
        self,
        model: BaseModel,
        data: list[dict[str, Any]],
        target_key: str = "target_spread",
        n_bootstrap: int = 100,
        ci_level: float = 0.95,
    ) -> dict[str, Any]:
        """
        Calculate confidence intervals using block bootstrap.

        Resamples entire clusters (games) rather than individual observations.

        Args:
            model: Trained model
            data: Data with cluster identifiers
            target_key: Target variable key
            n_bootstrap: Number of bootstrap iterations
            ci_level: Confidence level

        Returns:
            Bootstrap confidence intervals
        """
        # Group by cluster
        cluster_data: dict[str, list[dict]] = defaultdict(list)
        for d in data:
            cluster = d.get(self.cluster_key, "default")
            cluster_data[cluster].append(d)

        cluster_ids = list(cluster_data.keys())
        n_clusters = len(cluster_ids)

        bootstrap_maes = []

        for _ in range(n_bootstrap):
            # Sample clusters with replacement
            sampled_clusters = random.choices(cluster_ids, k=n_clusters)

            # Build bootstrap sample
            bootstrap_data = []
            for cluster_id in sampled_clusters:
                bootstrap_data.extend(cluster_data[cluster_id])

            if not bootstrap_data:
                continue

            # Prepare data
            X = [
                {k: v for k, v in d.items()
                 if not k.startswith("_") and not k.startswith("target_")}
                for d in bootstrap_data
            ]
            y = [d.get(target_key, 0.0) for d in bootstrap_data]

            # Get predictions (using already-trained model)
            predictions = model.predict(X)
            pred_values = [p.point_estimate for p in predictions]

            # Calculate MAE
            mae = sum(abs(p - a) for p, a in zip(pred_values, y)) / len(y)
            bootstrap_maes.append(mae)

        # Calculate confidence intervals
        bootstrap_maes.sort()
        alpha = 1 - ci_level
        lower_idx = int(alpha / 2 * n_bootstrap)
        upper_idx = int((1 - alpha / 2) * n_bootstrap)

        return {
            "point_estimate": sum(bootstrap_maes) / len(bootstrap_maes),
            "ci_lower": bootstrap_maes[lower_idx] if bootstrap_maes else 0.0,
            "ci_upper": bootstrap_maes[upper_idx - 1] if bootstrap_maes else 0.0,
            "ci_level": ci_level,
            "n_bootstrap": n_bootstrap,
        }


# ============================================================================
# Complete Validation Suite
# ============================================================================


class ValidationSuite:
    """
    Comprehensive validation suite combining all validation methods.
    """

    def __init__(self):
        self.walk_forward = WalkForwardValidator()
        self.probabilistic = ProbabilisticForecaster()
        self.hierarchical = HierarchicalValidator()

    def full_validation(
        self,
        model: BaseModel | StackingEnsemble,
        data: list[dict[str, Any]],
        target_key: str = "target_spread",
    ) -> dict[str, Any]:
        """
        Run complete validation suite.

        Args:
            model: Model to validate
            data: Dataset with features and targets
            target_key: Target variable

        Returns:
            Comprehensive validation results
        """
        results = {}

        # Walk-forward validation
        wf_result = self.walk_forward.validate(model, data, target_key)
        results["walk_forward"] = {
            "mae": wf_result.overall_mae,
            "rmse": wf_result.overall_rmse,
            "coverage": wf_result.overall_coverage,
            "n_folds": len(wf_result.folds),
        }

        # Hierarchical validation (on full dataset, model already trained)
        # Note: In production, this would use out-of-sample predictions
        hier_result = self.hierarchical.validate_with_clustering(
            model, data, target_key
        )
        results["hierarchical"] = hier_result

        # Generate report
        results["report"] = self.walk_forward.generate_report(wf_result)

        return results

    def evaluate_betting_edge(
        self,
        model: BaseModel,
        data: list[dict[str, Any]],
        lines: list[float],
        target_key: str = "target_spread",
    ) -> dict[str, Any]:
        """
        Evaluate model's edge against betting lines.

        Args:
            model: Trained model
            data: Historical data with outcomes
            lines: Betting lines at time of game
            target_key: Target variable

        Returns:
            Edge analysis results
        """
        self.probabilistic.fit(
            [{k: v for k, v in d.items()
              if not k.startswith("_") and not k.startswith("target_")}
             for d in data],
            [d.get(target_key, 0.0) for d in data],
        )

        X = [
            {k: v for k, v in d.items()
             if not k.startswith("_") and not k.startswith("target_")}
            for d in data
        ]
        y = [d.get(target_key, 0.0) for d in data]

        # Analyze each game
        correct_over = 0
        correct_under = 0
        total_bets = 0

        for features, actual, line in zip(X, y, lines):
            pred_result = self.probabilistic.predict_with_threshold(
                [features], line, "over"
            )[0]

            prob_over = pred_result["probability"]

            # Simulate betting on strong edges
            if prob_over > 0.55:  # Bet over
                total_bets += 1
                if actual > line:
                    correct_over += 1
            elif prob_over < 0.45:  # Bet under
                total_bets += 1
                if actual < line:
                    correct_under += 1

        win_rate = (
            (correct_over + correct_under) / total_bets * 100
            if total_bets > 0 else 0.0
        )

        return {
            "total_bets": total_bets,
            "wins": correct_over + correct_under,
            "win_rate": win_rate,
            "required_win_rate": 52.4,  # For -110 odds
            "edge": win_rate - 52.4,
            "profitable": win_rate > 52.4,
        }
