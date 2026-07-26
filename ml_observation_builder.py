import hashlib
import json
from collections import Counter, defaultdict

from belief_update import (
    HUNTER_SHOT_TARGET_P_WOLF_EFFECT,
    SEER_VILLAGE_P_WOLF_EFFECT,
    SEER_WOLF_P_WOLF_EFFECT,
    SPEECH_P_WOLF_EFFECTS,
    SPEECH_SUSPICION_EFFECTS,
    VOTE_TARGET_P_WOLF_EFFECT,
    WITCH_POISON_TARGET_P_WOLF_EFFECT,
    get_effective_speech_type,
    get_trust_speech_multiplier,
)
from position_model import get_seat_type, get_side
from roles import HUNTER, SEER, WITCH, WOLF_TEAM, get_team
from seat_order_neutral import get_actor_uid, get_physical_seat
from seer_action import circular_seat_distance, get_coverage_bonus


DEFAULT_INITIAL_P_WOLF = 0.3
SPECIAL_ROLES = {SEER, WITCH, HUNTER}
ACCUSATION_TYPES = {"accuse", "question"}
DEFENSE_TYPES = {"defend", "deny"}


def stable_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def stable_hash(value):
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def player_by_actor_uid(game_state):
    return {
        get_actor_uid(player): player
        for player in game_state.players
    }


def player_by_displayed_id(game_state):
    return {
        player.player_id: player
        for player in game_state.players
    }


def displayed_to_actor_map(game_state):
    return {
        player.player_id: get_actor_uid(player)
        for player in game_state.players
    }


def actor_to_displayed_map(game_state):
    return {
        get_actor_uid(player): player.player_id
        for player in game_state.players
    }


def clip01(value):
    return max(0.0, min(1.0, float(value)))


def safe_int(value, default=0):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def event_content(event):
    return event.get("content", {}) if event else {}


def is_accusation_speech(content):
    speech_type = get_effective_speech_type(content)
    return (
        speech_type in ACCUSATION_TYPES
        or content.get("deception_type") == "false_accuse"
        or (
            content.get("speech_type") == "last_words"
            and content.get("target") is not None
        )
    )


def is_defense_speech(content):
    speech_type = get_effective_speech_type(content)
    return (
        speech_type in DEFENSE_TYPES
        or content.get("deception_type") == "deflect_suspicion"
    )


def compute_score_state(players, past_events, initial_p_wolf=DEFAULT_INITIAL_P_WOLF):
    suspicion = {player.player_id: 0.0 for player in players}
    p_wolf = {player.player_id: initial_p_wolf for player in players}

    def update_suspicion(player_id, delta):
        if player_id in suspicion:
            suspicion[player_id] = clip01(suspicion[player_id] + delta)

    def update_p_wolf(player_id, delta):
        if player_id in p_wolf:
            p_wolf[player_id] = clip01(p_wolf[player_id] + delta)

    for event in past_events:
        content = event_content(event)
        event_type = event.get("event_type")

        if event_type in {"speech", "last_words"}:
            speech_type = get_effective_speech_type(content)
            target_id = content.get("target")
            speaker_id = content.get("speaker")
            multiplier = get_trust_speech_multiplier(content)
            p_delta = SPEECH_P_WOLF_EFFECTS.get(speech_type, 0.0) * multiplier
            s_delta = SPEECH_SUSPICION_EFFECTS.get(speech_type, 0.0) * multiplier
            affected_id = target_id if target_id is not None else speaker_id
            update_p_wolf(affected_id, p_delta)
            update_suspicion(affected_id, s_delta)
        elif event_type == "day_vote":
            for target_id in content.get("votes", {}).values():
                update_p_wolf(safe_int(target_id), VOTE_TARGET_P_WOLF_EFFECT)
        elif event_type == "seer_check":
            target_id = content.get("target")
            if content.get("target_is_wolf"):
                update_p_wolf(target_id, SEER_WOLF_P_WOLF_EFFECT)
                update_suspicion(target_id, 0.25)
            else:
                update_p_wolf(target_id, SEER_VILLAGE_P_WOLF_EFFECT)
                update_suspicion(target_id, -0.10)
        elif event_type == "witch_poison":
            update_p_wolf(
                content.get("poisoned_player"),
                WITCH_POISON_TARGET_P_WOLF_EFFECT,
            )
        elif event_type == "hunter_shot":
            update_p_wolf(
                content.get("shot_target"),
                HUNTER_SHOT_TARGET_P_WOLF_EFFECT,
            )
        elif event_type in {
            "accusation_pressure_cost",
            "self_defense_credibility_cost",
        }:
            speaker_id = content.get("speaker")
            update_suspicion(
                speaker_id,
                content.get("suspicion_delta", content.get("delta", 0.0)),
            )
            update_p_wolf(
                speaker_id,
                content.get("p_wolf_delta", content.get("delta", 0.0)),
            )
        elif event_type == "wrong_accusation_penalty":
            for penalty in content.get("penalties", []):
                speaker_id = penalty.get("speaker")
                update_suspicion(
                    speaker_id,
                    penalty.get("suspicion_delta", 0.0),
                )
                update_p_wolf(
                    speaker_id,
                    penalty.get("p_wolf_delta", 0.0),
                )

    return {
        "suspicion": suspicion,
        "p_wolf": p_wolf,
    }


