---
description: Train and validate the NCAAB prediction model using walk-forward validation
arguments:
  - name: data_path
    description: Path to training data file (CSV or JSON)
    required: true
  - name: target
    description: Target variable (spread, total, home_win)
    required: false
---

# Train NCAAB Prediction Model

Train a Global Forecasting Model with stacking ensemble using walk-forward validation.

## Parameters
- **Data Path**: $ARGUMENTS.data_path
- **Target Variable**: $ARGUMENTS.target (default: spread)

## Training Pipeline

### Step 1: Load and Validate Data
```python
import json
from pathlib import Path
from lib import NCAABDataWarehouse, FeaturePipeline

# Load data from file
data_path = Path("$ARGUMENTS.data_path")
# Parse and load into warehouse
```

### Step 2: Build Feature Pipeline
- Extract exogenous variables from all sources
- Create matchup interaction features
- Calculate rolling window statistics
- Build entity embeddings

### Step 3: Configure Model
```python
from lib import (
    GlobalForecastingModel,
    StackingEnsemble,
    BaseLearnersFactory,
)

# Create ensemble with all base learners
ensemble = StackingEnsemble(
    base_learners=BaseLearnersFactory.create_all_base_learners(),
    meta_model=GlobalForecastingModel(
        n_estimators=100,
        max_depth=6,
    ),
)
```

### Step 4: Walk-Forward Validation
```python
from lib import WalkForwardValidator

validator = WalkForwardValidator(
    min_train_days=60,
    test_window_days=14,
    step_days=7,
)

result = validator.validate(ensemble, training_data, "$ARGUMENTS.target")
```

### Step 5: Report Results

## Expected Output

### Validation Report
```
================================================
WALK-FORWARD VALIDATION REPORT
================================================

OVERALL METRICS:
  MAE:      X.XX
  RMSE:     X.XX
  Coverage: XX.X%

FOLD DETAILS:
[Details for each temporal fold]
```

### Feature Importance
Top 10 most important features for prediction

### Source Reliability
Which expert system (KenPom, Torvik, Miya) is most trusted by the meta-model

### Model Export
Save trained model to JSON for future predictions
