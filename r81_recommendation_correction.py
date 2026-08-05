"""Correct R8 role-strategy recommendation labels for R8.1."""

from __future__ import annotations

from r81_common import (
    CORRECTED_R8_DIR,
    R81_DIR,
    build_conclusion_change_rows,
    build_corrected_role_strategy_rows,
    build_policy_grade_rows,
    copy_corrected_r8_inputs,
    read_csv,
    write_csv,
)


def generate_recommendation_corrections(selection_rows: list[dict[str, object]] | None = None) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    if selection_rows is None:
        selection_rows = read_csv(R81_DIR / "r81_policy_selection_frequency.csv")
    corrected_rows = build_corrected_role_strategy_rows(selection_rows)
    grade_rows = build_policy_grade_rows(corrected_rows, selection_rows)
    conclusion_rows = build_conclusion_change_rows(corrected_rows)
    write_csv(R81_DIR / "r81_corrected_role_strategy_table.csv", corrected_rows)
    write_csv(R81_DIR / "r81_policy_evidence_grade_registry.csv", grade_rows)
    write_csv(R81_DIR / "r81_conclusion_change_registry.csv", conclusion_rows)
    write_csv(CORRECTED_R8_DIR / "corrected_role_strategy_table.csv", corrected_rows)
    copy_corrected_r8_inputs()
    return corrected_rows, grade_rows, conclusion_rows


if __name__ == "__main__":
    corrected, grades, changes = generate_recommendation_corrections()
    print(f"Corrected role-strategy rows: {len(corrected)}")
    print(f"Policy grade rows: {len(grades)}")
    print(f"Conclusion-change rows: {len(changes)}")
