from ml_dataset_generation import generate_reference_game
from ml_decision_logger import (
    extract_decision_rows_from_game,
    validate_decision_rows,
)
from ml_feature_registry import FEATURE_COLUMNS, LABEL_COLUMNS, PROHIBITED_FEATURES


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def test_feature_registry_excludes_labels():
    overlap = set(FEATURE_COLUMNS) & (set(LABEL_COLUMNS) | PROHIBITED_FEATURES)
    assert_true(not overlap, f"Feature leakage columns found: {overlap}")


def test_village_observation_has_no_hidden_role_access():
    game, _, _ = generate_reference_game(42, 1)
    rows = extract_decision_rows_from_game(
        game,
        game_id="unit_ml_safety",
        seed=42,
        base_game_index=1,
        max_candidates=6,
        initial_p_wolf=0.3,
    )
    validation = validate_decision_rows(rows)
    assert_true(validation["valid"], validation["errors"])
    unsafe_rows = [
        row for row in rows
        if (
            row["actor_team"] != "wolf"
            and row["actor_role_if_self_known"] != "seer"
            and int(row["candidate_known_wolf_to_actor"]) != 0
        )
    ]
    assert_true(not unsafe_rows, "Village non-seers learned hidden wolf status.")


def test_seer_private_checks_are_role_private():
    game, _, _ = generate_reference_game(43, 1)
    rows = extract_decision_rows_from_game(
        game,
        game_id="unit_ml_seer_private",
        seed=43,
        base_game_index=1,
        max_candidates=6,
        initial_p_wolf=0.3,
    )
    unsafe_rows = [
        row for row in rows
        if (
            int(row["candidate_checked_by_actor_status"]) != 0
            and row["actor_role_if_self_known"] != "seer"
        )
    ]
    assert_true(not unsafe_rows, "Seer private check status leaked.")


def test_future_events_are_absent_from_feature_columns():
    forbidden_tokens = [
        "future",
        "eventual_winner",
        "true_candidate_role",
        "final_survival",
    ]
    bad_columns = [
        column for column in FEATURE_COLUMNS
        if any(token in column for token in forbidden_tokens)
    ]
    assert_true(not bad_columns, f"Future/label feature columns: {bad_columns}")


if __name__ == "__main__":
    test_feature_registry_excludes_labels()
    test_village_observation_has_no_hidden_role_access()
    test_seer_private_checks_are_role_private()
    test_future_events_are_absent_from_feature_columns()
    print("test_ml_observation_safety.py passed")
