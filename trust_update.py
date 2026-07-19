from speaker_memory import (
    ensure_speaker_trust_record,
    get_speaker_trust,
    safe_get_player,
    update_speaker_trust,
)


ACCUSATION_SPEECH_TYPES = {"accuse", "question", "last_words"}
DEFENSE_SPEECH_TYPES = {"defend", "trust"}
FALSE_ACCUSATION_DECEPTION_TYPES = {"false_accuse"}
FALSE_DEFENSE_DECEPTION_TYPES = {"false_defend"}

CORRECT_ACCUSATION_TRUST_DELTA = 0.08
WRONG_ACCUSATION_TRUST_DELTA = -0.10
WRONG_DEFENSE_TRUST_DELTA = -0.08
CORRECT_DEFENSE_TRUST_DELTA = 0.06


def coerce_player_id(player_id):
    try:
        return int(player_id)
    except (TypeError, ValueError):
        return player_id


def normalize_speech_event(speech_event):
    if speech_event.get("event_type") == "speech":
        return speech_event.get("content", {})

    return speech_event


def is_accusation_speech(speech_event):
    speech_type = speech_event.get("speech_type")
    deception_type = speech_event.get("deception_type")

    return (
        speech_type in ACCUSATION_SPEECH_TYPES
        or deception_type in FALSE_ACCUSATION_DECEPTION_TYPES
        or (
            speech_event.get("is_deception") is True
            and deception_type in FALSE_ACCUSATION_DECEPTION_TYPES
        )
    )


def is_defense_speech(speech_event):
    speech_type = speech_event.get("speech_type")
    deception_type = speech_event.get("deception_type")

    return (
        speech_type in DEFENSE_SPEECH_TYPES
        or deception_type in FALSE_DEFENSE_DECEPTION_TYPES
        or (
            speech_event.get("is_deception") is True
            and deception_type in FALSE_DEFENSE_DECEPTION_TYPES
        )
    )


def update_trust_score(observer, speaker_id, delta, players=None, reason=None):
    ensure_speaker_trust_record(observer, speaker_id)
    update_speaker_trust(
        observer,
        speaker_id,
        delta,
        reason or "vote_outcome",
    )
    return get_speaker_trust(observer, speaker_id)


def update_trust_from_vote_outcome(
    game_state,
    speech_events,
    eliminated_id,
):
    eliminated_id = coerce_player_id(eliminated_id)
    eliminated_player = safe_get_player(game_state, eliminated_id)

    if eliminated_player is None:
        return []

    trust_events = []

    for speech_event in speech_events:
        content = normalize_speech_event(speech_event)
        target_id = content.get("target")

        if target_id is None:
            continue

        target_id = coerce_player_id(target_id)

        if target_id != eliminated_id:
            continue

        speaker_id = coerce_player_id(content.get("speaker"))

        if speaker_id is None:
            continue

        if is_accusation_speech(content):
            if eliminated_player.is_wolf():
                delta = CORRECT_ACCUSATION_TRUST_DELTA
                reason = "correct_accusation"
            else:
                delta = WRONG_ACCUSATION_TRUST_DELTA
                reason = "wrong_accusation"

        elif is_defense_speech(content):
            if eliminated_player.is_wolf():
                delta = WRONG_DEFENSE_TRUST_DELTA
                reason = "wrong_defense"
            else:
                delta = CORRECT_DEFENSE_TRUST_DELTA
                reason = "correct_defense"

        else:
            continue

        for observer in game_state.get_alive_players():
            if observer.player_id == speaker_id:
                continue

            new_score = update_trust_score(
                observer,
                speaker_id,
                delta,
                game_state.players,
                reason=reason,
            )

            trust_events.append({
                "observer": observer.player_id,
                "speaker": speaker_id,
                "target": eliminated_id,
                "delta": delta,
                "reason": reason,
                "trust_after": new_score,
            })

    return trust_events


if __name__ == "__main__":
    from player import Player
    from game_state import GameState
    from roles import WEREWOLF, VILLAGER, SEER

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, VILLAGER),
        Player(4, SEER),
    ]

    state = GameState(players)

    speech_events = [
        {
            "speaker": 2,
            "speech_type": "accuse",
            "target": 1,
        },
        {
            "speaker": 1,
            "speech_type": "accuse",
            "deception_type": "false_accuse",
            "is_deception": True,
            "target": 3,
        },
        {
            "speaker": 4,
            "speech_type": "defend",
            "target": 3,
        },
    ]

    print("Correct accusation outcome:")
    events1 = update_trust_from_vote_outcome(
        state,
        speech_events,
        eliminated_id=1,
    )
    print(events1)

    print("Wrong accusation / correct defense outcome:")
    events2 = update_trust_from_vote_outcome(
        state,
        speech_events,
        eliminated_id=3,
    )
    print(events2)

    for player in players:
        print(player.player_id, player.memory)
