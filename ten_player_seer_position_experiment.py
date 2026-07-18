import csv
from pathlib import Path

from config import DEFAULT_MAX_ROUNDS
from simulation import format_optional_float, run_simulation, summarize_results
from ten_player_experiment import (
    NUM_GAMES,
    SEED,
    TEN_PLAYER_BASE_CONFIG,
    format_percent,
)


RESULTS_DIR = Path("results")
CSV_PATH = RESULTS_DIR / "ten_player_seer_position_results.csv"
MARKDOWN_PATH = RESULTS_DIR / "ten_player_seer_position_results.md"

SEER_POSITION_STRATEGIES = [
    ("seer_default", "default"),
    ("seer_random", "random"),
    ("seer_edge_first", "edge_first"),
    ("seer_inner_first", "inner_first"),
    ("seer_highest_p_wolf", "highest_p_wolf"),
    ("seer_highest_suspicion", "highest_suspicion"),
    ("seer_opposite_side", "opposite_side"),
]

SEER_POSITION_BASE_CONFIG = {
    **TEN_PLAYER_BASE_CONFIG,
    "enable_speech": True,
    "enable_deception_credibility": True,
    "enable_speaker_memory": True,
    "trust_vote_weight": 0.20,
    "enable_last_words": False,
    "enable_risk_preference": False,
    "enable_position_model": True,
}

CSV_FIELDNAMES = [
    "condition",
    "seer_check_strategy",
    "num_games",
    "wolf_win_rate",
    "village_win_rate",
    "avg_rounds",
    "avg_payoff",
    "total_seer_checks",
    "seer_found_wolves",
    "seer_found_wolf_rate",
    "edge_checks",
    "inner_checks",
    "edge_check_rate",
    "edge_wolf_checks",
    "inner_wolf_checks",
    "opposite_side_checks",
    "same_side_checks",
    "avg_checks_per_game",
    "seer_survival_rate",
    "first_check_edge_rate",
    "first_check_found_wolf_rate",
]

MARKDOWN_COLUMNS = [
    "condition",
    "seer_check_strategy",
    "wolf_win_rate",
    "village_win_rate",
    "avg_rounds",
    "avg_payoff",
    "total_seer_checks",
    "seer_found_wolves",
    "seer_found_wolf_rate",
    "edge_checks",
    "inner_checks",
    "edge_wolf_checks",
    "inner_wolf_checks",
    "opposite_side_checks",
    "same_side_checks",
    "avg_checks_per_game",
    "seer_survival_rate",
    "first_check_edge_rate",
    "first_check_found_wolf_rate",
]


def get_seer_position_configs():
    configs = []

    for condition, strategy in SEER_POSITION_STRATEGIES:
        config = dict(SEER_POSITION_BASE_CONFIG)
        config["name"] = condition
        config["seer_check_strategy"] = strategy
        configs.append(config)

    return configs


def summarize_seer_position_condition(condition, strategy, summary):
    return {
        "condition": condition,
        "seer_check_strategy": strategy,
        "num_games": summary["total_games"],
        "wolf_win_rate": summary["wolf_win_rate"],
        "village_win_rate": summary["village_win_rate"],
        "avg_rounds": summary["average_rounds"],
        "avg_payoff": summary.get("average_payoff"),
        "total_seer_checks": summary.get("total_seer_checks", 0),
        "seer_found_wolves": summary.get("total_seer_found_wolves", 0),
        "seer_found_wolf_rate": summary.get("seer_found_wolf_rate", 0.0),
        "edge_checks": summary.get("total_edge_seer_checks", 0),
        "inner_checks": summary.get("total_inner_seer_checks", 0),
        "edge_check_rate": summary.get("edge_check_rate", 0.0),
        "edge_wolf_checks": summary.get("total_edge_wolf_seer_checks", 0),
        "inner_wolf_checks": summary.get("total_inner_wolf_seer_checks", 0),
        "opposite_side_checks": summary.get(
            "total_opposite_side_seer_checks",
            0,
        ),
        "same_side_checks": summary.get("total_same_side_seer_checks", 0),
        "avg_checks_per_game": summary.get(
            "average_seer_checks_per_game",
            0.0,
        ),
        "seer_survival_rate": summary.get("seer_survival_rate", 0.0),
        "first_check_edge_rate": summary.get("first_check_edge_rate", 0.0),
        "first_check_found_wolf_rate": summary.get(
            "first_check_found_wolf_rate",
            0.0,
        ),
    }


