import argparse
import csv
import platform
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

from config import DEFAULT_MAX_ROUNDS
from game import Game, create_default_players
from ml_counterfactual_rollout import ROLLOUT_FIELD_COLUMNS, add_rollout_values_to_rows
from ml_decision_logger import (
    DECISION_DATASET_FIELDNAMES,
    extract_decision_rows_from_game,
    split_for_seed,
    split_rows_by_decision_type,
    validate_decision_rows,
    write_csv_rows,
)
from ml_feature_registry import FEATURE_COLUMNS, write_feature_registry_markdown
from seat_order_neutral import stable_seed
from ten_player_seer_position_experiment import SEER_POSITION_BASE_CONFIG


RESULTS_DIR = Path("results") / "ml_optimization_stage1"
MODELS_DIR = RESULTS_DIR / "models"
SEEDS = [42, 43, 44, 45, 46]
DEFAULT_GAMES_PER_SEED = 12
DEFAULT_MAX_CANDIDATES = 6
DEFAULT_DECISION_LIMITS = {
    "seer_check": 500,
    "wolf_kill": 500,
    "day_vote": 1000,
}
DEFAULT_ROLLOUT_COUNTS = {
    "seer_check": 5,
    "wolf_kill": 5,
    "day_vote": 3,
}


DATASET_PATHS = {
    "seer_check": RESULTS_DIR / "ml_seer_check_decision_dataset.csv",
    "wolf_kill": RESULTS_DIR / "ml_wolf_kill_decision_dataset.csv",
    "day_vote": RESULTS_DIR / "ml_vote_decision_dataset.csv",
    "identity": RESULTS_DIR / "ml_identity_prediction_dataset.csv",
    "splits": RESULTS_DIR / "ml_dataset_split_assignments.csv",
    "validation": RESULTS_DIR / "ml_dataset_validation_summary.csv",
    "rollout_summary": RESULTS_DIR / "ml_rollout_value_summary.csv",
    "schema": RESULTS_DIR / "ml_stage1_schema.md",
    "feature_registry": RESULTS_DIR / "ml_feature_registry.md",
    "limitations": RESULTS_DIR / "ml_stage1_limitations.md",
}


ACTION_VALUE_FIELDNAMES = (
    DECISION_DATASET_FIELDNAMES + ROLLOUT_FIELD_COLUMNS
)


def get_ml_stage1_game_config():
    config = dict(SEER_POSITION_BASE_CONFIG)
    config.update({
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": True,
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "seer_first",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "trust_vote_weight": 0.20,
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": True,
        "enable_last_words": False,
        "enable_risk_preference": False,
        "enable_position_model": True,
        "randomize_seat_roles": True,
        "seer_check_strategy": "information_gain_proxy",
        "seer_avoid_repeat_checks": True,
    })
    return config


def generate_reference_game(seed, game_index, config=None):
    if config is None:
        config = get_ml_stage1_game_config()
    main_game_seed = stable_seed("ml_stage1_reference_game", seed, game_index)
    random.seed(main_game_seed)
    players = create_default_players(
        role_setup=config["role_setup"],
        initial_p_wolf=config["initial_p_wolf"],
    )
    game = Game(
        players,
        main_game_seed=main_game_seed,
        base_game_index=game_index,
        label_condition="ml_stage1",
        **config,
    )
    result = game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
    return game, result, main_game_seed


def limit_rows_by_decision_count(rows, limits):
    selected_decisions = defaultdict(set)
    selected_rows = []
    for row in rows:
        decision_type = row["decision_type"]
        decision_id = row["decision_id"]
        if decision_id in selected_decisions[decision_type]:
            selected_rows.append(row)
            continue
        if len(selected_decisions[decision_type]) >= limits.get(
            decision_type,
            0,
        ):
            continue
        selected_decisions[decision_type].add(decision_id)
        selected_rows.append(row)
    return selected_rows


