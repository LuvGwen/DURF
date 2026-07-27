from pathlib import Path
from tempfile import TemporaryDirectory

from ml_stage2b_live_experiment import (
    get_stage2a_behavioral_regimes,
    run_stage2b_live_experiment,
)


def main():
    with TemporaryDirectory() as directory:
        output = run_stage2b_live_experiment(
            output_dir=Path(directory),
            seeds=[220],
            split="unit",
            base_configs_per_seed=1,
            policies=["existing_rule", "continuous_frozen_ml"],
            regimes=get_stage2a_behavioral_regimes()[:1],
            max_rounds=20,
            write_outputs=True,
        )
        assert len(output["game_rows"]) == 2
        assert output["matched_sets"] == 1
        assert output["decision_rows"]
        assert output["prediction_rows"]
        assert (Path(directory) / "stage2b_live_game_level_raw.csv").exists()
        assert (Path(directory) / "stage2b_live_decision_raw.csv").exists()

    print("stage2b_live_games_complete: PASS")
    print("stage2b_live_logging_complete: PASS")


if __name__ == "__main__":
    main()
