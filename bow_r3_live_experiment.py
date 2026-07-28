"""Run R3 guarded BoW live-policy experiments."""

import csv
import hashlib
import random
import subprocess
from pathlib import Path

from bow_r3_full_rollout_analysis import rollout_rows_from_vote_decisions
from bow_r3_shadow_evaluation import shadow_rows_from_vote_event
from bow_r3_template_conditions import (
    R3_BEHAVIORAL_REGIMES,
    R3_TEMPLATE_CONDITIONS,
    behavioral_regime_registry_rows,
    template_condition_registry_rows,
)
from config import (
    DEFAULT_MAX_ROUNDS,
    TEN_PLAYER_CREDIBILITY_COST_SCALE,
    TEN_PLAYER_HERDING_WEIGHT_SCALE,
    TEN_PLAYER_INITIAL_P_WOLF,
    TEN_PLAYER_ROLE_SETUP,
    TEN_PLAYER_SPEECH_SIGNAL_SCALE,
)
from game import Game, create_default_players


R3_RESULTS_DIR = Path("results") / "bow_integration_stage_r3"
SOURCE_COMMIT = None

R3_SEED_GROUPS = {
    "development": list(range(400, 410)),
    "validation": list(range(410, 415)),
    "final_test": list(range(420, 440)),
    "ood_template_final": list(range(440, 450)),
    "ood_regime_final": list(range(450, 460)),
}

PRIMARY_CONDITIONS = [
    "existing_system",
    "guarded_bow_010_live",
    "structured_bow_guarded_live",
    "selective_bow_vote_override_live",
]

DIAGNOSTIC_CONDITIONS = [
    "guarded_bow_020_live",
    "pure_bow_diagnostic_live",
    "existing_with_bow_shadow",
]

ALL_CONDITIONS = PRIMARY_CONDITIONS + DIAGNOSTIC_CONDITIONS


