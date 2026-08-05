"""R8 proposal-completion synthesis."""

from __future__ import annotations

from r8_common import read_csv


PROPOSAL_COMPLETION_COLUMNS = [
    "proposal_component",
    "original_proposal_description",
    "r8_final_status",
    "evidence",
    "source_file",
    "quality_of_completion",
    "remaining_work",
    "required_next_stage",
    "blocking_final_report",
]

R8_STATUS_OVERRIDES = {
    "BoW integration into decisions": {
        "r8_final_status": "completed_with_negative_findings",
        "evidence": "R3 implemented guarded live BoW integration and found harmful or non-useful live effects.",
        "source_file": "results/bow_integration_stage_r3/r3_research_report.md",
        "quality_of_completion": "High with limitations",
        "remaining_work": "Do not use as final live policy without a new validated design.",
        "required_next_stage": "None before R9",
        "blocking_final_report": "No",
    },
    "Payoff variance": {
        "r8_final_status": "completed",
        "evidence": "R5 computes stdev, variance, downside deviation, VaR-like, and CVaR-like metrics by role and strategy.",
        "source_file": "results/financial_risk_stage_r5/r5_role_expected_payoff_summary.csv",
        "quality_of_completion": "High",
        "remaining_work": "None before R9.",
        "required_next_stage": "None before R9",
        "blocking_final_report": "No",
    },
    "Risk-adjusted return": {
        "r8_final_status": "completed",
        "evidence": "R5 computes Sharpe-like and Sortino-like ratios with validation.",
        "source_file": "results/financial_risk_stage_r5/r5_role_sharpe_like_summary.csv; results/financial_risk_stage_r5/r5_role_sortino_like_summary.csv",
        "quality_of_completion": "High",
        "remaining_work": "None before R9.",
        "required_next_stage": "None before R9",
        "blocking_final_report": "No",
    },
    "Sharpe-ratio analogue": {
        "r8_final_status": "completed",
        "evidence": "R5 defines and validates Sharpe-like denominator and benchmark.",
        "source_file": "results/financial_risk_stage_r5/r5_metric_validation_summary.csv",
        "quality_of_completion": "High",
        "remaining_work": "None before R9.",
        "required_next_stage": "None before R9",
        "blocking_final_report": "No",
    },
    "Final written report": {
        "r8_final_status": "ready_for_R9",
        "evidence": "R8 final integrated research report and R9 input pack generated.",
        "source_file": "results/final_integrated_analysis_stage_r8/r8_research_report.md",
        "quality_of_completion": "Ready for final drafting",
        "remaining_work": "Write final DURF report in R9.",
        "required_next_stage": "R9",
        "blocking_final_report": "No",
    },
}


def build_proposal_completion_matrix() -> list[dict[str, str]]:
    source_rows = read_csv("results/research_progress/durf_proposal_alignment_matrix.csv")
    rows = []
    for row in source_rows:
        override = R8_STATUS_OVERRIDES.get(row["proposal_component"], {})
        status = row.get("status", "not_reported")
        rows.append(
            {
                "proposal_component": row["proposal_component"],
                "original_proposal_description": row["original_proposal_description"],
                "r8_final_status": override.get("r8_final_status", status),
                "evidence": override.get("evidence", row["evidence"]),
                "source_file": override.get("source_file", row["source_file"]),
                "quality_of_completion": override.get("quality_of_completion", row["quality_of_completion"]),
                "remaining_work": override.get("remaining_work", row["remaining_work"]),
                "required_next_stage": override.get("required_next_stage", row["required_next_stage"]),
                "blocking_final_report": override.get("blocking_final_report", row["blocking_final_report"]),
            }
        )
    rows.append(
        {
            "proposal_component": "Final integrated evidence synthesis",
            "original_proposal_description": "Consolidate experiment evidence, statistical results, literature support, and final-report readiness.",
            "r8_final_status": "completed",
            "evidence": "R8 final integrated analysis tables and reports generated.",
            "source_file": "results/final_integrated_analysis_stage_r8/r8_research_report.md",
            "quality_of_completion": "High",
            "remaining_work": "Write final R9 report and presentation package.",
            "required_next_stage": "R9",
            "blocking_final_report": "No",
        }
    )
    return rows


def summarize_proposal_completion(rows: list[dict[str, str]]) -> dict[str, str]:
    completed = sum(1 for row in rows if "completed" in row["r8_final_status"])
    pending = sum(1 for row in rows if "pending" in row["r8_final_status"] or row["blocking_final_report"] == "Yes")
    return {
        "proposal_components_total": str(len(rows)),
        "proposal_components_completed_or_extended": str(completed),
        "proposal_components_pending": str(pending),
        "final_report_blockers": str(sum(1 for row in rows if row["blocking_final_report"] == "Yes")),
    }
