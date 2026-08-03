"""Finding-to-literature mapping helpers for R7."""

from __future__ import annotations

from literature_stage_r7_data import PROJECT_FINDINGS, source_by_id


def finding_mapping_rows() -> list[dict[str, str]]:
    sources = source_by_id()
    rows = []
    for (
        finding_id,
        chapter,
        finding,
        effect,
        grade,
        source_ids,
        relationship,
        explanation,
    ) in PROJECT_FINDINGS:
        for source_id in source_ids.split(";"):
            source = sources[source_id]
            rows.append(
                {
                    "finding_id": finding_id,
                    "project_chapter": chapter,
                    "project_finding": finding,
                    "project_effect_or_result": effect,
                    "evidence_grade": grade,
                    "literature_domain": source["domain"],
                    "source_id": source_id,
                    "literature_claim": source["exact_claim_supported"],
                    "relationship": relationship,
                    "theoretical_explanation": explanation,
                    "disagreement_explanation": ""
                    if relationship != "contradicts_some_literature"
                    else "See contradiction registry.",
                    "project_extension": "DURF tests the idea in a controlled 10-player hidden-role simulator.",
                    "limitation": source["limitations"],
                    "citation_ready_sentence": f"{finding} This is {relationship.replace('_', ' ')} relative to {source['authors'].split(';')[0]} ({source['year']}).",
                    "source_report": "results/literature_synthesis_stage_r7/r7_project_finding_comparison_report.md",
                }
            )
    return rows


def unmapped_findings() -> list[str]:
    mapped = {row["finding_id"] for row in finding_mapping_rows()}
    return [finding[0] for finding in PROJECT_FINDINGS if finding[0] not in mapped]


if __name__ == "__main__":
    print(f"Finding-literature rows: {len(finding_mapping_rows())}")
    print(f"Unmapped findings: {unmapped_findings()}")
