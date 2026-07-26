import csv
import random
from pathlib import Path

from ml_feature_registry import FEATURE_COLUMNS, LABEL_COLUMNS
from ml_observation_builder import (
    actor_to_displayed_map,
    build_actor_observation,
    build_candidate_feature_row,
    checked_target_uids_for_actor,
    displayed_to_actor_map,
    player_by_actor_uid,
    safe_int,
    stable_hash,
)
from roles import HUNTER, SEER, WITCH, WOLF_TEAM
from seat_order_neutral import get_actor_uid


DECISION_TYPES = {"seer_check", "wolf_kill", "day_vote"}
SPECIAL_ROLES = {SEER, WITCH, HUNTER}
TRAIN_SEEDS = {42, 43, 44}
VALIDATION_SEEDS = {45}
TEST_SEEDS = {46}


COMMON_ID_COLUMNS = [
    "decision_id",
    "observation_id",
    "game_id",
    "seed",
    "base_game_index",
    "round",
    "phase",
    "decision_type",
    "actor_uid",
    "actor_team",
    "actor_role_if_self_known",
    "candidate_uid",
    "action_legal",
    "action_selected_by_existing_policy",
    "existing_policy_name",
    "selected_candidate_uid",
    "dataset_split",
    "split_group_id",
]


LABEL_FIELD_COLUMNS = [
    "true_candidate_role_label",
    "candidate_is_wolf_label",
    "candidate_is_special_label",
    "check_target_is_wolf",
    "vote_target_is_wolf_label",
    "eventual_winner_label",
    "actor_team_win_label",
]


DECISION_DATASET_FIELDNAMES = (
    COMMON_ID_COLUMNS + FEATURE_COLUMNS + LABEL_FIELD_COLUMNS
)


def split_for_seed(seed):
    try:
        seed = int(seed)
    except (TypeError, ValueError):
        seed = None

    if seed in TRAIN_SEEDS:
        return "train"
    if seed in VALIDATION_SEEDS:
        return "validation"
    if seed in TEST_SEEDS:
        return "test"
    return "train"


def safe_event_content(event):
    return event.get("content", {}) if event else {}


def event_round_phase(event):
    return (event.get("round"), event.get("phase"))


def filtered_past_events_for_decision(event_log, event_index, event):
    past_events = list(event_log[:event_index])
    round_phase = event_round_phase(event)

    if event.get("event_type") in {"night_kill", "night_kill_prevented"}:
        excluded = {
            "witch_save",
            "night_kill",
            "night_kill_prevented",
            "player_death",
            "hunter_shot",
            "last_words",
            "witch_poison",
        }
    elif event.get("event_type") == "day_vote":
        excluded = {
            "player_death",
            "hunter_shot",
            "last_words",
        }
    else:
        excluded = set()

    if not excluded:
        return past_events

    return [
        past_event for past_event in past_events
        if not (
            event_round_phase(past_event) == round_phase
            and past_event.get("event_type") in excluded
        )
    ]


def sort_actor_uids(actor_uids):
    return sorted(actor_uids, key=lambda value: str(value))


def build_decision_id(game_id, event_index, decision_type, actor_uid):
    return stable_hash({
        "game_id": game_id,
        "event_index": event_index,
        "decision_type": decision_type,
        "actor_uid": actor_uid,
    })


def choose_existing_policy_name(game, decision_type):
    if decision_type == "seer_check":
        return getattr(game, "seer_check_strategy", "default")
    if decision_type == "wolf_kill":
        return getattr(game, "wolf_kill_strategy", "random")
    if decision_type == "day_vote":
        return "suspicion_based" if game.use_suspicion_voting else "random"
    return "unknown"


def actor_team_for_decision(game_state, actor_uid):
    if actor_uid == "wolf_team":
        return WOLF_TEAM
    actor = player_by_actor_uid(game_state).get(actor_uid)
    return actor.team if actor is not None else ""


