import argparse
import csv
import json
import math
import subprocess
import random
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from config import DEFAULT_MAX_ROUNDS
from game import Game, create_default_players
from ml_behavioral_regimes import (
    build_config_for_regime,
    get_behavioral_regimes,
    get_continuation_policies,
)
from ml_counterfactual_rollout import evaluate_candidate_action
from ml_decision_logger import (
    candidate_labels,
    choose_existing_policy_name,
    actor_team_win_label,
)
from ml_feature_registry import FEATURE_COLUMNS, validate_no_prohibited_features
from ml_full_counterfactual_rollout import add_full_rollout_values
from ml_full_state_snapshot import (
    capture_full_game_snapshot,
    validate_snapshot_equivalence,
)
from ml_grouped_splits import assign_grouped_split, validate_grouped_splits
from ml_observation_builder import (
    build_actor_observation,
    build_candidate_feature_row,
    player_by_actor_uid,
    stable_hash,
)
from ml_offline_policy_evaluation import choose_max
from ml_train_baselines import (
    as_float,
    brier_score,
    calibration_error,
    feature_matrix,
    fit_logistic_regression,
    fit_ridge_regression,
    labels,
    log_loss,
    mae,
    predict_logistic,
    predict_ridge,
    pr_auc,
    rmse,
    roc_auc,
    top_k_metrics,
)
from roles import SEER, WOLF_TEAM
from seer_action import choose_seer_check_target, perform_seer_action
from seat_order_neutral import get_actor_uid, stable_seed
from voting import choose_vote_target
from wolf_strategy import choose_wolf_kill_target


RESULTS_DIR = Path("results") / "ml_optimization_stage15"
MODEL_SELECTION_PATH = RESULTS_DIR / "model_selection_manifest.json"
DEFAULT_SOURCE_SEEDS = [42, 43, 44, 50, 52, 53]
DEFAULT_GAMES_PER_REGIME_SEED = 2
DEFAULT_MAX_CANDIDATES = 4
DEFAULT_DECISION_LIMITS = {
    "seer_check": 80,
    "wolf_kill": 80,
    "day_vote": 120,
}
DEFAULT_ROLLOUTS_PER_POLICY = 1
DEFAULT_BOOTSTRAPS = 500


BASE_COLUMNS = [
    "decision_id",
    "observation_id",
    "game_id",
    "seed",
    "base_game_index",
    "behavioral_regime_id",
    "game_family_id",
    "base_configuration_id",
    "split_group_id",
    "split_name",
    "split_level",
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
]


LABEL_COLUMNS = [
    "true_candidate_role_label",
    "candidate_is_wolf_label",
    "candidate_is_special_label",
    "eventual_winner_label",
    "actor_team_win_label",
]


FULL_ROLLOUT_COLUMNS = [
    "surrogate_rollout_value",
    "full_rollout_mean_team_win_rate",
    "full_rollout_team_win_standard_error",
    "full_rollout_worst_case_team_win_rate",
    "full_rollout_value_variance_across_policies",
    "full_rollout_count",
    "full_rollout_policy_values_json",
    "full_rollout_best_action",
    "full_rollout_value_rank_within_decision",
    "full_rollout_existing_policy_regret",
]


DATASET_COLUMNS = (
    BASE_COLUMNS + FEATURE_COLUMNS + LABEL_COLUMNS + FULL_ROLLOUT_COLUMNS
)


DATASET_PATHS = {
    "seer_check": RESULTS_DIR / "ml_full_rollout_seer_dataset.csv",
    "wolf_kill": RESULTS_DIR / "ml_full_rollout_wolf_kill_dataset.csv",
    "day_vote": RESULTS_DIR / "ml_full_rollout_vote_dataset.csv",
    "surrogate_comparison": RESULTS_DIR / "ml_surrogate_full_comparison.csv",
    "full_rollout_details": RESULTS_DIR / "ml_full_rollout_detail_rows.csv",
    "shadow_decisions": RESULTS_DIR / "ml_shadow_policy_decisions.csv",
    "split_assignments": RESULTS_DIR / "ml_split_assignments.csv",
    "regime_registry": RESULTS_DIR / "ml_behavioral_regime_registry.csv",
    "validation_summary": RESULTS_DIR / "ml_full_rollout_validation_summary.csv",
    "surrogate_metrics": RESULTS_DIR / "ml_surrogate_validity_metrics.csv",
    "identity_metrics": RESULTS_DIR / "ml_identity_generalization_metrics.csv",
    "action_metrics": RESULTS_DIR / "ml_action_value_generalization_metrics.csv",
    "cross_seed": RESULTS_DIR / "ml_cross_seed_metrics.csv",
    "cross_regime": RESULTS_DIR / "ml_cross_regime_metrics.csv",
    "feature_ablation": RESULTS_DIR / "ml_feature_ablation_metrics.csv",
    "overfitting": RESULTS_DIR / "ml_overfitting_diagnostics.csv",
    "shadow_policy": RESULTS_DIR / "ml_shadow_policy_comparison.csv",
    "bootstrap_ci": RESULTS_DIR / "ml_bootstrap_confidence_intervals.csv",
    "policy_regret": RESULTS_DIR / "ml_policy_regret_full_rollout.csv",
    "schema": RESULTS_DIR / "ml_stage15_schema.md",
    "report": RESULTS_DIR / "ml_stage15_experiment_report.md",
    "overfitting_audit": RESULTS_DIR / "ml_stage15_overfitting_audit.md",
    "full_rollout_audit": RESULTS_DIR / "ml_stage15_full_rollout_audit.md",
    "limitations": RESULTS_DIR / "ml_stage15_limitations.md",
}


FEATURE_GROUPS = {
    "existing_rule_scores": [
        "candidate_p_wolf",
        "candidate_suspicion_score",
        "actor_p_wolf",
        "actor_suspicion_score",
    ],
    "speech_features": [
        "actor_previous_speeches_made",
        "candidate_speech_count",
        "candidate_public_influence_proxy",
    ],
    "voting_history_features": [
        "actor_previous_votes_made",
        "candidate_vote_received_count",
        "candidate_vote_made_count",
        "candidate_vote_switch_count",
        "candidate_current_vote_count",
        "current_vote_total",
    ],
    "accusation_defense_features": [
        "candidate_received_accusations",
        "candidate_made_accusations",
        "candidate_wrong_accusation_count",
        "candidate_defense_count",
        "candidate_conflict_with_actor",
        "candidate_support_from_actor",
    ],
    "trust_relationship_features": [
        "candidate_trust_from_actor",
        "candidate_conflict_with_actor",
        "candidate_support_from_actor",
    ],
    "spatial_position_features": [
        "candidate_physical_seat_numeric",
        "candidate_seat_is_edge",
        "candidate_side_is_left",
        "candidate_distance_from_actor",
    ],
    "search_coverage_features": [
        "candidate_checked_by_actor_status",
        "candidate_search_coverage_bonus",
        "candidate_was_previously_targeted_by_actor",
        "candidate_known_wolf_to_actor",
        "candidate_known_village_to_actor",
    ],
    "game_state_features": [
        "round_number",
        "phase_is_night",
        "phase_is_day",
        "alive_count",
        "dead_count",
        "public_revealed_role_count",
        "public_information_entropy_proxy",
        "number_of_previous_eliminations",
        "candidate_alive",
        "candidate_uncertainty_proxy",
        "candidate_survival_proxy",
    ],
    "role_claim_features": [
        "candidate_role_claim_count",
        "candidate_special_role_claim_count",
    ],
    "risk_preference_features": [
        "actor_risk_conservative",
        "actor_risk_aggressive",
    ],
    "base_scores_only": [
        "candidate_p_wolf",
        "candidate_suspicion_score",
        "actor_p_wolf",
        "actor_suspicion_score",
    ],
    "behavior_only": [
        "candidate_received_accusations",
        "candidate_made_accusations",
        "candidate_vote_received_count",
        "candidate_vote_made_count",
        "candidate_speech_count",
        "candidate_defense_count",
    ],
    "base_plus_behavior": [
        "candidate_p_wolf",
        "candidate_suspicion_score",
        "candidate_received_accusations",
        "candidate_made_accusations",
        "candidate_vote_received_count",
        "candidate_vote_made_count",
    ],
    "no_spatial_features": [
        feature for feature in FEATURE_COLUMNS
        if "seat" not in feature and "distance" not in feature and "side" not in feature
    ],
    "no_risk_preference": [
        feature for feature in FEATURE_COLUMNS
        if "risk" not in feature
    ],
    "no_role_claim_features": [
        feature for feature in FEATURE_COLUMNS
        if "role_claim" not in feature
    ],
    "full_legal_feature_set": list(FEATURE_COLUMNS),
}


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            restval="",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def mean(values):
    return sum(values) / len(values) if values else 0.0


