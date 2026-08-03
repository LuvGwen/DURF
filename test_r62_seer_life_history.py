import csv
from pathlib import Path


def main():
    rows = list(csv.DictReader(
        Path("results/metrics_integrity_stage_r62/r62_seer_life_history_raw.csv").open()
    ))
    assert len(rows) == 1200
    assert all(row["reconstructable"] == "True" for row in rows)
    assert all(row["player_uid"] for row in rows)
    print("test_r62_seer_life_history.py passed")


if __name__ == "__main__":
    main()
