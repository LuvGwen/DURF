from copy import deepcopy

from ml_counterfactual_rollout import (
    RolloutError,
    evaluate_candidate_action,
)
from ml_dataset_generation import generate_reference_game
from ml_decision_logger import extract_decision_rows_from_game


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


def sample_row():
    game, _, _ = generate_reference_game(42, 2)
    rows = extract_decision_rows_from_game(
        game,
        game_id="unit_ml_rollout",
        seed=42,
        base_game_index=2,
        max_candidates=6,
        initial_p_wolf=0.3,
    )
    assert_true(rows, "Expected at least one decision row.")
    return rows[0]


def test_rollout_is_reproducible():
    row = sample_row()
    first = evaluate_candidate_action(
        row,
        row["candidate_uid"],
        rollout_count=7,
        rollout_seed=123,
    )
    second = evaluate_candidate_action(
        row,
        row["candidate_uid"],
        rollout_count=7,
        rollout_seed=123,
    )
    assert_equal(first, second, "Same rollout request should reproduce.")


def test_rollout_does_not_modify_snapshot():
    row = sample_row()
    before = deepcopy(row)
    evaluate_candidate_action(
        row,
        row["candidate_uid"],
        rollout_count=5,
        rollout_seed=99,
    )
    assert_equal(row, before, "Rollout should not mutate input row.")


def test_illegal_candidate_is_rejected():
    row = sample_row()
    illegal = dict(row)
    illegal["action_legal"] = 0
    assert_raises(
        RolloutError,
        lambda: evaluate_candidate_action(
            illegal,
            illegal["candidate_uid"],
            rollout_count=3,
        ),
        "Illegal candidate should raise RolloutError.",
    )


def test_forced_candidate_must_match_snapshot():
    row = sample_row()
    assert_raises(
        RolloutError,
        lambda: evaluate_candidate_action(
            row,
            "not_the_candidate",
            rollout_count=3,
        ),
        "Mismatched candidate should raise RolloutError.",
    )


if __name__ == "__main__":
    test_rollout_is_reproducible()
    test_rollout_does_not_modify_snapshot()
    test_illegal_candidate_is_rejected()
    test_forced_candidate_must_match_snapshot()
    print("test_ml_rollout.py passed")
