import math
import random
from collections import defaultdict

import game as game_module
import seer_action as seer_action_module

from config import DEFAULT_MAX_ROUNDS
from ml_counterfactual_rollout import evaluate_candidate_action
from ml_full_state_snapshot import clone_game_from_snapshot
from roles import HUNTER, SEER, WITCH, WOLF_TEAM
from seat_order_neutral import get_actor_uid, stable_seed


SPECIAL_ROLES = {SEER, WITCH, HUNTER}


class FullRolloutError(ValueError):
    pass


def get_player_by_actor_uid(game_state, actor_uid):
    for player in game_state.players:
        if get_actor_uid(player) == actor_uid:
            return player
    raise FullRolloutError(f"Unknown actor_uid: {actor_uid}")


def legal_candidate_uids(game, decision_type, actor_uid):
    alive = [
        player for player in game.state.players
        if player.alive
    ]
    if decision_type == "seer_check":
        return [
            get_actor_uid(player)
            for player in alive
            if get_actor_uid(player) != actor_uid
        ]
    if decision_type == "wolf_kill":
        return [
            get_actor_uid(player)
            for player in alive
            if not player.is_wolf()
        ]
    if decision_type == "day_vote":
        return [
            get_actor_uid(player)
            for player in alive
            if get_actor_uid(player) != actor_uid
        ]
    raise FullRolloutError(f"Unsupported decision_type: {decision_type}")


def apply_continuation_policy(game, policy):
    for field, value in policy.get("config_updates", {}).items():
        if hasattr(game, field):
            setattr(game, field, value)
        if field in {
            "seat_order_neutral_mode",
            "neutral_seed",
            "base_game_index",
            "label_condition",
        }:
            setattr(game.state, field, value)


def finish_current_phase_and_continue(game, max_rounds=DEFAULT_MAX_ROUNDS):
    if game.state.game_over:
        return

    if game.state.phase == "night":
        game.state.switch_phase()
        game.day_phase()
        if not game.state.game_over:
            game.state.switch_phase()
            game.state.reset_turn_actions()
    elif game.state.phase == "day":
        if not game.state.game_over:
            game.state.switch_phase()
            game.state.reset_turn_actions()

    while not game.state.game_over and game.state.round_number <= max_rounds:
        game.run_one_round()

    if not game.state.game_over:
        game.state.game_over = True
        game.state.winner = "draw"


def force_seer_check(game, actor_uid, candidate_uid):
    candidate = get_player_by_actor_uid(game.state, candidate_uid)
    original_choose = seer_action_module.choose_seer_check_target

    def forced_choose(game_state, seer, *args, **kwargs):
        if get_actor_uid(seer) != actor_uid:
            return original_choose(game_state, seer, *args, **kwargs)
        if not candidate.alive or get_actor_uid(candidate) == actor_uid:
            raise FullRolloutError("Forced seer target is illegal.")
        return candidate

    seer_action_module.choose_seer_check_target = forced_choose
    try:
        game.night_phase()
    finally:
        seer_action_module.choose_seer_check_target = original_choose


def force_wolf_kill(game, candidate_uid):
    candidate = get_player_by_actor_uid(game.state, candidate_uid)
    original_choose = game_module.choose_wolf_kill_target
    original_enable_seer = game.enable_seer

    def forced_choose(game_state, *args, **kwargs):
        if not candidate.alive or candidate.is_wolf():
            raise FullRolloutError("Forced wolf-kill target is illegal.")
        return candidate

    game_module.choose_wolf_kill_target = forced_choose
    game.enable_seer = False
    try:
        game.night_phase()
    finally:
        game.enable_seer = original_enable_seer
        game_module.choose_wolf_kill_target = original_choose


def force_day_vote(game, actor_uid, candidate_uid):
    candidate = get_player_by_actor_uid(game.state, candidate_uid)
    original_choose = game_module.choose_vote_target
    original_use_suspicion_voting = game.use_suspicion_voting

    def forced_choose(voter, candidates, *args, **kwargs):
        if get_actor_uid(voter) != actor_uid:
            return original_choose(voter, candidates, *args, **kwargs)
        if not candidate.alive or get_actor_uid(candidate) == actor_uid:
            raise FullRolloutError("Forced vote target is illegal.")
        return candidate

    game_module.choose_vote_target = forced_choose
    game.use_suspicion_voting = True
    try:
        game.day_phase()
    finally:
        game.use_suspicion_voting = original_use_suspicion_voting
        game_module.choose_vote_target = original_choose


