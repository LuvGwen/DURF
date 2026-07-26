import csv
import random
from collections import defaultdict

from config import DEFAULT_MAX_ROUNDS
from game import Game, create_default_players
from ml_behavioral_regimes import get_stage15_base_config
from ml_wolf_kill_model_freeze import (
    FROZEN_MODEL_MANIFEST_PATH,
    LIVE_FINAL_TEST_SEEDS,
    load_json,
    validate_frozen_model_manifest,
)
from ml_wolf_kill_policy import PRIMARY_WOLF_KILL_POLICIES
from roles import HUNTER, SEER, WITCH, WOLF_TEAM
from seat_order_neutral import stable_seed


SPECIAL_ROLES = {SEER, WITCH, HUNTER}


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


def get_stage2a_behavioral_regimes():
    base = get_stage15_base_config()

    def config(name, description, **updates):
        merged = dict(base)
        merged.update({
            "enable_position_model": True,
            "randomize_seat_roles": True,
            "enable_wolf_strategy": True,
            "wolf_kill_strategy": "threat_based",
            "wolf_kill_noise_level": 0.0,
            "seer_avoid_repeat_checks": True,
            "enable_last_words": False,
        })
        merged.update(updates)
        return {
            "behavioral_regime_id": name,
            "description": description,
            "config": merged,
            "speech_setting": str(merged.get("enable_speech")),
            "herding_setting": str(merged.get("enable_herding")),
            "deception_setting": str(merged.get("enable_wolf_deception")),
            "risk_distribution": merged.get(
                "risk_preference_mode",
                "disabled",
            ) if merged.get("enable_risk_preference") else "disabled",
            "seer_strategy": merged.get("seer_check_strategy"),
            "vote_strategy": (
                "suspicion_based"
                if merged.get("use_suspicion_voting")
                else "random"
            ),
            "witch_parameters": (
                f"threshold={merged.get('witch_poison_threshold')};"
                f"save={merged.get('witch_save_probability')}"
            ),
            "hunter_behavior": str(merged.get("enable_hunter")),
            "wolf_deception_strategy": merged.get(
                "wolf_deception_strategy",
                "disabled",
            ) if merged.get("enable_wolf_deception") else "disabled",
            "neutral_mode_setting": str(
                merged.get("seat_order_neutral_mode", False)
            ),
        }

    return [
        config(
            "baseline_speech_enabled",
            "Baseline ten-player randomized-role regime with speech enabled.",
            enable_speech=True,
            enable_herding=False,
            enable_wolf_deception=False,
            enable_deception_credibility=False,
            enable_speaker_memory=False,
            use_suspicion_voting=True,
            seer_check_strategy="information_gain_proxy",
        ),
        config(
            "speech_disabled",
            "Speech disabled, suspicion voting retained.",
            enable_speech=False,
            enable_herding=False,
            enable_wolf_deception=False,
            enable_speaker_memory=False,
            use_suspicion_voting=True,
            seer_check_strategy="information_gain_proxy",
        ),
        config(
            "herding_enabled",
            "Speech and herding enabled without wolf deception.",
            enable_speech=True,
            enable_herding=True,
            enable_role_prior=True,
            enable_speaker_memory=True,
            trust_vote_weight=0.20,
            use_suspicion_voting=True,
            seer_check_strategy="highest_p_wolf",
        ),
        config(
            "deception_enabled",
            "Adaptive wolf deception with credibility and trust memory.",
            enable_speech=True,
            enable_herding=True,
            enable_role_prior=True,
            enable_wolf_deception=True,
            wolf_deception_strategy="adaptive",
            enable_deception_credibility=True,
            enable_speaker_memory=True,
            trust_vote_weight=0.20,
            use_suspicion_voting=True,
            seer_check_strategy="information_gain_proxy",
        ),
        config(
            "heterogeneous_risk_preference",
            "Role-based risk preferences with deception enabled.",
            enable_speech=True,
            enable_herding=True,
            enable_role_prior=True,
            enable_wolf_deception=True,
            wolf_deception_strategy="adaptive",
            enable_deception_credibility=True,
            enable_speaker_memory=True,
            enable_risk_preference=True,
            risk_preference_mode="role_based",
            trust_vote_weight=0.20,
            use_suspicion_voting=True,
            seer_check_strategy="coverage_balanced",
        ),
        config(
            "strong_village_information",
            "High-information village with structured seer checks and strong saving.",
            enable_speech=True,
            enable_herding=True,
            enable_role_prior=True,
            enable_speaker_memory=True,
            trust_vote_weight=0.30,
            witch_save_probability=0.90,
            use_suspicion_voting=True,
            seer_check_strategy="information_gain_proxy",
        ),
        config(
            "weak_village_information",
            "Low-information village with random voting and weaker witch saves.",
            enable_speech=False,
            enable_herding=False,
            enable_role_prior=False,
            enable_speaker_memory=False,
            witch_save_probability=0.40,
            use_suspicion_voting=False,
            seer_check_strategy="random",
        ),
        config(
            "mixed_seer_strategy",
            "Coverage-balanced seer checks with normal voting.",
            enable_speech=True,
            enable_herding=True,
            enable_role_prior=True,
            enable_speaker_memory=True,
            use_suspicion_voting=True,
            seer_check_strategy="coverage_balanced",
        ),
        config(
            "mixed_voting_strategy",
            "Randomized legal day voting with speech enabled.",
            enable_speech=True,
            enable_herding=False,
            enable_role_prior=False,
            enable_speaker_memory=False,
            use_suspicion_voting=False,
            seer_check_strategy="highest_suspicion",
        ),
        config(
            "mixed_wolf_deception_strategy",
            "Mixed wolf deception policy instead of adaptive deception.",
            enable_speech=True,
            enable_herding=True,
            enable_role_prior=True,
            enable_wolf_deception=True,
            wolf_deception_strategy="mixed",
            enable_deception_credibility=True,
            enable_speaker_memory=True,
            trust_vote_weight=0.20,
            use_suspicion_voting=True,
            seer_check_strategy="information_gain_proxy",
        ),
    ]


