import random

from config import DEFAULT_MAX_ROUNDS
from game import Game
from physical_direction_replay import (
    ReplayActionLog,
    ReplayController,
    ReplayError,
    SuppliedAction,
    canonical_mirrored_state,
    assert_direction_reversal_preserved,
    assert_mirrored_adjacency_preserved,
    canonical_physical_state,
    capture_replay_action_log,
    compare_strategy_mirror_logs,
    create_players_from_actor_layout,
    mirror_action_log,
    mirror_actor_physical_seats,
    mirror_physical_role_assignment,
    mirror_physical_seat,
    mirror_supplied_action,
    physical_seats_by_actor_from_physical_roles,
    replay_action_log,
    replay_mirrored_action_log,
    role_by_actor_from_physical_roles,
)
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH
from seat_order_neutral import MIRROR_MAPPING, NORMAL_MAPPING, stable_seed
from seat_order_neutral_experiment import generate_physical_role_assignment
from ten_player_seer_position_experiment import SEER_POSITION_BASE_CONFIG


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


def fixed_role_by_actor():
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


def fixed_physical_by_actor():
    return {actor_uid: actor_uid for actor_uid in range(1, 11)}


def make_action(
    index,
    round_number,
    phase,
    subphase,
    actor_uid,
    action_type,
    target_uid=None,
    payload=None,
):
    physical_by_actor = fixed_physical_by_actor()
    return SuppliedAction(
        round_number=round_number,
        phase=phase,
        subphase=subphase,
        actor_uid=actor_uid,
        action_type=action_type,
        physical_target_uid=target_uid,
        physical_target_seat=(
            physical_by_actor[target_uid]
            if isinstance(target_uid, int)
            else None
        ),
        payload=payload or {},
        action_sequence_index=index,
    )


def make_action_log(actions, physical_by_actor=None):
    if physical_by_actor is None:
        physical_by_actor = fixed_physical_by_actor()
    return ReplayActionLog(
        action_log_id="unit_action_log",
        role_by_actor_uid=fixed_role_by_actor(),
        physical_seat_by_actor_uid=physical_by_actor,
        actions=actions,
        initial_p_wolf=0.3,
    )


def run_reference_game(seed=42, base_game_index=1, strategy="physical_clockwise"):
    role_by_physical = generate_physical_role_assignment(seed, base_game_index)
    role_by_actor = role_by_actor_from_physical_roles(role_by_physical)
    physical_by_actor = physical_seats_by_actor_from_physical_roles(
        role_by_physical
    )
    players = create_players_from_actor_layout(
        role_by_actor,
        physical_by_actor,
        NORMAL_MAPPING,
        initial_p_wolf=SEER_POSITION_BASE_CONFIG["initial_p_wolf"],
    )
    config = dict(SEER_POSITION_BASE_CONFIG)
    config.update({
        "seer_check_strategy": strategy,
        "seer_avoid_repeat_checks": True,
        "randomize_seat_roles": False,
        "seat_order_neutral_mode": True,
        "neutral_seed": seed,
        "base_game_index": base_game_index,
        "label_condition": "unit_test",
        "physical_to_displayed_mapping": NORMAL_MAPPING,
        "main_game_seed": stable_seed(
            "physical_direction_replay_main_game",
            seed,
            base_game_index,
        ),
    })
    random.seed(config["main_game_seed"])
    game = Game(players, **config)
    result = game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
    action_log = capture_replay_action_log(
        game,
        f"unit_seed_{seed}_base_{base_game_index}_{strategy}",
        role_by_actor_uid=role_by_actor,
        physical_seat_by_actor_uid=physical_by_actor,
        initial_p_wolf=config["initial_p_wolf"],
    )
    return game, result, action_log, role_by_actor, physical_by_actor


def test_physical_mirror_is_involutive():
    for seat in range(1, 11):
        assert_equal(
            mirror_physical_seat(mirror_physical_seat(seat)),
            seat,
            "physical mirror should be involutive",
        )


def test_mirrored_adjacency_is_preserved():
    assert_mirrored_adjacency_preserved()


def test_clockwise_maps_to_counterclockwise():
    assert_direction_reversal_preserved()


def test_actor_uid_identity_and_roles_are_preserved_under_mirror():
    roles = fixed_role_by_actor()
    physical_by_actor = fixed_physical_by_actor()
    mirrored_physical = mirror_actor_physical_seats(physical_by_actor)
    assert_equal(roles, fixed_role_by_actor(), "roles should be preserved")
    assert_equal(
        set(physical_by_actor),
        set(mirrored_physical),
        "actor_uids should be preserved",
    )


