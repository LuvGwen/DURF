import copy
import json

from game import Game
from game_level_logging import get_seer_check_events
from player import Player
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH
from seer_action import (
    choose_left_to_right_target,
    choose_seer_check_target,
)
from seat_order_neutral import (
    MIRROR_MAPPING,
    NORMAL_MAPPING,
    PHYSICAL_SEATS,
    build_neutral_actor_order,
    choose_neutral_candidate,
    get_physical_seat,
    invert_mapping,
    mirror_displayed_label,
)
from seat_order_neutral_experiment import (
    LABEL_CONDITIONS,
    NEUTRAL_SEER_STRATEGIES,
    create_neutral_displayed_players,
    generate_physical_role_assignment,
    get_label_condition_specs,
    run_seat_order_neutral_experiment,
    run_single_neutral_game,
    stable_seed,
    validate_neutral_rows,
)
from speech_action import generate_speech_action
from ten_player_seer_position_experiment import SEER_POSITION_BASE_CONFIG


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected}, found {actual}")


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def make_fixed_roles():
    return {
        1: SEER,
        2: WEREWOLF,
        3: VILLAGER,
        4: WITCH,
        5: HUNTER,
        6: WEREWOLF,
        7: VILLAGER,
        8: VILLAGER,
        9: WEREWOLF,
        10: VILLAGER,
    }


def make_game(mapping, strategy="physical_clockwise"):
    config = dict(SEER_POSITION_BASE_CONFIG)
    config.update({
        "seer_check_strategy": strategy,
        "seer_avoid_repeat_checks": True,
        "randomize_seat_roles": False,
        "seat_order_neutral_mode": True,
        "neutral_seed": 42,
        "base_game_index": 1,
        "label_condition": "test",
        "physical_to_displayed_mapping": mapping,
    })
    players = create_neutral_displayed_players(make_fixed_roles(), mapping)
    return Game(players, **config)


def test_mirror_is_involutive():
    for label in PHYSICAL_SEATS:
        assert_equal(
            mirror_displayed_label(mirror_displayed_label(label)),
            label,
            "mirror should be involutive",
        )


def test_actor_and_physical_identity_survive_relabeling():
    normal = create_neutral_displayed_players(
        make_fixed_roles(),
        NORMAL_MAPPING,
    )
    mirrored = create_neutral_displayed_players(
        make_fixed_roles(),
        MIRROR_MAPPING,
    )
    normal_identity = {
        player.actor_uid: (player.physical_seat, player.role)
        for player in normal
    }
    mirrored_identity = {
        player.actor_uid: (player.physical_seat, player.role)
        for player in mirrored
    }
    assert_equal(
        normal_identity,
        mirrored_identity,
        "actor_uid and physical role identity should match",
    )


def test_role_assignment_independent_of_displayed_labels():
    roles_a = generate_physical_role_assignment(42, 1)
    roles_b = generate_physical_role_assignment(42, 1)
    normal = create_neutral_displayed_players(roles_a, NORMAL_MAPPING)
    mirrored = create_neutral_displayed_players(roles_b, MIRROR_MAPPING)
    assert_equal(
        {
            player.physical_seat: player.role
            for player in normal
        },
        {
            player.physical_seat: player.role
            for player in mirrored
        },
        "physical role assignment should not depend on labels",
    )


def test_neutral_tie_break_independent_of_displayed_labels():
    normal_game = make_game(NORMAL_MAPPING)
    mirrored_game = make_game(MIRROR_MAPPING)
    normal_seer = [
        player for player in normal_game.state.players
        if player.role == SEER
    ][0]
    mirrored_seer = [
        player for player in mirrored_game.state.players
        if player.role == SEER
    ][0]
    normal_candidates = [
        player for player in normal_game.state.players
        if player.player_id != normal_seer.player_id
    ]
    mirrored_candidates = [
        player for player in mirrored_game.state.players
        if player.player_id != mirrored_seer.player_id
    ]
    normal_target = choose_neutral_candidate(
        normal_game.state,
        normal_candidates,
        "test_tie",
        normal_seer,
    )
    mirrored_target = choose_neutral_candidate(
        mirrored_game.state,
        mirrored_candidates,
        "test_tie",
        mirrored_seer,
    )
    assert_equal(
        normal_target.actor_uid,
        mirrored_target.actor_uid,
        "neutral tie-break should choose the same physical actor",
    )


