# R8 Dataset Schema

## r8_experiment_inventory

Path: `results/final_integrated_analysis_stage_r8/r8_experiment_inventory.csv`

Columns: stage_id, experiment_id, research_question, experiment_type, role_or_mechanism, policies_or_conditions, raw_game_rows, unique_games, matched_sets, seeds, regimes, player_rows, event_rows, utterance_rows, rollout_rows, candidate_rows, independent_unit, primary_outcome, secondary_outcomes, formal_inference, multiplicity_method, manifest_or_hash, source_report, source_data, evidence_status, included_in_final_analysis, exclusion_reason, notes

## r8_final_figure_registry

Path: `results/final_integrated_analysis_stage_r8/r8_final_figure_registry.csv`

Columns: figure_id, figure_name, svg_path, png_path, chart_family, primary_measure, source_data, final_report_use

## r8_final_hypothesis_registry

Path: `results/final_integrated_analysis_stage_r8/r8_final_hypothesis_registry.csv`

Columns: hypothesis_id, research_question_id, stage_id, role_or_mechanism, hypothesis, null_hypothesis, primary_outcome, independent_unit, sample_size, comparison, effect_direction, effect_size, confidence_interval, raw_p_value, adjusted_p_value, multiplicity_family, seed_robustness, regime_robustness, leakage_status, overfitting_status, evidence_grade, conclusion_status, final_safe_wording, literature_relationship, project_source, literature_source_ids

## r8_final_limitations_registry

Path: `results/final_integrated_analysis_stage_r8/r8_final_limitations_registry.csv`

Columns: limitation_id, domain, limitation, severity, mitigation_or_final_reporting_rule, source

## r8_final_literature_integration_table

Path: `results/final_integrated_analysis_stage_r8/r8_final_literature_integration_table.csv`

Columns: project_finding_id, project_chapter, project_finding, eligible_source_count, doi_verified_source_count, recent_source_count, foundational_source_count, source_ids, dois, literature_relationships, safe_final_wording, coverage_status, source_data

## r8_final_role_payoff_table

Path: `results/final_integrated_analysis_stage_r8/r8_final_role_payoff_table.csv`

Columns: role, calculation_specification, observations, mean_payoff, median_payoff, stdev, downside_deviation, negative_payoff_probability, var90_loss, var95_loss, cvar90_loss, cvar95_loss, sharpe_like_ratio, sortino_like_ratio, opportunity_cost_adjusted_mean_payoff, mean_payoff_bootstrap_ci, stdev_bootstrap_ci, downside_deviation_bootstrap_ci, sharpe_like_bootstrap_ci, sortino_like_bootstrap_ci, rank_mean_payoff, rank_lowest_volatility, rank_lowest_downside, rank_lowest_negative_probability, rank_sharpe_like, rank_sortino_like, source_data

## r8_final_role_strategy_table

Path: `results/final_integrated_analysis_stage_r8/r8_final_role_strategy_table.csv`

Columns: role, reference_policy, strongest_tested_policy, highest_mean_payoff_policy, highest_sharpe_like_policy, highest_sortino_like_policy, lowest_downside_risk_policy, village_win_rate, wolf_win_rate, mean_actor_payoff, actor_payoff_ci, primary_contrast, primary_mean_difference, primary_ci, raw_p_value, holm_adjusted_p_value, effective_matched_set_count, efficient_frontier_stdev, efficient_frontier_downside, efficient_frontier_cvar95, strictly_dominated_policies, evidence_grade, recommendation, gap_closed, source_data

## r8_final_statistical_evidence_table

Path: `results/final_integrated_analysis_stage_r8/r8_final_statistical_evidence_table.csv`

Columns: evidence_id, hypothesis_id, research_question_id, stage_id, mechanism_or_role, primary_outcome, comparison, independent_unit, sample_size, effect_direction, effect_size, confidence_interval, raw_p_value, adjusted_p_value, multiple_comparison_method, statistical_significance, practical_meaningfulness, robustness_summary, leakage_status, conclusion_status, final_safe_wording, source_data

## r8_final_table_registry

Path: `results/final_integrated_analysis_stage_r8/r8_final_table_registry.csv`

Columns: table_id, table_name, path, row_count, primary_use, source_module

## r8_financial_analogy_final_table

Path: `results/final_integrated_analysis_stage_r8/r8_financial_analogy_final_table.csv`

