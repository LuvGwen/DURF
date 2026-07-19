import csv
from pathlib import Path

from config import DEFAULT_MAX_ROUNDS
from simulation import format_optional_float, run_simulation, summarize_results
from ten_player_experiment import (
    NUM_GAMES,
    SEED,
    TEN_PLAYER_BASE_CONFIG,
    format_percent,
    total_credibility_cost_events,
    total_trust_updates,
)


RESULTS_DIR = Path("results")
CSV_PATH = RESULTS_DIR / "ten_player_risk_preference_results.csv"
MARKDOWN_PATH = RESULTS_DIR / "ten_player_risk_preference_results.md"


DECEPTION_CONFIG = {
    "enable_speech": True,
    "enable_wolf_deception": True,
    "wolf_deception_strategy": "adaptive",
}

CREDIBILITY_COST_CONFIG = {
    **DECEPTION_CONFIG,
    "enable_deception_credibility": True,
}

TRUST_MEMORY_CONFIG = {
    **CREDIBILITY_COST_CONFIG,
    "enable_speaker_memory": True,
    "trust_vote_weight": 0.20,
}


RISK_PREFERENCE_EXPERIMENTS = [
    {
        "name": "ten_player_trust_memory",
        **TRUST_MEMORY_CONFIG,
    },
    {
        "name": "ten_player_trust_memory_risk_mixed",
        **TRUST_MEMORY_CONFIG,
        "enable_risk_preference": True,
        "risk_preference_mode": "mixed",
    },
    {
        "name": "ten_player_trust_memory_risk_conservative_majority",
        **TRUST_MEMORY_CONFIG,
        "enable_risk_preference": True,
        "risk_preference_mode": "conservative_majority",
    },
    {
        "name": "ten_player_trust_memory_risk_aggressive_majority",
        **TRUST_MEMORY_CONFIG,
        "enable_risk_preference": True,
        "risk_preference_mode": "aggressive_majority",
    },
    {
        "name": "ten_player_credibility_cost",
        **CREDIBILITY_COST_CONFIG,
    },
    {
        "name": "ten_player_credibility_cost_risk_mixed",
        **CREDIBILITY_COST_CONFIG,
        "enable_risk_preference": True,
        "risk_preference_mode": "mixed",
    },
    {
        "name": "ten_player_deception",
        **DECEPTION_CONFIG,
    },
    {
        "name": "ten_player_deception_risk_mixed",
        **DECEPTION_CONFIG,
        "enable_risk_preference": True,
        "risk_preference_mode": "mixed",
    },
]


CSV_FIELDNAMES = [
    "condition",
    "wolf_win_rate",
    "village_win_rate",
    "avg_rounds",
    "avg_payoff",
    "conservative_count",
    "neutral_count",
    "aggressive_count",
    "conservative_avg_payoff",
    "neutral_avg_payoff",
    "aggressive_avg_payoff",
    "total_votes",
    "aggressive_votes",
    "conservative_votes",
    "total_witch_poison",
    "aggressive_witch_poison",
    "conservative_witch_poison",
    "total_wolf_deceptions",
    "aggressive_wolf_deceptions",
    "conservative_wolf_deceptions",
    "credibility_cost_events",
    "trust_updates",
]


def get_risk_preference_experiment_configs():
    configs = []

    for experiment in RISK_PREFERENCE_EXPERIMENTS:
        config = dict(TEN_PLAYER_BASE_CONFIG)
        config.update(experiment)
        configs.append(config)

    return configs


