import csv
from pathlib import Path
from statistics import mean, stdev

from ten_player_experiment import NUM_GAMES
from ten_player_seer_position_randomized_roles_experiment import (
    CSV_FIELDNAMES,
    get_randomized_role_seer_position_configs,
    run_randomized_role_seer_position_experiment,
)


SEEDS = [42, 43, 44, 45, 46]
RESULTS_DIR = Path("results")
RAW_CSV_PATH = (
    RESULTS_DIR / "ten_player_seer_position_randomized_roles_multi_seed_raw.csv"
)
SUMMARY_MARKDOWN_PATH = (
    RESULTS_DIR
    / "ten_player_seer_position_randomized_roles_multi_seed_summary.md"
)

RAW_FIELDNAMES = [
    "condition",
    "seed",
    "num_games",
] + [
    fieldname for fieldname in CSV_FIELDNAMES
    if fieldname not in {"condition", "num_games"}
]


def stdev_or_zero(values):
    if len(values) < 2:
        return 0.0

    return stdev(values)


def run_randomized_role_seer_position_multi_seed(
    seeds=None,
    num_games=NUM_GAMES,
    configs=None,
):
    if seeds is None:
        seeds = SEEDS

    if configs is None:
        configs = get_randomized_role_seer_position_configs()

    rows = []

    for seed in seeds:
        seed_rows = run_randomized_role_seer_position_experiment(
            num_games=num_games,
            seed=seed,
            configs=configs,
        )

        for row in seed_rows:
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
        seer_found_wolf_rates = [
            row["seer_found_wolf_rate"] * 100 for row in condition_rows
        ]
        first_check_found_wolf_rates = [
            row["first_check_found_wolf_rate"] * 100
            for row in condition_rows
        ]
        edge_check_rates = [
            row["edge_check_rate"] * 100 for row in condition_rows
        ]
        edge_has_wolf_rates = [
            row["edge_has_wolf_rate"] * 100 for row in condition_rows
        ]
        avg_wolves_on_edge_values = [
            row["avg_wolves_on_edge"] for row in condition_rows
        ]
        seer_on_edge_rates = [
            row["seer_on_edge_rate"] * 100 for row in condition_rows
        ]
        seer_left_side_rates = [
            row["seer_left_side_rate"] * 100 for row in condition_rows
        ]

        summary_rows.append({
            "condition": condition,
            "wolf_mean": mean(wolf_rates),
            "wolf_min": min(wolf_rates),
            "wolf_max": max(wolf_rates),
            "wolf_stdev_pp": stdev_or_zero(wolf_rates),
            "village_mean": mean(village_rates),
            "seer_found_wolf_rate_mean": mean(seer_found_wolf_rates),
            "first_check_found_wolf_rate_mean": mean(
                first_check_found_wolf_rates
            ),
            "edge_check_rate_mean": mean(edge_check_rates),
            "edge_has_wolf_rate_mean": mean(edge_has_wolf_rates),
            "avg_wolves_on_edge_mean": mean(avg_wolves_on_edge_values),
            "seer_on_edge_rate_mean": mean(seer_on_edge_rates),
            "seer_left_side_rate_mean": mean(seer_left_side_rates),
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
        file.write(
            "# Ten-Player Seer Position Randomized Roles "
            "Multi-Seed Summary\n\n"
        )
        file.write(
            "| condition | wolf_mean | wolf_min | wolf_max | "
            "wolf_stdev_pp | village_mean | "
            "seer_found_wolf_rate_mean | "
            "first_check_found_wolf_rate_mean | "
            "edge_check_rate_mean | edge_has_wolf_rate_mean | "
            "avg_wolves_on_edge_mean | seer_on_edge_rate_mean | "
            "seer_left_side_rate_mean |\n"
        )
        file.write(
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
            "---:|---:|---:|---:|\n"
        )

        for row in summary_rows:
            file.write(
                f"| {row['condition']} | "
                f"{row['wolf_mean']:.2f} | "
                f"{row['wolf_min']:.2f} | "
                f"{row['wolf_max']:.2f} | "
                f"{row['wolf_stdev_pp']:.2f} | "
                f"{row['village_mean']:.2f} | "
                f"{row['seer_found_wolf_rate_mean']:.2f} | "
                f"{row['first_check_found_wolf_rate_mean']:.2f} | "
                f"{row['edge_check_rate_mean']:.2f} | "
                f"{row['edge_has_wolf_rate_mean']:.2f} | "
                f"{row['avg_wolves_on_edge_mean']:.2f} | "
                f"{row['seer_on_edge_rate_mean']:.2f} | "
                f"{row['seer_left_side_rate_mean']:.2f} |\n"
            )


def export_multi_seed_results(raw_rows, summary_rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(RAW_CSV_PATH, raw_rows, RAW_FIELDNAMES)
    write_summary_markdown(SUMMARY_MARKDOWN_PATH, summary_rows)


def print_multi_seed_summary(summary_rows):
    print("Ten-player seer position randomized roles multi-seed summary")
    print("------------------------------------------------------------")

    for row in summary_rows:
        print(
            f"{row['condition']} | "
            f"Wolf mean: {row['wolf_mean']:.2f}% | "
            f"Wolf range: {row['wolf_min']:.2f}%"
            f"-{row['wolf_max']:.2f}% | "
            f"Wolf stdev: {row['wolf_stdev_pp']:.2f}pp | "
            f"Village mean: {row['village_mean']:.2f}% | "
            f"Seer found wolf: "
            f"{row['seer_found_wolf_rate_mean']:.2f}% | "
            f"First check wolf: "
            f"{row['first_check_found_wolf_rate_mean']:.2f}% | "
            f"Edge has wolf: "
            f"{row['edge_has_wolf_rate_mean']:.2f}%"
        )


if __name__ == "__main__":
    raw_result_rows = run_randomized_role_seer_position_multi_seed()
    summary_result_rows = summarize_multi_seed_rows(raw_result_rows)
    export_multi_seed_results(raw_result_rows, summary_result_rows)
    print_multi_seed_summary(summary_result_rows)
    print(f"\nWrote {RAW_CSV_PATH}")
    print(f"Wrote {SUMMARY_MARKDOWN_PATH}")
