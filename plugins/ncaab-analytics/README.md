# NCAAB Analytics Plugin

Advanced NCAA Basketball analysis using KenPom, EvanMiya, and BartTorvik metrics with Global Forecasting Models (GFM) and ensemble stacking.

## Overview

This plugin implements a comprehensive NCAAB prediction pipeline based on modern time series forecasting and ensemble learning principles:

1. **Star Schema Data Architecture**: Structured data warehouse with fact tables (games) and dimension tables (metrics snapshots)
2. **Feature Engineering**: Matchup interaction features, rolling windows, and entity embeddings
3. **Global Forecasting Model**: Single model trained on all games for cross-learning
4. **Stacking Ensemble**: Meta-model combining KenPom, EvanMiya, and BartTorvik predictions
5. **Walk-Forward Validation**: Time series cross-validation preventing lookahead bias
6. **Probabilistic Forecasting**: Full probability distributions, not just point predictions

## Installation

This plugin is included in the Claude Code plugins directory. To use it:

```bash
# The plugin is already available in plugins/ncaab-analytics/
# Import the library modules in your Python code
```

## Architecture

### Data Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   KenPom    │    │  EvanMiya   │    │ BartTorvik  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌──────────────────────────────────────────────────┐
│           Team Name Standardization              │
│         (Codes Management System)                │
└──────────────────────┬───────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  KenPom     │ │  EvanMiya   │ │ BartTorvik  │
│  Dimension  │ │  Dimension  │ │  Dimension  │
│   Table     │ │   Table     │ │   Table     │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Game Fact      │
              │  Table          │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Feature         │
              │ Engineering     │
              └────────┬────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Matchup     │ │ Rolling     │ │ Entity      │
│ Features    │ │ Windows     │ │ Embeddings  │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Stacking        │
              │ Ensemble        │
              │ (Meta-Model)    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Probabilistic   │
              │ Prediction      │
              └─────────────────┘
```

### Module Structure

```
lib/
├── __init__.py              # Package exports
├── data_architecture.py     # Star schema implementation
│   ├── TeamNameStandardizer # Resolves naming discrepancies
│   ├── GameFactTable        # Central fact table for games
│   ├── MetricsDimensionTable # Slowly changing dimensions
│   └── NCAABDataWarehouse   # Unified interface
├── feature_engineering.py   # Feature creation
│   ├── ExogenousVariableProcessor # Pre-game ratings
│   ├── MatchupFeatureEngine # Interaction features
│   ├── RollingWindowCalculator # Recent form
│   ├── EntityEmbedding      # Team similarity vectors
│   └── FeaturePipeline      # Complete pipeline
├── modeling.py              # Prediction models
│   ├── GlobalForecastingModel # GFM implementation
│   ├── ExpertSystemPredictor # KenPom/Torvik/Miya wrapper
│   ├── StackingEnsemble     # Meta-model
│   └── PredictionPipeline   # End-to-end prediction
└── validation.py            # Validation framework
    ├── WalkForwardValidator # Time series CV
    ├── ProbabilisticForecaster # Quantile regression
    ├── HierarchicalValidator # Clustered errors
    └── ValidationSuite      # Complete validation
```

## Usage

### Basic Matchup Analysis

```python
from datetime import date
from lib import (
    NCAABDataWarehouse,
    FeaturePipeline,
    StackingEnsemble,
)

# Initialize
warehouse = NCAABDataWarehouse()
pipeline = FeaturePipeline(warehouse)
ensemble = StackingEnsemble()

# Build features for a matchup
features = pipeline.build_game_features(
    home_team="Duke",
    away_team="North Carolina",
    game_date=date.today(),
)

# Get prediction with explanation
result = ensemble.explain_prediction(features)
print(f"Predicted spread: {result['ensemble_prediction']['point']:.1f}")
print(f"Most trusted source: {result['most_trusted_source']}")
```

### Training a Model

```python
from lib import (
    NCAABDataWarehouse,
    FeaturePipeline,
    StackingEnsemble,
    WalkForwardValidator,
)

# Load historical data into warehouse
warehouse = NCAABDataWarehouse()
# ... add games and metrics snapshots

# Build training dataset
pipeline = FeaturePipeline(warehouse)
games = warehouse.games.get_games_by_season(2024)
training_data = pipeline.build_training_dataset(games)

# Train ensemble with walk-forward validation
ensemble = StackingEnsemble()
validator = WalkForwardValidator(
    min_train_days=60,
    test_window_days=14,
)

result = validator.validate(ensemble, training_data)
print(validator.generate_report(result))
```

### Finding Betting Edges

```python
from lib import ProbabilisticForecaster

# Train forecaster
forecaster = ProbabilisticForecaster()
forecaster.fit(training_X, training_y)

# Analyze a line
spread_line = -3.5  # Duke -3.5
pred = forecaster.predict([game_features])[0]

# Probability of covering
prob_duke_covers = pred.prob_under(spread_line)
prob_unc_covers = pred.prob_over(spread_line)

# Calculate edge (need 52.4% to break even at -110)
edge = prob_unc_covers - 0.524
if edge > 0.03:  # 3% edge threshold
    print(f"Edge on UNC +3.5: {edge*100:.1f}%")
```

## Key Concepts

### Global Forecasting Model (GFM)

Instead of training 360+ separate models (one per team), we train a single model on ALL historical games. This enables **cross-learning**: the model learns how ANY team with certain characteristics performs against ANY opponent with certain characteristics, even if those specific teams have never played.

### Slowly Changing Dimensions

Metrics change throughout the season. We store metrics as **snapshots** on specific dates. When predicting a game, we use metrics **as they existed on the game date**, not end-of-season values. This prevents data leakage.

### Stacking Ensemble

Each expert system (KenPom, Torvik, Miya) has strengths in different situations:
- KenPom may be better for late-season games
- Torvik may be better for tempo-sensitive matchups
- Miya may be better for player-dependent analysis

The meta-model learns **when to trust which source**.

### Walk-Forward Validation

Never use random train/test splits for time series data. Instead:
- Train on Nov-Jan, test on Feb
- Train on Nov-Feb, test on March
- Etc.

This simulates real forecasting conditions and prevents looking into the future.

## Slash Commands

- `/analyze-matchup <home_team> <away_team>`: Full matchup breakdown
- `/find-edges [min_edge]`: Find betting edges for today's games
- `/train-model <data_path> [target]`: Train and validate model

## Agents

- **matchup-analyzer**: Comprehensive matchup analysis
- **model-trainer**: ML model training and validation
- **betting-edge-finder**: Identify value bets

## Data Requirements

To use this plugin, you need:

1. **Game Results**: Historical game outcomes with box score stats
2. **KenPom Data**: Efficiency ratings, tempo, four factors
3. **BartTorvik Data**: T-Rank ratings, BARTHAG, WAB
4. **EvanMiya Data**: BPR ratings, offensive/defensive metrics

Data should be loaded into the warehouse with proper date snapshots.

## References

This implementation is based on principles from:
- *Modern Time Series Forecasting with Python* (GFM, feature engineering)
- *The Data Model Resource Book* (Star schema, dimension tables)
- *Statistics Done Wrong* (Pseudoreplication, proper validation)
- *The Art of Data Science* (Backtesting, model evaluation)
