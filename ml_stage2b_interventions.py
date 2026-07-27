import copy
import random

from ml_full_state_snapshot import capture_full_game_snapshot
from ml_stage2b_selective_override import (
    evaluate_selective_override,
    load_selective_override_manifest,
)
from ml_wolf_kill_model_freeze import (
    FROZEN_MODEL_MANIFEST_PATH,
    load_json,
    validate_frozen_model_manifest,
)
from ml_wolf_kill_policy import (
    build_live_wolf_kill_candidate_rows,
    existing_rule_target,
    first_alive_wolf,
    rank_for_uid,
    select_policy_row,
)
from seat_order_neutral import get_actor_uid, stable_seed


STAGE2B_WOLF_KILL_POLICIES = [
    "existing_rule",
    "ml_first_kill_only",
    "ml_single_random_kill",
    "ml_first_two_kills",
    "continuous_frozen_ml",
    "existing_with_ml_shadow",
    "selective_ml_override",
    "high_confidence_shadow",
]

PRIMARY_STAGE2B_WOLF_KILL_POLICIES = [
    "existing_rule",
    "ml_first_kill_only",
    "ml_first_two_kills",
    "continuous_frozen_ml",
    "selective_ml_override",
]


def previous_stage2b_decision_events(game):
    return [
        event for event in game.event_log
        if event.get("event_type") == "wolf_kill_policy_decision"
    ]


def previous_ml_intervention_count(game):
    return sum(
        1 for event in previous_stage2b_decision_events(game)
        if event.get("content", {}).get("stage2b_executed_ml_intervention")
    )


def previous_ml_existing_disagreement_count(game):
    return sum(
        1 for event in previous_stage2b_decision_events(game)
        if not event.get("content", {}).get("ml_existing_agree", True)
    )


def stable_single_random_intervention_index(game, max_decisions=3):
    seed = stable_seed(
        "stage2b_single_random_intervention_index",
        getattr(game.state, "main_game_seed", None),
        getattr(game.state, "base_game_index", None),
        getattr(game.state, "label_condition", None),
        getattr(game, "ml_wolf_kill_policy_name", ""),
    )
    rng = random.Random(seed)
    return 1 + rng.randrange(max_decisions)


def stage2b_decision_id(game, policy_name, decision_index):
    explicit_game_id = getattr(game, "stage2b_game_id", None)
    if explicit_game_id:
        game_id = explicit_game_id
    else:
        game_id = (
            f"{getattr(game.state, 'label_condition', '')}_"
            f"{getattr(game.state, 'main_game_seed', '')}_"
            f"{getattr(game.state, 'base_game_index', '')}_"
            f"policy_{policy_name}"
        )
    return (
        f"{game_id}_round_{game.state.round_number}_"
        f"decision_{decision_index}"
    )


def maybe_capture_pre_decision_snapshot(game, policy_name, decision_id):
    if not getattr(game, "stage2b_capture_snapshots", False):
        return None
    allowed = getattr(game, "stage2b_snapshot_policies", None)
    if allowed is not None and policy_name not in set(allowed):
        return None
    snapshot = capture_full_game_snapshot(
        game,
        snapshot_id=decision_id,
        metadata={
            "stage": "ml_stage2b",
            "policy_name": policy_name,
            "round": game.state.round_number,
            "phase": game.state.phase,
        },
    )
    if not hasattr(game, "stage2b_snapshots"):
        game.stage2b_snapshots = {}
    game.stage2b_snapshots[decision_id] = snapshot
    return snapshot["canonical_hash"]


