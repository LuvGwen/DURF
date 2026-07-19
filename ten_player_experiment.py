import csv
from pathlib import Path

from config import (
    DEFAULT_HERDING_ALPHA,
    DEFAULT_HERDING_BETA,
    DEFAULT_HERDING_GAMMA,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_WITCH_POISON_THRESHOLD,
    TEN_PLAYER_CREDIBILITY_COST_SCALE,
    TEN_PLAYER_HERDING_WEIGHT_SCALE,
    TEN_PLAYER_INITIAL_P_WOLF,
    TEN_PLAYER_ROLE_SETUP,
    TEN_PLAYER_SPEECH_SIGNAL_SCALE,
)
from simulation import format_optional_float, run_simulation, summarize_results


NUM_GAMES = 500
SEED = 42
RESULTS_DIR = Path("results")
CSV_PATH = RESULTS_DIR / "ten_player_experiment_results.csv"
MARKDOWN_PATH = RESULTS_DIR / "ten_player_experiment_results.md"


TEN_PLAYER_BASE_CONFIG = {
    "role_setup": TEN_PLAYER_ROLE_SETUP,
    "initial_p_wolf": TEN_PLAYER_INITIAL_P_WOLF,
    "speech_signal_scale": TEN_PLAYER_SPEECH_SIGNAL_SCALE,
    "credibility_cost_scale": TEN_PLAYER_CREDIBILITY_COST_SCALE,
    "herding_alpha": DEFAULT_HERDING_ALPHA * TEN_PLAYER_HERDING_WEIGHT_SCALE,
    "herding_beta": DEFAULT_HERDING_BETA * TEN_PLAYER_HERDING_WEIGHT_SCALE,
    "herding_gamma": DEFAULT_HERDING_GAMMA * TEN_PLAYER_HERDING_WEIGHT_SCALE,
    "use_suspicion_voting": True,
    "enable_suspicion_update": True,
    "enable_seer": True,
    "enable_witch": True,
    "enable_hunter": True,
    "enable_speech": False,
    "enable_herding": False,
    "enable_role_prior": False,
    "enable_wolf_strategy": False,
    "enable_wolf_deception": False,
    "enable_deception_credibility": False,
    "enable_speaker_memory": False,
    "enable_trust_weighted_speech": False,
    "enable_trust_weighted_herding": False,
    "witch_poison_threshold": DEFAULT_WITCH_POISON_THRESHOLD,
}


TEN_PLAYER_EXPERIMENTS = [
    {
        "name": "ten_player_baseline",
    },
    {
        "name": "ten_player_speech",
        "enable_speech": True,
    },
    {
        "name": "ten_player_deception",
        "enable_speech": True,
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
    },
    {
        "name": "ten_player_credibility_cost",
        "enable_speech": True,
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
    },
    {
        "name": "ten_player_trust_memory",
        "enable_speech": True,
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "trust_vote_weight": 0.20,
    },
    {
        "name": "ten_player_trust_weighted_herding",
        "enable_speech": True,
        "enable_herding": True,
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "trust_vote_weight": 0.20,
        "enable_trust_weighted_herding": True,
    },
]


CSV_FIELDNAMES = [
    "condition",
    "num_games",
    "wolf_wins",
    "village_wins",
    "draws",
    "wolf_win_rate",
    "village_win_rate",
    "average_rounds",
    "average_alive_players",
    "average_payoff",
    "average_wolf_payoff",
    "average_village_payoff",
    "total_wolf_deceptions",
    "average_wolf_deceptions_per_game",
    "total_credibility_cost_events",
    "total_trust_updates",
    "average_speaker_trust",
    "average_herding_pressure",
]


MARKDOWN_COLUMNS = [
    "condition",
    "wolf_win_rate",
    "village_win_rate",
    "avg_rounds",
    "avg_payoff",
    "wolf_deceptions",
    "credibility_cost_events",
    "trust_updates",
]


def get_ten_player_experiment_configs():
    configs = []

    for experiment in TEN_PLAYER_EXPERIMENTS:
        config = dict(TEN_PLAYER_BASE_CONFIG)
        config.update(experiment)
        configs.append(config)

    return configs


def safe_summary_value(summary, key, default=0):
    value = summary.get(key, default)

    if value is None:
        return "NA"

    return value


