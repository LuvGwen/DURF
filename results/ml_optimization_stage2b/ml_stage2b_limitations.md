# ML Stage 2B Limitations

- This stage is diagnostic and does not retrain the frozen model.
- The default final live run uses 1,600 complete games, which is lower than the preferred 25,000-game design in the full pre-plan.
- Candidate and decision rows are not independent games.
- Single-intervention rollouts are sampled disagreement states and should be interpreted as mechanism diagnostics.
- Selective override thresholds are fixed before final-test evaluation but remain exploratory.
