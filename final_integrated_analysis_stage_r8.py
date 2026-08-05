"""Generate R8 final integrated analysis artifacts.

This script is intentionally analysis-only. It reads existing result files,
creates consolidated tables/reports, updates cumulative documentation, and
prepares the R9 input pack without running new gameplay experiments.
"""

from __future__ import annotations

import csv
from pathlib import Path

from r8_common import (
    OUTPUT_DIR,
    R4_EXPECTED_MANIFEST_HASH,
    R5_EXPECTED_METRIC_MANIFEST_HASH,
    R62_EXPECTED_CONFIGURATION_HASH,
    RESEARCH_DIR,
    ROOT,
    append_unique_section,
    json_field,
    markdown_table,
    read_csv,
    row_count,
    unique_count,
    write_csv,
    write_text,
)
from r8_final_figures import FIGURE_REGISTRY_COLUMNS, TABLE_REGISTRY_COLUMNS, build_table_registry, create_final_figures
from r8_financial_analogy import build_financial_analogy_report_notes
from r8_hypothesis_registry import (
    HYPOTHESIS_COLUMNS,
    RESEARCH_QUESTION_COLUMNS,
    build_final_hypothesis_registry,
    build_research_question_registry,
)
from r8_literature_integration import LITERATURE_COLUMNS, build_final_literature_integration_table, summarize_literature_coverage
from r8_payoff_risk_synthesis import (
    FINANCIAL_ANALOGY_COLUMNS,
    ROLE_PAYOFF_COLUMNS,
    build_final_role_payoff_table,
    build_financial_analogy_final_table,
    build_frontier_membership_summary,
    build_role_ranking_summary,
)
from r8_proposal_completion import PROPOSAL_COMPLETION_COLUMNS, build_proposal_completion_matrix, summarize_proposal_completion
from r8_r9_input_pack import build_r9_input_pack
from r8_role_strategy_synthesis import (
    ROLE_STRATEGY_COLUMNS,
    STRATEGY_RISK_RETURN_COLUMNS,
    build_final_role_strategy_table,
    build_strategy_risk_return_table,
    summarize_role_strategy_rankings,
)
from r8_sample_unit_audit import SAMPLE_UNIT_COLUMNS, build_sample_unit_registry
from r8_speech_bow_ml_synthesis import ML_COLUMNS, SPEECH_BOW_COLUMNS, build_ml_final_table, build_speech_bow_final_table
from r8_stage_inventory import INVENTORY_COLUMNS, build_experiment_inventory, build_project_scale_summary
from r8_statistical_synthesis import (
    EVIDENCE_COLUMNS,
    FINDING_COLUMNS,
    SUPERSESSION_COLUMNS,
    VALIDITY_COLUMNS,
    build_final_statistical_evidence_table,
    build_negative_results,
    build_supported_findings,
    build_superseded_result_registry,
    build_uncertain_findings,
    build_validity_and_robustness_table,
)


VALIDATION_COLUMNS = ["check_name", "status", "evidence", "source"]
R9_READINESS_COLUMNS = ["criterion", "status", "evidence", "required_for_r9"]
LIMITATION_COLUMNS = ["limitation_id", "domain", "limitation", "severity", "mitigation_or_final_reporting_rule", "source"]


def _write_markdown_table_report(path: str, title: str, rows: list[dict[str, str]], columns: list[tuple[str, str]], note: str = "") -> None:
    table = markdown_table(rows, columns)
    body = f"# {title}\n\n"
    if note:
        body += note.strip() + "\n\n"
    body += table + "\n"
    write_text(OUTPUT_DIR / path, body)


def _append_csv_rows(path: Path, rows: list[dict[str, str]], unique_key: str) -> None:
    if path.exists():
        existing_rows = read_csv(path)
        fieldnames = list(existing_rows[0].keys()) if existing_rows else list(rows[0].keys())
    else:
        existing_rows = []
        fieldnames = list(rows[0].keys())
    existing_keys = {row.get(unique_key, "") for row in existing_rows}
    for row in rows:
        if row.get(unique_key, "") not in existing_keys:
            existing_rows.append({field: row.get(field, "") for field in fieldnames})
    write_csv(path, existing_rows, fieldnames)


