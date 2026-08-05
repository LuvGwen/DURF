"""Output validation tests for R8.2 targeted independent replication."""

import csv
from pathlib import Path

from r82_targeted_replication import FROZEN_MODULES, R82_MATCHED_SETS_PER_MODULE


RESULTS_DIR = Path("results/targeted_replication_stage_r82")


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_r82_output_files_exist():
    required = [
        "r82_pre_registration.md",
        "r82_schema.md",
        "r82_seed_registry.csv",
        "r82_module_registry.csv",
        "r82_policy_registry.csv",
        "r82_game_level_raw.csv",
        "r82_action_raw.csv.gz",
        "r82_policy_summary.csv",
        "r82_primary_contrasts.csv",
        "r82_replication_decision_summary.csv",
        "r82_validation_summary.csv",
        "r82_research_report.md",
    ]
    missing = [name for name in required if not (RESULTS_DIR / name).exists()]
    assert not missing, missing


def test_r82_game_row_count_and_scope():
    rows = read_csv(RESULTS_DIR / "r82_game_level_raw.csv")
    expected = len(FROZEN_MODULES) * 2 * R82_MATCHED_SETS_PER_MODULE
    assert len(rows) == expected
    assert sorted({row["module"] for row in rows}) == ["seer", "villager", "witch"]
    assert "hunter" not in {row["module"] for row in rows}
    assert "wolf" not in {row["module"] for row in rows}


def test_r82_contrast_scope():
    rows = read_csv(RESULTS_DIR / "r82_primary_contrasts.csv")
    assert len(rows) == len(FROZEN_MODULES) * 2
    primary_rows = [row for row in rows if row["outcome_role"] == "primary"]
    assert len(primary_rows) == len(FROZEN_MODULES)
    assert {row["metric"] for row in primary_rows} == {"actor_payoff"}


def test_r82_validation_passed():
    rows = read_csv(RESULTS_DIR / "r82_validation_summary.csv")
    failed = [row for row in rows if row["passed"] != "True"]
    assert not failed, failed


if __name__ == "__main__":
    test_r82_output_files_exist()
    test_r82_game_row_count_and_scope()
    test_r82_contrast_scope()
    test_r82_validation_passed()
    print("R8.2 output tests passed.")