def build_game_for_policy(
    seed,
    base_game_index,
    regime,
    policy_name,
    manifest,
    manifest_path=FROZEN_MODEL_MANIFEST_PATH,
):
    random.seed(stable_seed(
        "stage2a_live_initial_state",
        seed,
        base_game_index,
        regime["behavioral_regime_id"],
    ))
    config = dict(regime["config"])
    players = create_default_players(
        role_setup=config.get("role_setup"),
        initial_p_wolf=config.get("initial_p_wolf"),
    )
    matched_set_id = (
        f"seed_{seed}_base_{base_game_index}_"
        f"regime_{regime['behavioral_regime_id']}"
    )
    game = Game(
        players,
        **config,
        base_game_index=base_game_index,
        label_condition=regime["behavioral_regime_id"],
        main_game_seed=stable_seed(
            "stage2a_live_game",
            seed,
            base_game_index,
            regime["behavioral_regime_id"],
        ),
        neutral_seed=stable_seed(
            "stage2a_live_neutral",
            seed,
            base_game_index,
            regime["behavioral_regime_id"],
        ),
        enable_ml_wolf_kill_policy=True,
        ml_wolf_kill_policy_name=policy_name,
        ml_wolf_kill_model_manifest_path=str(manifest_path),
        ml_wolf_kill_manifest_hash=manifest["manifest_hash"],
        ml_wolf_kill_epsilon=0.10,
    )
    return game, matched_set_id


def summarize_game(game, result, seed, base_game_index, regime, policy_name, matched_set_id):
    decision_events = [
        event for event in game.event_log
        if event["event_type"] == "wolf_kill_policy_decision"
    ]
    night_kill_events = [
        event for event in game.event_log
        if event["event_type"] == "night_kill"
    ]
    prevented_events = [
        event for event in game.event_log
        if event["event_type"] == "night_kill_prevented"
    ]
    hunter_events = [
        event for event in game.event_log
        if event["event_type"] == "hunter_shot"
    ]
    player_by_id = {
        player.player_id: player
        for player in game.state.players
    }
    successful_kill_roles = []
    for event in night_kill_events:
        target_id = event.get("content", {}).get("target")
        player = player_by_id.get(target_id)
        successful_kill_roles.append(player.role if player else "")
    day_vote_events = [
        event for event in game.event_log
        if event["event_type"] == "day_vote"
    ]
    wolf_vote_control = 0
    for event in day_vote_events:
        eliminated = event.get("content", {}).get("eliminated")
        player = player_by_id.get(eliminated)
        if player is not None and not player.is_wolf():
            wolf_vote_control += 1
    first_wolf_death_round = ""
    for event in game.event_log:
        if event["event_type"] != "player_death":
            continue
        player = player_by_id.get(event.get("content", {}).get("player"))
        if player is not None and player.is_wolf():
            first_wolf_death_round = event["round"]
            break

    wolf_win = 1 if result["winner"] == "wolf" else 0
    game_row = {
        "matched_set_id": matched_set_id,
        "game_id": f"{matched_set_id}_policy_{policy_name}",
        "seed": seed,
        "base_game_index": base_game_index,
        "behavioral_regime_id": regime["behavioral_regime_id"],
        "policy_name": policy_name,
        "winner": result["winner"],
        "wolf_win": wolf_win,
        "village_win": 1 if result["winner"] == "village" else 0,
        "draw": 1 if result["winner"] == "draw" else 0,
        "round_number": result["round_number"],
        "total_rounds": result["round_number"],
        "time_to_parity": result["round_number"] if wolf_win else "",
        "successful_night_kills": len(night_kill_events),
        "night_kill_attempts": len(night_kill_events) + len(prevented_events),
        "special_role_kills": sum(
            1 for role in successful_kill_roles
            if role in SPECIAL_ROLES
        ),
        "seer_kills": successful_kill_roles.count(SEER),
        "witch_kills": successful_kill_roles.count(WITCH),
        "hunter_kills": successful_kill_roles.count(HUNTER),
        "witch_saves": len(prevented_events),
        "hunter_retaliations": len(hunter_events),
        "wolf_survival_count": result["num_alive_wolves"],
        "first_wolf_death_round": first_wolf_death_round,
        "vote_control_proxy": wolf_vote_control,
        "wolf_kill_decisions": len(decision_events),
        "manifest_hash": (
            decision_events[0]["content"].get("manifest_hash")
            if decision_events else ""
        ),
    }
    return game_row


