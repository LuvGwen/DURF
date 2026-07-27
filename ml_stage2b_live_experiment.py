import csv
import random
from collections import defaultdict
from pathlib import Path

from config import DEFAULT_MAX_ROUNDS
from game import Game, create_default_players
from ml_wolf_kill_live_experiment import (
    get_stage2a_behavioral_regimes,
    summarize_game,
)
from ml_wolf_kill_model_freeze import (
    FROZEN_MODEL_MANIFEST_PATH,
    load_json,
    validate_frozen_model_manifest,
)
from roles import HUNTER, SEER, WITCH
from seat_order_neutral import stable_seed
from ml_stage2b_interventions import STAGE2B_WOLF_KILL_POLICIES


STAGE2B_RESULTS_DIR = Path("results") / "ml_optimization_stage2b"
SPECIAL_ROLES = {SEER, WITCH, HUNTER}


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(exist_ok=True, parents=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row}) if rows else []
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
    numeric = [float(value) for value in values]
    return sum(numeric) / len(numeric) if numeric else 0.0


def build_stage2b_matched_set_id(seed, base_game_index, regime):
    return (
        f"stage2b_seed_{seed}_base_{base_game_index}_"
        f"regime_{regime['behavioral_regime_id']}"
    )


def build_game_for_stage2b_policy(
    seed,
    split,
    base_game_index,
    regime,
    policy_name,
    manifest,
    manifest_path=FROZEN_MODEL_MANIFEST_PATH,
    selective_override_manifest_path=None,
    capture_snapshots=False,
):
    random.seed(stable_seed(
        "stage2b_live_initial_state",
        seed,
        base_game_index,
        regime["behavioral_regime_id"],
    ))
    config = dict(regime["config"])
    players = create_default_players(
        role_setup=config.get("role_setup"),
        initial_p_wolf=config.get("initial_p_wolf"),
    )
    matched_set_id = build_stage2b_matched_set_id(
        seed,
        base_game_index,
        regime,
    )
    game_id = f"{matched_set_id}_policy_{policy_name}"
    game = Game(
        players,
        **config,
        base_game_index=base_game_index,
        label_condition=regime["behavioral_regime_id"],
        main_game_seed=stable_seed(
            "stage2b_live_game",
            seed,
            base_game_index,
            regime["behavioral_regime_id"],
        ),
        neutral_seed=stable_seed(
            "stage2b_live_neutral",
            seed,
            base_game_index,
            regime["behavioral_regime_id"],
        ),
        enable_ml_wolf_kill_policy=True,
        ml_wolf_kill_policy_name=policy_name,
        ml_wolf_kill_model_manifest_path=str(manifest_path),
        ml_wolf_kill_manifest_hash=manifest["manifest_hash"],
        ml_wolf_kill_epsilon=0.10,
        enable_ml_stage2b_policy=True,
        ml_stage2b_selective_override_manifest_path=(
            str(selective_override_manifest_path)
            if selective_override_manifest_path is not None
            else None
        ),
    )
    game.stage2b_split = split
    game.stage2b_game_id = game_id
    game.stage2b_capture_snapshots = capture_snapshots
    game.stage2b_snapshot_policies = {"existing_with_ml_shadow"}
    game.stage2b_snapshots = {}
    return game, matched_set_id


def summarize_stage2b_game(
    game,
    result,
    seed,
    split,
    base_game_index,
    regime,
    policy_name,
    matched_set_id,
):
    row = summarize_game(
        game,
        result,
        seed,
        base_game_index,
        regime,
        policy_name,
        matched_set_id,
    )
    decision_events = [
        event for event in game.event_log
        if event.get("event_type") == "wolf_kill_policy_decision"
    ]
    contents = [event.get("content", {}) for event in decision_events]
    interventions = [
        content for content in contents
        if int(content.get("stage2b_executed_ml_intervention", 0)) == 1
    ]
    shift_categories = [
        content.get("distribution_shift_category", "unknown")
        for content in contents
    ]
    row.update({
        "split": split,
        "stage2b_policy_name": policy_name,
        "game_id": f"{matched_set_id}_policy_{policy_name}",
        "total_ml_interventions": len(interventions),
        "total_ml_existing_disagreements": sum(
            1 for content in contents
            if not content.get("ml_existing_agree", True)
        ),
        "total_selective_qualified_decisions": sum(
            int(content.get("selective_override_qualified", 0))
            for content in contents
        ),
        "total_shadow_only_decisions": sum(
            int(content.get("stage2b_shadow_only", 0))
            for content in contents
        ),
        "in_distribution_decisions": shift_categories.count("in_distribution"),
        "mild_shift_decisions": shift_categories.count("mild_shift"),
        "strong_shift_decisions": shift_categories.count("strong_shift"),
        "strong_shift_decision_rate": (
            shift_categories.count("strong_shift") / len(shift_categories)
            if shift_categories else 0.0
        ),
        "avg_top_two_margin": mean(
            content.get("top_two_predicted_value_margin", 0.0)
            for content in contents
        ) if contents else 0.0,
        "avg_ml_advantage_over_existing": mean(
            content.get("ml_advantage_over_existing", 0.0)
            for content in contents
        ) if contents else 0.0,
    })
    return row


