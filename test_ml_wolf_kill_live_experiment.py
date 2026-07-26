from pathlib import Path
from tempfile import TemporaryDirectory

from ml_wolf_kill_live_experiment import (
    get_stage2a_behavioral_regimes,
    run_wolf_kill_live_experiment,
)
from ml_wolf_kill_model_freeze import create_frozen_wolf_kill_model
from ml_wolf_kill_policy import PRIMARY_WOLF_KILL_POLICIES


def main():
    with TemporaryDirectory() as directory:
        directory = Path(directory)
        manifest_path = directory / "manifest.json"
        create_frozen_wolf_kill_model(
            output_path=manifest_path,
            created_at_utc="2026-07-26T00:00:00+00:00",
        )
        output = run_wolf_kill_live_experiment(
            directory,
            manifest_path=manifest_path,
            seeds=[100],
            base_configs_per_seed=1,
            policies=PRIMARY_WOLF_KILL_POLICIES,
            regimes=get_stage2a_behavioral_regimes()[:1],
            max_rounds=20,
        )
        assert len(output["game_rows"]) == len(PRIMARY_WOLF_KILL_POLICIES)
        assert output["matched_sets"] == 1
        assert len({
            row["matched_set_id"] for row in output["game_rows"]
        }) == 1
        assert set(row["policy_name"] for row in output["game_rows"]) == set(
            PRIMARY_WOLF_KILL_POLICIES
        )
        assert output["decision_rows"]
        assert output["prediction_rows"]
        assert (directory / "wolf_kill_live_game_level_raw.csv").exists()
        assert (directory / "wolf_kill_live_decision_raw.csv").exists()
        assert (directory / "wolf_kill_policy_predictions_raw.csv").exists()
        assert (directory / "wolf_kill_distribution_shift_raw.csv").exists()

    print("live_games_complete_normally: PASS")
    print("matched_configurations_present: PASS")
    print("game_level_logging_complete: PASS")
    print("policy_prediction_logging_complete: PASS")


if __name__ == "__main__":
    main()
