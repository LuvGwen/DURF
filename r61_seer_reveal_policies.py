"""R6.1 Seer reveal-timing policies."""

from __future__ import annotations

from roles import WOLF_TEAM


R61_SEER_REVEAL_POLICIES = [
    "private_only",
    "immediate_reveal",
    "reveal_first_wolf",
    "delayed_round_2",
    "under_threat",
    "selective_useful_info",
]


def _safe_player(game_state, player_id):
    try:
        return game_state.get_player_by_id(player_id)
    except ValueError:
        return None


def _previous_reveals(event_log, seer_id):
    return [
        event for event in event_log
        if (
            event.get("event_type") == "seer_reveal"
            and event.get("content", {}).get("seer") == seer_id
        )
    ]


def should_reveal_seer_check(game, seer_event, policy_name="private_only"):
    if policy_name == "private_only":
        return False, "private_only"

    seer_id = seer_event.get("seer")
    target_id = seer_event.get("target")
    target_is_wolf = bool(seer_event.get("target_is_wolf"))
    target = _safe_player(game.state, target_id)
    seer = _safe_player(game.state, seer_id)
    prior_reveals = _previous_reveals(game.event_log, seer_id)

    if policy_name == "immediate_reveal":
        return True, "immediate_reveal"

    if policy_name == "reveal_first_wolf":
        return target_is_wolf, "wolf_found" if target_is_wolf else "no_wolf"

    if policy_name == "delayed_round_2":
        return game.state.round_number >= 2, "round_threshold"

    if policy_name == "under_threat":
        if seer is None:
            return False, "seer_not_found"
        pressure = (
            getattr(seer, "suspicion_score", 0.0)
            + getattr(seer, "p_wolf", 0.0)
        ) / 2.0
        return pressure >= 0.35, "seer_under_pressure"

    if policy_name == "selective_useful_info":
        if target is None:
            return False, "target_not_found"
        if target_is_wolf and getattr(target, "p_wolf", 0.0) < 0.65:
            return True, "low_public_wolf_belief"
        if (not target_is_wolf) and len(prior_reveals) >= 1:
            return False, "avoid_excess_village_reveals"
        return False, "not_useful_enough"

    return False, "unknown_policy"


def apply_reveal_belief_effect(game_state, reveal_event):
    target = _safe_player(game_state, reveal_event.get("target"))
    if target is None:
        return

    if reveal_event.get("claimed_target_is_wolf"):
        target.update_suspicion(0.18)
        target.update_p_wolf(0.16)
    else:
        target.update_suspicion(-0.10)
        target.update_p_wolf(-0.12)

    reveal_event["target_suspicion_after_reveal"] = target.suspicion_score
    reveal_event["target_p_wolf_after_reveal"] = target.p_wolf


def maybe_apply_r61_seer_reveal(
    game,
    seer_event,
    policy_name="private_only",
):
    should_reveal, reason = should_reveal_seer_check(
        game,
        seer_event,
        policy_name=policy_name,
    )

    if not should_reveal:
        return None

    target_role = seer_event.get("target_role")
    reveal_event = {
        "seer": seer_event.get("seer"),
        "target": seer_event.get("target"),
        "target_role": target_role,
        "target_is_wolf": bool(seer_event.get("target_is_wolf")),
        "claimed_target_is_wolf": target_role == "werewolf",
        "seer_reveal_policy": policy_name,
        "reveal_reason": reason,
        "round_checked": seer_event.get("round"),
        "round_revealed": game.state.round_number,
        "uses_hidden_information": False,
        "information_source": "prior_seer_check",
        "target_team_after_game": (
            WOLF_TEAM if target_role == "werewolf" else "village"
        ),
    }
    apply_reveal_belief_effect(game.state, reveal_event)
    return reveal_event


if __name__ == "__main__":
    from game import Game
    from player import Player
    from roles import SEER, VILLAGER, WEREWOLF

    game = Game([
        Player(1, WEREWOLF),
        Player(2, SEER),
        Player(3, VILLAGER),
    ])
    event = {
        "seer": 2,
        "target": 1,
        "target_role": WEREWOLF,
        "target_is_wolf": True,
        "round": 1,
    }
    print(maybe_apply_r61_seer_reveal(game, event, "reveal_first_wolf"))
