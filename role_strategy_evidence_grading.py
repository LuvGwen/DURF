"""Evidence grading helpers for R6 role-strategy synthesis."""

from __future__ import annotations

from role_strategy_evidence_registry import EVIDENCE_GRADES, RECOMMENDATION_LABELS


GRADE_ORDER = {"A": 6, "B": 5, "C": 4, "D": 3, "E": 2, "F": 1, "U": 0}


def is_valid_evidence_grade(grade: str) -> bool:
    return grade in EVIDENCE_GRADES


def is_valid_recommendation_label(label: str) -> bool:
    return label in RECOMMENDATION_LABELS


def evidence_grade_rank(grade: str) -> int:
    if grade not in GRADE_ORDER:
        raise ValueError(f"Unknown evidence grade: {grade}")
    return GRADE_ORDER[grade]


def label_for_adjusted_p_value(
    adjusted_p_value: str,
    effect_direction: str,
    harmful_context: bool = False,
) -> str:
    """Return a conservative recommendation label from formal inference fields."""
    try:
        p_value = float(adjusted_p_value)
    except (TypeError, ValueError):
        return "promising but uncertain" if effect_direction == "positive" else "no supported improvement"

    if p_value <= 0.05 and harmful_context:
        return "statistically supported harmful"
    if p_value <= 0.05 and effect_direction == "positive":
        return "recommended under current evidence"
    if effect_direction == "positive":
        return "promising but uncertain"
    return "no supported improvement"