def rank_maps(candidate_rows):
    maps = {}
    score_fields = {
        "ml": "ml_predicted_wolf_value",
        "existing": "observation_safe_rule_proxy_score",
        "hybrid": "hybrid_score",
    }
    for label, field in score_fields.items():
        ordered = sorted(
            candidate_rows,
            key=lambda row: (
                -float(row.get(field, 0.0)),
                float(row.get("tie_break_value", 0.0)),
                str(row.get("candidate_uid")),
            ),
        )
        maps[label] = {
            str(row.get("candidate_uid")): index
            for index, row in enumerate(ordered, start=1)
        }
    return maps


def role_for_target(content, target_id):
    for row in content.get("candidate_rows", []):
        if str(row.get("candidate_player_id")) == str(target_id):
            return row.get("candidate_role_for_posthoc_analysis", "")
    return ""


def extract_stage2b_rows(game, game_row):
    decision_rows = []
    prediction_rows = []
    trajectory_rows = []
    downstream_rows = []
    decision_events = [
        event for event in game.event_log
        if event.get("event_type") == "wolf_kill_policy_decision"
    ]
    for fallback_index, event in enumerate(decision_events, start=1):
        content = event["content"]
        decision_index = int(content.get("decision_index", fallback_index))
        decision_id = content.get("decision_id") or (
            f"{game_row['game_id']}_round_{event['round']}_"
            f"decision_{decision_index}"
        )
        selected_target = content.get("selected_target")
        saved = any(
            later["event_type"] == "night_kill_prevented"
            and later["round"] == event["round"]
            and later.get("content", {}).get("target") == selected_target
            for later in game.event_log
        )
        killed = any(
            later["event_type"] == "night_kill"
            and later["round"] == event["round"]
            and later.get("content", {}).get("target") == selected_target
            for later in game.event_log
        )
        hunter_retaliation = any(
            later["event_type"] == "hunter_shot"
            and later["round"] == event["round"]
            for later in game.event_log
        )
        base = {
            **game_row,
            "decision_id": decision_id,
            "decision_type": "wolf_kill",
            "decision_index": decision_index,
            "round": event["round"],
            "phase": event["phase"],
            "actor": content.get("actor"),
            "actor_uid": content.get("actor_uid"),
            "selected_target": selected_target,
            "selected_target_actor_uid": content.get(
                "selected_target_actor_uid"
            ),
            "selected_target_role": content.get(
                "selected_target_role_for_posthoc_analysis"
            ),
            "selection_reason": content.get("selection_reason"),
            "actual_execution_policy": content.get(
                "actual_execution_policy",
            ),
            "stage2b_executed_ml_intervention": int(
                content.get("stage2b_executed_ml_intervention", 0)
            ),
            "stage2b_shadow_only": int(content.get("stage2b_shadow_only", 0)),
            "prior_ml_interventions": int(content.get(
                "prior_ml_interventions",
                0,
            )),
            "cumulative_ml_interventions": int(content.get(
                "cumulative_ml_interventions",
                0,
            )),
            "prior_ml_existing_disagreements": int(content.get(
                "prior_ml_existing_disagreements",
                0,
            )),
            "cumulative_ml_existing_disagreements": int(content.get(
                "cumulative_ml_existing_disagreements",
                0,
            )),
            "pre_decision_snapshot_id": content.get(
                "pre_decision_snapshot_id",
                "",
            ),
            "pre_decision_snapshot_hash": content.get(
                "pre_decision_snapshot_hash",
                "",
            ),
            "single_random_intervention_index": content.get(
                "single_random_intervention_index",
                "",
            ),
            "selective_override_qualified": int(content.get(
                "selective_override_qualified",
                0,
            )),
            "selective_override_manifest_hash": content.get(
                "selective_override_manifest_hash",
                "",
            ),
            "ml_advantage_over_existing": content.get(
                "ml_advantage_over_existing",
                0.0,
            ),
            "existing_rule_target": content.get("existing_rule_target"),
            "existing_rule_target_actor_uid": content.get(
                "existing_rule_target_actor_uid",
            ),
            "frozen_ml_target": content.get("frozen_ml_target"),
            "frozen_ml_target_actor_uid": content.get(
                "frozen_ml_target_actor_uid",
            ),
            "frozen_hybrid_50_50_target": content.get(
                "frozen_hybrid_50_50_target"
            ),
            "frozen_ml_epsilon_010_target": content.get(
                "frozen_ml_epsilon_010_target"
            ),
            "ml_existing_agree": int(content.get("ml_existing_agree", 0)),
            "hybrid_existing_agree": int(
                content.get("hybrid_existing_agree", 0)
            ),
            "ml_hybrid_agree": int(content.get("ml_hybrid_agree", 0)),
            "selected_target_rank_under_existing_rule": content.get(
                "selected_rank_under_existing_rule_proxy"
            ),
            "selected_target_rank_under_ml": content.get(
                "selected_rank_under_ml"
            ),
            "top_two_predicted_value_margin": content.get(
                "top_two_predicted_value_margin"
            ),
            "number_of_legal_candidates": content.get(
                "number_of_legal_candidates"
            ),
            "distribution_shift_category": content.get(
                "distribution_shift_category"
            ),
            "selected_target_killed": int(killed),
            "witch_saved_target": int(saved),
            "hunter_retaliation_occurred": int(hunter_retaliation),
        }
        decision_rows.append(base)
        trajectory_rows.append({
            **base,
            "alive_count": game_row.get("num_alive_players", ""),
            "shift_metric_scope": "selected_target",
        })
        downstream_rows.append({
            **base,
            "selected_target_is_special": int(
                base["selected_target_role"] in SPECIAL_ROLES
            ),
            "selected_target_is_seer": int(base["selected_target_role"] == SEER),
            "selected_target_is_witch": int(base["selected_target_role"] == WITCH),
            "selected_target_is_hunter": int(base["selected_target_role"] == HUNTER),
            "existing_rule_target_role": role_for_target(
                content,
                content.get("existing_rule_target"),
            ),
            "frozen_ml_target_role": role_for_target(
                content,
                content.get("frozen_ml_target"),
            ),
            "vote_control_proxy": game_row.get("vote_control_proxy", 0),
            "first_wolf_death_round": game_row.get("first_wolf_death_round", ""),
        })
        maps = rank_maps(content.get("candidate_rows", []))
        for candidate in content.get("candidate_rows", []):
            candidate_uid = str(candidate.get("candidate_uid"))
            candidate_row = {
                **base,
                "candidate_uid": candidate.get("candidate_uid"),
                "candidate_player_id": candidate.get("candidate_player_id"),
                "candidate_role_for_posthoc_analysis": candidate.get(
                    "candidate_role_for_posthoc_analysis"
                ),
                "candidate_seat_type": candidate.get("candidate_seat_type"),
                "candidate_side": candidate.get("candidate_side"),
                "action_legal": 1,
                "action_selected_by_existing_policy": int(
                    str(candidate.get("candidate_uid"))
                    == str(content.get("existing_rule_target_actor_uid"))
                ),
                "action_selected_by_ml_policy": int(
                    str(candidate.get("candidate_uid"))
                    == str(content.get("frozen_ml_target_actor_uid"))
                ),
                "action_selected_by_stage2b_policy": int(
                    str(candidate.get("candidate_uid"))
                    == str(content.get("selected_target_actor_uid"))
                ),
                "ml_rank": maps.get("ml", {}).get(candidate_uid, ""),
                "existing_rule_rank": maps.get("existing", {}).get(
                    candidate_uid,
                    "",
                ),
                "hybrid_rank": maps.get("hybrid", {}).get(candidate_uid, ""),
                "ml_predicted_wolf_value": candidate.get(
                    "ml_predicted_wolf_value"
                ),
                "normalized_ml_value": candidate.get("normalized_ml_value"),
                "observation_safe_rule_proxy_score": candidate.get(
                    "observation_safe_rule_proxy_score"
                ),
                "normalized_existing_rule_score": candidate.get(
                    "normalized_existing_rule_score"
                ),
                "hybrid_score": candidate.get("hybrid_score"),
                "candidate_ranking_margin": candidate.get(
                    "candidate_ranking_margin"
                ),
                "standardized_feature_distance": candidate.get(
                    "standardized_feature_distance"
                ),
                "maximum_absolute_z_score": candidate.get(
                    "maximum_absolute_z_score"
                ),
                "fraction_features_outside_training_minmax": candidate.get(
                    "fraction_features_outside_training_minmax"
                ),
                "missing_feature_count": candidate.get(
                    "missing_feature_count"
                ),
                "feature_vector_novelty_score": candidate.get(
                    "feature_vector_novelty_score"
                ),
                "prediction_extremity": candidate.get(
                    "prediction_extremity"
                ),
                "candidate_distribution_shift_category": candidate.get(
                    "distribution_shift_category"
                ),
            }
            prediction_rows.append(candidate_row)
    return decision_rows, prediction_rows, trajectory_rows, downstream_rows


