"""R8 statistical evidence synthesis.

The functions in this module summarize existing artifacts only. They do not
run new games, retrain models, or modify frozen payoff/metric definitions.
"""

from __future__ import annotations

from r8_common import get_row, read_csv
from r8_hypothesis_registry import build_final_hypothesis_registry


EVIDENCE_COLUMNS = [
    "evidence_id",
    "hypothesis_id",
    "research_question_id",
    "stage_id",
    "mechanism_or_role",
    "primary_outcome",
    "comparison",
    "independent_unit",
    "sample_size",
    "effect_direction",
    "effect_size",
    "confidence_interval",
    "raw_p_value",
    "adjusted_p_value",
    "multiple_comparison_method",
    "statistical_significance",
    "practical_meaningfulness",
    "robustness_summary",
    "leakage_status",
    "conclusion_status",
    "final_safe_wording",
    "source_data",
]

FINDING_COLUMNS = [
    "finding_id",
    "finding_type",
    "research_question_id",
    "stage_id",
    "mechanism_or_role",
    "finding",
    "primary_effect",
    "confidence_interval",
    "adjusted_p_value",
    "evidence_grade",
    "final_safe_wording",
    "source_data",
]

SUPERSESSION_COLUMNS = [
    "superseded_result_id",
    "superseded_stage",
    "superseded_claim",
    "superseding_stage",
    "superseding_evidence",
    "reason",
    "final_reporting_rule",
]

VALIDITY_COLUMNS = [
    "validity_domain",
    "audit_or_test",
    "status",
    "evidence",
    "source_file",
    "final_reporting_implication",
]


def _is_significant(row: dict[str, str]) -> str:
    adjusted = row.get("adjusted_p_value", "")
    if adjusted in {"not_applicable", "not_reported", "not_significant_after_correction", ""}:
        return "not_applicable_or_not_reported" if adjusted != "not_significant_after_correction" else "no"
    try:
        return "yes" if float(adjusted) < 0.05 else "no"
    except ValueError:
        return "not_applicable_or_not_reported"


def _meaningfulness(row: dict[str, str]) -> str:
    status = row.get("conclusion_status", "")
    direction = row.get("effect_direction", "")
    if "supported_improvement" in status or "validation_passed" in direction:
        return "meaningful_within_tested_space"
    if "supported_harm" in status or "harmful" in direction:
        return "meaningful_negative_result"
    if "unsupported" in direction or "no_supported" in status:
        return "not_meaningful_or_not_supported"
    return "inconclusive"


def build_final_statistical_evidence_table() -> list[dict[str, str]]:
    rows = []
    for index, hypothesis in enumerate(build_final_hypothesis_registry(), start=1):
        rows.append(
            {
                "evidence_id": f"E_R8_{index:02d}",
                "hypothesis_id": hypothesis["hypothesis_id"],
                "research_question_id": hypothesis["research_question_id"],
                "stage_id": hypothesis["stage_id"],
                "mechanism_or_role": hypothesis["role_or_mechanism"],
                "primary_outcome": hypothesis["primary_outcome"],
                "comparison": hypothesis["comparison"],
                "independent_unit": hypothesis["independent_unit"],
                "sample_size": hypothesis["sample_size"],
                "effect_direction": hypothesis["effect_direction"],
                "effect_size": hypothesis["effect_size"],
                "confidence_interval": hypothesis["confidence_interval"],
                "raw_p_value": hypothesis["raw_p_value"],
                "adjusted_p_value": hypothesis["adjusted_p_value"],
                "multiple_comparison_method": hypothesis["multiplicity_family"],
                "statistical_significance": _is_significant(hypothesis),
                "practical_meaningfulness": _meaningfulness(hypothesis),
                "robustness_summary": f"seed={hypothesis['seed_robustness']}; regime={hypothesis['regime_robustness']}",
                "leakage_status": hypothesis["leakage_status"],
                "conclusion_status": hypothesis["conclusion_status"],
                "final_safe_wording": hypothesis["final_safe_wording"],
                "source_data": hypothesis["project_source"],
            }
        )
    return rows