def actor_role_for_decision(game_state, actor_uid):
    if actor_uid == "wolf_team":
        return "werewolf_team"
    actor = player_by_actor_uid(game_state).get(actor_uid)
    return actor.role if actor is not None else ""


def candidate_labels(game_state, candidate_uid):
    candidate = player_by_actor_uid(game_state)[candidate_uid]
    return {
        "true_candidate_role_label": candidate.role,
        "candidate_is_wolf_label": 1 if candidate.is_wolf() else 0,
        "candidate_is_special_label": 1 if candidate.role in SPECIAL_ROLES else 0,
    }


def actor_team_win_label(game_state, actor_team):
    if game_state.winner == "draw":
        return 0
    return 1 if actor_team == game_state.winner else 0


def legal_seer_candidates(game_state, seer_uid, alive_actor_uids, past_events):
    checked = set(checked_target_uids_for_actor(game_state, seer_uid, past_events))
    return [
        uid for uid in alive_actor_uids
        if uid != seer_uid and uid not in checked
    ]


def legal_wolf_kill_candidates(game_state, alive_actor_uids):
    actors = player_by_actor_uid(game_state)
    return [
        uid for uid in alive_actor_uids
        if uid in actors and not actors[uid].is_wolf()
    ]


def legal_vote_candidates(voter_uid, alive_actor_uids):
    return [
        uid for uid in alive_actor_uids
        if uid != voter_uid
    ]


def selected_sampled_candidates(
    decision_id,
    selected_uid,
    candidate_feature_rows,
    max_candidates=None,
):
    if max_candidates is None or len(candidate_feature_rows) <= max_candidates:
        return candidate_feature_rows

    by_uid = {
        row["candidate_uid"]: row
        for row in candidate_feature_rows
    }
    selected = []

    def include(uid):
        if uid in by_uid and uid not in selected:
            selected.append(uid)

    include(selected_uid)
    for uid, _ in sorted(
        (
            (row["candidate_uid"], row["candidate_p_wolf"])
            for row in candidate_feature_rows
        ),
        key=lambda item: (-float(item[1]), str(item[0])),
    )[:1]:
        include(uid)
    for uid, _ in sorted(
        (
            (row["candidate_uid"], row["candidate_suspicion_score"])
            for row in candidate_feature_rows
        ),
        key=lambda item: (-float(item[1]), str(item[0])),
    )[:1]:
        include(uid)
    for uid, _ in sorted(
        (
            (row["candidate_uid"], row["candidate_uncertainty_proxy"])
            for row in candidate_feature_rows
        ),
        key=lambda item: (-float(item[1]), str(item[0])),
    )[:1]:
        include(uid)

    remaining = [
        row["candidate_uid"] for row in candidate_feature_rows
        if row["candidate_uid"] not in selected
    ]
    rng = random.Random(stable_hash({"decision_id": decision_id, "sample": True}))
    rng.shuffle(remaining)
    for uid in remaining:
        if len(selected) >= max_candidates:
            break
        include(uid)

    return [by_uid[uid] for uid in selected]


