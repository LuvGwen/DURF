import csv
from pathlib import Path

from ablation_experiment import run_ablation_experiment
from config import DEFAULT_RANDOM_SEED
from wolf_strategy_experiment import run_wolf_strategy_experiment


RESULTS_DIR = Path("results")


ABLATION_COLUMNS = [
    ("experiment", "Experiment"),
    ("total_games", "Total Games"),
    ("wolf_wins", "Wolf Wins"),
    ("village_wins", "Village Wins"),
    ("draws", "Draws"),
    ("wolf_win_pct", "Wolf Win %"),
    ("village_win_pct", "Village Win %"),
    ("draw_pct", "Draw %"),
    ("average_rounds", "Avg Rounds"),
    ("average_alive_players", "Avg Alive"),
    ("total_witch_saves", "Witch Saves"),
    ("total_witch_poison", "Witch Poison"),
    ("total_seer_checks", "Seer Checks"),
    ("total_hunter_shots", "Hunter Shots"),
    ("total_wolf_deceptions", "Wolf Deceptions"),
    ("total_accusation_pressure_costs", "Accusation Costs"),
    ("total_wrong_accusation_penalties", "Wrong Accusation Penalties"),
    ("total_self_defense_credibility_costs", "Self-Defense Costs"),
    ("total_deception_type_counts", "Deception Types"),
    ("total_wolf_kill_attempts", "Wolf Kills"),
    ("total_strategic_wolf_kills", "Strategic Wolf Kills"),
    ("average_herding_pressure", "Avg Herding"),
    (
        "average_trust_weighted_herding_pressure",
        "Avg Trust Weighted Herding",
    ),
    ("average_role_prior_score", "Avg Role Prior"),
    ("average_payoff", "Avg Payoff"),
    ("average_wolf_payoff", "Wolf Payoff"),
    ("average_village_payoff", "Village Payoff"),
]

WOLF_STRATEGY_COLUMNS = [
    ("strategy", "Strategy"),
    ("total_games", "Total Games"),
    ("wolf_wins", "Wolf Wins"),
    ("village_wins", "Village Wins"),
    ("draws", "Draws"),
    ("wolf_win_pct", "Wolf Win %"),
    ("village_win_pct", "Village Win %"),
    ("draw_pct", "Draw %"),
    ("average_rounds", "Avg Rounds"),
    ("average_alive_players", "Avg Alive"),
    ("total_wolf_kill_attempts", "Wolf Kills"),
    ("total_witch_saves", "Witch Saves"),
    ("total_witch_poison", "Witch Poison"),
    ("total_seer_checks", "Seer Checks"),
    ("total_hunter_shots", "Hunter Shots"),
    ("average_payoff", "Avg Payoff"),
    ("average_wolf_payoff", "Wolf Payoff"),
    ("average_village_payoff", "Village Payoff"),
]


def write_csv(path, rows, fieldnames):
    output_path = Path(path)
    output_path.parent.mkdir(exist_ok=True)

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                fieldname: row.get(fieldname, "")
                for fieldname in fieldnames
            })


def write_markdown_table(path, rows, columns, title):
    output_path = Path(path)
    output_path.parent.mkdir(exist_ok=True)

    lines = [f"# {title}", ""]
    lines.extend(markdown_table_lines(rows, columns))

    output_path.write_text("\n".join(lines) + "\n")


