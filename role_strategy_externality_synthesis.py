"""Cross-role externality synthesis helpers for R6."""

from __future__ import annotations

from role_strategy_synthesis import build_externality_matrix, load_evidence


def get_cross_role_externality_matrix() -> list[dict[str, object]]:
    return build_externality_matrix(load_evidence())


def summarize_externalities_by_owner() -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in get_cross_role_externality_matrix():
        owner = str(row["strategy_owner_role"])
        counts[owner] = counts.get(owner, 0) + 1
    return counts
