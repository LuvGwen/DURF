from deception_credibility import is_accusation_content


MEMORY_EVENT_TYPE = "speaker_trust"
DEFAULT_TRUST_SCORE = 0.5
MIN_TRUST_SCORE = 0.0
MAX_TRUST_SCORE = 1.0

TRUE_ACCUSATION_TRUST_DELTA = 0.08
WRONG_ACCUSATION_TRUST_DELTA = -0.08
ACCUSATION_COST_TRUST_DELTA = -0.02
SELF_DEFENSE_COST_TRUST_DELTA = -0.03


def clip_trust_score(score):
    return max(MIN_TRUST_SCORE, min(MAX_TRUST_SCORE, score))


def safe_get_player(game_state, player_id):
    try:
        return game_state.get_player_by_id(player_id)
    except ValueError:
        return None


def find_speaker_trust_record(listener, speaker_id):
    for memory_item in listener.memory:
        if memory_item.get("event_type") != MEMORY_EVENT_TYPE:
            continue

        content = memory_item.get("content", {})
        if content.get("speaker_id") == speaker_id:
            return memory_item

    return None


def ensure_speaker_trust_record(
    listener,
    speaker_id,
    initial_trust=DEFAULT_TRUST_SCORE,
):
    record = find_speaker_trust_record(listener, speaker_id)

    if record is not None:
        return record

    record = {
        "event_type": MEMORY_EVENT_TYPE,
        "content": {
            "speaker_id": speaker_id,
            "trust_score": clip_trust_score(initial_trust),
            "observations": 0,
            "positive_updates": 0,
            "negative_updates": 0,
            "last_reason": None,
        },
    }
    listener.memory.append(record)
    return record


def get_speaker_trust(listener, speaker_id, default=DEFAULT_TRUST_SCORE):
    record = find_speaker_trust_record(listener, speaker_id)

    if record is None:
        return default

    return record.get("content", {}).get("trust_score", default)


def update_speaker_trust(listener, speaker_id, delta, reason):
    record = ensure_speaker_trust_record(listener, speaker_id)
    content = record["content"]
    old_score = content["trust_score"]
    new_score = clip_trust_score(old_score + delta)

    content["trust_score"] = new_score
    content["observations"] += 1
    content["last_reason"] = reason

    if delta > 0:
        content["positive_updates"] += 1
    elif delta < 0:
        content["negative_updates"] += 1

    return {
        "listener": listener.player_id,
        "speaker": speaker_id,
        "old_trust": old_score,
        "new_trust": new_score,
        "delta": delta,
        "reason": reason,
    }


def initialize_speaker_memory(players):
    for listener in players:
        for speaker in players:
            if listener.player_id == speaker.player_id:
                continue

            ensure_speaker_trust_record(listener, speaker.player_id)


def update_speaker_trust_for_alive_listeners(
    game_state,
    speaker_id,
    delta,
    reason,
):
    updates = []

    for listener in game_state.get_alive_players():
        if listener.player_id == speaker_id:
            continue

        updates.append(update_speaker_trust(
            listener,
            speaker_id,
            delta,
            reason,
        ))

    return updates


def observe_speech(game_state, speech_content):
    speaker_id = speech_content.get("speaker")

    if speaker_id is None:
        return None

    for listener in game_state.get_alive_players():
        if listener.player_id == speaker_id:
            continue

        ensure_speaker_trust_record(listener, speaker_id)

    return {
        "speaker": speaker_id,
        "listeners": [
            listener.player_id for listener in game_state.get_alive_players()
            if listener.player_id != speaker_id
        ],
    }


