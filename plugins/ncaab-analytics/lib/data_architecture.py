"""
Data Architecture Module

Implements Star Schema design for NCAAB data warehousing with:
- Game Fact Table (atomic game data)
- Metrics Dimension Tables (KenPom, EvanMiya, BartTorvik as slowly changing dimensions)
- Team Name Standardization (resolving naming discrepancies across sources)
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
import json
import re


# ============================================================================
# Team Name Standardization
# ============================================================================

# Comprehensive team name mapping for standardization across data sources
TEAM_NAME_ALIASES: dict[str, list[str]] = {
    "Alabama": ["Alabama", "Bama", "UA"],
    "Arizona": ["Arizona", "Zona", "U of A", "AZ"],
    "Arizona State": ["Arizona State", "Arizona St", "Arizona St.", "ASU"],
    "Arkansas": ["Arkansas", "Ark", "U of A"],
    "Auburn": ["Auburn", "AU"],
    "Baylor": ["Baylor", "BU"],
    "Boston College": ["Boston College", "BC", "Boston Col"],
    "BYU": ["BYU", "Brigham Young", "Brigham Young University"],
    "California": ["California", "Cal", "UC Berkeley", "Berkeley"],
    "Cincinnati": ["Cincinnati", "Cincy", "UC"],
    "Clemson": ["Clemson", "CU"],
    "Colorado": ["Colorado", "CU", "Buffs", "Buffaloes"],
    "Connecticut": ["Connecticut", "UConn", "UCONN"],
    "Creighton": ["Creighton", "CU"],
    "Duke": ["Duke", "Blue Devils"],
    "Florida": ["Florida", "UF", "Gators"],
    "Florida State": ["Florida State", "Florida St", "Florida St.", "FSU"],
    "Georgetown": ["Georgetown", "GU", "Hoyas"],
    "Georgia": ["Georgia", "UGA", "Bulldogs"],
    "Georgia Tech": ["Georgia Tech", "GT", "Georgia Institute of Technology"],
    "Gonzaga": ["Gonzaga", "Zags", "GU"],
    "Houston": ["Houston", "UH", "Cougars"],
    "Illinois": ["Illinois", "Illini", "U of I"],
    "Indiana": ["Indiana", "IU", "Hoosiers"],
    "Iowa": ["Iowa", "Hawkeyes"],
    "Iowa State": ["Iowa State", "Iowa St", "Iowa St.", "ISU"],
    "Kansas": ["Kansas", "KU", "Jayhawks"],
    "Kansas State": ["Kansas State", "Kansas St", "Kansas St.", "K-State", "KSU"],
    "Kentucky": ["Kentucky", "UK", "Wildcats"],
    "Louisville": ["Louisville", "U of L", "Cards", "Cardinals"],
    "LSU": ["LSU", "Louisiana State", "Louisiana St", "Tigers"],
    "Marquette": ["Marquette", "MU"],
    "Maryland": ["Maryland", "UMD", "Terps", "Terrapins"],
    "Memphis": ["Memphis", "U of M", "Tigers"],
    "Miami FL": ["Miami FL", "Miami (FL)", "Miami", "U", "Hurricanes"],
    "Miami OH": ["Miami OH", "Miami (OH)", "Miami Ohio", "RedHawks"],
    "Michigan": ["Michigan", "UM", "Wolverines"],
    "Michigan State": ["Michigan State", "Michigan St", "Michigan St.", "MSU", "Spartans"],
    "Minnesota": ["Minnesota", "Minn", "Gophers", "Golden Gophers"],
    "Mississippi": ["Mississippi", "Ole Miss", "OM", "Rebels"],
    "Mississippi State": ["Mississippi State", "Mississippi St", "Miss St", "MSU", "Bulldogs"],
    "Missouri": ["Missouri", "Mizzou", "MU"],
    "NC State": ["NC State", "N.C. State", "North Carolina State", "NCSU", "Wolfpack"],
    "Nebraska": ["Nebraska", "Huskers", "NU"],
    "North Carolina": ["North Carolina", "UNC", "Carolina", "Tar Heels"],
    "Northwestern": ["Northwestern", "NU", "Wildcats"],
    "Notre Dame": ["Notre Dame", "ND", "Fighting Irish"],
    "Ohio State": ["Ohio State", "Ohio St", "Ohio St.", "OSU", "Buckeyes"],
    "Oklahoma": ["Oklahoma", "OU", "Sooners"],
    "Oklahoma State": ["Oklahoma State", "Oklahoma St", "Okla St", "OSU", "Cowboys"],
    "Oregon": ["Oregon", "UO", "Ducks"],
    "Oregon State": ["Oregon State", "Oregon St", "OSU", "Beavers"],
    "Penn State": ["Penn State", "PSU", "Nittany Lions"],
    "Pittsburgh": ["Pittsburgh", "Pitt", "Panthers"],
    "Purdue": ["Purdue", "PU", "Boilermakers"],
    "Rutgers": ["Rutgers", "RU", "Scarlet Knights"],
    "Saint Johns": ["Saint Johns", "St. John's", "St Johns", "SJU", "Red Storm"],
    "San Diego State": ["San Diego State", "SDSU", "Aztecs"],
    "Seton Hall": ["Seton Hall", "SHU", "Pirates"],
    "SMU": ["SMU", "Southern Methodist", "Mustangs"],
    "South Carolina": ["South Carolina", "USC", "SC", "Gamecocks"],
    "Stanford": ["Stanford", "Cardinal"],
    "Syracuse": ["Syracuse", "Cuse", "SU", "Orange"],
    "TCU": ["TCU", "Texas Christian", "Horned Frogs"],
    "Temple": ["Temple", "TU", "Owls"],
    "Tennessee": ["Tennessee", "UT", "Vols", "Volunteers"],
    "Texas": ["Texas", "UT", "Longhorns"],
    "Texas A&M": ["Texas A&M", "TAMU", "Aggies"],
    "Texas Tech": ["Texas Tech", "TTU", "Red Raiders"],
    "UCLA": ["UCLA", "Bruins"],
    "USC": ["USC", "Southern California", "Southern Cal", "Trojans"],
    "Vanderbilt": ["Vanderbilt", "Vandy", "Commodores"],
    "Villanova": ["Villanova", "Nova", "VU", "Wildcats"],
    "Virginia": ["Virginia", "UVA", "Cavaliers", "Wahoos"],
    "Virginia Tech": ["Virginia Tech", "VT", "Hokies"],
    "Wake Forest": ["Wake Forest", "Wake", "WFU", "Demon Deacons"],
    "Washington": ["Washington", "UW", "Huskies"],
    "Washington State": ["Washington State", "Washington St", "Wazzu", "WSU", "Cougars"],
    "West Virginia": ["West Virginia", "WVU", "Mountaineers"],
    "Wisconsin": ["Wisconsin", "Wisc", "UW", "Badgers"],
    "Xavier": ["Xavier", "XU", "Musketeers"],
}


class TeamNameStandardizer:
    """
    Resolves naming discrepancies across data sources (KenPom, EvanMiya, BartTorvik).
    Implements a 'Codes Management System' for consistent team identification.
    """

    def __init__(self, custom_mappings: dict[str, list[str]] | None = None):
        """
        Initialize the standardizer with optional custom mappings.

        Args:
            custom_mappings: Additional team name mappings to merge with defaults
        """
        self._alias_to_canonical: dict[str, str] = {}
        self._canonical_names: set[str] = set()

        # Build lookup from aliases
        all_mappings = {**TEAM_NAME_ALIASES}
        if custom_mappings:
            all_mappings.update(custom_mappings)

        for canonical, aliases in all_mappings.items():
            self._canonical_names.add(canonical)
            for alias in aliases:
                # Normalize alias for lookup
                normalized = self._normalize(alias)
                self._alias_to_canonical[normalized] = canonical

    def _normalize(self, name: str) -> str:
        """Normalize team name for matching (lowercase, remove punctuation)."""
        normalized = name.lower().strip()
        normalized = re.sub(r"[^\w\s]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def standardize(self, team_name: str) -> str:
        """
        Convert any team name variant to its canonical form.

        Args:
            team_name: Raw team name from any data source

        Returns:
            Canonical team name, or original if no match found
        """
        normalized = self._normalize(team_name)

        # Direct lookup
        if normalized in self._alias_to_canonical:
            return self._alias_to_canonical[normalized]

        # Fuzzy matching for close matches
        for alias, canonical in self._alias_to_canonical.items():
            if alias in normalized or normalized in alias:
                return canonical

        # Return original if no match (with warning in production)
        return team_name

    def is_valid_team(self, team_name: str) -> bool:
        """Check if a team name can be standardized."""
        return self._normalize(team_name) in self._alias_to_canonical

    def get_all_canonical_names(self) -> list[str]:
        """Return all known canonical team names."""
        return sorted(self._canonical_names)


# ============================================================================
# Fact Table: Game Results
# ============================================================================


@dataclass
class GameResult:
    """Atomic game data representing a single game outcome."""

    game_id: str
    game_date: date
    season: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_rebounds: int = 0
    away_rebounds: int = 0
    home_assists: int = 0
    away_assists: int = 0
    home_turnovers: int = 0
    away_turnovers: int = 0
    home_fg_made: int = 0
    home_fg_attempted: int = 0
    away_fg_made: int = 0
    away_fg_attempted: int = 0
    home_3pt_made: int = 0
    home_3pt_attempted: int = 0
    away_3pt_made: int = 0
    away_3pt_attempted: int = 0
    home_ft_made: int = 0
    home_ft_attempted: int = 0
    away_ft_made: int = 0
    away_ft_attempted: int = 0
    neutral_site: bool = False
    tournament_game: bool = False
    conference_game: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "game_id": self.game_id,
            "game_date": self.game_date.isoformat(),
            "season": self.season,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "home_rebounds": self.home_rebounds,
            "away_rebounds": self.away_rebounds,
            "home_assists": self.home_assists,
            "away_assists": self.away_assists,
            "home_turnovers": self.home_turnovers,
            "away_turnovers": self.away_turnovers,
            "home_fg_made": self.home_fg_made,
            "home_fg_attempted": self.home_fg_attempted,
            "away_fg_made": self.away_fg_made,
            "away_fg_attempted": self.away_fg_attempted,
            "home_3pt_made": self.home_3pt_made,
            "home_3pt_attempted": self.home_3pt_attempted,
            "away_3pt_made": self.away_3pt_made,
            "away_3pt_attempted": self.away_3pt_attempted,
            "home_ft_made": self.home_ft_made,
            "home_ft_attempted": self.home_ft_attempted,
            "away_ft_made": self.away_ft_made,
            "away_ft_attempted": self.away_ft_attempted,
            "neutral_site": self.neutral_site,
            "tournament_game": self.tournament_game,
            "conference_game": self.conference_game,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameResult":
        """Create from dictionary."""
        data = data.copy()
        if isinstance(data["game_date"], str):
            data["game_date"] = date.fromisoformat(data["game_date"])
        return cls(**data)


class GameFactTable:
    """
    Central fact table containing individual game results.
    Represents the 'atomic data' necessary for historical analysis.
    """

    def __init__(self, standardizer: TeamNameStandardizer | None = None):
        self._games: dict[str, GameResult] = {}
        self._by_date: dict[date, list[str]] = {}
        self._by_team: dict[str, list[str]] = {}
        self._by_season: dict[int, list[str]] = {}
        self._standardizer = standardizer or TeamNameStandardizer()

    def add_game(self, game: GameResult) -> None:
        """Add a game to the fact table with standardized team names."""
        # Standardize team names
        game.home_team = self._standardizer.standardize(game.home_team)
        game.away_team = self._standardizer.standardize(game.away_team)

        self._games[game.game_id] = game

        # Index by date
        if game.game_date not in self._by_date:
            self._by_date[game.game_date] = []
        self._by_date[game.game_date].append(game.game_id)

        # Index by team
        for team in [game.home_team, game.away_team]:
            if team not in self._by_team:
                self._by_team[team] = []
            self._by_team[team].append(game.game_id)

        # Index by season
        if game.season not in self._by_season:
            self._by_season[game.season] = []
        self._by_season[game.season].append(game.game_id)

    def get_game(self, game_id: str) -> GameResult | None:
        """Retrieve a game by ID."""
        return self._games.get(game_id)

    def get_games_by_date(self, game_date: date) -> list[GameResult]:
        """Get all games on a specific date."""
        game_ids = self._by_date.get(game_date, [])
        return [self._games[gid] for gid in game_ids]

    def get_games_by_team(
        self,
        team: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[GameResult]:
        """Get all games for a team, optionally filtered by date range."""
        team = self._standardizer.standardize(team)
        game_ids = self._by_team.get(team, [])
        games = [self._games[gid] for gid in game_ids]

        if start_date:
            games = [g for g in games if g.game_date >= start_date]
        if end_date:
            games = [g for g in games if g.game_date <= end_date]

        return sorted(games, key=lambda g: g.game_date)

    def get_games_by_season(self, season: int) -> list[GameResult]:
        """Get all games in a season."""
        game_ids = self._by_season.get(season, [])
        return [self._games[gid] for gid in game_ids]

    def get_head_to_head(
        self,
        team_a: str,
        team_b: str,
        seasons: list[int] | None = None,
    ) -> list[GameResult]:
        """Get all games between two teams."""
        team_a = self._standardizer.standardize(team_a)
        team_b = self._standardizer.standardize(team_b)

        games_a = set(self._by_team.get(team_a, []))
        games_b = set(self._by_team.get(team_b, []))
        common_ids = games_a & games_b

        games = [self._games[gid] for gid in common_ids]

        if seasons:
            games = [g for g in games if g.season in seasons]

        return sorted(games, key=lambda g: g.game_date)

    def export_to_json(self) -> str:
        """Export all games to JSON."""
        return json.dumps(
            [g.to_dict() for g in self._games.values()],
            indent=2,
        )

    def import_from_json(self, json_str: str) -> None:
        """Import games from JSON."""
        games_data = json.loads(json_str)
        for gd in games_data:
            self.add_game(GameResult.from_dict(gd))


# ============================================================================
# Dimension Tables: Metrics Snapshots
# ============================================================================


@dataclass
class MetricsSnapshot:
    """
    A point-in-time snapshot of team metrics.
    Handles 'Slowly Changing Dimensions' by recording metrics as they existed
    on a specific date, avoiding data leakage from future information.
    """

    team: str
    snapshot_date: date
    source: str  # "kenpom", "evanmiya", "barttorvik"

    # Common efficiency metrics
    adj_offense: float | None = None  # Adjusted Offensive Efficiency
    adj_defense: float | None = None  # Adjusted Defensive Efficiency
    adj_tempo: float | None = None  # Adjusted Tempo (possessions/40 min)
    adj_em: float | None = None  # Adjusted Efficiency Margin

    # Ranking
    overall_rank: int | None = None
    offense_rank: int | None = None
    defense_rank: int | None = None

    # Four Factors (Offense)
    efg_pct: float | None = None  # Effective FG%
    turnover_pct: float | None = None  # Turnover %
    orb_pct: float | None = None  # Offensive Rebound %
    ftr: float | None = None  # Free Throw Rate

    # Four Factors (Defense)
    opp_efg_pct: float | None = None
    opp_turnover_pct: float | None = None
    drb_pct: float | None = None  # Defensive Rebound %
    opp_ftr: float | None = None

    # Source-specific metrics
    luck_rating: float | None = None  # KenPom Luck
    sos: float | None = None  # Strength of Schedule
    sos_remaining: float | None = None
    ncsos: float | None = None  # Non-conference SOS

    # Additional BartTorvik metrics
    barthag: float | None = None  # Probability of beating avg D1 team
    wins_above_bubble: float | None = None

    # EvanMiya specific
    bpr: float | None = None  # Bayesian Performance Rating

    # Extended attributes
    extra_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "team": self.team,
            "snapshot_date": self.snapshot_date.isoformat(),
            "source": self.source,
            "adj_offense": self.adj_offense,
            "adj_defense": self.adj_defense,
            "adj_tempo": self.adj_tempo,
            "adj_em": self.adj_em,
            "overall_rank": self.overall_rank,
            "offense_rank": self.offense_rank,
            "defense_rank": self.defense_rank,
            "efg_pct": self.efg_pct,
            "turnover_pct": self.turnover_pct,
            "orb_pct": self.orb_pct,
            "ftr": self.ftr,
            "opp_efg_pct": self.opp_efg_pct,
            "opp_turnover_pct": self.opp_turnover_pct,
            "drb_pct": self.drb_pct,
            "opp_ftr": self.opp_ftr,
            "luck_rating": self.luck_rating,
            "sos": self.sos,
            "sos_remaining": self.sos_remaining,
            "ncsos": self.ncsos,
            "barthag": self.barthag,
            "wins_above_bubble": self.wins_above_bubble,
            "bpr": self.bpr,
            "extra_metrics": self.extra_metrics,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetricsSnapshot":
        """Create from dictionary."""
        data = data.copy()
        if isinstance(data["snapshot_date"], str):
            data["snapshot_date"] = date.fromisoformat(data["snapshot_date"])
        return cls(**data)


class MetricsDimensionTable:
    """
    Dimension table for team metrics from KenPom, EvanMiya, and BartTorvik.
    Implements Slowly Changing Dimensions (Type 2) with historical snapshots.
    """

    def __init__(self, source: str, standardizer: TeamNameStandardizer | None = None):
        """
        Initialize dimension table for a specific source.

        Args:
            source: Data source name ("kenpom", "evanmiya", "barttorvik")
            standardizer: Team name standardizer
        """
        self.source = source.lower()
        self._snapshots: list[MetricsSnapshot] = []
        self._by_team_date: dict[tuple[str, date], MetricsSnapshot] = {}
        self._standardizer = standardizer or TeamNameStandardizer()

    def add_snapshot(self, snapshot: MetricsSnapshot) -> None:
        """Add a metrics snapshot, ensuring correct source."""
        if snapshot.source.lower() != self.source:
            raise ValueError(
                f"Snapshot source '{snapshot.source}' doesn't match "
                f"table source '{self.source}'"
            )

        # Standardize team name
        snapshot.team = self._standardizer.standardize(snapshot.team)

        self._snapshots.append(snapshot)
        key = (snapshot.team, snapshot.snapshot_date)
        self._by_team_date[key] = snapshot

    def get_metrics_on_date(
        self,
        team: str,
        target_date: date,
    ) -> MetricsSnapshot | None:
        """
        Get team metrics as they existed on a specific date.
        Returns the most recent snapshot on or before the target date.
        This prevents data leakage from future information.
        """
        team = self._standardizer.standardize(team)

        # Direct lookup first
        if (team, target_date) in self._by_team_date:
            return self._by_team_date[(team, target_date)]

        # Find most recent snapshot before target date
        team_snapshots = [
            s for s in self._snapshots if s.team == team and s.snapshot_date <= target_date
        ]

        if not team_snapshots:
            return None

        return max(team_snapshots, key=lambda s: s.snapshot_date)

    def get_latest_metrics(self, team: str) -> MetricsSnapshot | None:
        """Get the most recent metrics for a team."""
        team = self._standardizer.standardize(team)
        team_snapshots = [s for s in self._snapshots if s.team == team]

        if not team_snapshots:
            return None

        return max(team_snapshots, key=lambda s: s.snapshot_date)

    def get_all_snapshots_for_team(self, team: str) -> list[MetricsSnapshot]:
        """Get full history of snapshots for a team."""
        team = self._standardizer.standardize(team)
        return sorted(
            [s for s in self._snapshots if s.team == team],
            key=lambda s: s.snapshot_date,
        )

    def get_snapshot_dates(self) -> list[date]:
        """Get all unique snapshot dates."""
        return sorted(set(s.snapshot_date for s in self._snapshots))


# ============================================================================
# Data Warehouse: Unified Interface
# ============================================================================


class NCAABDataWarehouse:
    """
    Unified data warehouse combining fact and dimension tables.
    Provides a single interface for accessing game data with metrics context.
    """

    def __init__(self, standardizer: TeamNameStandardizer | None = None):
        self._standardizer = standardizer or TeamNameStandardizer()
        self.games = GameFactTable(self._standardizer)
        self.kenpom = MetricsDimensionTable("kenpom", self._standardizer)
        self.evanmiya = MetricsDimensionTable("evanmiya", self._standardizer)
        self.barttorvik = MetricsDimensionTable("barttorvik", self._standardizer)

    def get_game_with_metrics(
        self,
        game: GameResult,
    ) -> dict[str, Any]:
        """
        Get a game with all available pre-game metrics.
        Metrics are retrieved as of the game date to prevent data leakage.
        """
        game_date = game.game_date

        # Get metrics for each team as of game date
        home_kenpom = self.kenpom.get_metrics_on_date(game.home_team, game_date)
        home_miya = self.evanmiya.get_metrics_on_date(game.home_team, game_date)
        home_torvik = self.barttorvik.get_metrics_on_date(game.home_team, game_date)

        away_kenpom = self.kenpom.get_metrics_on_date(game.away_team, game_date)
        away_miya = self.evanmiya.get_metrics_on_date(game.away_team, game_date)
        away_torvik = self.barttorvik.get_metrics_on_date(game.away_team, game_date)

        return {
            "game": game.to_dict(),
            "home_metrics": {
                "kenpom": home_kenpom.to_dict() if home_kenpom else None,
                "evanmiya": home_miya.to_dict() if home_miya else None,
                "barttorvik": home_torvik.to_dict() if home_torvik else None,
            },
            "away_metrics": {
                "kenpom": away_kenpom.to_dict() if away_kenpom else None,
                "evanmiya": away_miya.to_dict() if away_miya else None,
                "barttorvik": away_torvik.to_dict() if away_torvik else None,
            },
        }

    def get_matchup_data(
        self,
        home_team: str,
        away_team: str,
        target_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive matchup data for two teams.
        Useful for prediction without an existing game record.
        """
        if target_date is None:
            target_date = date.today()

        home_team = self._standardizer.standardize(home_team)
        away_team = self._standardizer.standardize(away_team)

        return {
            "home_team": home_team,
            "away_team": away_team,
            "target_date": target_date.isoformat(),
            "home_metrics": {
                "kenpom": (
                    self.kenpom.get_metrics_on_date(home_team, target_date)
                    or {}
                ),
                "evanmiya": (
                    self.evanmiya.get_metrics_on_date(home_team, target_date)
                    or {}
                ),
                "barttorvik": (
                    self.barttorvik.get_metrics_on_date(home_team, target_date)
                    or {}
                ),
            },
            "away_metrics": {
                "kenpom": (
                    self.kenpom.get_metrics_on_date(away_team, target_date)
                    or {}
                ),
                "evanmiya": (
                    self.evanmiya.get_metrics_on_date(away_team, target_date)
                    or {}
                ),
                "barttorvik": (
                    self.barttorvik.get_metrics_on_date(away_team, target_date)
                    or {}
                ),
            },
            "historical_matchups": [
                g.to_dict()
                for g in self.games.get_head_to_head(home_team, away_team)
            ],
        }

    def standardize_team(self, team_name: str) -> str:
        """Standardize a team name."""
        return self._standardizer.standardize(team_name)