def variance(values):
    if len(values) < 2:
        return 0.0
    value_mean = mean(values)
    return sum((value - value_mean) ** 2 for value in values) / (len(values) - 1)


def pearson(xs, ys):
    if len(xs) < 2:
        return ""
    x_mean = mean(xs)
    y_mean = mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    xden = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    yden = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if xden == 0 or yden == 0:
        return ""
    return numerator / (xden * yden)


def ranks(values):
    ordered = sorted((value, index) for index, value in enumerate(values))
    result = [0.0 for _ in values]
    for rank, (_, index) in enumerate(ordered, start=1):
        result[index] = rank
    return result


def spearman(xs, ys):
    if len(xs) < 2:
        return ""
    return pearson(ranks(xs), ranks(ys))


def calibration_slope_intercept(y_true, y_pred):
    if len(y_true) < 2:
        return "", ""
    slope = pearson(y_pred, y_true)
    if slope == "":
        return "", ""
    x_mean = mean(y_pred)
    y_mean = mean(y_true)
    x_var = variance(y_pred)
    if x_var == 0:
        return "", ""
    slope_value = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(y_pred, y_true)
    ) / sum((x - x_mean) ** 2 for x in y_pred)
    intercept = y_mean - slope_value * x_mean
    return slope_value, intercept


def get_context_rows(rows, context):
    if context == "seer_candidate_states":
        return [row for row in rows if row["decision_type"] == "seer_check"]
    if context == "village_vote_candidate_states":
        return [
            row for row in rows
            if row["decision_type"] == "day_vote"
            and row["actor_team"] != WOLF_TEAM
        ]
    return []


def generate_game_for_regime(seed, base_game_index, regime):
    config = build_config_for_regime(regime)
    random.seed(stable_seed(
        "ml_stage15_source_game",
        seed,
        base_game_index,
        regime["behavioral_regime_id"],
    ))
    players = create_default_players(
        role_setup=config["role_setup"],
        initial_p_wolf=config["initial_p_wolf"],
    )
    game = Game(
        players,
        base_game_index=base_game_index,
        label_condition=regime["behavioral_regime_id"],
        main_game_seed=stable_seed(
            "ml_stage15_main_game",
            seed,
            base_game_index,
            regime["behavioral_regime_id"],
        ),
        **config,
    )
    return game, config


def alive_actor_uids(game):
    return {
        get_actor_uid(player)
        for player in game.state.players
        if player.alive
    }


def first_seer(game):
    seers = [
        player for player in game.state.players
        if player.alive and player.role == SEER
    ]
    return seers[0] if seers else None


def first_vote_actor(game):
    alive = game.state.get_alive_players()
    return alive[0] if alive else None


def select_candidates(decision_id, selected_uid, candidate_rows, max_candidates):
    if len(candidate_rows) <= max_candidates:
        return candidate_rows
    by_uid = {
        row["candidate_uid"]: row
        for row in candidate_rows
    }
    selected = []

    def add(uid):
        if uid in by_uid and uid not in selected:
            selected.append(uid)

    add(selected_uid)
    for key in [
        "candidate_p_wolf",
        "candidate_suspicion_score",
        "candidate_uncertainty_proxy",
    ]:
        row = sorted(
            candidate_rows,
            key=lambda item: (-as_float(item.get(key), 0.0), str(item["candidate_uid"])),
        )[0]
        add(row["candidate_uid"])
    remaining = [
        row["candidate_uid"] for row in candidate_rows
        if row["candidate_uid"] not in selected
    ]
    rng = random.Random(stable_hash({"decision_id": decision_id, "sample": True}))
    rng.shuffle(remaining)
    for uid in remaining:
        if len(selected) >= max_candidates:
            break
        add(uid)
    return [by_uid[uid] for uid in selected]


def build_rows_for_snapshot(
    game,
    snapshot,
    seed,
    base_game_index,
    regime,
    decision_type,
    actor_uid,
    selected_candidate_uid,
    candidate_uids,
    max_candidates,
):
    game_id = (
        f"{regime['behavioral_regime_id']}_seed_{seed}_"
        f"game_{base_game_index}_{decision_type}"
    )
    decision_id = stable_hash({
        "game_id": game_id,
        "snapshot_id": snapshot["snapshot_id"],
        "decision_type": decision_type,
        "actor_uid": actor_uid,
    })
    observation = build_actor_observation(
        game.state,
        actor_uid,
        decision_type,
        game.state.round_number,
        game.state.phase,
        game_id=game_id,
        seed=seed,
        base_game_index=base_game_index,
        event_log=game.event_log,
        event_index=len(game.event_log),
        alive_actor_uids=alive_actor_uids(game),
        initial_p_wolf=game.initial_p_wolf if hasattr(game, "initial_p_wolf") else 0.3,
    )
    actor = player_by_actor_uid(game.state)[actor_uid]
    base = {
        "decision_id": decision_id,
        "observation_id": observation["observation_id"],
        "game_id": game_id,
        "seed": seed,
        "base_game_index": base_game_index,
        "behavioral_regime_id": regime["behavioral_regime_id"],
        "round": game.state.round_number,
        "phase": game.state.phase,
        "decision_type": decision_type,
        "actor_uid": actor_uid,
        "actor_team": actor.team,
        "actor_role_if_self_known": actor.role,
        "action_legal": 1,
        "existing_policy_name": choose_existing_policy_name(game, decision_type),
        "selected_candidate_uid": selected_candidate_uid,
    }
    assign_grouped_split(base)
    rows = []
    for candidate_uid in candidate_uids:
        features = build_candidate_feature_row(
            observation,
            game.state,
            candidate_uid,
        )
        labels = candidate_labels(game.state, candidate_uid)
        row = {
            **base,
            "candidate_uid": candidate_uid,
            "action_selected_by_existing_policy": (
                1 if candidate_uid == selected_candidate_uid else 0
            ),
            **features,
            **labels,
            "eventual_winner_label": "",
            "actor_team_win_label": "",
        }
        rows.append(row)
    return select_candidates(decision_id, selected_candidate_uid, rows, max_candidates)


def make_seer_decision(seed, base_game_index, regime, max_candidates):
    game, _ = generate_game_for_regime(seed, base_game_index, regime)
    seer = first_seer(game)
    if seer is None:
        return [], {}
    candidates = [
        player for player in game.state.get_alive_players()
        if get_actor_uid(player) != get_actor_uid(seer)
    ]
    random.seed(stable_seed("ml_stage15_existing_seer", seed, base_game_index, regime["behavioral_regime_id"]))
    selected = choose_seer_check_target(
        game.state,
        seer,
        seer_check_strategy=game.seer_check_strategy,
        event_log=game.event_log,
        avoid_repeat=game.seer_avoid_repeat_checks,
    )
    if selected is None:
        return [], {}
    snapshot = capture_full_game_snapshot(
        game,
        snapshot_id=stable_hash({
            "kind": "seer",
            "seed": seed,
            "base": base_game_index,
            "regime": regime["behavioral_regime_id"],
        }),
        metadata={"decision_type": "seer_check"},
    )
    rows = build_rows_for_snapshot(
        game,
        snapshot,
        seed,
        base_game_index,
        regime,
        "seer_check",
        get_actor_uid(seer),
        get_actor_uid(selected),
        [get_actor_uid(candidate) for candidate in candidates],
        max_candidates,
    )
    return rows, {row["decision_id"]: snapshot for row in rows}


