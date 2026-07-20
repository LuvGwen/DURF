import json
import random

from game_level_logging import get_seer_check_events
from player import Player
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH
from seer_action import choose_seer_check_target
from seat_order_symmetry_experiment import (
    MIRROR_MAPPING,
    NORMAL_MAPPING,
    SEAT_ORDER_STRATEGIES,
    build_symmetry_row,
    create_displayed_players,
    describe_physical_direction,
    generate_physical_role_assignment,
    get_orientation_specs,
    mirror_seat,
    run_seat_order_symmetry_experiment,
    run_single_orientation_game,
    stable_seed,
    validate_symmetry_rows,
)


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected}, found {actual}")


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def test_mirror_is_involutive():
    for seat in range(1, 11):
        assert_equal(
            mirror_seat(mirror_seat(seat)),
            seat,
            "mirror(mirror(seat)) should return seat",
        )


def test_role_identity_preserved_under_mirror():
    roles_by_physical = generate_physical_role_assignment(42, 1)
    normal_players = create_displayed_players(
        roles_by_physical,
        NORMAL_MAPPING,
    )
    mirrored_players = create_displayed_players(
        roles_by_physical,
        MIRROR_MAPPING,
    )

    normal_by_physical = {
        player.physical_seat: player.role
        for player in normal_players
    }
    mirrored_by_physical = {
        player.physical_seat: player.role
        for player in mirrored_players
    }
    assert_equal(
        normal_by_physical,
        mirrored_by_physical,
        "physical role identity should be preserved",
    )
    assert_equal(
        sum(1 for role in normal_by_physical.values() if role == WEREWOLF),
        3,
        "wolf count should remain three",
    )
    normal_seer_physical = [
        physical for physical, role in normal_by_physical.items()
        if role == SEER
    ]
    mirrored_seer_physical = [
        physical for physical, role in mirrored_by_physical.items()
        if role == SEER
    ]
    assert_equal(
        normal_seer_physical,
        mirrored_seer_physical,
        "seer physical identity should be unchanged",
    )


def test_pair_rows_and_validation():
    strategies = ["left_to_right", "right_to_left"]
    rows = run_seat_order_symmetry_experiment(
        seeds=[42],
        num_base_configs=3,
        strategies=strategies,
    )
    expected_count = 1 * 3 * len(strategies) * 2
    assert_equal(len(rows), expected_count, "row count should match design")

    errors = validate_symmetry_rows(
        rows,
        seeds=[42],
        strategies=strategies,
        num_base_configs=3,
    )
    assert_equal(errors, [], "validation should pass")

    pair_counts = {}
    for row in rows:
        pair_counts.setdefault(row["pair_id"], []).append(row)
    for pair_rows in pair_counts.values():
        assert_equal(len(pair_rows), 2, "each pair has two rows")
        assert_equal(
            sorted(row["orientation"] for row in pair_rows),
            ["mirrored", "normal"],
            "each pair has normal and mirrored rows",
        )


def test_strategy_direction_transforms_correctly():
    assert_equal(
        describe_physical_direction("left_to_right", NORMAL_MAPPING),
        "increasing_physical_seats",
        "left_to_right normal direction",
    )
    assert_equal(
        describe_physical_direction("left_to_right", MIRROR_MAPPING),
        "decreasing_physical_seats",
        "left_to_right mirrored direction",
    )
    assert_equal(
        describe_physical_direction("right_to_left", NORMAL_MAPPING),
        "decreasing_physical_seats",
        "right_to_left normal direction",
    )
    assert_equal(
        describe_physical_direction("right_to_left", MIRROR_MAPPING),
        "increasing_physical_seats",
        "right_to_left mirrored direction",
    )


def test_no_hidden_role_information_in_target_choice():
    seer = Player(1, SEER)
    candidate_roles_a = [
        VILLAGER,
        WEREWOLF,
        VILLAGER,
        WITCH,
        HUNTER,
        VILLAGER,
        WEREWOLF,
        VILLAGER,
        WEREWOLF,
    ]
    candidate_roles_b = [
        WEREWOLF,
        VILLAGER,
        WEREWOLF,
        WITCH,
        HUNTER,
        VILLAGER,
        VILLAGER,
        WEREWOLF,
        VILLAGER,
    ]

    class State:
        def __init__(self, players):
            self.players = players

    players_a = [seer] + [
        Player(player_id=index + 2, role=role)
        for index, role in enumerate(candidate_roles_a)
    ]
    players_b = [Player(1, SEER)] + [
        Player(player_id=index + 2, role=role)
        for index, role in enumerate(candidate_roles_b)
    ]

    for strategy in SEAT_ORDER_STRATEGIES:
        random.seed(stable_seed("hidden-role-test", strategy))
        target_a = choose_seer_check_target(
            State(players_a),
            players_a[0],
            seer_check_strategy=strategy,
            avoid_repeat=True,
        )
        random.seed(stable_seed("hidden-role-test", strategy))
        target_b = choose_seer_check_target(
            State(players_b),
            players_b[0],
            seer_check_strategy=strategy,
            avoid_repeat=True,
        )
        assert_equal(
            target_a.player_id,
            target_b.player_id,
            f"{strategy} should not use hidden target role",
        )


def test_no_duplicate_seer_checks_and_logging_rng_state():
    roles_by_physical = {
        1: SEER,
        2: WEREWOLF,
        3: WEREWOLF,
        4: WEREWOLF,
        5: VILLAGER,
        6: VILLAGER,
        7: VILLAGER,
        8: VILLAGER,
        9: WITCH,
        10: HUNTER,
    }
    orientation = get_orientation_specs()[0]
    game, result = run_single_orientation_game(
        42,
        1,
        "left_to_right",
        orientation,
        roles_by_physical,
    )
    events = get_seer_check_events(game.event_log)
    targets = [event["content"]["target"] for event in events]
    assert_equal(
        len(targets),
        len(set(targets)),
        "seer should not duplicate checks while avoid_repeat is enabled",
    )

    random.seed(123)
    state_before = random.getstate()
    row = build_symmetry_row(
        game,
        result,
        "pair",
        "game",
        42,
        1,
        "left_to_right",
        orientation,
    )
    state_after = random.getstate()
    assert_equal(
        state_before,
        state_after,
        "symmetry logging should not consume RNG",
    )
    assert_true(
        isinstance(json.loads(row["physical_to_displayed_seat_mapping"]), dict),
        "mapping should be logged as JSON object",
    )


def main():
    tests = [
        test_mirror_is_involutive,
        test_role_identity_preserved_under_mirror,
        test_pair_rows_and_validation,
        test_strategy_direction_transforms_correctly,
        test_no_hidden_role_information_in_target_choice,
        test_no_duplicate_seer_checks_and_logging_rng_state,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print("All seat-order symmetry tests passed.")


if __name__ == "__main__":
    main()