Columns: analogy_component, simulation_measure, financial_risk_analogue, supported_use, unsupported_or_limited_use, validation_status, source_data

## r8_ml_final_table

Path: `results/final_integrated_analysis_stage_r8/r8_ml_final_table.csv`

Columns: stage, policy_or_model, analysis_type, sample_unit, sample_size, primary_metric, metric_value, comparison, effect, confidence_interval, raw_p_value, holm_adjusted_p_value, conclusion, deployment_status, source_data

## r8_negative_results

Path: `results/final_integrated_analysis_stage_r8/r8_negative_results.csv`

Columns: finding_id, finding_type, research_question_id, stage_id, mechanism_or_role, finding, primary_effect, confidence_interval, adjusted_p_value, evidence_grade, final_safe_wording, source_data

## r8_project_scale_summary

Path: `results/final_integrated_analysis_stage_r8/r8_project_scale_summary.csv`

Columns: scale_metric, minimum_confirmed_unique, maximum_possible_rows, can_be_summed_across_stages, source_basis, overlap_caveat, final_reporting_rule

## r8_proposal_completion_matrix

Path: `results/final_integrated_analysis_stage_r8/r8_proposal_completion_matrix.csv`

Columns: proposal_component, original_proposal_description, r8_final_status, evidence, source_file, quality_of_completion, remaining_work, required_next_stage, blocking_final_report

## r8_r9_readiness_summary

Path: `results/final_integrated_analysis_stage_r8/r8_r9_readiness_summary.csv`

Columns: criterion, status, evidence, required_for_r9

## r8_research_question_registry

Path: `results/final_integrated_analysis_stage_r8/r8_research_question_registry.csv`

Columns: research_question_id, original_or_extended, proposal_text, operational_definition, main_hypotheses, completed_stages, final_status, primary_evidence, main_result, limitations, final_report_section

## r8_sample_unit_registry

Path: `results/final_integrated_analysis_stage_r8/r8_sample_unit_registry.csv`

Columns: unit_type, definition, stages_using_unit, total_rows, independent_or_clustered, clustering_variable, valid_for_inference, valid_for_descriptive_analysis, can_be_summed_across_stages, overlap_risk, final_reporting_rule, notes

## r8_speech_bow_final_table

Path: `results/final_integrated_analysis_stage_r8/r8_speech_bow_final_table.csv`

Columns: stage, artifact_or_policy, analysis_type, sample_unit, sample_size, primary_metric, metric_value, comparison, effect, confidence_interval, raw_p_value, holm_adjusted_p_value, conclusion, final_use, source_data

## r8_strategy_risk_return_table

Path: `results/final_integrated_analysis_stage_r8/r8_strategy_risk_return_table.csv`

Columns: role, policy, game_count, matched_set_count, seed_count, behavioral_regime_count, village_win_rate, wolf_win_rate, mean_actor_payoff, actor_payoff_ci, stdev_payoff, downside_deviation, negative_payoff_probability, var_like_90, var_like_95, cvar_like_90, cvar_like_95, sharpe_like_ratio, sortino_like_ratio, frontier_stdev, frontier_downside, frontier_cvar95, source_data

## r8_superseded_result_registry

Path: `results/final_integrated_analysis_stage_r8/r8_superseded_result_registry.csv`

Columns: superseded_result_id, superseded_stage, superseded_claim, superseding_stage, superseding_evidence, reason, final_reporting_rule

## r8_supported_findings

Path: `results/final_integrated_analysis_stage_r8/r8_supported_findings.csv`

Columns: finding_id, finding_type, research_question_id, stage_id, mechanism_or_role, finding, primary_effect, confidence_interval, adjusted_p_value, evidence_grade, final_safe_wording, source_data

## r8_uncertain_findings

Path: `results/final_integrated_analysis_stage_r8/r8_uncertain_findings.csv`

Columns: finding_id, finding_type, research_question_id, stage_id, mechanism_or_role, finding, primary_effect, confidence_interval, adjusted_p_value, evidence_grade, final_safe_wording, source_data

## r8_validation_summary

Path: `results/final_integrated_analysis_stage_r8/r8_validation_summary.csv`

Columns: check_name, status, evidence, source

## r8_validity_and_robustness_table

Path: `results/final_integrated_analysis_stage_r8/r8_validity_and_robustness_table.csv`

Columns: validity_domain, audit_or_test, status, evidence, source_file, final_reporting_implication
