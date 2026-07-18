import csv
from pathlib import Path
from statistics import mean, stdev

from config import DEFAULT_MAX_ROUNDS
from simulation import run_simulation, summarize_results
from ten_player_experiment import (
    NUM_GAMES,
    get_ten_player_experiment_configs,
    total_credibility_cost_events,
    total_trust_updates,
)


SEEDS = [42, 43, 44, 45, 46]
RESULTS_DIR = Path("results")
RAW_CSV_PATH = RESULTS_DIR / "ten_player_multi_seed_raw_results.csv"
SUMMARY_MARKDOWN_PATH = RESULTS_DIR / "ten_player_multi_seed_summary.md"


RAW_FIELDNAMES = [
    "condition",
    "seed",
    "num_games",
    "wolf_wins",
    "village_wins",
    "draws",
    "wolf_win_rate",
    "village_win_rate",
    "average_rounds",
    "average_payoff",
    "average_wolf_payoff",
    "average_village_payoff",
    "total_wolf_deceptions",
    "total_credibility_cost_events",
    "total_trust_updates",
]


def run_ten_player_multi_seed_experiment(
    seeds=None,
    num_games=NUM_GAMES,
    configs=None,
):
    if seeds is None:
        seeds = SEEDS

    if configs is None:
        configs = get_ten_player_experiment_configs()

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
            rows.append({
                "condition": condition,
                "seed": seed,
                "num_games": summary["total_games"],
                "wolf_wins": summary["wolf_wins"],
                "village_wins": summary["village_wins"],
                "draws": summary["draws"],
                "wolf_win_rate": summary["wolf_win_rate"],
                "village_win_rate": summary["village_win_rate"],
                "average_rounds": summary["average_rounds"],
                "average_payoff": summary.get("average_payoff"),
                "average_wolf_payoff": summary.get("average_wolf_payoff"),
                "average_village_payoff": summary.get(
                    "average_village_payoff"
                ),
                "total_wolf_deceptions": summary.get(
                    "total_wolf_deceptions",
                    0,
                ),
                "total_credibility_cost_events": (
                    total_credibility_cost_events(summary)
                ),
                "total_trust_updates": total_trust_updates(summary),
            })

    return rows


def stdev_or_zero(values):
    if len(values) < 2:
        return 0.0

    return stdev(values)


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


def write_summary_markdown(path, summary_rows):
    with path.open("w") as file:
        file.write("# Ten-Player Multi-Seed Summary\n\n")
        file.write(
            "| condition | wolf_mean | wolf_min | wolf_max | "
            "wolf_stdev_pp | village_mean |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|\n")

        for row in summary_rows:
            file.write(
                f"| {row['condition']} | "
                f"{row['wolf_mean']:.2f} | "
                f"{row['wolf_min']:.2f} | "
                f"{row['wolf_max']:.2f} | "
                f"{row['wolf_stdev_pp']:.2f} | "
                f"{row['village_mean']:.2f} |\n"
            )


def export_multi_seed_results(raw_rows, summary_rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(RAW_CSV_PATH, raw_rows, RAW_FIELDNAMES)
    write_summary_markdown(SUMMARY_MARKDOWN_PATH, summary_rows)


def print_multi_seed_summary(summary_rows):
    print("Ten-player multi-seed summary")
    print("-----------------------------")

    for row in summary_rows:
        print(
            f"{row['condition']} | "
            f"Wolf mean: {row['wolf_mean']:.2f}% | "
            f"Wolf range: {row['wolf_min']:.2f}%"
            f"-{row['wolf_max']:.2f}% | "
            f"Wolf stdev: {row['wolf_stdev_pp']:.2f}pp | "
            f"Village mean: {row['village_mean']:.2f}%"
        )


if __name__ == "__main__":
    raw_result_rows = run_ten_player_multi_seed_experiment()
    summary_result_rows = summarize_multi_seed_rows(raw_result_rows)
    export_multi_seed_results(raw_result_rows, summary_result_rows)
    print_multi_seed_summary(summary_result_rows)
    print(f"\nWrote {RAW_CSV_PATH}")
    print(f"Wrote {SUMMARY_MARKDOWN_PATH}")
