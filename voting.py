import random

from herding import calculate_herding_pressure
from risk_preference import get_risk_multiplier
from role_prior import calculate_role_prior_score
from speaker_memory import get_speaker_trust
from seat_order_neutral import neutral_tie_break_value


def choose_vote_target(
    voter,
    candidates,
    noise_level=0.1,
    recent_speech_events=None,
    recent_votes=None,
    alpha=0.45,
    beta=0.25,
    gamma=0.2,
    delta=0.10,
    game_state=None,
    enable_role_prior=True,
    event_log=None,
    enable_speaker_memory=False,
    speaker_memory_weight=0.15,
    trust_vote_weight=None,
    enable_trust_weighted_herding=False,
    trust_herding_min_multiplier=0.4,
    trust_herding_max_multiplier=1.4,
    enable_risk_preference=False,
):
    if trust_vote_weight is not None:
        speaker_memory_weight = trust_vote_weight

    valid_candidates = [
        candidate for candidate in candidates
        if candidate.alive and candidate.player_id != voter.player_id
    ]

    if not valid_candidates:
        return None

    scored_candidates = []
    for candidate in valid_candidates:
        herding_pressure = 0.0
        role_prior_score = 0.0
        speaker_memory_score = 0.0

        if game_state is not None:
            herding_pressure = calculate_herding_pressure(
                game_state,
                candidate.player_id,
                recent_speech_events=recent_speech_events,
                recent_votes=recent_votes,
                enable_trust_weighted_herding=(
                    enable_trust_weighted_herding
                ),
                trust_herding_min_multiplier=(
                    trust_herding_min_multiplier
                ),
                trust_herding_max_multiplier=(
                    trust_herding_max_multiplier
                ),
            )

        if enable_role_prior and game_state is not None:
            role_prior_score = calculate_role_prior_score(
                game_state,
                candidate.player_id,
                recent_speech_events=recent_speech_events,
                event_log=event_log,
            )

        if enable_speaker_memory:
            speaker_trust = get_speaker_trust(
                voter,
                candidate.player_id,
            )
            speaker_memory_score = 0.5 - speaker_trust

        score = (
            alpha * candidate.suspicion_score
            + beta * candidate.p_wolf
            + gamma * herding_pressure
            + delta * role_prior_score
            + speaker_memory_weight * speaker_memory_score
            + random.uniform(0, noise_level)
        )

        if enable_risk_preference:
            score *= get_risk_multiplier(voter, high_risk=False)

        if getattr(game_state, "seat_order_neutral_mode", False):
            tie_break = neutral_tie_break_value(
                game_state,
                "vote_target_tie",
                voter,
                candidate,
            )
        else:
            tie_break = 0.0

        scored_candidates.append((score, tie_break, candidate))

    if getattr(game_state, "seat_order_neutral_mode", False):
        scored_candidates.sort(key=lambda item: (-item[0], item[1]))
    else:
        scored_candidates.sort(key=lambda item: item[0], reverse=True)

    return scored_candidates[0][2]


if __name__ == "__main__":
    from player import Player
    from roles import WEREWOLF, VILLAGER, SEER

    voter = Player(1, VILLAGER)
    p2 = Player(2, WEREWOLF)
    p3 = Player(3, SEER)

    p2.suspicion_score = 0.8
    p3.suspicion_score = 0.2

    target = choose_vote_target(voter, [voter, p2, p3], noise_level=0.0)

    print("Chosen target:", target.player_id)
