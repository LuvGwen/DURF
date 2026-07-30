from r61_matched_design import (
    DEVELOPMENT_SEEDS,
    FINAL_SEEDS,
    OOD_STRESS_SEEDS,
    VALIDATION_SEEDS,
    validate_seed_isolation,
)


def main():
    assert validate_seed_isolation()
    assert not set(FINAL_SEEDS) & set(DEVELOPMENT_SEEDS + VALIDATION_SEEDS)
    assert not set(OOD_STRESS_SEEDS) & set(DEVELOPMENT_SEEDS + VALIDATION_SEEDS)
    print("test_r61_seed_isolation.py passed")


if __name__ == "__main__":
    main()
