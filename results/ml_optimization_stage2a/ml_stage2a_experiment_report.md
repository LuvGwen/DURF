# ML Stage 2A Experiment Report

## Summary

Stage 2A freezes the Stage 1.5 ridge wolf-kill action-value model and tests it in complete live games against the unchanged existing rule, a 50/50 hybrid policy, and a fixed epsilon-greedy variant.

## Experimental Scale

| Metric | Value |
| --- | --- |
| shadow_source_games | 105 |
| shadow_decision_states | 105 |
| shadow_candidate_rows | 420 |
| shadow_rollout_simulations | 2940 |
| live_complete_games | 800 |
| live_matched_sets | 200 |
| live_decision_rows | 2600 |
| live_candidate_prediction_rows | 14380 |

## Live Policy Summary

| Policy | Games | Wolf Wins | Village Wins | Wolf Win Rate | CI Low | CI High | Avg Rounds | Avg Night Kills | Avg Special Kills |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| existing_rule | 200 | 139 | 61 | 69.50% | 63.12% | 75.88% | 3.2300 | 2.3650 | 2.1800 |
| frozen_ml | 200 | 122 | 78 | 61.00% | 54.24% | 67.76% | 3.2650 | 2.4300 | 1.0300 |
| frozen_hybrid_50_50 | 200 | 116 | 84 | 58.00% | 51.16% | 64.84% | 3.2500 | 2.4050 | 1.0150 |
| frozen_ml_epsilon_010 | 200 | 122 | 78 | 61.00% | 54.24% | 67.76% | 3.2550 | 2.4300 | 1.0250 |

## Primary Matched Contrasts

| Contrast | Matched Sets | Existing Wolf Win | Policy Wolf Win | Difference | Diff CI Low | Diff CI High | Discordant OR | Raw p | Holm p | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_ml_vs_existing_rule | 200 | 69.50% | 61.00% | -8.50% | -16.08% | -0.92% | 0.5696 | 0.0396 | 0.0792 | harmful in this pilot |
| frozen_hybrid_50_50_vs_existing_rule | 200 | 69.50% | 58.00% | -11.50% | -18.04% | -4.96% | 0.3521 | 0.0011 | 0.0033 | harmful in this pilot |
| frozen_ml_epsilon_010_vs_existing_rule | 200 | 69.50% | 61.00% | -8.50% | -16.21% | -0.79% | 0.5802 | 0.0430 | 0.0792 | harmful in this pilot |

## Shadow Summary

| Policy | Decision States | Mean Rollout Value | Existing Value | Improvement | Regret to Best | Agreement Existing | Agreement Best |
| --- | --- | --- | --- | --- | --- | --- | --- |
| existing_rule | 105 | 0.7061 | 0.7061 | 0.0000 | 0.1333 | 1.0000 | 0.3143 |
| frozen_ml | 105 | 0.6721 | 0.7061 | -0.0340 | 0.1673 | 0.2190 | 0.1619 |
| frozen_hybrid_50_50 | 105 | 0.6639 | 0.7061 | -0.0422 | 0.1755 | 0.2667 | 0.1524 |
| frozen_ml_epsilon_010 | 105 | 0.6748 | 0.7061 | -0.0313 | 0.1646 | 0.2476 | 0.2000 |

## Secondary Outcomes

| Policy | Games | Avg Rounds | Night Kill Rate | Special Kill Rate | Seer Kill Rate | Witch Kill Rate | Hunter Kill Rate | Witch Save Rate | Hunter Retaliation Rate | Avg Wolf Survival | Avg Vote Control Proxy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| existing_rule | 200 | 3.2300 | 73.22% | 67.49% | 28.64% | 22.76% | 16.10% | 26.78% | 21.05% | 1.4000 | 1.7850 |
| frozen_hybrid_50_50 | 200 | 3.2500 | 74.00% | 31.23% | 9.38% | 9.85% | 12.00% | 26.00% | 18.46% | 1.1200 | 1.6500 |
| frozen_ml | 200 | 3.2650 | 74.43% | 31.55% | 8.88% | 10.87% | 11.79% | 25.57% | 17.76% | 1.2150 | 1.6750 |
| frozen_ml_epsilon_010 | 200 | 3.2550 | 74.65% | 31.49% | 8.76% | 11.83% | 10.91% | 25.35% | 16.90% | 1.2450 | 1.6250 |

## Policy Agreement

| Policy | Decision Rows | ML/Existing Agreement | Hybrid/Existing Agreement | ML/Hybrid Agreement | Low Margin Rate | Avg Legal Candidates |
| --- | --- | --- | --- | --- | --- | --- |
| existing_rule | 646 | 23.07% | 18.27% | 43.96% | 86.38% | 5.5650 |
| frozen_hybrid_50_50 | 650 | 20.92% | 16.92% | 46.62% | 84.46% | 5.5308 |
| frozen_ml | 653 | 20.52% | 16.08% | 43.49% | 87.29% | 5.5069 |
| frozen_ml_epsilon_010 | 651 | 19.66% | 15.67% | 43.16% | 86.79% | 5.5207 |

## Top Frozen Ridge Coefficients