def extract_live_decision_rows(game, game_row):
    decision_rows = []
    prediction_rows = []
    shift_rows = []
    for decision_index, event in enumerate([
        event for event in game.event_log
        if event["event_type"] == "wolf_kill_policy_decision"
    ], start=1):
        content = event["content"]
        decision_id = (
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
            "round": event["round"],
            "phase": event["phase"],
            "selected_target": selected_target,
            "selected_target_actor_uid": content.get(
                "selected_target_actor_uid"
            ),
            "selected_target_role": content.get(
                "selected_target_role_for_posthoc_analysis"
            ),
            "selection_reason": content.get("selection_reason"),
            "existing_rule_target": content.get("existing_rule_target"),
            "frozen_ml_target": content.get("frozen_ml_target"),
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
        for candidate in content.get("candidate_rows", []):
            candidate_row = {
                **base,
                "candidate_uid": candidate.get("candidate_uid"),
                "candidate_player_id": candidate.get("candidate_player_id"),
                "candidate_role_for_posthoc_analysis": candidate.get(
                    "candidate_role_for_posthoc_analysis"
                ),
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
            shift_rows.append(candidate_row)
    return decision_rows, prediction_rows, shift_rows


def run_wolf_kill_live_experiment(
    output_dir,
    manifest_path=FROZEN_MODEL_MANIFEST_PATH,
    seeds=None,
    base_configs_per_seed=1,
    policies=None,
    regimes=None,
    max_rounds=DEFAULT_MAX_ROUNDS,
):
    if seeds is None:
        seeds = LIVE_FINAL_TEST_SEEDS
    if policies is None:
        policies = list(PRIMARY_WOLF_KILL_POLICIES)
    if regimes is None:
        regimes = get_stage2a_behavioral_regimes()

    manifest = load_json(manifest_path)
    validate_frozen_model_manifest(manifest)
    game_rows = []
    decision_rows = []
    prediction_rows = []
    shift_rows = []

    for seed in seeds:
        for base_game_index in range(1, base_configs_per_seed + 1):
            for regime in regimes:
                for policy_name in policies:
                    game, matched_set_id = build_game_for_policy(
                        seed,
                        base_game_index,
                        regime,
                        policy_name,
                        manifest,
                        manifest_path=manifest_path,
                    )
                    result = game.run_game(max_rounds=max_rounds)
                    game_row = summarize_game(
                        game,
                        result,
                        seed,
                        base_game_index,
                        regime,
                        policy_name,
                        matched_set_id,
                    )
                    game_rows.append(game_row)
                    rows = extract_live_decision_rows(game, game_row)
                    decision_rows.extend(rows[0])
                    prediction_rows.extend(rows[1])
                    shift_rows.extend(rows[2])

    write_csv(
        output_dir / "wolf_kill_live_game_level_raw.csv",
        game_rows,
        sorted({key for row in game_rows for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_live_decision_raw.csv",
        decision_rows,
        sorted({key for row in decision_rows for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_policy_predictions_raw.csv",
        prediction_rows,
        sorted({key for row in prediction_rows for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_distribution_shift_raw.csv",
        shift_rows,
        sorted({key for row in shift_rows for key in row}),
    )
    return {
        "game_rows": game_rows,
        "decision_rows": decision_rows,
        "prediction_rows": prediction_rows,
        "shift_rows": shift_rows,
        "seeds": seeds,
        "policies": policies,
        "regimes": regimes,
        "matched_sets": len({
            row["matched_set_id"] for row in game_rows
        }),
    }


def summarize_by_group(game_rows, group_field):
    grouped = defaultdict(list)
    for row in game_rows:
        grouped[row[group_field]].append(row)
    output = []
    for group, rows in sorted(grouped.items()):
        output.append({
            group_field: group,
            "games": len(rows),
            "wolf_win_rate": mean(row["wolf_win"] for row in rows),
            "village_win_rate": mean(row["village_win"] for row in rows),
            "avg_rounds": mean(row["round_number"] for row in rows),
        })
    return output


def mean(values):
    numeric = [float(value) for value in values]
    return sum(numeric) / len(numeric) if numeric else 0.0


if __name__ == "__main__":
    from pathlib import Path

    output = run_wolf_kill_live_experiment(
        Path("results") / "ml_optimization_stage2a",
        seeds=[100],
        base_configs_per_seed=1,
    )
    print("Wolf-kill live experiment smoke run complete")
    print("Live games:", len(output["game_rows"]))
