"""Recommendation card generation helpers for R6."""

from __future__ import annotations

from role_strategy_synthesis import (
    build_decision_matrix,
    build_default_registry,
    build_remaining_gaps,
    build_role_card,
    load_evidence,
)


def get_role_strategy_card(role: str) -> str:
    evidence = load_evidence()
    matrix = build_decision_matrix(evidence)
    gaps = build_remaining_gaps()
    defaults = build_default_registry(matrix)
    return build_role_card(role, matrix, gaps, defaults)