def test_role_assignment_mirror_is_involutive():
    role_by_physical = {
        seat: fixed_role_by_actor()[seat]
        for seat in range(1, 11)
    }
    assert_equal(
        mirror_physical_role_assignment(
            mirror_physical_role_assignment(role_by_physical)
        ),
        role_by_physical,
        "role assignment mirror should be involutive",
    )


def test_supplied_action_mirrors_correctly():
    action = make_action(
        0,
        1,
        "night",
        "seer_check",
        1,
        "seer_check",
        2,
        payload={"strategy": "physical_clockwise"},
    )
    mirrored = mirror_supplied_action(action)
    assert_equal(
        mirrored.physical_target_uid,
        2,
        "mirroring should preserve target actor identity",
    )
    assert_equal(
        mirrored.physical_target_seat,
        9,
        "mirroring should transform target physical seat",
    )
    assert_equal(
        mirrored.payload["strategy"],
        "physical_counterclockwise",
        "mirroring should reverse direction metadata",
    )


def test_action_log_mirrors_correctly():
    action_log = make_action_log([
        make_action(0, 1, "night", "seer_check", 1, "seer_check", 2),
    ])
    mirrored = mirror_action_log(action_log)
    assert_equal(
        mirrored.physical_seat_by_actor_uid[1],
        10,
        "mirrored action log should mirror actor physical seats",
    )
    assert_equal(
        mirrored.actions[0].physical_target_seat,
        9,
        "mirrored action log should mirror target physical seats",
    )


def test_canonical_state_is_label_independent():
    roles = fixed_role_by_actor()
    physical_by_actor = fixed_physical_by_actor()
    normal_players = create_players_from_actor_layout(
        roles,
        physical_by_actor,
        NORMAL_MAPPING,
        initial_p_wolf=0.3,
    )
    mirrored_label_players = create_players_from_actor_layout(
        roles,
        physical_by_actor,
        MIRROR_MAPPING,
        initial_p_wolf=0.3,
    )
    assert_equal(
        canonical_physical_state(normal_players),
        canonical_physical_state(mirrored_label_players),
        "canonical physical state should ignore displayed labels",
    )


def test_canonical_mirrored_state_maps_back_to_reference_coordinates():
    roles = fixed_role_by_actor()
    physical_by_actor = fixed_physical_by_actor()
    mirrored_physical = mirror_actor_physical_seats(physical_by_actor)
    reference = ReplayController(roles, physical_by_actor)
    mirrored = ReplayController(roles, mirrored_physical)
    assert_equal(
        canonical_physical_state(reference),
        canonical_mirrored_state(mirrored),
        "canonical mirrored state should map back to reference coordinates",
    )


def test_action_log_json_serialization_is_stable():
    action_log = make_action_log([
        make_action(0, 1, "night", "seer_check", 1, "seer_check", 2),
    ])
    assert_equal(
        action_log.to_json(),
        action_log.to_json(),
        "action log JSON serialization should be stable",
    )


def test_capture_to_replay_reproduces_exact_state_sequence():
    _, _, action_log, _, _ = run_reference_game(42, 1)
    result, _ = replay_action_log(action_log)
    assert_true(
        result.state_sequence_exact_match,
        "capture to replay should reproduce state hashes",
    )


def test_capture_to_replay_reproduces_winner_and_final_alive_set():
    _, _, action_log, _, _ = run_reference_game(42, 2)
    result, _ = replay_action_log(action_log)
    assert_true(result.winner_match, "winner should match")
    assert_true(result.final_alive_set_match, "final alive set should match")


def test_invalid_replay_action_raises_clear_error():
    action_log = make_action_log([
        make_action(0, 1, "night", "seer_check", 3, "seer_check", 2),
    ])
    controller = ReplayController(
        action_log.role_by_actor_uid,
        action_log.physical_seat_by_actor_uid,
    )
    assert_raises(
        ReplayError,
        lambda: controller.apply_action(action_log.actions[0]),
        "non-seer seer_check should raise ReplayError",
    )


def test_wrong_phase_action_raises_clear_error():
    action_log = make_action_log([
        make_action(0, 1, "day", "seer_check", 1, "seer_check", 2),
    ])
    controller = ReplayController(
        action_log.role_by_actor_uid,
        action_log.physical_seat_by_actor_uid,
    )
    assert_raises(
        ReplayError,
        lambda: controller.apply_action(action_log.actions[0]),
        "seer_check in day phase should raise ReplayError",
    )


