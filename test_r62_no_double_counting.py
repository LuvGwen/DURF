import csv
from pathlib import Path


def main():
    rows = list(csv.DictReader(
        Path("results/metrics_integrity_stage_r62/r62_validation_summary.csv").open()
    ))
    checks = {row["check"]: row for row in rows}
    assert checks["wrong_poison_not_double_counted"]["passed"] == "True"
    print("test_r62_no_double_counting.py passed")


if __name__ == "__main__":
    main()