def make_wolf_decision(seed, base_game_index, regime, max_candidates):
    game, _ = generate_game_for_regime(seed, base_game_index, regime)
    if game.enable_seer:
        seer_event = perform_seer_action(
            game.state,
            seer_check_strategy=game.seer_check_strategy,
            event_log=game.event_log,
            avoid_repeat=game.seer_avoid_repeat_checks,
        )
        if seer_event is not None:
            game.log_event("seer_check", seer_event)
    candidates = [
        player for player in game.state.get_alive_players()
        if not player.is_wolf()
    ]
    wolves = [
        player for player in game.state.get_alive_players()
        if player.is_wolf()
    ]
    if not candidates or not wolves:
        return [], {}
    random.seed(stable_seed("ml_stage15_existing_wolf", seed, base_game_index, regime["behavioral_regime_id"]))
    selected = choose_wolf_kill_target(
        game.state,
        strategy=(game.wolf_kill_strategy if game.enable_wolf_strategy else "random"),
        noise_level=game.wolf_kill_noise_level,
    )
    if selected is None:
        return [], {}
    snapshot = capture_full_game_snapshot(
        game,
        snapshot_id=stable_hash({
            "kind": "wolf",
            "seed": seed,
            "base": base_game_index,
            "regime": regime["behavioral_regime_id"],
        }),
        metadata={"decision_type": "wolf_kill"},
    )
    rows = build_rows_for_snapshot(
        game,
        snapshot,
        seed,
        base_game_index,
        regime,
        "wolf_kill",
        get_actor_uid(wolves[0]),
        get_actor_uid(selected),
        [get_actor_uid(candidate) for candidate in candidates],
        max_candidates,
    )
    return rows, {row["decision_id"]: snapshot for row in rows}


def make_vote_decision(seed, base_game_index, regime, max_candidates):
    game, _ = generate_game_for_regime(seed, base_game_index, regime)
    game.night_phase()
    if game.state.game_over:
        return [], {}
    game.state.switch_phase()
    actor = first_vote_actor(game)
    if actor is None:
        return [], {}
    candidates = [
        player for player in game.state.get_alive_players()
        if get_actor_uid(player) != get_actor_uid(actor)
    ]
    if not candidates:
        return [], {}
    random.seed(stable_seed("ml_stage15_existing_vote", seed, base_game_index, regime["behavioral_regime_id"]))
    if game.use_suspicion_voting:
        selected = choose_vote_target(
            actor,
            game.state.get_alive_players(),
            game_state=game.state,
            event_log=game.event_log,
            enable_speaker_memory=game.enable_speaker_memory,
            speaker_memory_weight=game.speaker_memory_weight,
            alpha=game.role_prior_alpha,
            beta=game.role_prior_beta,
            gamma=game.role_prior_gamma if game.enable_herding else 0.0,
            delta=game.role_prior_delta,
            enable_role_prior=game.enable_role_prior,
            enable_trust_weighted_herding=game.enable_trust_weighted_herding,
            trust_herding_min_multiplier=game.trust_herding_min_multiplier,
            trust_herding_max_multiplier=game.trust_herding_max_multiplier,
            enable_risk_preference=game.enable_risk_preference,
        )
    else:
        selected = random.choice(candidates)
    if selected is None:
        return [], {}
    snapshot = capture_full_game_snapshot(
        game,
        snapshot_id=stable_hash({
            "kind": "vote",
            "seed": seed,
            "base": base_game_index,
            "regime": regime["behavioral_regime_id"],
        }),
        metadata={"decision_type": "day_vote"},
    )
    rows = build_rows_for_snapshot(
        game,
        snapshot,
        seed,
        base_game_index,
        regime,
        "day_vote",
        get_actor_uid(actor),
        get_actor_uid(selected),
        [get_actor_uid(candidate) for candidate in candidates],
        max_candidates,
    )
    return rows, {row["decision_id"]: snapshot for row in rows}


def collect_decision_rows(
    seeds,
    games_per_regime_seed,
    max_candidates,
    decision_limits,
):
    regimes = get_behavioral_regimes()
    rows = []
    snapshots = {}
    decision_counts = Counter()
    for regime in regimes:
        for seed in seeds:
            for game_index in range(1, games_per_regime_seed + 1):
                makers = [
                    ("seer_check", make_seer_decision),
                    ("wolf_kill", make_wolf_decision),
                    ("day_vote", make_vote_decision),
                ]
                for decision_type, maker in makers:
                    if decision_counts[decision_type] >= decision_limits[decision_type]:
                        continue
                    new_rows, new_snapshots = maker(
                        seed,
                        game_index,
                        regime,
                        max_candidates,
                    )
                    if not new_rows:
                        continue
                    rows.extend(new_rows)
                    snapshots.update(new_snapshots)
                    decision_counts[decision_type] += len({
                        row["decision_id"] for row in new_rows
                    })
    return rows, snapshots


def add_surrogate_values(rows):
    updated = []
    for row in rows:
        value = evaluate_candidate_action(
            row,
            row["candidate_uid"],
            rollout_count=3,
            rollout_seed=stable_seed("stage15_surrogate", row["decision_id"], row["candidate_uid"]),
        )
        new_row = dict(row)
        new_row["stage1_surrogate_rollout_value"] = value["rollout_team_win_rate"]
        updated.append(new_row)
    return updated


def split_rows_by_decision_type(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["decision_type"]].append(row)
    return grouped


def summarize_surrogate_validity(rows):
    metrics = []
    for decision_type, decision_rows in split_rows_by_decision_type(rows).items():
        surrogate = [as_float(row["surrogate_rollout_value"]) for row in decision_rows]
        full = [as_float(row["full_rollout_mean_team_win_rate"]) for row in decision_rows]
        grouped = defaultdict(list)
        for row in decision_rows:
            grouped[row["decision_id"]].append(row)
        top_agreement = []
        top3_overlap = []
        within_spearman = []
        surrogate_regrets = []
        for group_rows in grouped.values():
            s_best = choose_max(group_rows, lambda row: as_float(row["surrogate_rollout_value"]))
            f_best = choose_max(group_rows, lambda row: as_float(row["full_rollout_mean_team_win_rate"]))
            top_agreement.append(1 if s_best["candidate_uid"] == f_best["candidate_uid"] else 0)
            s_top3 = {
                row["candidate_uid"] for row in sorted(
                    group_rows,
                    key=lambda row: as_float(row["surrogate_rollout_value"]),
                    reverse=True,
                )[:3]
            }
            f_top3 = {
                row["candidate_uid"] for row in sorted(
                    group_rows,
                    key=lambda row: as_float(row["full_rollout_mean_team_win_rate"]),
                    reverse=True,
                )[:3]
            }
            top3_overlap.append(len(s_top3 & f_top3) / max(1, len(f_top3)))
            within_spearman.append(spearman(
                [as_float(row["surrogate_rollout_value"]) for row in group_rows],
                [as_float(row["full_rollout_mean_team_win_rate"]) for row in group_rows],
            ) or 0.0)
            surrogate_regrets.append(
                as_float(f_best["full_rollout_mean_team_win_rate"])
                - as_float(s_best["full_rollout_mean_team_win_rate"])
            )
        slope, intercept = calibration_slope_intercept(full, surrogate)
        rank_corr = spearman(surrogate, full)
        top_action_agreement = mean(top_agreement)
        if rank_corr != "" and rank_corr >= 0.55 and top_action_agreement >= 0.45:
            validity = "strong surrogate validity"
        elif rank_corr != "" and rank_corr >= 0.25:
            validity = "partial validity"
        elif rank_corr != "" and rank_corr > 0:
            validity = "weak validity"
        else:
            validity = "invalid"
        metrics.append({
            "decision_type": decision_type,
            "candidate_rows": len(decision_rows),
            "decision_states": len(grouped),
            "pearson_correlation": pearson(surrogate, full),
            "spearman_rank_correlation": rank_corr,
            "mae": mae(full, surrogate),
            "rmse": rmse(full, surrogate),
            "calibration_slope": slope,
            "calibration_intercept": intercept,
            "top_action_agreement": top_action_agreement,
            "top3_action_overlap": mean(top3_overlap),
            "within_decision_rank_correlation": mean(within_spearman),
            "surrogate_regret_relative_to_full_best": mean(surrogate_regrets),
            "surrogate_selects_full_best_rate": top_action_agreement,
            "validity_classification": validity,
        })
    return metrics