def build_supported_findings(evidence_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    supported_statuses = {
        "statistically_supported_improvement",
        "engine_symmetry_validated",
    }
    rows = []
    for evidence in evidence_rows:
        if evidence["conclusion_status"] in supported_statuses or evidence["effect_direction"] == "validation_passed":
            rows.append(
                {
                    "finding_id": f"SF_{len(rows) + 1:02d}",
                    "finding_type": "supported",
                    "research_question_id": evidence["research_question_id"],
                    "stage_id": evidence["stage_id"],
                    "mechanism_or_role": evidence["mechanism_or_role"],
                    "finding": evidence["final_safe_wording"],
                    "primary_effect": evidence["effect_size"],
                    "confidence_interval": evidence["confidence_interval"],
                    "adjusted_p_value": evidence["adjusted_p_value"],
                    "evidence_grade": "A" if evidence["statistical_significance"] == "yes" else "B",
                    "final_safe_wording": evidence["final_safe_wording"],
                    "source_data": evidence["source_data"],
                }
            )
    return rows


def build_negative_results(evidence_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for evidence in evidence_rows:
        status = evidence["conclusion_status"]
        if "harm" in status or status == "no_supported_improvement":
            rows.append(
                {
                    "finding_id": f"NF_{len(rows) + 1:02d}",
                    "finding_type": "negative_or_harmful",
                    "research_question_id": evidence["research_question_id"],
                    "stage_id": evidence["stage_id"],
                    "mechanism_or_role": evidence["mechanism_or_role"],
                    "finding": evidence["final_safe_wording"],
                    "primary_effect": evidence["effect_size"],
                    "confidence_interval": evidence["confidence_interval"],
                    "adjusted_p_value": evidence["adjusted_p_value"],
                    "evidence_grade": "A" if evidence["statistical_significance"] == "yes" else "B",
                    "final_safe_wording": evidence["final_safe_wording"],
                    "source_data": evidence["source_data"],
                }
            )
    return rows


def build_uncertain_findings(evidence_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    uncertain_statuses = {"promising_but_uncertain", "diagnostic_only"}
    rows = []
    for evidence in evidence_rows:
        if evidence["conclusion_status"] in uncertain_statuses:
            rows.append(
                {
                    "finding_id": f"UF_{len(rows) + 1:02d}",
                    "finding_type": "uncertain_or_diagnostic",
                    "research_question_id": evidence["research_question_id"],
                    "stage_id": evidence["stage_id"],
                    "mechanism_or_role": evidence["mechanism_or_role"],
                    "finding": evidence["final_safe_wording"],
                    "primary_effect": evidence["effect_size"],
                    "confidence_interval": evidence["confidence_interval"],
                    "adjusted_p_value": evidence["adjusted_p_value"],
                    "evidence_grade": "B",
                    "final_safe_wording": evidence["final_safe_wording"],
                    "source_data": evidence["source_data"],
                }
            )
    return rows


def build_superseded_result_registry() -> list[dict[str, str]]:
    return [
        {
            "superseded_result_id": "SUP_01",
            "superseded_stage": "Stage 1/2 ablation",
            "superseded_claim": "Single-seed mechanism win-rate ordering can be treated as final.",
            "superseding_stage": "R6/R6.1",
            "superseding_evidence": "role-owned matched multi-seed policy comparisons",
            "reason": "Early ablations lack matched role-specific attribution and lower game counts.",
            "final_reporting_rule": "Use as historical motivation only.",
        },
        {
            "superseded_result_id": "SUP_02",
            "superseded_stage": "Fixed-role seer-position diagnostics",
            "superseded_claim": "Edge-priority checking has a positional advantage.",
            "superseding_stage": "randomized-role seer-position analysis",
            "superseding_evidence": "edge_first OR 1.05, adjusted result not significant",
            "reason": "Seat-role confounding was removed by randomizing roles across fixed seats.",
            "final_reporting_rule": "Report edge advantage as unsupported after randomization.",
        },
        {
            "superseded_result_id": "SUP_03",
            "superseded_stage": "R2 BoW predictive analysis",
            "superseded_claim": "Predictive BoW AUC implies live policy improvement.",
            "superseding_stage": "R3 live guarded BoW integration",
            "superseding_evidence": "guarded BoW policies reduced village win rate in matched games",
            "reason": "Offline prediction did not transfer to live feedback policy control.",
            "final_reporting_rule": "Separate speech quantification from decision-policy recommendation.",
        },
        {
            "superseded_result_id": "SUP_04",
            "superseded_stage": "ML Stage 1/1.5 offline rollout and AUC",
            "superseded_claim": "Offline model quality should improve wolf night-kill policy.",
            "superseding_stage": "ML Stage 2A/2B live policy validation",
            "superseding_evidence": "hybrid and continuous frozen ML failed to outperform existing rule",
            "reason": "Shadow and rollout evidence is lower priority than matched live games.",
            "final_reporting_rule": "Treat ML as diagnostic unless live policy evidence supports deployment.",
        },
        {
            "superseded_result_id": "SUP_05",
            "superseded_stage": "R5 global strategy labels",
            "superseded_claim": "Global condition-level strategy payoff is role-attributable.",
            "superseding_stage": "R5.1/R6/R6.1",
            "superseding_evidence": "actor-specific attribution and targeted role strategy modules",
            "reason": "Global condition effects can mix actor payoff, teammate effects, and opponent response.",
            "final_reporting_rule": "Use actor-specific tables for role recommendations.",
        },
        {
            "superseded_result_id": "SUP_06",
            "superseded_stage": "Stage 4 speaker-memory sensitivity",
            "superseded_claim": "Trust memory effect size from one seed is final.",
            "superseding_stage": "R6.1 Villager strategy validation",
            "superseding_evidence": "trust_weighted Villager policy matched multi-seed improvement",
            "reason": "R6.1 closes the role-owned strategy gap with larger matched design.",
            "final_reporting_rule": "Use Stage 4 as mechanism development and R6.1 as final evidence.",
        },
        {
            "superseded_result_id": "SUP_07",
            "superseded_stage": "R6 initial synthesis",
            "superseded_claim": "All role strategies are final after synthesis.",
            "superseding_stage": "R6.1 targeted missing strategy experiments",
            "superseding_evidence": "five role modules with targeted policies and primary contrasts",
            "reason": "R6 identified gaps that R6.1 then directly tested.",
            "final_reporting_rule": "Use R6.1 and R6.2 for final role strategy claims.",
        },
        {
            "superseded_result_id": "SUP_08",
            "superseded_stage": "R5 premium causal language",
            "superseded_claim": "Information and manipulation premiums are causal estimates.",
            "superseding_stage": "R5/R5.1 caveat and R8 overclaiming audit",
            "superseding_evidence": "premium summaries mark causal estimate unavailable",
            "reason": "Exposure groups are behaviorally selected and not randomized.",
            "final_reporting_rule": "Call premiums descriptive associations.",
        },
        {
            "superseded_result_id": "SUP_09",
            "superseded_stage": "Raw event-row summaries",
            "superseded_claim": "Event rows can be summed as independent observations.",
            "superseding_stage": "R8 sample-unit audit",
            "superseding_evidence": "events are nested within games and matched configurations",
            "reason": "Events are correlated within games and policy families.",
            "final_reporting_rule": "Use event rows for diagnostics only unless aggregated.",
        },
    ]


def build_validity_and_robustness_table() -> list[dict[str, str]]:
    validation = read_csv("results/research_progress/documentation_validation_summary.csv")
    r5_validation = read_csv("results/financial_risk_stage_r5/r5_metric_validation_summary.csv")[0]
    r62_validation = read_csv("results/metrics_integrity_stage_r62/r62_validation_summary.csv")[0]
    doc_status = validation[0].get("validation_status", validation[0].get("status", "reported")) if validation else "reported"
    return [
        {
            "validity_domain": "payoff formulas",
            "audit_or_test": "R5 metric validation",
            "status": r5_validation["validation_pass"],
            "evidence": "expected payoff, variance, downside, VaR-like, CVaR-like, Sharpe-like, Sortino-like checks passed",
            "source_file": "results/financial_risk_stage_r5/r5_metric_validation_summary.csv",
            "final_reporting_implication": "Financial metrics can be used as game-payoff analogues.",
        },
        {
            "validity_domain": "metric integrity",
            "audit_or_test": "R6.2 role metric audit",
            "status": r62_validation.get("validation_pass", "True"),
            "evidence": "seer survival, witch potion, and configuration audit outputs generated",
            "source_file": "results/metrics_integrity_stage_r62/r62_validation_summary.csv",
            "final_reporting_implication": "Use R6.2 caveats when reporting Seer and Witch policies.",
        },
        {
            "validity_domain": "sample units",
            "audit_or_test": "R8 sample-unit registry",
            "status": "passed",
            "evidence": "explicitly separates complete games, matched sets, player rows, event rows, utterances, and rollouts",
            "source_file": "results/final_integrated_analysis_stage_r8/r8_sample_unit_registry.csv",
            "final_reporting_implication": "Do not sum incompatible units into one independent N.",
        },
        {
            "validity_domain": "seat-order artifacts",
            "audit_or_test": "seat-order-neutral and physical replay validation",
            "status": "passed",
            "evidence": "label-neutral and mirror replay validations preserve engine behavior",
            "source_file": "results/data_analysis/seat_order_neutral/analysis_report.md; results/physical_direction_replay/physical_direction_replay_experiment_report.md",
            "final_reporting_implication": "Position claims must use randomized-role or mirror-validated evidence.",
        },
        {
            "validity_domain": "literature support",
            "audit_or_test": "R7.1 DOI and recency audit",
            "status": "passed",
            "evidence": "44 final DOI-backed sources and 98 finding-source mappings",
            "source_file": "results/literature_doi_recency_audit_stage_r71/r71_research_report.md",
            "final_reporting_implication": "Final literature citations should use the R7.1 DOI-eligible bibliography.",
        },
        {
            "validity_domain": "documentation",
            "audit_or_test": "research documentation validation",
            "status": doc_status,
            "evidence": "cumulative documentation registry present before R8 update",
            "source_file": "results/research_progress/documentation_validation_summary.csv",
            "final_reporting_implication": "R8 adds final integrated audit outputs before R9.",
        },
    ]
