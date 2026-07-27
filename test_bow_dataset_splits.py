from collections import defaultdict

from bow_dataset_generation import (
    get_r2_behavioral_regimes,
    get_split_plan,
    validate_dataset,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def test_split_plan_has_required_splits():
    splits = {row["dataset_split"] for row in get_split_plan()}
    check(
        {"train", "validation", "final_test", "ood_template", "ood_regime"}
        .issubset(splits),
        "split plan contains all required split categories",
    )


def test_ood_regime_is_not_in_primary_regimes():
    regimes = get_r2_behavioral_regimes()
    ood_plan = [
        row for row in get_split_plan()
        if row["dataset_split"] == "ood_regime"
    ][0]
    train_regimes = set()
    for row in get_split_plan():
        if row["dataset_split"] == "train":
            train_regimes.update(row["regime_ids"])
    check(
        all(regime_id in regimes for regime_id in ood_plan["regime_ids"]),
        "OOD regime ids exist",
    )
    check(
        not (set(ood_plan["regime_ids"]) & train_regimes),
        "OOD regimes are excluded from train",
    )


def test_validation_catches_split_crossing():
    rows = [
        {
            "dataset_split": "train",
            "game_id": "g1",
            "game_family_id": "fam1",
            "base_configuration_id": "base_train",
            "seed": 1,
            "behavioral_regime": "r",
            "template_family": "family_a",
            "hidden_information_leakage_flag": "False",
        },
        {
            "dataset_split": "ood_template",
            "game_id": "g2",
            "game_family_id": "fam2",
            "base_configuration_id": "base_ood",
            "seed": 2,
            "behavioral_regime": "r",
            "template_family": "family_b",
            "hidden_information_leakage_flag": "False",
        },
    ]
    summary = validate_dataset(rows, rows, {"vocabulary_size": 5})
    by_metric = {row["metric"]: row for row in summary}
    check(
        by_metric["ood_template_overlap_with_train"]["status"] == "PASS",
        "held-out template families do not overlap train",
    )


if __name__ == "__main__":
    test_split_plan_has_required_splits()
    test_ood_regime_is_not_in_primary_regimes()
    test_validation_catches_split_crossing()
    print("test_bow_dataset_splits.py passed")