def previous_death_count(past_events):
    return sum(
        1 for event in past_events
        if event.get("event_type") == "player_death"
    )


def event_history_counts(game_state, past_events):
    displayed_to_actor = displayed_to_actor_map(game_state)
    speech_count = Counter()
    made_accusations = Counter()
    received_accusations = Counter()
    defense_count = Counter()
    role_claim_count = Counter()
    vote_made = Counter()
    vote_received = Counter()
    vote_switch_count = Counter()
    wrong_accusation_count = Counter()
    conflict_pairs = Counter()
    support_pairs = Counter()
    last_vote_target_by_voter = {}

    for event in past_events:
        content = event_content(event)
        event_type = event.get("event_type")

        if event_type in {"speech", "last_words"}:
            speaker_id = content.get("speaker")
            target_id = content.get("target")
            speaker_uid = displayed_to_actor.get(safe_int(speaker_id))
            target_uid = (
                displayed_to_actor.get(safe_int(target_id))
                if target_id is not None
                else None
            )
            if speaker_uid is None:
                continue
            speech_count[speaker_uid] += 1
            if is_accusation_speech(content):
                made_accusations[speaker_uid] += 1
                if target_uid is not None:
                    received_accusations[target_uid] += 1
                    conflict_pairs[(speaker_uid, target_uid)] += 1
                    conflict_pairs[(target_uid, speaker_uid)] += 1
            if is_defense_speech(content):
                defense_count[speaker_uid] += 1
            if get_effective_speech_type(content) == "claim_role":
                role_claim_count[speaker_uid] += 1
            if get_effective_speech_type(content) in {"trust", "defend"}:
                if target_uid is not None:
                    support_pairs[(speaker_uid, target_uid)] += 1
                    support_pairs[(target_uid, speaker_uid)] += 1
        elif event_type == "day_vote":
            for voter_id, target_id in content.get("votes", {}).items():
                voter_uid = displayed_to_actor.get(safe_int(voter_id))
                target_uid = displayed_to_actor.get(safe_int(target_id))
                if voter_uid is None or target_uid is None:
                    continue
                vote_made[voter_uid] += 1
                vote_received[target_uid] += 1
                if (
                    voter_uid in last_vote_target_by_voter
                    and last_vote_target_by_voter[voter_uid] != target_uid
                ):
                    vote_switch_count[voter_uid] += 1
                last_vote_target_by_voter[voter_uid] = target_uid
        elif event_type == "wrong_accusation_penalty":
            for penalty in content.get("penalties", []):
                speaker_uid = displayed_to_actor.get(
                    safe_int(penalty.get("speaker"))
                )
                if speaker_uid is not None:
                    wrong_accusation_count[speaker_uid] += 1

    return {
        "speech_count": speech_count,
        "made_accusations": made_accusations,
        "received_accusations": received_accusations,
        "defense_count": defense_count,
        "role_claim_count": role_claim_count,
        "vote_made": vote_made,
        "vote_received": vote_received,
        "vote_switch_count": vote_switch_count,
        "wrong_accusation_count": wrong_accusation_count,
        "conflict_pairs": conflict_pairs,
        "support_pairs": support_pairs,
    }


def speaker_trust_from_past_events(game_state, listener_uid, speaker_uid, past_events):
    actor_to_displayed = actor_to_displayed_map(game_state)
    listener_id = actor_to_displayed.get(listener_uid)
    speaker_id = actor_to_displayed.get(speaker_uid)
    trust = 0.5

    if listener_id is None or speaker_id is None:
        return trust

    for event in past_events:
        if event.get("event_type") != "speaker_trust_update":
            continue
        updates = event_content(event).get("updates", [])
        for update in updates:
            if (
                safe_int(update.get("listener")) == listener_id
                and safe_int(update.get("speaker")) == speaker_id
            ):
                trust = float(update.get("new_trust", trust))
    return trust


