# DURF Werewolf Simulation: ML Stage 2A Research Report

## 1. Research Background

This stage evaluates whether a frozen machine-learning wolf night-kill policy can improve live game outcomes in the DURF Werewolf simulation. Earlier stages established Werewolf as a controlled hidden-information social-deduction environment with speech signals, belief updates, role actions, deception, credibility costs, speaker memory, risk preferences, seat-position diagnostics, and physically symmetric replay validation.

The central research problem is not only whether a model can predict attractive actions offline, but whether a learned policy remains beneficial when inserted into the full stochastic game loop. In this setting, wolf win rate is the primary team-level outcome, and night-kill targeting is a strategic decision that can influence information flow, seer survival, witch/hunter value, and later voting.

## 2. Connection To Prior Stages

ML Stage 1 created observation-safe decision logs and baseline machine-learning models for seer checks, wolf kills, and day votes. Its village-vote identity model appeared very strong in an ordinary row split, with a reported ROC-AUC of 0.9458. ML Stage 1.5 then introduced grouped splits and full-state rollout validation, showing that the Stage 1 identity signal was too optimistic: the village-vote final-test ROC-AUC fell to 0.6679, only slightly above the existing `p_wolf` baseline at 0.6586.

ML Stage 1.5 also showed that surrogate action-value models had weak alignment with full rollouts. The wolf-kill surrogate-to-full Spearman correlation was only 0.0718, classified as weak validity. However, a validation shadow policy suggested that the learned wolf-kill recommendation might outperform the existing rule, which motivated this live-game test.

This stage also builds on the non-ML positional experiments:

- Randomized-role seer-position analysis found no statistically supported edge-priority advantage after roles were randomized across seats.
- Structured seer search found weak but promising support for diversified checking paths, while behaviorally exploitative strategies such as `highest_p_wolf` and `highest_suspicion` were statistically worse than random.
- Seat-order-neutral and physical-direction replay experiments validated that displayed labels and physical mirror transformations did not introduce engine artifacts.

Together, these prior results made live, matched-policy validation necessary before claiming that an ML action selector improves actual gameplay.

## 3. Previous Hypothesis

The previous ML Stage 1.5 hypothesis was:

> A model selected using full-state rollout validation can identify wolf night-kill targets that improve the wolf team's expected outcome compared with the existing hand-coded wolf-kill rule.

The Stage 1.5 shadow result was encouraging but not definitive. The selected wolf-kill model showed positive validation action value under shadow rollout evaluation, but that evaluation still substituted actions into sampled decision states rather than running fully independent complete games under the frozen policy.

## 4. Current Pre-Specified Hypotheses

The current Stage 2A hypotheses were:

H1: A frozen ML wolf-kill policy will produce a higher live wolf win rate than the existing rule policy.

H2: A 50/50 hybrid between the ML model and the existing rule will be at least competitive with the existing rule and may reduce pure-model risk.

H3: A small epsilon-greedy ML policy will preserve most of the ML benefit while reducing brittleness.

H4: If the learned policy generalizes, shadow policy value and live complete-game outcomes should point in the same direction.

## 5. Experimental Design

The experiment used a matched live policy comparison. For each base game configuration, multiple wolf-kill policies were evaluated under the same high-level seed schedule where possible:

- `existing_rule`
- `frozen_ml`
- `frozen_hybrid_50_50`
- `frozen_ml_epsilon_010`

The primary outcome was live complete-game wolf win rate. Secondary outcomes included average rounds, successful night kills, special-role kills, seer kills, witch kills, hunter kills, hunter retaliation, vote-control proxy, policy agreement with the existing rule, regime robustness, seed robustness, and distribution-shift diagnostics.

No new game mechanisms were introduced in this report. The report summarizes existing ML Stage 2A artifacts already generated under `results/ml_optimization_stage2a/`.

## 6. Algorithm And Model Implementation

The ML policy is a frozen standard-library ridge action-value model trained from observation-safe wolf-kill candidate rows. At live decision time, it scores legal wolf night-kill candidates using public and state-derived features available to the policy. The policy variants are:

- `frozen_ml`: choose the candidate with the highest frozen ML action value.
- `frozen_hybrid_50_50`: combine ML score and existing-rule score with equal weight.
- `frozen_ml_epsilon_010`: usually follow the frozen ML action but allow a 10% exploration branch.
- `existing_rule`: the original hand-coded wolf-kill target rule.

The frozen model manifest hash is `3636ee12b35a57bbe8811b59ccf2c37a2bfec25ced6170ee3f51615da6f64f83`. The model artifact hash is `f3c5e60275eea04c4a03e15a21aab2713e86a4e2b446ff0fbf9b194e90ae124b`.

## 7. Dataset And Effective Independent Sample Size

The Stage 2A live experiment generated:

| Data component | Count |
|---|---:|
| Shadow source games | 105 |
| Shadow decision states | 105 |
| Shadow candidate rows | 420 |
| Shadow rollout simulations | 2,940 |
| Live complete games | 800 |
| Live matched sets | 200 |
| Live decision rows | 2,600 |
| Live candidate prediction rows | 14,380 |

The primary independent unit for live policy inference is the matched base game set, not the candidate prediction row. The live policy comparison used 200 matched sets and 800 completed games.

## 8. Raw Row Count Versus Independent Units

Raw row counts are useful for diagnostics but should not be treated as independent observations:

- `wolf_kill_live_game_level_raw.csv`: 800 live complete-game rows.
- `wolf_kill_live_decision_raw.csv`: 2,600 decision rows.
- `wolf_kill_policy_predictions_raw.csv`: 14,380 candidate prediction rows.
- `wolf_kill_shadow_candidate_raw.csv`: 420 shadow candidate rows.
- `wolf_kill_shadow_decision_raw.csv`: 105 shadow decision rows.

The formal primary comparison uses the 200 matched sets in `wolf_kill_primary_contrasts.csv`. Treating candidate rows as independent would overstate precision because multiple candidates share the same decision state and multiple decisions occur inside the same game.

## 9. Validation And Data-Integrity Checks

The Stage 2A audit artifacts report:

- The model was frozen before live evaluation.
- The live final seeds were separated from the development seeds.
- Feature computation used observation-safe state information.
- Candidate prediction rows were linked to legal wolf-kill targets.
- The experiment produced policy-level, matched-pair, seed-level, regime-level, distribution-shift, coefficient, and failure-case outputs.

Development seeds were 42-49 for training and 50-51 for validation. Stage 1.5 final seeds 52-56 were excluded from live final evaluation. Live final seeds were 100-119.

## 10. Data Analysis Methods

The analysis uses:

- Descriptive policy summaries for live wolf win rate, village win rate, rounds, successful night kills, and special-role kills.
- Wilson-style 95% confidence intervals for policy-level wolf win rates as reported in the live summary.
- Matched policy contrasts against `existing_rule`.
- McNemar-style discordant-set comparisons for matched binary outcomes.
- Odds ratios based on discordant matched outcomes.
- Holm correction for multiple comparisons across three policy-vs-existing contrasts.
- Seed-level robustness summaries.
- Behavioral-regime robustness summaries.
- Distribution-shift diagnostics based on feature ranges and standardized feature distances.
- Overfitting diagnostics comparing shadow improvement with live outcome differences.
- Failure-case inspection for selected ML policy decisions.

## 11. Descriptive Results

Live complete-game results:

| Policy | Games | Wolf wins | Village wins | Wolf win rate | 95% CI | Avg rounds | Avg successful night kills | Avg special role kills |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| existing_rule | 200 | 139 | 61 | 69.50% | 63.12%-75.88% | 3.23 | 2.365 | 2.180 |
| frozen_ml | 200 | 122 | 78 | 61.00% | 54.24%-67.76% | 3.265 | 2.430 | 1.030 |
| frozen_hybrid_50_50 | 200 | 116 | 84 | 58.00% | 51.16%-64.84% | 3.250 | 2.405 | 1.015 |
| frozen_ml_epsilon_010 | 200 | 122 | 78 | 61.00% | 54.24%-67.76% | 3.255 | 2.430 | 1.025 |

