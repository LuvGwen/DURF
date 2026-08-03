import csv
from pathlib import Path


def main():
    rows = list(csv.DictReader(
        Path("results/metrics_integrity_stage_r62/r62_witch_potion_lifecycle_raw.csv").open()
    ))
    for row in rows:
        assert int(row["primary_save_waste"]) in {0, 1}
        assert int(row["primary_poison_waste"]) in {0, 1}
        assert int(row["total_primary_potion_waste_count"]) == (
            int(row["primary_save_waste"]) + int(row["primary_poison_waste"])
        )
    print("test_r62_witch_waste_nonoverlap.py passed")


if __name__ == "__main__":
    main()