def seer_private_check_status(game_state, actor_uid, candidate_uid, past_events):
    actor_map = actor_to_displayed_map(game_state)
    seer_id = actor_map.get(actor_uid)
    candidate_id = actor_map.get(candidate_uid)
    status = 0

    for event in past_events:
        if event.get("event_type") != "seer_check":
            continue
        content = event_content(event)
        if (
            content.get("seer_actor_uid") != actor_uid
            and content.get("seer") != seer_id
        ):
            continue
        if (
            content.get("target_actor_uid") != candidate_uid
            and content.get("target") != candidate_id
        ):
            continue
        status = 1 if content.get("target_is_wolf") else -1
    return status


def checked_target_uids_for_actor(game_state, actor_uid, past_events):
    checked = []
    actor_map = actor_to_displayed_map(game_state)
    seer_id = actor_map.get(actor_uid)
    displayed_to_actor = displayed_to_actor_map(game_state)
    for event in past_events:
        if event.get("event_type") != "seer_check":
            continue
        content = event_content(event)
        if (
            content.get("seer_actor_uid") != actor_uid
            and content.get("seer") != seer_id
        ):
            continue
        target_uid = content.get("target_actor_uid")
        if target_uid is None:
            target_uid = displayed_to_actor.get(safe_int(content.get("target")))
        if target_uid is not None:
            checked.append(target_uid)
    return checked


def known_information_for_actor(
    game_state,
    actor,
    candidate,
    past_events,
):
    status = seer_private_check_status(
        game_state,
        get_actor_uid(actor),
        get_actor_uid(candidate),
        past_events,
    )
    known_wolf = 1 if status == 1 else 0
    known_village = 1 if status == -1 else 0

    if actor.team == WOLF_TEAM and candidate.team == WOLF_TEAM:
        known_wolf = 1

    return known_wolf, known_village


def build_actor_observation(
    game_state,
    actor_uid,
    decision_type,
    current_round,
    current_phase,
    game_id="",
    seed=None,
    base_game_index=None,
    event_log=None,
    event_index=None,
    alive_actor_uids=None,
    current_votes=None,
    initial_p_wolf=DEFAULT_INITIAL_P_WOLF,
):
    if event_log is None:
        event_log = []
    if event_index is None:
        event_index = len(event_log)
    past_events = list(event_log[:event_index])
    actor_map = player_by_actor_uid(game_state)
    actor = actor_map.get(actor_uid)
    if actor is None:
        raise ValueError(f"Unknown actor_uid: {actor_uid}")
    if alive_actor_uids is None:
        alive_actor_uids = {
            get_actor_uid(player)
            for player in game_state.players
            if player.alive
        }
    if current_votes is None:
        current_votes = {}

    scores = compute_score_state(
        game_state.players,
        past_events,
        initial_p_wolf=initial_p_wolf,
    )
    counts = event_history_counts(game_state, past_events)
    p_values = list(scores["p_wolf"].values())
    entropy_proxy = (
        sum(min(value, 1.0 - value) for value in p_values) / len(p_values)
        if p_values
        else 0.0
    )
    actor_displayed_id = actor.player_id
    actor_role = actor.role
    actor_team = actor.team
    known_teammates = 0
    if actor_team == WOLF_TEAM:
        known_teammates = sum(
            1 for player in game_state.players
            if (
                get_actor_uid(player) in alive_actor_uids
                and get_actor_uid(player) != actor_uid
                and player.team == WOLF_TEAM
            )
        )

    risk = getattr(actor, "risk_preference", "neutral")
    observation = {
        "observation_id": stable_hash({
            "game_id": game_id,
            "event_index": event_index,
            "round": current_round,
            "phase": current_phase,
            "decision_type": decision_type,
            "actor_uid": actor_uid,
            "alive_actor_uids": sorted(alive_actor_uids, key=str),
            "current_votes": current_votes,
        }),
        "game_id": game_id,
        "seed": seed,
        "base_game_index": base_game_index,
        "round_number": current_round,
        "phase": current_phase,
        "decision_type": decision_type,
        "actor_uid": actor_uid,
        "actor_displayed_id": actor_displayed_id,
        "actor_team": actor_team,
        "actor_role_if_self_known": actor_role,
        "round_number": current_round,
        "phase_is_night": 1 if current_phase == "night" else 0,
        "phase_is_day": 1 if current_phase == "day" else 0,
        "actor_team_is_wolf": 1 if actor_team == WOLF_TEAM else 0,
        "actor_team_is_village": 1 if actor_team != WOLF_TEAM else 0,
        "alive_count": len(alive_actor_uids),
        "dead_count": len(game_state.players) - len(alive_actor_uids),
        "public_revealed_role_count": previous_death_count(past_events),
        "public_information_entropy_proxy": entropy_proxy,
        "number_of_public_check_results": 0,
        "number_of_previous_eliminations": previous_death_count(past_events),
        "actor_suspicion_score": scores["suspicion"].get(
            actor_displayed_id,
            0.0,
        ),
        "actor_p_wolf": scores["p_wolf"].get(
            actor_displayed_id,
            initial_p_wolf,
        ),
        "actor_risk_conservative": 1 if risk == "conservative" else 0,
        "actor_risk_aggressive": 1 if risk == "aggressive" else 0,
        "actor_previous_votes_made": counts["vote_made"][actor_uid],
        "actor_previous_speeches_made": counts["speech_count"][actor_uid],
        "actor_known_teammate_count": known_teammates,
        "current_vote_total": len(current_votes),
        "past_events": past_events,
        "score_state": scores,
        "history_counts": counts,
        "alive_actor_uids": set(alive_actor_uids),
        "current_votes": dict(current_votes),
        "initial_p_wolf": initial_p_wolf,
    }
    return observation