The existing rule had the highest observed wolf win rate. All frozen ML variants had lower wolf win rates than the existing rule.

## 12. Formal Statistical Inference

Primary matched contrasts against `existing_rule`:

| Contrast | Policy wolf win rate | Existing wolf win rate | Difference | 95% CI for difference | Discordant policy win / existing loss | Discordant policy loss / existing win | Odds ratio | Raw p | Holm p |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| frozen_ml vs existing_rule | 61.00% | 69.50% | -8.50 pp | -16.08 to -0.92 pp | 22 | 39 | 0.570 | 0.0396 | 0.0792 |
| frozen_hybrid_50_50 vs existing_rule | 58.00% | 69.50% | -11.50 pp | -18.04 to -4.96 pp | 12 | 35 | 0.352 | 0.0011 | 0.0033 |
| frozen_ml_epsilon_010 vs existing_rule | 61.00% | 69.50% | -8.50 pp | -16.21 to -0.79 pp | 23 | 40 | 0.580 | 0.0430 | 0.0792 |

After Holm correction, the hybrid policy was statistically significantly worse than the existing rule. The pure ML and epsilon-greedy variants were directionally worse, with raw p-values below 0.05 but adjusted p-values above 0.05.

## 13. Effect Sizes

The effect sizes are practically meaningful because they are measured in live wolf win-rate percentage points:

- `frozen_ml`: -8.50 percentage points versus existing.
- `frozen_hybrid_50_50`: -11.50 percentage points versus existing.
- `frozen_ml_epsilon_010`: -8.50 percentage points versus existing.

Discordant matched odds ratios are all below 1, indicating fewer matched-set wins than the existing rule:

- `frozen_ml`: OR 0.570.
- `frozen_hybrid_50_50`: OR 0.352.
- `frozen_ml_epsilon_010`: OR 0.580.

## 14. Confidence Intervals

Policy-level wolf win-rate confidence intervals:

- `existing_rule`: 63.12%-75.88%.
- `frozen_ml`: 54.24%-67.76%.
- `frozen_hybrid_50_50`: 51.16%-64.84%.
- `frozen_ml_epsilon_010`: 54.24%-67.76%.

Matched difference confidence intervals:

- `frozen_ml`: -16.08 to -0.92 percentage points.
- `frozen_hybrid_50_50`: -18.04 to -4.96 percentage points.
- `frozen_ml_epsilon_010`: -16.21 to -0.79 percentage points.

The intervals for the contrasts are centered on harmful effects for the ML variants.

## 15. Raw And Adjusted P-Values

The raw p-values were:

- `frozen_ml`: 0.0396.
- `frozen_hybrid_50_50`: 0.0011.
- `frozen_ml_epsilon_010`: 0.0430.

The Holm-adjusted p-values were:

- `frozen_ml`: 0.0792.
- `frozen_hybrid_50_50`: 0.0033.
- `frozen_ml_epsilon_010`: 0.0792.

The multiple-testing method was Holm correction over the three planned policy-vs-existing contrasts.

## 16. Seed Robustness

The live experiment used final seeds 100-119. Each seed contributed 10 games per policy. Seed-level rows are stored in `wolf_kill_seed_robustness.csv`.

At this scale, individual seed-policy cells are small, so the seed table is best interpreted as a robustness diagnostic rather than a primary inferential unit. The overall pattern across all seeds is that the existing rule remains stronger than the frozen ML variants in aggregate.

## 17. Behavioral-Regime Robustness

Regime-level diagnostics are stored in `wolf_kill_regime_robustness.csv`. The first rows show lower ML performance in several regimes:

- In `baseline_speech_enabled`, existing rule wolf win rate was 65%, while `frozen_ml` was 55% and the hybrid was 45%.
- In `deception_enabled`, existing was 60%, `frozen_ml` was 55%, hybrid was 50%, and epsilon was 60%.
- In `herding_enabled`, existing was 60%, `frozen_ml` was 50%, hybrid was 40%, and epsilon was 55%.

The available regime diagnostics do not show a clear regime where the frozen ML policy robustly dominates the existing rule.

## 18. Distribution-Shift Analysis

