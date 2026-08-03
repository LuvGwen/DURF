import csv
from pathlib import Path


def main():
    rows = list(csv.DictReader(
        Path("results/metrics_integrity_stage_r62/r62_witch_payoff_reconciliation.csv").open()
    ))
    assert rows
    assert all(row["duplicate_penalty_flag"] == "0" for row in rows)
    poison_villager = [
        row for row in rows if row["payoff_component"] == "poison_villager"
    ]
    assert all(float(row["payoff_value"]) == -0.5 for row in poison_villager)
    print("test_r62_witch_payoff_reconciliation.py passed")


if __name__ == "__main__":
    main()