def total_credibility_cost_events(summary):
    return (
        summary.get("total_accusation_pressure_costs", 0)
        + summary.get("total_wrong_accusation_penalties", 0)
        + summary.get("total_self_defense_credibility_costs", 0)
    )


def total_trust_updates(summary):
    return (
        summary.get("total_speaker_trust_updates", 0)
        + summary.get("total_vote_outcome_trust_updates", 0)
    )


def summarize_condition(condition, summary):
    return {
        "condition": condition,
        "num_games": summary["total_games"],
        "wolf_wins": summary["wolf_wins"],
        "village_wins": summary["village_wins"],
        "draws": summary["draws"],
        "wolf_win_rate": summary["wolf_win_rate"],
        "village_win_rate": summary["village_win_rate"],
        "average_rounds": summary["average_rounds"],
        "average_alive_players": summary["average_alive_players"],
        "average_payoff": safe_summary_value(summary, "average_payoff", "NA"),
        "average_wolf_payoff": safe_summary_value(
            summary,
            "average_wolf_payoff",
            "NA",
        ),
        "average_village_payoff": safe_summary_value(
            summary,
            "average_village_payoff",
            "NA",
        ),
        "total_wolf_deceptions": summary.get("total_wolf_deceptions", 0),
        "average_wolf_deceptions_per_game": summary.get(
            "average_wolf_deceptions_per_game",
            0,
        ),
        "total_credibility_cost_events": (
            total_credibility_cost_events(summary)
        ),
        "total_trust_updates": total_trust_updates(summary),
        "average_speaker_trust": summary.get("average_speaker_trust", 0),
        "average_herding_pressure": summary.get(
            "average_herding_pressure",
            0,
        ),
    }


def run_ten_player_experiment(
    num_games=NUM_GAMES,
    seed=SEED,
    configs=None,
):
    if configs is None:
        configs = get_ten_player_experiment_configs()

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
        rows.append(summarize_condition(condition, summary))

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


def format_percent(rate):
    return f"{rate * 100:.2f}%"


def format_number(value):
    if value == "NA":
        return "NA"

    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


def markdown_row(row):
    return {
        "condition": row["condition"],
        "wolf_win_rate": format_percent(row["wolf_win_rate"]),
        "village_win_rate": format_percent(row["village_win_rate"]),
        "avg_rounds": format_number(row["average_rounds"]),
        "avg_payoff": format_optional_float(row["average_payoff"]),
        "wolf_deceptions": row["total_wolf_deceptions"],
        "credibility_cost_events": row["total_credibility_cost_events"],
        "trust_updates": row["total_trust_updates"],
    }


def write_markdown(path, rows):
    with path.open("w") as file:
        file.write("# Ten-Player Experiment Results\n\n")
        file.write(
            "| condition | wolf_win_rate | village_win_rate | "
            "avg_rounds | avg_payoff | wolf_deceptions | "
            "credibility_cost_events | trust_updates |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")

        for row in rows:
            formatted = markdown_row(row)
            file.write(
                "| "
                + " | ".join(str(formatted[column]) for column in MARKDOWN_COLUMNS)
                + " |\n"
            )


def export_ten_player_results(rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(CSV_PATH, rows, CSV_FIELDNAMES)
    write_markdown(MARKDOWN_PATH, rows)


def print_ten_player_results(rows):
    print("Ten-player experiment")
    print("---------------------")

    for row in rows:
        print(
            f"{row['condition']} | "
            f"Wolf: {row['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {row['village_win_rate'] * 100:.2f}% | "
            f"Avg rounds: {row['average_rounds']:.2f} | "
            f"Avg payoff: {format_optional_float(row['average_payoff'])} | "
            f"Wolf deceptions: {row['total_wolf_deceptions']} | "
            f"Credibility costs: "
            f"{row['total_credibility_cost_events']} | "
            f"Trust updates: {row['total_trust_updates']}"
        )


if __name__ == "__main__":
    result_rows = run_ten_player_experiment()
    export_ten_player_results(result_rows)
    print_ten_player_results(result_rows)
    print(f"\nWrote {CSV_PATH}")
    print(f"Wrote {MARKDOWN_PATH}")
