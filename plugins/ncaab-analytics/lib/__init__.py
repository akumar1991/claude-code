"""
NCAAB Analytics Library

Advanced NCAA Basketball analysis using KenPom, EvanMiya, and BartTorvik metrics
with Global Forecasting Models (GFM) and ensemble stacking.
"""

from .data_architecture import (
    GameFactTable,
    MetricsDimensionTable,
    TeamNameStandardizer,
    NCAABDataWarehouse,
)
from .feature_engineering import (
    MatchupFeatureEngine,
    RollingWindowCalculator,
    EntityEmbedding,
    ExogenousVariableProcessor,
)
from .modeling import (
    GlobalForecastingModel,
    StackingEnsemble,
    BaseLearnersFactory,
)
from .validation import (
    WalkForwardValidator,
    ProbabilisticForecaster,
    HierarchicalValidator,
)

__version__ = "1.0.0"
__all__ = [
    "GameFactTable",
    "MetricsDimensionTable",
    "TeamNameStandardizer",
    "NCAABDataWarehouse",
    "MatchupFeatureEngine",
    "RollingWindowCalculator",
    "EntityEmbedding",
    "ExogenousVariableProcessor",
    "GlobalForecastingModel",
    "StackingEnsemble",
    "BaseLearnersFactory",
    "WalkForwardValidator",
    "ProbabilisticForecaster",
    "HierarchicalValidator",
]