| Feature | Coefficient | Magnitude | Sign | Interpretation |
| --- | --- | --- | --- | --- |
| public_information_entropy_proxy | -0.0420 | 0.0420 | pushes_away_from_kill | general public feature; pushes_away_from_kill; not a causal interpretation |
| candidate_distance_from_actor | 0.0139 | 0.0139 | pushes_toward_kill | position signal; pushes_toward_kill; not a causal interpretation |
| candidate_seat_is_edge | -0.0083 | 0.0083 | pushes_away_from_kill | position signal; pushes_away_from_kill; not a causal interpretation |
| actor_suspicion_score | -0.0027 | 0.0027 | pushes_away_from_kill | risk/suspicion signal; pushes_away_from_kill; not a causal interpretation |
| actor_p_wolf | -0.0027 | 0.0027 | pushes_away_from_kill | risk/suspicion signal; pushes_away_from_kill; not a causal interpretation |
| candidate_p_wolf | -0.0008 | 0.0008 | pushes_away_from_kill | risk/suspicion signal; pushes_away_from_kill; not a causal interpretation |
| candidate_uncertainty_proxy | -0.0008 | 0.0008 | pushes_away_from_kill | general public feature; pushes_away_from_kill; not a causal interpretation |
| candidate_survival_proxy | 0.0008 | 0.0008 | pushes_toward_kill | survival/game-state signal; pushes_toward_kill; not a causal interpretation |
| candidate_side_is_left | -0.0003 | 0.0003 | pushes_away_from_kill | position signal; pushes_away_from_kill; not a causal interpretation |
| candidate_physical_seat_numeric | -0.0003 | 0.0003 | pushes_away_from_kill | position signal; pushes_away_from_kill; not a causal interpretation |

## Model Freeze and Leakage

- Manifest hash: `3636ee12b35a57bbe8811b59ccf2c37a2bfec25ced6170ee3f51615da6f64f83`
- Model artifact hash: `f3c5e60275eea04c4a03e15a21aab2713e86a4e2b446ff0fbf9b194e90ae124b`
- Training seeds: [42, 43, 44, 45, 46, 47, 48, 49]
- Validation seeds: [50, 51]
- Excluded Stage 1.5 final-test seeds: [52, 53, 54, 55, 56]
- Stage 2A final live-test seeds: [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119]
- Leakage audit status: PASS for the live feature matrix.

## Required Questions

| Question | Answer |
| --- | --- |
| Was the wolf-kill model frozen before live testing? | Yes. |
| Were final-test seeds completely isolated? | Yes; seeds 100-119 are reserved for live testing. |
| Did any leakage checks fail? | No leakage checks failed. |
| How many source games, decisions, candidates, rollouts, matched sets, and live games were run? | 105 source games, 105 shadow decisions, 420 shadow candidates, 2940 rollout simulations, 200 matched sets, and 800 live games. |
| Does expanded shadow evaluation reproduce the previous +0.150 estimate? | No. The expanded pilot estimates frozen_ml shadow improvement at -0.0340, not +0.150. |
| Does pure ML improve actual complete-game wolf win rate? | Pure ML classification: harmful in this pilot. |
| Does hybrid ML improve wolf win rate? | Hybrid classification: harmful in this pilot. |
| Does epsilon exploration improve robustness? | Epsilon classification: harmful in this pilot. |
| Which policy has the highest wolf win rate? | `existing_rule` at 69.50%. |
| Which primary contrasts survive Holm correction? | frozen_hybrid_50_50_vs_existing_rule |
| What are the absolute percentage-point effects? | frozen_ml: -8.50 pp; frozen_hybrid_50_50: -11.50 pp; frozen_ml_epsilon_010: -8.50 pp |
| What are the odds ratios and confidence intervals? | Reported in `wolf_kill_primary_contrasts.csv`; CIs are normal paired-difference CIs. |
| Are gains stable across seeds? | See `wolf_kill_seed_robustness.csv`; seed-level robustness is descriptive in this pilot. |
| Are gains stable across regimes? | See `wolf_kill_regime_robustness.csv`; regime-level robustness is descriptive in this pilot. |
| Does performance deteriorate out of distribution? | See `wolf_kill_distribution_shift_summary.csv` and the distribution-shift report. |
| Which features drive target selection? | The largest standardized ridge coefficients are listed above and in `wolf_kill_feature_coefficients.csv`. |
| Does the model mainly target special roles or high-influence villagers? | existing_rule: 94.27% selected special roles; frozen_ml: 43.64% selected special roles; frozen_hybrid_50_50: 42.77% selected special roles; frozen_ml_epsilon_010: 43.47% selected special roles |
| Does it increase hunter-retaliation risk? | Hunter-retaliation rates are reported in secondary outcomes. |
| Does it increase witch-save risk? | Witch-save rates are reported in secondary outcomes. |
| Are there identifiable failure-state patterns? | Failure rows are summarized in `wolf_kill_policy_failure_cases.csv` and `ml_stage2a_failure_case_analysis.md`. |
| Does offline full-rollout value predict live policy performance? | This is assessed by comparing shadow improvement and live win-rate differences; evidence remains pilot-scale. |
| Is pure ML better than hybrid? | Use primary contrasts and policy summaries; prefer hybrid only if performance is similar and stability is better. |
| Is limited exploration useful? | Use the epsilon contrast and seed/regime robustness; it is not tuned in this stage. |
| Is the current frozen model ready for deployment beyond experiments? | Only if the primary contrast is positive, corrected, and stable; otherwise keep it experimental. |
| Should the next stage optimize voting or continue refining wolf kill? | If wolf-kill gains are inconclusive, continue refining kill policy diagnostics before optimizing voting. |

## Overfitting Diagnostics

| Policy | Shadow Improvement | Live Difference | Shadow-Live Gap | Flag | Classification |
| --- | --- | --- | --- | --- | --- |
| frozen_ml | -0.0340 | -0.0850 | 0.0510 | 0 | live harmful in this pilot |
| frozen_hybrid_50_50 | -0.0422 | -0.1150 | 0.0728 | 0 | live harmful in this pilot |
| frozen_ml_epsilon_010 | -0.0313 | -0.0850 | 0.0537 | 0 | live harmful in this pilot |