def test_illegal_target_raises_clear_error():
    action_log = make_action_log([
        make_action(0, 1, "night", "seer_check", 1, "seer_check", 1),
    ])
    controller = ReplayController(
        action_log.role_by_actor_uid,
        action_log.physical_seat_by_actor_uid,
    )
    assert_raises(
        ReplayError,
        lambda: controller.apply_action(action_log.actions[0]),
        "seer self-check should raise ReplayError",
    )


def test_duplicate_seer_check_is_rejected():
    actions = [
        make_action(0, 1, "night", "seer_check", 1, "seer_check", 2),
        make_action(1, 2, "night", "seer_check", 1, "seer_check", 2),
    ]
    action_log = make_action_log(actions)
    controller = ReplayController(
        action_log.role_by_actor_uid,
        action_log.physical_seat_by_actor_uid,
    )
    controller.apply_action(actions[0])
    assert_raises(
        ReplayError,
        lambda: controller.apply_action(actions[1]),
        "duplicate seer check should raise ReplayError",
    )


def test_fixed_vote_scenario_replays():
    actions = [
        make_action(0, 1, "day", "vote", 1, "vote", 2),
        make_action(1, 1, "day", "vote", 3, "vote", 2),
        make_action(2, 1, "day", "vote", 4, "vote", 2),
        make_action(3, 1, "day", "resolve", "village_vote", "day_vote_resolution", 2),
    ]
    controller = ReplayController(fixed_role_by_actor(), fixed_physical_by_actor())
    for action in actions:
        controller.apply_action(action)
    assert_true(
        not controller.get_actor(2).alive,
        "vote resolution should eliminate supplied target",
    )


def test_wolf_kill_only_mirror_scenario_is_symmetric():
    actions = [
        make_action(0, 1, "night", "wolf_kill", "wolf_team", "wolf_kill", 3),
    ]
    action_log = make_action_log(actions)
    result, _, _ = replay_mirrored_action_log(action_log)
    assert_true(
        result.state_sequence_exact_match,
        "wolf-kill-only mirror replay should be symmetric",
    )


def test_speech_only_mirror_scenario_is_symmetric():
    actions = [
        make_action(
            0,
            1,
            "day",
            "speech",
            3,
            "speech_action",
            2,
            payload={"speech_type": "accuse"},
        ),
    ]
    action_log = make_action_log(actions)
    result, _, _ = replay_mirrored_action_log(action_log)
    assert_true(
        result.state_sequence_exact_match,
        "speech-only mirror replay should be symmetric",
    )


def test_witch_resolution_is_symmetric():
    actions = [
        make_action(0, 1, "night", "witch_save", 4, "witch_save", 3),
    ]
    action_log = make_action_log(actions)
    result, _, _ = replay_mirrored_action_log(action_log)
    assert_true(
        result.state_sequence_exact_match,
        "witch save mirror replay should be symmetric",
    )


def test_witch_cannot_use_both_potions_same_night():
    actions = [
        make_action(0, 1, "night", "witch_save", 4, "witch_save", 3),
        make_action(1, 1, "night", "witch_poison", 4, "witch_poison", 2),
    ]
    controller = ReplayController(fixed_role_by_actor(), fixed_physical_by_actor())
    controller.apply_action(actions[0])
    assert_raises(
        ReplayError,
        lambda: controller.apply_action(actions[1]),
        "witch should not use antidote and poison in same night",
    )


def test_witch_cannot_use_antidote_twice():
    actions = [
        make_action(0, 1, "night", "witch_save", 4, "witch_save", 3),
        make_action(1, 2, "night", "witch_save", 4, "witch_save", 7),
    ]
    controller = ReplayController(fixed_role_by_actor(), fixed_physical_by_actor())
    controller.apply_action(actions[0])
    assert_raises(
        ReplayError,
        lambda: controller.apply_action(actions[1]),
        "witch antidote should be single use",
    )


def test_witch_cannot_use_poison_twice():
    actions = [
        make_action(0, 1, "night", "witch_poison", 4, "witch_poison", 3),
        make_action(1, 2, "night", "witch_poison", 4, "witch_poison", 7),
    ]
    controller = ReplayController(fixed_role_by_actor(), fixed_physical_by_actor())
    controller.apply_action(actions[0])
    assert_raises(
        ReplayError,
        lambda: controller.apply_action(actions[1]),
        "witch poison should be single use",
    )


