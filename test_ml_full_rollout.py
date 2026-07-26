from copy import deepcopy

from ml_behavioral_regimes import get_behavioral_regimes, get_continuation_policies
from ml_full_counterfactual_rollout import (
    FullRolloutError,
    evaluate_full_candidate_action,
)
from ml_full_state_snapshot import validate_snapshot_equivalence
from ml_stage15_experiment import make_seer_decision
from ml_stage15_experiment import make_vote_decision, make_wolf_decision


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected}, found {actual}")


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def assert_raises(error_type, func, message):
    try:
        func()
    except error_type:
        return
    raise AssertionError(message)


def sample_seer_decision():
    regime = get_behavioral_regimes()[0]
    rows, snapshots = make_seer_decision(
        seed=42,
        base_game_index=1,
        regime=regime,
        max_candidates=3,
    )
    assert_true(rows, "Expected seer candidate rows.")
    row = rows[0]
    return row, snapshots[row["decision_id"]]


def sample_decision(maker, seed, base_game_index):
    regime = get_behavioral_regimes()[0]
    rows, snapshots = maker(
        seed=seed,
        base_game_index=base_game_index,
        regime=regime,
        max_candidates=3,
    )
    assert_true(rows, "Expected candidate rows.")
    row = rows[0]
    return row, snapshots[row["decision_id"]]


def test_full_rollout_is_reproducible():
    row, snapshot = sample_seer_decision()
    policies = get_continuation_policies()[:1]
    first = evaluate_full_candidate_action(
        snapshot,
        row,
        row["candidate_uid"],
        policies,
        rollouts_per_policy=1,
        rollout_seed=123,
    )
    second = evaluate_full_candidate_action(
        snapshot,
        row,
        row["candidate_uid"],
        policies,
        rollouts_per_policy=1,
        rollout_seed=123,
    )
    assert_equal(first, second, "Full rollout should reproduce exactly.")


def test_full_rollout_does_not_mutate_snapshot():
    row, snapshot = sample_seer_decision()
    before = deepcopy(snapshot)
    evaluate_full_candidate_action(
        snapshot,
        row,
        row["candidate_uid"],
        get_continuation_policies()[:1],
        rollouts_per_policy=1,
        rollout_seed=99,
    )
    assert_equal(snapshot, before, "Full rollout should not mutate snapshot.")
    equivalence = validate_snapshot_equivalence(snapshot)
    assert_true(equivalence["equivalent"], equivalence)


def test_illegal_full_rollout_candidate_is_rejected():
    row, snapshot = sample_seer_decision()
    assert_raises(
        FullRolloutError,
        lambda: evaluate_full_candidate_action(
            snapshot,
            row,
            "missing_candidate",
            get_continuation_policies()[:1],
            rollouts_per_policy=1,
        ),
        "Illegal full-rollout candidate should be rejected.",
    )


def test_supported_full_rollout_action_types_run():
    policies = get_continuation_policies()[:1]
    samples = [
        sample_decision(make_seer_decision, 42, 1),
        sample_decision(make_wolf_decision, 42, 2),
        sample_decision(make_vote_decision, 42, 3),
    ]
    seen_types = set()
    for row, snapshot in samples:
        result = evaluate_full_candidate_action(
            snapshot,
            row,
            row["candidate_uid"],
            policies,
            rollouts_per_policy=1,
            rollout_seed=321,
        )
        seen_types.add(row["decision_type"])
        assert_true(
            result["full_rollout_count"] == 1,
            "Expected one full simulator rollout.",
        )
        assert_true(
            0.0 <= result["full_rollout_mean_team_win_rate"] <= 1.0,
            "Full rollout value should be a probability.",
        )
    assert_true(
        {"seer_check", "wolf_kill", "day_vote"}.issubset(seen_types),
        "Expected all supported action types.",
    )


if __name__ == "__main__":
    test_full_rollout_is_reproducible()
    test_full_rollout_does_not_mutate_snapshot()
    test_illegal_full_rollout_candidate_is_rejected()
    test_supported_full_rollout_action_types_run()
    print("test_ml_full_rollout.py passed")
