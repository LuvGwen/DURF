from pathlib import Path
from tempfile import TemporaryDirectory

from game import Game, create_default_players
from ml_wolf_kill_live_experiment import (
    build_game_for_policy,
    get_stage2a_behavioral_regimes,
)
from ml_wolf_kill_model_freeze import create_frozen_wolf_kill_model
from ml_wolf_kill_policy import (
    build_live_wolf_kill_candidate_rows,
    choose_stage2a_wolf_kill_target,
    select_policy_row,
)


def create_test_manifest(path):
    return create_frozen_wolf_kill_model(
        output_path=path,
        created_at_utc="2026-07-26T00:00:00+00:00",
    )


def assert_hybrid_scores(rows):
    for row in rows:
        expected = (
            0.5 * row["normalized_ml_value"]
            + 0.5 * row["normalized_existing_rule_score"]
        )
        assert abs(row["hybrid_score"] - expected) < 1e-12


def main():
    with TemporaryDirectory() as directory:
        manifest_path = Path(directory) / "manifest.json"
        manifest = create_test_manifest(manifest_path)
        regime = get_stage2a_behavioral_regimes()[0]

        game_one, _ = build_game_for_policy(
            100,
            1,
            regime,
            "frozen_ml",
            manifest,
        )
        target_one, event_one = choose_stage2a_wolf_kill_target(
            game_one,
            policy_name="frozen_ml",
            manifest_path=manifest_path,
            manifest=manifest,
        )
        assert target_one is not None
        assert target_one.alive
        assert not target_one.is_wolf()
        assert event_one["policy_name"] == "frozen_ml"
        assert event_one["manifest_hash"] == manifest["manifest_hash"]

        game_two, _ = build_game_for_policy(
            100,
            1,
            regime,
            "frozen_ml",
            manifest,
        )
        target_two, event_two = choose_stage2a_wolf_kill_target(
            game_two,
            policy_name="frozen_ml",
            manifest_path=manifest_path,
            manifest=manifest,
        )
        assert target_one.player_id == target_two.player_id
        assert event_one["frozen_ml_target"] == event_two["frozen_ml_target"]

        rows = build_live_wolf_kill_candidate_rows(
            game_one,
            manifest,
            game_id="policy_test",
        )
        assert rows
        assert_hybrid_scores(rows)
        epsilon_one, detail_one = select_policy_row(
            game_one,
            rows,
            "frozen_ml_epsilon_010",
            epsilon=0.10,
        )
        epsilon_two, detail_two = select_policy_row(
            game_one,
            rows,
            "frozen_ml_epsilon_010",
            epsilon=0.10,
        )
        assert epsilon_one["candidate_uid"] == epsilon_two["candidate_uid"]
        assert detail_one["epsilon_seed"] == detail_two["epsilon_seed"]

        default_game = Game(create_default_players())
        default_game.run_one_round()
        assert not any(
            event["event_type"] == "wolf_kill_policy_decision"
            for event in default_game.event_log
        )

        ml_game, _ = build_game_for_policy(
            101,
            1,
            regime,
            "frozen_ml",
            manifest,
        )
        ml_game.ml_wolf_kill_model_manifest_path = str(manifest_path)
        ml_game.run_one_round()
        assert any(
            event["event_type"] == "wolf_kill_policy_decision"
            for event in ml_game.event_log
        )

        for candidate in event_one["candidate_rows"]:
            assert "feature_row" not in candidate

    print("legal_wolf_kill_target: PASS")
    print("pure_ml_target_deterministic: PASS")
    print("epsilon_policy_reproducible: PASS")
    print("hybrid_score_calculation: PASS")
    print("default_strategy_unchanged: PASS")
    print("explicit_ml_flag_activates_policy: PASS")


if __name__ == "__main__":
    main()
