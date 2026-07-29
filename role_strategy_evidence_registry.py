"""Source registry and evidence grade definitions for R6 synthesis."""

from __future__ import annotations

from pathlib import Path


R6_RESULTS_DIR = Path("results") / "role_strategy_synthesis_stage_r6"

EVIDENCE_GRADES = {
    "A": "Strong formal support: valid actor-specific comparison, adequate sample, adjusted inference, and no major design concern.",
    "B": "Moderate support: valid repeated evidence with stable direction, but formal inference or strategy coverage is incomplete.",
    "C": "Promising but uncertain: positive or useful signal with unresolved inference, sparse coverage, or confidence intervals crossing no effect.",
    "D": "No supported improvement: no reliable advantage over the relevant reference condition.",
    "E": "Supported harmful or not recommended: formal harm, repeated live-policy failure, or clear negative mechanism result.",
    "F": "Invalid or superseded: leakage, mapping error, surrogate-only result contradicted by live validation, or superseded attribution.",
    "U": "Unresolved or insufficient data: no compatible actor-specific comparison or missing event-level coverage.",
}

RECOMMENDATION_LABELS = {
    "recommended under current evidence",
    "conditionally recommended",
    "retain reference/default",
    "promising but uncertain",
    "no supported improvement",
    "not recommended",
    "statistically supported harmful",
    "diagnostic only",
    "insufficient data",
    "invalid or superseded",
    "requires targeted experiment",
}

CONFIDENCE_LEVELS = {"high", "moderate", "low", "insufficient"}

SOURCE_EVIDENCE_FILES = [
    "results/payoff_matrix_stage_r4/r4_payoff_manifest.json",
    "results/financial_risk_stage_r5/r5_metric_definition_manifest.json",
    "results/financial_risk_stage_r5/r5_role_expected_payoff_summary.csv",
    "results/financial_risk_stage_r5/r5_role_var_cvar_summary.csv",
    "results/financial_risk_stage_r51/r51_mapping_validation_summary.csv",
    "results/financial_risk_stage_r51/r51_actor_specific_strategy_summary.csv",
    "results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv",
    "results/financial_risk_stage_r51/r51_cross_role_externality_summary.csv",
    "results/financial_risk_stage_r51/r51_information_premium_summary.csv",
    "results/financial_risk_stage_r51/r51_manipulation_premium_summary.csv",
    "results/financial_risk_stage_r51/r51_r5_result_validity_registry.csv",
    "results/bow_speech_stage_r2/bow_stage_r2_research_report.md",
    "results/bow_integration_stage_r3/r3_policy_game_outcome_summary.csv",
    "results/bow_integration_stage_r3/r3_primary_game_contrasts.csv",
    "results/structured_seer_search/structured_seer_search_strategy_summary.csv",
    "results/data_analysis/structured_seer_search/pairwise_strategy_contrasts.csv",
    "results/data_analysis/structured_seer_search/strategy_omnibus_tests.csv",
    "results/data_analysis/seer_position_randomized_roles/statistical_summary.csv",
    "results/data_analysis/seer_position_randomized_roles/pairwise_strategy_comparisons.csv",
    "results/data_analysis/seat_order_neutral/validation_summary.csv",
    "results/ml_optimization_stage2a/wolf_kill_live_policy_summary.csv",
    "results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv",
    "results/ml_optimization_stage2b/stage2b_policy_win_summary.csv",
    "results/ml_optimization_stage2b/stage2b_primary_contrasts.csv",
    "stage3_experiment_report.md",
]


def get_evidence_grade_definitions() -> list[dict[str, str]]:
    """Return evidence grade rows for export."""
    return [
        {"grade": grade, "definition": definition}
        for grade, definition in EVIDENCE_GRADES.items()
    ]


def get_source_evidence_files() -> list[str]:
    """Return all source files reviewed by the R6 synthesis."""
    return list(SOURCE_EVIDENCE_FILES)


def validate_source_files(root: Path | None = None) -> list[dict[str, str]]:
    """Validate that source paths used by R6 exist."""
    root = root or Path(".")
    rows = []
    for source in SOURCE_EVIDENCE_FILES:
        path = root / source
        rows.append(
            {
                "source_path": source,
                "exists": str(path.exists()),
                "source_type": path.suffix.lstrip(".") or "unknown",
            }
        )
    return rows
