import copy
import random

from ml_distribution_shift import calculate_distribution_shift
from ml_observation_builder import (
    build_actor_observation,
    build_candidate_feature_row,
)
from ml_wolf_kill_model_freeze import (
    FROZEN_MODEL_MANIFEST_PATH,
    load_json,
    predict_from_manifest,
    validate_frozen_model_manifest,
)
from roles import WOLF_TEAM
from seat_order_neutral import get_actor_uid, neutral_tie_break_value, stable_seed
from wolf_strategy import choose_wolf_kill_target, get_wolf_kill_candidates


PRIMARY_WOLF_KILL_POLICIES = [
    "existing_rule",
    "frozen_ml",
    "frozen_hybrid_50_50",
    "frozen_ml_epsilon_010",
]
EXPLORATORY_WOLF_KILL_POLICIES = [
    "ml_with_rule_fallback",
]
SUPPORTED_STAGE2A_WOLF_KILL_POLICIES = (
    PRIMARY_WOLF_KILL_POLICIES + EXPLORATORY_WOLF_KILL_POLICIES
)
DEFAULT_HYBRID_ML_WEIGHT = 0.50
DEFAULT_EPSILON = 0.10


def first_alive_wolf(game_state):
    wolves = [
        player for player in game_state.players
        if player.alive and player.is_wolf()
    ]
    if not wolves:
        return None
    return sorted(wolves, key=lambda player: str(get_actor_uid(player)))[0]


def legal_wolf_kill_candidates(game_state):
    return get_wolf_kill_candidates(game_state)


def normalize_scores(score_by_uid):
    if not score_by_uid:
        return {}
    values = list(score_by_uid.values())
    low = min(values)
    high = max(values)
    if high == low:
        return {uid: 0.5 for uid in score_by_uid}
    return {
        uid: (value - low) / (high - low)
        for uid, value in score_by_uid.items()
    }


def observation_safe_rule_proxy_score(feature_row):
    return (
        0.32 * float(feature_row.get("candidate_public_influence_proxy", 0.0))
        + 0.24 * float(feature_row.get("candidate_survival_proxy", 0.0))
        + 0.18 * (1.0 - float(feature_row.get("candidate_p_wolf", 0.0)))
        + 0.14 * (1.0 - float(feature_row.get("candidate_suspicion_score", 0.0)))
        + 0.08 * float(feature_row.get("candidate_received_accusations", 0.0))
        + 0.04 * float(feature_row.get("candidate_trust_from_actor", 0.5))
    )


def stable_candidate_sort_key(game_state, candidate, action_type):
    return neutral_tie_break_value(
        game_state,
        action_type,
        acting_player=None,
        candidate=candidate,
    )


def build_live_wolf_kill_candidate_rows(
    game,
    manifest,
    game_id="",
):
    actor = first_alive_wolf(game.state)
    if actor is None:
        return []
    candidates = legal_wolf_kill_candidates(game.state)
    if not candidates:
        return []
    alive_actor_uids = {
        get_actor_uid(player)
        for player in game.state.players
        if player.alive
    }
    observation = build_actor_observation(
        game.state,
        get_actor_uid(actor),
        "wolf_kill",
        game.state.round_number,
        game.state.phase,
        game_id=game_id,
        seed=getattr(game, "main_game_seed", None),
        base_game_index=getattr(game, "base_game_index", None),
        event_log=game.event_log,
        event_index=len(game.event_log),
        alive_actor_uids=alive_actor_uids,
        initial_p_wolf=getattr(game, "initial_p_wolf", 0.3),
    )
    rows = []
    for candidate in candidates:
        candidate_uid = get_actor_uid(candidate)
        feature_row = build_candidate_feature_row(
            observation,
            game.state,
            candidate_uid,
        )
        prediction, prediction_detail = predict_from_manifest(
            manifest,
            feature_row,
        )
        row = {
            "candidate_uid": candidate_uid,
            "candidate_player_id": candidate.player_id,
            "candidate_alive": candidate.alive,
            "candidate_is_wolf_team": candidate.team == WOLF_TEAM,
            "ml_predicted_wolf_value": prediction,
            "missing_feature_count": prediction_detail[
                "missing_feature_count"
            ],
            "observation_safe_rule_proxy_score": (
                observation_safe_rule_proxy_score(feature_row)
            ),
            "tie_break_value": stable_candidate_sort_key(
                game.state,
                candidate,
                "stage2a_wolf_kill_tie",
            ),
            "feature_row": feature_row,
            "candidate_role_for_posthoc_analysis": candidate.role,
            "candidate_seat_type": getattr(candidate, "seat_type", None),
            "candidate_side": getattr(candidate, "side", None),
        }
        rows.append(row)

    ml_values = {
        row["candidate_uid"]: row["ml_predicted_wolf_value"]
        for row in rows
    }
    normalized_ml = normalize_scores(ml_values)
    rule_values = {
        row["candidate_uid"]: row["observation_safe_rule_proxy_score"]
        for row in rows
    }
    normalized_rule = normalize_scores(rule_values)
    sorted_ml = sorted(
        rows,
        key=lambda row: (
            -row["ml_predicted_wolf_value"],
            row["tie_break_value"],
            str(row["candidate_uid"]),
        ),
    )
    top_margin = 0.0
    if len(sorted_ml) >= 2:
        top_margin = (
            sorted_ml[0]["ml_predicted_wolf_value"]
            - sorted_ml[1]["ml_predicted_wolf_value"]
        )
    for row in rows:
        row["normalized_ml_value"] = normalized_ml[row["candidate_uid"]]
        row["normalized_existing_rule_score"] = normalized_rule[
            row["candidate_uid"]
        ]
        row["hybrid_score"] = (
            DEFAULT_HYBRID_ML_WEIGHT * row["normalized_ml_value"]
            + (1.0 - DEFAULT_HYBRID_ML_WEIGHT)
            * row["normalized_existing_rule_score"]
        )
        row.update(calculate_distribution_shift(
            manifest,
            row["feature_row"],
            prediction=row["ml_predicted_wolf_value"],
            margin=top_margin,
        ))
    return rows


