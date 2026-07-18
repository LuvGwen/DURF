import random

from game import Game
from game_state import GameState
from player import Player
from position_model import assign_positions
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH
from seer_action import perform_seer_action


TEN_PLAYER_ROLES = [
    WEREWOLF,
    WEREWOLF,
    WEREWOLF,
    SEER,
    WITCH,
    HUNTER,
    VILLAGER,
    VILLAGER,
    VILLAGER,
    VILLAGER,
]


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"PASS: {message}")


def make_state():
    players = [
        Player(player_id=i + 1, role=role)
        for i, role in enumerate(TEN_PLAYER_ROLES)
    ]
    assign_positions(players)
    return GameState(players)


def get_player(state, player_id):
    return state.get_player_by_id(player_id)


def test_edge_first():
    random.seed(1)
    state = make_state()
    event = perform_seer_action(state, seer_check_strategy="edge_first")

    check(event["target_seat_type"] == "edge", "edge_first checks edge")
    check(event["target"] != event["seer"], "edge_first does not self-check")


def test_inner_first():
    random.seed(2)
    state = make_state()
    event = perform_seer_action(state, seer_check_strategy="inner_first")

    check(event["target_seat_type"] == "inner", "inner_first checks inner")
    check(event["target"] != event["seer"], "inner_first does not self-check")


def test_opposite_side():
    random.seed(3)
    state = make_state()
    event = perform_seer_action(state, seer_check_strategy="opposite_side")

    check(event["seer_side"] == "left", "seer side is left in test setup")
    check(
        event["target_side"] == "right",
        "opposite_side checks the other side",
    )


def test_highest_p_wolf():
    random.seed(4)
    state = make_state()
    get_player(state, 8).p_wolf = 0.95
    get_player(state, 9).p_wolf = 0.60

    event = perform_seer_action(state, seer_check_strategy="highest_p_wolf")

    check(event["target"] == 8, "highest_p_wolf checks max p_wolf target")


def test_highest_suspicion():
    random.seed(5)
    state = make_state()
    get_player(state, 7).suspicion_score = 0.30
    get_player(state, 9).suspicion_score = 0.90

    event = perform_seer_action(
        state,
        seer_check_strategy="highest_suspicion",
    )

    check(
        event["target"] == 9,
        "highest_suspicion checks max suspicion target",
    )


def test_no_dead_target():
    random.seed(6)
    state = make_state()
    get_player(state, 1).alive = False

    event = perform_seer_action(state, seer_check_strategy="edge_first")
    target = get_player(state, event["target"])

    check(target.alive, "seer does not check dead players")
    check(event["target"] != 1, "dead edge seat is not checked")


def test_avoids_repeat_when_possible():
    random.seed(7)
    state = make_state()

    first_event = perform_seer_action(
        state,
        seer_check_strategy="edge_first",
    )
    second_event = perform_seer_action(
        state,
        seer_check_strategy="edge_first",
    )

    check(
        first_event["target"] != second_event["target"],
        "seer avoids repeat checks when unchecked targets exist",
    )


def test_game_event_log_fields():
    random.seed(8)
    state = make_state()
    game = Game(
        state.players,
        enable_position_model=True,
        seer_check_strategy="edge_first",
        enable_witch=False,
        enable_hunter=False,
    )

    game.night_phase()
    seer_events = [
        event for event in game.event_log
        if event["event_type"] == "seer_check"
    ]

    check(len(seer_events) == 1, "game logs one seer_check event per night")
    content = seer_events[0]["content"]
    check("target_side" in content, "seer event records target_side")
    check("target_seat_type" in content, "seer event records target_seat_type")
    check(
        content["seer_check_strategy"] == "edge_first",
        "seer event records strategy",
    )


def test_default_strategy():
    random.seed(9)
    state = make_state()
    event = perform_seer_action(state)
    target = get_player(state, event["target"])

    check(target.alive, "default strategy checks alive target")
    check(event["target"] != event["seer"], "default strategy does not self-check")
    check(
        "target_is_wolf" in event,
        "default strategy records target_is_wolf",
    )


if __name__ == "__main__":
    test_edge_first()
    test_inner_first()
    test_opposite_side()
    test_highest_p_wolf()
    test_highest_suspicion()
    test_no_dead_target()
    test_avoids_repeat_when_possible()
    test_game_event_log_fields()
    test_default_strategy()
    print("All seer position strategy tests passed.")
