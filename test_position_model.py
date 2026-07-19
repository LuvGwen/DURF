from player import Player
from position_model import (
    assign_positions,
    get_seat_type,
    get_side,
    same_side,
)
from roles import VILLAGER


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"PASS: {message}")


def test_position_helpers():
    check(get_side(1) == "left", "get_side(1) == left")
    check(get_side(5) == "left", "get_side(5) == left")
    check(get_side(6) == "right", "get_side(6) == right")
    check(get_side(10) == "right", "get_side(10) == right")
    check(get_seat_type(1) == "edge", "get_seat_type(1) == edge")
    check(get_seat_type(5) == "edge", "get_seat_type(5) == edge")
    check(get_seat_type(6) == "edge", "get_seat_type(6) == edge")
    check(get_seat_type(10) == "edge", "get_seat_type(10) == edge")
    check(get_seat_type(2) == "inner", "get_seat_type(2) == inner")
    check(same_side(1, 5) is True, "same_side(1, 5) is True")
    check(same_side(1, 6) is False, "same_side(1, 6) is False")


def test_assign_positions():
    players = [Player(player_id=i, role=VILLAGER) for i in range(1, 11)]
    assign_positions(players)

    player_by_id = {player.player_id: player for player in players}

    check(player_by_id[1].side == "left", "player 1 side assigned")
    check(player_by_id[6].side == "right", "player 6 side assigned")
    check(player_by_id[1].seat_type == "edge", "player 1 edge assigned")
    check(player_by_id[2].seat_type == "inner", "player 2 inner assigned")


if __name__ == "__main__":
    test_position_helpers()
    test_assign_positions()
    print("All position model tests passed.")
