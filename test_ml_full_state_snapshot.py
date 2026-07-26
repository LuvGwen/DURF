from ml_behavioral_regimes import get_behavioral_regimes
from ml_full_state_snapshot import (
    capture_full_game_snapshot,
    restore_full_game_snapshot,
    validate_snapshot_equivalence,
)
from ml_stage15_experiment import generate_game_for_regime


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def test_snapshot_restore_reproduces_canonical_state():
    regime = get_behavioral_regimes()[0]
    game, _ = generate_game_for_regime(42, 1, regime)
    snapshot = capture_full_game_snapshot(
        game,
        snapshot_id="unit_snapshot",
        metadata={"test": "snapshot"},
    )
    equivalence = validate_snapshot_equivalence(snapshot)
    assert_true(equivalence["equivalent"], equivalence)


def test_restored_clone_does_not_mutate_original_snapshot():
    regime = get_behavioral_regimes()[0]
    game, _ = generate_game_for_regime(42, 2, regime)
    snapshot = capture_full_game_snapshot(game, snapshot_id="unit_clone")
    clone = restore_full_game_snapshot(snapshot)
    clone.state.players[0].suspicion_score = 1.0
    restored_again = restore_full_game_snapshot(snapshot)
    assert_true(
        restored_again.state.players[0].suspicion_score != 1.0,
        "Mutating a clone changed the saved snapshot.",
    )


if __name__ == "__main__":
    test_snapshot_restore_reproduces_canonical_state()
    test_restored_clone_does_not_mutate_original_snapshot()
    print("test_ml_full_state_snapshot.py passed")