def write_stage2b_raw_outputs(output_dir, output):
    write_csv(
        output_dir / "stage2b_live_game_level_raw.csv",
        output["game_rows"],
    )
    write_csv(
        output_dir / "stage2b_live_decision_raw.csv",
        output["decision_rows"],
    )
    write_csv(
        output_dir / "stage2b_policy_prediction_raw.csv",
        output["prediction_rows"],
    )
    write_csv(
        output_dir / "stage2b_distribution_shift_trajectory_raw.csv",
        output["trajectory_rows"],
    )
    write_csv(
        output_dir / "stage2b_downstream_mechanism_raw.csv",
        output["downstream_rows"],
    )


def run_stage2b_live_experiment(
    output_dir=STAGE2B_RESULTS_DIR,
    manifest_path=FROZEN_MODEL_MANIFEST_PATH,
    seeds=None,
    split="final_test",
    base_configs_per_seed=1,
    policies=None,
    regimes=None,
    max_rounds=DEFAULT_MAX_ROUNDS,
    selective_override_manifest_path=None,
    capture_snapshots=False,
    write_outputs=True,
):
    output_dir = Path(output_dir)
    if seeds is None:
        seeds = list(range(220, 240))
    if policies is None:
        policies = list(STAGE2B_WOLF_KILL_POLICIES)
    if regimes is None:
        regimes = get_stage2a_behavioral_regimes()

    manifest = load_json(manifest_path)
    validate_frozen_model_manifest(manifest)
    game_rows = []
    decision_rows = []
    prediction_rows = []
    trajectory_rows = []
    downstream_rows = []
    snapshots_by_decision_id = {}

    for seed in seeds:
        for base_game_index in range(1, base_configs_per_seed + 1):
            for regime in regimes:
                for policy_name in policies:
                    game, matched_set_id = build_game_for_stage2b_policy(
                        seed,
                        split,
                        base_game_index,
                        regime,
                        policy_name,
                        manifest,
                        manifest_path=manifest_path,
                        selective_override_manifest_path=(
                            selective_override_manifest_path
                        ),
                        capture_snapshots=capture_snapshots,
                    )
                    result = game.run_game(max_rounds=max_rounds)
                    game_row = summarize_stage2b_game(
                        game,
                        result,
                        seed,
                        split,
                        base_game_index,
                        regime,
                        policy_name,
                        matched_set_id,
                    )
                    game_rows.append(game_row)
                    rows = extract_stage2b_rows(game, game_row)
                    decision_rows.extend(rows[0])
                    prediction_rows.extend(rows[1])
                    trajectory_rows.extend(rows[2])
                    downstream_rows.extend(rows[3])
                    snapshots_by_decision_id.update(game.stage2b_snapshots)

    output = {
        "game_rows": game_rows,
        "decision_rows": decision_rows,
        "prediction_rows": prediction_rows,
        "trajectory_rows": trajectory_rows,
        "downstream_rows": downstream_rows,
        "snapshots_by_decision_id": snapshots_by_decision_id,
        "seeds": list(seeds),
        "split": split,
        "policies": list(policies),
        "regimes": regimes,
        "matched_sets": len({
            row["matched_set_id"] for row in game_rows
        }),
    }
    if write_outputs:
        write_stage2b_raw_outputs(output_dir, output)
    return output


