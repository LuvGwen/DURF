import csv
from pathlib import Path
from statistics import mean, stdev

from config import DEFAULT_MAX_ROUNDS
from simulation import run_simulation, summarize_results
from ten_player_experiment import NUM_GAMES
from ten_player_risk_preference_experiment import (
    CSV_FIELDNAMES,
    get_risk_preference_experiment_configs,
    summarize_risk_preference_condition,
)


SEEDS = [42, 43, 44, 45, 46]
RESULTS_DIR = Path("results")
RAW_CSV_PATH = RESULTS_DIR / "ten_player_risk_preference_multi_seed_raw.csv"
SUMMARY_MARKDOWN_PATH = (
    RESULTS_DIR / "ten_player_risk_preference_multi_seed_summary.md"
)


RAW_FIELDNAMES = [
    "condition",
    "seed",
    "num_games",
] + [
    fieldname for fieldname in CSV_FIELDNAMES
    if fieldname != "condition"
]


def average_optional(values):
    numeric_values = [value for value in values if value is not None]

    if not numeric_values:
        return None

    return mean(numeric_values)


def stdev_or_zero(values):
    if len(values) < 2:
        return 0.0

    return stdev(values)


def run_risk_preference_multi_seed(
    seeds=None,
    num_games=NUM_GAMES,
    configs=None,
):
    if seeds is None:
        seeds = SEEDS

    if configs is None:
        configs = get_risk_preference_experiment_configs()

    rows = []

    for config in configs:
        condition = config["name"]
        simulation_kwargs = {
            key: value for key, value in config.items()
            if key != "name"
        }

        for seed in seeds:
            results = run_simulation(
                num_games=num_games,
                max_rounds=DEFAULT_MAX_ROUNDS,
                seed=seed,
                **simulation_kwargs,
            )
            summary = summarize_results(results)
            row = summarize_risk_preference_condition(condition, summary)
            row["seed"] = seed
            row["num_games"] = num_games
            rows.append(row)

    return rows


def summarize_multi_seed_rows(rows):
    condition_order = []
    rows_by_condition = {}

    for row in rows:
        condition = row["condition"]

        if condition not in rows_by_condition:
            condition_order.append(condition)
            rows_by_condition[condition] = []

        rows_by_condition[condition].append(row)

    summary_rows = []

    for condition in condition_order:
        condition_rows = rows_by_condition[condition]
        wolf_rates = [row["wolf_win_rate"] * 100 for row in condition_rows]
        village_rates = [
            row["village_win_rate"] * 100 for row in condition_rows
        ]

        summary_rows.append({
            "condition": condition,
            "wolf_mean": mean(wolf_rates),
            "wolf_min": min(wolf_rates),
            "wolf_max": max(wolf_rates),
            "wolf_stdev_pp": stdev_or_zero(wolf_rates),
            "village_mean": mean(village_rates),
            "avg_payoff": average_optional(
                row["avg_payoff"] for row in condition_rows
            ),
            "conservative_avg_payoff": average_optional(
                row["conservative_avg_payoff"] for row in condition_rows
            ),
            "neutral_avg_payoff": average_optional(
                row["neutral_avg_payoff"] for row in condition_rows
            ),
            "aggressive_avg_payoff": average_optional(
                row["aggressive_avg_payoff"] for row in condition_rows
            ),
        })

    return summary_rows


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


def format_optional(value):
    if value is None:
        return "NA"

    return f"{value:.2f}"


def write_summary_markdown(path, summary_rows):
    with path.open("w") as file:
        file.write("# Ten-Player Risk Preference Multi-Seed Summary\n\n")
        file.write(
            "| condition | wolf_mean | wolf_min | wolf_max | "
            "wolf_stdev_pp | village_mean | avg_payoff | "
            "conservative_avg_payoff | neutral_avg_payoff | "
            "aggressive_avg_payoff |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")

        for row in summary_rows:
            file.write(
                f"| {row['condition']} | "
                f"{row['wolf_mean']:.2f} | "
                f"{row['wolf_min']:.2f} | "
                f"{row['wolf_max']:.2f} | "
                f"{row['wolf_stdev_pp']:.2f} | "
                f"{row['village_mean']:.2f} | "
                f"{format_optional(row['avg_payoff'])} | "
                f"{format_optional(row['conservative_avg_payoff'])} | "
                f"{format_optional(row['neutral_avg_payoff'])} | "
                f"{format_optional(row['aggressive_avg_payoff'])} |\n"
            )


def export_multi_seed_results(raw_rows, summary_rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(RAW_CSV_PATH, raw_rows, RAW_FIELDNAMES)
    write_summary_markdown(SUMMARY_MARKDOWN_PATH, summary_rows)


def print_multi_seed_summary(summary_rows):
    print("Ten-player risk preference multi-seed summary")
    print("---------------------------------------------")

    for row in summary_rows:
        print(
            f"{row['condition']} | "
            f"Wolf mean: {row['wolf_mean']:.2f}% | "
            f"Wolf range: {row['wolf_min']:.2f}%"
            f"-{row['wolf_max']:.2f}% | "
            f"Wolf stdev: {row['wolf_stdev_pp']:.2f}pp | "
            f"Village mean: {row['village_mean']:.2f}% | "
            f"Avg payoff: {format_optional(row['avg_payoff'])}"
        )


if __name__ == "__main__":
    raw_result_rows = run_risk_preference_multi_seed()
    summary_result_rows = summarize_multi_seed_rows(raw_result_rows)
    export_multi_seed_results(raw_result_rows, summary_result_rows)
    print_multi_seed_summary(summary_result_rows)
    print(f"\nWrote {RAW_CSV_PATH}")
    print(f"Wrote {SUMMARY_MARKDOWN_PATH}")
