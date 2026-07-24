import hashlib
import json
import random

from position_model import get_seat_type, get_side


TOTAL_SEATS = 10
PHYSICAL_SEATS = list(range(1, TOTAL_SEATS + 1))

NORMAL_MAPPING = {
    physical_seat: physical_seat
    for physical_seat in PHYSICAL_SEATS
}
MIRROR_MAPPING = {
    physical_seat: TOTAL_SEATS + 1 - physical_seat
    for physical_seat in PHYSICAL_SEATS
}

TIE_BREAK_SCHEME = "sha256_actor_uid_tiebreak_v1"
SPEECH_SUBSEED_SCHEME = "sha256_actor_uid_speech_rng_v1"
STRATEGY_SUBSEED_SCHEME = "sha256_actor_uid_strategy_rng_v1"


def stable_seed(*parts):
    text = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % (2 ** 32)


def stable_float(*parts):
    digest = hashlib.sha256(
        "|".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()
    return int(digest[:16], 16) / float(16 ** 16)


def json_dump(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def invert_mapping(mapping):
    return {
        displayed: physical
        for physical, displayed in mapping.items()
    }


def physical_to_displayed(mapping, physical_seat):
    return mapping[physical_seat]


def displayed_to_physical(mapping, displayed_player_id):
    return invert_mapping(mapping)[displayed_player_id]


def mirror_displayed_label(displayed_player_id, total_seats=TOTAL_SEATS):
    return total_seats + 1 - displayed_player_id


def rotated_mapping(rotation_offset, total_seats=TOTAL_SEATS):
    offset = rotation_offset % total_seats
    return {
        physical_seat: ((physical_seat + offset - 1) % total_seats) + 1
        for physical_seat in range(1, total_seats + 1)
    }


def clockwise_distance_physical(start_seat, target_seat, total_seats=TOTAL_SEATS):
    distance = (target_seat - start_seat) % total_seats
    return distance if distance != 0 else total_seats


def counterclockwise_distance_physical(
    start_seat,
    target_seat,
    total_seats=TOTAL_SEATS,
):
    distance = (start_seat - target_seat) % total_seats
    return distance if distance != 0 else total_seats


def circular_distance_physical(seat_a, seat_b, total_seats=TOTAL_SEATS):
    clockwise = (seat_b - seat_a) % total_seats
    counterclockwise = (seat_a - seat_b) % total_seats
    return min(clockwise, counterclockwise)


def get_actor_uid(player):
    return getattr(
        player,
        "actor_uid",
        getattr(player, "physical_seat", player.player_id),
    )


def get_physical_seat(player):
    return getattr(player, "physical_seat", player.player_id)


def get_displayed_player_id(player):
    return getattr(player, "displayed_player_id", player.player_id)


def infer_physical_to_displayed_mapping(players):
    mapping = {}
    for player in players:
        physical_seat = get_physical_seat(player)
        displayed_id = get_displayed_player_id(player)
        mapping[physical_seat] = displayed_id
    return mapping


def initialize_neutral_player_metadata(players, mapping=None):
    if mapping is None:
        mapping = infer_physical_to_displayed_mapping(players)

    displayed_to_physical_map = invert_mapping(mapping)

    for player in players:
        displayed_id = player.player_id
        physical_seat = getattr(
            player,
            "physical_seat",
            displayed_to_physical_map.get(displayed_id, displayed_id),
        )
        actor_uid = getattr(player, "actor_uid", physical_seat)

        player.actor_uid = actor_uid
        player.physical_seat = physical_seat
        player.displayed_player_id = displayed_id
        player.displayed_seat = displayed_id
        player.displayed_side = get_side(displayed_id)
        player.displayed_seat_type = get_seat_type(displayed_id)
        player.physical_side = get_side(physical_seat)
        player.physical_seat_type = get_seat_type(physical_seat)
        player.side = player.physical_side
        player.seat_type = player.physical_seat_type

    return mapping


def build_neutral_actor_order(players, seed=None, base_game_index=None):
    return [
        get_actor_uid(player)
        for player in sorted(
            players,
            key=lambda player: stable_float(
                "neutral_actor_order",
                "seed",
                seed,
                "base",
                base_game_index,
                "actor",
                get_actor_uid(player),
            ),
        )
    ]


def order_players_by_actor_order(players, actor_order):
    order_index = {
        actor_uid: index
        for index, actor_uid in enumerate(actor_order)
    }
    return sorted(
        players,
        key=lambda player: (
            order_index.get(get_actor_uid(player), len(order_index)),
            get_actor_uid(player),
        ),
    )


def get_neutral_context(game_state):
    return {
        "seed": getattr(game_state, "neutral_seed", None),
        "base_game_index": getattr(game_state, "base_game_index", None),
        "label_condition": getattr(game_state, "label_condition", None),
        "round": getattr(game_state, "round_number", None),
        "phase": getattr(game_state, "phase", None),
    }


def neutral_tie_break_value(
    game_state,
    action_type,
    acting_player,
    candidate,
    action_index=None,
):
    context = get_neutral_context(game_state)
    return stable_float(
        TIE_BREAK_SCHEME,
        context["seed"],
        context["base_game_index"],
        context["round"],
        context["phase"],
        action_type,
        get_actor_uid(acting_player) if acting_player is not None else "none",
        action_index if action_index is not None else "none",
        get_actor_uid(candidate),
    )


def choose_neutral_candidate(
    game_state,
    candidates,
    action_type,
    acting_player=None,
    action_index=None,
):
    if not candidates:
        return None

    return sorted(
        candidates,
        key=lambda candidate: neutral_tie_break_value(
            game_state,
            action_type,
            acting_player,
            candidate,
            action_index=action_index,
        ),
    )[0]


def neutral_rng(
    game_state,
    stream_name,
    actor_uid=None,
    action_index=None,
):
    context = get_neutral_context(game_state)
    return random.Random(
        stable_seed(
            stream_name,
            context["seed"],
            context["base_game_index"],
            context["round"],
            context["phase"],
            actor_uid if actor_uid is not None else "none",
            action_index if action_index is not None else "none",
        )
    )


def get_physical_to_displayed_mapping_from_state(game_state):
    mapping = getattr(game_state, "physical_to_displayed_mapping", None)
    if mapping is not None:
        return mapping
    return infer_physical_to_displayed_mapping(game_state.players)


def get_displayed_to_physical_mapping_from_state(game_state):
    mapping = get_physical_to_displayed_mapping_from_state(game_state)
    return invert_mapping(mapping)
