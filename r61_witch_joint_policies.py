"""R6.1 Witch joint antidote and poison timing policies."""

from __future__ import annotations

import random

from risk_preference import clamp
from roles import WITCH
from witch_action import perform_witch_poison, perform_witch_save


R61_WITCH_JOINT_POLICIES = [
    "reference",
    "aggressive_full",
    "save_aggressive_poison_conservative",
    "save_conservative_poison_aggressive",
    "conservative_full",
    "risk_balanced",
]


POLICY_PARAMS = {
    "reference": {"save_probability": None, "poison_threshold": None},
    "aggressive_full": {"save_probability": 1.0, "poison_threshold": 0.0},
    "save_aggressive_poison_conservative": {
        "save_probability": 1.0,
        "poison_threshold": 0.65,
    },
    "save_conservative_poison_aggressive": {
        "save_probability": 0.35,
        "poison_threshold": 0.0,
    },
    "conservative_full": {
        "save_probability": 0.35,
        "poison_threshold": 0.65,
    },
    "risk_balanced": {
        "save_probability": 0.70,
        "poison_threshold": 0.35,
    },
}


def _alive_witches(game_state, excluded_witch_ids=None):
    if excluded_witch_ids is None:
        excluded_witch_ids = set()
    return [
        player for player in game_state.players
        if (
            player.alive
            and player.role == WITCH
            and player.player_id not in excluded_witch_ids
        )
    ]


def _policy_params(policy_name):
    return POLICY_PARAMS.get(policy_name, POLICY_PARAMS["reference"])


def perform_r61_witch_save(
    game_state,
    killed_player_id,
    policy_name="reference",
    fallback_save_probability=0.7,
):
    params = _policy_params(policy_name)
    save_probability = params["save_probability"]
    if save_probability is None:
        save_probability = fallback_save_probability

    saved, event = perform_witch_save(
        game_state,
        killed_player_id,
        save_probability=save_probability,
    )
    if event is not None:
        event["witch_joint_policy"] = policy_name
        event["save_probability_used"] = save_probability
    return saved, event


def perform_r61_witch_poison(
    game_state,
    policy_name="reference",
    excluded_witch_ids=None,
    fallback_suspicion_threshold=0.15,
    enable_risk_preference=False,
):
    params = _policy_params(policy_name)
    threshold = params["poison_threshold"]
    if threshold is None:
        threshold = fallback_suspicion_threshold

    if policy_name == "risk_balanced":
        alive_witches = _alive_witches(game_state, excluded_witch_ids)
        if alive_witches:
            witch = random.choice(alive_witches)
            pressure = (
                getattr(witch, "suspicion_score", 0.0)
                + getattr(witch, "p_wolf", 0.0)
            ) / 2.0
            threshold = clamp(0.25 + pressure * 0.30, 0.15, 0.65)

    target_id, event = perform_witch_poison(
        game_state,
        suspicion_threshold=threshold,
        excluded_witch_ids=excluded_witch_ids,
        enable_risk_preference=enable_risk_preference,
    )
    if event is not None:
        event["witch_joint_policy"] = policy_name
        event["poison_threshold_used"] = threshold
    return target_id, event


if __name__ == "__main__":
    from game_state import GameState
    from player import Player
    from roles import VILLAGER, WEREWOLF

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, WITCH),
    ]
    players[0].suspicion_score = 0.8
    state = GameState(players)
    print(perform_r61_witch_save(state, 2, "aggressive_full"))
    print(perform_r61_witch_poison(
        state,
        "aggressive_full",
        excluded_witch_ids={3},
    ))
