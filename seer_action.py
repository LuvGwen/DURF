import random

from position_model import is_edge_seat, is_inner_seat
from roles import SEER


SEER_CHECK_STRATEGIES = {
    "default",
    "random",
    "edge_first",
    "inner_first",
    "highest_p_wolf",
    "highest_suspicion",
    "opposite_side",
}


def get_alive_seers(game_state):
    return [
        player for player in game_state.players
        if player.alive and player.role == SEER
    ]


def get_seer_candidates(game_state, seer):
    return [
        player for player in game_state.players
        if player.alive and player.player_id != seer.player_id
    ]


def get_checked_target_ids(seer, event_log=None):
    checked_target_ids = set()

    for memory_item in getattr(seer, "memory", []):
        if memory_item.get("event_type") != "seer_check":
            continue

        target_id = memory_item.get("content", {}).get("target")
        if target_id is not None:
            checked_target_ids.add(target_id)

    if event_log is None:
        return checked_target_ids

    for event in event_log:
        if event.get("event_type") != "seer_check":
            continue

        content = event.get("content", {})
        if content.get("seer") != seer.player_id:
            continue

        target_id = content.get("target")
        if target_id is not None:
            checked_target_ids.add(target_id)

    return checked_target_ids


def prefer_unchecked_candidates(candidates, checked_target_ids):
    unchecked_candidates = [
        candidate for candidate in candidates
        if candidate.player_id not in checked_target_ids
    ]

    return unchecked_candidates or candidates


def choose_random_target(candidates):
    if not candidates:
        return None

    return random.choice(candidates)


def choose_position_first_target(candidates, checked_target_ids, predicate):
    unchecked_candidates = prefer_unchecked_candidates(
        candidates,
        checked_target_ids,
    )
    preferred_candidates = [
        candidate for candidate in unchecked_candidates
        if predicate(candidate.player_id)
    ]

    if preferred_candidates:
        return choose_random_target(preferred_candidates)

    return choose_random_target(unchecked_candidates)


def choose_opposite_side_target(seer, candidates, checked_target_ids):
    seer_side = getattr(seer, "side", None)

    if seer_side == "left":
        opposite_side = "right"
    elif seer_side == "right":
        opposite_side = "left"
    else:
        return choose_random_target(
            prefer_unchecked_candidates(candidates, checked_target_ids)
        )

    unchecked_candidates = prefer_unchecked_candidates(
        candidates,
        checked_target_ids,
    )
    preferred_candidates = [
        candidate for candidate in unchecked_candidates
        if getattr(candidate, "side", None) == opposite_side
    ]

    if preferred_candidates:
        return choose_random_target(preferred_candidates)

    return choose_random_target(unchecked_candidates)


def choose_scored_target(candidates, checked_target_ids, score_attribute):
    candidate_pool = prefer_unchecked_candidates(
        candidates,
        checked_target_ids,
    )

    if not candidate_pool:
        return None

    highest_score = max(
        getattr(candidate, score_attribute, 0.0)
        for candidate in candidate_pool
    )
    tied_candidates = [
        candidate for candidate in candidate_pool
        if getattr(candidate, score_attribute, 0.0) == highest_score
    ]

    return choose_random_target(tied_candidates)


def choose_seer_check_target(
    game_state,
    seer,
    seer_check_strategy="default",
    event_log=None,
):
    candidates = get_seer_candidates(game_state, seer)

    if not candidates:
        return None

    if seer_check_strategy not in SEER_CHECK_STRATEGIES:
        seer_check_strategy = "default"

    if seer_check_strategy == "default":
        return choose_random_target(candidates)

    checked_target_ids = get_checked_target_ids(seer, event_log=event_log)

    if seer_check_strategy == "random":
        return choose_random_target(
            prefer_unchecked_candidates(candidates, checked_target_ids)
        )

    if seer_check_strategy == "edge_first":
        return choose_position_first_target(
            candidates,
            checked_target_ids,
            is_edge_seat,
        )

    if seer_check_strategy == "inner_first":
        return choose_position_first_target(
            candidates,
            checked_target_ids,
            is_inner_seat,
        )

    if seer_check_strategy == "highest_p_wolf":
        return choose_scored_target(
            candidates,
            checked_target_ids,
            "p_wolf",
        )

    if seer_check_strategy == "highest_suspicion":
        return choose_scored_target(
            candidates,
            checked_target_ids,
            "suspicion_score",
        )

    if seer_check_strategy == "opposite_side":
        return choose_opposite_side_target(
            seer,
            candidates,
            checked_target_ids,
        )

    return choose_random_target(candidates)


def remember_seer_check(seer, event):
    seer.add_memory(
        "seer_check",
        {
            "target": event["target"],
            "target_is_wolf": event["target_is_wolf"],
            "round": event["round"],
            "seer_check_strategy": event["seer_check_strategy"],
        },
    )


def perform_seer_action(
    game_state,
    suspicion_increase=0.25,
    suspicion_decrease=0.10,
    seer_check_strategy="default",
    event_log=None,
):
    alive_seers = get_alive_seers(game_state)

    if not alive_seers:
        return None

    seer = random.choice(alive_seers)
    target = choose_seer_check_target(
        game_state,
        seer,
        seer_check_strategy=seer_check_strategy,
        event_log=event_log,
    )

    if target is None:
        return None

    if target.is_wolf():
        target.update_suspicion(suspicion_increase)
    else:
        target.update_suspicion(-suspicion_decrease)

    event = {
        "type": "seer_check",
        "round": game_state.round_number,
        "seer": seer.player_id,
        "target": target.player_id,
        "target_role": target.role,
        "target_is_wolf": target.is_wolf(),
        "target_suspicion_after": target.suspicion_score,
        "seer_check_strategy": seer_check_strategy,
        "target_side": getattr(target, "side", None),
        "target_seat_type": getattr(target, "seat_type", None),
        "seer_side": getattr(seer, "side", None),
        "seer_seat_type": getattr(seer, "seat_type", None),
    }
    remember_seer_check(seer, event)

    return event


if __name__ == "__main__":
    from player import Player
    from game_state import GameState
    from position_model import assign_positions
    from roles import WEREWOLF, VILLAGER, SEER

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, SEER),
    ]

    assign_positions(players)
    state = GameState(players)

    for _ in range(5):
        event = perform_seer_action(state)
        print(event)

    for player in state.players:
        print(player.player_id, player.role, player.suspicion_score)
