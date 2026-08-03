import csv
from pathlib import Path


def main():
    rows = list(csv.DictReader(
        Path("results/metrics_integrity_stage_r62/r62_witch_potion_lifecycle_raw.csv").open()
    ))
    for row in rows:
        if int(row["save_used"]):
            assert int(row["save_available_at_death"]) == 0
            assert int(row["save_available_at_game_end"]) == 0
        if int(row["poison_used"]):
            assert int(row["poison_available_at_death"]) == 0
            assert int(row["poison_available_at_game_end"]) == 0
    print("test_r62_witch_unused_potion.py passed")


if __name__ == "__main__":
    main()
