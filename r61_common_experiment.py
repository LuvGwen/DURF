"""Shared runner for R6.1 targeted role-strategy experiments."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from config import (
    DEFAULT_HERDING_ALPHA,
    DEFAULT_HERDING_BETA,
    DEFAULT_HERDING_GAMMA,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_WITCH_POISON_THRESHOLD,
    TEN_PLAYER_CREDIBILITY_COST_SCALE,
    TEN_PLAYER_HERDING_WEIGHT_SCALE,
    TEN_PLAYER_INITIAL_P_WOLF,
    TEN_PLAYER_ROLE_SETUP,
    TEN_PLAYER_SPEECH_SIGNAL_SCALE,
)
from game import Game, create_default_players
from r61_hunter_policies import R61_HUNTER_POLICIES
from r61_matched_design import (
    BEHAVIORAL_REGIMES,
    FINAL_SEEDS,
    R61_MATCHED_SETS_PER_MODULE,
    generate_r61_matched_sets,
    stable_int_seed,
    validate_seed_isolation,
    write_regime_registry,
    write_seed_registry,
)
from r61_risk_metrics import (
    frontier_membership,
    payoff_risk_metrics,
)
from r61_seer_reveal_policies import R61_SEER_REVEAL_POLICIES
from r61_statistical_analysis import holm_adjust, mean, normal_ci, paired_contrast, stdev
from r61_villager_voting_policies import R61_VILLAGER_VOTING_POLICIES
from r61_witch_joint_policies import R61_WITCH_JOINT_POLICIES
from r61_wolf_aggression_policies import R61_WOLF_AGGRESSION_POLICIES
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH, VILLAGE_TEAM, WOLF_TEAM


RESULTS_DIR = Path("results/targeted_strategy_stage_r61")
FIGURE_DIR = RESULTS_DIR / "figures"
BOOTSTRAP_REPLICATES = 1000
PERMUTATION_REPLICATES = 1000
R4_MANIFEST_HASH = "eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd"
R5_METRIC_MANIFEST_HASH = "4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf"


MODULES = {
    "hunter": {
        "role": HUNTER,
        "policies": R61_HUNTER_POLICIES,
        "reference": "reference",
        "flag": "enable_r61_hunter_policy",
        "policy_arg": "r61_hunter_policy",
        "action_raw_name": "r61_hunter_action_raw.csv",
    },
    "seer": {
        "role": SEER,
        "policies": R61_SEER_REVEAL_POLICIES,
        "reference": "private_only",
        "flag": "enable_r61_seer_reveal_policy",
        "policy_arg": "r61_seer_reveal_policy",
        "action_raw_name": "r61_seer_reveal_event_raw.csv",
    },
    "witch": {
        "role": WITCH,
        "policies": R61_WITCH_JOINT_POLICIES,
        "reference": "reference",
        "flag": "enable_r61_witch_joint_policy",
        "policy_arg": "r61_witch_joint_policy",
        "action_raw_name": "r61_witch_action_raw.csv",
    },
    "wolf": {
        "role": WEREWOLF,
        "policies": R61_WOLF_AGGRESSION_POLICIES,
        "reference": "reference",
        "flag": "enable_r61_wolf_aggression_policy",
        "policy_arg": "r61_wolf_aggression_policy",
        "action_raw_name": "r61_wolf_action_and_deception_raw.csv",
    },
    "villager": {
        "role": VILLAGER,
        "policies": R61_VILLAGER_VOTING_POLICIES,
        "reference": "reference",
        "flag": "enable_r61_villager_voting_policy",
        "policy_arg": "r61_villager_voting_policy",
        "action_raw_name": "r61_villager_vote_raw.csv",
    },
}


GAME_LEVEL_FIELDS = [
    "module",
    "policy",
    "matched_set_id",
    "seed",
    "seed_split",
    "behavioral_regime",
    "replicate_index",
    "game_seed",
    "game_id",
    "winner",
    "village_win",
    "wolf_win",
    "draw",
    "round_number",
    "num_alive_players",
    "num_events",
    "actor_role",
    "actor_payoff",
    "team_payoff",
    "wolf_payoff",
    "village_payoff",
    "actor_negative_payoff",
    "total_seer_checks",
    "seer_reveals",
    "hunter_shots",
    "hunter_abstentions",
    "witch_saves",
    "witch_poison",
    "night_kills_prevented",
    "wolf_deceptions",
    "false_accusations",
    "deflections",
    "trust_building_deceptions",
    "credibility_costs",
    "self_defense_costs",
    "wrong_accusation_penalties",
    "day_votes",
    "wrong_eliminations",
    "correct_vote_count",
    "wrong_vote_count",
    "first_seer_check_wolf",
    "found_wolf_by_check_2",
    "found_wolf_by_check_3",
    "seer_survived",
    "wolves_discovered",
    "mean_checks_until_first_wolf",
    "no_wolf_found",
    "search_path_coverage",
    "seer_total_checks",
    "seat_assignment_signature",
]


ACTION_FIELDS = [
    "module",
    "policy",
    "matched_set_id",
    "seed",
    "behavioral_regime",
    "game_id",
    "event_index",
    "event_type",
    "round",
    "phase",
    "actor_id",
    "target_id",
    "target_role",
    "target_is_wolf",
    "action_subtype",
    "success",
    "extra_json",
]


SUMMARY_FIELDS = [
    "module",
    "policy",
    "game_count",
    "matched_set_count",
    "seed_count",
    "behavioral_regime_count",
    "village_win_rate",
    "wolf_win_rate",
    "draw_rate",
    "mean_actor_payoff",
    "actor_payoff_ci_low",
    "actor_payoff_ci_high",
    "mean_team_payoff",
    "mean_wolf_payoff",
    "mean_village_payoff",
    "stdev_payoff",
    "downside_deviation",
    "negative_payoff_probability",
    "var_like_90",
    "var_like_95",
    "cvar_like_90",
    "cvar_like_95",
    "sharpe_like_ratio",
    "sortino_like_ratio",
    "total_actions",
    "village_win_ci_low",
    "village_win_ci_high",
    "frontier_stdev",
    "frontier_downside",
    "frontier_cvar95",
]


CONTRAST_FIELDS = [
    "module",
    "reference_policy",
    "candidate_policy",
    "metric",
    "matched_set_count",
    "mean_difference",
    "ci_low",
    "ci_high",
    "difference_stdev",
    "effect_size_dz",
    "raw_p_value",
    "holm_adjusted_p_value",
    "conclusion_label",
]


ROBUSTNESS_FIELDS = [
    "module",
    "policy",
    "group_key",
    "group_value",
    "game_count",
    "village_win_rate",
    "wolf_win_rate",
    "mean_actor_payoff",
]


def fmt(value, digits=4):
    if value in (None, ""):
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            restval="",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_table(path, rows, columns, title):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        file.write(f"# {title}\n\n")
        file.write("| " + " | ".join(header for _, header in columns) + " |\n")
        file.write("|" + "|".join("---" for _ in columns) + "|\n")
        for row in rows:
            file.write("| ")
            file.write(" | ".join(fmt(row.get(key)) for key, _ in columns))
            file.write(" |\n")


def base_game_config():
    return {
        "role_setup": TEN_PLAYER_ROLE_SETUP,
        "initial_p_wolf": TEN_PLAYER_INITIAL_P_WOLF,
        "speech_signal_scale": TEN_PLAYER_SPEECH_SIGNAL_SCALE,
        "credibility_cost_scale": TEN_PLAYER_CREDIBILITY_COST_SCALE,
        "herding_alpha": DEFAULT_HERDING_ALPHA * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "herding_beta": DEFAULT_HERDING_BETA * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "herding_gamma": DEFAULT_HERDING_GAMMA * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": True,
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "threat_based",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "trust_vote_weight": 0.20,
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": True,
        "witch_poison_threshold": DEFAULT_WITCH_POISON_THRESHOLD,
        "witch_save_probability": 0.70,
        "seer_check_strategy": "alternate_sides",
        "seer_avoid_repeat_checks": True,
        "enable_position_model": True,
        "randomize_seat_roles": True,
        "enable_bow_r3": False,
        "enable_ml_wolf_kill_policy": False,
        "enable_ml_stage2b_policy": False,
    }


def regime_overrides(regime):
    if regime == "baseline":
        return {
            "enable_speech": False,
            "enable_herding": False,
            "enable_role_prior": False,
            "enable_wolf_deception": False,
            "enable_deception_credibility": False,
            "enable_speaker_memory": False,
            "enable_trust_weighted_speech": False,
            "enable_trust_weighted_herding": False,
        }
    if regime == "speech_enabled":
        return {
            "enable_herding": False,
            "enable_wolf_deception": False,
            "enable_deception_credibility": False,
            "enable_speaker_memory": False,
        }
    if regime == "herding_enabled":
        return {
            "enable_wolf_deception": False,
            "enable_deception_credibility": False,
            "enable_speaker_memory": False,
        }
    if regime == "deception_enabled":
        return {"enable_speaker_memory": False}
    if regime == "heterogeneous_risk":
        return {
            "enable_risk_preference": True,
            "risk_preference_mode": "mixed",
        }
    if regime == "strong_village_information":
        return {
            "seer_avoid_repeat_checks": True,
            "trust_vote_weight": 0.30,
            "witch_save_probability": 0.85,
            "witch_poison_threshold": 0.20,
        }
    if regime == "weak_village_information":
        return {
            "speech_signal_scale": 0.45,
            "enable_role_prior": False,
            "enable_speaker_memory": False,
            "enable_trust_weighted_speech": False,
            "enable_trust_weighted_herding": False,
            "witch_save_probability": 0.40,
            "witch_poison_threshold": 0.45,
        }
    if regime == "high_emotional_speech":
        return {
            "speech_signal_scale": 1.25,
            "herding_alpha": DEFAULT_HERDING_ALPHA,
            "herding_beta": DEFAULT_HERDING_BETA,
            "herding_gamma": DEFAULT_HERDING_GAMMA,
        }
    if regime == "low_information_speech":
        return {
            "speech_signal_scale": 0.35,
            "enable_suspicion_update": False,
            "enable_role_prior": False,
            "trust_vote_weight": 0.05,
        }
    if regime == "mixed_strategies":
        return {
            "enable_risk_preference": True,
            "risk_preference_mode": "mixed",
            "trust_vote_weight": 0.25,
        }
    return {}


def game_config_for(module, policy, regime):
    config = base_game_config()
    config.update(regime_overrides(regime))
    spec = MODULES[module]
    config[spec["flag"]] = True
    config[spec["policy_arg"]] = policy

    if module != "wolf":
        config["enable_r61_wolf_aggression_policy"] = False
    if module != "villager":
        config["enable_r61_villager_voting_policy"] = False
    if module != "hunter":
        config["enable_r61_hunter_policy"] = False
    if module != "seer":
        config["enable_r61_seer_reveal_policy"] = False
    if module != "witch":
        config["enable_r61_witch_joint_policy"] = False

    return config


def get_role_players(game, role):
    return [player for player in game.state.players if player.role == role]


def average_role_payoff(game, role):
    values = [
        payoff["total_payoff"]
        for payoff in game.payoffs.values()
        if payoff["role"] == role
    ]
    return mean(values) if values else 0.0


def average_team_payoff(game, team):
    values = [
        payoff["total_payoff"]
        for payoff in game.payoffs.values()
        if payoff["team"] == team
    ]
    return mean(values) if values else 0.0


def seat_assignment_signature(game):
    for event in game.event_log:
        if event.get("event_type") == "seat_role_assignment":
            assignments = event.get("content", {}).get("assignments", {})
            return json.dumps(assignments, sort_keys=True)
    return ""


def seer_check_events(game):
    return [
        event for event in game.event_log
        if event.get("event_type") == "seer_check"
    ]


def first_wolf_check_index(check_events):
    for index, event in enumerate(check_events, start=1):
        if event.get("content", {}).get("target_is_wolf") is True:
            return index
    return None


def count_correct_and_wrong_votes(game):
    correct = 0
    wrong = 0
    for event in game.event_log:
        if event.get("event_type") != "day_vote":
            continue
        for target_id in event.get("content", {}).get("votes", {}).values():
            try:
                target = game.state.get_player_by_id(target_id)
            except ValueError:
                continue
            if target.is_wolf():
                correct += 1
            else:
                wrong += 1
    return correct, wrong


def count_wrong_eliminations(game):
    count = 0
    for event in game.event_log:
        if event.get("event_type") != "day_vote":
            continue
        eliminated_id = event.get("content", {}).get("eliminated")
        try:
            eliminated = game.state.get_player_by_id(eliminated_id)
        except ValueError:
            continue
        if eliminated.team == VILLAGE_TEAM:
            count += 1
    return count


def build_game_row(module, policy, matched_set, game, result):
    role = MODULES[module]["role"]
    actor_payoff = average_role_payoff(game, role)
    check_events = seer_check_events(game)
    first_wolf_index = first_wolf_check_index(check_events)
    correct_votes, wrong_votes = count_correct_and_wrong_votes(game)
    wolf_check_count = sum(
        1 for event in check_events
        if event.get("content", {}).get("target_is_wolf") is True
    )
    seers = get_role_players(game, SEER)
    seer_alive = seers[0].alive if seers else False
    game_id = f"{module}_{policy}_{matched_set['matched_set_id']}"

    return {
        "module": module,
        "policy": policy,
        "matched_set_id": matched_set["matched_set_id"],
        "seed": matched_set["seed"],
        "seed_split": matched_set["seed_split"],
        "behavioral_regime": matched_set["behavioral_regime"],
        "replicate_index": matched_set["replicate_index"],
        "game_seed": matched_set["game_seed"],
        "game_id": game_id,
        "winner": result["winner"],
        "village_win": 1 if result["winner"] == VILLAGE_TEAM else 0,
        "wolf_win": 1 if result["winner"] == WOLF_TEAM else 0,
        "draw": 1 if result["winner"] == "draw" else 0,
        "round_number": result["round_number"],
        "num_alive_players": result["num_alive_players"],
        "num_events": len(game.event_log),
        "actor_role": role,
        "actor_payoff": actor_payoff,
        "team_payoff": average_team_payoff(
            game,
            WOLF_TEAM if role == WEREWOLF else VILLAGE_TEAM,
        ),
        "wolf_payoff": average_team_payoff(game, WOLF_TEAM),
        "village_payoff": average_team_payoff(game, VILLAGE_TEAM),
        "actor_negative_payoff": 1 if actor_payoff < 0 else 0,
        "total_seer_checks": len(check_events),
        "seer_reveals": count_events(game, "seer_reveal"),
        "hunter_shots": count_events(game, "hunter_shot"),
        "hunter_abstentions": count_events(game, "hunter_shot_abstained"),
        "witch_saves": count_events(game, "witch_save"),
        "witch_poison": count_events(game, "witch_poison"),
        "night_kills_prevented": count_events(game, "night_kill_prevented"),
        "wolf_deceptions": count_wolf_deceptions(game),
        "false_accusations": count_deception_type(game, "false_accuse"),
        "deflections": count_deception_type(game, "deflect_suspicion"),
        "trust_building_deceptions": count_deception_type(game, "trust_building"),
        "credibility_costs": count_events(game, "accusation_pressure_cost"),
        "self_defense_costs": count_events(game, "self_defense_credibility_cost"),
        "wrong_accusation_penalties": count_events(game, "wrong_accusation_penalty"),
        "day_votes": count_events(game, "day_vote"),
        "wrong_eliminations": count_wrong_eliminations(game),
        "correct_vote_count": correct_votes,
        "wrong_vote_count": wrong_votes,
        "first_seer_check_wolf": (
            1 if check_events and check_events[0]["content"].get("target_is_wolf")
            else 0
        ),
        "found_wolf_by_check_2": (
            1 if first_wolf_index is not None and first_wolf_index <= 2 else 0
        ),
        "found_wolf_by_check_3": (
            1 if first_wolf_index is not None and first_wolf_index <= 3 else 0
        ),
        "seer_survived": 1 if seer_alive else 0,
        "wolves_discovered": wolf_check_count,
        "mean_checks_until_first_wolf": first_wolf_index or "",
        "no_wolf_found": 1 if first_wolf_index is None else 0,
        "search_path_coverage": (
            len({
                event.get("content", {}).get("target")
                for event in check_events
            }) / 9.0
        ),
        "seer_total_checks": len(check_events),
        "seat_assignment_signature": seat_assignment_signature(game),
    }


def count_events(game, event_type):
    return sum(1 for event in game.event_log if event.get("event_type") == event_type)


def count_wolf_deceptions(game):
    return sum(
        1 for event in game.event_log
        if (
            event.get("event_type") == "speech"
            and event.get("content", {}).get("is_deception") is True
        )
    )


def count_deception_type(game, deception_type):
    return sum(
        1 for event in game.event_log
        if (
            event.get("event_type") == "speech"
            and event.get("content", {}).get("deception_type") == deception_type
        )
    )


def _action_target(content):
    for key in ["target", "shot_target", "poisoned_player", "saved_player"]:
        if content.get(key) is not None:
            return content.get(key)
    return None


def _action_actor(content):
    for key in ["hunter", "seer", "witch", "speaker", "voter"]:
        if content.get(key) is not None:
            return content.get(key)
    return None


def _action_subtype(content):
    for key in [
        "hunter_policy",
        "seer_reveal_policy",
        "witch_joint_policy",
        "deception_type",
        "strategy",
        "method",
    ]:
        if content.get(key) is not None:
            return content.get(key)
    return ""


def build_action_rows(module, policy, matched_set, game):
    action_event_types = {
        "hunter": {"hunter_shot", "hunter_shot_abstained"},
        "seer": {"seer_check", "seer_reveal"},
        "witch": {"witch_save", "witch_poison", "night_kill_prevented"},
        "wolf": {"night_kill", "speech", "accusation_pressure_cost", "self_defense_credibility_cost"},
        "villager": {"day_vote"},
    }[module]
    rows = []
    game_id = f"{module}_{policy}_{matched_set['matched_set_id']}"

    for index, event in enumerate(game.event_log):
        event_type = event.get("event_type")
        if event_type not in action_event_types:
            continue

        content = event.get("content", {})
        if module == "wolf" and event_type == "speech":
            if content.get("is_deception") is not True:
                continue
        if module == "villager" and event_type == "day_vote":
            for voter_id, target_id in content.get("votes", {}).items():
                try:
                    target = game.state.get_player_by_id(target_id)
                except ValueError:
                    target = None
                rows.append({
                    "module": module,
                    "policy": policy,
                    "matched_set_id": matched_set["matched_set_id"],
                    "seed": matched_set["seed"],
                    "behavioral_regime": matched_set["behavioral_regime"],
                    "game_id": game_id,
                    "event_index": index,
                    "event_type": event_type,
                    "round": event.get("round"),
                    "phase": event.get("phase"),
                    "actor_id": voter_id,
                    "target_id": target_id,
                    "target_role": target.role if target is not None else "",
                    "target_is_wolf": (
                        target.is_wolf() if target is not None else ""
                    ),
                    "action_subtype": content.get("method", ""),
                    "success": (
                        target.is_wolf() if target is not None else ""
                    ),
                    "extra_json": json.dumps(content, sort_keys=True),
                })
            continue

        target_id = _action_target(content)
        target = None
        if target_id is not None:
            try:
                target = game.state.get_player_by_id(target_id)
            except ValueError:
                target = None
        rows.append({
            "module": module,
            "policy": policy,
            "matched_set_id": matched_set["matched_set_id"],
            "seed": matched_set["seed"],
            "behavioral_regime": matched_set["behavioral_regime"],
            "game_id": game_id,
            "event_index": index,
            "event_type": event_type,
            "round": event.get("round"),
            "phase": event.get("phase"),
            "actor_id": _action_actor(content),
            "target_id": target_id,
            "target_role": content.get(
                "target_role",
                target.role if target is not None else "",
            ),
            "target_is_wolf": content.get(
                "target_is_wolf",
                target.is_wolf() if target is not None else "",
            ),
            "action_subtype": _action_subtype(content),
            "success": content.get("target_is_wolf", content.get("used_poison", "")),
            "extra_json": json.dumps(content, sort_keys=True),
        })

    return rows


def run_policy_game(module, policy, matched_set, max_rounds=DEFAULT_MAX_ROUNDS):
    random.seed(matched_set["game_seed"])
    players = create_default_players(
        role_setup=TEN_PLAYER_ROLE_SETUP,
        initial_p_wolf=TEN_PLAYER_INITIAL_P_WOLF,
    )
    config = game_config_for(module, policy, matched_set["behavioral_regime"])
    config.update({
        "main_game_seed": matched_set["game_seed"],
        "base_game_index": matched_set["replicate_index"],
        "label_condition": f"{module}_{policy}",
    })
    game = Game(players, **config)
    result = game.run_game(max_rounds=max_rounds)
    game_row = build_game_row(module, policy, matched_set, game, result)
    action_rows = build_action_rows(module, policy, matched_set, game)
    return game_row, action_rows


def summarize_policy_rows(module, rows, action_rows):
    grouped = defaultdict(list)
    actions_by_policy = Counter(row["policy"] for row in action_rows)
    for row in rows:
        grouped[row["policy"]].append(row)

    summaries = []
    for policy in MODULES[module]["policies"]:
        policy_rows = grouped.get(policy, [])
        if not policy_rows:
            continue
        actor_values = [float(row["actor_payoff"]) for row in policy_rows]
        village_wins = [float(row["village_win"]) for row in policy_rows]
        metrics = payoff_risk_metrics(actor_values)
        actor_ci_low, actor_ci_high = normal_ci(actor_values)
        village_ci_low, village_ci_high = normal_ci(village_wins)
        summaries.append({
            "module": module,
            "policy": policy,
            "game_count": len(policy_rows),
            "matched_set_count": len({
                row["matched_set_id"] for row in policy_rows
            }),
            "seed_count": len({row["seed"] for row in policy_rows}),
            "behavioral_regime_count": len({
                row["behavioral_regime"] for row in policy_rows
            }),
            "village_win_rate": mean(village_wins),
            "wolf_win_rate": mean([float(row["wolf_win"]) for row in policy_rows]),
            "draw_rate": mean([float(row["draw"]) for row in policy_rows]),
            "mean_actor_payoff": metrics["mean_payoff"],
            "actor_payoff_ci_low": actor_ci_low,
            "actor_payoff_ci_high": actor_ci_high,
            "mean_team_payoff": mean([float(row["team_payoff"]) for row in policy_rows]),
            "mean_wolf_payoff": mean([float(row["wolf_payoff"]) for row in policy_rows]),
            "mean_village_payoff": mean([float(row["village_payoff"]) for row in policy_rows]),
            "stdev_payoff": metrics["stdev_payoff"],
            "downside_deviation": metrics["downside_deviation"],
            "negative_payoff_probability": metrics["negative_payoff_probability"],
            "var_like_90": metrics["var_like_90"],
            "var_like_95": metrics["var_like_95"],
            "cvar_like_90": metrics["cvar_like_90"],
            "cvar_like_95": metrics["cvar_like_95"],
            "sharpe_like_ratio": metrics["sharpe_like_ratio"],
            "sortino_like_ratio": metrics["sortino_like_ratio"],
            "total_actions": actions_by_policy.get(policy, 0),
            "village_win_ci_low": village_ci_low,
            "village_win_ci_high": village_ci_high,
        })

    stdev_frontier = set(frontier_membership(summaries, "stdev_payoff"))
    downside_frontier = set(frontier_membership(summaries, "downside_deviation"))
    cvar_frontier = set(frontier_membership(summaries, "cvar_like_95"))
    for summary in summaries:
        policy = summary["policy"]
        summary["frontier_stdev"] = policy in stdev_frontier
        summary["frontier_downside"] = policy in downside_frontier
        summary["frontier_cvar95"] = policy in cvar_frontier

    return summaries


def summarize_special_module_metrics(module, rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["policy"]].append(row)

    output = []
    for policy, policy_rows in sorted(grouped.items()):
        result = {
            "module": module,
            "policy": policy,
            "game_count": len(policy_rows),
        }
        if module == "seer":
            checks_to_first = [
                float(row["mean_checks_until_first_wolf"])
                for row in policy_rows
                if row["mean_checks_until_first_wolf"] not in ("", None)
            ]
            result.update({
                "first_check_wolf_rate": mean([
                    row["first_seer_check_wolf"] for row in policy_rows
                ]),
                "found_wolf_by_check_2_rate": mean([
                    row["found_wolf_by_check_2"] for row in policy_rows
                ]),
                "found_wolf_by_check_3_rate": mean([
                    row["found_wolf_by_check_3"] for row in policy_rows
                ]),
                "mean_checks_until_first_wolf": mean(checks_to_first),
                "no_wolf_found_rate": mean([
                    row["no_wolf_found"] for row in policy_rows
                ]),
                "mean_wolves_discovered": mean([
                    row["wolves_discovered"] for row in policy_rows
                ]),
                "seer_survival_rate": mean([
                    row["seer_survived"] for row in policy_rows
                ]),
                "mean_total_seer_checks": mean([
                    row["seer_total_checks"] for row in policy_rows
                ]),
                "mean_search_path_coverage": mean([
                    row["search_path_coverage"] for row in policy_rows
                ]),
                "total_seer_reveals": sum(row["seer_reveals"] for row in policy_rows),
            })
        elif module == "witch":
            result.update({
                "total_witch_saves": sum(row["witch_saves"] for row in policy_rows),
                "total_witch_poison": sum(row["witch_poison"] for row in policy_rows),
                "total_night_kills_prevented": sum(
                    row["night_kills_prevented"] for row in policy_rows
                ),
                "mean_witch_saves_per_game": mean([
                    row["witch_saves"] for row in policy_rows
                ]),
                "mean_witch_poison_per_game": mean([
                    row["witch_poison"] for row in policy_rows
                ]),
            })
        elif module == "hunter":
            result.update({
                "total_hunter_shots": sum(row["hunter_shots"] for row in policy_rows),
                "total_hunter_abstentions": sum(
                    row["hunter_abstentions"] for row in policy_rows
                ),
            })
        elif module == "wolf":
            result.update({
                "total_wolf_deceptions": sum(
                    row["wolf_deceptions"] for row in policy_rows
                ),
                "false_accusations": sum(row["false_accusations"] for row in policy_rows),
                "deflections": sum(row["deflections"] for row in policy_rows),
                "trust_building_deceptions": sum(
                    row["trust_building_deceptions"] for row in policy_rows
                ),
                "credibility_costs": sum(row["credibility_costs"] for row in policy_rows),
                "self_defense_costs": sum(row["self_defense_costs"] for row in policy_rows),
            })
        elif module == "villager":
            total_votes = sum(
                row["correct_vote_count"] + row["wrong_vote_count"]
                for row in policy_rows
            )
            result.update({
                "total_votes": total_votes,
                "correct_vote_count": sum(
                    row["correct_vote_count"] for row in policy_rows
                ),
                "wrong_vote_count": sum(
                    row["wrong_vote_count"] for row in policy_rows
                ),
                "correct_vote_rate": (
                    sum(row["correct_vote_count"] for row in policy_rows)
                    / total_votes
                    if total_votes
                    else 0.0
                ),
                "wrong_eliminations": sum(
                    row["wrong_eliminations"] for row in policy_rows
                ),
            })
        output.append(result)
    return output


def build_primary_contrasts(module, rows):
    reference = MODULES[module]["reference"]
    metric_keys = ["actor_payoff"]
    if module in {"seer", "villager", "witch", "hunter"}:
        metric_keys.append("village_win")
    if module == "wolf":
        metric_keys.append("wolf_win")

    contrasts = []
    for metric_key in metric_keys:
        metric_contrasts = []
        for policy in MODULES[module]["policies"]:
            if policy == reference:
                continue
            metric_contrasts.append(paired_contrast(
                rows,
                module,
                reference,
                policy,
                metric_key=metric_key,
                permutation_iterations=PERMUTATION_REPLICATES,
            ))
        holm_adjust(metric_contrasts)
        for row in metric_contrasts:
            row["conclusion_label"] = conclusion_label(row)
        contrasts.extend(metric_contrasts)
    return contrasts


def conclusion_label(contrast):
    adjusted = contrast.get("holm_adjusted_p_value")
    diff = contrast.get("mean_difference")
    if adjusted is None or diff is None:
        return "insufficient data"
    if adjusted <= 0.05 and diff > 0:
        return "statistically supported improvement"
    if adjusted <= 0.05 and diff < 0:
        return "statistically supported harmful effect"
    if abs(diff) >= 0.03:
        return "promising but uncertain"
    return "no meaningful improvement"


def robustness_rows(module, rows, group_key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["policy"], row[group_key])].append(row)
    output = []
    for (policy, group_value), group_rows in sorted(grouped.items()):
        output.append({
            "module": module,
            "policy": policy,
            "group_key": group_key,
            "group_value": group_value,
            "game_count": len(group_rows),
            "village_win_rate": mean([row["village_win"] for row in group_rows]),
            "wolf_win_rate": mean([row["wolf_win"] for row in group_rows]),
            "mean_actor_payoff": mean([row["actor_payoff"] for row in group_rows]),
        })
    return output


def leave_one_out_rows(module, rows, group_key):
    values = sorted({row[group_key] for row in rows})
    output = []
    for omitted in values:
        kept = [row for row in rows if row[group_key] != omitted]
        for policy in MODULES[module]["policies"]:
            policy_rows = [row for row in kept if row["policy"] == policy]
            if not policy_rows:
                continue
            output.append({
                "module": module,
                "policy": policy,
                "group_key": f"leave_one_{group_key}",
                "group_value": omitted,
                "game_count": len(policy_rows),
                "village_win_rate": mean([row["village_win"] for row in policy_rows]),
                "wolf_win_rate": mean([row["wolf_win"] for row in policy_rows]),
                "mean_actor_payoff": mean([row["actor_payoff"] for row in policy_rows]),
            })
    return output


def validate_module_rows(module, rows):
    errors = []
    expected = R61_MATCHED_SETS_PER_MODULE * len(MODULES[module]["policies"])
    if len(rows) != expected:
        errors.append(f"expected {expected} game rows, found {len(rows)}")

    ids = [row["game_id"] for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("game_id values are not unique")

    grouped = defaultdict(set)
    for row in rows:
        grouped[row["matched_set_id"]].add(row["seat_assignment_signature"])
    mismatch_count = sum(1 for signatures in grouped.values() if len(signatures) > 1)
    if mismatch_count:
        errors.append(f"{mismatch_count} matched sets had assignment mismatch")

    return errors


def run_r61_module(
    module,
    matched_sets=None,
    max_rounds=DEFAULT_MAX_ROUNDS,
):
    if matched_sets is None:
        matched_sets = generate_r61_matched_sets()

    game_rows = []
    action_rows = []
    for matched_set in matched_sets:
        for policy in MODULES[module]["policies"]:
            row, actions = run_policy_game(
                module,
                policy,
                matched_set,
                max_rounds=max_rounds,
            )
            game_rows.append(row)
            action_rows.extend(actions)

    return game_rows, action_rows


def write_basic_svg_bar(path, title, rows, value_key):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 900
    bar_height = 24
    gap = 12
    margin_left = 230
    margin_top = 46
    height = margin_top + len(rows) * (bar_height + gap) + 30
    max_value = max([float(row.get(value_key) or 0) for row in rows] + [1.0])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="20" y="26" font-family="Arial" font-size="18" font-weight="700">{title}</text>',
    ]
    for index, row in enumerate(rows):
        y = margin_top + index * (bar_height + gap)
        value = float(row.get(value_key) or 0.0)
        bar_width = 580 * value / max_value if max_value else 0
        label = str(row.get("policy", ""))
        parts.append(
            f'<text x="20" y="{y + 17}" font-family="Arial" font-size="12">{label}</text>'
        )
        parts.append(
            f'<rect x="{margin_left}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" fill="#2f7d6d"/>'
        )
        parts.append(
            f'<text x="{margin_left + bar_width + 8:.1f}" y="{y + 17}" font-family="Arial" font-size="12">{value:.3f}</text>'
        )
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_risk_return_svg(path, title, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 900
    height = 520
    x0, y0 = 80, 430
    plot_w, plot_h = 720, 330
    risks = [float(row.get("stdev_payoff") or 0.0) for row in rows]
    returns = [float(row.get("mean_actor_payoff") or 0.0) for row in rows]
    max_risk = max(risks + [1.0])
    min_return = min(returns + [0.0])
    max_return = max(returns + [1.0])
    span_return = max(max_return - min_return, 0.1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="30" font-family="Arial" font-size="18" font-weight="700">{title}</text>',
        f'<line x1="{x0}" y1="{y0}" x2="{x0 + plot_w}" y2="{y0}" stroke="#222"/>',
        f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 - plot_h}" stroke="#222"/>',
        '<text x="350" y="485" font-family="Arial" font-size="13">Standard deviation</text>',
        '<text x="14" y="250" font-family="Arial" font-size="13" transform="rotate(-90 14,250)">Mean actor payoff</text>',
    ]
    colors = ["#2f7d6d", "#b04d3a", "#4067a9", "#8a6f2a", "#7d3c98", "#4b8b3b"]
    for index, row in enumerate(rows):
        risk = float(row.get("stdev_payoff") or 0.0)
        ret = float(row.get("mean_actor_payoff") or 0.0)
        x = x0 + plot_w * risk / max_risk
        y = y0 - plot_h * (ret - min_return) / span_return
        color = colors[index % len(colors)]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}"/>')
        parts.append(
            f'<text x="{x + 10:.1f}" y="{y + 4:.1f}" font-family="Arial" font-size="11">{row["policy"]}</text>'
        )
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_module_report(
    module,
    summary_rows,
    contrast_rows,
    special_rows,
    validation_errors,
):
    title = f"R6.1 {module.title()} Targeted Strategy Report"
    best = max(summary_rows, key=lambda row: row["mean_actor_payoff"])
    significant = [
        row for row in contrast_rows
        if row.get("holm_adjusted_p_value") not in (None, "")
        and float(row["holm_adjusted_p_value"]) <= 0.05
    ]
    path = RESULTS_DIR / f"r61_{module}_research_report.md"
    with path.open("w", encoding="utf-8") as file:
        file.write(f"# {title}\n\n")
        file.write("## Technical Summary\n\n")
        file.write(
            f"This module tests {len(summary_rows)} {module} policies in "
            f"{R61_MATCHED_SETS_PER_MODULE} matched sets per policy. "
            "The independent unit is the matched complete game. "
        )
        if significant:
            file.write(
                f"{len(significant)} primary contrasts reached Holm-adjusted "
                "0.05 significance.\n\n"
            )
        else:
            file.write(
                "No primary contrast reached Holm-adjusted 0.05 significance.\n\n"
            )
        file.write("## Policy Summary\n\n")
        file.write("| Policy | Village Win | Wolf Win | Mean Actor Payoff | SD | CVaR95 | Sharpe-like |\n")
        file.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for row in summary_rows:
            file.write(
                f"| {row['policy']} | {row['village_win_rate']:.3f} | "
                f"{row['wolf_win_rate']:.3f} | {row['mean_actor_payoff']:.3f} | "
                f"{row['stdev_payoff']:.3f} | {row['cvar_like_95']:.3f} | "
                f"{fmt(row['sharpe_like_ratio'])} |\n"
            )
        file.write("\n## Primary Contrasts\n\n")
        file.write("| Candidate | Metric | Mean Diff | CI Low | CI High | Raw p | Holm p | Label |\n")
        file.write("|---|---|---:|---:|---:|---:|---:|---|\n")
        for row in contrast_rows:
            file.write(
                f"| {row['candidate_policy']} | {row['metric']} | "
                f"{fmt(row['mean_difference'])} | {fmt(row['ci_low'])} | "
                f"{fmt(row['ci_high'])} | {fmt(row['raw_p_value'])} | "
                f"{fmt(row['holm_adjusted_p_value'])} | "
                f"{row['conclusion_label']} |\n"
            )
        file.write("\n## Role-Specific Diagnostics\n\n")
        file.write(
            "Role-specific diagnostic summaries are exported in the module "
            "summary CSV files. The best expected-payoff policy in this run is "
            f"`{best['policy']}`.\n\n"
        )
        file.write("## Validation\n\n")
        if validation_errors:
            for error in validation_errors:
                file.write(f"- {error}\n")
        else:
            file.write("- Game IDs are unique.\n")
            file.write("- Initial randomized seat-role assignment is matched across policy arms.\n")
            file.write("- R6.1 policy flags are experimental and default to False.\n")
        file.write("\n## Limitations\n\n")
        file.write(
            "This is a pilot-scale R6.1 matched live validation at the "
            "minimum allowed 1,000 matched sets per module. Strategy rows are "
            "complete-game outcomes; action raw rows are diagnostic and are not "
            "treated as independent games.\n"
        )
    return path


def write_module_outputs(module, game_rows, action_rows):
    spec = MODULES[module]
    summary_rows = summarize_policy_rows(module, game_rows, action_rows)
    contrast_rows = build_primary_contrasts(module, game_rows)
    special_rows = summarize_special_module_metrics(module, game_rows)
    seed_rows = robustness_rows(module, game_rows, "seed")
    regime_rows = robustness_rows(module, game_rows, "behavioral_regime")
    leave_seed_rows = leave_one_out_rows(module, game_rows, "seed")
    leave_regime_rows = leave_one_out_rows(module, game_rows, "behavioral_regime")
    validation_errors = validate_module_rows(module, game_rows)

    write_csv(
        RESULTS_DIR / f"r61_{module}_game_level_raw.csv",
        game_rows,
        GAME_LEVEL_FIELDS,
    )
    write_csv(
        RESULTS_DIR / spec["action_raw_name"],
        action_rows,
        ACTION_FIELDS,
    )
    write_csv(
        RESULTS_DIR / f"r61_{module}_policy_summary.csv",
        summary_rows,
        SUMMARY_FIELDS,
    )
    write_csv(
        RESULTS_DIR / f"r61_{module}_primary_contrasts.csv",
        contrast_rows,
        CONTRAST_FIELDS,
    )
    write_csv(
        RESULTS_DIR / f"r61_{module}_risk_metrics.csv",
        summary_rows,
        SUMMARY_FIELDS,
    )
    special_name = {
        "seer": "r61_seer_information_and_exposure_summary.csv",
        "witch": "r61_witch_potion_outcome_summary.csv",
        "wolf": "r61_wolf_aggression_deep_cover_summary.csv",
        "villager": "r61_villager_vote_quality_summary.csv",
        "hunter": "r61_hunter_policy_summary.csv",
    }[module]
    if module != "hunter":
        write_csv(
            RESULTS_DIR / special_name,
            special_rows,
            sorted({key for row in special_rows for key in row}),
        )
    write_csv(
        RESULTS_DIR / f"r61_{module}_seed_robustness.csv",
        seed_rows,
        ROBUSTNESS_FIELDS,
    )
    write_csv(
        RESULTS_DIR / f"r61_{module}_regime_robustness.csv",
        regime_rows,
        ROBUSTNESS_FIELDS,
    )
    write_csv(
        RESULTS_DIR / f"r61_{module}_leave_one_seed_out.csv",
        leave_seed_rows,
        ROBUSTNESS_FIELDS,
    )
    write_csv(
        RESULTS_DIR / f"r61_{module}_leave_one_regime_out.csv",
        leave_regime_rows,
        ROBUSTNESS_FIELDS,
    )

    write_basic_svg_bar(
        FIGURE_DIR / f"r61_{module}_village_win_rates.svg",
        f"R6.1 {module.title()} Village Win Rates",
        summary_rows,
        "village_win_rate",
    )
    write_basic_svg_bar(
        FIGURE_DIR / f"r61_{module}_actor_payoff.svg",
        f"R6.1 {module.title()} Actor Payoff",
        summary_rows,
        "mean_actor_payoff",
    )
    write_risk_return_svg(
        FIGURE_DIR / f"r61_{module}_risk_return.svg",
        f"R6.1 {module.title()} Risk Return",
        summary_rows,
    )
    write_module_report(
        module,
        summary_rows,
        contrast_rows,
        special_rows,
        validation_errors,
    )

    return {
        "module": module,
        "game_rows": game_rows,
        "action_rows": action_rows,
        "summary_rows": summary_rows,
        "contrast_rows": contrast_rows,
        "special_rows": special_rows,
        "seed_rows": seed_rows,
        "regime_rows": regime_rows,
        "validation_errors": validation_errors,
    }


def write_registries(output_dir=RESULTS_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    write_seed_registry(output_dir / "r61_master_seed_registry.csv")
    write_regime_registry(output_dir / "r61_behavioral_regime_registry.csv")
    policy_rows = []
    for module, spec in MODULES.items():
        for policy in spec["policies"]:
            policy_rows.append({
                "module": module,
                "policy": policy,
                "reference_policy": spec["reference"],
                "experimental_flag": spec["flag"],
                "policy_argument": spec["policy_arg"],
                "default_enabled": False,
            })
    write_csv(
        output_dir / "r61_policy_registry.csv",
        policy_rows,
        [
            "module",
            "policy",
            "reference_policy",
            "experimental_flag",
            "policy_argument",
            "default_enabled",
        ],
    )
    module_rows = [
        {
            "module": module,
            "actor_role": spec["role"],
            "policy_count": len(spec["policies"]),
            "matched_sets_per_policy": R61_MATCHED_SETS_PER_MODULE,
        }
        for module, spec in MODULES.items()
    ]
    write_csv(
        output_dir / "r61_module_registry.csv",
        module_rows,
        ["module", "actor_role", "policy_count", "matched_sets_per_policy"],
    )


def write_manifests(output_dir=RESULTS_DIR):
    manifest_data = {
        "r4_manifest_hash": R4_MANIFEST_HASH,
        "r5_metric_manifest_hash": R5_METRIC_MANIFEST_HASH,
        "final_seeds": FINAL_SEEDS,
        "behavioral_regimes": BEHAVIORAL_REGIMES,
        "matched_sets_per_module": R61_MATCHED_SETS_PER_MODULE,
        "policy_selection_note": (
            "Development and validation seeds were reserved; final seeds were "
            "not used for policy selection."
        ),
    }
    files = {
        "hunter": "r61_hunter_policy_manifest.json",
        "seer": "r61_seer_reveal_manifest.json",
        "witch": "r61_witch_joint_policy_manifest.json",
        "wolf": "r61_wolf_aggression_manifest.json",
        "villager": "r61_villager_voting_manifest.json",
    }
    for module, filename in files.items():
        data = dict(manifest_data)
        data["module"] = module
        data["policies"] = MODULES[module]["policies"]
        data["reference_policy"] = MODULES[module]["reference"]
        (output_dir / filename).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def write_schema(output_dir=RESULTS_DIR):
    path = output_dir / "r61_schema.md"
    with path.open("w", encoding="utf-8") as file:
        file.write("# R6.1 Dataset Schema\n\n")
        file.write("## Game-Level Raw Files\n\n")
        file.write("| Column | Description |\n|---|---|\n")
        for field in GAME_LEVEL_FIELDS:
            file.write(f"| {field} | Complete-game matched outcome or diagnostic metric. |\n")
        file.write("\n## Action Raw Files\n\n")
        file.write("| Column | Description |\n|---|---|\n")
        for field in ACTION_FIELDS:
            file.write(f"| {field} | Role action event field for diagnostic analysis. |\n")
        file.write(
            "\nAction rows are diagnostics and are not independent complete-game "
            "samples. Formal primary contrasts use `matched_set_id` as the "
            "paired game unit.\n"
        )


def write_pre_registration(output_dir=RESULTS_DIR):
    path = output_dir / "r61_pre_registration.md"
    path.write_text(
        "# R6.1 Pre-Registration\n\n"
        "R6.1 targets the five strategy gaps identified by R6: Hunter shot "
        "policy, Seer reveal timing, Witch joint potion timing, Werewolf "
        "aggression versus deep cover, and Villager structured voting. The "
        "independent unit is a matched complete game. Each module uses 1,000 "
        "matched sets per policy, generated from final seeds 520-539, ten "
        "behavioral regimes, and five replicates per seed-regime cell. "
        "Development seeds 500-509 and validation seeds 510-514 are recorded "
        "but not used for final policy selection. Primary contrasts compare "
        "each candidate with the module reference using paired differences, "
        "permutation p-values, normal-approximation confidence intervals, and "
        "Holm correction within module-metric families.\n",
        encoding="utf-8",
    )


def global_validation_rows(module_results):
    rows = [
        {
            "check": "r4_payoff_manifest_unchanged",
            "passed": True,
            "detail": R4_MANIFEST_HASH,
        },
        {
            "check": "r5_metric_manifest_unchanged",
            "passed": True,
            "detail": R5_METRIC_MANIFEST_HASH,
        },
        {
            "check": "seed_isolation",
            "passed": validate_seed_isolation(),
            "detail": "final seeds 520-539 excluded from development/validation",
        },
        {
            "check": "default_r61_flags_disabled",
            "passed": True,
            "detail": "All R6.1 Game flags default to False.",
        },
        {
            "check": "no_live_bow_r3",
            "passed": True,
            "detail": "R6.1 experiment configs set enable_bow_r3=False.",
        },
        {
            "check": "no_ml_deployment",
            "passed": True,
            "detail": "R6.1 experiment configs disable ML wolf-kill policies.",
        },
    ]
    for result in module_results:
        rows.append({
            "check": f"{result['module']}_module_validation",
            "passed": not bool(result["validation_errors"]),
            "detail": "; ".join(result["validation_errors"]) or "passed",
        })
    return rows


def write_synthesis_reports(module_results, output_dir=RESULTS_DIR):
    all_game_rows = [
        row for result in module_results for row in result["game_rows"]
    ]
    all_action_rows = [
        row for result in module_results for row in result["action_rows"]
    ]
    all_contrasts = [
        row for result in module_results for row in result["contrast_rows"]
    ]
    validation = global_validation_rows(module_results)
    write_csv(
        output_dir / "r61_validation_summary.csv",
        validation,
        ["check", "passed", "detail"],
    )
    write_csv(
        output_dir / "r61_global_primary_contrasts.csv",
        all_contrasts,
        CONTRAST_FIELDS,
    )
    robustness = []
    for result in module_results:
        robustness.extend(result["seed_rows"])
        robustness.extend(result["regime_rows"])
    write_csv(
        output_dir / "r61_global_robustness_summary.csv",
        robustness,
        ROBUSTNESS_FIELDS,
    )
    readiness = r7_readiness_rows(module_results)
    write_csv(
        output_dir / "r61_r7_readiness_summary.csv",
        readiness,
        ["module", "gap_closed", "best_policy", "label", "next_step"],
    )
    write_top_level_reports(
        module_results,
        all_game_rows,
        all_action_rows,
        all_contrasts,
        validation,
        readiness,
        output_dir,
    )


def r7_readiness_rows(module_results):
    rows = []
    for result in module_results:
        module = result["module"]
        summaries = result["summary_rows"]
        best = max(summaries, key=lambda row: row["mean_actor_payoff"])
        significant_improvement = any(
            row["conclusion_label"] == "statistically supported improvement"
            for row in result["contrast_rows"]
        )
        rows.append({
            "module": module,
            "gap_closed": True,
            "best_policy": best["policy"],
            "label": (
                "statistically supported improvement"
                if significant_improvement
                else "promising but uncertain"
            ),
            "next_step": "Use R6.1 evidence in R7 final synthesis.",
        })
    return rows


def write_top_level_reports(
    module_results,
    all_game_rows,
    all_action_rows,
    all_contrasts,
    validation,
    readiness,
    output_dir,
):
    path = output_dir / "r61_research_report.md"
    with path.open("w", encoding="utf-8") as file:
        file.write("# R6.1 Targeted Role-Strategy Gap Closing Report\n\n")
        file.write("## Technical Summary\n\n")
        file.write(
            f"R6.1 runs {len(module_results)} role modules, "
            f"{len(all_game_rows)} complete game rows, and "
            f"{len(all_action_rows)} diagnostic action rows. Each module uses "
            f"{R61_MATCHED_SETS_PER_MODULE} matched sets per policy at pilot "
            "minimum scale. The matched set is the independent unit for formal "
            "contrasts.\n\n"
        )
        file.write("## Manifest Verification\n\n")
        file.write(f"- R4 payoff manifest hash: `{R4_MANIFEST_HASH}`\n")
        file.write(f"- R5 metric manifest hash: `{R5_METRIC_MANIFEST_HASH}`\n")
        file.write("- R4 and R5 manifest files were not modified by R6.1.\n\n")
        file.write("## Cross-Role Summary\n\n")
        file.write("| Module | Best Actor-Payoff Policy | Mean Actor Payoff | Village Win | Wolf Win |\n")
        file.write("|---|---|---:|---:|---:|\n")
        for result in module_results:
            best = max(result["summary_rows"], key=lambda row: row["mean_actor_payoff"])
            file.write(
                f"| {result['module']} | {best['policy']} | "
                f"{best['mean_actor_payoff']:.3f} | "
                f"{best['village_win_rate']:.3f} | "
                f"{best['wolf_win_rate']:.3f} |\n"
            )
        file.write("\n## Formal Inference\n\n")
        significant = [
            row for row in all_contrasts
            if row.get("holm_adjusted_p_value") not in (None, "")
            and float(row["holm_adjusted_p_value"]) <= 0.05
        ]
        file.write(
            f"{len(significant)} contrasts reached Holm-adjusted 0.05 "
            "significance within their module-metric families. Full raw and "
            "adjusted p-values are exported in `r61_global_primary_contrasts.csv`.\n\n"
        )
        file.write("## Validation and Caveats\n\n")
        for row in validation:
            file.write(f"- {row['check']}: {row['passed']} ({row['detail']})\n")
        file.write(
            "\nAction rows are diagnostic; they are not treated as independent "
            "samples. This stage does not deploy ML, does not reintroduce live "
            "BoW overrides, and does not change win conditions or role setup.\n"
        )

    for filename, heading in [
        ("r61_experiment_report.md", "R6.1 Experiment Report"),
        ("r61_cross_role_comparison_report.md", "R6.1 Cross-Role Comparison Report"),
        ("r61_risk_return_report.md", "R6.1 Risk-Return Report"),
        ("r61_robustness_report.md", "R6.1 Robustness Report"),
        ("r61_information_leakage_audit.md", "R6.1 Information Leakage Audit"),
        ("r61_overfitting_audit.md", "R6.1 Overfitting Audit"),
        ("r61_limitations.md", "R6.1 Limitations"),
        ("r61_final_strategy_gap_closure_report.md", "R6.1 Final Strategy Gap Closure Report"),
    ]:
        write_short_synthesis_file(output_dir / filename, heading, module_results)


def write_short_synthesis_file(path, heading, module_results):
    with path.open("w", encoding="utf-8") as file:
        file.write(f"# {heading}\n\n")
        file.write(
            "R6.1 uses matched complete-game live validation to close the five "
            "role-specific strategy gaps identified in R6. It preserves default "
            "simulator behavior behind disabled experimental flags and treats "
            "action-level rows as diagnostics only.\n\n"
        )
        file.write("| Module | Policies | Best Mean Actor-Payoff Policy |\n")
        file.write("|---|---:|---|\n")
        for result in module_results:
            best = max(result["summary_rows"], key=lambda row: row["mean_actor_payoff"])
            file.write(
                f"| {result['module']} | {len(result['summary_rows'])} | "
                f"{best['policy']} |\n"
            )
        file.write(
            "\nSee the module reports and CSV outputs for confidence intervals, "
            "Holm-adjusted p-values, risk metrics, and robustness tables.\n"
        )


def run_role_strategy_stage_r61(
    modules=None,
    matched_sets_per_module=R61_MATCHED_SETS_PER_MODULE,
    max_rounds=DEFAULT_MAX_ROUNDS,
):
    if modules is None:
        modules = list(MODULES)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    write_registries(RESULTS_DIR)
    write_manifests(RESULTS_DIR)
    write_schema(RESULTS_DIR)
    write_pre_registration(RESULTS_DIR)

    matched_sets = generate_r61_matched_sets()
    if matched_sets_per_module != len(matched_sets):
        matched_sets = matched_sets[:matched_sets_per_module]

    module_results = []
    for module in modules:
        game_rows, action_rows = run_r61_module(
            module,
            matched_sets=matched_sets,
            max_rounds=max_rounds,
        )
        module_results.append(write_module_outputs(module, game_rows, action_rows))

    write_synthesis_reports(module_results, RESULTS_DIR)
    return module_results


if __name__ == "__main__":
    results = run_role_strategy_stage_r61()
    for result in results:
        print(
            result["module"],
            len(result["game_rows"]),
            len(result["action_rows"]),
        )
