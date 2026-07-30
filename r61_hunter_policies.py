"""R6.1 Hunter shot policies for targeted strategy validation."""

from __future__ import annotations

import random

from roles import HUNTER
from seat_order_neutral import neutral_tie_break_value


R61_HUNTER_POLICIES = [
    "reference",
    "random_shot",
    "no_shot",
    "highest_suspicion",
    "highest_p_wolf",
    "conservative_threshold",
]


def get_hunter(game_state, dead_player_id):
    try:
        hunter = game_state.get_player_by_id(dead_player_id)
    except ValueError:
        return None

    if hunter.role != HUNTER:
        return None

    return hunter


def get_legal_hunter_targets(game_state, hunter):
    return [
        player for player in game_state.players
        if player.alive and player.player_id != hunter.player_id
    ]


def _tie_break(game_state, hunter, player, label):
    if getattr(game_state, "seat_order_neutral_mode", False):
        return neutral_tie_break_value(game_state, label, hunter, player)
    return random.random()


def choose_r61_hunter_shot_target(
    game_state,
    dead_player_id,
    policy_name="reference",
):
    hunter = get_hunter(game_state, dead_player_id)

    if hunter is None:
        return None, None

    candidates = get_legal_hunter_targets(game_state, hunter)
    if not candidates:
        return None, {
            "hunter": hunter.player_id,
            "hunter_policy": policy_name,
            "abstained": True,
            "reason": "no_legal_targets",
        }

    if policy_name == "no_shot":
        return None, {
            "hunter": hunter.player_id,
            "hunter_policy": policy_name,
            "abstained": True,
            "reason": "policy_no_shot",
            "legal_target_count": len(candidates),
        }

    if policy_name == "random_shot":
        target = random.choice(candidates)
    elif policy_name == "highest_p_wolf":
        target = sorted(
            candidates,
            key=lambda player: (
                -getattr(player, "p_wolf", 0.0),
                _tie_break(game_state, hunter, player, "r61_hunter_p_wolf"),
            ),
        )[0]
    elif policy_name == "conservative_threshold":
        eligible = [
            player for player in candidates
            if (
                getattr(player, "suspicion_score", 0.0) >= 0.55
                or getattr(player, "p_wolf", 0.0) >= 0.55
            )
        ]
        if not eligible:
            return None, {
                "hunter": hunter.player_id,
                "hunter_policy": policy_name,
                "abstained": True,
                "reason": "threshold_not_met",
                "legal_target_count": len(candidates),
                "max_suspicion": max(
                    getattr(player, "suspicion_score", 0.0)
                    for player in candidates
                ),
                "max_p_wolf": max(
                    getattr(player, "p_wolf", 0.0)
                    for player in candidates
                ),
            }
        target = sorted(
            eligible,
            key=lambda player: (
                -(
                    getattr(player, "suspicion_score", 0.0)
                    + getattr(player, "p_wolf", 0.0)
                ),
                _tie_break(
                    game_state,
                    hunter,
                    player,
                    "r61_hunter_conservative",
                ),
            ),
        )[0]
    else:
        target = sorted(
            candidates,
            key=lambda player: (
                -getattr(player, "suspicion_score", 0.0),
                _tie_break(
                    game_state,
                    hunter,
                    player,
                    "r61_hunter_suspicion",
                ),
            ),
        )[0]

    return target.player_id, {
        "hunter": hunter.player_id,
        "hunter_policy": policy_name,
        "shot_target": target.player_id,
        "target_role": target.role,
        "target_is_wolf": target.is_wolf(),
        "target_suspicion": target.suspicion_score,
        "target_p_wolf": target.p_wolf,
        "abstained": False,
        "legal_target_count": len(candidates),
    }


def perform_r61_hunter_shot(
    game_state,
    dead_player_id,
    policy_name="reference",
):
    return choose_r61_hunter_shot_target(
        game_state,
        dead_player_id,
        policy_name=policy_name,
    )


if __name__ == "__main__":
    from game_state import GameState
    from player import Player
    from roles import VILLAGER, WEREWOLF

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, HUNTER),
    ]
    players[0].suspicion_score = 0.8
    state = GameState(players)
    state.kill_player(3)
    print(perform_r61_hunter_shot(state, 3, "highest_suspicion"))
