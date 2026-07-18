ACCUSATION_SPEECH_TYPES = {"accuse", "last_words"}
ACCUSATION_DECEPTION_TYPES = {"false_accuse"}
SELF_DEFENSE_DECEPTION_TYPES = {"deflect_suspicion"}
TRUST_BUILDING_DECEPTION_TYPES = {"trust_building"}

DEFAULT_FREE_ACCUSATIONS = 1
DEFAULT_REPEAT_SUSPICION_COST = 0.015
DEFAULT_REPEAT_P_WOLF_COST = 0.015
DEFAULT_FALSE_ACCUSATION_BASE_SUSPICION_COST = 0.005
DEFAULT_FALSE_ACCUSATION_BASE_P_WOLF_COST = 0.005
DEFAULT_WRONG_ACCUSATION_SUSPICION_PENALTY = 0.04
DEFAULT_WRONG_ACCUSATION_P_WOLF_PENALTY = 0.04
DEFAULT_SELF_DEFENSE_MAX_ROUNDS_BACK = 2
DEFAULT_FREE_SELF_DEFENSES = 1
DEFAULT_REPEAT_SELF_DEFENSE_SUSPICION_COST = 0.02
DEFAULT_REPEAT_SELF_DEFENSE_P_WOLF_COST = 0.02
DEFAULT_FREE_TRUST_BUILDING = 1
DEFAULT_REPEAT_TRUST_BUILDING_SUSPICION_COST = 0.01
DEFAULT_REPEAT_TRUST_BUILDING_P_WOLF_COST = 0.01


def safe_get_player(game_state, player_id):
    try:
        return game_state.get_player_by_id(player_id)
    except ValueError:
        return None


def is_accusation_content(content):
    return (
        content.get("speech_type") in ACCUSATION_SPEECH_TYPES
        or content.get("deception_type") in ACCUSATION_DECEPTION_TYPES
    )


def is_self_defense_content(content):
    return content.get("deception_type") in SELF_DEFENSE_DECEPTION_TYPES


def is_trust_building_content(content):
    return content.get("deception_type") in TRUST_BUILDING_DECEPTION_TYPES


def get_latest_round(event_log):
    rounds = [
        event.get("round", 0)
        for event in event_log
        if event.get("round") is not None
    ]

    if not rounds:
        return 0

    return max(rounds)


def is_recent_event(event, latest_round, max_rounds_back):
    event_round = event.get("round", latest_round)
    return event_round >= latest_round - max_rounds_back


def count_accusations_by_speaker(event_log, speaker_id):
    accusation_count = 0

    for event in event_log:
        if event.get("event_type") != "speech":
            continue

        content = event.get("content", {})

        if content.get("speaker") != speaker_id:
            continue

        if is_accusation_content(content):
            accusation_count += 1

    return accusation_count


def count_recent_self_defenses(event_log, speaker_id, max_rounds_back=2):
    latest_round = get_latest_round(event_log)
    self_defense_count = 0

    for event in event_log:
        if event.get("event_type") != "speech":
            continue

        if not is_recent_event(event, latest_round, max_rounds_back):
            continue

        content = event.get("content", {})

        if content.get("speaker") != speaker_id:
            continue

        if is_self_defense_content(content):
            self_defense_count += 1

    return self_defense_count


def count_recent_trust_building(event_log, speaker_id, max_rounds_back=2):
    latest_round = get_latest_round(event_log)
    trust_building_count = 0

    for event in event_log:
        if event.get("event_type") != "speech":
            continue

        if not is_recent_event(event, latest_round, max_rounds_back):
            continue

        content = event.get("content", {})

        if content.get("speaker") != speaker_id:
            continue

        if is_trust_building_content(content):
            trust_building_count += 1

    return trust_building_count


def apply_accusation_pressure_cost(
    game_state,
    speech_content,
    event_log,
    free_accusations=DEFAULT_FREE_ACCUSATIONS,
    repeat_suspicion_cost=DEFAULT_REPEAT_SUSPICION_COST,
    repeat_p_wolf_cost=DEFAULT_REPEAT_P_WOLF_COST,
    false_accusation_base_suspicion_cost=(
        DEFAULT_FALSE_ACCUSATION_BASE_SUSPICION_COST
    ),
    false_accusation_base_p_wolf_cost=(
        DEFAULT_FALSE_ACCUSATION_BASE_P_WOLF_COST
    ),
):
    if not is_accusation_content(speech_content):
        return None

    speaker_id = speech_content.get("speaker")
    speaker = safe_get_player(game_state, speaker_id)

    if speaker is None or not speaker.alive:
        return None

    accusation_count = count_accusations_by_speaker(event_log, speaker_id)
    repeat_count = max(0, accusation_count - free_accusations)
    suspicion_delta = repeat_count * repeat_suspicion_cost
    p_wolf_delta = repeat_count * repeat_p_wolf_cost

    if speech_content.get("deception_type") == "false_accuse":
        suspicion_delta += false_accusation_base_suspicion_cost
        p_wolf_delta += false_accusation_base_p_wolf_cost

    if suspicion_delta <= 0.0 and p_wolf_delta <= 0.0:
        return None

    speaker.update_suspicion(suspicion_delta)
    speaker.update_p_wolf(p_wolf_delta)

    return {
        "speaker": speaker_id,
        "target": speech_content.get("target"),
        "speech_type": speech_content.get("speech_type"),
        "deception_type": speech_content.get("deception_type"),
        "accusation_count": accusation_count,
        "suspicion_delta": suspicion_delta,
        "p_wolf_delta": p_wolf_delta,
        "speaker_suspicion_after": speaker.suspicion_score,
        "speaker_p_wolf_after": speaker.p_wolf,
    }


