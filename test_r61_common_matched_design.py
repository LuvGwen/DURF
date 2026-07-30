from r61_matched_design import (
    BEHAVIORAL_REGIMES,
    FINAL_SEEDS,
    generate_r61_matched_sets,
    validate_seed_isolation,
)


def main():
    rows = generate_r61_matched_sets()
    assert len(rows) == len(FINAL_SEEDS) * len(BEHAVIORAL_REGIMES) * 5
    assert len({row["matched_set_id"] for row in rows}) == len(rows)
    assert validate_seed_isolation()
    print("test_r61_common_matched_design.py passed")


if __name__ == "__main__":
    main()
