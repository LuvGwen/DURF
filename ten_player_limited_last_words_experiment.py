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
CSV_PATH = RESULTS_DIR / "ten_player_limited_last_words_results.csv"
MARKDOWN_PATH = RESULTS_DIR / "ten_player_limited_last_words_results.md"


BASE_CONDITION_OVERRIDES = {
    "speech": {
        "enable_speech": True,
    },
    "deception": {
        "enable_speech": True,
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
    },
    "credibility_cost": {
        "enable_speech": True,
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
    },
    "trust_memory": {
        "enable_speech": True,
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "trust_vote_weight": 0.20,
    },
}


CSV_FIELDNAMES = [
    "condition",
    "num_games",
    "wolf_win_rate",
    "village_win_rate",
    "average_rounds",
    "average_payoff",
    "total_last_words",
    "voted_out_last_words",
    "night1_kill_last_words",
    "wolf_last_words",
    "village_team_last_words",
    "correct_last_words_accusations",
    "wrong_last_words_accusations",
    "total_wolf_deceptions",
    "credibility_cost_events",
    "trust_updates",
]


MARKDOWN_COLUMNS = [
    "condition",
    "wolf_win_rate",
    "village_win_rate",
    "avg_rounds",
    "avg_payoff",
    "total_last_words",
    "voted_out_last_words",
    "night1_kill_last_words",
    "wolf_last_words",
    "village_team_last_words",
    "correct_last_words_accusations",
    "wrong_last_words_accusations",
    "total_wolf_deceptions",
    "credibility_cost_events",
    "trust_updates",
]


def get_limited_last_words_configs():
    configs = []

    for condition_name, overrides in BASE_CONDITION_OVERRIDES.items():
        base_config = dict(TEN_PLAYER_BASE_CONFIG)
        base_config.update(overrides)
        base_config["enable_last_words"] = False
        base_config["name"] = f"ten_player_{condition_name}"
        configs.append(base_config)

        last_words_config = dict(base_config)
        last_words_config["enable_last_words"] = True
        last_words_config["name"] = (
            f"ten_player_{condition_name}_limited_last_words"
        )
        configs.append(last_words_config)

    return configs


def summarize_last_words_condition(condition, summary):
    return {
        "condition": condition,
        "num_games": summary["total_games"],
        "wolf_win_rate": summary["wolf_win_rate"],
        "village_win_rate": summary["village_win_rate"],
        "average_rounds": summary["average_rounds"],
        "average_payoff": summary.get("average_payoff"),
        "total_last_words": summary.get("total_last_words", 0),
        "voted_out_last_words": summary.get(
            "total_voted_out_last_words",
            0,
        ),
        "night1_kill_last_words": summary.get(
            "total_night1_kill_last_words",
            0,
        ),
        "wolf_last_words": summary.get("total_wolf_last_words", 0),
        "village_team_last_words": summary.get(
            "total_village_team_last_words",
            0,
        ),
        "correct_last_words_accusations": summary.get(
            "total_correct_last_words_accusations",
            0,
        ),
        "wrong_last_words_accusations": summary.get(
            "total_wrong_last_words_accusations",
            0,
        ),
        "total_wolf_deceptions": summary.get("total_wolf_deceptions", 0),
        "credibility_cost_events": total_credibility_cost_events(summary),
        "trust_updates": total_trust_updates(summary),
    }


def run_limited_last_words_experiment(
    num_games=NUM_GAMES,
    seed=SEED,
    configs=None,
):
    if configs is None:
        configs = get_limited_last_words_configs()

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
        rows.append(summarize_last_words_condition(condition, summary))

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
        "wolf_win_rate": format_percent(row["wolf_win_rate"]),
        "village_win_rate": format_percent(row["village_win_rate"]),
        "avg_rounds": format_number(row["average_rounds"]),
        "avg_payoff": format_optional_float(row["average_payoff"]),
        "total_last_words": row["total_last_words"],
        "voted_out_last_words": row["voted_out_last_words"],
        "night1_kill_last_words": row["night1_kill_last_words"],
        "wolf_last_words": row["wolf_last_words"],
        "village_team_last_words": row["village_team_last_words"],
        "correct_last_words_accusations": (
            row["correct_last_words_accusations"]
        ),
        "wrong_last_words_accusations": (
            row["wrong_last_words_accusations"]
        ),
        "total_wolf_deceptions": row["total_wolf_deceptions"],
        "credibility_cost_events": row["credibility_cost_events"],
        "trust_updates": row["trust_updates"],
    }


def write_markdown(path, rows):
    with path.open("w") as file:
        file.write("# Ten-Player Limited Last Words Results\n\n")
        file.write(
            "| condition | wolf_win_rate | village_win_rate | avg_rounds | "
            "avg_payoff | total_last_words | voted_out_last_words | "
            "night1_kill_last_words | wolf_last_words | "
            "village_team_last_words | correct_last_words_accusations | "
            "wrong_last_words_accusations | total_wolf_deceptions | "
            "credibility_cost_events | trust_updates |\n"
        )
        file.write(
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
            "---:|---:|---:|---:|---:|\n"
        )

        for row in rows:
            formatted = format_markdown_row(row)
            file.write(
                "| "
                + " | ".join(str(formatted[column]) for column in MARKDOWN_COLUMNS)
                + " |\n"
            )


def export_limited_last_words_results(rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(CSV_PATH, rows, CSV_FIELDNAMES)
    write_markdown(MARKDOWN_PATH, rows)


def print_limited_last_words_results(rows):
    print("Ten-player limited last words experiment")
    print("----------------------------------------")

    for row in rows:
        print(
            f"{row['condition']} | "
            f"Wolf: {row['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {row['village_win_rate'] * 100:.2f}% | "
            f"Avg rounds: {row['average_rounds']:.2f} | "
            f"Last words: {row['total_last_words']} | "
            f"Voted-out: {row['voted_out_last_words']} | "
            f"Night 1 kill: {row['night1_kill_last_words']} | "
            f"Wolf last words: {row['wolf_last_words']} | "
            f"Village last words: {row['village_team_last_words']}"
        )


if __name__ == "__main__":
    result_rows = run_limited_last_words_experiment()
    export_limited_last_words_results(result_rows)
    print_limited_last_words_results(result_rows)
    print(f"\nWrote {CSV_PATH}")
    print(f"Wrote {MARKDOWN_PATH}")