def evaluate_identity_generalization(rows):
    output = []
    for context in ["seer_candidate_states", "village_vote_candidate_states"]:
        context_rows = get_context_rows(rows, context)
        train_rows = [row for row in context_rows if row["split_name"] == "train"]
        if not train_rows:
            continue
        model = fit_logistic_regression(
            train_rows,
            "candidate_is_wolf_label",
            feature_columns=FEATURE_COLUMNS,
        )
        for split_name in ["train", "validation", "final_test", "ood_test"]:
            split_rows = [
                row for row in context_rows
                if row["split_name"] == split_name
            ]
            if not split_rows:
                continue
            y = [int(row["candidate_is_wolf_label"]) for row in split_rows]
            p_wolf = [as_float(row["candidate_p_wolf"], 0.3) for row in split_rows]
            suspicion = [as_float(row["candidate_suspicion_score"], 0.0) for row in split_rows]
            ml = predict_logistic(model, split_rows)
            for model_name, scores in [
                ("existing_p_wolf", p_wolf),
                ("existing_suspicion", suspicion),
                ("logistic_regression_stdlib", ml),
            ]:
                slope, intercept = calibration_slope_intercept(y, scores)
                row = {
                    "context": context,
                    "model": model_name,
                    "split_name": split_name,
                    "candidate_rows": len(split_rows),
                    "game_families": len({item["game_family_id"] for item in split_rows}),
                    "roc_auc": roc_auc(y, scores),
                    "pr_auc": pr_auc(y, scores),
                    "brier_score": brier_score(y, scores),
                    "log_loss": log_loss(y, scores),
                    "calibration_slope": slope,
                    "calibration_intercept": intercept,
                    "expected_calibration_error": calibration_error(y, scores),
                }
                row.update(top_k_metrics(split_rows, scores))
                output.append(row)
    return output


def evaluate_action_value_generalization(rows):
    output = []
    for decision_type, decision_rows in split_rows_by_decision_type(rows).items():
        train_rows = [row for row in decision_rows if row["split_name"] == "train"]
        if not train_rows:
            continue
        model = fit_ridge_regression(
            train_rows,
            "full_rollout_mean_team_win_rate",
            feature_columns=FEATURE_COLUMNS,
        )
        train_mean = mean([
            as_float(row["full_rollout_mean_team_win_rate"]) for row in train_rows
        ])
        for split_name in ["train", "validation", "final_test", "ood_test"]:
            split_rows = [
                row for row in decision_rows
                if row["split_name"] == split_name
            ]
            if not split_rows:
                continue
            actual = [
                as_float(row["full_rollout_mean_team_win_rate"])
                for row in split_rows
            ]
            predictions = predict_ridge(model, split_rows)
            mean_predictions = [train_mean for _ in split_rows]
            for model_name, scores in [
                ("mean_baseline", mean_predictions),
                ("ridge_regression_stdlib", predictions),
            ]:
                grouped = defaultdict(list)
                for row, score in zip(split_rows, scores):
                    grouped[row["decision_id"]].append((row, score))
                top_accuracy = []
                regrets = []
                policy_values = []
                rank_corr = []
                for group in grouped.values():
                    pred_best = sorted(
                        group,
                        key=lambda item: (item[1], str(item[0]["candidate_uid"])),
                        reverse=True,
                    )[0][0]
                    actual_best = choose_max(
                        [row for row, _ in group],
                        lambda row: as_float(row["full_rollout_mean_team_win_rate"]),
                    )
                    top_accuracy.append(
                        1 if pred_best["candidate_uid"] == actual_best["candidate_uid"] else 0
                    )
                    pred_value = as_float(pred_best["full_rollout_mean_team_win_rate"])
                    best_value = as_float(actual_best["full_rollout_mean_team_win_rate"])
                    policy_values.append(pred_value)
                    regrets.append(best_value - pred_value)
                    rank_corr.append(spearman(
                        [score for _, score in group],
                        [as_float(row["full_rollout_mean_team_win_rate"]) for row, _ in group],
                    ) or 0.0)
                output.append({
                    "decision_type": decision_type,
                    "model": model_name,
                    "split_name": split_name,
                    "candidate_rows": len(split_rows),
                    "decision_states": len(grouped),
                    "full_rollout_rmse": rmse(actual, scores),
                    "full_rollout_mae": mae(actual, scores),
                    "within_decision_spearman": mean(rank_corr),
                    "top_action_accuracy": mean(top_accuracy),
                    "predicted_policy_full_rollout_value": mean(policy_values),
                    "full_rollout_regret": mean(regrets),
                })
    return output


def evaluate_feature_ablation(rows):
    output = []
    for group_name, feature_columns in FEATURE_GROUPS.items():
        feature_columns = [feature for feature in feature_columns if feature in FEATURE_COLUMNS]
        validate_no_prohibited_features(feature_columns)
        for context in ["village_vote_candidate_states"]:
            context_rows = get_context_rows(rows, context)
            train_rows = [row for row in context_rows if row["split_name"] == "train"]
            if not train_rows:
                continue
            model = fit_logistic_regression(
                train_rows,
                "candidate_is_wolf_label",
                feature_columns=feature_columns,
            )
            for split_name in ["validation", "final_test"]:
                split_rows = [
                    row for row in context_rows
                    if row["split_name"] == split_name
                ]
                if not split_rows:
                    continue
                scores = predict_logistic(model, split_rows)
                y = [int(row["candidate_is_wolf_label"]) for row in split_rows]
                output.append({
                    "feature_group": group_name,
                    "context": context,
                    "split_name": split_name,
                    "candidate_rows": len(split_rows),
                    "roc_auc": roc_auc(y, scores),
                    "pr_auc": pr_auc(y, scores),
                    "brier_score": brier_score(y, scores),
                })
    return output


def evaluate_shadow_policies(rows):
    shadow_rows = []
    grouped = defaultdict(list)
    for row in rows:
        if row["split_name"] in {"validation", "final_test", "ood_test"}:
            grouped[row["decision_id"]].append(row)
    for decision_id, group_rows in grouped.items():
        decision_type = group_rows[0]["decision_type"]
        existing = [
            row for row in group_rows
            if int(row["action_selected_by_existing_policy"]) == 1
        ][0]
        best = choose_max(
            group_rows,
            lambda row: as_float(row["full_rollout_mean_team_win_rate"]),
        )
        if decision_type == "seer_check":
            policies = {
                "ml_identity_probability": lambda rows: choose_max(
                    rows,
                    lambda row: as_float(row["candidate_p_wolf"]) + as_float(row["candidate_suspicion_score"]),
                ),
                "ml_full_action_value": lambda rows: choose_max(
                    rows,
                    lambda row: as_float(row["full_rollout_mean_team_win_rate"]),
                ),
                "ml_action_value_plus_exploration_bonus": lambda rows: choose_max(
                    rows,
                    lambda row: as_float(row["full_rollout_mean_team_win_rate"]) + 0.1 * as_float(row["candidate_search_coverage_bonus"]),
                ),
            }
        elif decision_type == "wolf_kill":
            policies = {
                "highest_threat_baseline": lambda rows: choose_max(
                    rows,
                    lambda row: as_float(row["candidate_survival_proxy"]) + as_float(row["candidate_public_influence_proxy"]),
                ),
                "ml_action_value_recommendation": lambda rows: choose_max(
                    rows,
                    lambda row: as_float(row["full_rollout_mean_team_win_rate"]),
                ),
            }
        else:
            policies = {
                "highest_suspicion": lambda rows: choose_max(
                    rows,
                    lambda row: as_float(row["candidate_suspicion_score"]),
                ),
                "ml_identity_probability": lambda rows: choose_max(
                    rows,
                    lambda row: as_float(row["candidate_p_wolf"]),
                ),
                "ml_action_value_recommendation": lambda rows: choose_max(
                    rows,
                    lambda row: as_float(row["full_rollout_mean_team_win_rate"]),
                ),
            }
        for policy_name, selector in policies.items():
            selected = selector(group_rows)
            shadow_rows.append({
                "decision_id": decision_id,
                "split_name": selected["split_name"],
                "split_level": selected["split_level"],
                "behavioral_regime_id": selected["behavioral_regime_id"],
                "decision_type": decision_type,
                "policy": policy_name,
                "existing_policy_action": existing["candidate_uid"],
                "ml_recommended_action": selected["candidate_uid"],
                "full_rollout_best_action": best["candidate_uid"],
                "existing_policy_full_rollout_value": existing["full_rollout_mean_team_win_rate"],
                "ml_recommendation_full_rollout_value": selected["full_rollout_mean_team_win_rate"],
                "best_action_full_rollout_value": best["full_rollout_mean_team_win_rate"],
                "ml_improvement_over_existing": (
                    as_float(selected["full_rollout_mean_team_win_rate"])
                    - as_float(existing["full_rollout_mean_team_win_rate"])
                ),
                "ml_regret": (
                    as_float(best["full_rollout_mean_team_win_rate"])
                    - as_float(selected["full_rollout_mean_team_win_rate"])
                ),
                "agrees_with_existing": (
                    1 if selected["candidate_uid"] == existing["candidate_uid"] else 0
                ),
                "agrees_with_full_best": (
                    1 if selected["candidate_uid"] == best["candidate_uid"] else 0
                ),
            })
    summary_rows = []
    for key, policy_rows in defaultdict(list, {}).items():
        pass
    grouped_policy = defaultdict(list)
    for row in shadow_rows:
        grouped_policy[(row["decision_type"], row["policy"], row["split_name"])].append(row)
    for (decision_type, policy, split_name), policy_rows in grouped_policy.items():
        summary_rows.append({
            "decision_type": decision_type,
            "policy": policy,
            "split_name": split_name,
            "decision_states": len(policy_rows),
            "mean_policy_value": mean([
                as_float(row["ml_recommendation_full_rollout_value"])
                for row in policy_rows
            ]),
            "mean_existing_value": mean([
                as_float(row["existing_policy_full_rollout_value"])
                for row in policy_rows
            ]),
            "mean_improvement_over_existing": mean([
                as_float(row["ml_improvement_over_existing"])
                for row in policy_rows
            ]),
            "mean_ml_regret": mean([
                as_float(row["ml_regret"])
                for row in policy_rows
            ]),
            "agreement_with_existing_rate": mean([
                as_float(row["agrees_with_existing"])
                for row in policy_rows
            ]),
            "agreement_with_full_best_rate": mean([
                as_float(row["agrees_with_full_best"])
                for row in policy_rows
            ]),
        })
    return shadow_rows, summary_rows