def test_neutral_actor_order_identical_in_physical_terms():
    normal_players = create_neutral_displayed_players(
        make_fixed_roles(),
        NORMAL_MAPPING,
    )
    mirrored_players = create_neutral_displayed_players(
        make_fixed_roles(),
        MIRROR_MAPPING,
    )
    assert_equal(
        build_neutral_actor_order(normal_players, seed=42, base_game_index=1),
        build_neutral_actor_order(mirrored_players, seed=42, base_game_index=1),
        "neutral actor order should be physical-label invariant",
    )


def test_speech_rng_independent_of_displayed_player_id():
    normal_game = make_game(NORMAL_MAPPING)
    mirrored_game = make_game(MIRROR_MAPPING)
    normal_actor = [
        player for player in normal_game.state.players
        if player.actor_uid == 3
    ][0]
    mirrored_actor = [
        player for player in mirrored_game.state.players
        if player.actor_uid == 3
    ][0]
    normal_speech = generate_speech_action(normal_actor, normal_game.state)
    mirrored_speech = generate_speech_action(mirrored_actor, mirrored_game.state)
    normal_inverse = invert_mapping(NORMAL_MAPPING)
    mirrored_inverse = invert_mapping(MIRROR_MAPPING)
    assert_equal(
        normal_speech["speech_type"],
        mirrored_speech["speech_type"],
        "speech type should match for same physical actor",
    )
    assert_equal(
        normal_speech["tokens"],
        mirrored_speech["tokens"],
        "speech tokens should match for same physical actor",
    )
    assert_equal(
        (
            normal_inverse.get(normal_speech["target"])
            if normal_speech["target"] is not None
            else None
        ),
        (
            mirrored_inverse.get(mirrored_speech["target"])
            if mirrored_speech["target"] is not None
            else None
        ),
        "target should match in physical terms",
    )


def test_random_neutral_same_physical_target_under_mirror():
    normal_game = make_game(NORMAL_MAPPING, strategy="random_neutral")
    mirrored_game = make_game(MIRROR_MAPPING, strategy="random_neutral")
    normal_seer = [
        player for player in normal_game.state.players
        if player.role == SEER
    ][0]
    mirrored_seer = [
        player for player in mirrored_game.state.players
        if player.role == SEER
    ][0]
    normal_target = choose_seer_check_target(
        normal_game.state,
        normal_seer,
        seer_check_strategy="random_neutral",
        avoid_repeat=True,
    )
    mirrored_target = choose_seer_check_target(
        mirrored_game.state,
        mirrored_seer,
        seer_check_strategy="random_neutral",
        avoid_repeat=True,
    )
    assert_equal(
        get_physical_seat(normal_target),
        get_physical_seat(mirrored_target),
        "random_neutral should choose same physical target",
    )


def test_physical_direction_strategies_ignore_label_mirroring():
    normal_game = make_game(NORMAL_MAPPING, strategy="physical_clockwise")
    mirrored_game = make_game(MIRROR_MAPPING, strategy="physical_clockwise")
    normal_seer = [
        player for player in normal_game.state.players
        if player.role == SEER
    ][0]
    mirrored_seer = [
        player for player in mirrored_game.state.players
        if player.role == SEER
    ][0]
    normal_target = choose_seer_check_target(
        normal_game.state,
        normal_seer,
        seer_check_strategy="physical_clockwise",
        avoid_repeat=True,
    )
    mirrored_target = choose_seer_check_target(
        mirrored_game.state,
        mirrored_seer,
        seer_check_strategy="physical_clockwise",
        avoid_repeat=True,
    )
    assert_equal(
        get_physical_seat(normal_target),
        get_physical_seat(mirrored_target),
        "physical clockwise target should be label-invariant",
    )