def determine_execution_policy(
    game,
    policy_name,
    decision_index,
    rows,
    existing_row,
    ml_row,
    selective_override_manifest,
):
    single_random_index = ""
    selective_detail = {
        "selective_override_qualified": False,
        "selective_override_checks": {},
        "ml_advantage_over_existing": 0.0,
        "selected_shift_category": (
            ml_row.get("distribution_shift_category", "unknown")
            if ml_row else "unknown"
        ),
    }
    actual_policy = "existing_rule"
    reason = "existing_rule_control"

    if policy_name == "continuous_frozen_ml":
        actual_policy = "frozen_ml"
        reason = "continuous_frozen_ml"
    elif policy_name == "ml_first_kill_only":
        if decision_index == 1:
            actual_policy = "frozen_ml"
            reason = "first_eligible_decision_uses_ml"
        else:
            reason = "after_first_decision_revert_to_existing_rule"
    elif policy_name == "ml_first_two_kills":
        if decision_index <= 2:
            actual_policy = "frozen_ml"
            reason = "first_two_eligible_decisions_use_ml"
        else:
            reason = "after_two_decisions_revert_to_existing_rule"
    elif policy_name == "ml_single_random_kill":
        single_random_index = stable_single_random_intervention_index(game)
        if decision_index == single_random_index:
            actual_policy = "frozen_ml"
            reason = "preselected_single_random_decision_uses_ml"
        else:
            reason = "not_preselected_single_random_decision"
    elif policy_name == "selective_ml_override":
        if selective_override_manifest is None:
            raise ValueError("selective_ml_override requires a manifest.")
        selective_detail = evaluate_selective_override(
            rows,
            existing_row,
            ml_row,
            selective_override_manifest,
        )
        if selective_detail["selective_override_qualified"]:
            actual_policy = "frozen_ml"
            reason = "selective_override_qualified"
        else:
            reason = "selective_override_not_qualified"
    elif policy_name == "high_confidence_shadow":
        if selective_override_manifest is not None:
            selective_detail = evaluate_selective_override(
                rows,
                existing_row,
                ml_row,
                selective_override_manifest,
            )
        reason = "high_confidence_shadow_existing_rule_executed"
    elif policy_name == "existing_with_ml_shadow":
        reason = "existing_rule_executed_with_ml_shadow_logging"
    elif policy_name == "existing_rule":
        reason = "existing_rule_control"
    else:
        raise ValueError(f"Unknown Stage 2B wolf-kill policy: {policy_name}")

    return {
        "actual_execution_policy": actual_policy,
        "selection_reason": reason,
        "stage2b_executed_ml_intervention": actual_policy == "frozen_ml",
        "stage2b_shadow_only": policy_name in {
            "existing_with_ml_shadow",
            "high_confidence_shadow",
        },
        "single_random_intervention_index": single_random_index,
        **selective_detail,
    }