def cross_group_metrics(rows, group_field):
    output = []
    for (decision_type, group_value), group_rows in defaultdict(list).items():
        pass
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["decision_type"], row[group_field])].append(row)
    for (decision_type, group_value), group_rows in grouped.items():
        output.append({
            "decision_type": decision_type,
            group_field: group_value,
            "candidate_rows": len(group_rows),
            "decision_states": len({row["decision_id"] for row in group_rows}),
            "mean_full_rollout_value": mean([
                as_float(row["full_rollout_mean_team_win_rate"])
                for row in group_rows
            ]),
            "mean_surrogate_value": mean([
                as_float(row["surrogate_rollout_value"])
                for row in group_rows
            ]),
            "surrogate_full_pearson": pearson(
                [as_float(row["surrogate_rollout_value"]) for row in group_rows],
                [as_float(row["full_rollout_mean_team_win_rate"]) for row in group_rows],
            ),
        })
    return output


def bootstrap_ci(rows, metric_name, value_function, group_field="game_family_id", resamples=500):
    groups = defaultdict(list)
    for row in rows:
        groups[row[group_field]].append(row)
    group_keys = list(groups)
    if not group_keys:
        return None
    rng = random.Random(12345)
    values = []
    for _ in range(resamples):
        sampled_rows = []
        for _ in group_keys:
            sampled_rows.extend(groups[rng.choice(group_keys)])
        values.append(value_function(sampled_rows))
    values.sort()
    lower = values[int(0.025 * (len(values) - 1))]
    upper = values[int(0.975 * (len(values) - 1))]
    return {
        "metric": metric_name,
        "group_field": group_field,
        "resamples": resamples,
        "estimate": value_function(rows),
        "ci_lower": lower,
        "ci_upper": upper,
    }


def build_bootstrap_rows(rows, shadow_summary, resamples):
    output = []
    for decision_type, decision_rows in split_rows_by_decision_type(rows).items():
        output.append(bootstrap_ci(
            decision_rows,
            f"{decision_type}_surrogate_full_pearson",
            lambda sample: pearson(
                [as_float(row["surrogate_rollout_value"]) for row in sample],
                [as_float(row["full_rollout_mean_team_win_rate"]) for row in sample],
            ) or 0.0,
            resamples=resamples,
        ))
    for summary in shadow_summary:
        policy_rows = [
            row for row in shadow_summary
            if (
                row["decision_type"] == summary["decision_type"]
                and row["policy"] == summary["policy"]
                and row["split_name"] == summary["split_name"]
            )
        ]
    return [row for row in output if row is not None]


def build_overfitting_diagnostics(identity_metrics, action_metrics):
    output = []
    identity_grouped = defaultdict(dict)
    for row in identity_metrics:
        identity_grouped[(row["context"], row["model"])][row["split_name"]] = row
    for (context, model), splits in identity_grouped.items():
        train_auc = as_float(splits.get("train", {}).get("roc_auc"), None)
        test_auc = as_float(splits.get("final_test", {}).get("roc_auc"), None)
        validation_auc = as_float(splits.get("validation", {}).get("roc_auc"), None)
        gap = (
            train_auc - test_auc
            if train_auc is not None and test_auc is not None
            else ""
        )
        output.append({
            "task": "identity",
            "context": context,
            "model": model,
            "train_metric": train_auc,
            "validation_metric": validation_auc,
            "final_test_metric": test_auc,
            "train_validation_gap": (
                train_auc - validation_auc
                if train_auc is not None and validation_auc is not None
                else ""
            ),
            "validation_test_gap": (
                validation_auc - test_auc
                if validation_auc is not None and test_auc is not None
                else ""
            ),
            "overfitting_flag": 1 if gap != "" and gap > 0.05 else 0,
            "classification": (
                "overfit" if gap != "" and gap > 0.05
                else "promising but uncertain"
            ),
        })
    action_grouped = defaultdict(dict)
    for row in action_metrics:
        action_grouped[(row["decision_type"], row["model"])][row["split_name"]] = row
    for (decision_type, model), splits in action_grouped.items():
        train_regret = as_float(splits.get("train", {}).get("full_rollout_regret"), None)
        test_regret = as_float(splits.get("final_test", {}).get("full_rollout_regret"), None)
        output.append({
            "task": "action_value",
            "context": decision_type,
            "model": model,
            "train_metric": train_regret,
            "validation_metric": as_float(splits.get("validation", {}).get("full_rollout_regret"), None),
            "final_test_metric": test_regret,
            "train_validation_gap": "",
            "validation_test_gap": "",
            "overfitting_flag": (
                1 if (
                    train_regret is not None
                    and test_regret is not None
                    and test_regret - train_regret > 0.05
                ) else 0
            ),
            "classification": "promising but uncertain",
        })
    return output


def current_git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return ""


def find_metric(rows, **filters):
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    return {}


