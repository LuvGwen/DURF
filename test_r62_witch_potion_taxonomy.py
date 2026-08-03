import csv
from pathlib import Path


VALID_SAVE = {"", "save_regular_villager", "save_special_role", "save_wolf", "unnecessary_save", "invalid_save_attempt"}
VALID_POISON = {"", "correct_poison_wolf", "poison_regular_villager", "poison_special_role", "invalid_poison_attempt"}


def main():
    rows = list(csv.DictReader(
        Path("results/metrics_integrity_stage_r62/r62_witch_potion_lifecycle_raw.csv").open()
    ))
    assert len(rows) == 1200
    assert all(row["save_event_category"] in VALID_SAVE for row in rows)
    assert all(row["poison_event_category"] in VALID_POISON for row in rows)
    print("test_r62_witch_potion_taxonomy.py passed")


if __name__ == "__main__":
    main()