def test_no_duplicate_self_or_dead_seer_checks():
    label_spec = get_label_condition_specs(42, 1)[0]
    game, result, _ = run_single_neutral_game(
        42,
        1,
        "physical_clockwise",
        label_spec,
        make_fixed_roles(),
    )
    events = get_seer_check_events(game.event_log)
    targets = [
        event["content"]["target_physical_seat"]
        for event in events
    ]
    seer_targets = [
        event["content"]["seer_physical_seat"]
        for event in events
    ]
    assert_equal(
        len(targets),
        len(set(targets)),
        "seer should not duplicate checks",
    )
    assert_true(
        all(target != seer for target, seer in zip(targets, seer_targets)),
        "seer should not self-check",
    )
    assert_true(result["winner"] in {"wolf", "village", "draw"}, "valid winner")


def test_no_hidden_role_access_for_neutral_targeting():
    roles_a = make_fixed_roles()
    roles_b = copy.deepcopy(roles_a)
    roles_b[2] = VILLAGER
    roles_b[3] = WEREWOLF
    mapping = NORMAL_MAPPING
    players_a = create_neutral_displayed_players(roles_a, mapping)
    players_b = create_neutral_displayed_players(roles_b, mapping)
    game_a = Game(
        players_a,
        **{
            **SEER_POSITION_BASE_CONFIG,
            "seer_check_strategy": "physical_clockwise",
            "seat_order_neutral_mode": True,
            "neutral_seed": 99,
            "base_game_index": 1,
            "physical_to_displayed_mapping": mapping,
        },
    )
    game_b = Game(
        players_b,
        **{
            **SEER_POSITION_BASE_CONFIG,
            "seer_check_strategy": "physical_clockwise",
            "seat_order_neutral_mode": True,
            "neutral_seed": 99,
            "base_game_index": 1,
            "physical_to_displayed_mapping": mapping,
        },
    )
    seer_a = [player for player in game_a.state.players if player.role == SEER][0]
    seer_b = [player for player in game_b.state.players if player.role == SEER][0]
    target_a = choose_seer_check_target(
        game_a.state,
        seer_a,
        seer_check_strategy="physical_clockwise",
        avoid_repeat=True,
    )
    target_b = choose_seer_check_target(
        game_b.state,
        seer_b,
        seer_check_strategy="physical_clockwise",
        avoid_repeat=True,
    )
    assert_equal(
        target_a.physical_seat,
        target_b.physical_seat,
        "neutral physical strategy should not inspect hidden roles",
    )


def test_row_count_unique_ids_and_label_conditions():
    rows = run_seat_order_neutral_experiment(
        seeds=[42],
        num_base_configs=2,
        configs=[
            {
                **SEER_POSITION_BASE_CONFIG,
                "name": "physical_clockwise",
                "seer_check_strategy": "physical_clockwise",
                "seer_avoid_repeat_checks": True,
                "randomize_seat_roles": False,
                "seat_order_neutral_mode": True,
            }
        ],
    )
    validation = validate_neutral_rows(
        rows,
        seeds=[42],
        strategies=["physical_clockwise"],
        num_base_configs=2,
        label_conditions=LABEL_CONDITIONS,
    )
    assert_true(validation["valid"], f"validation failed: {validation['errors']}")
    assert_equal(
        validation["row_count"],
        1 * 1 * 2 * len(LABEL_CONDITIONS),
        "row count should match design",
    )
    for row in rows:
        assert_true(row["winner"] in {"wolf", "village", "draw"}, "winner valid")


def test_default_legacy_left_to_right_behavior_unchanged():
    seer = Player(5, SEER)
    candidates = [
        Player(3, VILLAGER),
        Player(1, WEREWOLF),
        Player(4, VILLAGER),
    ]
    target = choose_left_to_right_target(candidates, checked_target_ids=set())
    assert_equal(
        target.player_id,
        1,
        "legacy left_to_right should still favor lowest displayed id",
    )


