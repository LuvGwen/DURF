from ml_feature_registry import PROHIBITED_FEATURES
from ml_stage2b_experiment import (
    FINAL_TEST_SEEDS,
    verify_frozen_stage2a_model,
    seed_registry_rows,
)
from ml_wolf_kill_model_freeze import live_feature_columns


def main():
    validation = verify_frozen_stage2a_model()
    assert validation["valid"] is True
    features = live_feature_columns()
    assert not (set(features) & set(PROHIBITED_FEATURES))
    seed_rows = seed_registry_rows()
    final_rows = [
        row for row in seed_rows
        if int(row["seed"]) in FINAL_TEST_SEEDS
    ]
    assert final_rows
    assert all(
        row["allowed_for_threshold_selection"] == "False"
        for row in final_rows
    )
    assert all(
        row["allowed_for_model_training"] == "False"
        for row in seed_rows
    )
    print("frozen_model_hash_unchanged: PASS")
    print("live_features_observation_safe: PASS")
    print("stage2b_final_seed_isolation: PASS")


if __name__ == "__main__":
    main()
