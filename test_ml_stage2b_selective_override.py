from tempfile import TemporaryDirectory
from pathlib import Path

from ml_stage2b_selective_override import (
    build_selective_override_manifest,
    evaluate_selective_override,
)


def main():
    rows = [
        {
            "candidate_uid": "a",
            "candidate_player_id": 1,
            "ml_predicted_wolf_value": 0.70,
            "candidate_ranking_margin": 0.08,
            "distribution_shift_category": "in_distribution",
            "missing_feature_count": 0,
            "maximum_absolute_z_score": 1.0,
            "fraction_features_outside_training_minmax": 0.0,
            "feature_vector_novelty_score": 1.5,
            "prediction_extremity": 0.20,
        },
        {
            "candidate_uid": "b",
            "candidate_player_id": 2,
            "ml_predicted_wolf_value": 0.55,
            "candidate_ranking_margin": 0.08,
            "distribution_shift_category": "in_distribution",
            "missing_feature_count": 0,
            "maximum_absolute_z_score": 1.0,
            "fraction_features_outside_training_minmax": 0.0,
            "feature_vector_novelty_score": 1.5,
            "prediction_extremity": 0.05,
        },
    ]
    manifest = {
        "manifest_hash": "unit",
        "rule": {
            "allowed_shift_categories": ["in_distribution"],
            "min_top_two_margin": 0.02,
            "min_ml_advantage_over_existing": 0.05,
            "max_missing_feature_count": 0,
            "max_absolute_z_score": 2.5,
            "max_fraction_outside_training_minmax": 0.0,
            "max_feature_vector_novelty_score": 3.0,
        },
    }
    result = evaluate_selective_override(
        rows,
        existing_row=rows[1],
        ml_row=rows[0],
        manifest=manifest,
    )
    assert result["selective_override_qualified"] is True

    with TemporaryDirectory() as directory:
        path = Path(directory) / "selective.json"
        built = build_selective_override_manifest(
            decision_rows=[
                {
                    "decision_id": "d1",
                    "seed": 200,
                    "existing_rule_target": 2,
                    "frozen_ml_target": 1,
                }
            ],
            prediction_rows=[
                {"decision_id": "d1", **rows[0]},
                {"decision_id": "d1", **rows[1]},
            ],
            development_seeds=[200],
            validation_seeds=[210],
            final_test_seeds=[220],
            output_path=path,
        )
        assert built["development_seeds"] == [200]
        assert built["excluded_final_test_seeds"] == [220]
        assert built["primary_model_retrained"] is False
        assert path.exists()

    print("selective_override_qualification: PASS")
    print("selective_manifest_seed_isolation: PASS")


if __name__ == "__main__":
    main()