def choose_stage2b_wolf_kill_target(
    game,
    policy_name="existing_rule",
    manifest_path=FROZEN_MODEL_MANIFEST_PATH,
    selective_override_manifest_path=None,
    existing_rule_strategy="threat_based",
    epsilon=0.10,
    manifest=None,
    selective_override_manifest=None,
):
    if policy_name not in STAGE2B_WOLF_KILL_POLICIES:
        raise ValueError(f"Unknown Stage 2B wolf-kill policy: {policy_name}")
    if manifest is None:
        if manifest_path is None:
            manifest_path = FROZEN_MODEL_MANIFEST_PATH
        manifest = load_json(manifest_path)
    validate_frozen_model_manifest(manifest)
    if (
        selective_override_manifest is None
        and selective_override_manifest_path is not None
    ):
        selective_override_manifest = load_selective_override_manifest(
            selective_override_manifest_path
        )

    actor = first_alive_wolf(game.state)
    decision_index = len(previous_stage2b_decision_events(game)) + 1
    decision_id = stage2b_decision_id(game, policy_name, decision_index)
    snapshot_hash = maybe_capture_pre_decision_snapshot(
        game,
        policy_name,
        decision_id,
    )
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
        game_id=decision_id,
    )
    existing_row, existing_detail = select_policy_row(
        game,
        rows,
        "existing_rule",
        existing_rule_strategy=existing_rule_strategy,
        existing_rule_target_uid=existing_target_uid,
    )
    ml_row, ml_detail = select_policy_row(
        game,
        rows,
        "frozen_ml",
        existing_rule_strategy=existing_rule_strategy,
        existing_rule_target_uid=existing_target_uid,
    )
    hybrid_row, hybrid_detail = select_policy_row(
        game,
        rows,
        "frozen_hybrid_50_50",
        existing_rule_strategy=existing_rule_strategy,
        existing_rule_target_uid=existing_target_uid,
    )
    epsilon_row, epsilon_detail = select_policy_row(
        game,
        rows,
        "frozen_ml_epsilon_010",
        existing_rule_strategy=existing_rule_strategy,
        existing_rule_target_uid=existing_target_uid,
        epsilon=epsilon,
    )
    execution_detail = determine_execution_policy(
        game,
        policy_name,
        decision_index,
        rows,
        existing_row,
        ml_row,
        selective_override_manifest,
    )
    selected_row = ml_row if (
        execution_detail["actual_execution_policy"] == "frozen_ml"
    ) else existing_row

    after_players = [player.to_dict() for player in game.state.players]
    if before_players != after_players:
        raise RuntimeError("Stage 2B wolf-kill scoring mutated game state.")
    if selected_row is None:
        return None, {
            "policy_name": policy_name,
            "stage2b_policy_name": policy_name,
            "decision_id": decision_id,
            "candidate_rows": [],
            "selection_reason": (
                execution_detail.get("selection_reason")
                or existing_detail.get("selection_reason")
                or ml_detail.get("selection_reason")
            ),
        }

    selected_uid = selected_row["candidate_uid"]
    selected_player = None
    for player in game.state.players:
        if get_actor_uid(player) == selected_uid:
            selected_player = player
            break
    if selected_player is None or not selected_player.alive:
        raise ValueError("Stage 2B wolf-kill policy selected illegal target.")
    if selected_player.is_wolf():
        raise ValueError("Stage 2B wolf-kill policy selected wolf teammate.")

    prior_ml_interventions = previous_ml_intervention_count(game)
    prior_disagreements = previous_ml_existing_disagreement_count(game)
    ml_existing_agree = bool(
        ml_row and existing_row
        and ml_row["candidate_uid"] == existing_row["candidate_uid"]
    )
    ml_advantage = execution_detail.get("ml_advantage_over_existing")
    if ml_advantage in ("", None) and ml_row and existing_row:
        ml_advantage = (
            ml_row["ml_predicted_wolf_value"]
            - existing_row["ml_predicted_wolf_value"]
        )
    event = {
        "policy_name": policy_name,
        "stage2b_policy_name": policy_name,
        "decision_id": decision_id,
        "decision_index": decision_index,
        "actor": actor.player_id if actor else "",
        "actor_uid": get_actor_uid(actor) if actor else "",
        "manifest_hash": manifest["manifest_hash"],
        "model_artifact_hash": manifest["model_artifact_hash"],
        "pre_decision_snapshot_id": decision_id if snapshot_hash else "",
        "pre_decision_snapshot_hash": snapshot_hash or "",
        "selected_target": selected_player.player_id,
        "selected_target_actor_uid": selected_uid,
        "selected_target_role_for_posthoc_analysis": selected_player.role,
        "selection_reason": execution_detail["selection_reason"],
        "actual_execution_policy": execution_detail[
            "actual_execution_policy"
        ],
        "stage2b_executed_ml_intervention": int(
            execution_detail["stage2b_executed_ml_intervention"]
        ),
        "stage2b_shadow_only": int(execution_detail["stage2b_shadow_only"]),
        "prior_ml_interventions": prior_ml_interventions,
        "cumulative_ml_interventions": (
            prior_ml_interventions
            + int(execution_detail["stage2b_executed_ml_intervention"])
        ),
        "prior_ml_existing_disagreements": prior_disagreements,
        "cumulative_ml_existing_disagreements": (
            prior_disagreements + int(not ml_existing_agree)
        ),
        "single_random_intervention_index": execution_detail[
            "single_random_intervention_index"
        ],
        "selective_override_qualified": int(
            execution_detail["selective_override_qualified"]
        ),
        "selective_override_manifest_hash": execution_detail.get(
            "selective_override_manifest_hash",
            "",
        ),
        "selective_override_checks": execution_detail.get(
            "selective_override_checks",
            {},
        ),
        "ml_advantage_over_existing": ml_advantage,
        "selected_shift_category": execution_detail.get(
            "selected_shift_category",
            "",
        ),
        "epsilon": epsilon,
        "epsilon_triggered": epsilon_detail.get("epsilon_triggered", False),
        "epsilon_seed": epsilon_detail.get("epsilon_seed", ""),
        "existing_rule_target": (
            existing_row["candidate_player_id"] if existing_row else None
        ),
        "existing_rule_target_actor_uid": (
            existing_row["candidate_uid"] if existing_row else None
        ),
        "frozen_ml_target": ml_row["candidate_player_id"] if ml_row else None,
        "frozen_ml_target_actor_uid": (
            ml_row["candidate_uid"] if ml_row else None
        ),
        "frozen_hybrid_50_50_target": (
            hybrid_row["candidate_player_id"] if hybrid_row else None
        ),
        "frozen_ml_epsilon_010_target": (
            epsilon_row["candidate_player_id"] if epsilon_row else None
        ),
        "ml_existing_agree": ml_existing_agree,
        "hybrid_existing_agree": bool(
            hybrid_row and existing_row
            and hybrid_row["candidate_uid"] == existing_row["candidate_uid"]
        ),
        "ml_hybrid_agree": bool(
            ml_row and hybrid_row
            and ml_row["candidate_uid"] == hybrid_row["candidate_uid"]
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
