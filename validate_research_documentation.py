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

PROPOSAL_STATUSES = {
    "completed",
    "completed_by_alternative_implementation",
    "completed_and_extended",
    "partially_completed",
    "not_started",
    "requires_formal_analysis",
    "requires_documentation",
    "no_longer_scientifically_justified",
}

TRACE_STATUSES = {
    "verified_from_source",
    "verified_from_multiple_sources",
    "reported_in_handoff_only",
    "source_not_found",
    "inconsistent_sources",
    "requires_manual_review",
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
        row["status"] != "completed"
        for row in bow_decision_rows
    )
    add_result(
        summary,
        "proposal_bow_r2_completed_but_decision_integration_deferred",
        bow_artifacts_exist and bow_decision_not_complete,
        ",".join(
            row["proposal_component"] + "=" + row["status"]
            for row in bow_rows
        ),
    )

    financial_rows = [row for row in proposal_rows if row["proposal_component"] in {"Risk-adjusted return", "Sharpe-ratio analogue", "Payoff variance", "Risk cost"}]
    financial_not_false_complete = all(row["status"] != "completed" for row in financial_rows)
    add_result(summary, "proposal_financial_metrics_not_falsely_completed", financial_not_false_complete, ",".join(row["proposal_component"] + "=" + row["status"] for row in financial_rows))

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