def select_row_by_score(rows, score_field, game_state, action_type):
    if not rows:
        return None
    return sorted(
        rows,
        key=lambda row: (
            -float(row[score_field]),
            row["tie_break_value"],
            str(row["candidate_uid"]),
        ),
    )[0]


def existing_rule_target(game, existing_rule_strategy="threat_based"):
    return choose_wolf_kill_target(
        game.state,
        strategy=existing_rule_strategy,
        noise_level=getattr(game, "wolf_kill_noise_level", 0.0),
    )


def select_policy_row(
    game,
    rows,
    policy_name,
    existing_rule_strategy="threat_based",
    epsilon=DEFAULT_EPSILON,
    existing_rule_target_uid=None,
):
    if policy_name not in SUPPORTED_STAGE2A_WOLF_KILL_POLICIES:
        raise ValueError(f"Unknown Stage 2A wolf-kill policy: {policy_name}")
    if not rows:
        return None, {
            "selection_reason": "no_legal_candidates",
            "epsilon_triggered": False,
        }

    if policy_name == "existing_rule":
        target_uid = existing_rule_target_uid
        if target_uid is None:
            target = existing_rule_target(game, existing_rule_strategy)
            target_uid = get_actor_uid(target) if target is not None else None
        if target_uid is None:
            return None, {
                "selection_reason": "existing_rule_no_target",
                "epsilon_triggered": False,
            }
        for row in rows:
            if row["candidate_uid"] == target_uid:
                return row, {
                    "selection_reason": "existing_rule",
                    "epsilon_triggered": False,
                }
        return None, {
            "selection_reason": "existing_rule_illegal_target",
            "epsilon_triggered": False,
        }

    if policy_name == "frozen_ml":
        return select_row_by_score(
            rows,
            "ml_predicted_wolf_value",
            game.state,
            "stage2a_frozen_ml_tie",
        ), {
            "selection_reason": "highest_frozen_ml_value",
            "epsilon_triggered": False,
        }

    if policy_name == "frozen_hybrid_50_50":
        return select_row_by_score(
            rows,
            "hybrid_score",
            game.state,
            "stage2a_hybrid_tie",
        ), {
            "selection_reason": "highest_hybrid_score_50_50",
            "epsilon_triggered": False,
        }

    if policy_name == "frozen_ml_epsilon_010":
        sorted_rows = sorted(
            rows,
            key=lambda row: (
                -row["ml_predicted_wolf_value"],
                row["tie_break_value"],
                str(row["candidate_uid"]),
            ),
        )
        best = sorted_rows[0]
        seed = stable_seed(
            "stage2a_epsilon_policy",
            getattr(game.state, "main_game_seed", None),
            getattr(game.state, "base_game_index", None),
            getattr(game.state, "label_condition", None),
            game.state.round_number,
            game.state.phase,
            len(game.event_log),
        )
        rng = random.Random(seed)
        if len(sorted_rows) > 1 and rng.random() < epsilon:
            alternatives = sorted_rows[1:]
            selected = alternatives[rng.randrange(len(alternatives))]
            return selected, {
                "selection_reason": "epsilon_exploration",
                "epsilon_triggered": True,
                "epsilon_seed": seed,
            }
        return best, {
            "selection_reason": "epsilon_policy_greedy",
            "epsilon_triggered": False,
            "epsilon_seed": seed,
        }

    fallback_row = select_row_by_score(
        rows,
        "ml_predicted_wolf_value",
        game.state,
        "stage2a_fallback_tie",
    )
    if (
        fallback_row["distribution_shift_category"] == "strong_shift"
        or fallback_row["candidate_ranking_margin"] < 0.01
    ):
        return select_policy_row(
            game,
            rows,
            "existing_rule",
            existing_rule_strategy=existing_rule_strategy,
        )
    return fallback_row, {
        "selection_reason": "ml_with_rule_fallback_used_ml",
        "epsilon_triggered": False,
    }


def rank_for_uid(rows, uid, score_field):
    ordered = sorted(
        rows,
        key=lambda row: (
            -float(row[score_field]),
            row["tie_break_value"],
            str(row["candidate_uid"]),
        ),
    )
    for index, row in enumerate(ordered, start=1):
        if row["candidate_uid"] == uid:
            return index
    return ""


