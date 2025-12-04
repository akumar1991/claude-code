"""
Feature Engineering Module

Implements feature creation for NCAAB predictions:
- Exogenous Variables: Pre-game ratings as parallel time series
- Interaction Features: Matchup deltas combining team styles
- Rolling Window Aggregations: Capturing recent form
- Entity Embeddings: Vector representations of categorical variables
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Callable
import math
import json

from .data_architecture import (
    GameResult,
    MetricsSnapshot,
    NCAABDataWarehouse,
    TeamNameStandardizer,
)


# ============================================================================
# Exogenous Variable Processor
# ============================================================================


class ExogenousVariableProcessor:
    """
    Treats pre-game KenPom, Torvik, and Miya ratings as exogenous variables.
    These are parallel time series that help model the target variable (game score).
    """

    # Standard metric names across sources
    COMMON_METRICS = [
        "adj_offense",
        "adj_defense",
        "adj_tempo",
        "adj_em",
        "efg_pct",
        "turnover_pct",
        "orb_pct",
        "ftr",
        "opp_efg_pct",
        "opp_turnover_pct",
        "drb_pct",
        "opp_ftr",
    ]

    def __init__(self, warehouse: NCAABDataWarehouse):
        self._warehouse = warehouse

    def extract_exogenous_features(
        self,
        team: str,
        game_date: date,
        sources: list[str] | None = None,
    ) -> dict[str, float | None]:
        """
        Extract exogenous features for a team on a specific date.

        Args:
            team: Team name
            game_date: Date to get metrics for
            sources: List of sources to use (default: all)

        Returns:
            Dictionary of feature name -> value
        """
        if sources is None:
            sources = ["kenpom", "evanmiya", "barttorvik"]

        features: dict[str, float | None] = {}

        source_tables = {
            "kenpom": self._warehouse.kenpom,
            "evanmiya": self._warehouse.evanmiya,
            "barttorvik": self._warehouse.barttorvik,
        }

        for source in sources:
            table = source_tables.get(source)
            if not table:
                continue

            snapshot = table.get_metrics_on_date(team, game_date)
            if not snapshot:
                # Fill with None for missing data
                for metric in self.COMMON_METRICS:
                    features[f"{source}_{metric}"] = None
                continue

            # Extract common metrics
            for metric in self.COMMON_METRICS:
                value = getattr(snapshot, metric, None)
                features[f"{source}_{metric}"] = value

            # Source-specific metrics
            if source == "kenpom":
                features["kenpom_luck"] = snapshot.luck_rating
                features["kenpom_sos"] = snapshot.sos
            elif source == "barttorvik":
                features["barttorvik_barthag"] = snapshot.barthag
                features["barttorvik_wab"] = snapshot.wins_above_bubble
            elif source == "evanmiya":
                features["evanmiya_bpr"] = snapshot.bpr

        return features

    def extract_game_features(
        self,
        home_team: str,
        away_team: str,
        game_date: date,
    ) -> dict[str, float | None]:
        """
        Extract exogenous features for both teams in a game.

        Returns:
            Dictionary with home_ and away_ prefixed features
        """
        home_features = self.extract_exogenous_features(home_team, game_date)
        away_features = self.extract_exogenous_features(away_team, game_date)

        features = {}
        for k, v in home_features.items():
            features[f"home_{k}"] = v
        for k, v in away_features.items():
            features[f"away_{k}"] = v

        return features


# ============================================================================
# Matchup Feature Engine
# ============================================================================


@dataclass
class MatchupFeature:
    """Definition of a matchup interaction feature."""

    name: str
    home_metric: str
    away_metric: str
    operation: str  # "subtract", "multiply", "divide", "average", "max", "min"
    description: str = ""


class MatchupFeatureEngine:
    """
    Creates features that explicitly interact two teams' styles.
    Allows the model to learn nonlinear relationships like how
    high-tempo teams struggle against pack-line defenses.
    """

    # Predefined matchup features based on basketball strategy
    DEFAULT_MATCHUP_FEATURES: list[MatchupFeature] = [
        # Efficiency Margins
        MatchupFeature(
            "efficiency_margin_delta",
            "adj_em",
            "adj_em",
            "subtract",
            "Home efficiency margin minus away efficiency margin",
        ),
        # Pace Matchups
        MatchupFeature(
            "tempo_delta",
            "adj_tempo",
            "adj_tempo",
            "subtract",
            "Tempo difference (positive = home faster)",
        ),
        MatchupFeature(
            "expected_tempo",
            "adj_tempo",
            "adj_tempo",
            "average",
            "Expected game tempo",
        ),
        # Offense vs Defense Matchups
        MatchupFeature(
            "home_off_vs_away_def",
            "adj_offense",
            "adj_defense",
            "subtract",
            "Home offense efficiency vs away defense (higher = home advantage)",
        ),
        MatchupFeature(
            "away_off_vs_home_def",
            "adj_offense",
            "adj_defense",
            "subtract",
            "Away offense efficiency vs home defense (from away perspective)",
        ),
        # Four Factors Matchups
        MatchupFeature(
            "shooting_battle",
            "efg_pct",
            "opp_efg_pct",
            "subtract",
            "Home EFG% vs Away defensive EFG% allowed",
        ),
        MatchupFeature(
            "turnover_battle",
            "turnover_pct",
            "opp_turnover_pct",
            "subtract",
            "Home TO% vs Away forced TO% (negative = home advantage)",
        ),
        MatchupFeature(
            "rebounding_battle",
            "orb_pct",
            "drb_pct",
            "subtract",
            "Home ORB% vs Away DRB%",
        ),
        MatchupFeature(
            "foul_drawing_battle",
            "ftr",
            "opp_ftr",
            "subtract",
            "Home FT rate vs Away FT rate allowed",
        ),
        # Style Matchups
        MatchupFeature(
            "pace_mismatch",
            "adj_tempo",
            "adj_tempo",
            "subtract",
            "Absolute tempo difference (style clash indicator)",
        ),
    ]

    def __init__(
        self,
        exogenous_processor: ExogenousVariableProcessor,
        custom_features: list[MatchupFeature] | None = None,
    ):
        self._processor = exogenous_processor
        self._features = self.DEFAULT_MATCHUP_FEATURES.copy()
        if custom_features:
            self._features.extend(custom_features)

    def _apply_operation(
        self,
        home_value: float | None,
        away_value: float | None,
        operation: str,
    ) -> float | None:
        """Apply the specified operation to create the interaction feature."""
        if home_value is None or away_value is None:
            return None

        if operation == "subtract":
            return home_value - away_value
        elif operation == "multiply":
            return home_value * away_value
        elif operation == "divide":
            if away_value == 0:
                return None
            return home_value / away_value
        elif operation == "average":
            return (home_value + away_value) / 2
        elif operation == "max":
            return max(home_value, away_value)
        elif operation == "min":
            return min(home_value, away_value)
        elif operation == "abs_diff":
            return abs(home_value - away_value)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def create_matchup_features(
        self,
        home_team: str,
        away_team: str,
        game_date: date,
        sources: list[str] | None = None,
    ) -> dict[str, float | None]:
        """
        Create all matchup interaction features for a game.

        Args:
            home_team: Home team name
            away_team: Away team name
            game_date: Date of the game
            sources: Data sources to use (default: all)

        Returns:
            Dictionary of matchup feature name -> value
        """
        if sources is None:
            sources = ["kenpom", "evanmiya", "barttorvik"]

        # Get raw features for both teams
        home_features = self._processor.extract_exogenous_features(
            home_team, game_date, sources
        )
        away_features = self._processor.extract_exogenous_features(
            away_team, game_date, sources
        )

        matchup_features: dict[str, float | None] = {}

        # Create interaction features for each source
        for source in sources:
            for feature_def in self._features:
                home_key = f"{source}_{feature_def.home_metric}"
                away_key = f"{source}_{feature_def.away_metric}"

                home_val = home_features.get(home_key)
                away_val = away_features.get(away_key)

                feature_name = f"{source}_{feature_def.name}"
                matchup_features[feature_name] = self._apply_operation(
                    home_val, away_val, feature_def.operation
                )

        # Create cross-source consensus features
        matchup_features.update(
            self._create_consensus_features(home_features, away_features, sources)
        )

        return matchup_features

    def _create_consensus_features(
        self,
        home_features: dict[str, float | None],
        away_features: dict[str, float | None],
        sources: list[str],
    ) -> dict[str, float | None]:
        """Create features averaging across multiple sources."""
        consensus = {}

        # Average efficiency margin across sources
        home_ems = [
            home_features.get(f"{s}_adj_em")
            for s in sources
            if home_features.get(f"{s}_adj_em") is not None
        ]
        away_ems = [
            away_features.get(f"{s}_adj_em")
            for s in sources
            if away_features.get(f"{s}_adj_em") is not None
        ]

        if home_ems and away_ems:
            home_avg_em = sum(home_ems) / len(home_ems)
            away_avg_em = sum(away_ems) / len(away_ems)
            consensus["consensus_em_delta"] = home_avg_em - away_avg_em
            consensus["consensus_home_em"] = home_avg_em
            consensus["consensus_away_em"] = away_avg_em

        # Source agreement (std dev of predictions)
        if len(home_ems) > 1:
            mean_home = sum(home_ems) / len(home_ems)
            variance = sum((x - mean_home) ** 2 for x in home_ems) / len(home_ems)
            consensus["home_source_disagreement"] = math.sqrt(variance)

        if len(away_ems) > 1:
            mean_away = sum(away_ems) / len(away_ems)
            variance = sum((x - mean_away) ** 2 for x in away_ems) / len(away_ems)
            consensus["away_source_disagreement"] = math.sqrt(variance)

        return consensus

    def add_custom_feature(self, feature: MatchupFeature) -> None:
        """Add a custom matchup feature definition."""
        self._features.append(feature)


# ============================================================================
# Rolling Window Calculator
# ============================================================================


@dataclass
class RollingConfig:
    """Configuration for rolling window calculations."""

    window_sizes: list[int] = field(default_factory=lambda: [3, 5, 10])
    metrics: list[str] = field(
        default_factory=lambda: [
            "points",
            "rebounds",
            "assists",
            "fg_pct",
            "efg_pct",
            "turnovers",
        ]
    )
    include_opponent_adjusted: bool = True


class RollingWindowCalculator:
    """
    Applies rolling windows to capture recent form rather than season-long averages.
    Smooths out noise and captures trending performance.
    """

    def __init__(
        self,
        warehouse: NCAABDataWarehouse,
        config: RollingConfig | None = None,
    ):
        self._warehouse = warehouse
        self._config = config or RollingConfig()

    def _calculate_game_stats(
        self,
        game: GameResult,
        team: str,
    ) -> dict[str, float]:
        """Extract stats for a team from a game."""
        is_home = game.home_team == team

        if is_home:
            stats = {
                "points": game.home_score,
                "rebounds": game.home_rebounds,
                "assists": game.home_assists,
                "turnovers": game.home_turnovers,
                "fg_made": game.home_fg_made,
                "fg_attempted": game.home_fg_attempted,
                "3pt_made": game.home_3pt_made,
                "3pt_attempted": game.home_3pt_attempted,
                "opp_points": game.away_score,
            }
        else:
            stats = {
                "points": game.away_score,
                "rebounds": game.away_rebounds,
                "assists": game.away_assists,
                "turnovers": game.away_turnovers,
                "fg_made": game.away_fg_made,
                "fg_attempted": game.away_fg_attempted,
                "3pt_made": game.away_3pt_made,
                "3pt_attempted": game.away_3pt_attempted,
                "opp_points": game.home_score,
            }

        # Calculate percentages
        if stats["fg_attempted"] > 0:
            stats["fg_pct"] = stats["fg_made"] / stats["fg_attempted"]
            # Effective FG% = (FGM + 0.5 * 3PM) / FGA
            stats["efg_pct"] = (
                stats["fg_made"] + 0.5 * stats["3pt_made"]
            ) / stats["fg_attempted"]
        else:
            stats["fg_pct"] = 0.0
            stats["efg_pct"] = 0.0

        if stats["3pt_attempted"] > 0:
            stats["3pt_pct"] = stats["3pt_made"] / stats["3pt_attempted"]
        else:
            stats["3pt_pct"] = 0.0

        # Point differential
        stats["point_diff"] = stats["points"] - stats["opp_points"]
        stats["win"] = 1.0 if stats["point_diff"] > 0 else 0.0

        return stats

    def calculate_rolling_features(
        self,
        team: str,
        as_of_date: date,
    ) -> dict[str, float | None]:
        """
        Calculate rolling window features for a team as of a specific date.

        Args:
            team: Team name
            as_of_date: Calculate based on games before this date

        Returns:
            Dictionary of rolling feature name -> value
        """
        team = self._warehouse.standardize_team(team)

        # Get games before the target date
        games = self._warehouse.games.get_games_by_team(team, end_date=as_of_date)
        # Exclude games on the target date (we're predicting that game)
        games = [g for g in games if g.game_date < as_of_date]

        if not games:
            return {}

        # Sort by date descending (most recent first)
        games = sorted(games, key=lambda g: g.game_date, reverse=True)

        # Calculate stats for each game
        game_stats = [self._calculate_game_stats(g, team) for g in games]

        features: dict[str, float | None] = {}

        # Calculate rolling averages for each window size
        for window in self._config.window_sizes:
            window_games = game_stats[:window]
            if not window_games:
                continue

            n = len(window_games)
            suffix = f"_L{window}"

            # Basic counting stats
            for metric in ["points", "rebounds", "assists", "turnovers", "opp_points"]:
                values = [g.get(metric, 0) for g in window_games]
                features[f"{metric}_avg{suffix}"] = sum(values) / n

            # Percentages (use game-level averages, not totals)
            for metric in ["fg_pct", "efg_pct", "3pt_pct"]:
                values = [g.get(metric, 0) for g in window_games]
                features[f"{metric}_avg{suffix}"] = sum(values) / n

            # Win rate
            wins = sum(g.get("win", 0) for g in window_games)
            features[f"win_rate{suffix}"] = wins / n

            # Point differential
            diffs = [g.get("point_diff", 0) for g in window_games]
            features[f"point_diff_avg{suffix}"] = sum(diffs) / n

            # Variance/consistency metrics
            if n > 1:
                mean_pts = sum(g.get("points", 0) for g in window_games) / n
                variance = sum(
                    (g.get("points", 0) - mean_pts) ** 2 for g in window_games
                ) / n
                features[f"points_std{suffix}"] = math.sqrt(variance)

        # Trend features (comparing recent to older)
        if len(game_stats) >= 5:
            recent_3 = game_stats[:3]
            older_5 = game_stats[:5]

            recent_pts = sum(g.get("points", 0) for g in recent_3) / 3
            older_pts = sum(g.get("points", 0) for g in older_5) / 5
            features["scoring_trend"] = recent_pts - older_pts

            recent_diff = sum(g.get("point_diff", 0) for g in recent_3) / 3
            older_diff = sum(g.get("point_diff", 0) for g in older_5) / 5
            features["margin_trend"] = recent_diff - older_diff

        # Days rest
        if games:
            most_recent_game = games[0]
            days_rest = (as_of_date - most_recent_game.game_date).days
            features["days_rest"] = float(days_rest)

        return features

    def calculate_game_rolling_features(
        self,
        home_team: str,
        away_team: str,
        game_date: date,
    ) -> dict[str, float | None]:
        """
        Calculate rolling features for both teams in a matchup.

        Returns:
            Dictionary with home_ and away_ prefixed rolling features
        """
        home_features = self.calculate_rolling_features(home_team, game_date)
        away_features = self.calculate_rolling_features(away_team, game_date)

        features = {}
        for k, v in home_features.items():
            features[f"home_{k}"] = v
        for k, v in away_features.items():
            features[f"away_{k}"] = v

        # Rolling feature deltas
        for window in self._config.window_sizes:
            suffix = f"_L{window}"

            home_pts = home_features.get(f"points_avg{suffix}")
            away_pts = away_features.get(f"points_avg{suffix}")
            if home_pts is not None and away_pts is not None:
                features[f"points_avg_delta{suffix}"] = home_pts - away_pts

            home_diff = home_features.get(f"point_diff_avg{suffix}")
            away_diff = away_features.get(f"point_diff_avg{suffix}")
            if home_diff is not None and away_diff is not None:
                features[f"point_diff_delta{suffix}"] = home_diff - away_diff

        return features


# ============================================================================
# Entity Embedding
# ============================================================================


class EntityEmbedding:
    """
    Maps categorical variables (Team ID, Conference) into vector space.
    Learns which teams are mathematically similar based on performance history.

    This is a simplified implementation that creates initial embeddings based
    on team metrics. In production, these would be learned during model training.
    """

    def __init__(
        self,
        warehouse: NCAABDataWarehouse,
        embedding_dim: int = 16,
    ):
        self._warehouse = warehouse
        self._embedding_dim = embedding_dim
        self._team_embeddings: dict[str, list[float]] = {}
        self._conference_embeddings: dict[str, list[float]] = {}

    def _normalize(self, values: list[float]) -> list[float]:
        """Normalize values to unit length."""
        magnitude = math.sqrt(sum(v * v for v in values))
        if magnitude == 0:
            return values
        return [v / magnitude for v in values]

    def _metrics_to_embedding(
        self,
        snapshot: MetricsSnapshot | None,
    ) -> list[float]:
        """Convert a metrics snapshot to an embedding vector."""
        if snapshot is None:
            return [0.0] * self._embedding_dim

        # Use key metrics as embedding dimensions
        raw_values = [
            snapshot.adj_offense or 100.0,
            snapshot.adj_defense or 100.0,
            snapshot.adj_tempo or 68.0,
            snapshot.efg_pct or 0.5,
            snapshot.turnover_pct or 0.18,
            snapshot.orb_pct or 0.30,
            snapshot.ftr or 0.30,
            snapshot.opp_efg_pct or 0.5,
        ]

        # Pad or truncate to embedding dimension
        if len(raw_values) < self._embedding_dim:
            raw_values.extend([0.0] * (self._embedding_dim - len(raw_values)))
        elif len(raw_values) > self._embedding_dim:
            raw_values = raw_values[: self._embedding_dim]

        return self._normalize(raw_values)

    def build_team_embeddings(
        self,
        teams: list[str],
        as_of_date: date,
        source: str = "kenpom",
    ) -> None:
        """
        Build embeddings for a list of teams based on their metrics.

        Args:
            teams: List of team names
            as_of_date: Date to get metrics from
            source: Data source to use for metrics
        """
        source_table = {
            "kenpom": self._warehouse.kenpom,
            "evanmiya": self._warehouse.evanmiya,
            "barttorvik": self._warehouse.barttorvik,
        }.get(source.lower())

        if not source_table:
            raise ValueError(f"Unknown source: {source}")

        for team in teams:
            team = self._warehouse.standardize_team(team)
            snapshot = source_table.get_metrics_on_date(team, as_of_date)
            self._team_embeddings[team] = self._metrics_to_embedding(snapshot)

    def get_team_embedding(self, team: str) -> list[float]:
        """Get the embedding vector for a team."""
        team = self._warehouse.standardize_team(team)
        return self._team_embeddings.get(team, [0.0] * self._embedding_dim)

    def get_similarity(self, team_a: str, team_b: str) -> float:
        """
        Calculate cosine similarity between two teams' embeddings.
        Higher values indicate more similar playing styles.
        """
        emb_a = self.get_team_embedding(team_a)
        emb_b = self.get_team_embedding(team_b)

        dot_product = sum(a * b for a, b in zip(emb_a, emb_b))
        return dot_product  # Already normalized, so this is cosine similarity

    def find_similar_teams(
        self,
        team: str,
        n: int = 5,
    ) -> list[tuple[str, float]]:
        """Find the N most similar teams to the given team."""
        team = self._warehouse.standardize_team(team)

        similarities = []
        for other_team in self._team_embeddings:
            if other_team != team:
                sim = self.get_similarity(team, other_team)
                similarities.append((other_team, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:n]

    def get_matchup_embedding_features(
        self,
        home_team: str,
        away_team: str,
    ) -> dict[str, float]:
        """
        Create features from team embeddings for a matchup.

        Returns:
            Dictionary with embedding-based features
        """
        home_emb = self.get_team_embedding(home_team)
        away_emb = self.get_team_embedding(away_team)

        features = {}

        # Individual embedding dimensions
        for i, (h, a) in enumerate(zip(home_emb, away_emb)):
            features[f"home_emb_{i}"] = h
            features[f"away_emb_{i}"] = a
            features[f"emb_diff_{i}"] = h - a

        # Similarity score
        features["team_similarity"] = self.get_similarity(home_team, away_team)

        return features

    def export_embeddings(self) -> str:
        """Export embeddings to JSON."""
        return json.dumps(self._team_embeddings, indent=2)

    def import_embeddings(self, json_str: str) -> None:
        """Import embeddings from JSON."""
        self._team_embeddings = json.loads(json_str)


# ============================================================================
# Complete Feature Pipeline
# ============================================================================


class FeaturePipeline:
    """
    Complete feature engineering pipeline combining all components.
    """

    def __init__(self, warehouse: NCAABDataWarehouse):
        self._warehouse = warehouse
        self._exogenous = ExogenousVariableProcessor(warehouse)
        self._matchup = MatchupFeatureEngine(self._exogenous)
        self._rolling = RollingWindowCalculator(warehouse)
        self._embeddings = EntityEmbedding(warehouse)

    def build_game_features(
        self,
        home_team: str,
        away_team: str,
        game_date: date,
        include_embeddings: bool = True,
    ) -> dict[str, float | None]:
        """
        Build complete feature set for a game prediction.

        Args:
            home_team: Home team name
            away_team: Away team name
            game_date: Date of the game
            include_embeddings: Whether to include embedding features

        Returns:
            Complete feature dictionary for the game
        """
        features: dict[str, float | None] = {}

        # 1. Exogenous features (pre-game ratings)
        exog_features = self._exogenous.extract_game_features(
            home_team, away_team, game_date
        )
        features.update(exog_features)

        # 2. Matchup interaction features
        matchup_features = self._matchup.create_matchup_features(
            home_team, away_team, game_date
        )
        features.update(matchup_features)

        # 3. Rolling window features (recent form)
        rolling_features = self._rolling.calculate_game_rolling_features(
            home_team, away_team, game_date
        )
        features.update(rolling_features)

        # 4. Entity embeddings
        if include_embeddings:
            emb_features = self._embeddings.get_matchup_embedding_features(
                home_team, away_team
            )
            features.update(emb_features)

        # 5. Static features
        features["is_neutral_site"] = 0.0  # Would come from game data
        features["is_conference_game"] = 0.0  # Would come from game data
        features["is_tournament_game"] = 0.0  # Would come from game data

        return features

    def build_training_dataset(
        self,
        games: list[GameResult],
        include_embeddings: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Build a complete training dataset from historical games.

        Args:
            games: List of historical games
            include_embeddings: Whether to include embedding features

        Returns:
            List of feature dictionaries with target variables
        """
        dataset = []

        for game in games:
            features = self.build_game_features(
                game.home_team,
                game.away_team,
                game.game_date,
                include_embeddings,
            )

            # Add target variables
            features["target_home_score"] = float(game.home_score)
            features["target_away_score"] = float(game.away_score)
            features["target_total"] = float(game.home_score + game.away_score)
            features["target_spread"] = float(game.home_score - game.away_score)
            features["target_home_win"] = 1.0 if game.home_score > game.away_score else 0.0

            # Metadata (not features)
            features["_game_id"] = game.game_id
            features["_game_date"] = game.game_date.isoformat()
            features["_home_team"] = game.home_team
            features["_away_team"] = game.away_team

            dataset.append(features)

        return dataset