def build_candidate_rows_for_decision(
    game,
    game_id,
    seed,
    base_game_index,
    event_index,
    event,
    decision_type,
    actor_uid,
    selected_candidate_uid,
    legal_candidate_uids,
    alive_actor_uids,
    current_votes=None,
    max_candidates=None,
    initial_p_wolf=0.3,
):
    decision_id = build_decision_id(
        game_id,
        event_index,
        decision_type,
        actor_uid,
    )
    past_events = filtered_past_events_for_decision(
        game.event_log,
        event_index,
        event,
    )
    observation = build_actor_observation(
        game.state,
        actor_uid,
        decision_type,
        event.get("round"),
        event.get("phase"),
        game_id=game_id,
        seed=seed,
        base_game_index=base_game_index,
        event_log=past_events,
        event_index=len(past_events),
        alive_actor_uids=set(alive_actor_uids),
        current_votes=current_votes or {},
        initial_p_wolf=initial_p_wolf,
    )
    actor_team = actor_team_for_decision(game.state, actor_uid)
    actor_role = actor_role_for_decision(game.state, actor_uid)
    split = split_for_seed(seed)
    split_group_id = f"seed_{seed}_game_{base_game_index}"
    existing_policy_name = choose_existing_policy_name(game, decision_type)
    full_candidate_rows = []

    for candidate_uid in sort_actor_uids(legal_candidate_uids):
        feature_values = build_candidate_feature_row(
            observation,
            game.state,
            candidate_uid,
        )
        feature_values["candidate_uid"] = candidate_uid
        full_candidate_rows.append(feature_values)

    candidate_rows = selected_sampled_candidates(
        decision_id,
        selected_candidate_uid,
        full_candidate_rows,
        max_candidates=max_candidates,
    )
    rows = []
    for feature_values in candidate_rows:
        candidate_uid = feature_values.pop("candidate_uid")
        labels = candidate_labels(game.state, candidate_uid)
        row = {
            "decision_id": decision_id,
            "observation_id": observation["observation_id"],
            "game_id": game_id,
            "seed": seed,
            "base_game_index": base_game_index,
            "round": event.get("round"),
            "phase": event.get("phase"),
            "decision_type": decision_type,
            "actor_uid": actor_uid,
            "actor_team": actor_team,
            "actor_role_if_self_known": actor_role,
            "candidate_uid": candidate_uid,
            "action_legal": 1,
            "action_selected_by_existing_policy": (
                1 if candidate_uid == selected_candidate_uid else 0
            ),
            "existing_policy_name": existing_policy_name,
            "selected_candidate_uid": selected_candidate_uid,
            "dataset_split": split,
            "split_group_id": split_group_id,
            **feature_values,
            **labels,
            "check_target_is_wolf": labels["candidate_is_wolf_label"],
            "vote_target_is_wolf_label": labels["candidate_is_wolf_label"],
            "eventual_winner_label": game.state.winner,
            "actor_team_win_label": actor_team_win_label(
                game.state,
                actor_team,
            ),
        }
        rows.append(row)
    return rows


