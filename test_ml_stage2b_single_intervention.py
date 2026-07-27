from ml_stage2b_live_experiment import (
    get_stage2a_behavioral_regimes,
    run_stage2b_live_experiment,
)
from ml_stage2b_single_intervention import run_single_intervention_rollouts


def main():
    output = run_stage2b_live_experiment(
        seeds=[220],
        split="unit",
        base_configs_per_seed=1,
        policies=["existing_with_ml_shadow"],
        regimes=get_stage2a_behavioral_regimes()[:1],
        max_rounds=20,
        capture_snapshots=True,
        write_outputs=False,
    )
    assert output["decision_rows"]
    decision = dict(output["decision_rows"][0])
    candidates = [
        row for row in output["prediction_rows"]
        if row["decision_id"] == decision["decision_id"]
    ]
    alternative = next(
        row for row in candidates
        if str(row["candidate_uid"])
        != str(decision["existing_rule_target_actor_uid"])
    )
    decision["ml_existing_agree"] = 0
    decision["frozen_ml_target_actor_uid"] = alternative["candidate_uid"]
    decision["frozen_ml_target"] = alternative["candidate_player_id"]
    rows = run_single_intervention_rollouts(
        [decision],
        output["snapshots_by_decision_id"],
        max_decisions=1,
        rollouts_per_branch=1,
        rollout_seed=999,
        max_rounds=20,
    )
    assert len(rows) == 2
    assert {
        row["branch_policy"] for row in rows
    } == {"existing_rule_forced_once", "frozen_ml_forced_once"}
    print("single_intervention_branches_share_snapshot: PASS")
    print("single_intervention_rollouts_complete: PASS")


if __name__ == "__main__":
    main()
