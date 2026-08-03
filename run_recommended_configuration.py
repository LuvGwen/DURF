"""Run a small explicit opt-in recommended configuration smoke test."""

import random

from config import DEFAULT_MAX_ROUNDS, TEN_PLAYER_INITIAL_P_WOLF, TEN_PLAYER_ROLE_SETUP
from game import Game, create_default_players
from research_configuration import recommended_game_kwargs, recommended_research_configuration


def run_recommended_configuration(seed=6202, max_rounds=DEFAULT_MAX_ROUNDS):
    random.seed(seed)
    players = create_default_players(
        role_setup=TEN_PLAYER_ROLE_SETUP,
        initial_p_wolf=TEN_PLAYER_INITIAL_P_WOLF,
    )
    game = Game(players, **recommended_game_kwargs())
    result = game.run_game(max_rounds=max_rounds)
    return game, result


if __name__ == "__main__":
    manifest = recommended_research_configuration()
    game, result = run_recommended_configuration()
    print("Recommended research configuration")
    print("Configuration hash:", manifest["configuration_hash"])
    print("Winner:", result["winner"])
    print("Game over:", result["game_over"])
    print("Events:", len(game.event_log))
