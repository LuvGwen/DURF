from roles import WEREWOLF


def safe_get_player(game_state, player_id):
    try:
        return game_state.get_player_by_id(player_id)
    except ValueError:
        return None


def calculate_role_prior_score(
    game_state,
    target_player_id,
    recent_speech_events=None,
    event_log=None,
):
    target = safe_get_player(game_state, target_player_id)

    if target is None:
        return 0.0

    if recent_speech_events is None:
        recent_speech_events = []

    if event_log is None:
        event_log = []

    score = 0.0

    for speech_event in recent_speech_events:
        if speech_event.get("speaker") != target_player_id:
            continue

        speech_type = speech_event.get("speech_type")

        if speech_type == "claim_role":
            if target.role == WEREWOLF:
                score += 0.10
            else:
                score -= 0.05
        elif speech_type == "deny":
            score += 0.03

    for event in event_log:
        event_type = event.get("event_type")
        content = event.get("content", {})

        if event_type == "seer_check":
            if content.get("target") != target_player_id:
                continue

            if content.get("target_is_wolf"):
                score += 0.25
            else:
                score -= 0.20

        elif event_type == "witch_poison":
            if content.get("poisoned_player") == target_player_id:
                score += 0.10

        elif event_type == "hunter_shot":
            if content.get("shot_target") == target_player_id:
                score += 0.10

    return max(0.0, min(1.0, score))


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
            "speaker": 1,
            "speech_type": "deny",
            "target": None,
            "text": "I deny being a wolf.",
        },
        {
            "speaker": 3,
            "speech_type": "claim_role",
            "target": None,
            "text": "My role is seer.",
        },
    ]

    event_log = [
        {
            "event_type": "seer_check",
            "content": {
                "target": 1,
                "target_is_wolf": True,
            },
        }
    ]

    print("Player 1 role prior:", calculate_role_prior_score(
        state,
        1,
        recent_speech_events=speech_events,
        event_log=event_log,
    ))

    print("Player 3 role prior:", calculate_role_prior_score(
        state,
        3,
        recent_speech_events=speech_events,
        event_log=event_log,
    ))