def combine_live_outputs(outputs):
    combined = {
        "game_rows": [],
        "decision_rows": [],
        "prediction_rows": [],
        "trajectory_rows": [],
        "downstream_rows": [],
        "snapshots_by_decision_id": {},
        "seeds": [],
        "policies": [],
        "regimes": [],
        "matched_sets": 0,
    }
    regime_by_id = {}
    policies = set()
    seeds = set()
    matched_sets = set()
    for output in outputs:
        for key in [
            "game_rows",
            "decision_rows",
            "prediction_rows",
            "trajectory_rows",
            "downstream_rows",
        ]:
            combined[key].extend(output.get(key, []))
        combined["snapshots_by_decision_id"].update(
            output.get("snapshots_by_decision_id", {})
        )
        seeds.update(output.get("seeds", []))
        policies.update(output.get("policies", []))
        for regime in output.get("regimes", []):
            regime_by_id[regime["behavioral_regime_id"]] = regime
        matched_sets.update(row["matched_set_id"] for row in output.get(
            "game_rows",
            [],
        ))
    combined["seeds"] = sorted(seeds)
    combined["policies"] = sorted(policies)
    combined["regimes"] = [
        regime_by_id[key] for key in sorted(regime_by_id)
    ]
    combined["matched_sets"] = len(matched_sets)
    return combined