def build_candidate_feature_row(observation, game_state, candidate_uid):
    actor_uid = observation["actor_uid"]
    actor = player_by_actor_uid(game_state)[actor_uid]
    candidate = player_by_actor_uid(game_state)[candidate_uid]
    candidate_id = candidate.player_id
    actor_id = actor.player_id
    past_events = observation["past_events"]
    scores = observation["score_state"]
    counts = observation["history_counts"]
    alive_actor_uids = observation["alive_actor_uids"]
    current_votes = observation.get("current_votes", {})
    current_vote_count = sum(
        1 for target_uid in current_votes.values()
        if target_uid == candidate_uid
    )
    checked_status = seer_private_check_status(
        game_state,
        actor_uid,
        candidate_uid,
        past_events,
    )
    known_wolf, known_village = known_information_for_actor(
        game_state,
        actor,
        candidate,
        past_events,
    )
    checked_uids = checked_target_uids_for_actor(
        game_state,
        actor_uid,
        past_events,
    ) if observation["decision_type"] == "seer_check" else []
    candidate_suspicion = scores["suspicion"].get(candidate_id, 0.0)
    candidate_p_wolf = scores["p_wolf"].get(
        candidate_id,
        observation["initial_p_wolf"],
    )
    support = counts["support_pairs"][(actor_uid, candidate_uid)]
    conflict = counts["conflict_pairs"][(actor_uid, candidate_uid)]
    candidate_physical_seat = get_physical_seat(candidate)
    actor_physical_seat = get_physical_seat(actor)
    search_coverage_bonus = 0.0
    if observation["decision_type"] != "seer_check":
        search_coverage_bonus = 0.0
    elif checked_uids:
        checked_displayed_ids = [
            player_by_actor_uid(game_state)[uid].player_id
            for uid in checked_uids
            if uid in player_by_actor_uid(game_state)
        ]
        if checked_displayed_ids:
            nearest_distance = min(
                circular_seat_distance(candidate_id, checked_id)
                for checked_id in checked_displayed_ids
            )
            search_coverage_bonus = nearest_distance / 5.0
    else:
        try:
            search_coverage_bonus = get_coverage_bonus(
                actor,
                candidate,
                set(),
            )
        except Exception:
            search_coverage_bonus = 0.0
    previously_targeted = 1 if (
        counts["conflict_pairs"][(actor_uid, candidate_uid)]
        or candidate_uid in checked_uids
        or any(
            voter == actor_uid and target == candidate_uid
            for voter, target in current_votes.items()
        )
    ) else 0

    row = {
        "round_number": observation["round_number"],
        "phase_is_night": observation["phase_is_night"],
        "phase_is_day": observation["phase_is_day"],
        "decision_type_is_seer_check": (
            1 if observation["decision_type"] == "seer_check" else 0
        ),
        "decision_type_is_wolf_kill": (
            1 if observation["decision_type"] == "wolf_kill" else 0
        ),
        "decision_type_is_day_vote": (
            1 if observation["decision_type"] == "day_vote" else 0
        ),
        "actor_team_is_wolf": observation["actor_team_is_wolf"],
        "actor_team_is_village": observation["actor_team_is_village"],
        "alive_count": observation["alive_count"],
        "dead_count": observation["dead_count"],
        "public_revealed_role_count": observation[
            "public_revealed_role_count"
        ],
        "public_information_entropy_proxy": observation[
            "public_information_entropy_proxy"
        ],
        "number_of_public_check_results": observation[
            "number_of_public_check_results"
        ],
        "number_of_previous_eliminations": observation[
            "number_of_previous_eliminations"
        ],
        "actor_suspicion_score": observation["actor_suspicion_score"],
        "actor_p_wolf": observation["actor_p_wolf"],
        "actor_risk_conservative": observation["actor_risk_conservative"],
        "actor_risk_aggressive": observation["actor_risk_aggressive"],
        "actor_previous_votes_made": observation[
            "actor_previous_votes_made"
        ],
        "actor_previous_speeches_made": observation[
            "actor_previous_speeches_made"
        ],
        "actor_known_teammate_count": observation[
            "actor_known_teammate_count"
        ],
        "candidate_alive": 1 if candidate_uid in alive_actor_uids else 0,
        "candidate_checked_by_actor_status": checked_status,
        "candidate_public_role_known": 0,
        "candidate_suspicion_score": candidate_suspicion,
        "candidate_p_wolf": candidate_p_wolf,
        "candidate_received_accusations": counts[
            "received_accusations"
        ][candidate_uid],
        "candidate_made_accusations": counts[
            "made_accusations"
        ][candidate_uid],
        "candidate_wrong_accusation_count": counts[
            "wrong_accusation_count"
        ][candidate_uid],
        "candidate_vote_received_count": counts[
            "vote_received"
        ][candidate_uid],
        "candidate_vote_made_count": counts["vote_made"][candidate_uid],
        "candidate_vote_switch_count": counts[
            "vote_switch_count"
        ][candidate_uid],
        "candidate_speech_count": counts["speech_count"][candidate_uid],
        "candidate_defense_count": counts["defense_count"][candidate_uid],
        "candidate_role_claim_count": counts[
            "role_claim_count"
        ][candidate_uid],
        "candidate_special_role_claim_count": counts[
            "role_claim_count"
        ][candidate_uid],
        "candidate_trust_from_actor": speaker_trust_from_past_events(
            game_state,
            actor_uid,
            candidate_uid,
            past_events,
        ),
        "candidate_conflict_with_actor": conflict,
        "candidate_support_from_actor": support,
        "candidate_public_influence_proxy": (
            counts["speech_count"][candidate_uid]
            + 0.5 * counts["vote_received"][candidate_uid]
        ),
        "candidate_physical_seat_numeric": candidate_physical_seat,
        "candidate_seat_is_edge": (
            1 if get_seat_type(candidate_physical_seat) == "edge" else 0
        ),
        "candidate_side_is_left": (
            1 if get_side(candidate_physical_seat) == "left" else 0
        ),
        "candidate_distance_from_actor": circular_seat_distance(
            actor_physical_seat,
            candidate_physical_seat,
        ),
        "candidate_search_coverage_bonus": search_coverage_bonus,
        "candidate_was_previously_targeted_by_actor": previously_targeted,
        "candidate_known_wolf_to_actor": known_wolf,
        "candidate_known_village_to_actor": known_village,
        "candidate_current_vote_count": current_vote_count,
        "current_vote_total": observation["current_vote_total"],
        "candidate_uncertainty_proxy": min(
            candidate_p_wolf,
            1.0 - candidate_p_wolf,
        ),
        "candidate_survival_proxy": (
            1.0
            if candidate_uid in alive_actor_uids
            else 0.0
        ) + 0.25 * (1.0 - candidate_suspicion) + 0.25 * (
            1.0 - candidate_p_wolf
        ),
    }
    return row


def minimal_observation_for_serialization(observation):
    omitted = {
        "past_events",
        "score_state",
        "history_counts",
        "alive_actor_uids",
        "current_votes",
    }
    return {
        key: value
        for key, value in observation.items()
        if key not in omitted
    }


def assert_observation_is_safe(observation):
    serialized = stable_json(minimal_observation_for_serialization(observation))
    prohibited_tokens = [
        "true_candidate_role_label",
        "eventual_winner_label",
        "future_votes",
        "future_speech",
        "future_deaths",
    ]
    for token in prohibited_tokens:
        if token in serialized:
            raise AssertionError(f"Unsafe observation token found: {token}")
    return True