Distribution-shift diagnostics show substantial live candidate-row shift:

| Shift category | Rows | Overall wolf win rate |
|---|---:|---:|
| in_distribution | 3,815 | 63.49% |
| mild_shift | 3,684 | 60.59% |
| strong_shift | 6,881 | 57.43% |

Policy-specific examples:

- `existing_rule:in_distribution`: 71.25% wolf win rate.
- `existing_rule:strong_shift`: 65.88%.
- `frozen_ml:in_distribution`: 62.77%.
- `frozen_ml:strong_shift`: 56.62%.
- `frozen_hybrid_50_50:in_distribution`: 58.48%.
- `frozen_hybrid_50_50:strong_shift`: 53.82%.

The live environment contains many candidate rows outside the training feature ranges. However, the existing rule also performs better than ML within the in-distribution subset, so distribution shift is not the only explanation.

## 19. Overfitting Diagnostics

The overfitting diagnostic file classifies all three ML variants as "live harmful in this pilot":

| Policy | Shadow improvement | Live wolf-win difference | Shadow-live gap | Overfitting flag |
|---|---:|---:|---:|---:|
| frozen_ml | -0.0340 | -0.0850 | 0.0510 | 0 |
| frozen_hybrid_50_50 | -0.0422 | -0.1150 | 0.0728 | 0 |
| frozen_ml_epsilon_010 | -0.0313 | -0.0850 | 0.0537 | 0 |

The Stage 2A shadow rerun did not reproduce the earlier Stage 1.5 optimistic wolf-kill improvement. This suggests that the issue is not simply ordinary overfitting to the validation split; it is also a mismatch between action-value estimates and live strategic consequences.

## 20. Information Leakage Audit

The information-leakage audit indicates that the frozen model used observation-safe features and did not use hidden target roles directly. This matters because a night-kill model could trivially improve if it were allowed to see hidden identities, but such a policy would be scientifically invalid.

The key leakage conclusion is that the negative live result is not explained by an obvious hidden-information leak. Instead, the result suggests that the available public features and learned coefficients were not sufficient to outperform the hand-coded rule.

## 21. Failure-Case Analysis

Failure-case analysis is stored in `wolf_kill_policy_failure_cases.csv` and summarized in `ml_stage2a_failure_case_analysis.md`. The failure cases indicate that ML policies often selected targets that looked favorable under candidate features but did not translate into stronger complete-game outcomes.

The feature coefficients help explain why:

- The largest coefficient was negative for `public_information_entropy_proxy` (-0.0420).
- `candidate_distance_from_actor` was positive (+0.0139).
- `candidate_seat_is_edge` was negative (-0.0083).
- Most suspicion and `p_wolf` coefficients were very small.

The learned policy therefore emphasized relatively weak structural proxies. It also killed far fewer special roles than the existing rule: the existing rule averaged 2.180 special-role kills per game, while ML variants averaged about 1.015-1.030.

## 22. Comparison With Previous Algorithms

The result revises the ML Stage 1.5 optimism. Stage 1.5 reported a validation shadow policy where the wolf-kill ML action-value recommendation appeared promising. Stage 2A shows that, when frozen and deployed in live complete games, the same direction of claim does not hold.

This pattern is consistent with earlier non-ML lessons:

- Simple behavioral exploitation can be harmful, as seen when `highest_p_wolf` and `highest_suspicion` seer strategies underperformed random in structured seer search.
- Apparent positional or policy advantages can disappear after role randomization, seed expansion, or paired replay validation.
- A hand-coded policy can remain competitive if the learned model optimizes a proxy that is weakly coupled to full-game winning.

## 23. Hypothesis Status

| Hypothesis | Status | Evidence |
|---|---|---|
| H1: frozen ML improves wolf win rate | Rejected in this pilot | Wolf win rate fell from 69.50% to 61.00%; Holm p = 0.0792. |
| H2: hybrid is competitive or better | Rejected | Wolf win rate fell to 58.00%; Holm p = 0.0033. |
| H3: epsilon-greedy preserves benefit while reducing brittleness | Rejected in this pilot | Wolf win rate was 61.00%; Holm p = 0.0792. |
| H4: shadow and live outcomes align | Rejected | Stage 2A shadow improvement was negative and live performance was also worse. |