def stable_seed(*parts):
    digest = hashlib.sha256(
        "|".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()
    return int(digest[:16], 16) % (2 ** 32)


def current_git_commit():
    global SOURCE_COMMIT
    if SOURCE_COMMIT is not None:
        return SOURCE_COMMIT
    try:
        SOURCE_COMMIT = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        SOURCE_COMMIT = "unknown"
    return SOURCE_COMMIT


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            restval="",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def base_game_config(behavioral_regime):
    base = {
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": True,
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "seer_first",
        "enable_wolf_deception": False,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": True,
        "enable_risk_preference": False,
        "enable_last_words": False,
        "trust_vote_weight": 0.20,
        "speech_signal_scale": TEN_PLAYER_SPEECH_SIGNAL_SCALE,
        "credibility_cost_scale": TEN_PLAYER_CREDIBILITY_COST_SCALE,
        "herding_alpha": 0.5 * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "herding_beta": 0.3 * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "herding_gamma": 0.2 * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "seer_check_strategy": "information_gain_proxy",
        "seer_avoid_repeat_checks": True,
        "enable_position_model": True,
        "randomize_seat_roles": True,
        "role_setup": TEN_PLAYER_ROLE_SETUP,
        "initial_p_wolf": TEN_PLAYER_INITIAL_P_WOLF,
    }

    if behavioral_regime == "baseline_speech":
        return base
    if behavioral_regime == "herding_enabled":
        return {**base, "herding_gamma": 0.28}
    if behavioral_regime == "deception_enabled":
        return {
            **base,
            "enable_wolf_deception": True,
            "wolf_deception_strategy": "adaptive",
        }
    if behavioral_regime == "heterogeneous_risk":
        return {
            **base,
            "enable_risk_preference": True,
            "risk_preference_mode": "role_based",
            "enable_wolf_deception": True,
        }
    if behavioral_regime == "strong_village_information":
        return {
            **base,
            "seer_check_strategy": "information_gain_proxy",
            "seer_avoid_repeat_checks": True,
            "witch_save_probability": 0.85,
        }
    if behavioral_regime == "weak_village_information":
        return {
            **base,
            "enable_seer": False,
            "witch_save_probability": 0.45,
            "enable_wolf_deception": True,
        }
    if behavioral_regime == "high_emotional_speech":
        return {
            **base,
            "enable_wolf_deception": True,
            "wolf_deception_strategy": "false_accuse",
        }
    if behavioral_regime == "high_low_information_speech":
        return {
            **base,
            "enable_role_prior": False,
            "enable_herding": False,
        }
    if behavioral_regime == "mixed_structured_speech":
        return {
            **base,
            "enable_wolf_deception": True,
            "wolf_deception_strategy": "mixed",
            "enable_last_words": True,
        }
    if behavioral_regime == "unseen_speech_regime":
        return {
            **base,
            "use_suspicion_voting": False,
            "enable_wolf_strategy": False,
            "enable_wolf_deception": True,
            "enable_risk_preference": True,
            "risk_preference_mode": "mixed",
            "enable_last_words": True,
        }
    raise ValueError(f"Unknown R3 behavioral regime: {behavioral_regime}")


def policy_config(condition_name):
    if condition_name == "existing_system":
        return {"enable_bow_r3": False}
    if condition_name == "guarded_bow_010_live":
        return {
            "enable_bow_r3": True,
            "r3_belief_policy": "guarded_bow_010",
            "r3_vote_policy": "guarded_bow_vote_010",
        }
    if condition_name == "structured_bow_guarded_live":
        return {
            "enable_bow_r3": True,
            "r3_belief_policy": "structured_bow_guarded",
            "r3_vote_policy": "structured_bow_vote",
        }
    if condition_name == "selective_bow_vote_override_live":
        return {
            "enable_bow_r3": True,
            "r3_belief_policy": "bow_shadow_belief",
            "r3_vote_policy": "selective_bow_vote_override",
        }
    if condition_name == "guarded_bow_020_live":
        return {
            "enable_bow_r3": True,
            "r3_belief_policy": "guarded_bow_020",
            "r3_vote_policy": "guarded_bow_vote_010",
        }
    if condition_name == "pure_bow_diagnostic_live":
        return {
            "enable_bow_r3": True,
            "r3_belief_policy": "pure_bow_diagnostic",
            "r3_vote_policy": "pure_bow_vote_diagnostic",
        }
    if condition_name == "existing_with_bow_shadow":
        return {
            "enable_bow_r3": True,
            "r3_belief_policy": "bow_shadow_belief",
            "r3_vote_policy": "bow_shadow_vote",
        }
    raise ValueError(f"Unknown R3 condition: {condition_name}")


def seed_registry_rows():
    rows = []
    for split, seeds in R3_SEED_GROUPS.items():
        for seed in seeds:
            rows.append({
                "seed": seed,
                "seed_split": split,
                "used_for_threshold_selection": split in {
                    "development",
                    "validation",
                },
                "excluded_from_threshold_selection": split not in {
                    "development",
                    "validation",
                },
            })
    return rows


def matched_set_rows(matched_games_per_cell=2):
    rows = []
    for seed_split, seeds in R3_SEED_GROUPS.items():
        for seed in seeds:
            for behavioral_regime in R3_BEHAVIORAL_REGIMES:
                for template_condition in R3_TEMPLATE_CONDITIONS:
                    for game_index in range(1, matched_games_per_cell + 1):
                        matched_set_id = (
                            f"r3_{seed_split}_{seed}_{behavioral_regime}_"
                            f"{template_condition}_{game_index}"
                        )
                        rows.append({
                            "matched_set_id": matched_set_id,
                            "seed_split": seed_split,
                            "seed": seed,
                            "behavioral_regime": behavioral_regime,
                            "template_condition": template_condition,
                            "base_game_index": game_index,
                        })
    return rows


def player_lookup(game):
    return {player.player_id: player for player in game.state.players}


def safe_role_label(players, player_id):
    try:
        player = players.get(int(player_id))
    except (TypeError, ValueError):
        return "", "", ""
    if player is None:
        return "", "", ""
    return player.role, player.team, player.is_wolf()


def extract_event_rows(game, game_row):
    players = player_lookup(game)
    speech_rows = []
    belief_rows = []
    vote_rows = []
    shadow_rows = []
    template_rows = []

    for event_index, event in enumerate(game.event_log):
        event_type = event.get("event_type")
        content = event.get("content", {})
        base = {
            "game_uid": game_row["game_uid"],
            "matched_set_id": game_row["matched_set_id"],
            "condition_name": game_row["condition_name"],
            "policy_name": game_row["policy_name"],
            "seed": game_row["seed"],
            "seed_split": game_row["seed_split"],
            "template_condition": game_row["template_condition"],
            "behavioral_regime": game_row["behavioral_regime"],
            "round": event.get("round"),
            "phase": event.get("phase"),
            "event_index": event_index,
        }

        if event_type == "speech":
            role, team, is_wolf = safe_role_label(players, content.get("speaker"))
            speech_rows.append({
                **base,
                "speaker": content.get("speaker"),
                "target": content.get("target"),
                "speech_type": content.get("speech_type", ""),
                "is_deception": bool(content.get("is_deception")),
                "deception_type": content.get("deception_type", ""),
                "utterance_text": content.get("text", ""),
                "speaker_role": role,
                "speaker_team": team,
                "speaker_is_wolf": is_wolf,
            })

        if event_type == "r3_bow_belief_update":
            role, team, is_wolf = safe_role_label(players, content.get("speaker"))
            target_role, target_team, target_is_wolf = safe_role_label(
                players,
                content.get("belief_target"),
            )
            row = {
                **base,
                **{key: content.get(key, "") for key in [
                    "speaker",
                    "speech_target",
                    "belief_target",
                    "template_family",
                    "template_id",
                    "known_token_fraction",
                    "unknown_token_fraction",
                    "vocabulary_overlap",
                    "ngram_novelty",
                    "ood_category",
                    "missing_feature_count",
                    "bow_signal",
                    "structured_signal",
                    "bow_werewolf_leaning_score",
                    "bow_emotional_intensity_score",
                    "bow_information_density_score",
                    "token_count",
                    "unique_token_count",
                    "before_p_wolf",
                    "after_p_wolf",
                    "before_suspicion",
                    "after_suspicion",
                    "p_wolf_delta",
                    "suspicion_delta",
                    "proposed_guarded_adjustment",
                    "proposed_pure_bow_adjustment",
                    "signal_extremity",
                    "normalization_distance",
                    "live_applied",
                ]},
                "speaker_role": role,
                "speaker_team": team,
                "speaker_is_wolf": is_wolf,
                "belief_target_role": target_role,
                "belief_target_team": target_team,
                "belief_target_is_wolf": target_is_wolf,
                "listener_count": len(content.get("listener_ids", [])),
            }
            belief_rows.append(row)
            template_rows.append({
                **base,
                "speaker": content.get("speaker"),
                "template_family": content.get("template_family", ""),
                "template_id": content.get("template_id", ""),
                "known_token_fraction": content.get("known_token_fraction", 0.0),
                "unknown_token_fraction": content.get("unknown_token_fraction", 0.0),
                "vocabulary_overlap": content.get("vocabulary_overlap", 0.0),
                "ngram_novelty": content.get("ngram_novelty", 0.0),
                "score_extremity": content.get("score_extremity", 0.0),
                "normalization_distance": content.get(
                    "normalization_distance",
                    0.0,
                ),
                "missing_feature_count": content.get("missing_feature_count", 0),
                "ood_category": content.get("ood_category", ""),
            })

        if event_type == "r3_bow_vote_decision":
            existing_role, existing_team, existing_is_wolf = safe_role_label(
                players,
                content.get("existing_target"),
            )
            selected_role, selected_team, selected_is_wolf = safe_role_label(
                players,
                content.get("selected_target"),
            )
            row = {
                **base,
                **{key: content.get(key, "") for key in [
                    "voter",
                    "existing_target",
                    "selected_target",
                    "bow_guarded_target",
                    "structured_bow_target",
                    "pure_bow_target",
                    "selected_reason",
                    "selected_score",
                    "disagrees_with_existing",
                    "ood_category",
                    "selected_bow_signal",
                    "selected_information_density",
                    "selected_emotional_intensity",
                    "selective_override_margin",
                    "selective_min_information_density",
                ]},
                "existing_target_role": existing_role,
                "existing_target_team": existing_team,
                "existing_target_is_wolf": existing_is_wolf,
                "selected_target_role": selected_role,
                "selected_target_team": selected_team,
                "selected_target_is_wolf": selected_is_wolf,
            }
            vote_rows.append(row)
            shadow_rows.extend(shadow_rows_from_vote_event(base, content))

    return speech_rows, belief_rows, vote_rows, shadow_rows, template_rows


def run_single_game(matched_row, condition_name, max_rounds):
    seed = int(matched_row["seed"])
    game_seed = stable_seed(
        "r3_live",
        matched_row["matched_set_id"],
        condition_name,
    )
    random.seed(game_seed)
    players = create_default_players(
        role_setup=TEN_PLAYER_ROLE_SETUP,
        initial_p_wolf=TEN_PLAYER_INITIAL_P_WOLF,
    )
    config = {
        **base_game_config(matched_row["behavioral_regime"]),
        **policy_config(condition_name),
        "r3_template_condition": matched_row["template_condition"],
        "r3_behavioral_regime": matched_row["behavioral_regime"],
        "base_game_index": matched_row["base_game_index"],
        "main_game_seed": seed,
    }
    game = Game(players, **config)
    result = game.run_game(max_rounds=max_rounds)
    game_uid = f"{matched_row['matched_set_id']}__{condition_name}"
    player_by_id = player_lookup(game)
    day_vote_events = [
        event for event in game.event_log if event["event_type"] == "day_vote"
    ]
    eliminated_wolves = 0
    eliminated_villagers = 0
    for event in day_vote_events:
        eliminated = event.get("content", {}).get("eliminated")
        player = player_by_id.get(eliminated)
        if player is None:
            continue
        if player.is_wolf():
            eliminated_wolves += 1
        else:
            eliminated_villagers += 1
    game_row = {
        "game_uid": game_uid,
        "matched_set_id": matched_row["matched_set_id"],
        "condition_name": condition_name,
        "policy_name": condition_name,
        "seed": seed,
        "seed_split": matched_row["seed_split"],
        "base_game_index": matched_row["base_game_index"],
        "template_condition": matched_row["template_condition"],
        "behavioral_regime": matched_row["behavioral_regime"],
        "winner": result["winner"],
        "village_win": result["winner"] == "village",
        "wolf_win": result["winner"] == "wolf",
        "draw": result["winner"] == "draw",
        "round_number": result["round_number"],
        "num_events": len(game.event_log),
        "num_alive_players": result["num_alive_players"],
        "num_alive_wolves": result["num_alive_wolves"],
        "num_alive_villagers": result["num_alive_villagers"],
        "num_speech_events": sum(
            1 for event in game.event_log if event["event_type"] == "speech"
        ),
        "num_r3_belief_updates": sum(
            1 for event in game.event_log
            if event["event_type"] == "r3_bow_belief_update"
        ),
        "num_r3_vote_decisions": sum(
            1 for event in game.event_log
            if event["event_type"] == "r3_bow_vote_decision"
        ),
        "num_r3_vote_disagreements": sum(
            1 for event in game.event_log
            if (
                event["event_type"] == "r3_bow_vote_decision"
                and event.get("content", {}).get("disagrees_with_existing")
            )
        ),
        "num_selective_overrides": sum(
            1 for event in game.event_log
            if (
                event["event_type"] == "r3_bow_vote_decision"
                and event.get("content", {}).get("selected_reason")
                == "override_allowed"
            )
        ),
        "num_day_votes": len(day_vote_events),
        "num_day_eliminated_wolves": eliminated_wolves,
        "num_day_eliminated_villagers": eliminated_villagers,
        "source_commit": current_git_commit(),
    }
    return game, game_row


def run_r3_live_experiment(
    matched_games_per_cell=1,
    max_rounds=DEFAULT_MAX_ROUNDS,
    output_dir=R3_RESULTS_DIR,
    conditions=None,
    matched_rows_override=None,
):
    output_dir = Path(output_dir)
    conditions = conditions or ALL_CONDITIONS
    matched_rows = (
        matched_rows_override
        if matched_rows_override is not None
        else matched_set_rows(matched_games_per_cell)
    )
    game_rows = []
    speech_rows = []
    belief_rows = []
    vote_rows = []
    shadow_rows = []
    template_rows = []

    for matched_row in matched_rows:
        for condition_name in conditions:
            game, game_row = run_single_game(
                matched_row,
                condition_name,
                max_rounds,
            )
            game_rows.append(game_row)
            extracted = extract_event_rows(game, game_row)
            speech_rows.extend(extracted[0])
            belief_rows.extend(extracted[1])
            vote_rows.extend(extracted[2])
            shadow_rows.extend(extracted[3])
            template_rows.extend(extracted[4])

    rollout_rows = rollout_rows_from_vote_decisions(game_rows, vote_rows)
    policy_prediction_rows = [
        {
            "game_uid": row["game_uid"],
            "matched_set_id": row["matched_set_id"],
            "condition_name": row["condition_name"],
            "policy_name": row["policy_name"],
            "seed": row["seed"],
            "seed_split": row["seed_split"],
            "template_condition": row["template_condition"],
            "behavioral_regime": row["behavioral_regime"],
            "round": row["round"],
            "belief_target": row["belief_target"],
            "prediction_score": row["after_p_wolf"],
            "label_is_wolf": row["belief_target_is_wolf"],
            "bow_signal": row["bow_signal"],
            "structured_signal": row["structured_signal"],
        }
        for row in belief_rows
    ]

    write_csv(output_dir / "r3_live_game_level_raw.csv", game_rows)
    write_csv(output_dir / "r3_live_speech_event_raw.csv", speech_rows)
    write_csv(output_dir / "r3_live_belief_update_raw.csv", belief_rows)
    write_csv(output_dir / "r3_live_vote_decision_raw.csv", vote_rows)
    write_csv(output_dir / "r3_shadow_recommendation_raw.csv", shadow_rows)
    write_csv(
        output_dir / "r3_vote_disagreement_rollout_raw.csv",
        rollout_rows,
    )
    write_csv(output_dir / "r3_template_shift_raw.csv", template_rows)
    write_csv(output_dir / "r3_policy_prediction_raw.csv", policy_prediction_rows)
    write_csv(output_dir / "r3_seed_registry.csv", seed_registry_rows())
    write_csv(
        output_dir / "r3_template_condition_registry.csv",
        template_condition_registry_rows(),
    )
    write_csv(
        output_dir / "r3_behavioral_regime_registry.csv",
        behavioral_regime_registry_rows(),
    )
    return {
        "game_rows": game_rows,
        "speech_rows": speech_rows,
        "belief_rows": belief_rows,
        "vote_rows": vote_rows,
        "shadow_rows": shadow_rows,
        "rollout_rows": rollout_rows,
        "template_rows": template_rows,
        "policy_prediction_rows": policy_prediction_rows,
        "matched_set_count": len(matched_rows),
    }


if __name__ == "__main__":
    artifacts = run_r3_live_experiment()
    print("R3 live experiment complete")
    print(f"Matched sets: {artifacts['matched_set_count']}")
    print(f"Live games: {len(artifacts['game_rows'])}")
    print(f"Speech events: {len(artifacts['speech_rows'])}")
    print(f"Belief updates: {len(artifacts['belief_rows'])}")
    print(f"Vote decisions: {len(artifacts['vote_rows'])}")
