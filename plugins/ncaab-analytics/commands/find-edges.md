---
description: Find betting edges for today's NCAAB games by comparing model predictions to betting lines
arguments:
  - name: min_edge
    description: Minimum edge percentage to report (default 3)
    required: false
---

# Find NCAAB Betting Edges

Scan today's NCAAB games to find potential betting edges where the model probability differs significantly from the implied odds.

## Parameters
- **Minimum Edge**: $ARGUMENTS.min_edge% (default 3%)

## Analysis Process

1. **Get Today's Games**
   - Fetch today's NCAAB schedule
   - Get current betting lines (spreads and totals)

2. **For Each Game**
   - Build complete feature set (exogenous variables, matchup features, rolling windows)
   - Generate probabilistic prediction
   - Calculate probability of covering spread
   - Compare to implied probability (52.4% for -110)

3. **Rank by Edge**
   - Sort all potential bets by edge size
   - Filter to games meeting minimum edge threshold
   - Flag any red flags (sharp line movement, injury news)

## Output Format

### Top Edges Found

| Game | Line | Model | Prob | Edge | Action |
|------|------|-------|------|------|--------|
| Duke @ UNC | UNC +3.5 | Duke -2.1 | 56.8% | +4.4% | Lean |
| Kansas @ Baylor | Kansas -1.5 | Kansas -4.2 | 61.2% | +8.8% | Bet |

### Detailed Analysis for Top 3 Edges

For each top edge, provide:
- Full matchup breakdown
- Why model differs from line
- Key uncertainties
- Suggested bet size (Kelly fraction)

### Red Flags
- List any games with concerning factors
- Sharp line movement
- Injury reports
- Model uncertainty warnings

## Risk Management

Always remind:
- These are edges, not guarantees
- Use proper bankroll management
- Half Kelly recommended for safety
- Track results for calibration
