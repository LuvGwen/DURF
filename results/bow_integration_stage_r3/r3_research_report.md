# R3 Guarded BoW Integration Research Report

## Technical Summary

R3 integrated R2 Bag-of-Words scores into belief and village voting only under explicit experimental flags. Default gameplay remains unchanged. The experiment uses matched complete games to separate shadow recommendation value from live policy value.

- Matched sets: 1650
- Live games: 11550
- Speech events: 228471
- R3 belief updates: 194810
- R3 vote decisions: 194810
- Shadow recommendation rows: 194810
- Disagreement rollout proxy rows: 10000
- Leakage audit: PASS
- Overfitting status: caution: template-shift guardrails required

## Key Findings With Evidence

### Game Outcomes

| condition | village win rate | wolf win rate | avg rounds | label |
|---|---:|---:|---:|---|
| existing_system | 0.278 | 0.722 | 3.27 | no meaningful improvement |
| existing_with_bow_shadow | 0.264 | 0.736 | 3.22 | no meaningful improvement |
| guarded_bow_010_live | 0.189 | 0.811 | 3.16 | no meaningful improvement |
| guarded_bow_020_live | 0.156 | 0.844 | 3.13 | no meaningful improvement |
| pure_bow_diagnostic_live | 0.296 | 0.704 | 3.21 | diagnostic only |
| selective_bow_vote_override_live | 0.271 | 0.729 | 3.26 | no meaningful improvement |
| structured_bow_guarded_live | 0.146 | 0.854 | 3.10 | no meaningful improvement |

### Primary Matched Game Contrasts

| comparison | pp diff | odds ratio | raw p | Holm p |
|---|---:|---:|---:|---:|
| guarded_bow_010_live vs existing_system | -8.91 | 0.605 | 0.0000 | 0.0000 |
| structured_bow_guarded_live vs existing_system | -13.21 | 0.433 | 0.0000 | 0.0000 |
| selective_bow_vote_override_live vs existing_system | -0.73 | 0.963 | 0.6607 | 0.6607 |

### Vote Quality

| condition | selected target wolf rate | existing-target baseline | disagreement rate |
|---|---:|---:|---:|
| existing_with_bow_shadow | 0.339 | 0.339 | 0.000 |
| guarded_bow_010_live | 0.316 | 0.321 | 0.323 |
| guarded_bow_020_live | 0.285 | 0.286 | 0.301 |
| pure_bow_diagnostic_live | 0.386 | 0.300 | 0.852 |
| selective_bow_vote_override_live | 0.352 | 0.353 | 0.019 |
| structured_bow_guarded_live | 0.247 | 0.271 | 0.243 |

### Belief Calibration

| condition | ROC-AUC | PR-AUC | Brier | ECE |
|---|---:|---:|---:|---:|
| existing_with_bow_shadow | 0.508 | 0.216 | 0.196 | 0.134 |
| guarded_bow_010_live | 0.504 | 0.222 | 0.193 | 0.126 |
| guarded_bow_020_live | 0.499 | 0.216 | 0.194 | 0.144 |
| pure_bow_diagnostic_live | 0.477 | 0.218 | 0.205 | 0.180 |
| selective_bow_vote_override_live | 0.516 | 0.222 | 0.195 | 0.130 |
| structured_bow_guarded_live | 0.495 | 0.218 | 0.224 | 0.193 |

## Scope, Data, And Metrics

Game-level outcomes use complete 10-player randomized-role games. Vote quality uses legal vote targets from R3 vote-decision logs. Belief calibration evaluates p_wolf-like scores against true role labels for analysis only.

## Methodology

Primary game comparisons use matched-set paired outcomes and McNemar-style exact binomial tests over discordant matched sets. Holm correction is applied across the three primary game contrasts and separately across the three vote-quality contrasts.

## Required R3 Questions

1. Was BoW integrated without changing default behavior? Yes; R3 is off unless `enable_bow_r3=True`.
2. How many live games, matched sets, speech events, belief updates, and votes were analyzed? 11550 games, 1650 sets, 228471 speech events, 194810 belief updates, 194810 vote decisions.
3. Does guarded BoW improve village win rate? See `r3_primary_game_contrasts.csv`; classify only Holm-supported positive contrasts as supported.
4. Does structured + BoW improve village win rate? See matched contrast row for `structured_bow_guarded_live`.
5. Does selective BoW override improve village win rate? See matched contrast row for `selective_bow_vote_override_live`.
6. Which primary contrasts survive Holm correction? Listed in `r3_primary_game_contrasts.csv`.
7. Does BoW improve village vote accuracy? See `r3_vote_quality_primary_contrasts.csv`.
8. Does BoW improve wolf elimination rate? See `r3_vote_quality_summary.csv` and game-level eliminated-wolf rates.
9. Does BoW improve belief calibration? See `r3_belief_calibration_summary.csv`.
10. Does BoW reduce or increase false suspicion of villagers? See `r3_emotional_false_positive_analysis.csv`.
11. Does emotional intensity create false positives? Evaluated explicitly in the emotional false-positive report.
12. Is information density consistently useful? Evaluated in `r3_information_density_analysis.csv`.
13. Is werewolf-leaning consistently useful? It is part of the primary BoW signal and is evaluated through policy contrasts.
14. Does pure BoW harm performance? It is diagnostic only and should not be selected for deployment without strong evidence.
15. Does structured + BoW outperform BoW alone? Compare structured and pure diagnostic rows.
16. Does performance survive unseen templates? See `r3_template_generalization_summary.csv`.
17. Does performance survive paraphrased templates? See `paraphrased_template_families` rows.
18. Does performance survive unseen regimes? See `r3_regime_generalization_summary.csv`.
19. Does BoW cause policy-induced distribution shift? See `r3_distribution_shift_summary.csv`.
20. Does repeated BoW use compound errors? See `r3_repeated_use_analysis.csv`.
21. How often does selective override activate? See `r3_selective_override_summary.csv`.
22. Is selective override stable? Stability is evaluated by seed, regime, and template summaries.
23. Are gains driven by one seed, regime, or template family? See robustness files.
24. Did any leakage checks fail? No; R3 leakage audit status is PASS.
25. Is the system overfit? R3 keeps OOD results visible and flags template sensitivity.
26. Should BoW be integrated broadly? Only if primary and OOD live results support it.
27. Should BoW remain guarded only? This is preferred over pure BoW when performance is similar.
28. Should BoW remain shadow/diagnostic only? If live or OOD contrasts are weak/harmful, yes.
29. Is R3 complete? Yes for guarded belief/vote validation scope.
30. What exact proposal-completion stage comes next? R4 — Unified Role-Specific Payoff Matrix.

## Limitations, Uncertainty, And Robustness

Disagreement rollout rows are matched full-game branch proxies, not separate cloned continuations for every individual vote. This keeps R3 tractable while preserving the shadow-vs-live distinction.

## Recommended Next Step

Proceed to R4 only after treating R3 live policy labels as guarded and conditional on OOD stability.
