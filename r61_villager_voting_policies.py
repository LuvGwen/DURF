"""R6.1 Villager-owned voting policies."""

from __future__ import annotations

import random

from voting import choose_vote_target


R61_VILLAGER_VOTING_POLICIES = [
    "reference",
    "random_vote",
    "suspicion_only",
    "p_wolf_only",
    "trust_weighted",
    "guarded_herding",
]


def _valid_candidates(voter, candidates):
    return [
        candidate for candidate in candidates
        if candidate.alive and candidate.player_id != voter.player_id
    ]


def choose_r61_villager_vote_target(
    voter,
    candidates,
    game_state,
    policy_name="reference",
    recent_speech_events=None,
    event_log=None,
    speaker_memory_weight=0.20,
    enable_risk_preference=False,
):
    valid_candidates = _valid_candidates(voter, candidates)
    if not valid_candidates:
        return None

    if policy_name == "random_vote":
        return random.choice(valid_candidates)

    if policy_name == "suspicion_only":
        return choose_vote_target(
            voter,
            candidates,
            game_state=game_state,
            recent_speech_events=recent_speech_events,
            event_log=event_log,
            alpha=1.0,
            beta=0.0,
            gamma=0.0,
            delta=0.0,
            enable_role_prior=False,
            enable_speaker_memory=False,
            enable_risk_preference=enable_risk_preference,
        )

    if policy_name == "p_wolf_only":
        return choose_vote_target(
            voter,
            candidates,
            game_state=game_state,
            recent_speech_events=recent_speech_events,
            event_log=event_log,
            alpha=0.0,
            beta=1.0,
            gamma=0.0,
            delta=0.0,
            enable_role_prior=False,
            enable_speaker_memory=False,
            enable_risk_preference=enable_risk_preference,
        )

    if policy_name == "trust_weighted":
        return choose_vote_target(
            voter,
            candidates,
            game_state=game_state,
            recent_speech_events=recent_speech_events,
            event_log=event_log,
            alpha=0.35,
            beta=0.30,
            gamma=0.0,
            delta=0.05,
            enable_role_prior=True,
            enable_speaker_memory=True,
            speaker_memory_weight=max(speaker_memory_weight, 0.30),
            enable_risk_preference=enable_risk_preference,
        )

    if policy_name == "guarded_herding":
        return choose_vote_target(
            voter,
            candidates,
            game_state=game_state,
            recent_speech_events=recent_speech_events,
            event_log=event_log,
            alpha=0.35,
            beta=0.30,
            gamma=0.15,
            delta=0.05,
            enable_role_prior=True,
            enable_speaker_memory=True,
            speaker_memory_weight=max(speaker_memory_weight, 0.20),
            enable_trust_weighted_herding=True,
            trust_herding_min_multiplier=0.3,
            trust_herding_max_multiplier=1.2,
            enable_risk_preference=enable_risk_preference,
        )

    return choose_vote_target(
        voter,
        candidates,
        game_state=game_state,
        recent_speech_events=recent_speech_events,
        event_log=event_log,
        enable_speaker_memory=True,
        speaker_memory_weight=speaker_memory_weight,
        enable_role_prior=True,
        enable_risk_preference=enable_risk_preference,
    )


if __name__ == "__main__":
    from game_state import GameState
    from player import Player
    from roles import VILLAGER, WEREWOLF

    players = [
        Player(1, VILLAGER),
        Player(2, WEREWOLF),
        Player(3, VILLAGER),
    ]
    players[1].p_wolf = 0.8
    state = GameState(players)
    print(choose_r61_villager_vote_target(
        players[0],
        players,
        state,
        "p_wolf_only",
    ).player_id)