def test_hunter_resolution_is_symmetric():
    actions = [
        make_action(0, 1, "night", "wolf_kill", "wolf_team", "wolf_kill", 5),
        make_action(1, 1, "night", "hunter_shot", 5, "hunter_shot", 2),
    ]
    action_log = make_action_log(actions)
    result, _, _ = replay_mirrored_action_log(action_log)
    assert_true(
        result.state_sequence_exact_match,
        "hunter-shot mirror replay should be symmetric",
    )


def test_chained_death_resolution_is_symmetric():
    actions = [
        make_action(0, 1, "night", "witch_poison", 4, "witch_poison", 5),
        make_action(1, 1, "night", "hunter_shot", 5, "hunter_shot", 2),
    ]
    action_log = make_action_log(actions)
    result, _, _ = replay_mirrored_action_log(action_log)
    assert_true(
        result.state_sequence_exact_match,
        "chained death mirror replay should be symmetric",
    )


def test_strategy_mirror_first_targets_match():
    _, _, reference_log, role_by_actor, physical_by_actor = run_reference_game(
        42,
        3,
        strategy="physical_clockwise",
    )
    mirrored_physical = mirror_actor_physical_seats(physical_by_actor)
    players = create_players_from_actor_layout(
        role_by_actor,
        mirrored_physical,
        NORMAL_MAPPING,
        initial_p_wolf=SEER_POSITION_BASE_CONFIG["initial_p_wolf"],
    )
    config = dict(SEER_POSITION_BASE_CONFIG)
    config.update({
        "seer_check_strategy": "physical_counterclockwise",
        "seer_avoid_repeat_checks": True,
        "randomize_seat_roles": False,
        "seat_order_neutral_mode": True,
        "neutral_seed": 42,
        "base_game_index": 3,
        "label_condition": "strategy_mirror_unit_test",
        "physical_to_displayed_mapping": NORMAL_MAPPING,
        "main_game_seed": stable_seed(
            "physical_direction_replay_main_game",
            42,
            3,
        ),
    })
    random.seed(config["main_game_seed"])
    mirrored_game = Game(players, **config)
    mirrored_game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
    mirrored_log = capture_replay_action_log(
        mirrored_game,
        "strategy_mirror_unit_test",
        role_by_actor,
        mirrored_physical,
        initial_p_wolf=config["initial_p_wolf"],
    )
    comparison = compare_strategy_mirror_logs(reference_log, mirrored_log)
    assert_true(
        comparison["first_check_mirror_match"],
        "strategy-mirror first target should match",
    )


def test_strategy_mirror_full_check_paths_match_under_equivalent_state():
    _, _, reference_log, role_by_actor, physical_by_actor = run_reference_game(
        43,
        3,
        strategy="physical_clockwise",
    )
    mirrored_physical = mirror_actor_physical_seats(physical_by_actor)
    players = create_players_from_actor_layout(
        role_by_actor,
        mirrored_physical,
        NORMAL_MAPPING,
        initial_p_wolf=SEER_POSITION_BASE_CONFIG["initial_p_wolf"],
    )
    config = dict(SEER_POSITION_BASE_CONFIG)
    config.update({
        "seer_check_strategy": "physical_counterclockwise",
        "seer_avoid_repeat_checks": True,
        "randomize_seat_roles": False,
        "seat_order_neutral_mode": True,
        "neutral_seed": 43,
        "base_game_index": 3,
        "label_condition": "strategy_mirror_unit_test",
        "physical_to_displayed_mapping": NORMAL_MAPPING,
        "main_game_seed": stable_seed(
            "physical_direction_replay_main_game",
            43,
            3,
        ),
    })
    random.seed(config["main_game_seed"])
    mirrored_game = Game(players, **config)
    mirrored_game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
    mirrored_log = capture_replay_action_log(
        mirrored_game,
        "strategy_mirror_unit_test",
        role_by_actor,
        mirrored_physical,
        initial_p_wolf=config["initial_p_wolf"],
    )
    comparison = compare_strategy_mirror_logs(reference_log, mirrored_log)
    assert_true(
        comparison["full_check_sequence_mirror_match"],
        "strategy-mirror full check path should match",
    )


def test_default_game_behavior_still_runs():
    game = Game()
    result = game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
    assert_true(result["game_over"], "default game should still finish")


def run_all_tests():
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"All {len(tests)} physical direction replay tests passed.")


if __name__ == "__main__":
    run_all_tests()
