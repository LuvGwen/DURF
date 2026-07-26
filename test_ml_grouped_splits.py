from ml_grouped_splits import assign_grouped_split, validate_grouped_splits


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected}, found {actual}")


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def test_grouped_split_assignments_are_valid():
    rows = []
    for seed in [42, 50, 52]:
        row = {
            "seed": seed,
            "base_game_index": 1,
            "behavioral_regime_id": "baseline_rule_policy",
        }
        rows.append(assign_grouped_split(row))

    validation = validate_grouped_splits(rows)
    assert_true(validation["valid"], validation["errors"])
    assert_true(
        {"train", "validation", "final_test"}.issubset({
            row["split_name"] for row in rows
        }),
        "Expected train, validation, and final_test split rows.",
    )


def test_ood_regime_uses_level_c_split():
    row = assign_grouped_split({
        "seed": 42,
        "base_game_index": 1,
        "behavioral_regime_id": "deception_enabled_policy",
    })
    assert_equal(row["split_name"], "ood_test", "OOD split name mismatch.")
    assert_equal(
        row["split_level"],
        "C_out_of_distribution",
        "OOD split level mismatch.",
    )


def test_cross_split_group_is_rejected():
    rows = [
        {
            "split_group_id": "same",
            "game_family_id": "same",
            "base_configuration_id": "same",
            "split_name": "train",
        },
        {
            "split_group_id": "same",
            "game_family_id": "same",
            "base_configuration_id": "same",
            "split_name": "final_test",
        },
    ]
    validation = validate_grouped_splits(rows)
    assert_true(not validation["valid"], "Cross-split group should fail.")


if __name__ == "__main__":
    test_grouped_split_assignments_are_valid()
    test_ood_regime_uses_level_c_split()
    test_cross_split_group_is_rejected()
    print("test_ml_grouped_splits.py passed")