def apply_self_defense_credibility_cost(
    game_state,
    speech_content,
    event_log,
    max_rounds_back=DEFAULT_SELF_DEFENSE_MAX_ROUNDS_BACK,
    free_self_defenses=DEFAULT_FREE_SELF_DEFENSES,
    repeat_self_defense_suspicion_cost=(
        DEFAULT_REPEAT_SELF_DEFENSE_SUSPICION_COST
    ),
    repeat_self_defense_p_wolf_cost=DEFAULT_REPEAT_SELF_DEFENSE_P_WOLF_COST,
    free_trust_building=DEFAULT_FREE_TRUST_BUILDING,
    repeat_trust_building_suspicion_cost=(
        DEFAULT_REPEAT_TRUST_BUILDING_SUSPICION_COST
    ),
    repeat_trust_building_p_wolf_cost=(
        DEFAULT_REPEAT_TRUST_BUILDING_P_WOLF_COST
    ),
):
    if (
        not is_self_defense_content(speech_content)
        and not is_trust_building_content(speech_content)
    ):
        return None

    speaker_id = speech_content.get("speaker")
    speaker = safe_get_player(game_state, speaker_id)

    if speaker is None or not speaker.alive:
        return None

    self_defense_count = count_recent_self_defenses(
        event_log,
        speaker_id,
        max_rounds_back=max_rounds_back,
    )
    trust_building_count = count_recent_trust_building(
        event_log,
        speaker_id,
        max_rounds_back=max_rounds_back,
    )
    suspicion_delta = 0.0
    p_wolf_delta = 0.0
    cost_type = None

    if is_self_defense_content(speech_content):
        repeat_count = max(0, self_defense_count - free_self_defenses)
        suspicion_delta = repeat_count * repeat_self_defense_suspicion_cost
        p_wolf_delta = repeat_count * repeat_self_defense_p_wolf_cost
        cost_type = "repeated_self_defense"

    elif is_trust_building_content(speech_content):
        repeat_count = max(0, trust_building_count - free_trust_building)
        suspicion_delta = repeat_count * repeat_trust_building_suspicion_cost
        p_wolf_delta = repeat_count * repeat_trust_building_p_wolf_cost
        cost_type = "excessive_trust_building"

    if suspicion_delta <= 0.0 and p_wolf_delta <= 0.0:
        return None

    speaker.update_suspicion(suspicion_delta)
    speaker.update_p_wolf(p_wolf_delta)

    return {
        "speaker": speaker_id,
        "target": speech_content.get("target"),
        "speech_type": speech_content.get("speech_type"),
        "deception_type": speech_content.get("deception_type"),
        "cost_type": cost_type,
        "recent_self_defenses": self_defense_count,
        "recent_trust_building": trust_building_count,
        "max_rounds_back": max_rounds_back,
        "suspicion_delta": suspicion_delta,
        "p_wolf_delta": p_wolf_delta,
        "speaker_suspicion_after": speaker.suspicion_score,
        "speaker_p_wolf_after": speaker.p_wolf,
    }


def apply_wrong_accusation_penalties(
    game_state,
    event_log,
    revealed_player_id,
    suspicion_penalty=DEFAULT_WRONG_ACCUSATION_SUSPICION_PENALTY,
    p_wolf_penalty=DEFAULT_WRONG_ACCUSATION_P_WOLF_PENALTY,
):
    revealed_player = safe_get_player(game_state, revealed_player_id)

    if revealed_player is None or revealed_player.is_wolf():
        return None

    penalties = []

    for event in event_log:
        if event.get("event_type") != "speech":
            continue

        content = event.get("content", {})

        if content.get("target") != revealed_player_id:
            continue

        if not is_accusation_content(content):
            continue

        speaker_id = content.get("speaker")

        if speaker_id == revealed_player_id:
            continue

        speaker = safe_get_player(game_state, speaker_id)

        if speaker is None or not speaker.alive:
            continue

        speaker.update_suspicion(suspicion_penalty)
        speaker.update_p_wolf(p_wolf_penalty)
        penalties.append({
            "speaker": speaker_id,
            "accused_player": revealed_player_id,
            "accused_role": revealed_player.role,
            "speech_type": content.get("speech_type"),
            "deception_type": content.get("deception_type"),
            "suspicion_delta": suspicion_penalty,
            "p_wolf_delta": p_wolf_penalty,
            "speaker_suspicion_after": speaker.suspicion_score,
            "speaker_p_wolf_after": speaker.p_wolf,
        })

    if not penalties:
        return None

    return {
        "revealed_player": revealed_player_id,
        "revealed_role": revealed_player.role,
        "revealed_is_wolf": revealed_player.is_wolf(),
        "penalties": penalties,
    }


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
    speech = {
        "speaker": 1,
        "speech_type": "accuse",
        "deception_type": "false_accuse",
        "target": 2,
    }
    event_log = [{"event_type": "speech", "content": speech}]

    print(apply_accusation_pressure_cost(state, speech, event_log))
    defense = {
        "speaker": 1,
        "speech_type": "question",
        "deception_type": "deflect_suspicion",
        "target": 3,
    }
    event_log.extend([
        {"round": 1, "event_type": "speech", "content": defense},
        {"round": 2, "event_type": "speech", "content": defense},
    ])
    print(apply_self_defense_credibility_cost(state, defense, event_log))
    state.kill_player(2)
    print(apply_wrong_accusation_penalties(state, event_log, 2))
    print(players[0].to_dict())