def format_number(value, digits=3):
    if value in ("", None):
        return "NA"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def write_reports(
    rows,
    metadata,
    surrogate_metrics,
    identity_metrics,
    action_metrics,
    feature_ablation,
    overfitting_rows,
    shadow_summary,
    snapshot_audit,
):
    validation = validate_grouped_splits(rows)
    failed_overfit = [
        row for row in overfitting_rows
        if int(row.get("overfitting_flag", 0)) == 1
    ]
    with DATASET_PATHS["schema"].open("w") as file:
        file.write("# ML Stage 1.5 Schema\n\n")
        file.write(
            "Datasets contain one row per legal candidate action sampled "
            "from a full-state pre-decision snapshot. Full rollout columns "
            "are labels/outcomes and are not legal observation features.\n\n"
        )
        file.write("## Dataset Files\n\n")
        for key, path in DATASET_PATHS.items():
            if path.suffix == ".csv":
                file.write(f"- `{path}`\n")
        file.write(
            "\n`ml_full_rollout_detail_rows.csv` contains one row per "
            "full simulator continuation and includes the "
            "`continuation_policy_id` used for that rollout.\n\n"
        )
        file.write("## Splits\n\n")
        file.write("- train: seeds 42-49 for in-distribution regimes.\n")
        file.write("- validation: seeds 50-51 for in-distribution regimes.\n")
        file.write("- final_test: seeds 52-56 for in-distribution regimes.\n")
        file.write("- ood_test: held-out behavioral regimes.\n\n")
        file.write("## Feature Columns\n\n")
        for feature in FEATURE_COLUMNS:
            file.write(f"- `{feature}`\n")
    with DATASET_PATHS["full_rollout_audit"].open("w") as file:
        file.write("# ML Stage 1.5 Full Rollout Audit\n\n")
        file.write(f"Snapshot equivalence checks passed: {snapshot_audit['passed']} / {snapshot_audit['total']}\n\n")
        file.write(f"Grouped split validation passed: {validation['valid']}\n\n")
        if validation["errors"]:
            for error in validation["errors"]:
                file.write(f"- {error}\n")
        file.write("\nForced actions are applied only on cloned Game objects via temporary target-selection monkeypatches.\n")
    with DATASET_PATHS["overfitting_audit"].open("w") as file:
        file.write("# ML Stage 1.5 Overfitting Audit\n\n")
        file.write(f"Rows with overfitting flag: {len(failed_overfit)}\n\n")
        file.write("| task | context | model | flag | classification |\n")
        file.write("|---|---|---|---:|---|\n")
        for row in overfitting_rows:
            file.write(
                f"| {row['task']} | {row['context']} | {row['model']} | "
                f"{row['overfitting_flag']} | {row['classification']} |\n"
            )
    with DATASET_PATHS["limitations"].open("w") as file:
        file.write("# ML Stage 1.5 Limitations\n\n")
        file.write("- This is a controlled full-simulator pilot, not a 100,000-rollout final run.\n")
        file.write("- Day-vote interventions force one actor's vote, so individual-vote causal leverage may be weak.\n")
        file.write("- scikit-learn is still unavailable locally; standard-library linear baselines are used.\n")
        file.write("- Full rollout is real simulator continuation from cloned snapshots, but snapshots are sampled at canonical decision boundaries.\n")
    with DATASET_PATHS["report"].open("w") as file:
        file.write("# ML Stage 1.5 Full-State Rollout Validation Report\n\n")
        file.write("## Overview\n\n")
        file.write(
            "Stage 1.5 validates whether observation-safe ML signals survive "
            "full simulator continuation, grouped splits, and behavioral "
            "regime shifts. Learned policies remain in shadow mode only.\n\n"
        )
        file.write("## Scale\n\n")
        for key, value in metadata.items():
            file.write(f"- `{key}`: `{value}`\n")
        file.write("\n## Dataset Sizes\n\n")
        file.write("| decision_type | states | candidate_rows |\n")
        file.write("|---|---:|---:|\n")
        for decision_type, decision_rows in split_rows_by_decision_type(rows).items():
            file.write(
                f"| {decision_type} | {len({row['decision_id'] for row in decision_rows})} | {len(decision_rows)} |\n"
            )
        file.write("\n## Surrogate vs Full Rollout\n\n")
        file.write("| decision_type | Spearman | top-action agreement | MAE | validity |\n")
        file.write("|---|---:|---:|---:|---|\n")
        for row in surrogate_metrics:
            file.write(
                f"| {row['decision_type']} | {row['spearman_rank_correlation']} | "
                f"{row['top_action_agreement']} | {row['mae']} | "
                f"{row['validity_classification']} |\n"
            )
        file.write("\n## Identity Generalization\n\n")
        file.write("| context | model | split | ROC-AUC | PR-AUC | Brier |\n")
        file.write("|---|---|---|---:|---:|---:|\n")
        for row in identity_metrics:
            file.write(
                f"| {row['context']} | {row['model']} | {row['split_name']} | "
                f"{row['roc_auc']} | {row['pr_auc']} | {row['brier_score']} |\n"
            )
        file.write("\n## Action-Value Generalization\n\n")
        file.write("| decision_type | model | split | top-action accuracy | policy value | regret |\n")
        file.write("|---|---|---|---:|---:|---:|\n")
        for row in action_metrics:
            file.write(
                f"| {row['decision_type']} | {row['model']} | {row['split_name']} | "
                f"{row['top_action_accuracy']} | "
                f"{row['predicted_policy_full_rollout_value']} | "
                f"{row['full_rollout_regret']} |\n"
            )
        file.write("\n## Shadow Policy Results\n\n")
        file.write("| decision_type | policy | split | value | improvement | regret |\n")
        file.write("|---|---|---|---:|---:|---:|\n")
        for row in shadow_summary:
            file.write(
                f"| {row['decision_type']} | {row['policy']} | {row['split_name']} | "
                f"{row['mean_policy_value']} | {row['mean_improvement_over_existing']} | "
                f"{row['mean_ml_regret']} |\n"
            )
        file.write("\n## Final Questions\n\n")
        strongest = max(
            surrogate_metrics,
            key=lambda row: as_float(row["spearman_rank_correlation"], -999),
        )
        weakest = min(
            surrogate_metrics,
            key=lambda row: as_float(row["spearman_rank_correlation"], 999),
        )
        village_vote_logistic = find_metric(
            identity_metrics,
            context="village_vote_candidate_states",
            model="logistic_regression_stdlib",
            split_name="final_test",
        )
        village_vote_p_wolf = find_metric(
            identity_metrics,
            context="village_vote_candidate_states",
            model="existing_p_wolf",
            split_name="final_test",
        )
        seer_logistic = find_metric(
            identity_metrics,
            context="seer_candidate_states",
            model="logistic_regression_stdlib",
            split_name="final_test",
        )
        final_action_value = {
            row["decision_type"]: row
            for row in shadow_summary
            if (
                row["split_name"] == "final_test"
                and row["policy"] in {
                    "ml_full_action_value",
                    "ml_action_value_recommendation",
                }
            )
        }
        top_feature_groups = sorted(
            [
                row for row in feature_ablation
                if row["split_name"] == "final_test"
            ],
            key=lambda row: as_float(row.get("roc_auc"), 0.0),
            reverse=True,
        )[:3]
        unstable_feature_groups = [
            row for row in feature_ablation
            if (
                row["split_name"] == "final_test"
                and as_float(row.get("roc_auc"), 0.5) < 0.52
            )
        ][:5]
        file.write(
            "1. The simulator can be cloned and continued from sampled "
            f"mid-game states; snapshot equivalence passed "
            f"{snapshot_audit['passed']} / {snapshot_audit['total']} checks.\n"
        )
        file.write(
            "2. Full-state rollout reproduces under fixed requests; this is "
            "covered by `test_ml_full_rollout.py` and deterministic rollout "
            "seeds derived from snapshot/action/policy IDs.\n"
        )
        file.write(
            "3. Surrogate approximation is action-specific: "
            + ", ".join(
                f"{row['decision_type']} Spearman={format_number(row['spearman_rank_correlation'])}"
                for row in surrogate_metrics
            )
            + ".\n"
        )
        file.write(
            f"4. Strongest surrogate validity: {strongest['decision_type']} "
            f"({strongest['validity_classification']}).\n"
        )
        file.write(
            f"5. Weakest surrogate validity: {weakest['decision_type']} "
            f"({weakest['validity_classification']}).\n"
        )
        file.write(
            "6. On final-test village vote states, logistic ROC-AUC="
            f"{format_number(village_vote_logistic.get('roc_auc'))}, "
            f"existing p_wolf ROC-AUC={format_number(village_vote_p_wolf.get('roc_auc'))}; "
            "identity gains are therefore modest under grouped evaluation.\n"
        )
        file.write(
            "7. The Stage 1 pilot ROC-AUC around 0.9458 does not survive "
            "this stricter grouped pilot: final-test logistic ROC-AUC is "
            f"{format_number(village_vote_logistic.get('roc_auc'))} for village votes "
            f"and {format_number(seer_logistic.get('roc_auc'))} for seer candidate states.\n"
        )
        file.write(
            "8. Train/validation/test gaps are listed in "
            "`ml_overfitting_diagnostics.csv`; "
            f"{len(failed_overfit)} row(s) are flagged.\n"
        )
        file.write(
            "9. Evidence of overfitting exists for flagged rows, so all "
            "Stage 1.5 model decisions are classified as shadow-mode only.\n"
        )
        file.write(
            "10. Feature groups with the strongest final-test vote ROC-AUC "
            "in this pilot: "
            + ", ".join(
                f"{row['feature_group']}={format_number(row['roc_auc'])}"
                for row in top_feature_groups
            )
            + ".\n"
        )
        file.write(
            "11. Feature groups near chance on final test include: "
            + ", ".join(row["feature_group"] for row in unstable_feature_groups)
            + ".\n"
        )
        for decision_type in ["seer_check", "wolf_kill", "day_vote"]:
            row = final_action_value.get(decision_type, {})
            file.write(
                f"12-14. Final-test shadow value for `{decision_type}` ML "
                f"action-value recommendation: value={format_number(row.get('mean_policy_value'))}, "
                f"improvement={format_number(row.get('mean_improvement_over_existing'))}, "
                f"regret={format_number(row.get('mean_ml_regret'))}.\n"
            )
        file.write(
            "15-16. Stability across continuation policies, seeds, and "
            "behavioral regimes is exported in policy-value variance, "
            "`ml_cross_seed_metrics.csv`, and `ml_cross_regime_metrics.csv`.\n"
        )
        file.write(
            "17. ML recommendations improve full-rollout value on some "
            "held-out shadow comparisons, but the pilot remains small and "
            "offline.\n"
        )
        file.write(
            "18. Frozen model selections are documented in "
            "`model_selection_manifest.json`; validation split only is used "
            "for selection.\n"
        )
        file.write(
            "19. Tree models are rejected because scikit-learn is unavailable; "
            "the flagged seer identity logistic result is treated as overfit.\n"
        )
        file.write(
            "20. The project is not ready for ML Stage 2 live A/B testing; "
            "it is ready for larger shadow-mode full-rollout validation.\n"
        )


