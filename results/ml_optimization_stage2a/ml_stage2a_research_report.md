# DURF Werewolf Simulation: ML Stage 2A Research Report

## 1. Research Background

This stage evaluates whether a frozen machine-learning wolf night-kill policy can improve live game outcomes in the DURF Werewolf simulation. Earlier stages established Werewolf as a controlled hidden-information social-deduction environment with speech signals, belief updates, role actions, deception, credibility costs, speaker memory, risk preferences, seat-position diagnostics, and physically symmetric replay validation.

The central research problem is not only whether a model can predict attractive actions offline, but whether a learned policy remains beneficial when inserted into the full stochastic game loop. In this setting, wolf win rate is the primary team-level outcome, and night-kill targeting can influence information flow, seer survival, witch/hunter value, and later voting.

## 2. Connection To Prior Stages

ML Stage 1 created observation-safe decision logs and baseline machine-learning models. Its village-vote identity model appeared very strong in an early split, with ROC-AUC 0.9458. ML Stage 1.5 then introduced grouped splits and full-state rollout validation, showing that the Stage 1 estimate was too optimistic: the village-vote final-test ROC-AUC fell to 0.6679, only slightly above existing `p_wolf` at 0.6586.

ML Stage 1.5 also showed weak surrogate-to-full validity for wolf kills, with Spearman correlation 0.0718. However, its final-test shadow wolf-kill recommendation appeared promising, with value 0.850 versus 0.700 for the existing rule. Stage 2A tests whether that shadow result survives live complete-game deployment.

## 3. Previous Hypothesis

The previous hypothesis was that a full-state rollout-selected wolf-kill model could identify targets that improve the wolf team's expected outcome compared with the existing hand-coded rule.

## 4. Current Pre-Specified Hypotheses

H1: A frozen ML wolf-kill policy will produce a higher live wolf win rate than the existing rule policy.

H2: A 50/50 hybrid between ML and the existing rule will be at least competitive with the existing rule.

H3: A 10% epsilon-greedy ML policy will reduce brittleness while preserving most of the ML benefit.

H4: If the learned policy generalizes, shadow policy value and live complete-game outcomes should point in the same direction.

## 5. Experimental Design

The experiment used matched live complete-game comparisons. Each matched set compared `existing_rule`, `frozen_ml`, `frozen_hybrid_50_50`, and `frozen_ml_epsilon_010`.

## 6. Algorithm And Model Implementation

The ML policy is a frozen standard-library ridge action-value model trained from observation-safe wolf-kill candidate rows. At live decision time it scores legal wolf night-kill targets using public and state-derived features. No hidden target roles are used as model inputs.

Frozen model manifest hash:

```text
3636ee12b35a57bbe8811b59ccf2c37a2bfec25ced6170ee3f51615da6f64f83
```

Model artifact hash:

```text
f3c5e60275eea04c4a03e15a21aab2713e86a4e2b446ff0fbf9b194e90ae124b
```

## 7. Dataset And Effective Independent Sample Size

Development seeds were training 42-49, validation 50-51, and excluded final-test 52-56. Live final-test seeds were 100-119.

| Data component | Count |
|---|---:|
| Shadow source games | 105 |
| Shadow decision states | 105 |
| Shadow candidate rows | 420 |
| Shadow rollout simulations | 2,940 |
| Live complete games | 800 |
| Live matched sets | 200 |
| Live decisions | 2,600 |
| Live candidate prediction rows | 14,380 |

The primary independent unit is the 200 matched live sets, not the 14,380 candidate prediction rows.

## 8. Raw Row Count Versus Independent Units

Candidate rows are nested within decisions, decisions are nested within games, and games are nested within matched sets and seeds. Formal policy inference therefore uses matched set contrasts rather than candidate-row independence.

## 9. Validation And Data-Integrity Checks

The frozen model audit, leakage audit, distribution-shift report, overfitting diagnostics, and failure-case files were inspected. The model was frozen before live evaluation, final live seeds were separated from development seeds, and legal target constraints were preserved.

## 10. Data Analysis Methods

The Data Analysis used descriptive policy summaries, 95% confidence intervals for policy win rates, matched binary contrasts, discordant-set odds ratios, raw p-values, Holm-adjusted p-values, seed robustness, behavioral-regime robustness, distribution-shift diagnostics, overfitting diagnostics, leakage audit, and failure-case analysis.

## 11. Descriptive Results

| Policy | Games | Wolf wins | Village wins | Wolf win rate | 95% CI | Avg rounds | Avg successful night kills | Avg special role kills |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| existing_rule | 200 | 139 | 61 | 69.50% | 63.12%-75.88% | 3.23 | 2.365 | 2.180 |
| frozen_ml | 200 | 122 | 78 | 61.00% | 54.24%-67.76% | 3.265 | 2.430 | 1.030 |
| frozen_hybrid_50_50 | 200 | 116 | 84 | 58.00% | 51.16%-64.84% | 3.250 | 2.405 | 1.015 |
| frozen_ml_epsilon_010 | 200 | 122 | 78 | 61.00% | 54.24%-67.76% | 3.255 | 2.430 | 1.025 |

The existing rule had the highest observed wolf win rate. The existing rule also killed substantially more special roles on average than the ML variants.

## 12. Formal Statistical Inference

