import random

from config import TEN_PLAYER_ROLE_SETUP
from game import Game, create_default_players


if __name__ == "__main__":
    random.seed(123)
    players = create_default_players(role_setup=TEN_PLAYER_ROLE_SETUP)
    game = Game(players)
    result = game.run_game(max_rounds=5)
    assert "r4_payoff_summary" not in result
    assert game.enable_r4_payoff_ledger is False
    assert game.r4_payoff_results == {}

    random.seed(123)
    players_enabled = create_default_players(role_setup=TEN_PLAYER_ROLE_SETUP)
    game_enabled = Game(players_enabled, enable_r4_payoff_ledger=True)
    enabled_result = game_enabled.run_game(max_rounds=5)
    assert "r4_payoff_summary" in enabled_result
    assert game_enabled.r4_payoff_results
    print("test_payoff_default_behavior.py passed")
