from game_level_logging import GAME_LEVEL_FIELDNAMES, validate_game_level_rows
from ten_player_seer_position_randomized_roles_experiment import (
    get_randomized_role_seer_position_configs,
    run_randomized_role_seer_position_experiment_with_game_level,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"PASS: {message}")


def test_game_level_logging_rows():
    configs = get_randomized_role_seer_position_configs()[:2]
    _, game_level_rows = (
        run_randomized_role_seer_position_experiment_with_game_level(
            num_games=3,
            seed=42,
            configs=configs,
        )
    )
    valid_strategies = [
        config["seer_check_strategy"] for config in configs
    ]
    validation = validate_game_level_rows(
        game_level_rows,
        expected_count=6,
        valid_strategies=valid_strategies,
        valid_seeds=[42],
    )

    check(validation["valid"], "game-level validation passes")
    check(
        validation["row_count"] == 6,
        "game-level row count matches strategies times games",
    )
    check(
        all(
            fieldname in row
            for row in game_level_rows
            for fieldname in GAME_LEVEL_FIELDNAMES
        ),
        "all required game-level columns are present",
    )
    check(
        len({row["game_id"] for row in game_level_rows})
        == len(game_level_rows),
        "game_id values are unique",
    )
    check(
        all(row["winner"] in {"wolf", "village", "draw"}
            for row in game_level_rows),
        "winner values are valid",
    )
    check(
        all(row["strategy"] in valid_strategies for row in game_level_rows),
        "strategy values are valid",
    )


if __name__ == "__main__":
    test_game_level_logging_rows()
    print("All game-level logging tests passed.")
