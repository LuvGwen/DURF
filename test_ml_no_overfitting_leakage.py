import json

from ml_feature_registry import FEATURE_COLUMNS, LABEL_COLUMNS, PROHIBITED_FEATURES
from ml_stage15_experiment import MODEL_SELECTION_PATH, run_stage15_experiment


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def test_stage15_features_exclude_labels_and_future_fields():
    overlap = set(FEATURE_COLUMNS) & (set(LABEL_COLUMNS) | PROHIBITED_FEATURES)
    assert_true(not overlap, f"Feature leakage columns found: {overlap}")
    forbidden_tokens = [
        "eventual_winner",
        "true_candidate_role",
        "full_rollout",
        "future",
    ]
    bad_columns = [
        column for column in FEATURE_COLUMNS
        if any(token in column for token in forbidden_tokens)
    ]
    assert_true(not bad_columns, f"Future/label feature columns: {bad_columns}")


def test_tiny_stage15_uses_validation_for_model_selection():
    result = run_stage15_experiment(
        seeds=[42, 50, 52],
        games_per_regime_seed=1,
        max_candidates=2,
        decision_limits={
            "seer_check": 3,
            "wolf_kill": 3,
            "day_vote": 3,
        },
        rollouts_per_policy=1,
        bootstrap_resamples=20,
    )
    assert_true(result["metadata"]["candidate_rows"] > 0, "Expected rows.")
    assert_true(
        result["snapshot_audit"]["passed"] == result["snapshot_audit"]["total"],
        "Snapshot equivalence audit failed.",
    )
    with MODEL_SELECTION_PATH.open() as file:
        manifest = json.load(file)
    assert_true(
        "validation only" in manifest["selection_rule"],
        "Model selection should be validation-only.",
    )
    assert_true(
        "final_test" in {row["split_name"] for row in result["rows"]},
        "Expected final_test rows in tiny Stage 1.5 run.",
    )


if __name__ == "__main__":
    test_stage15_features_exclude_labels_and_future_fields()
    test_tiny_stage15_uses_validation_for_model_selection()
    print("test_ml_no_overfitting_leakage.py passed")
