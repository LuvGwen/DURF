from ml_stage15_experiment import evaluate_shadow_policies, run_stage15_experiment


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def test_shadow_policy_outputs_required_fields():
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
    shadow_rows, shadow_summary = evaluate_shadow_policies(result["rows"])
    assert_true(shadow_rows, "Expected shadow decision rows.")
    assert_true(shadow_summary, "Expected shadow policy summary.")
    required_fields = {
        "decision_type",
        "policy",
        "split_name",
        "mean_policy_value",
        "mean_improvement_over_existing",
        "mean_ml_regret",
    }
    missing = required_fields - set(shadow_summary[0])
    assert_true(not missing, f"Missing shadow summary fields: {missing}")


if __name__ == "__main__":
    test_shadow_policy_outputs_required_fields()
    print("test_ml_shadow_policy.py passed")
