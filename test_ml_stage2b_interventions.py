from ml_stage2b_interventions import STAGE2B_WOLF_KILL_POLICIES
from ml_stage2b_live_experiment import (
    get_stage2a_behavioral_regimes,
    run_stage2b_live_experiment,
)


def intervention_count(game_rows, policy_name):
    row = [row for row in game_rows if row["policy_name"] == policy_name][0]
    return int(row["total_ml_interventions"]), int(row["wolf_kill_decisions"])


def main():
    assert "ml_first_kill_only" in STAGE2B_WOLF_KILL_POLICIES
    assert "selective_ml_override" in STAGE2B_WOLF_KILL_POLICIES
    output = run_stage2b_live_experiment(
        seeds=[220],
        split="unit",
        base_configs_per_seed=1,
        policies=[
            "existing_rule",
            "ml_first_kill_only",
            "ml_first_two_kills",
            "continuous_frozen_ml",
        ],
        regimes=get_stage2a_behavioral_regimes()[:1],
        max_rounds=20,
        write_outputs=False,
    )
    existing_interventions, existing_decisions = intervention_count(
        output["game_rows"],
        "existing_rule",
    )
    first_interventions, first_decisions = intervention_count(
        output["game_rows"],
        "ml_first_kill_only",
    )
    two_interventions, two_decisions = intervention_count(
        output["game_rows"],
        "ml_first_two_kills",
    )
    continuous_interventions, continuous_decisions = intervention_count(
        output["game_rows"],
        "continuous_frozen_ml",
    )
    assert existing_interventions == 0
    assert first_interventions == min(1, first_decisions)
    assert two_interventions == min(2, two_decisions)
    assert continuous_interventions == continuous_decisions
    print("stage2b_policy_names_available: PASS")
    print("existing_rule_no_ml_interventions: PASS")
    print("one_two_continuous_intervention_counts: PASS")


if __name__ == "__main__":
    main()
