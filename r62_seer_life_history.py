"""R6.2 Seer life-history reconstruction utilities."""

from __future__ import annotations

from roles import SEER, VILLAGE_TEAM


PHASE_ORDER = {"night": 0, "day": 1}


def event_time(event):
    return (
        int(event.get("round") or 0),
        PHASE_ORDER.get(event.get("phase"), 0),
    )


def after_or_equal(left, right):
    return event_time(left) >= event_time(right)


def get_seer_player(game):
    seers = [player for player in game.state.players if player.role == SEER]
    return seers[0] if seers else None


def events_for_player(game, event_type, player_id, actor_key=None):
    rows = []
    for event in game.event_log:
        if event.get("event_type") != event_type:
            continue
        content = event.get("content", {})
        if actor_key is None or content.get(actor_key) == player_id:
            rows.append(event)
    return rows


def death_event_for_player(game, player_id):
    for event in game.event_log:
        if event.get("event_type") != "player_death":
            continue
        content = event.get("content", {})
        if content.get("player") == player_id:
            return event
    return None


def first_event(events):
    return events[0] if events else None


def first_wolf_check(check_events):
    for event in check_events:
        if event.get("content", {}).get("target_is_wolf") is True:
            return event
    return None


def count_checks_before(check_events, boundary_event):
    if boundary_event is None:
        return len(check_events)
    return sum(1 for event in check_events if after_or_equal(boundary_event, event))


def count_wolf_checks_before(check_events, boundary_event):
    if boundary_event is None:
        return sum(
            1 for event in check_events
            if event.get("content", {}).get("target_is_wolf") is True
        )
    return sum(
        1 for event in check_events
        if (
            event.get("content", {}).get("target_is_wolf") is True
            and after_or_equal(boundary_event, event)
        )
    )


def phase_index(round_number, phase):
    return int(round_number or 0) * 2 + PHASE_ORDER.get(phase, 0)


def reconstruct_seer_life_history(module, policy, matched_set, game, result):
    seer = get_seer_player(game)
    game_id = f"{module}_{policy}_{matched_set['matched_set_id']}"
    if seer is None:
        return {
            "game_id": game_id,
            "matched_set_id": matched_set["matched_set_id"],
            "seed": matched_set["seed"],
            "regime": matched_set["behavioral_regime"],
            "policy": policy,
            "player_uid": "",
            "reconstructable": False,
            "missing_reason": "seer_not_found",
        }

    seer_id = seer.player_id
    check_events = events_for_player(game, "seer_check", seer_id, "seer")
    reveal_events = events_for_player(game, "seer_reveal", seer_id, "seer")
    first_check = first_event(check_events)
    first_reveal = first_event(reveal_events)
    first_wolf = first_wolf_check(check_events)
    death = death_event_for_player(game, seer_id)
    terminal_round = result["round_number"]
    terminal_phase = game.state.phase

    reveal_round = first_reveal.get("round") if first_reveal else ""
    reveal_phase = first_reveal.get("phase") if first_reveal else ""
    death_round = death.get("round") if death else ""
    death_phase = death.get("phase") if death else ""
    death_cause = death.get("content", {}).get("cause", "") if death else ""
    death_occurred = death is not None
    reveal_occurred = first_reveal is not None

    survived_one = ""
    survived_two = ""
    died_same_round = ""
    died_next_night = ""
    rounds_after = ""
    phases_after = ""
    if reveal_occurred:
        end_round = int(death_round or terminal_round)
        end_phase = death_phase or terminal_phase
        rounds_after = max(0, end_round - int(reveal_round))
        phases_after = max(
            0,
            phase_index(end_round, end_phase)
            - phase_index(reveal_round, reveal_phase),
        )
        survived_one = int(rounds_after >= 1 and not (
            death_occurred
            and int(death_round) == int(reveal_round) + 1
            and death_phase == "night"
        ))
        survived_two = int(rounds_after >= 2)
        died_same_round = int(death_occurred and int(death_round) == int(reveal_round))
        died_next_night = int(
            death_occurred
            and death_cause == "night_kill"
            and int(death_round) == int(reveal_round) + 1
            and death_phase == "night"
        )

    useful_information_event = first_reveal or first_wolf
    useful_information_round = (
        useful_information_event.get("round") if useful_information_event else ""
    )
    useful_before_death = (
        bool(useful_information_event)
        if death is None
        else bool(useful_information_event)
        and after_or_equal(death, useful_information_event)
    )

    return {
        "game_id": game_id,
        "matched_set_id": matched_set["matched_set_id"],
        "seed": matched_set["seed"],
        "regime": matched_set["behavioral_regime"],
        "policy": policy,
        "player_uid": seer_id,
        "reconstructable": True,
        "missing_reason": "",
        "reveal_occurred": int(reveal_occurred),
        "reveal_round": reveal_round,
        "reveal_phase": reveal_phase,
        "first_check_round": first_check.get("round") if first_check else "",
        "first_wolf_found_round": first_wolf.get("round") if first_wolf else "",
        "useful_information_round": useful_information_round,
        "death_occurred": int(death_occurred),
        "death_round": death_round,
        "death_phase": death_phase,
        "death_cause": death_cause,
        "terminal_round": terminal_round,
        "terminal_phase": terminal_phase,
        "alive_at_game_end": int(seer.alive),
        "alive_at_terminal_start": int(seer.alive),
        "survived_one_full_round_after_reveal": survived_one,
        "survived_two_full_rounds_after_reveal": survived_two,
        "died_same_round_as_reveal": died_same_round,
        "died_next_night_after_reveal": died_next_night,
        "rounds_survived_after_reveal": rounds_after,
        "phases_survived_after_reveal": phases_after,
        "checks_completed_before_death": count_checks_before(check_events, death),
        "wolves_found_before_death": count_wolf_checks_before(check_events, death),
        "useful_information_before_death": int(useful_before_death),
        "village_win": int(result["winner"] == VILLAGE_TEAM),
    }


SEER_LIFE_HISTORY_FIELDS = [
    "game_id",
    "matched_set_id",
    "seed",
    "regime",
    "policy",
    "player_uid",
    "reconstructable",
    "missing_reason",
    "reveal_occurred",
    "reveal_round",
    "reveal_phase",
    "first_check_round",
    "first_wolf_found_round",
    "useful_information_round",
    "death_occurred",
    "death_round",
    "death_phase",
    "death_cause",
    "terminal_round",
    "terminal_phase",
    "alive_at_game_end",
    "alive_at_terminal_start",
    "survived_one_full_round_after_reveal",
    "survived_two_full_rounds_after_reveal",
    "died_same_round_as_reveal",
    "died_next_night_after_reveal",
    "rounds_survived_after_reveal",
    "phases_survived_after_reveal",
    "checks_completed_before_death",
    "wolves_found_before_death",
    "useful_information_before_death",
    "village_win",
]
