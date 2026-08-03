"""Claim support audit helpers for R7."""

from __future__ import annotations

from literature_stage_r7_data import CLAIMS, source_by_id


def claim_support_rows() -> list[dict[str, str]]:
    sources = source_by_id()
    rows = []
    for (
        claim_id,
        claim_text,
        project_evidence_source,
        source_ids,
        claim_type,
        support_status,
        overclaim_risk,
        revision_needed,
        final_safe_wording,
    ) in CLAIMS:
        missing_sources = [source_id for source_id in source_ids.split(";") if source_id not in sources]
        rows.append(
            {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "project_evidence_source": project_evidence_source,
                "literature_source": source_ids,
                "claim_type": claim_type,
                "support_status": support_status,
                "overclaim_risk": overclaim_risk,
                "revision_needed": revision_needed if not missing_sources else "Fix missing source IDs.",
                "final_safe_wording": final_safe_wording,
            }
        )
    return rows


if __name__ == "__main__":
    for row in claim_support_rows():
        print(row)
