from pathlib import Path
from tempfile import TemporaryDirectory

from ml_wolf_kill_model_freeze import (
    LIVE_FINAL_TEST_SEEDS,
    TRAINING_SEEDS,
    VALIDATION_SEEDS,
    create_frozen_wolf_kill_model,
    validate_frozen_model_manifest,
)


def main():
    with TemporaryDirectory() as directory:
        path_one = Path(directory) / "manifest_one.json"
        path_two = Path(directory) / "manifest_two.json"
        timestamp = "2026-07-26T00:00:00+00:00"
        manifest_one = create_frozen_wolf_kill_model(
            output_path=path_one,
            created_at_utc=timestamp,
        )
        manifest_two = create_frozen_wolf_kill_model(
            output_path=path_two,
            created_at_utc=timestamp,
        )
        validation = validate_frozen_model_manifest(path_one)

        assert manifest_one["manifest_hash"] == manifest_two["manifest_hash"]
        assert validation["valid"] is True
        assert len(manifest_one["coefficients"]) == len(
            manifest_one["feature_order"]
        )
        assert len(manifest_one["standardization_means"]) == len(
            manifest_one["feature_order"]
        )
        assert len(manifest_one["standardization_scales"]) == len(
            manifest_one["feature_order"]
        )
        assert not (
            set(LIVE_FINAL_TEST_SEEDS)
            & set(TRAINING_SEEDS + VALIDATION_SEEDS)
        )

    print("manifest_hash_stable: PASS")
    print("model_coefficients_match_manifest: PASS")
    print("preprocessing_statistics_match_manifest: PASS")
    print("final_test_seed_isolation: PASS")


if __name__ == "__main__":
    main()
