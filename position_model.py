LEFT_SIDE_SEATS = {1, 2, 3, 4, 5}
RIGHT_SIDE_SEATS = {6, 7, 8, 9, 10}
EDGE_SEATS = {1, 5, 6, 10}
INNER_SEATS = {2, 3, 4, 7, 8, 9}


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


if __name__ == "__main__":
    for player_id in range(1, 11):
        print(player_id, get_side(player_id), get_seat_type(player_id))