def run_seer_position_experiment(
    num_games=NUM_GAMES,
    seed=SEED,
    configs=None,
):
    if configs is None:
        configs = get_seer_position_configs()

    rows = []

    for config in configs:
        condition = config["name"]
        strategy = config["seer_check_strategy"]
        simulation_kwargs = {
            key: value for key, value in config.items()
            if key != "name"
        }
        results = run_simulation(
            num_games=num_games,
            max_rounds=DEFAULT_MAX_ROUNDS,
            seed=seed,
            **simulation_kwargs,
        )
        summary = summarize_results(results)
        rows.append(
            summarize_seer_position_condition(condition, strategy, summary)
        )

    return rows


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            restval="",
        )
        writer.writeheader()
        writer.writerows(rows)


def format_number(value):
    if value is None:
        return "NA"

    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


def format_markdown_row(row):
    return {
        "condition": row["condition"],
        "seer_check_strategy": row["seer_check_strategy"],
        "wolf_win_rate": format_percent(row["wolf_win_rate"]),
        "village_win_rate": format_percent(row["village_win_rate"]),
        "avg_rounds": format_number(row["avg_rounds"]),
        "avg_payoff": format_optional_float(row["avg_payoff"]),
        "total_seer_checks": row["total_seer_checks"],
        "seer_found_wolves": row["seer_found_wolves"],
        "seer_found_wolf_rate": format_percent(row["seer_found_wolf_rate"]),
        "edge_checks": row["edge_checks"],
        "inner_checks": row["inner_checks"],
        "edge_wolf_checks": row["edge_wolf_checks"],
        "inner_wolf_checks": row["inner_wolf_checks"],
        "opposite_side_checks": row["opposite_side_checks"],
        "same_side_checks": row["same_side_checks"],
        "avg_checks_per_game": format_number(row["avg_checks_per_game"]),
        "seer_survival_rate": format_percent(row["seer_survival_rate"]),
        "first_check_edge_rate": format_percent(row["first_check_edge_rate"]),
        "first_check_found_wolf_rate": format_percent(
            row["first_check_found_wolf_rate"]
        ),
    }


def write_markdown(path, rows):
    with path.open("w") as file:
        file.write("# Ten-Player Seer Position Results\n\n")
        file.write(
            "| condition | seer_check_strategy | wolf_win_rate | "
            "village_win_rate | avg_rounds | avg_payoff | "
            "total_seer_checks | seer_found_wolves | "
            "seer_found_wolf_rate | edge_checks | inner_checks | "
            "edge_wolf_checks | inner_wolf_checks | opposite_side_checks | "
            "same_side_checks | avg_checks_per_game | seer_survival_rate | "
            "first_check_edge_rate | first_check_found_wolf_rate |\n"
        )
        file.write(
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"
            "---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )

        for row in rows:
            formatted = format_markdown_row(row)
            file.write(
                "| "
                + " | ".join(str(formatted[column]) for column in MARKDOWN_COLUMNS)
                + " |\n"
            )


def export_seer_position_results(rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(CSV_PATH, rows, CSV_FIELDNAMES)
    write_markdown(MARKDOWN_PATH, rows)


def print_seer_position_results(rows):
    print("Ten-player seer position experiment")
    print("-----------------------------------")

    for row in rows:
        print(
            f"{row['condition']} | "
            f"Strategy: {row['seer_check_strategy']} | "
            f"Wolf: {row['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {row['village_win_rate'] * 100:.2f}% | "
            f"Seer found wolf: "
            f"{row['seer_found_wolf_rate'] * 100:.2f}% | "
            f"First check wolf: "
            f"{row['first_check_found_wolf_rate'] * 100:.2f}% | "
            f"Edge checks: {row['edge_checks']} | "
            f"Inner checks: {row['inner_checks']}"
        )


if __name__ == "__main__":
    result_rows = run_seer_position_experiment()
    export_seer_position_results(result_rows)
    print_seer_position_results(result_rows)
    print(f"\nWrote {CSV_PATH}")
    print(f"Wrote {MARKDOWN_PATH}")
