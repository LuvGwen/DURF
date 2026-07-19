import random
from collections import Counter

from config import TEN_PLAYER_ROLE_SETUP
from game import Game, create_default_players
from position_model import get_seat_type, get_side
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH
from simulation import run_simulation, summarize_results


EXPECTED_ROLE_COUNTS = {
    WEREWOLF: 3,
    VILLAGER: 4,
    SEER: 1,
    WITCH: 1,
    HUNTER: 1,
}


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"PASS: {message}")


def count_roles(players):
    return Counter(player.role for player in players)


def test_default_does_not_randomize_roles():
    players = create_default_players(role_setup=TEN_PLAYER_ROLE_SETUP)
    game = Game(
        players,
        enable_position_model=True,
        randomize_seat_roles=False,
    )

    roles_after_init = [player.role for player in game.state.players]

    check(
        roles_after_init == TEN_PLAYER_ROLE_SETUP,
        "randomize_seat_roles False preserves role order",
    )
    check(
        not any(
            event["event_type"] == "seat_role_assignment"
            for event in game.event_log
        ),
        "default game does not log seat_role_assignment",
    )


def test_randomize_roles_keeps_seat_ids_and_role_pool():
    random.seed(42)
    players = create_default_players(role_setup=TEN_PLAYER_ROLE_SETUP)
    game = Game(
        players,
        enable_position_model=True,
        randomize_seat_roles=True,
    )

    player_ids = [player.player_id for player in game.state.players]

    check(player_ids == list(range(1, 11)), "player_id remains seat number")
    check(
        count_roles(game.state.players) == EXPECTED_ROLE_COUNTS,
        "randomized role pool has expected 10-player counts",
    )

    for player in game.state.players:
        check(
            player.side == get_side(player.player_id),
            f"player {player.player_id} side comes from seat id",
        )
        check(
            player.seat_type == get_seat_type(player.player_id),
            f"player {player.player_id} seat_type comes from seat id",
        )


def test_seat_role_assignment_event():
    random.seed(7)
    players = create_default_players(role_setup=TEN_PLAYER_ROLE_SETUP)
    game = Game(
        players,
        enable_position_model=True,
        randomize_seat_roles=True,
    )
    events = [
        event for event in game.event_log
        if event["event_type"] == "seat_role_assignment"
    ]

    check(len(events) == 1, "seat_role_assignment event is logged once")

    content = events[0]["content"]
    assignments = content["assignments"]

    check(content["randomize_seat_roles"] is True, "event records toggle")
    check(len(assignments) == 10, "event records all 10 seats")
    check(
        content["wolves_on_edge"] + content["wolves_on_inner"] == 3,
        "event records all wolves by seat type",
    )
    check(
        content["wolves_left_side"] + content["wolves_right_side"] == 3,
        "event records all wolves by side",
    )
    check(content["seer"] is not None, "event records seer seat")


def test_simulation_seat_role_statistics():
    results = run_simulation(
        num_games=5,
        seed=42,
        role_setup=TEN_PLAYER_ROLE_SETUP,
        enable_position_model=True,
        randomize_seat_roles=True,
    )
    summary = summarize_results(results)

    check(
        summary["seat_role_assignment_games"] == 5,
        "simulation records one seat assignment per randomized game",
    )
    check(
        summary["total_wolves_on_edge"] + summary["total_wolves_on_inner"]
        == 15,
        "simulation counts all wolves by edge/inner seats",
    )
    check(
        summary["total_wolves_left_side"] + summary["total_wolves_right_side"]
        == 15,
        "simulation counts all wolves by left/right side",
    )
    check(
        0.0 <= summary["edge_has_wolf_rate"] <= 1.0,
        "edge_has_wolf_rate is a valid rate",
    )
    check(
        0.0 <= summary["seer_on_edge_rate"] <= 1.0,
        "seer_on_edge_rate is a valid rate",
    )
    check(
        0.0 <= summary["seer_left_side_rate"] <= 1.0,
        "seer_left_side_rate is a valid rate",
    )


if __name__ == "__main__":
    test_default_does_not_randomize_roles()
    test_randomize_roles_keeps_seat_ids_and_role_pool()
    test_seat_role_assignment_event()
    test_simulation_seat_role_statistics()
    print("All randomized seat-role tests passed.")