Standard conclusion label: `statistically supported harmful effect` for the hybrid policy; `weak/inconclusive` but directionally harmful for the pure ML and epsilon policies after multiple-comparison correction.

## 24. Scientific Interpretation

The main scientific finding is that offline or shadow ML value estimates are not sufficient evidence for policy improvement in this social-deduction environment. Night-kill targeting is strategically coupled to hidden roles, future speech, trust, day votes, and special-role interactions. A model that scores candidate targets well under weak action-value proxies can still damage the wolf team in live games.

The result is especially informative because the learned policies did not merely fail to improve; they reduced special-role kills substantially. The existing rule appears to preserve an important tactical capability: removing information or power roles. The frozen ML model was too indirect and too weakly aligned with that strategic objective.

## 25. Limitations

This is still a pilot live deployment:

- The live comparison used 200 matched sets, enough to detect large effects but not all small differences.
- Seed-level cells contain only 10 games per policy.
- The model class is a simple standard-library ridge model.
- The policy only affects wolf night kills, not speech, voting, deception, or mixed strategic planning.
- The policy was trained from synthetic simulation data, not human Werewolf play.
- Feature engineering may omit important interaction terms such as role removal value, future seer information suppression, and witch/hunter risk tradeoffs.
- Stage 2A is a live-game test inside this simulation engine, not an external human-subject result.

## 26. Next Hypothesis

Next hypothesis:

> A wolf-kill policy trained to directly value role-removal and future information suppression, rather than generic candidate action value, will outperform the existing rule only if it is validated through grouped, matched, live-game evaluation before deployment.

## 27. Exact Recommended Next Experiment

Recommended next experiment:

1. Freeze the current engine and existing rule as the control.
2. Build a role-removal-aware wolf-kill feature set using only observation-safe information.
3. Add explicit proxy labels for special-role kill value, seer survival reduction, and future village information reduction.
4. Train only on development seeds and exclude all live final seeds.
5. Run shadow validation but treat it as screening only.
6. Run a live matched-policy experiment with at least 500 matched sets.
7. Include the same policies as Stage 2A plus a role-removal-aware ML policy.
8. Pre-register primary outcome as live wolf win rate.
9. Use matched contrasts, 95% confidence intervals, Holm correction, seed robustness, regime robustness, and distribution-shift diagnostics.
10. Do not declare improvement unless the live matched contrast remains positive after correction and the effect is practically meaningful.

## 28. Relevant Source Files

Relevant source and artifact files include:

- `ml_wolf_kill_policy.py`
- `ml_stage2a_wolf_kill_experiment.py`
- `simulation.py`
- `game.py`
- `wolf_strategy.py`
- `results/ml_optimization_stage2a/wolf_kill_frozen_model_manifest.json`
- `results/ml_optimization_stage2a/wolf_kill_live_policy_summary.csv`
- `results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv`
- `results/ml_optimization_stage2a/wolf_kill_seed_robustness.csv`
- `results/ml_optimization_stage2a/wolf_kill_regime_robustness.csv`
- `results/ml_optimization_stage2a/wolf_kill_distribution_shift_summary.csv`
- `results/ml_optimization_stage2a/wolf_kill_overfitting_diagnostics.csv`
- `results/ml_optimization_stage2a/wolf_kill_policy_failure_cases.csv`
- `results/ml_optimization_stage2a/ml_stage2a_experiment_report.md`
- `results/ml_optimization_stage2a/ml_stage2a_distribution_shift_report.md`
- `results/ml_optimization_stage2a/ml_stage2a_information_leakage_audit.md`
- `results/ml_optimization_stage2a/ml_stage2a_failure_case_analysis.md`

## 29. Commit Hash And Reproducibility

The Stage 2A source state consulted by this report was:

```text
e4e583387febd51dddc6330076db6f2a2a7532bc
```

At the time this report was prepared, that commit was present on both local `main` and `origin/main`. The report is a synthesis of committed Stage 2A artifacts and does not rerun simulations or modify experiment logic.

