SPEECH_P_WOLF_EFFECTS = {
    "accuse": 0.10,
    "agree": 0.07,
    "question": 0.05,
    "defend": -0.06,
    "trust": -0.08,
    "claim_role": 0.03,
    "deny": 0.02,
    "neutral": 0.0,
}

SPEECH_SUSPICION_EFFECTS = {
    "accuse": 0.05,
    "agree": 0.035,
    "question": 0.025,
    "defend": -0.03,
    "trust": -0.04,
    "claim_role": 0.015,
    "deny": 0.01,
    "neutral": 0.0,
}

DECEPTION_TO_SPEECH_TYPE = {
    "false_accuse": "accuse",
    "false_defend": "defend",
    "false_role_claim": "claim_role",
    "deflect_suspicion": "question",
    "trust_building": "trust",
}

VOTE_TARGET_P_WOLF_EFFECT = 0.04
SEER_WOLF_P_WOLF_EFFECT = 0.25
SEER_VILLAGE_P_WOLF_EFFECT = -0.15
WITCH_POISON_TARGET_P_WOLF_EFFECT = 0.12
HUNTER_SHOT_TARGET_P_WOLF_EFFECT = 0.12
LAST_WORDS_WEIGHT = 1.20


def safe_get_player(game_state, player_id):
    try:
        return game_state.get_player_by_id(player_id)
    except ValueError:
        return None


def update_p_wolf_for_player(game_state, player_id, delta):
    player = safe_get_player(game_state, player_id)

    if player is None:
        return

    player.update_p_wolf(delta)


def update_suspicion_for_player(game_state, player_id, delta):
    player = safe_get_player(game_state, player_id)

    if player is None:
        return

    player.update_suspicion(delta)


def get_effective_speech_type(speech_content):
    if speech_content.get("speech_type") == "last_words":
        if speech_content.get("target") is not None:
            return "accuse"

        return "neutral"

    deception_type = speech_content.get("deception_type")

    if deception_type in DECEPTION_TO_SPEECH_TYPE:
        return DECEPTION_TO_SPEECH_TYPE[deception_type]

    return speech_content.get("speech_type", "neutral")


def get_trust_speech_multiplier(speech_content):
    try:
        multiplier = float(speech_content.get("trust_speech_multiplier", 1.0))
    except (TypeError, ValueError):
        multiplier = 1.0

    if speech_content.get("speech_type") == "last_words":
        multiplier *= LAST_WORDS_WEIGHT

    return multiplier


def update_belief_from_speech(game_state, speech_content):
    speech_type = get_effective_speech_type(speech_content)
    speaker_id = speech_content.get("speaker")
    target_id = speech_content.get("target")
    multiplier = get_trust_speech_multiplier(speech_content)
    p_wolf_delta = SPEECH_P_WOLF_EFFECTS.get(speech_type, 0.0) * multiplier
    suspicion_delta = (
        SPEECH_SUSPICION_EFFECTS.get(speech_type, 0.0) * multiplier
    )

    if target_id is not None:
        update_p_wolf_for_player(game_state, target_id, p_wolf_delta)
        update_suspicion_for_player(game_state, target_id, suspicion_delta)
        return

    update_p_wolf_for_player(game_state, speaker_id, p_wolf_delta)
    update_suspicion_for_player(game_state, speaker_id, suspicion_delta)


def update_belief_from_vote(game_state, vote_content):
    votes = vote_content.get("votes", {})

    for target_id in votes.values():
        update_p_wolf_for_player(
            game_state,
            target_id,
            VOTE_TARGET_P_WOLF_EFFECT,
        )


def update_belief_from_role_action(game_state, event_type, content):
    if event_type == "seer_check":
        target_id = content.get("target")

        if content.get("target_is_wolf"):
            delta = SEER_WOLF_P_WOLF_EFFECT
        else:
            delta = SEER_VILLAGE_P_WOLF_EFFECT

        update_p_wolf_for_player(game_state, target_id, delta)

    elif event_type == "witch_poison":
        target_id = content.get("poisoned_player")
        update_p_wolf_for_player(
            game_state,
            target_id,
            WITCH_POISON_TARGET_P_WOLF_EFFECT,
        )

    elif event_type == "hunter_shot":
        target_id = content.get("shot_target")
        update_p_wolf_for_player(
            game_state,
            target_id,
            HUNTER_SHOT_TARGET_P_WOLF_EFFECT,
        )


def update_beliefs_from_event(game_state, event):
    event_type = event.get("event_type")
    content = event.get("content", {})

    if event_type in {"speech", "last_words"}:
        update_belief_from_speech(game_state, content)
    elif event_type == "day_vote":
        update_belief_from_vote(game_state, content)
    elif event_type in {"seer_check", "witch_poison", "hunter_shot"}:
        update_belief_from_role_action(game_state, event_type, content)


if __name__ == "__main__":
    from game_state import GameState
    from player import Player
    from roles import SEER, VILLAGER, WEREWOLF

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, SEER),
    ]
    state = GameState(players)

    events = [
        {
            "event_type": "speech",
            "content": {
                "speaker": 2,
                "speech_type": "accuse",
                "target": 1,
            },
        },
        {
            "event_type": "day_vote",
            "content": {
                "votes": {
                    2: 1,
                    3: 1,
                    1: 2,
                },
            },
        },
        {
            "event_type": "seer_check",
            "content": {
                "seer": 3,
                "target": 1,
                "target_is_wolf": True,
            },
        },
    ]

    for event in events:
        update_beliefs_from_event(state, event)

    for player in state.players:
        print(player.player_id, player.role, player.p_wolf)
