import csv
from pathlib import Path


def main():
    rows = list(csv.DictReader(
        Path("results/metrics_integrity_stage_r62/r62_seer_life_history_raw.csv").open()
    ))
    assert all(row["player_uid"].isdigit() for row in rows)
    assert all(row["game_id"].startswith("seer_") for row in rows)
    assert len({(row["game_id"], row["player_uid"]) for row in rows}) == len(rows)
    print("test_r62_seer_identifier_linkage.py passed")


if __name__ == "__main__":
    main()