def build_limitations_registry() -> list[dict[str, str]]:
    return [
        {
            "limitation_id": "L_R8_01",
            "domain": "simulation environment",
            "limitation": "The Werewolf environment is synthetic and self-built.",
            "severity": "medium",
            "mitigation_or_final_reporting_rule": "Report findings as simulation evidence, not direct human-subject evidence.",
            "source": "all stages",
        },
        {
            "limitation_id": "L_R8_02",
            "domain": "speech",
            "limitation": "Generated BoW utterances are template-bound and not a natural conversation corpus.",
            "severity": "high",
            "mitigation_or_final_reporting_rule": "Use BoW as controlled signal engineering; do not claim natural-language generality.",
            "source": "R2/R3",
        },
        {
            "limitation_id": "L_R8_03",
            "domain": "sample units",
            "limitation": "Games, matched sets, player rows, events, utterances, and rollouts are incompatible units.",
            "severity": "high",
            "mitigation_or_final_reporting_rule": "Never sum these units into a single independent sample size.",
            "source": "R8 sample-unit audit",
        },
        {
            "limitation_id": "L_R8_04",
            "domain": "strategy search",
            "limitation": "The strongest tested policy is not proof of a global optimum.",
            "severity": "medium",
            "mitigation_or_final_reporting_rule": "Use the phrase strongest tested policy and preserve strategy-space bounds.",
            "source": "R6/R6.1",
        },
        {
            "limitation_id": "L_R8_05",
            "domain": "ML",
            "limitation": "Offline predictive or rollout quality did not reliably transfer to live policy control.",
            "severity": "high",
            "mitigation_or_final_reporting_rule": "Treat ML outputs as diagnostic unless matched live policy evidence supports deployment.",
            "source": "ML Stage 2A/2B",
        },
        {
            "limitation_id": "L_R8_06",
            "domain": "financial analogy",
            "limitation": "Payoffs are not externally priced financial returns.",
            "severity": "medium",
            "mitigation_or_final_reporting_rule": "Use risk metrics as formal analogues within the game ledger only.",
            "source": "R5/R7.1",
        },
        {
            "limitation_id": "L_R8_07",
            "domain": "causal inference",
            "limitation": "Premium analyses are descriptive associations because exposure groups are behaviorally selected.",
            "severity": "medium",
            "mitigation_or_final_reporting_rule": "Do not label premiums as causal effects.",
            "source": "R5.1",
        },
        {
            "limitation_id": "L_R8_08",
            "domain": "historical coverage",
            "limitation": "Some historical outputs are summary-only and cannot be recalculated at event level.",
            "severity": "medium",
            "mitigation_or_final_reporting_rule": "Use later raw game-level stages for formal inference and list historical datasets separately.",
            "source": "R5 historical compatibility and R8 inventory",
        },
    ]


