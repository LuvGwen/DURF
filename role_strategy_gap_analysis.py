"""Remaining evidence gap helpers for R6."""

from __future__ import annotations

from role_strategy_synthesis import build_remaining_gaps, build_targeted_priorities


def get_remaining_evidence_gaps() -> list[dict[str, object]]:
    return build_remaining_gaps()


def get_targeted_experiment_priorities() -> list[dict[str, object]]:
    return build_targeted_priorities(build_remaining_gaps())


def critical_gap_roles() -> set[str]:
    return {
        str(row["role"])
        for row in get_remaining_evidence_gaps()
        if row["priority"] == "critical"
    }