def extract_decision_rows_from_game(
    game,
    game_id,
    seed,
    base_game_index,
    max_candidates=None,
    initial_p_wolf=0.3,
):
    displayed_to_actor = displayed_to_actor_map(game.state)
    actor_to_displayed = actor_to_displayed_map(game.state)
    alive_actor_uids = {
        get_actor_uid(player)
        for player in game.state.players
    }
    current_phase_key = None
    phase_alive_actor_uids = set(alive_actor_uids)
    rows = []

    for event_index, event in enumerate(game.event_log):
        if event_round_phase(event) != current_phase_key:
            current_phase_key = event_round_phase(event)
            phase_alive_actor_uids = set(alive_actor_uids)

        content = safe_event_content(event)
        event_type = event.get("event_type")

        if event_type == "seer_check":
            actor_uid = content.get("seer_actor_uid")
            if actor_uid is None:
                actor_uid = displayed_to_actor.get(content.get("seer"))
            selected_uid = content.get("target_actor_uid")
            if selected_uid is None:
                selected_uid = displayed_to_actor.get(content.get("target"))
            legal_uids = legal_seer_candidates(
                game.state,
                actor_uid,
                phase_alive_actor_uids,
                filtered_past_events_for_decision(
                    game.event_log,
                    event_index,
                    event,
                ),
            )
            if selected_uid is not None and selected_uid not in legal_uids:
                legal_uids.append(selected_uid)
            rows.extend(build_candidate_rows_for_decision(
                game,
                game_id,
                seed,
                base_game_index,
                event_index,
                event,
                "seer_check",
                actor_uid,
                selected_uid,
                legal_uids,
                phase_alive_actor_uids,
                max_candidates=max_candidates,
                initial_p_wolf=initial_p_wolf,
            ))
        elif event_type in {"night_kill", "night_kill_prevented"}:
            selected_uid = displayed_to_actor.get(content.get("target"))
            alive_wolf_uids = [
                uid for uid in phase_alive_actor_uids
                if (
                    uid in player_by_actor_uid(game.state)
                    and player_by_actor_uid(game.state)[uid].is_wolf()
                )
            ]
            actor_uid = sort_actor_uids(alive_wolf_uids)[0] if alive_wolf_uids else None
            if actor_uid is not None:
                legal_uids = legal_wolf_kill_candidates(
                    game.state,
                    phase_alive_actor_uids,
                )
                if selected_uid is not None and selected_uid not in legal_uids:
                    legal_uids.append(selected_uid)
                rows.extend(build_candidate_rows_for_decision(
                    game,
                    game_id,
                    seed,
                    base_game_index,
                    event_index,
                    event,
                    "wolf_kill",
                    actor_uid,
                    selected_uid,
                    legal_uids,
                    phase_alive_actor_uids,
                    max_candidates=max_candidates,
                    initial_p_wolf=initial_p_wolf,
                ))
        elif event_type == "day_vote":
            votes_by_actor_uid = content.get("votes_by_actor_uid")
            if not votes_by_actor_uid:
                votes_by_actor_uid = {
                    displayed_to_actor.get(safe_int(safe_voter)): displayed_to_actor.get(
                        safe_int(safe_target)
                    )
                    for safe_voter, safe_target in content.get("votes", {}).items()
                }
            current_votes = {}
            for voter_uid, selected_uid in votes_by_actor_uid.items():
                voter_uid = int(voter_uid) if str(voter_uid).isdigit() else voter_uid
                selected_uid = (
                    int(selected_uid)
                    if str(selected_uid).isdigit()
                    else selected_uid
                )
                legal_uids = legal_vote_candidates(
                    voter_uid,
                    phase_alive_actor_uids,
                )
                if selected_uid is not None and selected_uid not in legal_uids:
                    legal_uids.append(selected_uid)
                rows.extend(build_candidate_rows_for_decision(
                    game,
                    game_id,
                    seed,
                    base_game_index,
                    event_index,
                    event,
                    "day_vote",
                    voter_uid,
                    selected_uid,
                    legal_uids,
                    phase_alive_actor_uids,
                    current_votes=current_votes,
                    max_candidates=max_candidates,
                    initial_p_wolf=initial_p_wolf,
                ))
                current_votes[voter_uid] = selected_uid

        if event_type == "player_death":
            player_id = content.get("player")
            uid = displayed_to_actor.get(player_id)
            if uid is not None:
                alive_actor_uids.discard(uid)

    return rows


def split_rows_by_decision_type(rows):
    grouped = {decision_type: [] for decision_type in DECISION_TYPES}
    for row in rows:
        grouped.setdefault(row["decision_type"], []).append(row)
    return grouped


def write_csv_rows(path, rows, fieldnames=None):
    if fieldnames is None:
        fieldnames = DECISION_DATASET_FIELDNAMES
    Path(path).parent.mkdir(exist_ok=True, parents=True)
    with Path(path).open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            restval="",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def validate_decision_rows(rows):
    errors = []
    for row in rows:
        if row["decision_type"] not in DECISION_TYPES:
            errors.append(f"Invalid decision_type {row['decision_type']}")
        if int(row.get("action_legal", 0)) != 1:
            errors.append(f"Illegal row found {row.get('decision_id')}")
        if row["candidate_uid"] == row["actor_uid"]:
            errors.append(f"Self-target row found {row.get('decision_id')}")
        if row["candidate_is_wolf_label"] not in {0, 1}:
            errors.append(f"Invalid wolf label {row.get('decision_id')}")
    for label_column in LABEL_COLUMNS:
        if label_column in FEATURE_COLUMNS:
            errors.append(f"Label appears in features: {label_column}")
    return {
        "row_count": len(rows),
        "decision_count": len({row["decision_id"] for row in rows}),
        "valid": not errors,
        "errors": errors,
    }