def choose_stage2a_wolf_kill_target(
    game,
    policy_name="existing_rule",
    manifest_path=FROZEN_MODEL_MANIFEST_PATH,
    existing_rule_strategy="threat_based",
    epsilon=DEFAULT_EPSILON,
    manifest=None,
):
    if manifest is None:
        if manifest_path is None:
            manifest_path = FROZEN_MODEL_MANIFEST_PATH
        manifest = load_json(manifest_path)
    validate_frozen_model_manifest(manifest)
    before_players = copy.deepcopy([
        player.to_dict() for player in game.state.players
    ])
    existing_target = existing_rule_target(game, existing_rule_strategy)
    existing_target_uid = (
        get_actor_uid(existing_target) if existing_target is not None else None
    )
    rows = build_live_wolf_kill_candidate_rows(
        game,
        manifest,
        game_id=(
            f"{getattr(game.state, 'label_condition', '')}_"
            f"{getattr(game.state, 'main_game_seed', '')}_"
            f"{getattr(game.state, 'base_game_index', '')}"
        ),
    )
    selected_row, selection_detail = select_policy_row(
        game,
        rows,
        policy_name,
        existing_rule_strategy=existing_rule_strategy,
        epsilon=epsilon,
        existing_rule_target_uid=existing_target_uid,
    )
    after_players = [player.to_dict() for player in game.state.players]
    if before_players != after_players:
        raise RuntimeError("ML wolf-kill scoring mutated game state.")
    if selected_row is None:
        return None, {
            "policy_name": policy_name,
            "candidate_rows": [],
            **selection_detail,
        }
    selected_uid = selected_row["candidate_uid"]
    selected_player = None
    for player in game.state.players:
        if get_actor_uid(player) == selected_uid:
            selected_player = player
            break
    if selected_player is None or not selected_player.alive:
        raise ValueError("Stage 2A wolf-kill policy selected illegal target.")
    if selected_player.is_wolf():
        raise ValueError("Stage 2A wolf-kill policy selected wolf teammate.")

    existing_row, _ = select_policy_row(
        game,
        rows,
        "existing_rule",
        existing_rule_strategy=existing_rule_strategy,
        existing_rule_target_uid=existing_target_uid,
    )
    ml_row, _ = select_policy_row(
        game,
        rows,
        "frozen_ml",
        existing_rule_strategy=existing_rule_strategy,
    )
    hybrid_row, _ = select_policy_row(
        game,
        rows,
        "frozen_hybrid_50_50",
        existing_rule_strategy=existing_rule_strategy,
    )
    epsilon_row, epsilon_detail = select_policy_row(
        game,
        rows,
        "frozen_ml_epsilon_010",
        existing_rule_strategy=existing_rule_strategy,
        epsilon=epsilon,
    )
    event = {
        "policy_name": policy_name,
        "manifest_hash": manifest["manifest_hash"],
        "model_artifact_hash": manifest["model_artifact_hash"],
        "selected_target": selected_player.player_id,
        "selected_target_actor_uid": selected_uid,
        "selected_target_role_for_posthoc_analysis": selected_player.role,
        "selection_reason": selection_detail.get("selection_reason"),
        "epsilon": epsilon,
        "epsilon_triggered": selection_detail.get("epsilon_triggered", False),
        "epsilon_seed": selection_detail.get(
            "epsilon_seed",
            epsilon_detail.get("epsilon_seed"),
        ),
        "existing_rule_target": (
            existing_row["candidate_player_id"] if existing_row else None
        ),
        "frozen_ml_target": ml_row["candidate_player_id"] if ml_row else None,
        "frozen_hybrid_50_50_target": (
            hybrid_row["candidate_player_id"] if hybrid_row else None
        ),
        "frozen_ml_epsilon_010_target": (
            epsilon_row["candidate_player_id"] if epsilon_row else None
        ),
        "ml_existing_agree": (
            bool(ml_row and existing_row and ml_row["candidate_uid"] == existing_row["candidate_uid"])
        ),
        "hybrid_existing_agree": (
            bool(hybrid_row and existing_row and hybrid_row["candidate_uid"] == existing_row["candidate_uid"])
        ),
        "ml_hybrid_agree": (
            bool(ml_row and hybrid_row and ml_row["candidate_uid"] == hybrid_row["candidate_uid"])
        ),
        "selected_rank_under_existing_rule_proxy": rank_for_uid(
            rows,
            selected_uid,
            "observation_safe_rule_proxy_score",
        ),
        "selected_rank_under_ml": rank_for_uid(
            rows,
            selected_uid,
            "ml_predicted_wolf_value",
        ),
        "top_two_predicted_value_margin": (
            selected_row["candidate_ranking_margin"]
        ),
        "number_of_legal_candidates": len(rows),
        "distribution_shift_category": (
            selected_row["distribution_shift_category"]
        ),
        "candidate_rows": [
            {
                key: value for key, value in row.items()
                if key != "feature_row"
            }
            for row in rows
        ],
    }
    return selected_player, event