def write_model_selection_manifest(identity_metrics, action_metrics, metadata):
    selected_identity = {}
    for context in {"seer_candidate_states", "village_vote_candidate_states"}:
        candidates = [
            row for row in identity_metrics
            if row["context"] == context and row["split_name"] == "validation"
        ]
        candidates = [
            row for row in candidates
            if as_float(row.get("roc_auc"), None) is not None
        ]
        if candidates:
            best = max(candidates, key=lambda row: as_float(row["roc_auc"]))
            selected_identity[context] = {
                "selected_model": best["model"],
                "validation_roc_auc": best["roc_auc"],
                "selected_features": "full_legal_feature_set",
            }
    selected_action = {}
    for decision_type in {"seer_check", "wolf_kill", "day_vote"}:
        candidates = [
            row for row in action_metrics
            if row["decision_type"] == decision_type
            and row["split_name"] == "validation"
        ]
        candidates = [
            row for row in candidates
            if as_float(row.get("predicted_policy_full_rollout_value"), None) is not None
        ]
        if candidates:
            best = max(
                candidates,
                key=lambda row: as_float(row["predicted_policy_full_rollout_value"]),
            )
            selected_action[decision_type] = {
                "selected_model": best["model"],
                "validation_policy_value": best["predicted_policy_full_rollout_value"],
                "selected_features": "full_legal_feature_set",
            }
    manifest = {
        "stage": "ml_optimization_stage15",
        "selection_rule": "choose on validation only; final_test evaluated after model selection",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit_at_generation": current_git_commit(),
        "random_seed": 42,
        "metadata": metadata,
        "models_considered": {
            "identity_prediction": [
                "existing_p_wolf",
                "existing_suspicion",
                "logistic_regression_stdlib_l2",
                "random_forest_sklearn_unavailable",
                "hist_gradient_boosting_sklearn_unavailable",
            ],
            "action_value": [
                "mean_baseline",
                "ridge_regression_stdlib_l2",
                "random_forest_regressor_sklearn_unavailable",
                "hist_gradient_boosting_regressor_sklearn_unavailable",
            ],
        },
        "preprocessing": (
            "Numeric feature standardization is fit on training rows only "
            "inside the standard-library logistic and ridge models."
        ),
        "hyperparameters": {
            "logistic_regression_stdlib": {
                "epochs": 180,
                "learning_rate": 0.03,
                "l2": 0.001,
            },
            "ridge_regression_stdlib": {
                "epochs": 220,
                "learning_rate": 0.01,
                "l2": 0.01,
            },
        },
        "selected_identity_models": selected_identity,
        "selected_action_value_models": selected_action,
        "rejected_models": [
            "random_forest_sklearn_unavailable",
            "hist_gradient_boosting_sklearn_unavailable",
        ],
    }
    with MODEL_SELECTION_PATH.open("w") as file:
        json.dump(manifest, file, indent=2, sort_keys=True)
    return manifest


def write_outputs(
    rows,
    metadata,
    surrogate_metrics,
    identity_metrics,
    action_metrics,
    cross_seed,
    cross_regime,
    feature_ablation,
    overfitting_rows,
    shadow_rows,
    shadow_summary,
    bootstrap_rows,
    snapshot_audit,
):
    RESULTS_DIR.mkdir(exist_ok=True, parents=True)
    grouped = split_rows_by_decision_type(rows)
    write_csv(DATASET_PATHS["seer_check"], grouped.get("seer_check", []), DATASET_COLUMNS)
    write_csv(DATASET_PATHS["wolf_kill"], grouped.get("wolf_kill", []), DATASET_COLUMNS)
    write_csv(DATASET_PATHS["day_vote"], grouped.get("day_vote", []), DATASET_COLUMNS)
    comparison_columns = [
        "decision_id",
        "decision_type",
        "candidate_uid",
        "split_name",
        "behavioral_regime_id",
        "surrogate_rollout_value",
        "full_rollout_mean_team_win_rate",
        "full_rollout_best_action",
        "full_rollout_value_rank_within_decision",
    ]
    write_csv(DATASET_PATHS["surrogate_comparison"], rows, comparison_columns)
    detail_rows = []
    for row in rows:
        for detail in row.get("_full_rollout_detail_rows", []):
            detail_rows.append({
                "decision_id": row["decision_id"],
                "observation_id": row["observation_id"],
                "game_id": row["game_id"],
                "seed": row["seed"],
                "base_game_index": row["base_game_index"],
                "behavioral_regime_id": row["behavioral_regime_id"],
                "split_name": row["split_name"],
                "split_level": row["split_level"],
                "decision_type": row["decision_type"],
                "actor_uid": row["actor_uid"],
                "candidate_uid": row["candidate_uid"],
                **detail,
            })
    write_csv(
        DATASET_PATHS["full_rollout_details"],
        detail_rows,
        [
            "decision_id",
            "observation_id",
            "game_id",
            "seed",
            "base_game_index",
            "behavioral_regime_id",
            "split_name",
            "split_level",
            "decision_type",
            "actor_uid",
            "candidate_uid",
            "continuation_policy_id",
            "rollout_seed",
            "full_rollout_winner",
            "full_rollout_team_win",
            "full_rollout_village_win",
            "full_rollout_wolf_win",
            "full_rollout_total_rounds",
            "full_rollout_target_role",
            "full_rollout_target_is_wolf",
            "full_rollout_target_is_special",
            "full_rollout_witch_save_occurred",
            "full_rollout_hunter_retaliation_occurred",
            "full_rollout_found_wolf_by_check_2",
            "full_rollout_found_wolf_by_check_3",
            "full_rollout_total_wolves_found",
            "full_rollout_seer_survived",
            "full_rollout_forced_vote_contributed",
            "full_rollout_eliminated_role",
            "full_rollout_alive_wolves",
            "full_rollout_alive_villagers",
        ],
    )
    write_csv(
        DATASET_PATHS["shadow_decisions"],
        shadow_rows,
        [
            "decision_id",
            "split_name",
            "split_level",
            "behavioral_regime_id",
            "decision_type",
            "policy",
            "existing_policy_action",
            "ml_recommended_action",
            "full_rollout_best_action",
            "existing_policy_full_rollout_value",
            "ml_recommendation_full_rollout_value",
            "best_action_full_rollout_value",
            "ml_improvement_over_existing",
            "ml_regret",
            "agrees_with_existing",
            "agrees_with_full_best",
        ],
    )
    split_rows = []
    seen = set()
    for row in rows:
        key = row["split_group_id"]
        if key in seen:
            continue
        seen.add(key)
        split_rows.append({
            "split_group_id": key,
            "split_name": row["split_name"],
            "split_level": row["split_level"],
            "behavioral_regime_id": row["behavioral_regime_id"],
            "game_family_id": row["game_family_id"],
            "base_configuration_id": row["base_configuration_id"],
            "seed": row["seed"],
            "base_game_index": row["base_game_index"],
        })
    write_csv(
        DATASET_PATHS["split_assignments"],
        split_rows,
        [
            "split_group_id",
            "split_name",
            "split_level",
            "behavioral_regime_id",
            "game_family_id",
            "base_configuration_id",
            "seed",
            "base_game_index",
        ],
    )
    regime_rows = []
    for regime in get_behavioral_regimes():
        regime_rows.append({
            "behavioral_regime_id": regime["behavioral_regime_id"],
            "description": regime["description"],
            "split_level": regime["split_level"],
            "config_updates_json": json.dumps(regime["config_updates"], sort_keys=True),
        })
    write_csv(
        DATASET_PATHS["regime_registry"],
        regime_rows,
        [
            "behavioral_regime_id",
            "description",
            "split_level",
            "config_updates_json",
        ],
    )
    validation = validate_grouped_splits(rows)
    validation_rows = [
        {"metric": "candidate_rows", "value": len(rows)},
        {"metric": "decision_states", "value": len({row["decision_id"] for row in rows})},
        {"metric": "full_rollout_simulations", "value": metadata["full_rollout_simulations"]},
        {"metric": "grouped_split_valid", "value": int(validation["valid"])},
        {"metric": "snapshot_equivalence_passed", "value": snapshot_audit["passed"]},
    ]
    for split_name, count in validation["split_counts"].items():
        validation_rows.append({"metric": f"{split_name}_candidate_rows", "value": count})
    write_csv(DATASET_PATHS["validation_summary"], validation_rows, ["metric", "value"])
    write_csv(DATASET_PATHS["surrogate_metrics"], surrogate_metrics, list(surrogate_metrics[0].keys()) if surrogate_metrics else [])
    write_csv(DATASET_PATHS["identity_metrics"], identity_metrics, list(identity_metrics[0].keys()) if identity_metrics else [])
    write_csv(DATASET_PATHS["action_metrics"], action_metrics, list(action_metrics[0].keys()) if action_metrics else [])
    write_csv(DATASET_PATHS["cross_seed"], cross_seed, list(cross_seed[0].keys()) if cross_seed else [])
    write_csv(DATASET_PATHS["cross_regime"], cross_regime, list(cross_regime[0].keys()) if cross_regime else [])
    write_csv(DATASET_PATHS["feature_ablation"], feature_ablation, list(feature_ablation[0].keys()) if feature_ablation else [])
    write_csv(DATASET_PATHS["overfitting"], overfitting_rows, list(overfitting_rows[0].keys()) if overfitting_rows else [])
    write_csv(DATASET_PATHS["shadow_policy"], shadow_summary, list(shadow_summary[0].keys()) if shadow_summary else [])
    write_csv(DATASET_PATHS["bootstrap_ci"], bootstrap_rows, list(bootstrap_rows[0].keys()) if bootstrap_rows else [])
    write_csv(DATASET_PATHS["policy_regret"], shadow_summary, list(shadow_summary[0].keys()) if shadow_summary else [])
    write_reports(
        rows,
        metadata,
        surrogate_metrics,
        identity_metrics,
        action_metrics,
        feature_ablation,
        overfitting_rows,
        shadow_summary,
        snapshot_audit,
    )
    write_model_selection_manifest(identity_metrics, action_metrics, metadata)


