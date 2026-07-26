from pathlib import Path

from ml_train_baselines import read_csv_rows
from ml_wolf_kill_analysis import failure_cases, write_csv


DEFAULT_OUTPUT_DIR = Path("results") / "ml_optimization_stage2a"


def run_policy_failure_analysis(output_dir=DEFAULT_OUTPUT_DIR):
    output_dir = Path(output_dir)
    game_rows = read_csv_rows(output_dir / "wolf_kill_live_game_level_raw.csv")
    decision_rows = read_csv_rows(output_dir / "wolf_kill_live_decision_raw.csv")
    rows = failure_cases(game_rows, decision_rows)
    fieldnames = sorted({key for row in rows for key in row}) if rows else [
        "matched_set_id",
        "policy_name",
        "failure_reason",
    ]
    write_csv(
        output_dir / "wolf_kill_policy_failure_cases.csv",
        rows,
        fieldnames,
    )
    return rows


if __name__ == "__main__":
    rows = run_policy_failure_analysis()
    print("Wolf-kill policy failure cases:", len(rows))