def markdown_table_lines(rows, columns):
    headers = [heading for _, heading in columns]
    keys = [key for key, _ in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for row in rows:
        values = [
            format_markdown_value(row.get(key, ""))
            for key in keys
        ]
        lines.append("| " + " | ".join(values) + " |")

    return lines


def format_markdown_value(value):
    if value is None:
        return ""

    return str(value).replace("|", "\\|")


def format_percent(value):
    return f"{value * 100:.2f}"


def format_float(value):
    if value is None:
        return None

    return f"{value:.2f}"


def build_common_row(summary):
    return {
        "total_games": summary["total_games"],
        "wolf_wins": summary["wolf_wins"],
        "village_wins": summary["village_wins"],
        "draws": summary["draws"],
        "wolf_win_pct": format_percent(summary["wolf_win_rate"]),
        "village_win_pct": format_percent(summary["village_win_rate"]),
        "draw_pct": format_percent(summary["draw_rate"]),
        "average_rounds": format_float(summary["average_rounds"]),
        "average_alive_players": format_float(summary["average_alive_players"]),
        "total_witch_saves": summary["total_witch_saves"],
        "total_witch_poison": summary["total_witch_poison"],
        "total_seer_checks": summary["total_seer_checks"],
        "total_hunter_shots": summary["total_hunter_shots"],
        "total_wolf_deceptions": summary["total_wolf_deceptions"],
        "total_accusation_pressure_costs": (
            summary["total_accusation_pressure_costs"]
        ),
        "total_wrong_accusation_penalties": (
            summary["total_wrong_accusation_penalties"]
        ),
        "total_self_defense_credibility_costs": (
            summary["total_self_defense_credibility_costs"]
        ),
        "total_deception_type_counts": (
            summary["total_deception_type_counts"]
        ),
        "total_wolf_kill_attempts": summary["total_wolf_kill_attempts"],
        "total_strategic_wolf_kills": (
            summary["total_strategic_wolf_kills"]
        ),
        "average_herding_pressure": format_float(
            summary["average_herding_pressure"]
        ),
        "average_trust_weighted_herding_pressure": format_float(
            summary.get(
                "average_trust_weighted_herding_pressure",
                summary.get("average_herding_pressure"),
            )
        ),
        "average_role_prior_score": format_float(
            summary["average_role_prior_score"]
        ),
        "average_payoff": format_float(summary["average_payoff"]),
        "average_wolf_payoff": format_float(summary["average_wolf_payoff"]),
        "average_village_payoff": format_float(
            summary["average_village_payoff"]
        ),
    }


def build_ablation_rows(experiment_results):
    rows = []

    for summary in experiment_results:
        row = build_common_row(summary)
        row["experiment"] = summary["name"]
        rows.append(row)

    return rows


def build_wolf_strategy_rows(experiment_results):
    rows = []

    for summary in experiment_results:
        row = build_common_row(summary)
        row["strategy"] = summary["wolf_kill_strategy"]
        rows.append(row)

    return rows


def write_combined_report(path, ablation_rows, wolf_strategy_rows):
    output_path = Path(path)
    output_path.parent.mkdir(exist_ok=True)

    lines = [
        "# DURF Werewolf Experiment Results",
        "",
        f"Random seed: {DEFAULT_RANDOM_SEED}",
        "",
        "## Ablation Experiment Results",
        "",
    ]
    lines.extend(markdown_table_lines(ablation_rows, ABLATION_COLUMNS))
    lines.extend([
        "",
        "## Wolf Strategy Experiment Results",
        "",
    ])
    lines.extend(markdown_table_lines(
        wolf_strategy_rows,
        WOLF_STRATEGY_COLUMNS,
    ))

    output_path.write_text("\n".join(lines) + "\n")


def export_results():
    RESULTS_DIR.mkdir(exist_ok=True)

    ablation_results = run_ablation_experiment(seed=DEFAULT_RANDOM_SEED)
    wolf_strategy_results = run_wolf_strategy_experiment(
        seed=DEFAULT_RANDOM_SEED,
    )

    ablation_rows = build_ablation_rows(ablation_results)
    wolf_strategy_rows = build_wolf_strategy_rows(wolf_strategy_results)

    ablation_csv = RESULTS_DIR / "ablation_results.csv"
    ablation_md = RESULTS_DIR / "ablation_results.md"
    wolf_strategy_csv = RESULTS_DIR / "wolf_strategy_results.csv"
    wolf_strategy_md = RESULTS_DIR / "wolf_strategy_results.md"
    combined_md = RESULTS_DIR / "experiment_results.md"

    write_csv(
        ablation_csv,
        ablation_rows,
        [key for key, _ in ABLATION_COLUMNS],
    )
    write_markdown_table(
        ablation_md,
        ablation_rows,
        ABLATION_COLUMNS,
        "Ablation Experiment Results",
    )

    write_csv(
        wolf_strategy_csv,
        wolf_strategy_rows,
        [key for key, _ in WOLF_STRATEGY_COLUMNS],
    )
    write_markdown_table(
        wolf_strategy_md,
        wolf_strategy_rows,
        WOLF_STRATEGY_COLUMNS,
        "Wolf Strategy Experiment Results",
    )
    write_combined_report(combined_md, ablation_rows, wolf_strategy_rows)

    return [
        ablation_csv,
        ablation_md,
        wolf_strategy_csv,
        wolf_strategy_md,
        combined_md,
    ]


if __name__ == "__main__":
    output_paths = export_results()

    print("Exported result files:")
    for output_path in output_paths:
        print(output_path)
