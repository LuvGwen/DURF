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
