---
description: Analyze an NCAAB matchup between two teams using advanced metrics
arguments:
  - name: home_team
    description: Home team name
    required: true
  - name: away_team
    description: Away team name
    required: true
---

# NCAAB Matchup Analysis

Analyze the matchup between **$ARGUMENTS.home_team** (home) and **$ARGUMENTS.away_team** (away).

## Analysis Steps

1. **Retrieve Current Metrics**
   - Get KenPom ratings for both teams
   - Get EvanMiya ratings for both teams
   - Get BartTorvik ratings for both teams

2. **Build Matchup Features**
   - Calculate efficiency margin delta (consensus across sources)
   - Analyze tempo matchup
   - Compare offensive strengths vs defensive weaknesses
   - Evaluate four factors matchups

3. **Historical Context**
   - Recent head-to-head results
   - Similar style matchups (using entity embeddings)
   - Performance trends (rolling windows)

4. **Generate Prediction**
   - Point spread prediction with 90% confidence interval
   - Win probability
   - Source reliability in this context

## Output Format

Provide a comprehensive matchup report including:

### Team Comparison Table
| Metric | $ARGUMENTS.home_team | $ARGUMENTS.away_team | Advantage |
|--------|---------------------|---------------------|-----------|
| KenPom AdjEM | | | |
| BartTorvik AdjEM | | | |
| EvanMiya BPR | | | |
| Adj Offense | | | |
| Adj Defense | | | |
| Adj Tempo | | | |

### Key Matchup Factors
1. Factor 1
2. Factor 2
3. Factor 3

### Prediction
- **Spread**: X.X (90% CI: X.X to X.X)
- **Total**: X.X (90% CI: X.X to X.X)
- **$ARGUMENTS.home_team Win Probability**: XX%

### Source Consensus
- KenPom says: ...
- Torvik says: ...
- Miya says: ...
- Model confidence in each source for this matchup type

Use the ncaab-analytics library modules to perform the analysis.
