import csv
from pathlib import Path


def main():
    rows = list(csv.DictReader(
        Path("results/metrics_integrity_stage_r62/r62_seer_post_reveal_hazard_summary.csv").open()
    ))
    assert rows
    for row in rows:
        hazard = float(row["night_kill_hazard_after_reveal"])
        assert 0.0 <= hazard <= 1.0
        assert "eligible_post_reveal_nights" in row
    print("test_r62_seer_post_reveal_hazard.py passed")


if __name__ == "__main__":
    main()
