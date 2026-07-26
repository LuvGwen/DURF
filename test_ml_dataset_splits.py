from collections import defaultdict

from ml_dataset_generation import generate_ml_decision_rows


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def test_group_split_prevents_game_family_leakage():
    rows, _ = generate_ml_decision_rows(
        seeds=[42, 45, 46],
        games_per_seed=2,
        max_candidates=4,
        decision_limits={
            "seer_check": 20,
            "wolf_kill": 20,
            "day_vote": 30,
        },
        rollout_counts={
            "seer_check": 2,
            "wolf_kill": 2,
            "day_vote": 2,
        },
    )
    group_to_splits = defaultdict(set)
    decision_to_splits = defaultdict(set)
    for row in rows:
        group_to_splits[row["split_group_id"]].add(row["dataset_split"])
        decision_to_splits[row["decision_id"]].add(row["dataset_split"])

    assert_true(rows, "Expected rows from split test generation.")
    assert_true(
        all(len(splits) == 1 for splits in group_to_splits.values()),
        "A split group crossed train/validation/test.",
    )
    assert_true(
        all(len(splits) == 1 for splits in decision_to_splits.values()),
        "A decision state crossed train/validation/test.",
    )
    assert_true(
        {"train", "validation", "test"}.issubset({
            row["dataset_split"] for row in rows
        }),
        "Expected train, validation, and test rows.",
    )


if __name__ == "__main__":
    test_group_split_prevents_game_family_leakage()
    print("test_ml_dataset_splits.py passed")
