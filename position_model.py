import random

from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH, get_team


LEFT_SIDE_SEATS = {1, 2, 3, 4, 5}
RIGHT_SIDE_SEATS = {6, 7, 8, 9, 10}
EDGE_SEATS = {1, 5, 6, 10}
INNER_SEATS = {2, 3, 4, 7, 8, 9}

TEN_PLAYER_ROLE_POOL = [
    WEREWOLF,
    WEREWOLF,
    WEREWOLF,
    VILLAGER,
    VILLAGER,
    VILLAGER,
    VILLAGER,
    SEER,
    WITCH,
    HUNTER,
]


def get_side(player_id):
    if player_id in LEFT_SIDE_SEATS:
        return "left"

    if player_id in RIGHT_SIDE_SEATS:
        return "right"

    return None


def get_seat_type(player_id):
    if player_id in EDGE_SEATS:
        return "edge"

    if player_id in INNER_SEATS:
        return "inner"

    return None


def is_edge_seat(player_id):
    return get_seat_type(player_id) == "edge"


def is_inner_seat(player_id):
    return get_seat_type(player_id) == "inner"


def same_side(player_id_a, player_id_b):
    side_a = get_side(player_id_a)
    side_b = get_side(player_id_b)

    return side_a is not None and side_a == side_b


def assign_positions(players):
    for player in players:
        player.side = get_side(player.player_id)
        player.seat_type = get_seat_type(player.player_id)

    return players


def assign_random_roles_to_seats(players, role_pool=None):
    if role_pool is None:
        role_pool = TEN_PLAYER_ROLE_POOL

    if len(players) != len(role_pool):
        raise ValueError("Role pool size must match number of players.")

    shuffled_roles = list(role_pool)
    random.shuffle(shuffled_roles)
    assign_positions(players)

    for player, role in zip(players, shuffled_roles):
        player.role = role
        player.team = get_team(role)

    return players


def summarize_seat_role_assignment(players):
    wolves = [player for player in players if player.is_wolf()]
    seers = [player for player in players if player.role == SEER]

    wolves_on_edge = sum(
        1 for player in wolves
        if getattr(player, "seat_type", None) == "edge"
    )
    wolves_on_inner = sum(
        1 for player in wolves
        if getattr(player, "seat_type", None) == "inner"
    )
    wolves_left_side = sum(
        1 for player in wolves
        if getattr(player, "side", None) == "left"
    )
    wolves_right_side = sum(
        1 for player in wolves
        if getattr(player, "side", None) == "right"
    )
    seer = seers[0] if seers else None

    return {
        "assignments": {
            player.player_id: {
                "role": player.role,
                "side": getattr(player, "side", None),
                "seat_type": getattr(player, "seat_type", None),
            }
            for player in players
        },
        "wolves_on_edge": wolves_on_edge,
        "wolves_on_inner": wolves_on_inner,
        "wolves_left_side": wolves_left_side,
        "wolves_right_side": wolves_right_side,
        "edge_has_wolf": wolves_on_edge > 0,
        "seer": seer.player_id if seer is not None else None,
        "seer_side": getattr(seer, "side", None) if seer is not None else None,
        "seer_seat_type": (
            getattr(seer, "seat_type", None) if seer is not None else None
        ),
        "seer_on_edge": (
            getattr(seer, "seat_type", None) == "edge"
            if seer is not None
            else False
        ),
        "seer_left_side": (
            getattr(seer, "side", None) == "left"
            if seer is not None
            else False
        ),
    }


if __name__ == "__main__":
    for player_id in range(1, 11):
        print(player_id, get_side(player_id), get_seat_type(player_id))
