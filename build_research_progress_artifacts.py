"""Build cumulative DURF research documentation artifacts.

This helper writes documentation and evidence-tracking files only. It does not
run simulations, alter experiment logic, or modify raw experimental datasets.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "results" / "research_progress"
STAGE1_DIR = ROOT / "results" / "ml_optimization_stage1"
STAGE15_DIR = ROOT / "results" / "ml_optimization_stage15"
STAGE2A_DIR = ROOT / "results" / "ml_optimization_stage2a"

SOURCE_COMMIT = "e4e583387febd51dddc6330076db6f2a2a7532bc"
CURRENT_DOCUMENTATION_COMMIT = "pending_current_stage_commit"

CONCLUSION_LABELS = [
    "statistically supported improvement",
    "statistically supported harmful effect",
    "promising but uncertain",
    "weak/inconclusive",
    "no meaningful improvement",
    "overfit",
    "unstable across regimes",
    "surrogate-only improvement",
    "invalid due to leakage",
    "invalid due to design limitation",
    "hypothesis supported",
    "hypothesis rejected",
    "hypothesis unresolved",
    "implementation validated",
    "engine symmetry validated",
]

REGISTRY_COLUMNS = [
    "stage_id",
    "stage_name",
    "research_domain",
    "hypothesis_id",
    "hypothesis",
    "prior_hypothesis_source",
    "experiment_design",
    "dataset_path",
    "report_path",
    "raw_row_count",
    "raw_game_count",
    "independent_sample_size",
    "matched_set_count",
    "seed_count",
    "behavioral_regime_count",
    "primary_outcome",
    "comparison",
    "control_condition",
    "descriptive_effect",
    "absolute_percentage_point_effect",
    "effect_size_type",
    "effect_size",
    "confidence_interval",
    "raw_p_value",
    "adjusted_p_value",
    "multiplicity_method",
    "evidence_level",
    "seed_robustness",
    "regime_robustness",
    "design_validity",
    "engine_validity",
    "distribution_shift_status",
    "overfitting_status",
    "leakage_status",
    "conclusion_label",
    "hypothesis_status",
    "main_limitation",
    "supersedes_stage_id",
    "superseded_by_stage_id",
    "next_hypothesis",
    "source_commit",
    "current_documentation_commit",
]

PROPOSAL_COLUMNS = [
    "proposal_component",
    "original_proposal_description",
    "status",
    "evidence",
    "source_file",
    "quality_of_completion",
    "remaining_work",
    "required_next_stage",
    "priority",
    "blocking_final_report",
]

TRACE_COLUMNS = [
    "claim_id",
    "claim_summary",
    "stage",
    "source_file",
    "source_table_or_section",
    "dataset",
    "analysis_script",
    "commit_hash",
    "verification_status",
    "notes",
]


def rel(path: str) -> str:
    return path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def stage1_research_report() -> str:
    return """
# ML Stage 1 Research Report: Observation-Safe Logging And Offline ML Pilot

## 1. Background

ML Stage 1 was the first machine-learning optimization stage for the DURF Werewolf simulation. Its goal was to determine whether game states could be logged in an observation-safe way and converted into candidate-action datasets for identity prediction and action-value modeling.

## 2. Prior-Stage Connection

Stages 1-4 had already implemented the game engine, role actions, speech-like signals, belief updates, herding, wolf deception, credibility costs, speaker memory, and ten-player variants. ML Stage 1 treated these mechanisms as a source of simulated decisions and public state features.

## 3. Hypothesis

Observation-safe features should contain learnable signals about hidden wolf identity and action value without using prohibited hidden labels as model inputs.

## 4. Pre-Specified Outcomes

Primary outcomes were identity prediction metrics, action-value ranking metrics, offline policy value, regret, and leakage-audit status.

## 5. Experimental Design

The stage generated candidate rows for seer checks, wolf night kills, and day votes. Learned policies were not deployed into the live simulator. Splits were grouped by seed/game family where possible: seeds 42-44 for training, 45 for validation, and 46 for testing.

## 6. Data Scale

The pilot used seeds 42-46, 12 games per seed, 60 generated games, and 24,599 rollout simulations. Dataset sizes were 98 seer-check states with 588 candidate rows, 192 wolf-kill states with 979 rows, and 1,000 day-vote states with 5,588 rows, for 7,155 total candidate rows.

## 7. Independent Sample Definition

The independent unit is closer to a source game family or decision state than a candidate row. Candidate rows from the same decision are not independent.

## 8. Implementation

Feature logging used only information available before each decision. Public features included `p_wolf`, `suspicion_score`, speech and vote histories, trust summaries, role claims, seat features, and vote context. Seer-private information was available only to the seer, and wolf teammate identity was available only to wolf actors.

## 9. Validation

The leakage audit listed prohibited fields such as `candidate_is_wolf_label`, `true_candidate_role_label`, `eventual_winner_label`, future deaths, future speech, and rollout labels. The Stage 1 report states that all leakage checks passed.

## 10. Data Analysis

The analysis was primarily descriptive and pilot-level. It reported ROC-AUC, PR-AUC, Brier score, log loss, top-k identity metrics, RMSE, MAE, rank correlation, policy value, regret, and offline agreement with existing rules.

## 11. Descriptive Findings

The most striking pilot identity result was the village-vote logistic model ROC-AUC of 0.9458, compared with existing `p_wolf` ROC-AUC of 0.5042 and existing suspicion ROC-AUC of 0.5109 in that pilot split. The best wolf-kill ridge action-value policy had value 0.6821, below the existing wolf strategy value of 0.7128 in the offline comparison.

## 12. Formal Inference

Formal statistical inference was not performed in Stage 1. No confidence intervals or adjusted p-values were reported for model-performance differences. Stage 1 should therefore be read as an implementation and feasibility pilot, not a final model-validation result.

## 13. Robustness

Robustness was limited. The split used five seeds, but the later ML Stage 1.5 grouped/full-rollout evaluation superseded Stage 1 for generalization claims.

## 14. Leakage, Overfitting, And Design Audit

Leakage checks passed, but later evidence showed that row-level or small grouped pilots could still be optimistic. The Stage 1 village-vote ROC-AUC of about 0.9458 did not survive stricter grouped evaluation.

## 15. Scientific Interpretation

ML Stage 1 successfully built the data infrastructure but did not prove that learned policies improve live game outcomes. The correct scientific interpretation is that observation-safe logging is feasible and that some identity signals appear learnable, but the strength of those signals required stricter validation.

## 16. Conclusion Label

Conclusion label: `weak/inconclusive` for predictive or policy-improvement claims; `implementation validated` for observation-safe logging and leakage-audit infrastructure.

## 17. Limitations

The stage used a small pilot sample, candidate-row outputs, surrogate rollout values, and no live policy deployment. scikit-learn baselines were skipped because scikit-learn was unavailable.

## 18. Next Hypothesis

The next hypothesis was that grouped full-state rollout validation would separate true generalization from row-split optimism and surrogate artifacts.

## 19. Source Files

- `ml_decision_logging.py`
- `ml_dataset_builder.py`
- `ml_model_training.py`
- `results/ml_optimization_stage1/ml_stage1_experiment_report.md`
- `results/ml_optimization_stage1/ml_identity_model_metrics.csv`
- `results/ml_optimization_stage1/ml_action_value_model_metrics.csv`
- `results/ml_optimization_stage1/ml_offline_policy_comparison.csv`
- `results/ml_optimization_stage1/ml_information_leakage_audit.md`

## 20. Reproducibility Information

The Stage 1 report records the seed list, generated-game count, decision limits, rollout counts, Python version, and runtime. Source artifacts are committed in the repository.

## 21. Commit Information

This reconstruction used repository state `{source_commit}`. The current documentation commit is recorded after this stage is committed.
""".format(source_commit=SOURCE_COMMIT)


def stage15_research_report() -> str:
    return """
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