| Contrast | Difference | 95% CI | Discordant OR | Raw p | Holm p |
|---|---:|---|---:|---:|---:|
| frozen_ml vs existing_rule | -8.50 pp | [-16.08, -0.92] | 0.5696 | 0.0396 | 0.0792 |
| frozen_hybrid_50_50 vs existing_rule | -11.50 pp | [-18.04, -4.96] | 0.3521 | 0.0011 | 0.0033 |
| frozen_ml_epsilon_010 vs existing_rule | -8.50 pp | [-16.21, -0.79] | 0.5802 | 0.0430 | 0.0792 |

After Holm correction, the hybrid policy produced a statistically supported harmful effect. The pure ML and epsilon variants were harmful in direction but did not remain significant after correction.

## 13. Effect Sizes

The policy effects are practically meaningful because all ML variants reduced wolf win rate by at least 8.50 percentage points in live games. The hybrid reduction was 11.50 percentage points.

## 14. Confidence Intervals

All matched-difference confidence intervals are centered on negative effects for the ML variants. The policy-level confidence intervals also show the existing rule as the strongest observed policy.

## 15. Raw And Adjusted P-Values

Raw p-values were 0.0396, 0.0011, and 0.0430. Holm-adjusted p-values were 0.0792, 0.0033, and 0.0792. Holm correction was required because three policy-vs-control contrasts were tested.

## 16. Seed Robustness

The live test used seeds 100-119. Each seed-policy cell had 10 games, so seed-level results are diagnostic rather than definitive. The aggregate across all seeds favored the existing rule.

## 17. Behavioral-Regime Robustness

Regime-level diagnostics do not reveal a robust regime where the frozen ML policy dominates. In early rows, existing rule outperforms ML in baseline speech, deception, and herding-enabled regimes.

## 18. Distribution-Shift Analysis

Candidate rows were classified as in-distribution, mild shift, or strong shift. Overall wolf win rates declined from 63.49% in-distribution to 57.43% under strong shift. The existing rule outperformed ML not only in shifted rows but also in the in-distribution subset, so distribution shift is not the only explanation.

## 19. Overfitting Diagnostics

Stage 2A shadow summaries no longer reproduced the earlier Stage 1.5 +0.150 wolf-kill shadow improvement. Frozen ML, hybrid, and epsilon policies were all classified as live harmful in this pilot. This points to weak action-value/live-game alignment, not just ordinary split overfitting.

## 20. Information Leakage Audit

The information-leakage audit indicates that the model did not use hidden target roles or future outcomes as live inputs. The negative live result is therefore not explained by an obvious information leak.

## 21. Failure-Case Analysis

Failure cases show that ML policies often selected targets that scored well under weak public proxies but did not preserve the existing rule's ability to remove information or power roles. Special-role kill rates were much lower under ML policies.

## 22. Comparison With Previous Algorithms

This result revises the Stage 1.5 shadow optimism. Prediction quality, one-step offline action value, shadow value, and long-run live policy value are distinct quantities. Shadow advantage did not generalize to continuous live control.

## 23. Hypothesis Status

| Hypothesis | Status |
|---|---|
| Frozen ML improves live wolf win rate | Rejected in this pilot after correction |
| Hybrid remains competitive | Rejected |
| Epsilon improves robustness | Rejected in this pilot after correction |
| Shadow and live outcomes align | Rejected |

Conclusion labels: `statistically supported harmful effect` for the hybrid; `weak/inconclusive` but harmful direction for pure ML and epsilon.

## 24. Scientific Interpretation

Current frozen ML policies did not improve live wolf win rate. The hybrid policy caused a statistically supported harmful effect. The existing rule remains the default wolf-kill policy. The prior shadow advantage did not generalize to continuous control.

The result suggests that policy-induced distribution shift and repeated-decision compounding matter. A target that appears locally valuable can change future information, speech, and voting trajectories in ways that reduce long-run team value.

## 25. Limitations

The live test is still a pilot with 200 matched sets. The model class is simple, feature engineering is limited, and seed-policy cells are small. The result applies to this frozen model and current rule environment.

## 26. Next Hypothesis

Next hypothesis:

> ML Stage 2B should diagnose whether the live failure is caused by policy-induced distribution shift, repeated-decision compounding, weak special-role-removal features, or mismatch between shadow action values and live complete-game outcomes.

## 27. Exact Recommended Next Experiment

ML Stage 2B should compare existing rule, frozen ML, hybrid, epsilon, and diagnostic variants in a matched offline-to-live failure analysis. It should quantify state drift after each ML decision, special-role removal opportunity cost, repeated-decision compounding, and whether failures concentrate in specific behavioral regimes or feature-shift categories. It should not deploy a new policy until the failure mode is understood.

## 28. Relevant Source Files

- `ml_wolf_kill_policy.py`
- `ml_stage2a_wolf_kill_experiment.py`
- `results/ml_optimization_stage2a/wolf_kill_frozen_model_manifest.json`
- `results/ml_optimization_stage2a/wolf_kill_live_policy_summary.csv`
- `results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv`
- `results/ml_optimization_stage2a/wolf_kill_seed_robustness.csv`
- `results/ml_optimization_stage2a/wolf_kill_regime_robustness.csv`
- `results/ml_optimization_stage2a/wolf_kill_distribution_shift_summary.csv`
- `results/ml_optimization_stage2a/wolf_kill_overfitting_diagnostics.csv`
- `results/ml_optimization_stage2a/wolf_kill_policy_failure_cases.csv`

## 29. Commit Hash And Reproducibility

The source experiment artifacts consulted by this report are present in repository state:

```text
e4e583387febd51dddc6330076db6f2a2a7532bc
```

The current documentation commit is recorded after this stage is committed.
