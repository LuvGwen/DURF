import csv
from pathlib import Path


def main():
    path = Path("results/metrics_integrity_stage_r62/r62_seer_survival_summary.csv")
    rows = list(csv.DictReader(path.open()))
    assert rows
    assert all("terminal_survival_rate" in row for row in rows)
    assert all("one_round_post_reveal_survival_rate" in row for row in rows)
    assert all(float(row["terminal_survival_rate"]) == 0.0 for row in rows)
    print("test_r62_seer_survival_definition.py passed")


if __name__ == "__main__":
    main()