def test_deterministic_small_rerun_is_identical():
    rows_a = run_seat_order_neutral_experiment(
        seeds=[42],
        num_base_configs=1,
        configs=[
            {
                **SEER_POSITION_BASE_CONFIG,
                "name": "random_neutral",
                "seer_check_strategy": "random_neutral",
                "seer_avoid_repeat_checks": True,
                "randomize_seat_roles": False,
                "seat_order_neutral_mode": True,
            }
        ],
    )
    rows_b = run_seat_order_neutral_experiment(
        seeds=[42],
        num_base_configs=1,
        configs=[
            {
                **SEER_POSITION_BASE_CONFIG,
                "name": "random_neutral",
                "seer_check_strategy": "random_neutral",
                "seer_avoid_repeat_checks": True,
                "randomize_seat_roles": False,
                "seat_order_neutral_mode": True,
            }
        ],
    )
    assert_equal(
        json.dumps(rows_a, sort_keys=True),
        json.dumps(rows_b, sort_keys=True),
        "small deterministic rerun should be byte-identical as JSON",
    )


def test_no_strategy_engine_pair_control_equivalence():
    base_config = {
        **SEER_POSITION_BASE_CONFIG,
        "use_suspicion_voting": False,
        "enable_suspicion_update": False,
        "enable_seer": False,
        "enable_witch": False,
        "enable_hunter": False,
        "enable_speech": False,
        "enable_herding": False,
        "enable_role_prior": False,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
        "enable_deception_credibility": False,
        "enable_speaker_memory": False,
        "randomize_seat_roles": False,
        "seat_order_neutral_mode": True,
        "neutral_seed": 123,
        "base_game_index": 1,
    }
    normal_players = create_neutral_displayed_players(
        make_fixed_roles(),
        NORMAL_MAPPING,
    )
    mirrored_players = create_neutral_displayed_players(
        make_fixed_roles(),
        MIRROR_MAPPING,
    )
    normal_game = Game(
        normal_players,
        **{
            **base_config,
            "label_condition": "normal",
            "physical_to_displayed_mapping": NORMAL_MAPPING,
        },
    )
    mirrored_game = Game(
        mirrored_players,
        **{
            **base_config,
            "label_condition": "mirrored",
            "physical_to_displayed_mapping": MIRROR_MAPPING,
        },
    )
    result_normal = normal_game.run_game(max_rounds=5)
    result_mirrored = mirrored_game.run_game(max_rounds=5)
    normal_alive_physical = sorted(
        player.physical_seat
        for player in normal_game.state.players
        if player.alive
    )
    mirrored_alive_physical = sorted(
        player.physical_seat
        for player in mirrored_game.state.players
        if player.alive
    )
    assert_equal(
        result_normal["winner"],
        result_mirrored["winner"],
        "no-strategy pair winners should match",
    )
    assert_equal(
        normal_alive_physical,
        mirrored_alive_physical,
        "no-strategy pair final alive physical sets should match",
    )


def main():
    tests = [
        test_mirror_is_involutive,
        test_actor_and_physical_identity_survive_relabeling,
        test_role_assignment_independent_of_displayed_labels,
        test_neutral_tie_break_independent_of_displayed_labels,
        test_neutral_actor_order_identical_in_physical_terms,
        test_speech_rng_independent_of_displayed_player_id,
        test_random_neutral_same_physical_target_under_mirror,
        test_physical_direction_strategies_ignore_label_mirroring,
        test_no_duplicate_self_or_dead_seer_checks,
        test_no_hidden_role_access_for_neutral_targeting,
        test_row_count_unique_ids_and_label_conditions,
        test_default_legacy_left_to_right_behavior_unchanged,
        test_deterministic_small_rerun_is_identical,
        test_no_strategy_engine_pair_control_equivalence,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print("All seat-order-neutral tests passed.")


if __name__ == "__main__":
    main()