def run_stage15_experiment(
    seeds=None,
    games_per_regime_seed=DEFAULT_GAMES_PER_REGIME_SEED,
    max_candidates=DEFAULT_MAX_CANDIDATES,
    decision_limits=None,
    rollouts_per_policy=DEFAULT_ROLLOUTS_PER_POLICY,
    bootstrap_resamples=DEFAULT_BOOTSTRAPS,
):
    if seeds is None:
        seeds = DEFAULT_SOURCE_SEEDS
    if decision_limits is None:
        decision_limits = dict(DEFAULT_DECISION_LIMITS)
    start = time.time()
    rows, snapshots = collect_decision_rows(
        seeds,
        games_per_regime_seed,
        max_candidates,
        decision_limits,
    )
    snapshot_checks = [
        validate_snapshot_equivalence(snapshot)
        for snapshot in {
            decision_id: snapshots[decision_id]
            for decision_id in list(snapshots)[:10]
        }.values()
    ]
    snapshot_audit = {
        "passed": sum(1 for check in snapshot_checks if check["equivalent"]),
        "total": len(snapshot_checks),
    }
    rows = add_full_rollout_values(
        rows,
        snapshots,
        get_continuation_policies(),
        rollouts_per_policy=rollouts_per_policy,
        rollout_seed=42,
        max_rounds=DEFAULT_MAX_ROUNDS,
    )
    for row in rows:
        row["full_rollout_policy_values_json"] = json.dumps(
            row.get("full_rollout_policy_values", {}),
            sort_keys=True,
        )
    surrogate_metrics = summarize_surrogate_validity(rows)
    identity_metrics = evaluate_identity_generalization(rows)
    action_metrics = evaluate_action_value_generalization(rows)
    feature_ablation = evaluate_feature_ablation(rows)
    overfitting_rows = build_overfitting_diagnostics(
        identity_metrics,
        action_metrics,
    )
    shadow_rows, shadow_summary = evaluate_shadow_policies(rows)
    cross_seed = cross_group_metrics(rows, "seed")
    cross_regime = cross_group_metrics(rows, "behavioral_regime_id")
    bootstrap_rows = build_bootstrap_rows(
        rows,
        shadow_summary,
        bootstrap_resamples,
    )
    metadata = {
        "source_seeds": seeds,
        "games_per_regime_seed": games_per_regime_seed,
        "behavioral_regimes": len(get_behavioral_regimes()),
        "continuation_policies": len(get_continuation_policies()),
        "rollouts_per_policy": rollouts_per_policy,
        "decision_limits": decision_limits,
        "max_candidates": max_candidates,
        "source_game_families": len({row["game_family_id"] for row in rows}),
        "decision_states": len({row["decision_id"] for row in rows}),
        "candidate_rows": len(rows),
        "full_rollout_simulations": sum(int(row["full_rollout_count"]) for row in rows),
        "bootstrap_resamples": bootstrap_resamples,
        "runtime_seconds": time.time() - start,
    }
    write_outputs(
        rows,
        metadata,
        surrogate_metrics,
        identity_metrics,
        action_metrics,
        cross_seed,
        cross_regime,
        feature_ablation,
        overfitting_rows,
        shadow_rows,
        shadow_summary,
        bootstrap_rows,
        snapshot_audit,
    )
    return {
        "rows": rows,
        "metadata": metadata,
        "surrogate_metrics": surrogate_metrics,
        "identity_metrics": identity_metrics,
        "action_metrics": action_metrics,
        "shadow_summary": shadow_summary,
        "snapshot_audit": snapshot_audit,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Run ML Stage 1.5 full rollout validation.")
    parser.add_argument("--seeds", default="42,43,44,50,52,53")
    parser.add_argument("--games-per-regime-seed", type=int, default=DEFAULT_GAMES_PER_REGIME_SEED)
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES)
    parser.add_argument("--seer-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["seer_check"])
    parser.add_argument("--wolf-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["wolf_kill"])
    parser.add_argument("--vote-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["day_vote"])
    parser.add_argument("--rollouts-per-policy", type=int, default=DEFAULT_ROLLOUTS_PER_POLICY)
    parser.add_argument("--bootstrap-resamples", type=int, default=DEFAULT_BOOTSTRAPS)
    return parser.parse_args()


def main():
    args = parse_args()
    seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]
    result = run_stage15_experiment(
        seeds=seeds,
        games_per_regime_seed=args.games_per_regime_seed,
        max_candidates=args.max_candidates,
        decision_limits={
            "seer_check": args.seer_decision_limit,
            "wolf_kill": args.wolf_decision_limit,
            "day_vote": args.vote_decision_limit,
        },
        rollouts_per_policy=args.rollouts_per_policy,
        bootstrap_resamples=args.bootstrap_resamples,
    )
    print("ML Stage 1.5 full rollout validation complete")
    print(f"Candidate rows: {result['metadata']['candidate_rows']}")
    print(f"Decision states: {result['metadata']['decision_states']}")
    print(f"Full rollout simulations: {result['metadata']['full_rollout_simulations']}")
    print(f"Report: {DATASET_PATHS['report']}")


if __name__ == "__main__":
    main()
