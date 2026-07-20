import random

from game_state import GameState
from player import Player
from position_model import assign_positions
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH
from seer_action import circular_seat_distance, perform_seer_action
from structured_seer_search_experiment import (
    STRUCTURED_SEER_STRATEGIES,
    get_structured_seer_search_configs,
    run_structured_seer_search_experiment,
    validate_structured_game_level_rows,
)


TEN_PLAYER_ROLES = [
    WEREWOLF,
    WEREWOLF,
    VILLAGER,
    SEER,
    WITCH,
    HUNTER,
    VILLAGER,
    VILLAGER,
    WEREWOLF,
    VILLAGER,
]

ALT_TEN_PLAYER_ROLES = [
    VILLAGER,
    WITCH,
    WEREWOLF,
    SEER,
    WEREWOLF,
    VILLAGER,
    HUNTER,
    VILLAGER,
    VILLAGER,
    WEREWOLF,
]


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"PASS: {message}")


def make_state(roles=None):
    if roles is None:
        roles = TEN_PLAYER_ROLES

    players = [
        Player(player_id=i + 1, role=role)
        for i, role in enumerate(roles)
    ]
    assign_positions(players)
    return GameState(players)


def test_distance_calculation():
    check(circular_seat_distance(1, 2) == 1, "adjacent distance is 1")
    check(circular_seat_distance(1, 10) == 1, "wrap distance is 1")
    check(circular_seat_distance(1, 6) == 5, "opposite distance is 5")
    check(circular_seat_distance(4, 8) == 4, "middle distance is valid")


def test_all_strategies_choose_valid_targets():
    for strategy in STRUCTURED_SEER_STRATEGIES:
        random.seed(100)
        state = make_state()
        event = perform_seer_action(
            state,
            seer_check_strategy=strategy,
            avoid_repeat=True,
        )
        target = state.get_player_by_id(event["target"])

        check(target.alive, f"{strategy} checks alive target")
        check(event["target"] != event["seer"], f"{strategy} avoids self")


def test_no_duplicate_check_histories():
    for strategy in STRUCTURED_SEER_STRATEGIES:
        random.seed(200)
        state = make_state()
        targets = []

        for _ in range(4):
            event = perform_seer_action(
                state,
                seer_check_strategy=strategy,
                avoid_repeat=True,
            )
            targets.append(event["target"])

        check(
            len(targets) == len(set(targets)),
            f"{strategy} avoids duplicate targets",
        )


def test_random_strategy_reproducible_under_seed():
    random.seed(300)
    first_state = make_state()
    first_event = perform_seer_action(
        first_state,
        seer_check_strategy="random",
        avoid_repeat=True,
    )

    random.seed(300)
    second_state = make_state()
    second_event = perform_seer_action(
        second_state,
        seer_check_strategy="random",
        avoid_repeat=True,
    )

    check(
        first_event["target"] == second_event["target"],
        "random strategy is reproducible with the same seed",
    )


def test_strategy_selection_does_not_use_hidden_roles():
    for strategy in STRUCTURED_SEER_STRATEGIES:
        random.seed(400)
        first_state = make_state(TEN_PLAYER_ROLES)
        first_event = perform_seer_action(
            first_state,
            seer_check_strategy=strategy,
            avoid_repeat=True,
        )

        random.seed(400)
        second_state = make_state(ALT_TEN_PLAYER_ROLES)
        second_event = perform_seer_action(
            second_state,
            seer_check_strategy=strategy,
            avoid_repeat=True,
        )

        check(
            first_event["target"] == second_event["target"],
            f"{strategy} target choice is unchanged by hidden roles",
        )


def test_structured_game_level_validation():
    configs = get_structured_seer_search_configs()[:2]
    raw_rows, _, _ = run_structured_seer_search_experiment(
        num_games=2,
        seeds=[42],
        configs=configs,
    )
    validation = validate_structured_game_level_rows(
        raw_rows,
        expected_count=4,
        valid_strategies=[
            config["seer_check_strategy"] for config in configs
        ],
        valid_seeds=[42],
    )

    check(validation["valid"], "structured game-level validation passes")
    check(validation["row_count"] == 4, "structured row count matches")
    check(
        len({row["game_id"] for row in raw_rows}) == 4,
        "structured game ids are unique",
    )


if __name__ == "__main__":
    test_distance_calculation()
    test_all_strategies_choose_valid_targets()
    test_no_duplicate_check_histories()
    test_random_strategy_reproducible_under_seed()
    test_strategy_selection_does_not_use_hidden_roles()
    test_structured_game_level_validation()
    print("All structured seer search tests passed.")