def generate_ml_decision_rows(
    seeds=None,
    games_per_seed=DEFAULT_GAMES_PER_SEED,
    max_candidates=DEFAULT_MAX_CANDIDATES,
    decision_limits=None,
    rollout_counts=None,
):
    if seeds is None:
        seeds = SEEDS
    if decision_limits is None:
        decision_limits = dict(DEFAULT_DECISION_LIMITS)
    if rollout_counts is None:
        rollout_counts = dict(DEFAULT_ROLLOUT_COUNTS)

    config = get_ml_stage1_game_config()
    all_rows = []
    generated_games = 0
    start_time = time.time()

    for seed in seeds:
        for game_index in range(1, games_per_seed + 1):
            game, _, _ = generate_reference_game(
                seed,
                game_index,
                config=config,
            )
            game_id = f"ml_stage1_seed_{seed}_game_{game_index}"
            all_rows.extend(extract_decision_rows_from_game(
                game,
                game_id=game_id,
                seed=seed,
                base_game_index=game_index,
                max_candidates=max_candidates,
                initial_p_wolf=config["initial_p_wolf"],
            ))
            generated_games += 1

    limited_rows = limit_rows_by_decision_count(all_rows, decision_limits)
    valued_rows = add_rollout_values_to_rows(
        limited_rows,
        rollout_count_by_type=rollout_counts,
        rollout_seed=stable_seed("ml_stage1_rollout_seed", seeds, games_per_seed),
        continuation_policy_config={
            "policy": "fixed_baseline",
            "rollout_mode": "observation_safe_surrogate",
        },
    )
    runtime = time.time() - start_time
    metadata = {
        "seeds": seeds,
        "games_per_seed": games_per_seed,
        "generated_games": generated_games,
        "max_candidates": max_candidates,
        "decision_limits": decision_limits,
        "rollout_counts": rollout_counts,
        "dataset_generation_runtime_seconds": runtime,
        "python_version": platform.python_version(),
    }
    return valued_rows, metadata


def write_split_assignments(rows, path):
    seen = {}
    for row in rows:
        key = row["split_group_id"]
        seen[key] = {
            "split_group_id": key,
            "seed": row["seed"],
            "base_game_index": row["base_game_index"],
            "dataset_split": row["dataset_split"],
        }
    write_csv_rows(
        path,
        list(seen.values()),
        [
            "split_group_id",
            "seed",
            "base_game_index",
            "dataset_split",
        ],
    )


def write_validation_summary(rows, metadata, path):
    validation = validate_decision_rows(rows)
    grouped = split_rows_by_decision_type(rows)
    summary_rows = []
    total_rollouts = sum(
        int(row["rollout_count"]) for row in rows
    )
    summary_rows.append({
        "metric": "generated_games",
        "value": metadata["generated_games"],
    })
    summary_rows.append({
        "metric": "candidate_rows",
        "value": len(rows),
    })
    summary_rows.append({
        "metric": "decision_states",
        "value": validation["decision_count"],
    })
    summary_rows.append({
        "metric": "rollout_simulations",
        "value": total_rollouts,
    })
    summary_rows.append({
        "metric": "validation_passed",
        "value": int(validation["valid"]),
    })
    for decision_type, decision_rows in grouped.items():
        summary_rows.append({
            "metric": f"{decision_type}_candidate_rows",
            "value": len(decision_rows),
        })
        summary_rows.append({
            "metric": f"{decision_type}_decision_states",
            "value": len({row["decision_id"] for row in decision_rows}),
        })
    for split in ["train", "validation", "test"]:
        summary_rows.append({
            "metric": f"{split}_candidate_rows",
            "value": sum(1 for row in rows if row["dataset_split"] == split),
        })
    write_csv_rows(path, summary_rows, ["metric", "value"])


def write_rollout_summary(rows, path):
    summary_rows = []
    for decision_type, decision_rows in split_rows_by_decision_type(rows).items():
        if not decision_rows:
            continue
        values = [float(row["rollout_team_win_rate"]) for row in decision_rows]
        regrets = [
            float(row["rollout_existing_policy_regret"])
            for row in decision_rows
        ]
        summary_rows.append({
            "decision_type": decision_type,
            "candidate_rows": len(decision_rows),
            "decision_states": len({
                row["decision_id"] for row in decision_rows
            }),
            "mean_rollout_team_win_rate": sum(values) / len(values),
            "min_rollout_team_win_rate": min(values),
            "max_rollout_team_win_rate": max(values),
            "mean_existing_policy_regret": sum(regrets) / len(regrets),
            "total_rollout_simulations": sum(
                int(row["rollout_count"]) for row in decision_rows
            ),
        })
    write_csv_rows(
        path,
        summary_rows,
        [
            "decision_type",
            "candidate_rows",
            "decision_states",
            "mean_rollout_team_win_rate",
            "min_rollout_team_win_rate",
            "max_rollout_team_win_rate",
            "mean_existing_policy_regret",
            "total_rollout_simulations",
        ],
    )