def summarize_risk_preference_condition(condition, summary):
    return {
        "condition": condition,
        "wolf_win_rate": summary["wolf_win_rate"],
        "village_win_rate": summary["village_win_rate"],
        "avg_rounds": summary["average_rounds"],
        "avg_payoff": summary.get("average_payoff"),
        "conservative_count": summary.get("conservative_count", 0),
        "neutral_count": summary.get("neutral_count", 0),
        "aggressive_count": summary.get("aggressive_count", 0),
        "conservative_avg_payoff": summary.get("conservative_avg_payoff"),
        "neutral_avg_payoff": summary.get("neutral_avg_payoff"),
        "aggressive_avg_payoff": summary.get("aggressive_avg_payoff"),
        "total_votes": summary.get("total_votes", 0),
        "aggressive_votes": summary.get("aggressive_votes", 0),
        "conservative_votes": summary.get("conservative_votes", 0),
        "total_witch_poison": summary.get("total_witch_poison", 0),
        "aggressive_witch_poison": summary.get(
            "total_aggressive_witch_poison",
            0,
        ),
        "conservative_witch_poison": summary.get(
            "total_conservative_witch_poison",
            0,
        ),
        "total_wolf_deceptions": summary.get("total_wolf_deceptions", 0),
        "aggressive_wolf_deceptions": summary.get(
            "total_aggressive_wolf_deceptions",
            0,
        ),
        "conservative_wolf_deceptions": summary.get(
            "total_conservative_wolf_deceptions",
            0,
        ),
        "credibility_cost_events": total_credibility_cost_events(summary),
        "trust_updates": total_trust_updates(summary),
    }


def run_risk_preference_experiment(
    num_games=NUM_GAMES,
    seed=SEED,
    configs=None,
):
    if configs is None:
        configs = get_risk_preference_experiment_configs()

    rows = []

    for config in configs:
        condition = config["name"]
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
        rows.append(summarize_risk_preference_condition(condition, summary))

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


def write_markdown(path, rows):
    with path.open("w") as file:
        file.write("# Ten-Player Risk Preference Results\n\n")
        file.write(
            "| condition | wolf_win_rate | village_win_rate | avg_rounds | "
            "avg_payoff | conservative_count | neutral_count | "
            "aggressive_count | conservative_avg_payoff | "
            "neutral_avg_payoff | aggressive_avg_payoff | total_votes | "
            "aggressive_votes | conservative_votes | total_witch_poison | "
            "aggressive_witch_poison | conservative_witch_poison | "
            "total_wolf_deceptions | aggressive_wolf_deceptions | "
            "conservative_wolf_deceptions | credibility_cost_events | "
            "trust_updates |\n"
        )
        file.write(
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
            "---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )

        for row in rows:
            file.write(
                f"| {row['condition']} | "
                f"{format_percent(row['wolf_win_rate'])} | "
                f"{format_percent(row['village_win_rate'])} | "
                f"{row['avg_rounds']:.2f} | "
                f"{format_optional_float(row['avg_payoff'])} | "
                f"{row['conservative_count']} | "
                f"{row['neutral_count']} | "
                f"{row['aggressive_count']} | "
                f"{format_number(row['conservative_avg_payoff'])} | "
                f"{format_number(row['neutral_avg_payoff'])} | "
                f"{format_number(row['aggressive_avg_payoff'])} | "
                f"{row['total_votes']} | "
                f"{row['aggressive_votes']} | "
                f"{row['conservative_votes']} | "
                f"{row['total_witch_poison']} | "
                f"{row['aggressive_witch_poison']} | "
                f"{row['conservative_witch_poison']} | "
                f"{row['total_wolf_deceptions']} | "
                f"{row['aggressive_wolf_deceptions']} | "
                f"{row['conservative_wolf_deceptions']} | "
                f"{row['credibility_cost_events']} | "
                f"{row['trust_updates']} |\n"
            )


def export_risk_preference_results(rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(CSV_PATH, rows, CSV_FIELDNAMES)
    write_markdown(MARKDOWN_PATH, rows)


def print_risk_preference_results(rows):
    print("Ten-player risk preference experiment")
    print("-------------------------------------")

    for row in rows:
        print(
            f"{row['condition']} | "
            f"Wolf: {row['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {row['village_win_rate'] * 100:.2f}% | "
            f"Avg payoff: {format_optional_float(row['avg_payoff'])} | "
            f"Risk counts C/N/A: "
            f"{row['conservative_count']}/"
            f"{row['neutral_count']}/"
            f"{row['aggressive_count']} | "
            f"Wolf deceptions: {row['total_wolf_deceptions']}"
        )


if __name__ == "__main__":
    result_rows = run_risk_preference_experiment()
    export_risk_preference_results(result_rows)
    print_risk_preference_results(result_rows)
    print(f"\nWrote {CSV_PATH}")
    print(f"Wrote {MARKDOWN_PATH}")