def summarize_forced_rollout(game, decision_type, actor_uid, candidate_uid):
    candidate = get_player_by_actor_uid(game.state, candidate_uid)
    actor_team = (
        WOLF_TEAM
        if decision_type == "wolf_kill"
        else get_player_by_actor_uid(game.state, actor_uid).team
    )
    winner = game.state.winner
    team_win = 1 if winner == actor_team else 0
    seer_checks = [
        event for event in game.event_log
        if event.get("event_type") == "seer_check"
    ]
    checked_wolves = [
        event for event in seer_checks
        if event.get("content", {}).get("target_is_wolf") is True
    ]
    witch_save = any(
        event.get("event_type") == "witch_save"
        for event in game.event_log
    )
    hunter_retaliation = any(
        event.get("event_type") == "hunter_shot"
        for event in game.event_log
    )
    day_votes = [
        event for event in game.event_log
        if event.get("event_type") == "day_vote"
    ]
    eliminated_role = ""
    forced_vote_contributed = 0
    if day_votes:
        final_vote = day_votes[-1].get("content", {})
        eliminated = final_vote.get("eliminated")
        if eliminated is not None:
            try:
                eliminated_role = game.state.get_player_by_id(
                    eliminated
                ).role
            except ValueError:
                eliminated_role = ""
        votes_by_actor_uid = final_vote.get("votes_by_actor_uid", {})
        forced_vote_contributed = 1 if (
            str(votes_by_actor_uid.get(str(actor_uid), ""))
            == str(eliminated)
            or votes_by_actor_uid.get(actor_uid) == eliminated
        ) else 0

    return {
        "full_rollout_winner": winner,
        "full_rollout_team_win": team_win,
        "full_rollout_village_win": 1 if winner == "village" else 0,
        "full_rollout_wolf_win": 1 if winner == "wolf" else 0,
        "full_rollout_total_rounds": game.state.round_number,
        "full_rollout_target_role": candidate.role,
        "full_rollout_target_is_wolf": 1 if candidate.is_wolf() else 0,
        "full_rollout_target_is_special": (
            1 if candidate.role in SPECIAL_ROLES else 0
        ),
        "full_rollout_witch_save_occurred": 1 if witch_save else 0,
        "full_rollout_hunter_retaliation_occurred": (
            1 if hunter_retaliation else 0
        ),
        "full_rollout_found_wolf_by_check_2": (
            1 if any(
                event.get("content", {}).get("target_is_wolf") is True
                for event in seer_checks[:2]
            ) else 0
        ),
        "full_rollout_found_wolf_by_check_3": (
            1 if any(
                event.get("content", {}).get("target_is_wolf") is True
                for event in seer_checks[:3]
            ) else 0
        ),
        "full_rollout_total_wolves_found": len(checked_wolves),
        "full_rollout_seer_survived": (
            1 if any(
                player.role == SEER and player.alive
                for player in game.state.players
            ) else 0
        ),
        "full_rollout_forced_vote_contributed": forced_vote_contributed,
        "full_rollout_eliminated_role": eliminated_role,
        "full_rollout_alive_wolves": game.state.count_alive_wolves(),
        "full_rollout_alive_villagers": game.state.count_alive_villagers(),
    }


def run_single_full_rollout(
    snapshot,
    decision_row,
    candidate_uid,
    continuation_policy,
    rollout_seed,
    max_rounds=DEFAULT_MAX_ROUNDS,
):
    game = clone_game_from_snapshot(snapshot)
    apply_continuation_policy(game, continuation_policy)
    random.seed(rollout_seed)
    decision_type = decision_row["decision_type"]
    actor_uid = decision_row["actor_uid"]
    if candidate_uid not in legal_candidate_uids(game, decision_type, actor_uid):
        raise FullRolloutError("Candidate is not legal for this snapshot.")

    if decision_type == "seer_check":
        force_seer_check(game, actor_uid, candidate_uid)
        finish_current_phase_and_continue(game, max_rounds=max_rounds)
    elif decision_type == "wolf_kill":
        force_wolf_kill(game, candidate_uid)
        finish_current_phase_and_continue(game, max_rounds=max_rounds)
    elif decision_type == "day_vote":
        force_day_vote(game, actor_uid, candidate_uid)
        finish_current_phase_and_continue(game, max_rounds=max_rounds)
    else:
        raise FullRolloutError(f"Unsupported decision_type: {decision_type}")

    return summarize_forced_rollout(
        game,
        decision_type,
        actor_uid,
        candidate_uid,
    )


def mean(values):
    return sum(values) / len(values) if values else 0.0