def apply_speaker_memory_from_credibility_event(
    game_state,
    event_type,
    content,
):
    if event_type == "accusation_pressure_cost":
        speaker_id = content.get("speaker")
        delta = ACCUSATION_COST_TRUST_DELTA
        reason = "accusation_pressure_cost"
    elif event_type == "self_defense_credibility_cost":
        speaker_id = content.get("speaker")
        delta = SELF_DEFENSE_COST_TRUST_DELTA
        reason = "self_defense_credibility_cost"
    else:
        return None

    if speaker_id is None:
        return None

    updates = update_speaker_trust_for_alive_listeners(
        game_state,
        speaker_id,
        delta,
        reason,
    )

    if not updates:
        return None

    return {
        "source_event_type": event_type,
        "speaker": speaker_id,
        "delta": delta,
        "reason": reason,
        "updates": updates,
    }


def apply_speaker_memory_from_reveal(
    game_state,
    event_log,
    revealed_player_id,
):
    revealed_player = safe_get_player(game_state, revealed_player_id)

    if revealed_player is None:
        return None

    updates = []

    for event in event_log:
        if event.get("event_type") not in {"speech", "last_words"}:
            continue

        content = event.get("content", {})
        if content.get("target") != revealed_player_id:
            continue

        if not is_accusation_content(content):
            continue

        speaker_id = content.get("speaker")
        if speaker_id is None or speaker_id == revealed_player_id:
            continue

        if revealed_player.is_wolf():
            delta = TRUE_ACCUSATION_TRUST_DELTA
            reason = "true_accusation_reveal"
        else:
            delta = WRONG_ACCUSATION_TRUST_DELTA
            reason = "wrong_accusation_reveal"

        updates.extend(update_speaker_trust_for_alive_listeners(
            game_state,
            speaker_id,
            delta,
            reason,
        ))

    if not updates:
        return None

    return {
        "revealed_player": revealed_player_id,
        "revealed_role": revealed_player.role,
        "revealed_is_wolf": revealed_player.is_wolf(),
        "updates": updates,
    }


def get_average_trust_received(game_state, speaker_id):
    trust_scores = [
        get_speaker_trust(listener, speaker_id)
        for listener in game_state.players
        if listener.player_id != speaker_id
    ]

    if not trust_scores:
        return DEFAULT_TRUST_SCORE

    return sum(trust_scores) / len(trust_scores)


def get_average_speaker_trust(game_state):
    trust_scores = []

    for listener in game_state.players:
        for speaker in game_state.players:
            if listener.player_id == speaker.player_id:
                continue

            trust_scores.append(get_speaker_trust(listener, speaker.player_id))

    if not trust_scores:
        return DEFAULT_TRUST_SCORE

    return sum(trust_scores) / len(trust_scores)


def get_average_team_speaker_trust(game_state, team):
    trust_scores = []

    for listener in game_state.players:
        for speaker in game_state.players:
            if listener.player_id == speaker.player_id:
                continue

            if speaker.team != team:
                continue

            trust_scores.append(get_speaker_trust(listener, speaker.player_id))

    if not trust_scores:
        return DEFAULT_TRUST_SCORE

    return sum(trust_scores) / len(trust_scores)


def calculate_trust_speech_multiplier(
    game_state,
    speaker_id,
    min_multiplier=0.5,
    max_multiplier=1.5,
):
    average_trust = get_average_trust_received(game_state, speaker_id)

    return (
        min_multiplier
        + average_trust * (max_multiplier - min_multiplier)
    )


if __name__ == "__main__":
    from game_state import GameState
    from player import Player
    from roles import VILLAGER, WEREWOLF

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, VILLAGER),
    ]
    state = GameState(players)
    initialize_speaker_memory(players)

    speech = {
        "speaker": 1,
        "speech_type": "accuse",
        "deception_type": "false_accuse",
        "target": 2,
    }
    event_log = [{"event_type": "speech", "content": speech}]

    observe_speech(state, speech)
    state.kill_player(2)
    print(apply_speaker_memory_from_reveal(state, event_log, 2))
    print(get_average_trust_received(state, 1))
    print(calculate_trust_speech_multiplier(state, 1))
