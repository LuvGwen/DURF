# ML Stage 1.5 Research Report: Grouped Splits And Full-State Rollout Validation

## 1. Background

ML Stage 1.5 tested whether the encouraging Stage 1 ML signals survived stricter validation. The stage introduced full-state simulator continuation, grouped split controls, behavioral regimes, bootstrap summaries, and overfitting diagnostics.

## 2. Prior-Stage Connection

Stage 1 produced observation-safe datasets and promising pilot metrics, including a village-vote ROC-AUC near 0.9458. Stage 1.5 was designed to audit whether those results generalized beyond the original pilot split and whether surrogate action values approximated complete simulator outcomes.

## 3. Hypothesis

Observation-safe ML models should retain useful identity and action-value signal under grouped validation and full-state rollout continuation.

## 4. Pre-Specified Outcomes

Primary outcomes included grouped identity metrics, surrogate-versus-full rollout correlations, action-value generalization, shadow policy values, regret, cross-seed robustness, cross-regime robustness, leakage status, and overfitting diagnostics.

## 5. Experimental Design

The stage used six source seeds, seven behavioral regimes, and seven continuation policies. Learned policies remained in shadow mode only. The stage evaluated decisions without deploying any learned policy into complete live games.

## 6. Data Scale

The report records 84 source game families, 244 decision states, 976 candidate rows, and 6,832 full rollout simulations. Decision-state datasets included 80 seer-check states, 80 wolf-kill states, and 84 day-vote states.

## 7. Independent Sample Definition

Decision states and source game families are the relevant independent units. Candidate rows are nested within decisions, and rollout rows are nested within state-action-policy combinations.

## 8. Implementation

The stage cloned mid-game simulator states and continued games under requested action substitutions. Deterministic rollout seeds were derived from snapshot, action, and policy identifiers. A model-selection manifest recorded frozen model choices.

## 9. Validation

Snapshot equivalence passed 10 of 10 checks. Full-state rollout reproducibility was covered by deterministic rollout seeds and validation summaries. Leakage audits and overfitting audits were exported.

## 10. Data Analysis

The analysis reported grouped ROC-AUC and calibration metrics, surrogate-full Pearson and Spearman correlations, top-action agreement, top-3 overlap, rollout regret, shadow policy values, cross-seed metrics, cross-regime metrics, feature ablations, bootstrap confidence intervals, and overfitting flags.

## 11. Descriptive Findings

The Stage 1 village-vote ROC-AUC around 0.9458 fell to 0.6679 on the grouped final test, while existing `p_wolf` achieved 0.6586. This means the pilot estimate was optimistic. The seer-candidate final-test logistic ROC-AUC was 0.5986.

Surrogate-to-full validity was limited: seer-check Spearman correlation was 0.2989, wolf-kill was 0.0718, and day-vote was 0.2419. The wolf-kill and day-vote surrogate values were therefore weak substitutes for full simulator continuation.

## 12. Formal Inference

This stage included bootstrap confidence intervals and robustness diagnostics, but its main policy comparisons were still shadow-mode estimates. They should not be treated as live win-rate inference.

## 13. Robustness

The stage included cross-seed and cross-regime outputs. It found that feature groups and action values were not uniformly stable, and some overfitting diagnostics were flagged.

## 14. Leakage, Overfitting, And Design Audit

No hidden-role leakage was treated as valid model input. However, overfitting risk remained. The report explicitly states that Stage 1.5 model decisions were shadow-mode only and not ready as deployed live policies.

## 15. Scientific Interpretation

ML Stage 1.5 revised two important Stage 1 interpretations. First, identity prediction was learnable but much weaker under grouped validation than the pilot suggested. Second, surrogate action values were not reliable enough to replace full simulator rollouts. The stage nevertheless identified wolf-kill shadow recommendations as a candidate for a stricter live test.

## 16. Conclusion Label

Conclusion label: `surrogate-only improvement` for the shadow wolf-kill advantage; `weak/inconclusive` for live policy improvement.

## 17. Limitations

The rollout scale was still modest. Each state-action evaluation used limited continuations, and shadow policy values do not equal complete live game outcomes.

## 18. Next Hypothesis

The next hypothesis was that a frozen wolf-kill model selected from Stage 1.5 could improve live complete-game wolf win rate when tested on held-out final seeds.

## 19. Source Files

- `ml_full_state_rollout.py`
- `ml_nested_validation.py`
- `results/ml_optimization_stage15/ml_stage15_experiment_report.md`
- `results/ml_optimization_stage15/ml_surrogate_validity_metrics.csv`
- `results/ml_optimization_stage15/ml_identity_generalization_metrics.csv`
- `results/ml_optimization_stage15/ml_shadow_policy_comparison.csv`
- `results/ml_optimization_stage15/ml_overfitting_diagnostics.csv`
- `results/ml_optimization_stage15/ml_stage15_full_rollout_audit.md`
- `results/ml_optimization_stage15/ml_stage15_overfitting_audit.md`

## 20. Reproducibility Information

The report records source seeds, behavioral regimes, continuation policies, rollout counts, decision limits, candidate caps, bootstrap resamples, and runtime.

## 21. Commit Information

This reconstruction used repository state `e4e583387febd51dddc6330076db6f2a2a7532bc`. The current documentation commit is recorded after this stage is committed.
