from pathlib import Path
from tempfile import TemporaryDirectory

from ml_distribution_shift import calculate_distribution_shift
from ml_wolf_kill_model_freeze import create_frozen_wolf_kill_model


def main():
    with TemporaryDirectory() as directory:
        manifest = create_frozen_wolf_kill_model(
            output_path=Path(directory) / "manifest.json",
            created_at_utc="2026-07-26T00:00:00+00:00",
        )
        feature_row = {
            feature: mean
            for feature, mean in zip(
                manifest["feature_order"],
                manifest["standardization_means"],
            )
        }
        shift_one = calculate_distribution_shift(
            manifest,
            feature_row,
            prediction=0.51,
            margin=0.05,
        )
        shift_two = calculate_distribution_shift(
            manifest,
            feature_row,
            prediction=0.51,
            margin=0.05,
        )
        assert shift_one == shift_two
        assert shift_one["missing_feature_count"] == 0
        assert shift_one["distribution_shift_category"] == "in_distribution"

        extreme_row = {feature: 999.0 for feature in manifest["feature_order"]}
        extreme_shift = calculate_distribution_shift(
            manifest,
            extreme_row,
            prediction=0.99,
            margin=0.0,
        )
        assert extreme_shift["distribution_shift_category"] == "strong_shift"
        assert extreme_shift["maximum_absolute_z_score"] > 3.0

    print("distribution_shift_metrics_deterministic: PASS")
    print("in_distribution_category: PASS")
    print("strong_shift_category: PASS")


if __name__ == "__main__":
    main()