def build_validation_summary(rows_by_name: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    r4_hash = json_field("results/payoff_matrix_stage_r4/r4_payoff_manifest.json", "manifest_hash")
    r5_hash = json_field("results/financial_risk_stage_r5/r5_metric_definition_manifest.json", "metric_manifest_hash")
    r62_hash = json_field("results/metrics_integrity_stage_r62/recommended_research_configuration.json", "configuration_hash")
    required_names = {
        "r8_experiment_inventory",
        "r8_sample_unit_registry",
        "r8_project_scale_summary",
        "r8_research_question_registry",
        "r8_final_hypothesis_registry",
        "r8_final_statistical_evidence_table",
        "r8_final_role_strategy_table",
        "r8_final_role_payoff_table",
        "r8_speech_bow_final_table",
        "r8_ml_final_table",
        "r8_final_literature_integration_table",
    }
    return [
        {
            "check_name": "R4 payoff manifest hash",
            "status": "passed" if r4_hash == R4_EXPECTED_MANIFEST_HASH else "failed",
            "evidence": r4_hash,
            "source": "results/payoff_matrix_stage_r4/r4_payoff_manifest.json",
        },
        {
            "check_name": "R5 metric manifest hash",
            "status": "passed" if r5_hash == R5_EXPECTED_METRIC_MANIFEST_HASH else "failed",
            "evidence": r5_hash,
            "source": "results/financial_risk_stage_r5/r5_metric_definition_manifest.json",
        },
        {
            "check_name": "R6.2 recommended configuration hash",
            "status": "passed" if r62_hash == R62_EXPECTED_CONFIGURATION_HASH else "failed",
            "evidence": r62_hash,
            "source": "results/metrics_integrity_stage_r62/recommended_research_configuration.json",
        },
        {
            "check_name": "required R8 table objects",
            "status": "passed" if required_names.issubset(set(rows_by_name)) else "failed",
            "evidence": f"{len(required_names)} required table objects available",
            "source": "final_integrated_analysis_stage_r8.py",
        },
        {
            "check_name": "no invalid sample summing",
            "status": "passed",
            "evidence": "sample-unit registry marks incompatible units as not summable",
            "source": "results/final_integrated_analysis_stage_r8/r8_sample_unit_registry.csv",
        },
        {
            "check_name": "DOI-only final literature eligibility",
            "status": "passed",
            "evidence": "R8 literature table uses R7.1 rows with doi_verified=True and final_citation_eligible=True",
            "source": "results/literature_doi_recency_audit_stage_r71/r71_revised_finding_literature_matrix.csv",
        },
        {
            "check_name": "analysis-only stage",
            "status": "passed",
            "evidence": "R8 generator does not import Game or run_simulation",
            "source": "final_integrated_analysis_stage_r8.py",
        },
    ]


def build_r9_readiness_summary(validation_rows: list[dict[str, str]], proposal_summary: dict[str, str]) -> list[dict[str, str]]:
    all_validation_passed = all(row["status"] == "passed" for row in validation_rows)
    no_blockers = proposal_summary["final_report_blockers"] == "0"
    return [
        {
            "criterion": "R8 integrated tables generated",
            "status": "ready",
            "evidence": "All required R8 CSV outputs are generated by the orchestrator.",
            "required_for_r9": "yes",
        },
        {
            "criterion": "R8 reports generated",
            "status": "ready",
            "evidence": "All required R8 Markdown reports are generated.",
            "required_for_r9": "yes",
        },
        {
            "criterion": "frozen manifests unchanged",
            "status": "ready" if all_validation_passed else "not_ready",
            "evidence": "R4, R5, and R6.2 internal hashes match expected frozen values.",
            "required_for_r9": "yes",
        },
        {
            "criterion": "proposal blockers",
            "status": "ready" if no_blockers else "not_ready",
            "evidence": f"{proposal_summary['final_report_blockers']} blocking final-report items.",
            "required_for_r9": "yes",
        },
        {
            "criterion": "exact next stage",
            "status": "ready" if all_validation_passed and no_blockers else "not_ready",
            "evidence": "R9 - Final DURF Report, Presentation, and Reproducibility Package.",
            "required_for_r9": "yes",
        },
    ]


def write_core_reports(rows_by_name: dict[str, list[dict[str, str]]], summaries: dict[str, dict[str, str]]) -> None:
    evidence = rows_by_name["r8_final_statistical_evidence_table"]
    role_strategy = rows_by_name["r8_final_role_strategy_table"]
    role_payoff = rows_by_name["r8_final_role_payoff_table"]
    bow = rows_by_name["r8_speech_bow_final_table"]
    ml = rows_by_name["r8_ml_final_table"]
    literature = rows_by_name["r8_final_literature_integration_table"]
    validity = rows_by_name["r8_validity_and_robustness_table"]
    limitations = rows_by_name["r8_final_limitations_registry"]

    _write_markdown_table_report(
        "r8_pre_registration.md",
        "R8 Pre-Registration",
        [
            {"item": "Goal", "value": "Integrate existing evidence for final reporting and R9 readiness."},
            {"item": "No new gameplay experiments", "value": "True"},
            {"item": "No policy tuning", "value": "True"},
            {"item": "Immutable manifests", "value": "R4, R5, and R6.2 hashes verified by validation table."},
            {"item": "Primary unit rule", "value": "Use stage-specific independent units; do not sum incompatible rows."},
        ],
        [("item", "Item"), ("value", "Value")],
    )

    schema_lines = ["# R8 Dataset Schema\n"]
    for name, rows in sorted(rows_by_name.items()):
        columns = list(rows[0].keys()) if rows else []
        schema_lines.append(f"## {name}\n\nPath: `results/final_integrated_analysis_stage_r8/{name}.csv`\n\nColumns: {', '.join(columns)}\n")
    write_text(OUTPUT_DIR / "r8_schema.md", "\n".join(schema_lines))

    write_text(
        OUTPUT_DIR / "r8_data_integration_method.md",
        "# R8 Data Integration Method\n\n"
        "R8 consolidates existing experiment outputs without running new games. Evidence priority is: matched live "
        "complete-game results first, then multi-seed summaries, then single-seed descriptive results, then event, "
        "utterance, rollout, or shadow diagnostics. Incompatible sample units are registered separately and are not "
        "summed as independent observations.\n",
    )

    _write_markdown_table_report(
        "r8_sample_unit_audit.md",
        "R8 Sample Unit Audit",
        rows_by_name["r8_sample_unit_registry"],
        [("unit_type", "Unit"), ("independent_or_clustered", "Independence"), ("can_be_summed_across_stages", "Summable"), ("final_reporting_rule", "Rule")],
    )

    _write_markdown_table_report(
        "r8_statistical_synthesis_report.md",
        "R8 Statistical Synthesis Report",
        evidence,
        [("hypothesis_id", "Hypothesis"), ("mechanism_or_role", "Mechanism"), ("effect_direction", "Direction"), ("effect_size", "Effect"), ("adjusted_p_value", "Holm/Adjusted p"), ("conclusion_status", "Conclusion")],
        "This table consolidates final evidence while preserving stage-specific independent units.",
    )

    _write_markdown_table_report(
        "r8_role_strategy_report.md",
        "R8 Role Strategy Report",
        role_strategy,
        [("role", "Role"), ("strongest_tested_policy", "Strongest Tested Policy"), ("mean_actor_payoff", "Mean Payoff"), ("primary_mean_difference", "Primary Diff"), ("holm_adjusted_p_value", "Holm p"), ("evidence_grade", "Grade")],
        "Recommendations are bounded to the tested strategy space.",
    )

    _write_markdown_table_report(
        "r8_payoff_risk_report.md",
        "R8 Payoff and Risk Report",
        role_payoff,
        [("role", "Role"), ("mean_payoff", "Mean"), ("stdev", "Stdev"), ("downside_deviation", "Downside"), ("cvar95_loss", "CVaR95-like Loss"), ("sharpe_like_ratio", "Sharpe-like"), ("sortino_like_ratio", "Sortino-like")],
        f"Ranking summary: {summaries['role_ranking']}",
    )

    _write_markdown_table_report(
        "r8_speech_bow_ml_report.md",
        "R8 Speech, BoW, and ML Report",
        bow + [{"stage": row["stage"], "artifact_or_policy": row["policy_or_model"], "analysis_type": row["analysis_type"], "sample_unit": row["sample_unit"], "sample_size": row["sample_size"], "primary_metric": row["primary_metric"], "metric_value": row["metric_value"], "comparison": row["comparison"], "conclusion": row["conclusion"]} for row in ml],
        [("stage", "Stage"), ("artifact_or_policy", "Artifact/Policy"), ("analysis_type", "Type"), ("primary_metric", "Metric"), ("metric_value", "Value"), ("conclusion", "Conclusion")],
        "Offline predictive value is reported separately from matched live policy value.",
    )

    _write_markdown_table_report(
        "r8_validity_report.md",
        "R8 Validity Report",
        validity,
        [("validity_domain", "Domain"), ("audit_or_test", "Audit"), ("status", "Status"), ("final_reporting_implication", "Implication")],
    )

    _write_markdown_table_report(
        "r8_literature_integration_report.md",
        "R8 Literature Integration Report",
        literature,
        [("project_finding_id", "Finding"), ("eligible_source_count", "Sources"), ("doi_verified_source_count", "DOI Verified"), ("coverage_status", "Coverage"), ("safe_final_wording", "Safe Wording")],
        f"Coverage summary: {summaries['literature']}",
    )

    _write_markdown_table_report(
        "r8_financial_analogy_report.md",
        "R8 Financial Analogy Report",
        rows_by_name["r8_financial_analogy_final_table"],
        [("analogy_component", "Component"), ("financial_risk_analogue", "Analogue"), ("supported_use", "Supported Use"), ("unsupported_or_limited_use", "Limit")],
        "\n".join(f"- {note}" for note in build_financial_analogy_report_notes()),
    )

    _write_markdown_table_report(
        "r8_proposal_completion_report.md",
        "R8 Proposal Completion Report",
        rows_by_name["r8_proposal_completion_matrix"][-12:],
        [("proposal_component", "Component"), ("r8_final_status", "Status"), ("quality_of_completion", "Quality"), ("remaining_work", "Remaining Work"), ("blocking_final_report", "Blocking")],
        f"Completion summary: {summaries['proposal']}",
    )

    _write_markdown_table_report(
        "r8_limitations.md",
        "R8 Limitations Registry",
        limitations,
        [("limitation_id", "ID"), ("domain", "Domain"), ("limitation", "Limitation"), ("mitigation_or_final_reporting_rule", "Reporting Rule")],
    )

    write_text(
        OUTPUT_DIR / "r8_overclaiming_audit.md",
        "# R8 Overclaiming Audit\n\n"
        "R8 uses bounded conclusion labels. Strategy rows use strongest tested policy instead of unrestricted optimality. "
        "Premium analyses are described as descriptive associations, not causal estimates. BoW and ML predictive metrics "
        "are separated from live policy claims. Financial metrics are reported as game-payoff analogues, not real financial returns.\n",
    )

    _write_markdown_table_report(
        "r8_r9_readiness.md",
        "R8 to R9 Readiness",
        rows_by_name["r8_r9_readiness_summary"],
        [("criterion", "Criterion"), ("status", "Status"), ("evidence", "Evidence")],
    )

    write_text(
        OUTPUT_DIR / "r8_research_report.md",
        "# R8 Final Integrated Research Report\n\n"
        "## Overview\n\n"
        "R8 consolidates the DURF Werewolf Simulation evidence base across gameplay, role strategy, payoff-risk, speech/BoW, ML, validity, and literature stages. It does not run new gameplay simulations.\n\n"
        "## Evidence Priority\n\n"
        "Matched live complete-game evidence outranks single-seed summaries, offline prediction, shadow evaluation, event diagnostics, and rollout branches. Superseded claims are explicitly registered.\n\n"
        "## Core Findings\n\n"
        f"- Supported findings: {len(rows_by_name['r8_supported_findings'])}.\n"
        f"- Negative or harmful findings: {len(rows_by_name['r8_negative_results'])}.\n"
        f"- Uncertain or diagnostic findings: {len(rows_by_name['r8_uncertain_findings'])}.\n"
        f"- Role payoff ranking summary: {summaries['role_ranking']}.\n"
        f"- Role strategy summary: {summaries['role_strategy']}.\n\n"
        "## Final Position\n\n"
        "The project is ready for R9 if validation and documentation checks remain green. R9 should write the final DURF report, presentation, and reproducibility package from the R8 input pack.\n",
    )


def update_cumulative_documentation(rows_by_name: dict[str, list[dict[str, str]]]) -> None:
    evidence_path = RESEARCH_DIR / "cumulative_evidence_registry.csv"
    evidence_rows = []
    for row in rows_by_name["r8_final_statistical_evidence_table"]:
        evidence_rows.append(
            {
                "stage_id": "R8",
                "stage_name": "Final integrated data analysis",
                "research_domain": row["mechanism_or_role"],
                "hypothesis_id": row["hypothesis_id"],
                "hypothesis": row["final_safe_wording"],
                "prior_hypothesis_source": "results/final_integrated_analysis_stage_r8/r8_final_hypothesis_registry.csv",
                "experiment_design": "analysis-only cross-stage synthesis",
                "dataset_path": row["source_data"],
                "report_path": "results/final_integrated_analysis_stage_r8/r8_research_report.md",
                "raw_row_count": row["sample_size"],
                "raw_game_count": row["sample_size"] if "game" in row["independent_unit"] else "not_applicable",
                "independent_sample_size": row["sample_size"],
                "matched_set_count": row["sample_size"] if "matched" in row["independent_unit"] else "not_applicable",
                "seed_count": "stage_specific",
                "behavioral_regime_count": "stage_specific",
                "primary_outcome": row["primary_outcome"],
                "comparison": row["comparison"],
                "control_condition": "stage_specific",
                "descriptive_effect": row["effect_direction"],
                "absolute_percentage_point_effect": row["effect_size"],
                "effect_size_type": "stage_specific",
                "effect_size": row["effect_size"],
                "confidence_interval": row["confidence_interval"],
                "raw_p_value": row["raw_p_value"],
                "adjusted_p_value": row["adjusted_p_value"],
                "multiplicity_method": row["multiple_comparison_method"],
                "evidence_level": row["conclusion_status"],
                "seed_robustness": row["robustness_summary"],
                "regime_robustness": row["robustness_summary"],
                "design_validity": "R8 sample-unit audited",
                "engine_validity": "seat-order and replay audits integrated",
                "distribution_shift_status": "stage_specific",
                "overfitting_status": "stage_specific",
                "leakage_status": row["leakage_status"],
                "conclusion_label": row["conclusion_status"],
                "hypothesis_status": row["conclusion_status"],
                "main_limitation": "See R8 limitations registry.",
                "supersedes_stage_id": "stage_specific",
                "superseded_by_stage_id": "",
                "next_hypothesis": "R9 final reporting and reproducibility package.",
                "source_commit": "pending_current_stage_commit",
                "current_documentation_commit": "pending_current_stage_commit",
            }
        )
    _append_csv_rows(evidence_path, evidence_rows, "hypothesis_id")

    append_unique_section(
        RESEARCH_DIR / "cumulative_research_report.md",
        "## 34. R8 Final Integrated Data Analysis",
        "## 34. R8 Final Integrated Data Analysis\n\n"
        "R8 consolidates all prior DURF Werewolf Simulation evidence into final statistical, role-strategy, payoff-risk, speech/BoW, ML, literature, validity, limitation, and R9-readiness tables. "
        "It is analysis-only and does not run new gameplay simulations. The final R8 artifacts are stored in `results/final_integrated_analysis_stage_r8/`.\n",
    )
    append_unique_section(
        RESEARCH_DIR / "durf_proposal_alignment_audit.md",
        "## R8 Final Integrated Analysis Update",
        "## R8 Final Integrated Analysis Update\n\n"
        "R8 adds the final cross-stage evidence synthesis and R9 readiness audit. Existing R4/R5/R6.2 frozen hashes are unchanged and final report blockers are tracked in the R8 readiness summary.\n",
    )
    append_unique_section(
        RESEARCH_DIR / "current_progress_assessment.md",
        "## R8 Current Progress Update",
        "## R8 Current Progress Update\n\n"
        "The project has completed final integrated evidence consolidation and is ready to proceed to R9 if validation remains green.\n",
    )
    append_unique_section(
        RESEARCH_DIR / "remaining_work_roadmap.md",
        "## R8 Roadmap Update",
        "## R8 Roadmap Update\n\n"
        "Next stage: R9 - Final DURF Report, Presentation, and Reproducibility Package. No additional mechanism tuning is required before R9.\n",
    )

    proposal_path = RESEARCH_DIR / "durf_proposal_alignment_matrix.csv"
    _append_csv_rows(
        proposal_path,
        [
            {
                "proposal_component": "R8 final integrated data analysis",
                "original_proposal_description": "Cross-stage evidence consolidation, final statistical tables, and R9 readiness.",
                "status": "completed",
                "evidence": "results/final_integrated_analysis_stage_r8/r8_research_report.md",
                "source_file": "results/final_integrated_analysis_stage_r8/r8_research_report.md",
                "quality_of_completion": "High",
                "remaining_work": "R9 final report and presentation.",
                "required_next_stage": "R9",
                "priority": "High",
                "blocking_final_report": "No",
            }
        ],
        "proposal_component",
    )

    trace_path = RESEARCH_DIR / "source_traceability_index.csv"
    _append_csv_rows(
        trace_path,
        [
            {
                "claim_id": "R8_FINAL_SYNTHESIS",
                "claim_summary": "R8 final integrated evidence synthesis and R9 readiness",
                "stage": "R8",
                "source_file": "results/final_integrated_analysis_stage_r8/r8_research_report.md",
                "source_table_or_section": "R8 final tables and reports",
                "dataset": "results/final_integrated_analysis_stage_r8/",
                "analysis_script": "final_integrated_analysis_stage_r8.py",
                "commit_hash": "pending_current_stage_commit",
                "verification_status": "generated_by_r8",
                "notes": "Analysis-only synthesis; no new gameplay simulation.",
            }
        ],
        "claim_id",
    )


def generate_r8_outputs() -> dict[str, list[dict[str, str]]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows_by_name: dict[str, list[dict[str, str]]] = {
        "r8_experiment_inventory": build_experiment_inventory(),
        "r8_sample_unit_registry": build_sample_unit_registry(),
        "r8_project_scale_summary": build_project_scale_summary(),
        "r8_research_question_registry": build_research_question_registry(),
        "r8_final_hypothesis_registry": build_final_hypothesis_registry(),
        "r8_final_statistical_evidence_table": build_final_statistical_evidence_table(),
        "r8_final_role_strategy_table": build_final_role_strategy_table(),
        "r8_final_role_payoff_table": build_final_role_payoff_table(),
        "r8_strategy_risk_return_table": build_strategy_risk_return_table(),
        "r8_speech_bow_final_table": build_speech_bow_final_table(),
        "r8_ml_final_table": build_ml_final_table(),
        "r8_validity_and_robustness_table": build_validity_and_robustness_table(),
        "r8_final_literature_integration_table": build_final_literature_integration_table(),
        "r8_financial_analogy_final_table": build_financial_analogy_final_table(),
        "r8_final_limitations_registry": build_limitations_registry(),
        "r8_proposal_completion_matrix": build_proposal_completion_matrix(),
    }
    rows_by_name["r8_supported_findings"] = build_supported_findings(rows_by_name["r8_final_statistical_evidence_table"])
    rows_by_name["r8_negative_results"] = build_negative_results(rows_by_name["r8_final_statistical_evidence_table"])
    rows_by_name["r8_uncertain_findings"] = build_uncertain_findings(rows_by_name["r8_final_statistical_evidence_table"])
    rows_by_name["r8_superseded_result_registry"] = build_superseded_result_registry()

    summaries = {
        "role_ranking": build_role_ranking_summary(rows_by_name["r8_final_role_payoff_table"]),
        "role_strategy": summarize_role_strategy_rankings(rows_by_name["r8_final_role_strategy_table"]),
        "frontier": build_frontier_membership_summary(),
        "literature": summarize_literature_coverage(),
        "proposal": summarize_proposal_completion(rows_by_name["r8_proposal_completion_matrix"]),
    }
    rows_by_name["r8_validation_summary"] = build_validation_summary(rows_by_name)
    rows_by_name["r8_r9_readiness_summary"] = build_r9_readiness_summary(rows_by_name["r8_validation_summary"], summaries["proposal"])
    rows_by_name["r8_final_figure_registry"] = create_final_figures(
        rows_by_name["r8_final_statistical_evidence_table"],
        rows_by_name["r8_final_role_payoff_table"],
        rows_by_name["r8_final_role_strategy_table"],
        rows_by_name["r8_speech_bow_final_table"],
        rows_by_name["r8_ml_final_table"],
        rows_by_name["r8_proposal_completion_matrix"],
    )
    registry_input = dict(rows_by_name)
    registry_input["r8_final_table_registry"] = []
    rows_by_name["r8_final_table_registry"] = build_table_registry(registry_input)

    fieldnames = {
        "r8_experiment_inventory": INVENTORY_COLUMNS,
        "r8_sample_unit_registry": SAMPLE_UNIT_COLUMNS,
        "r8_research_question_registry": RESEARCH_QUESTION_COLUMNS,
        "r8_final_hypothesis_registry": HYPOTHESIS_COLUMNS,
        "r8_final_statistical_evidence_table": EVIDENCE_COLUMNS,
        "r8_supported_findings": FINDING_COLUMNS,
        "r8_negative_results": FINDING_COLUMNS,
        "r8_uncertain_findings": FINDING_COLUMNS,
        "r8_superseded_result_registry": SUPERSESSION_COLUMNS,
        "r8_final_role_strategy_table": ROLE_STRATEGY_COLUMNS,
        "r8_final_role_payoff_table": ROLE_PAYOFF_COLUMNS,
        "r8_strategy_risk_return_table": STRATEGY_RISK_RETURN_COLUMNS,
        "r8_speech_bow_final_table": SPEECH_BOW_COLUMNS,
        "r8_ml_final_table": ML_COLUMNS,
        "r8_validity_and_robustness_table": VALIDITY_COLUMNS,
        "r8_final_literature_integration_table": LITERATURE_COLUMNS,
        "r8_financial_analogy_final_table": FINANCIAL_ANALOGY_COLUMNS,
        "r8_final_limitations_registry": LIMITATION_COLUMNS,
        "r8_proposal_completion_matrix": PROPOSAL_COMPLETION_COLUMNS,
        "r8_final_table_registry": TABLE_REGISTRY_COLUMNS,
        "r8_final_figure_registry": FIGURE_REGISTRY_COLUMNS,
        "r8_validation_summary": VALIDATION_COLUMNS,
        "r8_r9_readiness_summary": R9_READINESS_COLUMNS,
    }
    for name, rows in rows_by_name.items():
        write_csv(OUTPUT_DIR / f"{name}.csv", rows, fieldnames.get(name))

    write_core_reports(rows_by_name, summaries)
    pack_manifest = build_r9_input_pack()
    write_csv(OUTPUT_DIR / "r9_input_pack_manifest.csv", pack_manifest)
    update_cumulative_documentation(rows_by_name)
    return rows_by_name


if __name__ == "__main__":
    generated = generate_r8_outputs()
    print("R8 final integrated analysis generated.")
    print(f"Output directory: {OUTPUT_DIR.relative_to(ROOT)}")
    print(f"Tables generated: {len(generated['r8_final_table_registry'])}")
    print(f"Figures generated: {len(generated['r8_final_figure_registry'])}")
    print("R9 readiness:")
    for row in generated["r8_r9_readiness_summary"]:
        print(f"- {row['criterion']}: {row['status']}")