def write_schema(path, metadata):
    with path.open("w") as file:
        file.write("# ML Stage 1 Dataset Schema\n\n")
        file.write(
            "Rows are actor-candidate decision snapshots. Each decision "
            "state is expanded to one row per sampled legal candidate. "
            "Features are reconstructed from events available before the "
            "decision. True roles and final winner are label columns only.\n\n"
        )
        file.write("## Pilot Scale\n\n")
        for key, value in metadata.items():
            file.write(f"- `{key}`: `{value}`\n")
        file.write("\n## Required Dataset Files\n\n")
        for name, path_value in DATASET_PATHS.items():
            file.write(f"- `{name}`: `{path_value}`\n")
        file.write("\n## Column Groups\n\n")
        file.write("- Identification columns: decision/game/split metadata.\n")
        file.write("- Feature columns: registered observation-safe values.\n")
        file.write("- Label columns: true role and outcome labels excluded from models.\n")
        file.write("- Rollout columns: offline action-value estimates.\n")


def write_limitations(path):
    with path.open("w") as file:
        file.write("# ML Stage 1 Limitations\n\n")
        file.write(
            "This first ML stage creates observation-safe logs and offline "
            "baseline datasets. It does not deploy learned policies into the "
            "live simulator.\n\n"
        )
        file.write("- The local environment does not include scikit-learn, so tree-based sklearn baselines are marked as unavailable.\n")
        file.write("- Counterfactual rollout values use a deterministic observation-safe surrogate evaluator rather than full mid-game simulator cloning.\n")
        file.write("- Existing global `p_wolf` and `suspicion_score` are treated as observable internal agent-state signals because the current rule engine already uses them for decisions.\n")
        file.write("- Larger recommended pilot scales can be run by increasing CLI limits and rollout counts.\n")


def write_datasets(rows, metadata, results_dir=RESULTS_DIR):
    results_dir.mkdir(exist_ok=True, parents=True)
    MODELS_DIR.mkdir(exist_ok=True, parents=True)
    grouped = split_rows_by_decision_type(rows)
    write_csv_rows(
        DATASET_PATHS["seer_check"],
        grouped.get("seer_check", []),
        ACTION_VALUE_FIELDNAMES,
    )
    write_csv_rows(
        DATASET_PATHS["wolf_kill"],
        grouped.get("wolf_kill", []),
        ACTION_VALUE_FIELDNAMES,
    )
    write_csv_rows(
        DATASET_PATHS["day_vote"],
        grouped.get("day_vote", []),
        ACTION_VALUE_FIELDNAMES,
    )
    write_csv_rows(
        DATASET_PATHS["identity"],
        rows,
        ACTION_VALUE_FIELDNAMES,
    )
    write_split_assignments(rows, DATASET_PATHS["splits"])
    write_validation_summary(rows, metadata, DATASET_PATHS["validation"])
    write_rollout_summary(rows, DATASET_PATHS["rollout_summary"])
    write_schema(DATASET_PATHS["schema"], metadata)
    write_feature_registry_markdown(DATASET_PATHS["feature_registry"])
    write_limitations(DATASET_PATHS["limitations"])


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate ML Stage 1 observation-safe decision datasets.",
    )
    parser.add_argument("--games-per-seed", type=int, default=DEFAULT_GAMES_PER_SEED)
    parser.add_argument("--seeds", default="42,43,44,45,46")
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES)
    parser.add_argument("--seer-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["seer_check"])
    parser.add_argument("--wolf-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["wolf_kill"])
    parser.add_argument("--vote-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["day_vote"])
    parser.add_argument("--seer-rollouts", type=int, default=DEFAULT_ROLLOUT_COUNTS["seer_check"])
    parser.add_argument("--wolf-rollouts", type=int, default=DEFAULT_ROLLOUT_COUNTS["wolf_kill"])
    parser.add_argument("--vote-rollouts", type=int, default=DEFAULT_ROLLOUT_COUNTS["day_vote"])
    return parser.parse_args()


def main():
    args = parse_args()
    seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]
    rows, metadata = generate_ml_decision_rows(
        seeds=seeds,
        games_per_seed=args.games_per_seed,
        max_candidates=args.max_candidates,
        decision_limits={
            "seer_check": args.seer_decision_limit,
            "wolf_kill": args.wolf_decision_limit,
            "day_vote": args.vote_decision_limit,
        },
        rollout_counts={
            "seer_check": args.seer_rollouts,
            "wolf_kill": args.wolf_rollouts,
            "day_vote": args.vote_rollouts,
        },
    )
    write_datasets(rows, metadata)
    validation = validate_decision_rows(rows)
    counts = Counter(row["decision_type"] for row in rows)
    print("ML Stage 1 datasets generated")
    print(f"Candidate rows: {len(rows)}")
    print(f"Decision states: {validation['decision_count']}")
    print(f"Rows by decision type: {dict(counts)}")
    print(f"Validation passed: {validation['valid']}")
    print(f"Output directory: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
