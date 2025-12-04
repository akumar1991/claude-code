"""
Modeling Module

Implements the Global Forecasting Model (GFM) approach and ensemble stacking:
- Global Forecasting Model: Single model trained on all games for cross-learning
- Base Learners: Individual predictors (including external expert systems)
- Stacking Ensemble: Meta-model combining multiple expert predictions
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable
import json
import math
import random


# ============================================================================
# Base Model Interface
# ============================================================================


@dataclass
class Prediction:
    """Model prediction with uncertainty estimates."""

    point_estimate: float
    lower_bound: float  # e.g., 10th percentile
    upper_bound: float  # e.g., 90th percentile
    std_dev: float | None = None
    confidence: float = 0.0  # Model's confidence in this prediction
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseModel(ABC):
    """Abstract base class for all prediction models."""

    @abstractmethod
    def fit(
        self,
        X: list[dict[str, float]],
        y: list[float],
    ) -> None:
        """Train the model on feature dictionaries and targets."""
        pass

    @abstractmethod
    def predict(self, X: list[dict[str, float]]) -> list[Prediction]:
        """Generate predictions with uncertainty estimates."""
        pass

    @abstractmethod
    def get_feature_importance(self) -> dict[str, float]:
        """Return feature importance scores."""
        pass


# ============================================================================
# Global Forecasting Model
# ============================================================================


class GlobalForecastingModel(BaseModel):
    """
    Global Forecasting Model (GFM) that trains on all historical games.

    Instead of training 360+ separate models (one per team), this trains
    a single model on all games to learn universal patterns through
    cross-learning. For example, it learns how ANY team with high defensive
    efficiency performs against ANY team with high offensive tempo.

    This implementation uses a Gradient Boosted Trees approach (simplified
    version without external dependencies).
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        min_samples_split: int = 10,
        subsample: float = 0.8,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.min_samples_split = min_samples_split
        self.subsample = subsample
        self.random_state = random_state

        self._trees: list[dict] = []
        self._feature_names: list[str] = []
        self._feature_importance: dict[str, float] = {}
        self._global_mean: float = 0.0
        self._residual_std: float = 1.0
        self._is_fitted: bool = False

    def _prepare_features(
        self,
        X: list[dict[str, float]],
    ) -> tuple[list[list[float]], list[str]]:
        """Convert feature dictionaries to matrix format."""
        if not X:
            return [], []

        # Get all feature names (excluding metadata starting with _)
        all_features = set()
        for row in X:
            all_features.update(
                k for k in row.keys()
                if not k.startswith("_") and not k.startswith("target_")
            )

        feature_names = sorted(all_features)

        # Convert to matrix
        matrix = []
        for row in X:
            row_values = []
            for feat in feature_names:
                val = row.get(feat)
                # Handle missing values with mean imputation placeholder
                row_values.append(val if val is not None else 0.0)
            matrix.append(row_values)

        return matrix, feature_names

    def _build_tree(
        self,
        X: list[list[float]],
        residuals: list[float],
        depth: int = 0,
    ) -> dict:
        """Build a single decision tree (simplified CART algorithm)."""
        n_samples = len(X)

        # Base cases
        if depth >= self.max_depth or n_samples < self.min_samples_split:
            return {"leaf": True, "value": sum(residuals) / max(n_samples, 1)}

        # Find best split
        best_gain = 0.0
        best_split = None
        n_features = len(X[0]) if X else 0

        # Sample features for split consideration (feature bagging)
        feature_indices = list(range(n_features))
        random.shuffle(feature_indices)
        features_to_try = feature_indices[: max(1, n_features // 3)]

        parent_variance = self._variance(residuals)

        for feat_idx in features_to_try:
            values = sorted(set(row[feat_idx] for row in X))
            if len(values) < 2:
                continue

            # Try split points between unique values
            for i in range(len(values) - 1):
                threshold = (values[i] + values[i + 1]) / 2

                left_idx = [j for j, row in enumerate(X) if row[feat_idx] <= threshold]
                right_idx = [j for j, row in enumerate(X) if row[feat_idx] > threshold]

                if len(left_idx) < 2 or len(right_idx) < 2:
                    continue

                left_res = [residuals[j] for j in left_idx]
                right_res = [residuals[j] for j in right_idx]

                # Calculate information gain
                left_var = self._variance(left_res)
                right_var = self._variance(right_res)

                weighted_var = (
                    len(left_idx) * left_var + len(right_idx) * right_var
                ) / n_samples
                gain = parent_variance - weighted_var

                if gain > best_gain:
                    best_gain = gain
                    best_split = {
                        "feature": feat_idx,
                        "threshold": threshold,
                        "left_idx": left_idx,
                        "right_idx": right_idx,
                    }

        # If no good split found, make leaf
        if best_split is None:
            return {"leaf": True, "value": sum(residuals) / max(n_samples, 1)}

        # Recursively build subtrees
        left_X = [X[i] for i in best_split["left_idx"]]
        left_res = [residuals[i] for i in best_split["left_idx"]]

        right_X = [X[i] for i in best_split["right_idx"]]
        right_res = [residuals[i] for i in best_split["right_idx"]]

        return {
            "leaf": False,
            "feature": best_split["feature"],
            "threshold": best_split["threshold"],
            "left": self._build_tree(left_X, left_res, depth + 1),
            "right": self._build_tree(right_X, right_res, depth + 1),
        }

    def _variance(self, values: list[float]) -> float:
        """Calculate variance of a list."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    def _predict_tree(self, tree: dict, row: list[float]) -> float:
        """Get prediction from a single tree."""
        if tree["leaf"]:
            return tree["value"]

        if row[tree["feature"]] <= tree["threshold"]:
            return self._predict_tree(tree["left"], row)
        else:
            return self._predict_tree(tree["right"], row)

    def _update_feature_importance(self, tree: dict, importance: dict) -> None:
        """Recursively accumulate feature importance from tree splits."""
        if tree["leaf"]:
            return

        feat_idx = tree["feature"]
        feat_name = (
            self._feature_names[feat_idx]
            if feat_idx < len(self._feature_names)
            else f"feature_{feat_idx}"
        )
        importance[feat_name] = importance.get(feat_name, 0.0) + 1.0

        self._update_feature_importance(tree["left"], importance)
        self._update_feature_importance(tree["right"], importance)

    def fit(
        self,
        X: list[dict[str, float]],
        y: list[float],
    ) -> None:
        """
        Train the Global Forecasting Model on all games.

        Args:
            X: List of feature dictionaries (one per game)
            y: List of target values (e.g., point spreads)
        """
        random.seed(self.random_state)

        # Convert features
        X_matrix, self._feature_names = self._prepare_features(X)

        if not X_matrix:
            raise ValueError("No valid training data")

        n_samples = len(X_matrix)
        self._global_mean = sum(y) / n_samples

        # Initialize residuals
        residuals = [yi - self._global_mean for yi in y]
        predictions = [self._global_mean] * n_samples

        self._trees = []

        # Build trees
        for _ in range(self.n_estimators):
            # Subsample
            if self.subsample < 1.0:
                sample_size = int(n_samples * self.subsample)
                indices = random.sample(range(n_samples), sample_size)
                X_sample = [X_matrix[i] for i in indices]
                res_sample = [residuals[i] for i in indices]
            else:
                X_sample = X_matrix
                res_sample = residuals

            # Build tree on residuals
            tree = self._build_tree(X_sample, res_sample)
            self._trees.append(tree)

            # Update predictions and residuals
            for i in range(n_samples):
                pred = self._predict_tree(tree, X_matrix[i])
                predictions[i] += self.learning_rate * pred
                residuals[i] = y[i] - predictions[i]

        # Calculate residual standard deviation for uncertainty
        final_residuals = [y[i] - predictions[i] for i in range(n_samples)]
        self._residual_std = math.sqrt(self._variance(final_residuals))

        # Calculate feature importance
        importance: dict[str, float] = {}
        for tree in self._trees:
            self._update_feature_importance(tree, importance)

        # Normalize importance
        total = sum(importance.values()) or 1.0
        self._feature_importance = {k: v / total for k, v in importance.items()}

        self._is_fitted = True

    def predict(self, X: list[dict[str, float]]) -> list[Prediction]:
        """
        Generate predictions with uncertainty estimates.

        Args:
            X: List of feature dictionaries

        Returns:
            List of Prediction objects
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        X_matrix, _ = self._prepare_features(X)
        predictions = []

        for row in X_matrix:
            # Sum predictions from all trees
            pred = self._global_mean
            for tree in self._trees:
                pred += self.learning_rate * self._predict_tree(tree, row)

            # Create prediction with uncertainty
            predictions.append(
                Prediction(
                    point_estimate=pred,
                    lower_bound=pred - 1.645 * self._residual_std,  # 90% CI
                    upper_bound=pred + 1.645 * self._residual_std,
                    std_dev=self._residual_std,
                    confidence=0.9,
                )
            )

        return predictions

    def get_feature_importance(self) -> dict[str, float]:
        """Return feature importance scores."""
        return self._feature_importance.copy()

    def export_model(self) -> str:
        """Export model to JSON."""
        return json.dumps({
            "global_mean": self._global_mean,
            "residual_std": self._residual_std,
            "feature_names": self._feature_names,
            "feature_importance": self._feature_importance,
            "trees": self._trees,
            "params": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "learning_rate": self.learning_rate,
            },
        })

    def import_model(self, json_str: str) -> None:
        """Import model from JSON."""
        data = json.loads(json_str)
        self._global_mean = data["global_mean"]
        self._residual_std = data["residual_std"]
        self._feature_names = data["feature_names"]
        self._feature_importance = data["feature_importance"]
        self._trees = data["trees"]
        self._is_fitted = True


# ============================================================================
# Base Learners Factory
# ============================================================================


class ExpertSystemPredictor(BaseModel):
    """
    Wrapper for external expert system predictions (KenPom, Torvik, Miya).
    Uses their pre-computed predictions as the primary signal.
    """

    def __init__(self, source: str):
        """
        Initialize expert system predictor.

        Args:
            source: Name of expert system ("kenpom", "evanmiya", "barttorvik")
        """
        self.source = source.lower()
        self._historical_errors: list[float] = []
        self._mean_error: float = 0.0
        self._std_error: float = 3.0  # Default uncertainty

    def fit(
        self,
        X: list[dict[str, float]],
        y: list[float],
    ) -> None:
        """
        Calibrate the expert system based on historical performance.
        Uses the efficiency margin delta as the prediction.
        """
        em_key = f"{self.source}_efficiency_margin_delta"

        errors = []
        for features, actual in zip(X, y):
            pred = features.get(em_key)
            if pred is not None:
                errors.append(actual - pred)

        if errors:
            self._historical_errors = errors
            self._mean_error = sum(errors) / len(errors)
            self._std_error = math.sqrt(
                sum((e - self._mean_error) ** 2 for e in errors) / len(errors)
            )

    def predict(self, X: list[dict[str, float]]) -> list[Prediction]:
        """Generate predictions from expert system ratings."""
        em_key = f"{self.source}_efficiency_margin_delta"
        predictions = []

        for features in X:
            pred = features.get(em_key, 0.0) or 0.0
            # Adjust for historical bias
            adjusted_pred = pred + self._mean_error

            predictions.append(
                Prediction(
                    point_estimate=adjusted_pred,
                    lower_bound=adjusted_pred - 1.645 * self._std_error,
                    upper_bound=adjusted_pred + 1.645 * self._std_error,
                    std_dev=self._std_error,
                    confidence=0.8,
                    metadata={"source": self.source},
                )
            )

        return predictions

    def get_feature_importance(self) -> dict[str, float]:
        """Expert systems use a single feature."""
        return {f"{self.source}_efficiency_margin_delta": 1.0}


class LinearRegressionModel(BaseModel):
    """Simple linear regression for baseline comparisons."""

    def __init__(self, regularization: float = 0.01):
        self._weights: dict[str, float] = {}
        self._bias: float = 0.0
        self._residual_std: float = 1.0
        self._regularization = regularization
        self._feature_names: list[str] = []

    def fit(
        self,
        X: list[dict[str, float]],
        y: list[float],
    ) -> None:
        """Fit using gradient descent (simplified)."""
        if not X:
            return

        # Get feature names
        self._feature_names = sorted(
            k for k in X[0].keys()
            if not k.startswith("_") and not k.startswith("target_")
        )

        n_samples = len(X)
        n_features = len(self._feature_names)

        # Initialize weights
        self._weights = {f: 0.0 for f in self._feature_names}
        self._bias = sum(y) / n_samples

        # Simple gradient descent
        learning_rate = 0.001
        for _ in range(1000):
            # Calculate gradients
            grad_weights = {f: 0.0 for f in self._feature_names}
            grad_bias = 0.0

            for features, target in zip(X, y):
                pred = self._bias
                for f in self._feature_names:
                    val = features.get(f, 0.0) or 0.0
                    pred += self._weights[f] * val

                error = pred - target
                grad_bias += error / n_samples

                for f in self._feature_names:
                    val = features.get(f, 0.0) or 0.0
                    grad_weights[f] += (error * val) / n_samples
                    # L2 regularization
                    grad_weights[f] += self._regularization * self._weights[f]

            # Update weights
            self._bias -= learning_rate * grad_bias
            for f in self._feature_names:
                self._weights[f] -= learning_rate * grad_weights[f]

        # Calculate residual std
        residuals = []
        for features, target in zip(X, y):
            pred = self._bias
            for f in self._feature_names:
                val = features.get(f, 0.0) or 0.0
                pred += self._weights[f] * val
            residuals.append(target - pred)

        if residuals:
            mean_res = sum(residuals) / len(residuals)
            self._residual_std = math.sqrt(
                sum((r - mean_res) ** 2 for r in residuals) / len(residuals)
            )

    def predict(self, X: list[dict[str, float]]) -> list[Prediction]:
        """Generate predictions."""
        predictions = []

        for features in X:
            pred = self._bias
            for f in self._feature_names:
                val = features.get(f, 0.0) or 0.0
                pred += self._weights[f] * val

            predictions.append(
                Prediction(
                    point_estimate=pred,
                    lower_bound=pred - 1.645 * self._residual_std,
                    upper_bound=pred + 1.645 * self._residual_std,
                    std_dev=self._residual_std,
                    confidence=0.85,
                )
            )

        return predictions

    def get_feature_importance(self) -> dict[str, float]:
        """Return absolute weight magnitudes as importance."""
        total = sum(abs(w) for w in self._weights.values()) or 1.0
        return {k: abs(v) / total for k, v in self._weights.items()}


class BaseLearnersFactory:
    """Factory for creating base learner models."""

    @staticmethod
    def create_expert_predictors() -> list[BaseModel]:
        """Create predictors for each expert system."""
        return [
            ExpertSystemPredictor("kenpom"),
            ExpertSystemPredictor("evanmiya"),
            ExpertSystemPredictor("barttorvik"),
        ]

    @staticmethod
    def create_gfm(
        n_estimators: int = 100,
        max_depth: int = 6,
    ) -> GlobalForecastingModel:
        """Create a Global Forecasting Model."""
        return GlobalForecastingModel(
            n_estimators=n_estimators,
            max_depth=max_depth,
        )

    @staticmethod
    def create_linear_model() -> LinearRegressionModel:
        """Create a linear regression baseline."""
        return LinearRegressionModel()

    @staticmethod
    def create_all_base_learners() -> list[BaseModel]:
        """Create a complete set of base learners for stacking."""
        learners = []
        learners.extend(BaseLearnersFactory.create_expert_predictors())
        learners.append(BaseLearnersFactory.create_gfm())
        learners.append(BaseLearnersFactory.create_linear_model())
        return learners


# ============================================================================
# Stacking Ensemble
# ============================================================================


class StackingEnsemble:
    """
    Stacking meta-model that combines multiple expert predictions.

    The meta-model learns which source is most accurate in specific situations:
    - "Trust Torvik more early in the season"
    - "Trust KenPom for high-tempo games"
    - "Trust the GFM for unusual matchups"
    """

    def __init__(
        self,
        base_learners: list[BaseModel] | None = None,
        meta_model: BaseModel | None = None,
    ):
        """
        Initialize stacking ensemble.

        Args:
            base_learners: List of base models (default: all available)
            meta_model: Meta-model for combining (default: GFM)
        """
        self._base_learners = base_learners or BaseLearnersFactory.create_all_base_learners()
        self._meta_model = meta_model or GlobalForecastingModel(
            n_estimators=50,
            max_depth=4,
        )
        self._base_learner_names: list[str] = []
        self._is_fitted = False

    def fit(
        self,
        X: list[dict[str, float]],
        y: list[float],
        cv_folds: int = 5,
    ) -> None:
        """
        Fit the stacking ensemble using cross-validation.

        Args:
            X: Feature dictionaries
            y: Target values
            cv_folds: Number of cross-validation folds
        """
        n_samples = len(X)
        fold_size = n_samples // cv_folds

        # Generate out-of-fold predictions for each base learner
        base_predictions: list[list[float]] = [[] for _ in self._base_learners]
        oof_targets: list[float] = []

        for fold in range(cv_folds):
            # Split data
            val_start = fold * fold_size
            val_end = (fold + 1) * fold_size if fold < cv_folds - 1 else n_samples

            train_X = X[:val_start] + X[val_end:]
            train_y = y[:val_start] + y[val_end:]
            val_X = X[val_start:val_end]
            val_y = y[val_start:val_end]

            # Train and predict with each base learner
            for i, learner in enumerate(self._base_learners):
                learner.fit(train_X, train_y)
                preds = learner.predict(val_X)
                base_predictions[i].extend([p.point_estimate for p in preds])

            oof_targets.extend(val_y)

        # Create meta-features from base predictions
        meta_X = []
        for i in range(len(oof_targets)):
            meta_features = {}
            for j, learner in enumerate(self._base_learners):
                learner_name = type(learner).__name__
                if hasattr(learner, "source"):
                    learner_name = f"{learner_name}_{learner.source}"
                meta_features[f"base_{learner_name}"] = base_predictions[j][i]

                # Add original features for context
                if i < len(X):
                    for k, v in X[i].items():
                        if not k.startswith("_") and not k.startswith("target_"):
                            meta_features[k] = v

            meta_X.append(meta_features)

        # Fit meta-model
        self._meta_model.fit(meta_X, oof_targets)

        # Re-fit base learners on full data
        for learner in self._base_learners:
            learner.fit(X, y)

        # Store learner names
        self._base_learner_names = []
        for learner in self._base_learners:
            name = type(learner).__name__
            if hasattr(learner, "source"):
                name = f"{name}_{learner.source}"
            self._base_learner_names.append(name)

        self._is_fitted = True

    def predict(self, X: list[dict[str, float]]) -> list[Prediction]:
        """
        Generate stacked predictions.

        Args:
            X: Feature dictionaries

        Returns:
            List of Prediction objects
        """
        if not self._is_fitted:
            raise RuntimeError("Ensemble not fitted. Call fit() first.")

        # Get base learner predictions
        base_preds = []
        for learner in self._base_learners:
            preds = learner.predict(X)
            base_preds.append([p.point_estimate for p in preds])

        # Create meta-features
        meta_X = []
        for i in range(len(X)):
            meta_features = {}
            for j, name in enumerate(self._base_learner_names):
                meta_features[f"base_{name}"] = base_preds[j][i]

            # Add original features
            for k, v in X[i].items():
                if not k.startswith("_") and not k.startswith("target_"):
                    meta_features[k] = v

            meta_X.append(meta_features)

        # Get meta-model predictions
        return self._meta_model.predict(meta_X)

    def get_base_learner_weights(self) -> dict[str, float]:
        """
        Get the effective weights of each base learner.
        Derived from meta-model feature importance.
        """
        importance = self._meta_model.get_feature_importance()

        weights = {}
        total = 0.0
        for name in self._base_learner_names:
            key = f"base_{name}"
            weight = importance.get(key, 0.0)
            weights[name] = weight
            total += weight

        # Normalize
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def get_source_reliability(
        self,
        context_features: dict[str, float],
    ) -> dict[str, float]:
        """
        Get reliability scores for each source in a specific context.

        Args:
            context_features: Game context (tempo, conference, etc.)

        Returns:
            Dictionary of source -> reliability score
        """
        # Use feature importance as proxy for reliability
        # In production, this would analyze conditional performance
        return self.get_base_learner_weights()

    def explain_prediction(
        self,
        features: dict[str, float],
    ) -> dict[str, Any]:
        """
        Explain a prediction showing base learner contributions.

        Args:
            features: Single game feature dictionary

        Returns:
            Explanation with base predictions and weights
        """
        # Get individual predictions
        base_results = {}
        for learner, name in zip(self._base_learners, self._base_learner_names):
            pred = learner.predict([features])[0]
            base_results[name] = {
                "prediction": pred.point_estimate,
                "lower": pred.lower_bound,
                "upper": pred.upper_bound,
                "confidence": pred.confidence,
            }

        # Get ensemble prediction
        ensemble_pred = self.predict([features])[0]

        # Get weights
        weights = self.get_base_learner_weights()

        return {
            "ensemble_prediction": {
                "point": ensemble_pred.point_estimate,
                "lower": ensemble_pred.lower_bound,
                "upper": ensemble_pred.upper_bound,
            },
            "base_predictions": base_results,
            "base_weights": weights,
            "most_trusted_source": max(weights.keys(), key=lambda k: weights[k]),
        }


# ============================================================================
# Prediction Pipeline
# ============================================================================


class PredictionPipeline:
    """
    Complete prediction pipeline combining feature engineering and modeling.
    """

    def __init__(
        self,
        ensemble: StackingEnsemble | None = None,
        target: str = "spread",  # "spread", "total", "home_win"
    ):
        self._ensemble = ensemble or StackingEnsemble()
        self._target = target
        self._target_map = {
            "spread": "target_spread",
            "total": "target_total",
            "home_win": "target_home_win",
            "home_score": "target_home_score",
            "away_score": "target_away_score",
        }

    def train(self, training_data: list[dict[str, Any]]) -> None:
        """
        Train the pipeline on historical data.

        Args:
            training_data: List of feature dictionaries with targets
        """
        target_key = self._target_map.get(self._target, "target_spread")

        # Extract features and targets
        X = []
        y = []

        for row in training_data:
            target_val = row.get(target_key)
            if target_val is None:
                continue

            features = {
                k: v for k, v in row.items()
                if not k.startswith("_") and not k.startswith("target_")
            }
            X.append(features)
            y.append(float(target_val))

        if not X:
            raise ValueError("No valid training samples")

        self._ensemble.fit(X, y)

    def predict_game(
        self,
        features: dict[str, float],
    ) -> dict[str, Any]:
        """
        Predict a single game.

        Args:
            features: Game feature dictionary

        Returns:
            Prediction with explanation
        """
        clean_features = {
            k: v for k, v in features.items()
            if not k.startswith("_") and not k.startswith("target_")
        }

        pred = self._ensemble.predict([clean_features])[0]
        explanation = self._ensemble.explain_prediction(clean_features)

        return {
            "target": self._target,
            "prediction": pred.point_estimate,
            "confidence_interval": {
                "lower": pred.lower_bound,
                "upper": pred.upper_bound,
            },
            "std_dev": pred.std_dev,
            "explanation": explanation,
        }

    def predict_batch(
        self,
        features_list: list[dict[str, float]],
    ) -> list[dict[str, Any]]:
        """Predict multiple games."""
        return [self.predict_game(f) for f in features_list]
