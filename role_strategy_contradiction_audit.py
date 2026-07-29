"""Cross-stage contradiction audit helpers for R6."""

from __future__ import annotations

from role_strategy_synthesis import build_contradiction_audit, load_evidence


def get_cross_stage_contradictions() -> list[dict[str, object]]:
    return build_contradiction_audit(load_evidence())


def get_priority_sources() -> dict[str, str]:
    return {
        str(row["contradiction_id"]): str(row["which_result_has_priority"])
        for row in get_cross_stage_contradictions()
    }