def variance(values):
    if len(values) < 2:
        return 0.0
    value_mean = mean(values)
    return sum((value - value_mean) ** 2 for value in values) / (
        len(values) - 1
    )


def standard_error(values):
    return math.sqrt(variance(values) / len(values)) if values else 0.0


def evaluate_full_candidate_action(
    snapshot,
    decision_row,
    candidate_uid,
    continuation_policies,
    rollouts_per_policy=2,
    rollout_seed=42,
    max_rounds=DEFAULT_MAX_ROUNDS,
):
    policy_results = []
    all_team_wins = []
    for policy in continuation_policies:
        policy_wins = []
        for index in range(rollouts_per_policy):
            seed = stable_seed(
                "ml_stage15_full_rollout",
                rollout_seed,
                snapshot["snapshot_id"],
                decision_row["decision_id"],
                candidate_uid,
                policy["continuation_policy_id"],
                index,
            )
            outcome = run_single_full_rollout(
                snapshot,
                decision_row,
                candidate_uid,
                policy,
                seed,
                max_rounds=max_rounds,
            )
            policy_wins.append(outcome["full_rollout_team_win"])
            policy_results.append({
                **outcome,
                "continuation_policy_id": policy["continuation_policy_id"],
                "rollout_seed": seed,
            })
        all_team_wins.extend(policy_wins)

    policy_means = defaultdict(list)
    for result in policy_results:
        policy_means[result["continuation_policy_id"]].append(
            result["full_rollout_team_win"]
        )
    policy_value_by_id = {
        policy_id: mean(values)
        for policy_id, values in policy_means.items()
    }
    surrogate = evaluate_candidate_action(
        decision_row,
        candidate_uid,
        rollout_count=max(3, rollouts_per_policy),
        rollout_seed=rollout_seed,
        continuation_policy_config={
            "rollout_mode": "observation_safe_surrogate",
        },
    )
    return {
        "surrogate_rollout_value": surrogate["rollout_team_win_rate"],
        "full_rollout_mean_team_win_rate": mean(all_team_wins),
        "full_rollout_team_win_standard_error": standard_error(all_team_wins),
        "full_rollout_worst_case_team_win_rate": (
            min(policy_value_by_id.values()) if policy_value_by_id else 0.0
        ),
        "full_rollout_value_variance_across_policies": variance(
            list(policy_value_by_id.values())
        ),
        "full_rollout_count": len(all_team_wins),
        "full_rollout_policy_values": dict(policy_value_by_id),
        "full_rollout_detail_rows": policy_results,
    }


def add_full_rollout_values(
    rows,
    snapshot_by_decision_id,
    continuation_policies,
    rollouts_per_policy=2,
    rollout_seed=42,
    max_rounds=DEFAULT_MAX_ROUNDS,
):
    valued_rows = []
    by_decision = defaultdict(list)
    for row in rows:
        snapshot = snapshot_by_decision_id[row["decision_id"]]
        value = evaluate_full_candidate_action(
            snapshot,
            row,
            row["candidate_uid"],
            continuation_policies,
            rollouts_per_policy=rollouts_per_policy,
            rollout_seed=rollout_seed,
            max_rounds=max_rounds,
        )
        detail_rows = value.pop("full_rollout_detail_rows")
        row_with_value = dict(row)
        row_with_value.update(value)
        row_with_value["full_rollout_policy_values_json"] = (
            str(value["full_rollout_policy_values"])
        )
        row_with_value["_full_rollout_detail_rows"] = detail_rows
        by_decision[row["decision_id"]].append(row_with_value)
        valued_rows.append(row_with_value)

    for decision_rows in by_decision.values():
        best_value = max(
            row["full_rollout_mean_team_win_rate"]
            for row in decision_rows
        )
        best_actions = [
            row for row in decision_rows
            if row["full_rollout_mean_team_win_rate"] == best_value
        ]
        best_action = sorted(
            best_actions,
            key=lambda row: str(row["candidate_uid"]),
        )[0]["candidate_uid"]
        existing_values = [
            row["full_rollout_mean_team_win_rate"]
            for row in decision_rows
            if int(row["action_selected_by_existing_policy"]) == 1
        ]
        existing_value = existing_values[0] if existing_values else best_value
        for row in decision_rows:
            row["full_rollout_best_action"] = best_action
            row["full_rollout_value_rank_within_decision"] = (
                1 + sum(
                    1 for other in decision_rows
                    if other["full_rollout_mean_team_win_rate"]
                    > row["full_rollout_mean_team_win_rate"]
                )
            )
            row["full_rollout_existing_policy_regret"] = (
                best_value - existing_value
            )
    return valued_rows
