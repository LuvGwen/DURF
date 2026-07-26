from pathlib import Path
from tempfile import TemporaryDirectory

from ml_feature_registry import PROHIBITED_FEATURES
from ml_wolf_kill_live_experiment import (
    build_game_for_policy,
    get_stage2a_behavioral_regimes,
)
from ml_wolf_kill_model_freeze import (
    PROHIBITED_LIVE_FEATURE_TOKENS,
    create_frozen_wolf_kill_model,
    live_feature_columns,
    validate_live_feature_safety,
)
from ml_wolf_kill_policy import choose_stage2a_wolf_kill_target


def main():
    features = live_feature_columns()
    validate_live_feature_safety(features)
    assert not (set(features) & set(PROHIBITED_FEATURES))
    for feature in features:
        assert not any(
            token in feature for token in PROHIBITED_LIVE_FEATURE_TOKENS
        )

    with TemporaryDirectory() as directory:
        manifest_path = Path(directory) / "manifest.json"
        manifest = create_frozen_wolf_kill_model(
            output_path=manifest_path,
            created_at_utc="2026-07-26T00:00:00+00:00",
        )
        regime = get_stage2a_behavioral_regimes()[0]
        game, _ = build_game_for_policy(
            100,
            1,
            regime,
            "frozen_ml",
            manifest,
        )
        target, event = choose_stage2a_wolf_kill_target(
            game,
            policy_name="frozen_ml",
            manifest_path=manifest_path,
            manifest=manifest,
        )
        assert target is not None
        for candidate in event["candidate_rows"]:
            assert "feature_row" not in candidate
            assert "true_candidate_role_label" not in candidate
            assert "full_rollout_mean_team_win_rate" not in candidate

    print("live_feature_safety: PASS")
    print("no_true_role_or_rollout_live_features: PASS")
    print("logged_candidate_rows_exclude_feature_matrix: PASS")


if __name__ == "__main__":
    main()
