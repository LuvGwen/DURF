from ml_stage2b_distribution_shift import (
    classify_margin_band,
    intervention_count_band,
    summarize_distribution_shift,
)


def main():
    assert classify_margin_band(0.001) == "very_low_margin"
    assert classify_margin_band(0.02) == "low_margin"
    assert classify_margin_band(0.04) == "medium_margin"
    assert classify_margin_band(0.10) == "high_margin"
    assert intervention_count_band(0) == "0_interventions"
    assert intervention_count_band(1) == "1_intervention"
    assert intervention_count_band(2) == "2_interventions"
    assert intervention_count_band(3) == "3_plus_interventions"
    summary = summarize_distribution_shift([
        {
            "policy_name": "continuous_frozen_ml",
            "distribution_shift_category": "strong_shift",
            "wolf_win": 1,
            "top_two_predicted_value_margin": 0.02,
            "ml_advantage_over_existing": 0.01,
            "prior_ml_interventions": 2,
            "cumulative_ml_interventions": 3,
        }
    ])
    assert summary[0]["rows"] == 1
    assert summary[0]["avg_strong_shift_flag"] == 1.0
    print("distribution_shift_bands: PASS")
    print("distribution_shift_summary: PASS")


if __name__ == "__main__":
    main()
