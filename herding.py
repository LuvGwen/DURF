from trust_weighting import calculate_trust_multiplier


SPEECH_HERDING_EFFECTS = {
    "accuse": 0.15,
    "agree": 0.10,
    "question": 0.08,
    "defend": -0.10,
    "trust": -0.12,
}

VOTE_HERDING_EFFECT = 0.08


def calculate_herding_pressure(
    game_state,
    target_player_id,
    recent_speech_events=None,
    recent_votes=None,
    enable_trust_weighted_herding=False,
    trust_herding_min_multiplier=0.4,
    trust_herding_max_multiplier=1.4,
):
    pressure = 0.0

    if recent_speech_events is None:
        recent_speech_events = []

    if recent_votes is None:
        recent_votes = {}

    for event in recent_speech_events:
        if event.get("target") != target_player_id:
            continue

        speech_type = event.get("speech_type")
        base_effect = SPEECH_HERDING_EFFECTS.get(speech_type, 0.0)
        speaker_id = event.get("speaker")
        multiplier = 1.0

        if enable_trust_weighted_herding and speaker_id is not None:
            multiplier = calculate_trust_multiplier(
                game_state,
                speaker_id,
                min_multiplier=trust_herding_min_multiplier,
                max_multiplier=trust_herding_max_multiplier,
            )

        pressure += base_effect * multiplier

    for vote_target_id in recent_votes.values():
        if vote_target_id == target_player_id:
            pressure += VOTE_HERDING_EFFECT

    return max(0.0, min(1.0, pressure))


if __name__ == "__main__":
    from player import Player
    from game_state import GameState
    from roles import WEREWOLF, VILLAGER, SEER

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, SEER),
    ]

    state = GameState(players)

    speech_events = [
        {
            "speaker": 2,
            "speech_type": "accuse",
            "target": 1,
            "text": "I think player 1 is suspicious.",
        },
        {
            "speaker": 3,
            "speech_type": "agree",
            "target": 1,
            "text": "The case against player 1 makes sense.",
        },
        {
            "speaker": 1,
            "speech_type": "defend",
            "target": 1,
            "text": "I do not think player 1 is suspicious.",
        },
    ]

    pressure = calculate_herding_pressure(
        state,
        target_player_id=1,
        recent_speech_events=speech_events,
        enable_trust_weighted_herding=True,
    )

    print("Herding pressure for player 1:", pressure)