This reconstruction used repository state `{source_commit}`. The current documentation commit is recorded after this stage is committed.
""".format(source_commit=SOURCE_COMMIT)


def stage2a_research_report() -> str:
    return """
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
{source_commit}
```

The current documentation commit is recorded after this stage is committed.
""".format(source_commit=SOURCE_COMMIT)


def documentation_completion_report() -> str:
    return """
# Research Documentation Completion Stage Report

## Background

This stage reconstructs the evidence chain across the DURF Werewolf project. It does not introduce a new gameplay algorithm, deploy a new ML policy, or rerun large simulations.

## Prior-Stage Connection

The stage integrates reports from the core simulator, special-role actions, speech and deception, risk preference, position theory, structured seer search, seat-order validity, physical replay validation, and ML Stages 1, 1.5, and 2A.

## Hypothesis

A cumulative documentation audit can clarify which claims are supported, which are descriptive only, which were revised by later validation, and which proposal deliverables remain incomplete.

## Pre-Specified Outcomes

Required outcomes include complete stage reports, a cumulative evidence registry, a proposal-alignment audit, a source-traceability index, an inconsistencies file, a roadmap, a permanent reporting standard, and a documentation validation summary.

## Experimental Design

This is a documentation and Data Analysis reconstruction stage. It inspects committed source reports and result files without modifying simulation logic or regenerating raw experimental data.

## Data Scale

No new simulation rows were generated. The stage references existing datasets ranging from 100-game exploratory ablations to 35,000-game formal seer-search analyses and 800-game live ML Stage 2A tests.

## Independent Sample Definition

The report records each stage's independent unit separately: games, matched sets, seed-condition cells, decision states, candidate rows, or deterministic replay pairs.

## Implementation

Documentation artifacts are generated by `build_research_progress_artifacts.py` and validated by `validate_research_documentation.py`.

## Validation

Validation checks required files, registry columns, duplicate evidence IDs, conclusion labels, source paths, proposal BoW status, financial-metric status, Stage 2A adjusted p-values, and preservation of revised findings.

## Data Analysis

The Data Analysis contribution of this stage is classificatory rather than computational: it assigns evidence levels, separates descriptive results from formal inference, and records whether confidence intervals, adjusted p-values, robustness, leakage audits, or engine-validity checks exist.

## Descriptive Findings

The project has extensive implementation and experimental coverage. The strongest formal evidence exists for engine/design validation, structured seer-search negative behavioral results, randomized-role rejection of edge-seat folklore, and the harmful Stage 2A hybrid live policy result.

## Formal Inference

No new statistical test is performed in this stage. Formal inference is imported from prior Data Analysis reports and labeled according to its source.

## Robustness

The audit identifies which findings have multi-seed, matched, regime, or replay robustness and which remain single-seed or pilot-level.

## Leakage, Overfitting, And Design Audit

The documentation preserves key revisions: Stage 1 identity AUC was optimistic, surrogate values were weak substitutes for full rollouts, and Stage 1.5 shadow wolf-kill advantage did not generalize to Stage 2A live control.

## Scientific Interpretation

The scientific chain has matured from mechanism-building to artifact-aware validation. The next research step should diagnose why ML wolf-kill shadow value failed in live repeated control.

## Conclusion Label

Conclusion label: `implementation validated` for documentation infrastructure; `hypothesis supported` that cumulative reconstruction clarifies the project state.

## Limitations

The original DURF proposal file was not found in the repository. Proposal alignment therefore uses the user-provided proposal summary and repository evidence.

## Next Hypothesis

ML Stage 2B should test whether offline-to-live failure is driven by policy-induced distribution shift and repeated-decision compounding.

## Source Files

- `build_research_progress_artifacts.py`
- `validate_research_documentation.py`
- `results/research_progress/cumulative_evidence_registry.csv`
- `results/research_progress/cumulative_research_report.md`
- `results/research_progress/durf_proposal_alignment_audit.md`

## Reproducibility Information

Running `python3 build_research_progress_artifacts.py` regenerates the documentation artifacts. Running `python3 validate_research_documentation.py` regenerates validation output.

## Commit Information

The source state before this documentation stage was local `main` at `{head_commit}`, with `origin/main` at `{origin_commit}`. The current documentation commit is recorded after this stage is committed.
""".format(
        head_commit="16ec261e5b50f4560d731cfebab585dd8dfb0ea2",
        origin_commit=SOURCE_COMMIT,
    )


def registry_rows() -> list[dict[str, object]]:
    base = {
        "source_commit": SOURCE_COMMIT,
        "current_documentation_commit": CURRENT_DOCUMENTATION_COMMIT,
        "behavioral_regime_count": "not reported",
        "matched_set_count": "NA",
        "seed_count": "not reported",
        "seed_robustness": "not reported",
        "regime_robustness": "not reported",
        "design_validity": "not reported",
        "engine_validity": "not separately tested",
        "distribution_shift_status": "not assessed",
        "overfitting_status": "not assessed",
        "leakage_status": "not assessed",
        "supersedes_stage_id": "",
        "superseded_by_stage_id": "",
    }

    def row(**kwargs: object) -> dict[str, object]:
        out = dict(base)
        out.update(kwargs)
        return out

    return [
        row(
            stage_id="stage1_baseline",
            stage_name="Low-information baseline",
            research_domain="baseline simulation",
            hypothesis_id="H1_low_information_wolf_advantage",
            hypothesis="Wolves dominate when village agents lack reliable information.",
            prior_hypothesis_source="experiment_report.md",
            experiment_design="7-player Stage 1 ablation with random voting baseline.",
            dataset_path="results/ablation_results.csv",
            report_path="experiment_report.md",
            raw_row_count="6 exported ablation rows; Stage 1 report states 500 games per condition",
            raw_game_count="500 per condition reported in Stage 1 report; current exported CSV has 100 per condition",
            independent_sample_size="games per condition",
            primary_outcome="wolf_win_rate",
            comparison="random_baseline",
            control_condition="NA",
            descriptive_effect="random baseline wolf win 93 percent and village win 7 percent",
            absolute_percentage_point_effect="86 pp wolf-village gap",
            effect_size_type="percentage-point gap",
            effect_size="86 pp",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 1 - descriptive pilot",
            conclusion_label="hypothesis supported",
            hypothesis_status="supported descriptively",
            main_limitation="Stage 1 report and later exported ablation CSV differ on game count; no formal inference.",
            next_hypothesis="Special-role information should reduce wolf advantage.",
        ),
        row(
            stage_id="stage1_special_roles",
            stage_name="Special-role activation",
            research_domain="role mechanics",
            hypothesis_id="H2_special_roles_reduce_wolf_advantage",
            hypothesis="Seer, witch, and hunter mechanics reduce wolf advantage by adding information and intervention.",
            prior_hypothesis_source="experiment_report.md",
            experiment_design="Sequential role-action ablation.",
            dataset_path="results/ablation_results.csv",
            report_path="experiment_report.md",
            raw_row_count="6 exported ablation rows; report table has role-action conditions",
            raw_game_count="500 per condition reported in Stage 1 report",
            independent_sample_size="games per condition",
            primary_outcome="village_win_rate",
            comparison="random_baseline vs witch_action and hunter_action",
            control_condition="random_baseline",
            descriptive_effect="witch_action village win 49 percent; hunter_action village win 46 percent in Stage 1 report",
            absolute_percentage_point_effect="witch plus 42 pp over baseline village win",
            effect_size_type="percentage-point difference",
            effect_size="+42 pp village win for witch_action vs baseline",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 1 - descriptive pilot",
            leakage_status="not applicable",
            conclusion_label="promising but uncertain",
            hypothesis_status="partially supported descriptively",
            main_limitation="Role effects were sequential and not formally isolated.",
            next_hypothesis="Speech and belief mechanisms should further improve village coordination.",
        ),
        row(
            stage_id="stage2_speech",
            stage_name="Speech and information flow",
            research_domain="social information",
            hypothesis_id="H3_speech_improves_village_coordination",
            hypothesis="Speech-like signals and belief updates improve village coordination.",
            prior_hypothesis_source="stage2_experiment_report.md",
            experiment_design="Stage 2 ablation adding speech, p_wolf, herding, role prior, and wolf strategy.",
            dataset_path="results/ablation_results.csv",
            report_path="stage2_experiment_report.md",
            raw_row_count="15 exported ablation rows",
            raw_game_count="100 per condition in current exported CSV",
            independent_sample_size="games per condition",
            primary_outcome="village_win_rate",
            comparison="random_baseline vs speech_enabled",
            control_condition="random_baseline",
            descriptive_effect="current exported CSV shows village win 59 percent under speech_enabled vs 7 percent baseline",
            absolute_percentage_point_effect="+52 pp village win",
            effect_size_type="percentage-point difference",
            effect_size="+52 pp",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 1 - descriptive pilot",
            conclusion_label="promising but uncertain",
            hypothesis_status="supported descriptively",
            main_limitation="Structured speech labels are not full BoW tokenization or quantified text features.",
            next_hypothesis="Trust and credibility should control deceptive speech influence.",
        ),
        row(
            stage_id="stage3_deception",
            stage_name="Wolf deception and credibility costs",
            research_domain="deception",
            hypothesis_id="H4_credibility_costs_constrain_deception",
            hypothesis="Wolf deception can increase wolf advantage, but credibility costs should prevent cost-free manipulation.",
            prior_hypothesis_source="stage3_experiment_report.md",
            experiment_design="Wolf deception strategy diagnostics with false accusation, deflection, role claim, adaptive policy, and credibility penalties.",
            dataset_path="stage3_experiment_report.md",
            report_path="stage3_experiment_report.md",
            raw_row_count="strategy summary tables only",
            raw_game_count="100 per diagnostic condition reported",
            independent_sample_size="games per condition",
            primary_outcome="wolf_win_rate",
            comparison="false_accuse before and after credibility costs",
            control_condition="cost-free false_accuse",
            descriptive_effect="false_accuse fell from 78 percent wolf win to 50 percent after accusation costs; deflection fell to 46 percent after self-defense costs",
            absolute_percentage_point_effect="-28 pp for false_accuse after accusation costs",
            effect_size_type="percentage-point difference",
            effect_size="-28 pp",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 1 - descriptive pilot",
            conclusion_label="promising but uncertain",
            hypothesis_status="supported descriptively",
            main_limitation="No formal multi-seed inference for deception-specific contrasts.",
            next_hypothesis="Speaker-specific trust memory should make deception less effective.",
        ),
        row(
            stage_id="stage4_speaker_memory",
            stage_name="Speaker-specific trust memory",
            research_domain="trust and reputation",
            hypothesis_id="H5_speaker_memory_reduces_deception",
            hypothesis="Speaker-specific trust memory helps villagers resist wolf deception.",
            prior_hypothesis_source="stage4_experiment_report.md",
            experiment_design="Trust vote-weight sensitivity experiment.",
            dataset_path="speaker_memory_sensitivity.py output summarized in stage4_experiment_report.md",
            report_path="stage4_experiment_report.md",
            raw_row_count="summary table only",
            raw_game_count="500 per condition reported",
            independent_sample_size="games per condition",
            seed_count="1",
            primary_outcome="wolf_win_rate",
            comparison="trust_vote_weight 0.40 vs 0.00",
            control_condition="trust_vote_weight 0.00",
            descriptive_effect="wolf win fell from 47.80 percent to 36.40 percent",
            absolute_percentage_point_effect="-11.40 pp",
            effect_size_type="percentage-point difference",
            effect_size="-11.40 pp",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 2 - replicated descriptive experiment",
            conclusion_label="promising but uncertain",
            hypothesis_status="partially supported",
            main_limitation="Single-seed sensitivity and nonmonotonic response.",
            next_hypothesis="Risk preference and larger ten-player games should test robustness of social mechanisms.",
        ),
        row(
            stage_id="ten_player_multi_seed",
            stage_name="Ten-player multi-seed robustness",
            research_domain="larger-game robustness",
            hypothesis_id="H6_mechanisms_generalize_to_ten_players",
            hypothesis="Core mechanisms generalize to a 10-player game.",
            prior_hypothesis_source="ten_player_experiment_report.md",
            experiment_design="Five-seed ten-player summary over six conditions.",
            dataset_path="results/ten_player_multi_seed_summary.md",
            report_path="ten_player_experiment_report.md",
            raw_row_count="summary table only",
            raw_game_count="2500 per condition",
            independent_sample_size="games per condition",
            seed_count="5",
            primary_outcome="village_win_rate",
            comparison="ten_player_speech vs ten_player_baseline",
            control_condition="ten_player_baseline",
            descriptive_effect="speech village mean 65.16 percent vs baseline 43.68 percent",
            absolute_percentage_point_effect="+21.48 pp village win",
            effect_size_type="percentage-point difference",
            effect_size="+21.48 pp",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 2 - replicated descriptive experiment",
            conclusion_label="promising but uncertain",
            hypothesis_status="supported descriptively across seeds",
            main_limitation="Summary lacks formal CIs and p-values.",
            next_hypothesis="Risk preference changes collective resilience and payoff distribution.",
        ),
        row(
            stage_id="risk_preference_multi_seed",
            stage_name="Risk preference multi-seed robustness",
            research_domain="risk preference",
            hypothesis_id="H7_conservative_majority_reduces_wolf_win",
            hypothesis="Conservative-majority populations reduce wolf win rate relative to neutral trust memory.",
            prior_hypothesis_source="risk_preference_experiment_report.md",
            experiment_design="Five-seed ten-player risk-preference robustness with 500 games per seed-condition.",
            dataset_path="results/ten_player_risk_preference_multi_seed_summary.md",
            report_path="risk_preference_experiment_report.md",
            raw_row_count="8 summary rows plus raw multi-seed CSV",
            raw_game_count="2500 per condition",
            independent_sample_size="games per condition and seed-condition cells",
            seed_count="5",
            primary_outcome="wolf_win_rate",
            comparison="ten_player_trust_memory_risk_conservative_majority vs ten_player_trust_memory",
            control_condition="ten_player_trust_memory",
            descriptive_effect="wolf mean 38.56 percent vs 42.96 percent",
            absolute_percentage_point_effect="-4.40 pp",
            effect_size_type="percentage-point difference",
            effect_size="-4.40 pp wolf win",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 2 - replicated descriptive experiment",
            conclusion_label="promising but uncertain",
            hypothesis_status="supported descriptively across seeds",
            main_limitation="No formal statistical contrast reported.",
            next_hypothesis="Position and search strategy should be tested with randomized role assignment.",
        ),
        row(
            stage_id="seer_position_randomized_roles",
            stage_name="Randomized-role seer position",
            research_domain="position theory",
            hypothesis_id="H8_edge_seats_are_more_wolf_heavy",
            hypothesis="Edge seats contain more wolves after randomized role assignment.",
            prior_hypothesis_source="seer_position_randomized_roles_report.md",
            experiment_design="Game-level randomized-role seer-position analysis.",
            dataset_path="results/ten_player_seer_position_randomized_roles_game_level_raw.csv",
            report_path="results/data_analysis/seer_position_game_level/analysis_report.md",
            raw_row_count="17500 game rows",
            raw_game_count="17500",
            independent_sample_size="17500 games",
            seed_count="5",
            primary_outcome="edge seat wolf probability",
            comparison="edge seats vs inner seats",
            control_condition="expected 30 percent role-pool probability",
            descriptive_effect="edge 30.23 percent, inner 29.85 percent, expected 30.00 percent",
            absolute_percentage_point_effect="+0.23 pp edge vs expected",
            effect_size_type="Cramer's V",
            effect_size="0.009",
            confidence_interval="edge CI 29.89 percent to 30.57 percent",
            raw_p_value="0.281",
            adjusted_p_value="not required for single hypergeometric check",
            multiplicity_method="not applied",
            evidence_level="LEVEL 3 - formal statistical analysis",
            seed_robustness="leave-one-seed-out diagnostics performed",
            design_validity="roles randomized across seats",
            conclusion_label="hypothesis rejected",
            hypothesis_status="rejected",
            main_limitation="Simulation-only result.",
            next_hypothesis="Structured search paths may matter more than edge categories.",
        ),
        row(
            stage_id="seer_position_randomized_roles",
            stage_name="Randomized-role seer position",
            research_domain="position theory",
            hypothesis_id="H9_edge_first_improves_village_outcomes",
            hypothesis="Edge-first seer checking improves village outcomes over random after role randomization.",
            prior_hypothesis_source="seer_position_randomized_roles_report.md",
            experiment_design="Seed-adjusted game-level logistic model.",
            dataset_path="results/ten_player_seer_position_randomized_roles_game_level_raw.csv",
            report_path="results/data_analysis/seer_position_game_level/analysis_report.md",
            raw_row_count="17500 game rows",
            raw_game_count="17500",
            independent_sample_size="17500 games",
            seed_count="5",
            primary_outcome="village_win_rate",
            comparison="edge_first vs random",
            control_condition="random",
            descriptive_effect="edge_first first-check wolf 34.20 percent vs random 34.72 percent; adjusted village model OR 1.05",
            absolute_percentage_point_effect="first-check difference -0.52 pp",
            effect_size_type="odds ratio",
            effect_size="1.05",
            confidence_interval="OR CI 0.94 to 1.17",
            raw_p_value="0.417",
            adjusted_p_value="not significant after correction",
            multiplicity_method="Holm for related pairwise tests",
            evidence_level="LEVEL 3 - formal statistical analysis",
            seed_robustness="leave-one-seed-out diagnostics did not reverse conclusion",
            design_validity="randomized role assignment",
            conclusion_label="hypothesis rejected",
            hypothesis_status="rejected",
            main_limitation="Edge-first higher than default but not random; structured path remains separate hypothesis.",
            next_hypothesis="Explicit structured seer search strategies may improve information acquisition.",
        ),
        row(
            stage_id="structured_seer_search",
            stage_name="Structured seer search",
            research_domain="information search",
            hypothesis_id="H10_alternate_sides_outperforms_random",
            hypothesis="Diversified alternate-side seer search outperforms random checking.",
            prior_hypothesis_source="results/structured_seer_search/structured_seer_search_experiment_report.md",
            experiment_design="14-strategy game-level comparison with seed-adjusted logistic models.",
            dataset_path="results/structured_seer_search/structured_seer_search_game_level_raw.csv",
            report_path="results/data_analysis/structured_seer_search/analysis_report.md",
            raw_row_count="35000 game rows",
            raw_game_count="35000",
            independent_sample_size="35000 games",
            seed_count="5",
            primary_outcome="village_win_rate",
            comparison="alternate_sides vs random",
            control_condition="random",
            descriptive_effect="alternate_sides village win 44.16 percent vs random 40.52 percent",
            absolute_percentage_point_effect="+3.64 pp village win",
            effect_size_type="odds ratio",
            effect_size="1.161",
            confidence_interval="OR CI 1.038 to 1.299",
            raw_p_value="0.0092",
            adjusted_p_value="0.0552",
            multiplicity_method="Holm",
            evidence_level="LEVEL 4 - robustness-validated",
            seed_robustness="seed-stratified and leave-one-seed-out summaries",
            design_validity="randomized roles; strategy pre-treatment",
            conclusion_label="promising but uncertain",
            hypothesis_status="unresolved after correction",
            main_limitation="Positive contrast narrowly missed Holm-adjusted significance.",
            next_hypothesis="Seat-order-neutral tests should isolate label and direction artifacts.",
        ),
        row(
            stage_id="structured_seer_search",
            stage_name="Structured seer search",
            research_domain="information search",
            hypothesis_id="H11_behavioral_exploitation_improves_search",
            hypothesis="Using current suspicion or p_wolf should improve seer checking.",
            prior_hypothesis_source="results/data_analysis/structured_seer_search/analysis_report.md",
            experiment_design="Pairwise formal comparisons against random.",
            dataset_path="results/structured_seer_search/structured_seer_search_game_level_raw.csv",
            report_path="results/data_analysis/structured_seer_search/analysis_report.md",
            raw_row_count="35000 game rows",
            raw_game_count="35000",
            independent_sample_size="35000 games",
            seed_count="5",
            primary_outcome="village_win_rate",
            comparison="highest_p_wolf vs random; highest_suspicion vs random",
            control_condition="random",
            descriptive_effect="highest_p_wolf and highest_suspicion were statistically worse than random",
            absolute_percentage_point_effect="-5.64 pp for highest_p_wolf vs random village win",
            effect_size_type="odds ratio",
            effect_size="highest_p_wolf OR 0.786; highest_suspicion OR 0.785",
            confidence_interval="highest_p_wolf OR CI 0.701 to 0.882",
            raw_p_value="0.0000392",
            adjusted_p_value="0.000276",
            multiplicity_method="Holm",
            evidence_level="LEVEL 4 - robustness-validated",
            seed_robustness="seed-stratified and leave-one-seed-out summaries",
            conclusion_label="statistically supported harmful effect",
            hypothesis_status="rejected",
            main_limitation="Applies to current belief dynamics; not all possible behavioral signals.",
            next_hypothesis="Physical path and label artifacts should be tested directly.",
        ),
        row(
            stage_id="seat_order_neutral",
            stage_name="Displayed-label neutralization",
            research_domain="design validity",
            hypothesis_id="H12_displayed_labels_alter_outcomes",
            hypothesis="Displayed seat labels alter physical trajectories or outcomes.",
            prior_hypothesis_source="results/seat_order_neutral/seat_order_neutral_experiment_report.md",
            experiment_design="Normal, mirrored, and rotated label rows for identical physical configurations.",
            dataset_path="results/seat_order_neutral/seat_order_neutral_game_level_raw.csv",
            report_path="results/data_analysis/seat_order_neutral/analysis_report.md",
            raw_row_count="30000 rows",
            raw_game_count="30000 rows with deterministic duplicates",
            independent_sample_size="10000 strategy/base rows",
            matched_set_count="2500 physical configurations",
            seed_count="5",
            primary_outcome="label invariance",
            comparison="normal vs mirrored vs rotated labels",
            control_condition="same physical configuration",
            descriptive_effect="all tested physical trajectories and outcomes matched exactly across label conditions",
            absolute_percentage_point_effect="0 divergences",
            effect_size_type="deterministic equivalence",
            effect_size="100 percent match",
            confidence_interval="not applicable",
            raw_p_value="not applicable",
            adjusted_p_value="not applicable",
            multiplicity_method="not applicable",
            evidence_level="LEVEL 5 - engine/design validated",
            design_validity="displayed-label duplicates identified and collapsed for inference",
            engine_validity="label invariance validated",
            conclusion_label="implementation validated",
            hypothesis_status="rejected for displayed-label artifact",
            main_limitation="Does not alone prove physical clockwise advantage.",
            next_hypothesis="Physical mirror replay should validate engine direction symmetry.",
        ),
        row(
            stage_id="seat_order_neutral",
            stage_name="Seat-order-neutral directional strategies",
            research_domain="position theory",
            hypothesis_id="H13_physical_clockwise_outperforms_random",
            hypothesis="Physical clockwise search outperforms random neutral search.",
            prior_hypothesis_source="results/data_analysis/seat_order_neutral/analysis_report.md",
            experiment_design="Paired physical configuration comparison after collapsing label duplicates.",
            dataset_path="results/seat_order_neutral/seat_order_neutral_game_level_raw.csv",
            report_path="results/data_analysis/seat_order_neutral/analysis_report.md",
            raw_row_count="30000 rows",
            raw_game_count="30000 rows with deterministic duplicates",
            independent_sample_size="10000 strategy/base rows",
            matched_set_count="2500 physical configurations",
            seed_count="5",
            primary_outcome="village_win_rate",
            comparison="physical_clockwise vs random_neutral",
            control_condition="random_neutral",
            descriptive_effect="physical_clockwise village win 43.24 percent vs random_neutral 40.20 percent",
            absolute_percentage_point_effect="+3.04 pp village win",
            effect_size_type="paired difference and OR",
            effect_size="paired OR 1.179",
            confidence_interval="paired difference CI 0.66 to 5.42 pp",
            raw_p_value="0.0136 paired; 0.0293 seed-adjusted",
            adjusted_p_value="0.0814 paired Holm; 0.1758 seed-adjusted Holm",
            multiplicity_method="Holm",
            evidence_level="LEVEL 4 - robustness-validated",
            seed_robustness="seed-stratified table reported",
            design_validity="label duplicates collapsed",
            conclusion_label="promising but uncertain",
            hypothesis_status="unresolved after correction",
            main_limitation="Positive effect did not survive multiple-comparison correction.",
            next_hypothesis="Supplied-action replay should test physical-direction engine symmetry.",
        ),
        row(
            stage_id="physical_direction_replay",
            stage_name="Physical-direction replay validation",
            research_domain="engine validity",
            hypothesis_id="H14_engine_physical_symmetry",
            hypothesis="Supplied-action replay and physical mirror transformations should preserve outcomes if the engine is symmetric.",
            prior_hypothesis_source="results/physical_direction_replay/physical_direction_replay_experiment_report.md",
            experiment_design="Exact supplied-action replay, physical mirror replay, and strategy mirror counterfactual validation.",
            dataset_path="results/physical_direction_replay/supplied_action_replay_game_level_raw.csv",
            report_path="results/physical_direction_replay/physical_direction_replay_experiment_report.md",
            raw_row_count="10000 completed games plus replay-pair summaries",
            raw_game_count="10000 completed games",
            independent_sample_size="8500 replay or mirror pairs across validation summaries",
            matched_set_count="8500 validation pairs",
            seed_count="not central",
            primary_outcome="replay match rate",
            comparison="source vs replay or mirror",
            control_condition="source action trace",
            descriptive_effect="exact replay, physical mirror, and strategy mirror validations all matched at 100 percent",
            absolute_percentage_point_effect="0 divergences",
            effect_size_type="deterministic replay match",
            effect_size="100 percent match",
            confidence_interval="not applicable",
            raw_p_value="not applicable",
            adjusted_p_value="not applicable",
            multiplicity_method="not applicable",
            evidence_level="LEVEL 5 - engine/design validated",
            design_validity="supplied-action trace validation",
            engine_validity="physical mirror symmetry validated",
            conclusion_label="engine symmetry validated",
            hypothesis_status="supported",
            main_limitation="Validation confirms engine symmetry but not strategic superiority.",
            next_hypothesis="ML policy evaluation should use validated matched live-game controls.",
        ),
        row(
            stage_id="ml_stage1",
            stage_name="ML Stage 1 observation-safe pilot",
            research_domain="machine learning",
            hypothesis_id="H15_observation_safe_identity_learning",
            hypothesis="Observation-safe features can learn useful hidden-identity signals.",
            prior_hypothesis_source="results/ml_optimization_stage1/ml_stage1_experiment_report.md",
            experiment_design="Candidate-row identity prediction and action-value pilot.",
            dataset_path="results/ml_optimization_stage1/ml_identity_prediction_dataset.csv",
            report_path="results/ml_optimization_stage1/ml_stage1_research_report.md",
            raw_row_count="7155 candidate rows across decision datasets",
            raw_game_count="60 generated games",
            independent_sample_size="decision states or source game families, not candidate rows",
            matched_set_count="NA",
            seed_count="5",
            primary_outcome="ROC-AUC",
            comparison="village-vote logistic vs existing p_wolf",
            control_condition="existing_p_wolf",
            descriptive_effect="pilot village-vote logistic ROC-AUC 0.9458 vs p_wolf 0.5042",
            absolute_percentage_point_effect="+44.16 AUC points",
            effect_size_type="ROC-AUC difference",
            effect_size="+0.4416",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 1 - descriptive pilot",
            seed_robustness="grouped split by seed but small",
            design_validity="observation-safe feature registry",
            overfitting_status="later Stage 1.5 showed pilot optimism",
            leakage_status="leakage audit passed",
            conclusion_label="weak/inconclusive",
            hypothesis_status="superseded for generalization claims",
            main_limitation="Pilot AUC did not survive strict grouped validation.",
            superseded_by_stage_id="ml_stage15",
            next_hypothesis="Grouped full-state rollout validation should test generalization.",
        ),
        row(
            stage_id="ml_stage15",
            stage_name="ML Stage 1.5 grouped and full-state validation",
            research_domain="machine learning",
            hypothesis_id="H16_grouped_identity_generalization",
            hypothesis="Stage 1 identity models retain strong signal under grouped validation.",
            prior_hypothesis_source="results/ml_optimization_stage1/ml_stage1_experiment_report.md",
            experiment_design="Grouped split identity generalization across regimes.",
            dataset_path="results/ml_optimization_stage15/ml_identity_generalization_metrics.csv",
            report_path="results/ml_optimization_stage15/ml_stage15_research_report.md",
            raw_row_count="976 candidate rows",
            raw_game_count="84 source game families",
            independent_sample_size="source game families and grouped decision states",
            matched_set_count="NA",
            seed_count="6 source seeds",
            behavioral_regime_count="7",
            primary_outcome="ROC-AUC",
            comparison="village-vote logistic vs existing p_wolf on final test",
            control_condition="existing_p_wolf",
            descriptive_effect="logistic ROC-AUC 0.6679 vs existing p_wolf 0.6586",
            absolute_percentage_point_effect="+0.93 AUC points",
            effect_size_type="ROC-AUC difference",
            effect_size="+0.0092",
            confidence_interval="not reported",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 3 - formal validation design",
            seed_robustness="cross-seed metrics exported",
            regime_robustness="cross-regime metrics exported",
            overfitting_status="some diagnostics flagged; pilot optimism revised",
            leakage_status="leakage audit performed",
            conclusion_label="weak/inconclusive",
            hypothesis_status="partially rejected; signal much weaker than pilot",
            supersedes_stage_id="ml_stage1",
            next_hypothesis="Full rollout action-value policies should be tested in shadow mode only.",
        ),
        row(
            stage_id="ml_stage15",
            stage_name="ML Stage 1.5 full-state rollout validation",
            research_domain="machine learning",
            hypothesis_id="H17_surrogate_values_approximate_full_rollouts",
            hypothesis="Surrogate action values approximate full simulator rollout values.",
            prior_hypothesis_source="results/ml_optimization_stage1/ml_stage1_experiment_report.md",
            experiment_design="Surrogate-vs-full rollout validation over seer, wolf-kill, and vote actions.",
            dataset_path="results/ml_optimization_stage15/ml_surrogate_validity_metrics.csv",
            report_path="results/ml_optimization_stage15/ml_stage15_research_report.md",
            raw_row_count="6832 full rollouts; 976 candidate rows",
            raw_game_count="84 source game families",
            independent_sample_size="244 decision states",
            matched_set_count="NA",
            seed_count="6 source seeds",
            behavioral_regime_count="7",
            primary_outcome="Spearman rank correlation",
            comparison="surrogate value vs full rollout value",
            control_condition="full rollout value",
            descriptive_effect="seer Spearman 0.299 partial; wolf-kill 0.072 weak; day-vote 0.242 weak",
            absolute_percentage_point_effect="not a percentage-point outcome",
            effect_size_type="Spearman correlation",
            effect_size="wolf-kill 0.0718",
            confidence_interval="not reported in primary table",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 4 - robustness-validated",
            seed_robustness="cross-seed metrics exported",
            regime_robustness="cross-regime metrics exported",
            conclusion_label="weak/inconclusive",
            hypothesis_status="mostly rejected",
            main_limitation="Full-rollout sample remained modest.",
            next_hypothesis="Only live matched games can validate deployed policy value.",
        ),
        row(
            stage_id="ml_stage15",
            stage_name="ML Stage 1.5 shadow wolf-kill policy",
            research_domain="machine learning",
            hypothesis_id="H18_shadow_wolf_kill_policy_improves_value",
            hypothesis="A shadow ML wolf-kill action-value recommendation improves wolf-team value.",
            prior_hypothesis_source="results/ml_optimization_stage15/ml_stage15_experiment_report.md",
            experiment_design="Shadow policy comparison on grouped final-test decision states.",
            dataset_path="results/ml_optimization_stage15/ml_shadow_policy_comparison.csv",
            report_path="results/ml_optimization_stage15/ml_stage15_research_report.md",
            raw_row_count="24 shadow summary rows",
            raw_game_count="84 source game families overall",
            independent_sample_size="decision states by split and action type",
            matched_set_count="NA",
            seed_count="6 source seeds",
            behavioral_regime_count="7",
            primary_outcome="mean_policy_value",
            comparison="wolf_kill ml_action_value_recommendation vs existing on final test",
            control_condition="existing rule value",
            descriptive_effect="final-test shadow value 0.850 vs existing 0.700",
            absolute_percentage_point_effect="+0.150 action value",
            effect_size_type="mean action-value difference",
            effect_size="+0.150",
            confidence_interval="bootstrap CIs available in source artifacts but not transcribed here",
            raw_p_value="not reported",
            adjusted_p_value="not reported",
            multiplicity_method="not applied",
            evidence_level="LEVEL 3 - formal validation design",
            overfitting_status="shadow-only; later live Stage 2A contradicted",
            conclusion_label="surrogate-only improvement",
            hypothesis_status="superseded by live Stage 2A",
            superseded_by_stage_id="ml_stage2a",
            next_hypothesis="Freeze and test the wolf-kill model in live matched complete games.",
        ),
        row(
            stage_id="ml_stage2a",
            stage_name="ML Stage 2A frozen wolf-kill live experiment",
            research_domain="machine learning",
            hypothesis_id="H19_frozen_ml_improves_live_wolf_win",
            hypothesis="A frozen ML wolf-kill policy improves live wolf win rate over the existing rule.",
            prior_hypothesis_source="results/ml_optimization_stage15/ml_stage15_research_report.md",
            experiment_design="Matched live complete-game policy comparison.",
            dataset_path="results/ml_optimization_stage2a/wolf_kill_live_game_level_raw.csv",
            report_path="results/ml_optimization_stage2a/ml_stage2a_research_report.md",
            raw_row_count="800 live game rows; 2600 live decision rows; 14380 prediction rows",
            raw_game_count="800",
            independent_sample_size="200 matched sets",
            matched_set_count="200",
            seed_count="20 live final seeds",
            behavioral_regime_count="multiple live regimes reported",
            primary_outcome="wolf_win_rate",
            comparison="frozen_ml vs existing_rule",
            control_condition="existing_rule",
            descriptive_effect="wolf win fell from 69.50 percent to 61.00 percent",
            absolute_percentage_point_effect="-8.50 pp",
            effect_size_type="discordant matched odds ratio",
            effect_size="0.5696",
            confidence_interval="difference CI [-16.08, -0.92] pp",
            raw_p_value="0.0396",
            adjusted_p_value="0.0792",
            multiplicity_method="Holm",
            evidence_level="LEVEL 4 - robustness-validated",
            seed_robustness="20 final seeds assessed",
            regime_robustness="regime robustness exported",
            distribution_shift_status="candidate rows include substantial strong-shift subset",
            overfitting_status="live harmful in pilot; not simple overfitting flag",
            leakage_status="information-leakage audit passed",
            conclusion_label="weak/inconclusive",
            hypothesis_status="rejected in pilot after correction",
            supersedes_stage_id="ml_stage15",
            next_hypothesis="ML Stage 2B should diagnose offline-to-live failure.",
        ),
        row(
            stage_id="ml_stage2a",
            stage_name="ML Stage 2A frozen hybrid live experiment",
            research_domain="machine learning",
            hypothesis_id="H20_hybrid_improves_live_wolf_win",
            hypothesis="A 50/50 ML-rule hybrid improves or remains competitive with the existing rule.",
            prior_hypothesis_source="results/ml_optimization_stage2a/ml_stage2a_pre_registration.md",
            experiment_design="Matched live complete-game policy comparison.",
            dataset_path="results/ml_optimization_stage2a/wolf_kill_live_game_level_raw.csv",
            report_path="results/ml_optimization_stage2a/ml_stage2a_research_report.md",
            raw_row_count="800 live game rows; 2600 live decision rows; 14380 prediction rows",
            raw_game_count="800",
            independent_sample_size="200 matched sets",
            matched_set_count="200",
            seed_count="20 live final seeds",
            behavioral_regime_count="multiple live regimes reported",
            primary_outcome="wolf_win_rate",
            comparison="frozen_hybrid_50_50 vs existing_rule",
            control_condition="existing_rule",
            descriptive_effect="wolf win fell from 69.50 percent to 58.00 percent",
            absolute_percentage_point_effect="-11.50 pp",
            effect_size_type="discordant matched odds ratio",
            effect_size="0.3521",
            confidence_interval="difference CI [-18.04, -4.96] pp",
            raw_p_value="0.0011",
            adjusted_p_value="0.0033",
            multiplicity_method="Holm",
            evidence_level="LEVEL 4 - robustness-validated",
            seed_robustness="20 final seeds assessed",
            regime_robustness="regime robustness exported",
            distribution_shift_status="candidate rows include substantial strong-shift subset",
            overfitting_status="live harmful in pilot",
            leakage_status="information-leakage audit passed",
            conclusion_label="statistically supported harmful effect",
            hypothesis_status="rejected",
            supersedes_stage_id="ml_stage15",
            next_hypothesis="Diagnose whether hybrid diluted special-role targeting and compounded state drift.",
        ),
        row(
            stage_id="ml_stage2a",
            stage_name="ML Stage 2A epsilon live experiment",
            research_domain="machine learning",
            hypothesis_id="H21_epsilon_ml_improves_live_wolf_win",
            hypothesis="A 10 percent epsilon-greedy ML policy improves live wolf win rate while reducing brittleness.",
            prior_hypothesis_source="results/ml_optimization_stage2a/ml_stage2a_pre_registration.md",
            experiment_design="Matched live complete-game policy comparison.",
            dataset_path="results/ml_optimization_stage2a/wolf_kill_live_game_level_raw.csv",
            report_path="results/ml_optimization_stage2a/ml_stage2a_research_report.md",
            raw_row_count="800 live game rows; 2600 live decision rows; 14380 prediction rows",
            raw_game_count="800",
            independent_sample_size="200 matched sets",
            matched_set_count="200",
            seed_count="20 live final seeds",
            behavioral_regime_count="multiple live regimes reported",
            primary_outcome="wolf_win_rate",
            comparison="frozen_ml_epsilon_010 vs existing_rule",
            control_condition="existing_rule",
            descriptive_effect="wolf win fell from 69.50 percent to 61.00 percent",
            absolute_percentage_point_effect="-8.50 pp",
            effect_size_type="discordant matched odds ratio",
            effect_size="0.5802",
            confidence_interval="difference CI [-16.21, -0.79] pp",
            raw_p_value="0.0430",
            adjusted_p_value="0.0792",
            multiplicity_method="Holm",
            evidence_level="LEVEL 4 - robustness-validated",
            seed_robustness="20 final seeds assessed",
            regime_robustness="regime robustness exported",
            distribution_shift_status="candidate rows include substantial strong-shift subset",
            overfitting_status="live harmful in pilot",
            leakage_status="information-leakage audit passed",
            conclusion_label="weak/inconclusive",
            hypothesis_status="rejected in pilot after correction",
            supersedes_stage_id="ml_stage15",
            next_hypothesis="Diagnose whether exploration changes repeated-decision state drift.",
        ),
    ]


def cumulative_report() -> str:
    return """
# DURF Werewolf Cumulative Research Report

## 1. Original Proposal and Research Questions

The project uses Werewolf as a controlled environment for hidden-information decision making. The proposal commitments include a 10-player simulation, Bag-of-Words speech quantification, suspicion and credibility decisions, herding, coordinated wolf behavior, role-specific payoff optimization, financial-market analogies, risk and opportunity-cost analysis, 10,000+ simulations, a final report, and a DURF presentation.

The original proposal file was not found in the repository during this audit. Proposal alignment therefore uses the user-provided proposal summary and repository evidence.

## 2. Simulation Environment

The repository implements a modular Python simulation with roles, players, game state, night/day phases, win conditions, randomized role assignment, event logs, and batch simulation. Both 7-player and 10-player settings are represented. The 10-player setup matches the proposal role pool: 3 wolves, 4 villagers, seer, witch, and hunter.

## 3. Payoff and Role Framework

Payoff calculation exists and has been used in ablation, ten-player, risk-preference, and ML outputs. However, a unified role-specific payoff matrix and formal payoff-optimization synthesis remain incomplete. Risk-adjusted return and Sharpe-like metrics are not yet fully implemented as formal financial analogues.

## 4. Low-Information Baseline

Question: Does the baseline expose a real hidden-information problem?

Hypothesis: Wolves dominate when village agents lack reliable information.

Design: Stage 1 ablation with random voting and no information mechanisms.

Evidence: The Stage 1 report gives random baseline wolf win 93% and village win 7%.

Formal analysis: Not performed; descriptive pilot only.

Conclusion: `hypothesis supported` descriptively. This baseline motivates all later information mechanisms.

## 5. Special-Role Actions

Question: Do seer, witch, and hunter mechanics reduce wolf dominance?

Hypothesis: Special roles add information and intervention value for the village.

Design: Sequential Stage 1 ablations.

Evidence: Stage 1 report shows seer_action village win 23%, witch_action 49%, and hunter_action 46%.

Formal analysis: Not performed.

Conclusion: `promising but uncertain`. Special roles matter, but effects were sequential and not fully isolated.

## 6. Speech and Information Flow

Question: Do speech-like signals turn voting into a social inference process?

Hypothesis: Speech, belief updating, and role priors improve village coordination.

Design: Stage 2 added structured speech acts, `p_wolf`, suspicion updates, herding, and role prior.

Evidence: Current exported ablation results show speech_enabled village win 59% versus 7% baseline, but Stage 2 values are exploratory and some report versions differ.

Formal analysis: Not performed for the early Stage 2 ablation.

Conclusion: `promising but uncertain`. Structured speech labels are not yet full Bag-of-Words text quantification.

## 7. Herding

Question: Does group pressure improve voting?

Hypothesis: Herding can amplify useful signals but may also amplify noise.

Design: Stage 2 and Stage 4 trust-weighted herding experiments.

Evidence: Stage 2 suggested herding added value beyond speech in exploratory runs. Later multi-seed summaries showed trust-weighted herding changed outcomes but did not always monotonically improve village performance.

Formal analysis: Not yet fully formalized for herding-specific claims.

Conclusion: `promising but uncertain`.

## 8. Wolf Strategy and Deception

Question: Can wolves regain advantage through night strategy and daytime deception?

Hypothesis: Deception helps wolves unless credibility costs penalize manipulation.

Design: Wolf night-kill diagnostics, wolf daytime deception policies, accusation costs, wrong-accusation penalties, and self-defense costs.

Evidence: `false_accuse` reached 78% wolf win before costs, then fell to 50% after accusation costs. Deflection fell to 46% after self-defense costs.

Formal analysis: Mostly descriptive diagnostics.

Conclusion: `promising but uncertain`. Deception matters, and credibility costs are necessary.

## 9. Risk Preference

Question: Does risk appetite alter collective resilience and payoff?

Hypothesis: Conservative populations should reduce false-positive eliminations and lower wolf win rate.

Design: Ten-player risk-preference multi-seed experiment.

Evidence: Conservative-majority trust memory had wolf mean 38.56% versus 42.96% for neutral trust memory. Aggressive-majority trust memory had wolf mean 50.96%.

Formal analysis: Replicated descriptive multi-seed summary, without formal contrast p-values.

Conclusion: `promising but uncertain`.

## 10. Position Theory

Question: Are edge seats inherently informative?

Hypothesis: Edge seats contain more wolves or edge-first checking improves village outcomes.

Design: Randomized-role seer-position experiments and game-level Data Analysis.

Evidence: Edge seat wolf probability was 30.23%, inner was 29.85%, and expected was 30.00%. Edge-first versus random adjusted OR was 1.05, p = 0.417.

Formal analysis: Formal game-level analysis exists.

Conclusion: `hypothesis rejected` for strong edge-seat theory after role randomization.

## 11. Structured Seer Search

Question: Do structured search paths beat random checking?

Hypothesis: Diversified search paths such as alternate_sides improve village win rate.

Design: 14-strategy, 35,000-game structured seer search with formal Data Analysis.

Evidence: Alternate_sides had 44.16% village win versus random 40.52%, OR 1.161, raw p = 0.0092, Holm p = 0.0552. Highest_p_wolf and highest_suspicion were statistically worse than random, Holm p = 0.000276.

Conclusion: Structured diversification is `promising but uncertain`; behavioral exploitation has a `statistically supported harmful effect`.

## 12. Seat-Order and Label Validity

Question: Are directional results artifacts of displayed labels?

Hypothesis: Neutralizing displayed labels should expose whether label order changes outcomes.

Design: Seat-order-neutral experiment with normal, mirrored, and rotated labels.

Evidence: Displayed-label invariance was exact across all tested physical trajectories and outcomes. Source rows were 30,000, but effective independent sample for strategy inference was 10,000 strategy/base rows and 2,500 physical configurations.

Conclusion: Displayed-label artifact rejected; physical clockwise advantage remains `promising but uncertain`.

## 13. Physical-Direction Engine Validation

Question: Is the engine physically mirror-symmetric under supplied actions?

Hypothesis: Replay and mirror transforms should preserve trajectories and outcomes if the engine is symmetric.

Design: Supplied-action replay and physical mirror validation.

Evidence: Exact replay, physical mirror replay, and strategy mirror action validation all matched at 100% with zero divergences.

Conclusion: `engine symmetry validated`.

## 14. Machine Learning Stage 1

Question: Can observation-safe features support ML identity and action models?

Hypothesis: Public and actor-available features contain useful signal.

Evidence: Stage 1 generated 7,155 candidate rows and reported village-vote logistic ROC-AUC 0.9458.

Formal analysis: Pilot only. The result was later revised by Stage 1.5.

Conclusion: `weak/inconclusive` for generalization; `implementation validated` for logging.

## 15. Machine Learning Stage 1.5

Question: Do ML signals survive grouped splits and full-state rollouts?

Hypothesis: Grouped validation and full rollouts should retain meaningful ML value.

Evidence: Village-vote ROC-AUC fell to 0.6679, close to existing `p_wolf` at 0.6586. Surrogate validity was weak for wolf-kill action value, with Spearman 0.0718. A final-test shadow wolf-kill recommendation still appeared promising with +0.150 action value.

Conclusion: `surrogate-only improvement` for shadow wolf-kill; not ready as a live policy.

## 16. Machine Learning Stage 2A

Question: Does the frozen ML wolf-kill policy improve live complete-game wolf win rate?

Hypothesis: Frozen ML, hybrid, and epsilon policies should outperform or match the existing rule.

Evidence: Existing rule wolf win was 69.50%. Frozen ML and epsilon were 61.00%, and hybrid was 58.00%. Hybrid difference was -11.50 pp with Holm p = 0.0033.

Conclusion: Hybrid has a `statistically supported harmful effect`; pure ML and epsilon are `weak/inconclusive` but harmful in direction. Existing rule remains default.

## 17. Cross-Stage Data Analysis Lessons

Raw rows are not always independent. Candidate rows are not games. Deterministic label duplicates must be collapsed. Shadow values are not live policy values. Model coefficients are not causal effects. Post-treatment variables such as first-check success and seer survival are diagnostic unless explicitly randomized.

## 18. Current Scientific Conclusions

The project supports the claim that information, credibility, and search structure shape social-deduction outcomes. It rejects strong edge-seat folklore after role randomization. It validates engine symmetry. It also shows that ML policies require live matched validation and can be harmful even after apparently promising shadow analysis.

## 19. Proposal Alignment

The project has completed and extended the core simulator, night/day mechanics, role actions, suspicion, credibility, herding, wolf coordination, competing seer scenarios, 10,000+ simulations, Data Analysis, visualization, and presentation outputs. It has partially completed payoff and financial-market interpretation. Formal BoW tokenization, quantified emotional intensity, information density, unified payoff optimization, risk-adjusted return, Sharpe-like analysis, and systematic literature comparison remain incomplete.

## 20. Remaining Deliverables

Remaining deliverables are ordered in `remaining_work_roadmap.md`: ML Stage 2B failure diagnosis, formal BoW speech quantification, BoW integration, unified role-specific payoff matrix, financial risk metrics, role strategy optimization synthesis, systematic literature comparison, final integrated Data Analysis, and final DURF report/presentation.

## 21. Next Research Priorities

The exact next stage is ML Stage 2B - Offline-to-Live Failure Diagnosis. It should diagnose policy-induced distribution shift, repeated-decision compounding, special-role targeting loss, and shadow/live mismatch before any new ML policy is deployed.

## 22. Reproducibility and Source Index

The cumulative evidence registry is `results/research_progress/cumulative_evidence_registry.csv`. Source traceability is `results/research_progress/source_traceability_index.csv`. Known inconsistencies are documented in `results/research_progress/documentation_inconsistencies.md`.
"""


def proposal_matrix_rows() -> list[dict[str, object]]:
    data = [
        ("Classic 10-player simulator", "10-player Werewolf with 4 villagers, seer, witch, hunter, and 3 wolves.", "completed_and_extended", "10-player reports and multi-seed outputs exist.", "ten_player_experiment_report.md; results/ten_player_multi_seed_summary.md", "High", "None for simulator core.", "None", "Low", "No"),
        ("Night/day mechanics", "Automated night and day phases with win conditions.", "completed_and_extended", "Core game loop and experiments run complete games.", "game.py; simulation.py", "High", "None for current scope.", "None", "Low", "No"),
        ("Role-specific actions", "Seer, witch, hunter, and wolves act according to role.", "completed_and_extended", "Role action modules and validations exist.", "seer_action.py; witch_action.py; hunter_action.py", "High", "Formal role-specific synthesis still useful.", "R4", "Medium", "No"),
        ("Suspicion system", "Agents use suspicion-based decisions.", "completed_and_extended", "suspicion_score, p_wolf, voting, and updates implemented.", "voting.py; belief_update.py", "High", "Calibration summary needed in final report.", "R8", "Low", "No"),
        ("Credibility/trust", "Credibility and trust affect decisions.", "completed_and_extended", "Credibility costs, speaker memory, trust-weighted voting/speech/herding implemented.", "deception_credibility.py; speaker_memory.py; trust_update.py", "High", "Formal synthesis across trust variants needed.", "R8", "Medium", "No"),
        ("Herding", "Group pressure affects decisions.", "completed_and_extended", "Herding and trust-weighted herding implemented.", "herding.py; trust_weighted_herding_experiment.py", "Medium", "Formal herding-specific inference incomplete.", "R8", "Medium", "No"),
        ("Wolf coordination", "Wolves coordinate behavior strategically.", "completed_by_alternative_implementation", "Night-kill strategies and deception policies implemented; full multi-wolf coordination remains simplified.", "wolf_strategy.py; wolf_deception.py", "Medium", "Explicit coordinated multi-wolf daytime planning not implemented.", "R6", "Medium", "No"),
        ("Competing seer scenarios", "Alternative seer strategies are compared.", "completed_and_extended", "Randomized-role, structured search, neutral-mode, and replay analyses exist.", "results/data_analysis/structured_seer_search/analysis_report.md", "High", "Final synthesis needed.", "R8", "Low", "No"),
        ("Aggression vs deep cover", "Compare aggressive and hidden/deep-cover wolf behavior.", "completed_by_alternative_implementation", "Risk preference and deception strategies approximate aggression/cover tradeoffs.", "risk_preference_experiment_report.md; stage3_experiment_report.md", "Medium", "No explicit deep-cover formal metric.", "R6", "Medium", "No"),
        ("Bag-of-Words vocabulary", "BoW speech vocabulary.", "partially_completed", "Structured speech labels exist, but not full BoW tokenization.", "bow_lexicon.py; speech_action.py", "Low-Medium", "Implement formal token features.", "R2", "High", "Yes"),
        ("Speech text tokenization", "Tokenize speech text.", "not_started", "No formal text tokenization found.", "MISSING:speech text tokenizer", "Low", "Create tokenization and validation.", "R2", "High", "Yes"),
        ("Werewolf-leaning speech score", "Quantify wolf-leaning speech.", "partially_completed", "p_wolf and speech effects exist, but no formal BoW wolf-leaning text score.", "belief_update.py; bow_lexicon.py", "Low-Medium", "Define and validate score.", "R2", "High", "Yes"),
        ("Emotional-intensity score", "Quantify emotional intensity.", "not_started", "No emotional-intensity metric found.", "MISSING:emotional intensity metric", "Low", "Implement metric and experiment.", "R2", "High", "Yes"),
        ("Information-density score", "Quantify information density.", "not_started", "No information-density metric found.", "MISSING:information density metric", "Low", "Implement metric and experiment.", "R2", "High", "Yes"),
        ("BoW integration into decisions", "Use BoW features in decisions.", "partially_completed", "Structured speech labels influence beliefs, but full BoW does not.", "speech_action.py; belief_update.py", "Medium", "Integrate formal BoW scores.", "R3", "High", "Yes"),
        ("Role-specific payoff matrix", "Define payoff matrix by role.", "partially_completed", "Payoff exists but unified formal matrix not synthesized.", "payoff.py; experiment_report.md", "Medium", "Build unified matrix.", "R4", "High", "Yes"),
        ("Villager payoff", "Villager payoff result.", "requires_formal_analysis", "Average village payoff appears in reports.", "experiment_report.md; results/ablation_results.csv", "Medium", "Synthesize role-specific payoff.", "R4", "Medium", "No"),
        ("Seer payoff", "Seer payoff result.", "requires_formal_analysis", "Role-specific payoff not fully synthesized.", "payoff.py", "Low-Medium", "Extract seer payoff by condition.", "R4", "Medium", "Yes"),
        ("Witch payoff", "Witch payoff result.", "requires_formal_analysis", "Witch-related events and payoff exist; formal role payoff missing.", "witch_action.py; payoff.py", "Low-Medium", "Extract witch payoff.", "R4", "Medium", "Yes"),
        ("Hunter payoff", "Hunter payoff result.", "requires_formal_analysis", "Hunter actions exist; formal role payoff missing.", "hunter_action.py; payoff.py", "Low-Medium", "Extract hunter payoff.", "R4", "Medium", "Yes"),
        ("Werewolf payoff", "Werewolf payoff result.", "requires_formal_analysis", "Average wolf payoff reported in some summaries.", "experiment_report.md; results/ablation_results.csv", "Medium", "Formal cross-stage payoff synthesis.", "R4", "Medium", "No"),
        ("Risk cost", "Cost of risky action.", "partially_completed", "Risk preference experiments approximate risk behavior.", "risk_preference_experiment_report.md", "Medium", "Define explicit risk cost metric.", "R5", "High", "Yes"),
        ("Opportunity cost", "Opportunity cost of strategy choice.", "partially_completed", "ML regret and policy regret approximate opportunity cost.", "results/ml_optimization_stage15/ml_policy_regret_full_rollout.csv", "Medium", "Unify across roles and strategies.", "R5", "Medium", "No"),
        ("Expected payoff", "Expected payoff by strategy.", "requires_formal_analysis", "Average payoff reported, but not unified.", "results/ablation_results.csv", "Medium", "Formal payoff table by role/condition.", "R4", "High", "Yes"),
        ("Payoff variance", "Variance of payoff.", "not_started", "No unified payoff variance analysis found.", "MISSING:payoff variance analysis", "Low", "Compute variance by role and condition.", "R5", "High", "Yes"),
        ("Risk-adjusted return", "Risk-adjusted return metric.", "not_started", "No formal risk-adjusted return metric found.", "MISSING:risk-adjusted return analysis", "Low", "Define and compute.", "R5", "High", "Yes"),
        ("Sharpe-ratio analogue", "Sharpe-like payoff ratio.", "not_started", "No Sharpe-like metric found.", "MISSING:Sharpe-like analysis", "Low", "Define denominator and baseline.", "R5", "High", "Yes"),
        ("Financial-market interpretation", "Connect simulation to markets.", "partially_completed", "Conceptual analogies appear in reports and outlines.", "final_research_report_outline.md; risk_preference_experiment_report.md", "Medium", "Formal financial metrics incomplete.", "R5", "Medium", "No"),
        ("Retail-investor analogy", "Villagers as retail investors.", "requires_documentation", "Conceptual analogy exists in outline, not fully formalized.", "final_research_report_outline.md", "Medium", "Write final report section.", "R9", "Medium", "No"),
        ("Informed-trader/analyst analogy", "Special roles as informed actors.", "requires_documentation", "Conceptual analogy exists.", "final_research_report_outline.md", "Medium", "Write final report section.", "R9", "Medium", "No"),
        ("Regulator/central-bank analogy", "Special roles as regulators or central bank analogues.", "requires_documentation", "Conceptual analogy listed in proposal summary; limited repo evidence.", "MISSING:proposal original file", "Low", "Decide whether scientifically justified.", "R7", "Medium", "No"),
        ("Market-manipulator analogy", "Werewolves as manipulators.", "requires_documentation", "Deception results support conceptual analogy.", "stage3_experiment_report.md", "Medium", "Tie to financial manipulation literature.", "R7", "Medium", "No"),
        ("10,000+ simulations", "Run at least 10,000 simulations.", "completed_and_extended", "Several analyses exceed 10,000 games, including 35,000 structured search games.", "results/structured_seer_search/structured_seer_search_game_level_raw.csv", "High", "None.", "None", "Low", "No"),
        ("Data Analysis", "Analyze outcomes and strategies.", "completed_and_extended", "Formal Data Analysis outputs exist for seer position, structured search, seat-order neutral, and ML Stage 2A.", "results/data_analysis/", "High", "Fill gaps for payoff and BoW.", "R8", "Medium", "No"),
        ("Visualization", "Create visual outputs.", "completed_and_extended", "SVG analysis plots and PPT exist.", "results/data_analysis/structured_seer_search/village_win_rate_by_strategy.svg; DURF_Werewolf_Full_Research_Progress_Report.pptx", "High", "Final figure selection.", "R9", "Low", "No"),
        ("Literature cross-check", "Compare with literature.", "not_started", "No systematic literature comparison found.", "MISSING:literature review", "Low", "Conduct literature cross-check.", "R7", "High", "Yes"),
        ("Final written report", "Create final written report.", "partially_completed", "Outline and stage reports exist, final report not complete.", "final_research_report_outline.md", "Medium", "Write final integrated report.", "R9", "High", "Yes"),
        ("Final DURF presentation", "Create DURF presentation.", "completed", "PPT and slide outline exist.", "DURF_Werewolf_Full_Research_Progress_Report.pptx; DURF_Werewolf_Full_Research_Progress_Slide_Outline.md", "Medium-High", "May need final factual refresh.", "R9", "Medium", "No"),
        ("Reproducibility documentation", "Document seeds, code, schemas, and source files.", "partially_completed", "Schemas and reproducibility scripts exist; cumulative standard added now.", "results/research_progress/permanent_stage_reporting_standard.md", "Medium", "Keep updating per stage.", "All future stages", "High", "No"),
    ]
    return [
        {
            "proposal_component": row[0],
            "original_proposal_description": row[1],
            "status": row[2],
            "evidence": row[3],
            "source_file": row[4],
            "quality_of_completion": row[5],
            "remaining_work": row[6],
            "required_next_stage": row[7],
            "priority": row[8],
            "blocking_final_report": row[9],
        }
        for row in data
    ]


def proposal_alignment_audit() -> str:
    return """
# DURF Proposal Alignment Audit

## Source Note

The original DURF proposal file was not found in the repository during this audit. This alignment uses the proposal commitments supplied in the current task prompt and repository evidence files. Any final report should replace this source note with a citation to the original proposal if the proposal file is later added.

## Summary

The project has completed and extended the core simulator, 10-player setup, role mechanics, suspicion and credibility systems, wolf strategy, competing seer scenarios, large-scale simulations, Data Analysis outputs, visualization, and presentation materials. It has partially completed payoff and financial analogy work. It has not yet completed formal Bag-of-Words tokenization, emotional intensity, information density, unified role-specific payoff optimization, risk-adjusted return, Sharpe-like analysis, or systematic literature comparison.

## Completed Or Extended

- Classic 10-player simulator.
- Night/day mechanics.
- Role-specific actions.
- Suspicion system.
- Credibility and trust.
- Herding.
- Wolf night strategy and deception.
- Competing seer scenarios.
- 10,000+ simulations.
- Data Analysis and visualization.
- DURF progress presentation.

## Partially Completed

- Bag-of-Words vocabulary: structured labels exist, but formal text tokenization and proposed quantitative scores do not.
- Role-specific payoff matrix: payoff functions and summary payoffs exist, but the unified matrix and role-level synthesis are incomplete.
- Financial-market interpretation: conceptual analogies exist, but formal risk metrics are incomplete.
- Reproducibility documentation: many schemas exist, and this stage adds a permanent standard, but future stages must keep it current.

## Not Yet Completed

- Speech text tokenization.
- Werewolf-leaning speech score as a true BoW metric.
- Emotional-intensity score.
- Information-density score.
- Payoff variance.
- Risk-adjusted return.
- Sharpe-ratio analogue.
- Systematic literature cross-check.
- Final integrated written report.

## Requires A New Experiment

- Formal BoW quantification and BoW-driven decisions.
- Unified role-specific payoff and risk-adjusted payoff analysis.
- ML Stage 2B offline-to-live failure diagnosis.

## Requires Documentation Only

- Financial-market analogy can be strengthened using existing deception, risk, and trust results, but quantitative financial metrics still require new analysis.
- Retail-investor, informed-trader, regulator, and manipulator analogies require a final report synthesis and literature cross-check.

## Matrix

The full component-by-component audit is in `results/research_progress/durf_proposal_alignment_matrix.csv`.
"""


def current_progress_assessment() -> str:
    return """
# Current Progress Assessment

## A. Technical Implementation Completion

Qualitative status: high.

The core simulation, 10-player game, special roles, speech-like labels, belief updates, herding, trust memory, deception, risk preference, position strategy, replay validation, and ML logging/policy infrastructure are implemented. The project has substantially exceeded the original basic simulation requirement.

## B. Scientific-Analysis Completion

Qualitative status: medium-high.

Formal Data Analysis exists for randomized-role seer position, structured seer search, seat-order-neutral analysis, physical replay validation, and ML Stage 2A. Some earlier mechanism stages remain descriptive only. Payoff, financial risk, and BoW-specific claims still need formal synthesis.

## C. Proposal-Alignment Completion

Qualitative status: medium.

Core simulator commitments are complete or extended. BoW quantification, unified role payoff optimization, financial risk metrics, Sharpe-like analysis, and literature cross-check remain incomplete.

## D. Documentation Completion

Qualitative status: improving; currently medium-high after this stage.

This stage creates missing ML research reports, cumulative evidence registry, cumulative report, proposal audit, source traceability, roadmap, permanent reporting standard, inconsistencies log, and validation summary.

## E. Final-Report Readiness

Qualitative status: not yet final-report ready, but close for simulation/mechanism chapters.

The project is ready to draft strong sections on simulation design, information flow, deception, trust, seer search, engine validity, and ML validation failure. It is not ready to finalize BoW quantification, financial risk metrics, unified role-specific payoff optimization, or literature comparison.

## Expected Assessment

- Core simulation: completed and extended.
- Game mechanics: completed.
- Large-scale simulation: completed and extended.
- Data Analysis: advanced.
- Engine validity: strongly validated.
- ML optimization: active, with negative live Stage 2A result.
- BoW: incomplete.
- Unified payoff matrix: incomplete.
- Financial risk metrics: incomplete.
- Systematic literature comparison: incomplete.
- Final cumulative reporting: completed for current repository state by this stage.
"""


def documentation_inventory() -> str:
    return """
# Repository Documentation Inventory

## Repository State Before This Stage

- Current branch before documentation work: `main`
- Local HEAD before this stage: `16ec261e5b50f4560d731cfebab585dd8dfb0ea2`
- origin/main before this stage: `e4e583387febd51dddc6330076db6f2a2a7532bc`
- Status before this stage: local branch ahead of origin/main by 1 commit, working tree otherwise clean.

## Stages With Experiment Reports

- Stage 1: `experiment_report.md`
- Stage 2: `stage2_experiment_report.md`
- Stage 3: `stage3_experiment_report.md`
- Stage 4: `stage4_experiment_report.md`
- Ten-player: `ten_player_experiment_report.md`
- Limited last words: `limited_last_words_experiment_report.md`
- Risk preference: `risk_preference_experiment_report.md`
- Seer position: `seer_position_experiment_report.md`
- Structured seer search: `results/structured_seer_search/structured_seer_search_experiment_report.md`
- Seat-order symmetry: `results/seat_order_symmetry/seat_order_symmetry_experiment_report.md`
- Seat-order neutral: `results/seat_order_neutral/seat_order_neutral_experiment_report.md`
- Physical direction replay: `results/physical_direction_replay/physical_direction_replay_experiment_report.md`
- ML Stage 1: `results/ml_optimization_stage1/ml_stage1_experiment_report.md`
- ML Stage 1.5: `results/ml_optimization_stage15/ml_stage15_experiment_report.md`
- ML Stage 2A: `results/ml_optimization_stage2a/ml_stage2a_experiment_report.md`

## Stages With Formal Data Analysis

- Randomized-role seer-position game-level analysis: `results/data_analysis/seer_position_game_level/analysis_report.md`
- Structured seer search: `results/data_analysis/structured_seer_search/analysis_report.md`
- Seat-order neutral: `results/data_analysis/seat_order_neutral/analysis_report.md`
- Seer-position randomized-role analysis: `results/data_analysis/seer_position_randomized_roles/analysis_report.md`
- ML Stage 2A live policy contrasts: `results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv` and related reports.

## Stages Without Formal Data Analysis

- Early Stage 1 ablations.
- Stage 2 speech/herding/role-prior ablations.
- Stage 3 wolf deception diagnostics.
- Stage 4 speaker-memory sensitivity.
- Ten-player mechanism summaries.
- Risk preference summaries.
- Limited last words.

These stages are valuable but should be labeled descriptive unless formal CIs, p-values, adjusted p-values, and independent-sample definitions are later added.

## Stages Missing Stage Research Reports Before This Stage

- ML Stage 1 lacked `ml_stage1_research_report.md`.
- ML Stage 1.5 lacked `ml_stage15_research_report.md`.
- ML Stage 2A had an experiment report and a first-pass research report from a previous local documentation commit; this stage replaces it with the required cumulative-reporting version.

## Stages Missing Reproducibility Information

- Early non-ML stages often report seeds and game counts narratively but lack dedicated reproducibility scripts.
- Formal Data Analysis folders generally include source datasets, analysis scripts, schemas, or validation summaries.
- The original DURF proposal source file is missing from the repository.

## Stages With Conflicting Results Or Documentation Caveats

- Stage 1 report states 500 games per condition; current `results/ablation_results.csv` has 100 games per condition.
- Stage 1 identity ROC-AUC around 0.9458 is contradicted by Stage 1.5 grouped ROC-AUC around 0.6679.
- Stage 1.5 shadow wolf-kill improvement did not generalize to Stage 2A live complete games.
- Seat-order-neutral raw rows include deterministic label duplicates and must not be counted as independent.
- Structured search positive rankings are descriptive unless Holm correction supports them.

## Stages Whose Later Validation Revised Earlier Conclusions

- ML Stage 1 identity pilot was revised by ML Stage 1.5 grouped validation.
- ML Stage 1/1.5 surrogate action-value optimism was revised by full-rollout validity checks.
- ML Stage 1.5 shadow wolf-kill advantage was revised by ML Stage 2A live complete-game testing.
- Edge-seat folklore was revised by randomized-role and game-level position analysis.
- Directional search speculation was revised by seat-order-neutral and physical replay validation.
"""


def roadmap() -> str:
    stages = [
        ("R0", "Documentation and cumulative evidence completion", "Reconstruct evidence chain and proposal alignment.", "Which claims are supported, rejected, or unresolved?", "Generate documentation artifacts and validation script.", "No new simulation; validate documentation only.", "research_progress documentation set.", "Existing reports and result files present.", "Required files pass validation.", "All prior committed results.", "Risk of transcription error; mitigated by source traceability.", "Cumulative reports, registry, proposal audit, roadmap, validation summary."),
        ("R1", "ML Stage 2B - offline-to-live failure diagnosis", "Diagnose why frozen wolf-kill ML failed live.", "Was failure caused by distribution shift, repeated-decision compounding, or special-role targeting loss?", "Add diagnostic logging, not a new deployed policy.", "Matched analysis of existing Stage 2A decisions and targeted small diagnostics if needed.", "ML Stage 2B research report.", "Stage 2A negative result documented.", "Failure modes ranked with evidence.", "Stage 2A artifacts.", "High overfitting risk if tuned on live final seeds.", "Failure taxonomy, drift metrics, opportunity-cost diagnostics."),
        ("R2", "Formal Bag-of-Words speech quantification", "Implement proposal-level BoW metrics.", "Can werewolf-leaning, emotional-intensity, and information-density scores be defined without leakage?", "Tokenizer and score calculators.", "Validation on generated speech events.", "BoW quantification report.", "Documentation stage complete.", "Scores reproducible and observation-safe.", "Speech modules.", "Risk of post-hoc metric design.", "BoW lexicon, tokenizer, schema, validation."),
        ("R3", "BoW integration and comparative Data Analysis", "Test whether BoW metrics improve decisions.", "Do formal BoW scores improve village coordination or enable wolf manipulation?", "Integrate BoW scores into belief/voting toggles.", "Matched multi-seed ablation.", "BoW integration research report.", "R2 scores validated.", "Formal contrasts with CIs and adjusted p-values.", "R2 outputs.", "Risk of confounding speech generation and voting.", "Raw data, formal analysis, plots."),
        ("R4", "Unified role-specific payoff matrix", "Synthesize payoff by role and strategy.", "Which roles gain or lose under each mechanism?", "Role-level payoff extraction.", "Multi-seed payoff summary and formal contrasts.", "Role payoff report.", "Core results stable.", "Role payoff matrix complete.", "payoff.py and experiment outputs.", "Risk of mixing game sizes and incompatible conditions.", "Payoff matrix, expected payoff by role."),
        ("R5", "Financial-risk and Sharpe-like payoff analysis", "Translate payoff into financial risk metrics.", "Do strategies improve risk-adjusted returns?", "Variance, downside risk, opportunity cost, Sharpe-like metrics.", "Role/strategy risk-return analysis.", "Financial risk report.", "R4 payoff matrix complete.", "Risk metrics validated and documented.", "R4 outputs.", "Risk of overextending analogy.", "Risk cost, opportunity cost, Sharpe-like tables."),
        ("R6", "Unified role strategy optimization synthesis", "Compare strategic choices across roles.", "Which strategies optimize team and individual outcomes?", "No new mechanics unless needed; synthesize existing policies.", "Formal cross-role strategy comparison.", "Strategy synthesis report.", "R4 and R5 complete.", "Strategy recommendations labeled by evidence level.", "All strategy experiments.", "Risk of multiple comparisons and selective reporting.", "Unified strategy matrix."),
        ("R7", "Systematic literature comparison", "Connect findings to social deduction, deception, trust, and financial manipulation literature.", "Which findings align with prior theory?", "Literature search and citation map.", "No simulation required.", "Literature comparison report.", "Core results documented.", "Citations and claim mapping complete.", "Final outline and reports.", "Risk of unsupported analogy.", "Literature matrix and synthesis."),
        ("R8", "Final integrated Data Analysis", "Finalize statistical evidence for report.", "Which claims remain significant or practically meaningful after correction?", "Consolidated analysis scripts.", "Formal models, CIs, effect sizes, robustness summaries.", "Final Data Analysis report.", "R1-R7 complete or intentionally deferred.", "All final claims trace to source files.", "All results.", "Risk of treating pilots as final.", "Final tables, plots, evidence registry."),
        ("R9", "Final DURF report and presentation", "Produce final written report and presentation.", "What did the project establish scientifically?", "Write report and refresh presentation.", "No new analysis except final checks.", "Final DURF report and final presentation.", "R8 complete.", "Final deliverables ready to submit.", "All prior reports.", "Risk of overclaiming incomplete proposal pieces.", "Final report, slides, appendix."),
    ]
    lines = ["# Remaining Work Roadmap", ""]
    for sid, title, objective, question, implementation, experiment, report, entry, exit_cond, deps, risk, outputs in stages:
        lines += [
            f"## Stage {sid}: {title}",
            "",
            f"- Objective: {objective}",
            f"- Unanswered question: {question}",
            f"- Implementation: {implementation}",
            f"- Experiment: {experiment}",
            f"- Data Analysis: {experiment}",
            f"- Required report: {report}",
            f"- Entry condition: {entry}",
            f"- Exit condition: {exit_cond}",
            f"- Dependencies: {deps}",
            f"- Risk of overfitting or invalid inference: {risk}",
            f"- Expected outputs: {outputs}",
            "",
        ]
    return "\n".join(lines)


def permanent_standard() -> str:
    return """
# Permanent Stage Reporting Standard

Every future DURF Werewolf stage must produce the following before it can be marked complete:

1. Implementation or experiment outputs.
2. Formal Data Analysis, or an explicit statement that only implementation validation was possible.
3. Stage research report.
4. Cumulative evidence registry update.
5. Cumulative research report update.
6. Proposal-alignment audit update where relevant.
7. Next hypothesis.
8. Exact next experiment.
9. Reproducibility information.
10. Git commit and push status.

## Required Stage Report Sections

Each stage report must include background, prior-stage connection, hypothesis, pre-specified outcomes, experimental design, data scale, independent sample definition, implementation, validation, Data Analysis, descriptive findings, formal inference, robustness, leakage/overfitting/design audit, scientific interpretation, conclusion label, limitations, next hypothesis, source files, reproducibility information, and commit information.

## Required Evidence Discipline

- Distinguish descriptive results from formal statistical results.
- State the independent unit.
- Separate raw rows from games, decision states, matched sets, and deterministic duplicates.
- Report confidence intervals and effect sizes when formal inference is performed.
- Report raw and adjusted p-values when multiple comparisons are tested.
- Preserve superseded findings rather than deleting them.
- Never treat shadow policy values as live win rates.
- Never treat candidate rows as independent games.
- Never claim BoW completion unless tokenized text features and proposed speech scores exist.
- Never claim financial-risk completion unless risk cost, opportunity cost, payoff variance, and Sharpe-like metrics are formally computed.

## Required Conclusion Labels

Allowed labels are:

- statistically supported improvement
- statistically supported harmful effect
- promising but uncertain
- weak/inconclusive
- no meaningful improvement
- overfit
- unstable across regimes
- surrogate-only improvement
- invalid due to leakage
- invalid due to design limitation
- hypothesis supported
- hypothesis rejected
- hypothesis unresolved
- implementation validated
- engine symmetry validated

No future stage may be marked complete unless all applicable reporting outputs exist.
"""


def inconsistencies() -> str:
    return """
# Documentation Inconsistencies And Revision Log

## 1. Original Proposal File Not Found

The prompt references a Dean's Undergraduate Research Fund proposal, but no proposal file was found in the repository. The proposal-alignment audit uses the prompt-provided proposal summary. Verification status: `source_not_found`.

## 2. Stage 1 Game Count Inconsistency

`experiment_report.md` states that each Stage 1 ablation condition was evaluated with 500 games. The current `results/ablation_results.csv` contains 100 games per condition and appears to reflect a later exported ablation state. Reports should cite the Stage 1 table when discussing Stage 1 and cite the CSV only with this caveat.

## 3. Stage 1 Identity ROC-AUC Revised By Stage 1.5

ML Stage 1 reported village-vote logistic ROC-AUC around 0.9458. ML Stage 1.5 grouped validation reported final-test ROC-AUC around 0.6679, close to existing `p_wolf` at 0.6586. The Stage 1 pilot estimate must not be cited without the Stage 1.5 correction.

## 4. Surrogate Action Values Revised By Full Rollout

Surrogate models appeared useful in early ML outputs, but Stage 1.5 found weak surrogate-to-full validity for wolf-kill and day-vote action values. Surrogate value must not be treated as live game value.

## 5. Stage 1.5 Shadow Advantage Revised By Stage 2A Live Test

Stage 1.5 shadow analysis suggested approximately +0.150 wolf-team action-value improvement for ML wolf-kill recommendation. Stage 2A live complete-game results showed existing_rule wolf win 69.50%, frozen_ml 61.00%, hybrid 58.00%, and epsilon 61.00%. The hybrid policy was statistically harmful after Holm correction.

## 6. Seat-Order-Neutral Raw Rows Versus Independent Units

The seat-order-neutral source file has 30,000 rows, but normal, mirrored, and rotated label rows are deterministic duplicates for tested physical mechanisms. Effective independent strategy inference uses 10,000 strategy/base rows and 2,500 physical configurations.

## 7. Structured Seer Search Positive Strategy Ranking

`alternate_sides` and `right_to_left` are descriptively strong, but their positive contrasts versus random do not survive Holm correction. They should be called promising but uncertain, not statistically superior.

## 8. Bag-of-Words Completion Risk

The project has structured speech act labels, but the proposal's BoW requirements include werewolf-leaning, emotional intensity, and information density. These should remain partially completed or not started until formal tokenized scores exist.

## 9. Financial-Metric Completion Risk

The project has payoff outputs and conceptual financial analogies, but formal risk cost, opportunity cost, payoff variance, risk-adjusted return, and Sharpe-like metrics remain incomplete.
"""


def source_trace_rows() -> list[dict[str, object]]:
    rows = [
        ("C1", "Stage 1 random baseline wolf win 93 percent", "Stage 1", "experiment_report.md", "Results Table", "results/ablation_results.csv", "ablation_experiment.py", SOURCE_COMMIT, "verified_from_source", "Report says 500 games; current CSV has 100."),
        ("C2", "Stage 1 witch_action village win 49 percent", "Stage 1", "experiment_report.md", "Results Table", "results/ablation_results.csv", "ablation_experiment.py", SOURCE_COMMIT, "verified_from_source", "Sequential role-action ablation."),
        ("C3", "Stage 2 speech and role-prior mechanisms improve village descriptively", "Stage 2", "stage2_experiment_report.md", "Sections 6-10", "results/ablation_results.csv", "ablation_experiment.py", SOURCE_COMMIT, "verified_from_source", "Exploratory 100-game/current CSV mismatch noted."),
        ("C4", "False accusation fell from 78 percent to 50 percent after costs", "Stage 3", "stage3_experiment_report.md", "Results sections", "stage3_experiment_report.md", "wolf_deception_experiment.py", SOURCE_COMMIT, "verified_from_source", "No formal p-values."),
        ("C5", "Trust vote weight 0.40 reduced wolf win to 36.40 percent", "Stage 4", "stage4_experiment_report.md", "Sensitivity results", "stage4_experiment_report.md", "speaker_memory_sensitivity.py", SOURCE_COMMIT, "verified_from_source", "Single-seed 500-game sensitivity."),
        ("C6", "Ten-player speech village mean 65.16 percent", "Ten-player", "ten_player_experiment_report.md", "Multi-seed summary", "results/ten_player_multi_seed_summary.md", "ten_player_multi_seed_experiment.py", SOURCE_COMMIT, "verified_from_source", "Summary lacks formal p-values."),
        ("C7", "Risk conservative majority wolf mean 38.56 percent", "Risk preference", "risk_preference_experiment_report.md", "Multi-Seed Robustness", "results/ten_player_risk_preference_multi_seed_summary.md", "ten_player_risk_preference_multi_seed.py", SOURCE_COMMIT, "verified_from_source", "Descriptive multi-seed summary."),
        ("C8", "Edge seats were not wolf-heavy after randomization", "Seer position", "results/data_analysis/seer_position_game_level/analysis_report.md", "Edge Seats Are Not Intrinsically Wolf-Heavy", "results/ten_player_seer_position_randomized_roles_game_level_raw.csv", "results/data_analysis/seer_position_game_level/analysis_reproducibility.py", SOURCE_COMMIT, "verified_from_source", "Chi-square p 0.281, Cramer's V 0.009."),
        ("C9", "Edge-first vs random adjusted OR 1.05, p 0.417", "Seer position", "results/data_analysis/seer_position_game_level/analysis_report.md", "Adjusted Village-Win Model", "results/ten_player_seer_position_randomized_roles_game_level_raw.csv", "results/data_analysis/seer_position_game_level/analysis_reproducibility.py", SOURCE_COMMIT, "verified_from_source", "Formal analysis."),
        ("C10", "Alternate_sides vs random OR 1.161, Holm p 0.0552", "Structured seer search", "results/data_analysis/structured_seer_search/analysis_report.md", "Strategy Comparison Model", "results/structured_seer_search/structured_seer_search_game_level_raw.csv", "results/data_analysis/structured_seer_search/analyze_structured_seer_search.py", SOURCE_COMMIT, "verified_from_source", "Promising but uncertain."),
        ("C11", "Highest_p_wolf vs random Holm p 0.000276 harmful", "Structured seer search", "results/data_analysis/structured_seer_search/analysis_report.md", "Strategy Comparison Model", "results/structured_seer_search/structured_seer_search_game_level_raw.csv", "results/data_analysis/structured_seer_search/analyze_structured_seer_search.py", SOURCE_COMMIT, "verified_from_source", "Statistically harmful."),
        ("C12", "Seat-order-neutral label rows are deterministic duplicates", "Seat-order neutral", "results/data_analysis/seat_order_neutral/analysis_report.md", "Data Validation and Label Invariance", "results/seat_order_neutral/seat_order_neutral_game_level_raw.csv", "results/data_analysis/seat_order_neutral/analysis_reproducibility.py", SOURCE_COMMIT, "verified_from_source", "Effective independent sample is lower than raw rows."),
        ("C13", "Physical_clockwise vs random paired Holm p 0.0814", "Seat-order neutral", "results/data_analysis/seat_order_neutral/analysis_report.md", "Paired Configuration Analysis", "results/seat_order_neutral/seat_order_neutral_game_level_raw.csv", "results/data_analysis/seat_order_neutral/analysis_reproducibility.py", SOURCE_COMMIT, "verified_from_source", "Promising but uncertain."),
        ("C14", "Physical replay validation matched at 100 percent", "Physical replay", "results/physical_direction_replay/physical_direction_replay_experiment_report.md", "Validation summaries", "results/physical_direction_replay/supplied_action_replay_game_level_raw.csv", "physical_direction_replay_experiment.py", SOURCE_COMMIT, "verified_from_source", "Engine symmetry validated."),
        ("C15", "ML Stage 1 village-vote ROC-AUC 0.9458", "ML Stage 1", "results/ml_optimization_stage1/ml_stage1_experiment_report.md", "Identity Prediction Results", "results/ml_optimization_stage1/ml_identity_model_metrics.csv", "ml_model_training.py", SOURCE_COMMIT, "verified_from_source", "Superseded by Stage 1.5 for generalization."),
        ("C16", "ML Stage 1.5 village-vote ROC-AUC 0.6679", "ML Stage 1.5", "results/ml_optimization_stage15/ml_stage15_experiment_report.md", "Identity Generalization", "results/ml_optimization_stage15/ml_identity_generalization_metrics.csv", "ml_nested_validation.py", SOURCE_COMMIT, "verified_from_source", "Grouped final-test result."),
        ("C17", "ML Stage 1.5 wolf-kill surrogate Spearman 0.0718", "ML Stage 1.5", "results/ml_optimization_stage15/ml_stage15_experiment_report.md", "Surrogate vs Full Rollout", "results/ml_optimization_stage15/ml_surrogate_validity_metrics.csv", "ml_nested_validation.py", SOURCE_COMMIT, "verified_from_source", "Weak validity."),
        ("C18", "ML Stage 1.5 shadow wolf-kill improvement +0.150", "ML Stage 1.5", "results/ml_optimization_stage15/ml_stage15_experiment_report.md", "Shadow Policy Results", "results/ml_optimization_stage15/ml_shadow_policy_comparison.csv", "ml_nested_validation.py", SOURCE_COMMIT, "verified_from_source", "Superseded by live Stage 2A."),
        ("C19", "ML Stage 2A existing_rule wolf win 69.50 percent", "ML Stage 2A", "results/ml_optimization_stage2a/ml_stage2a_experiment_report.md", "Live policy summary", "results/ml_optimization_stage2a/wolf_kill_live_policy_summary.csv", "ml_stage2a_wolf_kill_experiment.py", SOURCE_COMMIT, "verified_from_source", "Live complete games."),
        ("C20", "ML Stage 2A hybrid harmful, Holm p 0.0033", "ML Stage 2A", "results/ml_optimization_stage2a/ml_stage2a_experiment_report.md", "Primary contrasts", "results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv", "ml_stage2a_wolf_kill_experiment.py", SOURCE_COMMIT, "verified_from_source", "Statistically supported harmful effect."),
        ("C21", "Original proposal file was not found", "Proposal alignment", "MISSING:DURF proposal file", "Repository search", "MISSING:DURF proposal file", "none", SOURCE_COMMIT, "source_not_found", "Used user-provided proposal summary."),
    ]
    return [
        {
            "claim_id": r[0],
            "claim_summary": r[1],
            "stage": r[2],
            "source_file": r[3],
            "source_table_or_section": r[4],
            "dataset": r[5],
            "analysis_script": r[6],
            "commit_hash": r[7],
            "verification_status": r[8],
            "notes": r[9],
        }
        for r in rows
    ]


def main() -> None:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    write_text(STAGE1_DIR / "ml_stage1_research_report.md", stage1_research_report())
    write_text(STAGE15_DIR / "ml_stage15_research_report.md", stage15_research_report())
    write_text(STAGE2A_DIR / "ml_stage2a_research_report.md", stage2a_research_report())
    write_text(RESEARCH_DIR / "research_documentation_completion_report.md", documentation_completion_report())
    write_csv(RESEARCH_DIR / "cumulative_evidence_registry.csv", registry_rows(), REGISTRY_COLUMNS)
    write_text(RESEARCH_DIR / "cumulative_research_report.md", cumulative_report())
    write_csv(RESEARCH_DIR / "durf_proposal_alignment_matrix.csv", proposal_matrix_rows(), PROPOSAL_COLUMNS)
    write_text(RESEARCH_DIR / "durf_proposal_alignment_audit.md", proposal_alignment_audit())
    write_text(RESEARCH_DIR / "current_progress_assessment.md", current_progress_assessment())
    write_text(RESEARCH_DIR / "repository_documentation_inventory.md", documentation_inventory())
    write_text(RESEARCH_DIR / "remaining_work_roadmap.md", roadmap())
    write_text(RESEARCH_DIR / "permanent_stage_reporting_standard.md", permanent_standard())
    write_csv(RESEARCH_DIR / "source_traceability_index.csv", source_trace_rows(), TRACE_COLUMNS)
    write_text(RESEARCH_DIR / "documentation_inconsistencies.md", inconsistencies())
    print("Research progress artifacts generated.")


if __name__ == "__main__":
    main()
