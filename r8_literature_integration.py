"""R8 DOI-backed literature integration."""

from __future__ import annotations

from collections import defaultdict

from r8_common import read_csv


LITERATURE_COLUMNS = [
    "project_finding_id",
    "project_chapter",
    "project_finding",
    "eligible_source_count",
    "doi_verified_source_count",
    "recent_source_count",
    "foundational_source_count",
    "source_ids",
    "dois",
    "literature_relationships",
    "safe_final_wording",
    "coverage_status",
    "source_data",
]


def build_final_literature_integration_table() -> list[dict[str, str]]:
    rows = read_csv("results/literature_doi_recency_audit_stage_r71/r71_revised_finding_literature_matrix.csv")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("final_citation_eligible") == "True" and row.get("doi_verified") == "True":
            grouped[row["finding_id"]].append(row)

    output = []
    for finding_id, items in sorted(grouped.items()):
        first = items[0]
        output.append(
            {
                "project_finding_id": finding_id,
                "project_chapter": first["project_chapter"],
                "project_finding": first["project_finding"],
                "eligible_source_count": str(len(items)),
                "doi_verified_source_count": str(sum(1 for item in items if item["doi_verified"] == "True")),
                "recent_source_count": str(sum(1 for item in items if item["recent_source"] == "True")),
                "foundational_source_count": str(sum(1 for item in items if item["foundational_source"] == "True")),
                "source_ids": ";".join(sorted({item["literature_source_id"] for item in items})),
                "dois": ";".join(sorted({item["doi"] for item in items})),
                "literature_relationships": ";".join(sorted({item["relationship"] for item in items})),
                "safe_final_wording": first["safe_final_wording"],
                "coverage_status": first["coverage_status"],
                "source_data": "results/literature_doi_recency_audit_stage_r71/r71_revised_finding_literature_matrix.csv",
            }
        )
    return output


def summarize_literature_coverage() -> dict[str, str]:
    bibliography = read_csv("results/literature_doi_recency_audit_stage_r71/r71_doi_validation_registry.csv")
    matrix = read_csv("results/literature_doi_recency_audit_stage_r71/r71_revised_finding_literature_matrix.csv")
    domains = read_csv("results/literature_doi_recency_audit_stage_r71/r71_domain_recency_coverage.csv")
    doi_verified = [row for row in bibliography if row.get("final_doi_status") == "verified"]
    return {
        "final_doi_backed_sources": str(len(doi_verified)),
        "finding_literature_mappings": str(len(matrix)),
        "domain_count": str(len(domains)),
        "domain_labels": ";".join(row["domain_label"] for row in domains),
        "source_data": "results/literature_doi_recency_audit_stage_r71/*.csv",
    }
