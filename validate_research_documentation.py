"""Validate DURF cumulative research documentation artifacts."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "results" / "research_progress"
SUMMARY_PATH = RESEARCH_DIR / "documentation_validation_summary.csv"

ALLOWED_CONCLUSION_LABELS = {
    "statistically supported improvement",
    "statistically supported harmful effect",
    "promising but uncertain",
    "weak/inconclusive",
    "template-bound",
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
    "unified payoff system validated",
    "partially validated",
    "design inconsistency found",
    "historical recalculation limited",
    "invalid due to double counting",
    "invalid due to missing event data",
    "ready for risk-adjusted analysis",
    "requires one correction before R5",
    "highest expected payoff",
    "highest payoff volatility",
    "lowest payoff volatility",
    "lowest downside risk",
    "negative-payoff probability",
    "lowest CVaR-like loss",
    "highest Sharpe-like payoff ratio",
    "highest Sortino-like payoff ratio",
    "opportunity-cost-adjusted payoff",
    "information premium analogue",
    "manipulation premium analogue",
    "risk-return efficient",
    "strictly dominated",
    "robust across seeds",
    "robust across regimes",
    "sensitive to payoff specification",
    "fragile under coefficient sensitivity",
    "descriptive only",
    "insufficient data",
    "financial analogy supported",
    "ready for synthesis",
    "statistically_supported_improvement",
    "statistically_supported_harm",
    "promising_but_uncertain",
    "diagnostic_only",
    "no_supported_improvement",
    "engine_symmetry_validated",
    "post-selection risk found",
    "selection risk found and corrected",
    "replication required",
}

REQUIRED_FILES = [
    "results/research_progress/cumulative_evidence_registry.csv",
    "results/research_progress/cumulative_research_report.md",
    "results/research_progress/durf_proposal_alignment_audit.md",
    "results/research_progress/durf_proposal_alignment_matrix.csv",
    "results/research_progress/current_progress_assessment.md",
    "results/research_progress/repository_documentation_inventory.md",
    "results/research_progress/remaining_work_roadmap.md",
    "results/research_progress/permanent_stage_reporting_standard.md",
    "results/research_progress/source_traceability_index.csv",
    "results/research_progress/documentation_inconsistencies.md",
    "results/ml_optimization_stage1/ml_stage1_research_report.md",
    "results/ml_optimization_stage15/ml_stage15_research_report.md",
    "results/ml_optimization_stage2a/ml_stage2a_research_report.md",
    "results/ml_optimization_stage2b/ml_stage2b_research_report.md",
    "results/bow_speech_stage_r2/bow_stage_r2_research_report.md",
    "results/bow_speech_stage_r2/bow_stage_r2_information_leakage_audit.md",
    "results/bow_speech_stage_r2/bow_information_leakage_audit.md",
    "results/bow_speech_stage_r2/bow_vocabulary_manifest.json",
    "results/bow_speech_stage_r2/bow_score_definition_manifest.json",
    "results/research_progress/research_documentation_completion_report.md",
    "results/payoff_matrix_stage_r4/r4_payoff_manifest.json",
    "results/payoff_matrix_stage_r4/r4_research_report.md",
    "results/payoff_matrix_stage_r4/r4_information_leakage_audit.md",
    "results/payoff_matrix_stage_r4/r4_validation_summary.csv",
    "results/payoff_matrix_stage_r4/r4_double_counting_audit.md",
    "results/financial_risk_stage_r5/r5_metric_definition_manifest.json",
    "results/financial_risk_stage_r5/r5_research_report.md",
    "results/financial_risk_stage_r5/r5_metric_validation_summary.csv",
    "results/financial_risk_stage_r5/r5_strategy_frontier_summary.csv",
    "results/financial_risk_stage_r5/r5_information_leakage_audit.md",
    "results/financial_risk_stage_r51/r51_strategy_attribution_registry.csv",
    "results/financial_risk_stage_r51/r51_r5_strategy_mapping_audit.csv",
    "results/financial_risk_stage_r51/r51_actor_specific_strategy_payoff_raw.csv",
    "results/financial_risk_stage_r51/r51_cross_role_externality_raw.csv",
    "results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv",
    "results/financial_risk_stage_r51/r51_actor_specific_frontier_summary.csv",
    "results/financial_risk_stage_r51/r51_information_premium_summary.csv",
    "results/financial_risk_stage_r51/r51_manipulation_premium_summary.csv",
    "results/financial_risk_stage_r51/r51_mapping_validation_summary.csv",
    "results/financial_risk_stage_r51/r51_research_report.md",
    "results/role_strategy_synthesis_stage_r6/r6_role_strategy_decision_matrix.csv",
    "results/role_strategy_synthesis_stage_r6/r6_data_analysis_summary.csv",
    "results/role_strategy_synthesis_stage_r6/r6_cross_stage_contradiction_audit.csv",
    "results/role_strategy_synthesis_stage_r6/r6_cross_role_externality_matrix.csv",
    "results/role_strategy_synthesis_stage_r6/r6_remaining_evidence_gaps.csv",
    "results/role_strategy_synthesis_stage_r6/r6_targeted_experiment_priorities.csv",
    "results/role_strategy_synthesis_stage_r6/r6_rejected_strategy_registry.csv",
    "results/role_strategy_synthesis_stage_r6/r6_current_default_registry.csv",
    "results/role_strategy_synthesis_stage_r6/r6_evidence_grade_registry.csv",
    "results/role_strategy_synthesis_stage_r6/r6_source_evidence_index.csv",
    "results/role_strategy_synthesis_stage_r6/r6_proposal_alignment_summary.csv",
    "results/role_strategy_synthesis_stage_r6/r6_validation_summary.csv",
    "results/role_strategy_synthesis_stage_r6/r6_research_report.md",
    "results/role_strategy_synthesis_stage_r6/r6_overclaiming_audit.md",
    "results/targeted_strategy_stage_r61/r61_master_seed_registry.csv",
    "results/targeted_strategy_stage_r61/r61_behavioral_regime_registry.csv",
    "results/targeted_strategy_stage_r61/r61_policy_registry.csv",
    "results/targeted_strategy_stage_r61/r61_module_registry.csv",
    "results/targeted_strategy_stage_r61/r61_validation_summary.csv",
    "results/targeted_strategy_stage_r61/r61_global_primary_contrasts.csv",
    "results/targeted_strategy_stage_r61/r61_global_robustness_summary.csv",
    "results/targeted_strategy_stage_r61/r61_r7_readiness_summary.csv",
    "results/targeted_strategy_stage_r61/r61_hunter_research_report.md",
    "results/targeted_strategy_stage_r61/r61_seer_research_report.md",
    "results/targeted_strategy_stage_r61/r61_witch_research_report.md",
    "results/targeted_strategy_stage_r61/r61_wolf_research_report.md",
    "results/targeted_strategy_stage_r61/r61_villager_research_report.md",
    "results/targeted_strategy_stage_r61/r61_research_report.md",
    "results/targeted_strategy_stage_r61/r61_final_strategy_gap_closure_report.md",
    "results/metrics_integrity_stage_r62/r62_seer_survival_field_inventory.csv",
    "results/metrics_integrity_stage_r62/r62_seer_life_history_raw.csv",
    "results/metrics_integrity_stage_r62/r62_seer_survival_summary.csv",
    "results/metrics_integrity_stage_r62/r62_seer_post_reveal_hazard_summary.csv",
    "results/metrics_integrity_stage_r62/r62_seer_survival_root_cause_report.md",
    "results/metrics_integrity_stage_r62/r62_seer_survival_audit_report.md",
    "results/metrics_integrity_stage_r62/r62_witch_potion_field_inventory.csv",
    "results/metrics_integrity_stage_r62/r62_witch_potion_lifecycle_raw.csv",
    "results/metrics_integrity_stage_r62/r62_witch_payoff_reconciliation.csv",
    "results/metrics_integrity_stage_r62/r62_witch_potion_waste_summary.csv",
    "results/metrics_integrity_stage_r62/r62_witch_potion_root_cause_report.md",
    "results/metrics_integrity_stage_r62/r62_witch_potion_waste_audit_report.md",
    "results/metrics_integrity_stage_r62/recommended_research_configuration.json",
    "results/metrics_integrity_stage_r62/recommended_research_configuration.md",
    "results/metrics_integrity_stage_r62/historical_default_configuration.json",
    "results/metrics_integrity_stage_r62/experimental_candidate_configuration.json",
    "results/metrics_integrity_stage_r62/rejected_policy_registry.csv",
    "results/metrics_integrity_stage_r62/r62_configuration_validation_summary.csv",
    "results/metrics_integrity_stage_r62/r62_research_report.md",
    "results/metrics_integrity_stage_r62/r62_validation_summary.csv",
    "results/metrics_integrity_stage_r62/r62_information_leakage_audit.md",
    "results/metrics_integrity_stage_r62/r62_double_counting_audit.md",
    "results/metrics_integrity_stage_r62/r62_next_stage_readiness.md",
    "results/literature_synthesis_stage_r7/r7_literature_search_log.csv",
    "results/literature_synthesis_stage_r7/r7_source_screening_registry.csv",
    "results/literature_synthesis_stage_r7/r7_source_quality_registry.csv",
    "results/literature_synthesis_stage_r7/r7_finding_literature_comparison_matrix.csv",
    "results/literature_synthesis_stage_r7/r7_financial_analogy_crosswalk.csv",
    "results/literature_synthesis_stage_r7/r7_literature_contradiction_registry.csv",
    "results/literature_synthesis_stage_r7/r7_claim_support_audit.csv",
    "results/literature_synthesis_stage_r7/r7_reference_metadata_validation.csv",
    "results/literature_synthesis_stage_r7/r7_domain_coverage_summary.csv",
    "results/literature_synthesis_stage_r7/r7_r8_readiness_summary.csv",
    "results/literature_synthesis_stage_r7/r7_bibliography.bib",
    "results/literature_synthesis_stage_r7/r7_references_apa7.md",
    "results/literature_synthesis_stage_r7/r7_references_author_year.csv",
    "results/literature_synthesis_stage_r7/r7_pre_registration.md",
    "results/literature_synthesis_stage_r7/r7_search_methodology.md",
    "results/literature_synthesis_stage_r7/r7_screening_report.md",
    "results/literature_synthesis_stage_r7/r7_social_deduction_literature.md",
    "results/literature_synthesis_stage_r7/r7_asymmetric_information_literature.md",
    "results/literature_synthesis_stage_r7/r7_herding_and_trust_literature.md",
    "results/literature_synthesis_stage_r7/r7_deception_and_misinformation_literature.md",
    "results/literature_synthesis_stage_r7/r7_behavioral_finance_literature.md",
    "results/literature_synthesis_stage_r7/r7_bow_and_domain_shift_literature.md",
    "results/literature_synthesis_stage_r7/r7_offline_policy_failure_literature.md",
    "results/literature_synthesis_stage_r7/r7_multi_agent_validation_literature.md",
    "results/literature_synthesis_stage_r7/r7_risk_metrics_literature.md",
    "results/literature_synthesis_stage_r7/r7_financial_analogy_report.md",
    "results/literature_synthesis_stage_r7/r7_project_finding_comparison_report.md",
    "results/literature_synthesis_stage_r7/r7_theoretical_synthesis.md",
    "results/literature_synthesis_stage_r7/r7_research_report.md",
    "results/literature_synthesis_stage_r7/r7_limitations.md",
    "results/literature_synthesis_stage_r7/r7_manual_review_items.md",
    "results/literature_synthesis_stage_r7/literature_domain_coverage.svg",
    "results/literature_synthesis_stage_r7/project_finding_literature_relationships.svg",
    "results/literature_synthesis_stage_r7/source_quality_distribution.svg",
    "results/literature_synthesis_stage_r7/theoretical_framework_map.svg",
    "results/literature_synthesis_stage_r7/financial_analogy_crosswalk.svg",
    "results/literature_synthesis_stage_r7/literature_agreement_disagreement_map.svg",
    "results/literature_doi_recency_audit_stage_r71/r71_doi_validation_registry.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_recency_audit.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_foundational_exception_registry.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_replacement_source_registry.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_revised_finding_literature_matrix.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_final_bibliography.bib",
    "results/literature_doi_recency_audit_stage_r71/r71_final_references_apa7.md",
    "results/literature_doi_recency_audit_stage_r71/r71_final_references_author_year.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_excluded_no_doi_sources.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_revised_claim_support_audit.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_domain_recency_coverage.csv",
    "results/literature_doi_recency_audit_stage_r71/r71_manual_review_items.md",
    "results/literature_doi_recency_audit_stage_r71/r71_pre_registration.md",
    "results/literature_doi_recency_audit_stage_r71/r71_doi_verification_method.md",
    "results/literature_doi_recency_audit_stage_r71/r71_recency_review_method.md",
    "results/literature_doi_recency_audit_stage_r71/r71_source_replacement_report.md",
    "results/literature_doi_recency_audit_stage_r71/r71_foundational_exception_report.md",
    "results/literature_doi_recency_audit_stage_r71/r71_finding_coverage_report.md",
    "results/literature_doi_recency_audit_stage_r71/r71_final_bibliography_validation.md",
    "results/literature_doi_recency_audit_stage_r71/r71_research_report.md",
    "results/literature_doi_recency_audit_stage_r71/r71_limitations.md",
    "results/literature_doi_recency_audit_stage_r71/r71_r8_readiness.md",
]

REQUIRED_FILES.extend(
    [
        "results/final_integrated_analysis_stage_r8/r8_experiment_inventory.csv",
        "results/final_integrated_analysis_stage_r8/r8_sample_unit_registry.csv",
        "results/final_integrated_analysis_stage_r8/r8_project_scale_summary.csv",
        "results/final_integrated_analysis_stage_r8/r8_research_question_registry.csv",
        "results/final_integrated_analysis_stage_r8/r8_final_hypothesis_registry.csv",
        "results/final_integrated_analysis_stage_r8/r8_final_statistical_evidence_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_supported_findings.csv",
        "results/final_integrated_analysis_stage_r8/r8_negative_results.csv",
        "results/final_integrated_analysis_stage_r8/r8_uncertain_findings.csv",
        "results/final_integrated_analysis_stage_r8/r8_superseded_result_registry.csv",
        "results/final_integrated_analysis_stage_r8/r8_final_role_strategy_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_final_role_payoff_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_strategy_risk_return_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_speech_bow_final_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_ml_final_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_validity_and_robustness_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_final_literature_integration_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_financial_analogy_final_table.csv",
        "results/final_integrated_analysis_stage_r8/r8_final_limitations_registry.csv",
        "results/final_integrated_analysis_stage_r8/r8_proposal_completion_matrix.csv",
        "results/final_integrated_analysis_stage_r8/r8_final_table_registry.csv",
        "results/final_integrated_analysis_stage_r8/r8_final_figure_registry.csv",
        "results/final_integrated_analysis_stage_r8/r8_validation_summary.csv",
        "results/final_integrated_analysis_stage_r8/r8_r9_readiness_summary.csv",
        "results/final_integrated_analysis_stage_r8/r8_pre_registration.md",
        "results/final_integrated_analysis_stage_r8/r8_schema.md",
        "results/final_integrated_analysis_stage_r8/r8_data_integration_method.md",
        "results/final_integrated_analysis_stage_r8/r8_sample_unit_audit.md",
        "results/final_integrated_analysis_stage_r8/r8_statistical_synthesis_report.md",
        "results/final_integrated_analysis_stage_r8/r8_role_strategy_report.md",
        "results/final_integrated_analysis_stage_r8/r8_payoff_risk_report.md",
        "results/final_integrated_analysis_stage_r8/r8_speech_bow_ml_report.md",
        "results/final_integrated_analysis_stage_r8/r8_validity_report.md",
        "results/final_integrated_analysis_stage_r8/r8_literature_integration_report.md",
        "results/final_integrated_analysis_stage_r8/r8_financial_analogy_report.md",
        "results/final_integrated_analysis_stage_r8/r8_proposal_completion_report.md",
        "results/final_integrated_analysis_stage_r8/r8_limitations.md",
        "results/final_integrated_analysis_stage_r8/r8_overclaiming_audit.md",
        "results/final_integrated_analysis_stage_r8/r8_research_report.md",
        "results/final_integrated_analysis_stage_r8/r8_r9_readiness.md",
    ]
)

REQUIRED_FILES.extend(
    [
        "results/project_overfitting_audit_stage_r81/r81_experimental_decision_history.csv",
        "results/project_overfitting_audit_stage_r81/r81_strategy_search_registry.csv",
        "results/project_overfitting_audit_stage_r81/r81_threshold_search_registry.csv",
        "results/project_overfitting_audit_stage_r81/r81_outcome_switching_registry.csv",
        "results/project_overfitting_audit_stage_r81/r81_split_integrity_registry.csv",
        "results/project_overfitting_audit_stage_r81/r81_final_seed_reuse_audit.csv",
        "results/project_overfitting_audit_stage_r81/r81_project_wide_multiple_testing_inventory.csv",
        "results/project_overfitting_audit_stage_r81/r81_policy_rank_bootstrap.csv",
        "results/project_overfitting_audit_stage_r81/r81_policy_selection_frequency.csv",
        "results/project_overfitting_audit_stage_r81/r81_winners_curse_estimates.csv",
        "results/project_overfitting_audit_stage_r81/r81_selection_stability_summary.csv",
        "results/project_overfitting_audit_stage_r81/r81_corrected_role_strategy_table.csv",
        "results/project_overfitting_audit_stage_r81/r81_policy_evidence_grade_registry.csv",
        "results/project_overfitting_audit_stage_r81/r81_payoff_sensitivity_scenarios.csv",
        "results/project_overfitting_audit_stage_r81/r81_payoff_sensitivity_results.csv",
        "results/project_overfitting_audit_stage_r81/r81_policy_rank_under_payoff_variants.csv",
        "results/project_overfitting_audit_stage_r81/r81_regime_coverage_audit.csv",
        "results/project_overfitting_audit_stage_r81/r81_distribution_shift_risk_registry.csv",
        "results/project_overfitting_audit_stage_r81/r81_bow_overfitting_audit.csv",
        "results/project_overfitting_audit_stage_r81/r81_ml_overfitting_audit.csv",
        "results/project_overfitting_audit_stage_r81/r81_literature_confirmation_bias_audit.csv",
        "results/project_overfitting_audit_stage_r81/r81_replication_priority_registry.csv",
        "results/project_overfitting_audit_stage_r81/r81_conclusion_change_registry.csv",
        "results/project_overfitting_audit_stage_r81/r81_validation_summary.csv",
        "results/project_overfitting_audit_stage_r81/r81_r9_readiness_summary.csv",
        "results/project_overfitting_audit_stage_r81/r81_pre_registration.md",
        "results/project_overfitting_audit_stage_r81/r81_audit_methodology.md",
        "results/project_overfitting_audit_stage_r81/r81_project_decision_history_report.md",
        "results/project_overfitting_audit_stage_r81/r81_strategy_search_report.md",
        "results/project_overfitting_audit_stage_r81/r81_outcome_switching_report.md",
        "results/project_overfitting_audit_stage_r81/r81_split_and_seed_integrity_report.md",
        "results/project_overfitting_audit_stage_r81/r81_multiple_testing_report.md",
        "results/project_overfitting_audit_stage_r81/r81_post_selection_bias_report.md",
        "results/project_overfitting_audit_stage_r81/r81_payoff_sensitivity_report.md",
        "results/project_overfitting_audit_stage_r81/r81_distribution_sensitivity_report.md",
        "results/project_overfitting_audit_stage_r81/r81_bow_overfitting_report.md",
        "results/project_overfitting_audit_stage_r81/r81_ml_overfitting_report.md",
        "results/project_overfitting_audit_stage_r81/r81_literature_confirmation_bias_report.md",
        "results/project_overfitting_audit_stage_r81/r81_villager_strategy_development_audit.md",
        "results/project_overfitting_audit_stage_r81/r81_seer_strategy_development_audit.md",
        "results/project_overfitting_audit_stage_r81/r81_witch_strategy_development_audit.md",
        "results/project_overfitting_audit_stage_r81/r81_hunter_strategy_development_audit.md",
        "results/project_overfitting_audit_stage_r81/r81_werewolf_strategy_development_audit.md",
        "results/project_overfitting_audit_stage_r81/r81_corrected_conclusions.md",
        "results/project_overfitting_audit_stage_r81/r81_replication_decision.md",
        "results/project_overfitting_audit_stage_r81/r81_limitations.md",
        "results/project_overfitting_audit_stage_r81/r81_overclaiming_audit.md",
        "results/project_overfitting_audit_stage_r81/r81_research_report.md",
        "results/project_overfitting_audit_stage_r81/r81_r9_readiness.md",
        "results/project_overfitting_audit_stage_r81/r81_manifest_hash_forensic_audit.csv",
        "results/project_overfitting_audit_stage_r81/r81_manifest_hash_forensic_report.md",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_role_strategy_table.csv",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_supported_findings.csv",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_negative_results.csv",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_uncertain_findings.csv",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_superseded_result_registry.csv",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_final_hypothesis_registry.csv",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_final_statistical_evidence_table.csv",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_proposal_completion_matrix.csv",
        "results/project_overfitting_audit_stage_r81/corrected_r8/corrected_r9_input_pack_manifest.csv",
    ]
)

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

PROPOSAL_STATUSES = {
    "completed",
    "completed_by_alternative_implementation",
    "completed_and_extended",
    "completed_with_limitations",
    "partially_completed",
    "not_started",
    "requires_formal_analysis",
    "requires_documentation",
    "requires_targeted_experiment",
    "insufficient_data",
    "no_longer_scientifically_justified",
    "completed_with_negative_findings",
    "ready_for_R9",
}

TRACE_STATUSES = {
    "verified_from_source",
    "verified_from_multiple_sources",
    "reported_in_handoff_only",
    "source_not_found",
    "inconsistent_sources",
    "requires_manual_review",
    "generated_by_r8",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def path_exists_or_marked(value: str, status: str) -> bool:
    if not value or value == "none":
        return True
    for piece in value.split(";"):
        item = piece.strip()
        if not item:
            continue
        if item.startswith("MISSING:"):
            if status not in {"source_not_found", "reported_in_handoff_only", "requires_manual_review"}:
                return False
            continue
        if item.startswith("speaker_memory_sensitivity.py output"):
            continue
        if not (ROOT / item).exists():
            return False
    return True


def add_result(rows: list[dict[str, str]], check: str, passed: bool, detail: str) -> None:
    rows.append({"check": check, "passed": str(bool(passed)), "detail": detail})


def main() -> int:
    summary: list[dict[str, str]] = []

    for file_name in REQUIRED_FILES:
        path = ROOT / file_name
        add_result(summary, f"required_file_exists:{file_name}", path.exists(), str(path))

    registry_path = RESEARCH_DIR / "cumulative_evidence_registry.csv"
    registry_rows = read_csv(registry_path)
    add_result(summary, "registry_row_count", len(registry_rows) >= 15, str(len(registry_rows)))
    add_result(
        summary,
        "registry_required_columns",
        set(REGISTRY_COLUMNS).issubset(registry_rows[0].keys() if registry_rows else set()),
        ",".join(REGISTRY_COLUMNS),
    )

    evidence_ids = [(row["stage_id"], row["hypothesis_id"]) for row in registry_rows]
    add_result(summary, "registry_no_duplicate_evidence_ids", len(evidence_ids) == len(set(evidence_ids)), str(len(evidence_ids)))

    bad_labels = sorted({row["conclusion_label"] for row in registry_rows} - ALLOWED_CONCLUSION_LABELS)
    add_result(summary, "conclusion_labels_allowed", not bad_labels, ";".join(bad_labels) if bad_labels else "all labels allowed")

    for row in registry_rows:
        status = "verified_from_source"
        dataset_ok = path_exists_or_marked(row["dataset_path"], status)
        report_ok = path_exists_or_marked(row["report_path"], status)
        add_result(summary, f"registry_paths:{row['stage_id']}:{row['hypothesis_id']}", dataset_ok and report_ok, f"dataset={row['dataset_path']} report={row['report_path']}")

    proposal_rows = read_csv(RESEARCH_DIR / "durf_proposal_alignment_matrix.csv")
    add_result(summary, "proposal_component_count", len(proposal_rows) >= 39, str(len(proposal_rows)))
    bad_statuses = sorted({row["status"] for row in proposal_rows} - PROPOSAL_STATUSES)
    add_result(summary, "proposal_statuses_allowed", not bad_statuses, ";".join(bad_statuses) if bad_statuses else "all statuses allowed")

    bow_rows = [
        row for row in proposal_rows
        if (
            "Bag-of-Words" in row["proposal_component"]
            or "Speech text tokenization" in row["proposal_component"]
            or "Emotional" in row["proposal_component"]
            or "Information-density" in row["proposal_component"]
            or row["proposal_component"] == "Werewolf-leaning speech score"
        )
    ]
    bow_artifacts_exist = all(
        (ROOT / path).exists()
        for path in [
            "results/bow_speech_stage_r2/bow_speech_utterance_dataset.csv",
            "results/bow_speech_stage_r2/bow_vocabulary.csv",
            "results/bow_speech_stage_r2/bow_score_intent_contrasts.csv",
            "results/bow_speech_stage_r2/bow_stage_r2_research_report.md",
        ]
    )
    bow_decision_rows = [
        row for row in proposal_rows
        if row["proposal_component"] == "BoW integration into decisions"
    ]
    bow_decision_not_complete = all(
        row["status"] in {"partially_completed", "completed_with_negative_findings"}
        for row in bow_decision_rows
    )
    add_result(
        summary,
        "proposal_bow_r2_completed_and_decision_integration_qualified",
        bow_artifacts_exist and bow_decision_not_complete,
        ",".join(
            row["proposal_component"] + "=" + row["status"]
            for row in bow_rows
        ),
    )

    financial_rows = [row for row in proposal_rows if row["proposal_component"] in {"Risk-adjusted return", "Sharpe-ratio analogue", "Payoff variance", "Risk cost"}]
    financial_supported_by_r5 = all(
        row["status"] in {"completed", "completed_and_extended", "completed_with_limitations", "partially_completed", "not_started"}
        for row in financial_rows
    ) and (ROOT / "results/financial_risk_stage_r5/r5_metric_validation_summary.csv").exists()
    add_result(summary, "proposal_financial_metrics_completed_or_historically_flagged", financial_supported_by_r5, ",".join(row["proposal_component"] + "=" + row["status"] for row in financial_rows))

    trace_rows = read_csv(RESEARCH_DIR / "source_traceability_index.csv")
    bad_trace_statuses = sorted({row["verification_status"] for row in trace_rows} - TRACE_STATUSES)
    add_result(summary, "trace_statuses_allowed", not bad_trace_statuses, ";".join(bad_trace_statuses) if bad_trace_statuses else "all statuses allowed")
    trace_paths_ok = all(
        path_exists_or_marked(row["source_file"], row["verification_status"]) and path_exists_or_marked(row["dataset"], row["verification_status"])
        for row in trace_rows
    )
    add_result(summary, "trace_source_paths_exist_or_marked", trace_paths_ok, str(len(trace_rows)))

    cumulative_text = (RESEARCH_DIR / "cumulative_research_report.md").read_text(encoding="utf-8")
    required_chapters = [
        "## 1. Original Proposal and Research Questions",
        "## 10. Position Theory",
        "## 16. Machine Learning Stage 2A",
        "## 19. Proposal Alignment",
        "## 21. Next Research Priorities",
    ]
    add_result(summary, "cumulative_report_major_chapters_present", all(ch in cumulative_text for ch in required_chapters), "checked key chapters")
    add_result(
        summary,
        "cumulative_report_r2_present",
        "## 24. R2 Formal Bag-of-Words Speech Quantification" in cumulative_text,
        "R2 chapter",
    )
    add_result(
        summary,
        "cumulative_report_r51_present",
        "## 29. R5.1 Role-Strategy Attribution Audit" in cumulative_text,
        "R5.1 chapter",
    )
    add_result(
        summary,
        "cumulative_report_r6_present",
        "## 30. R6 Unified Role Strategy Evidence Synthesis" in cumulative_text,
        "R6 chapter",
    )
    add_result(
        summary,
        "cumulative_report_r7_present",
        "## 32. R7 Systematic Literature Comparison" in cumulative_text,
        "R7 chapter",
    )
    add_result(
        summary,
        "cumulative_report_r71_present",
        "## 33. R7.1 DOI-Verified and Recency-Prioritized Literature Audit" in cumulative_text,
        "R7.1 chapter",
    )
    add_result(
        summary,
        "cumulative_report_r8_present",
        "## 34. R8 Final Integrated Data Analysis" in cumulative_text,
        "R8 chapter",
    )

    stage2a_text = (ROOT / "results/ml_optimization_stage2a/ml_stage2a_research_report.md").read_text(encoding="utf-8")
    add_result(summary, "stage2a_adjusted_p_values_reported", "0.0792" in stage2a_text and "0.0033" in stage2a_text, "Stage 2A Holm p-values")
    add_result(summary, "stage2a_next_hypothesis_present", "policy-induced distribution shift" in stage2a_text and "repeated-decision compounding" in stage2a_text, "Stage 2B hypothesis")

    r2_text = (ROOT / "results/bow_speech_stage_r2/bow_stage_r2_research_report.md").read_text(encoding="utf-8")
    add_result(
        summary,
        "r2_bow_report_has_required_answers",
        "Required Final Questions" in r2_text
        and "32721 utterances" in r2_text
        and "R3" in r2_text,
        "R2 final questions",
    )
    leakage_text = (
        ROOT
        / "results/bow_speech_stage_r2/bow_stage_r2_information_leakage_audit.md"
    ).read_text(encoding="utf-8")
    add_result(
        summary,
        "r2_bow_leakage_audit_passed",
        "Status: PASS" in leakage_text,
        "R2 leakage audit",
    )

    completion_text = (RESEARCH_DIR / "research_documentation_completion_report.md").read_text(encoding="utf-8")
    add_result(summary, "current_stage_report_has_data_analysis", "## Data Analysis" in completion_text, "research_documentation_completion_report.md")
    add_result(summary, "current_stage_report_has_next_hypothesis", "## Next Hypothesis" in completion_text, "research_documentation_completion_report.md")

    inconsistencies_text = (RESEARCH_DIR / "documentation_inconsistencies.md").read_text(encoding="utf-8")
    add_result(summary, "superseded_findings_preserved", "0.9458" in inconsistencies_text and "0.6679" in inconsistencies_text and "shadow" in inconsistencies_text, "revision chain documented")
    add_result(summary, "label_duplicates_not_independent", "deterministic duplicates" in inconsistencies_text and "10,000 strategy/base rows" in inconsistencies_text, "seat-order-neutral note")

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["check", "passed", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(summary)

    failed = [row for row in summary if row["passed"] != "True"]
    print(f"Documentation validation checks: {len(summary)}")
    print(f"Passed: {len(summary) - len(failed)}")
    print(f"Failed: {len(failed)}")
    for row in failed:
        print(f"FAIL {row['check']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
