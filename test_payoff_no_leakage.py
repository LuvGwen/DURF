from config import TEN_PLAYER_ROLE_SETUP
from game import Game, create_default_players


if __name__ == "__main__":
    players = create_default_players(role_setup=TEN_PLAYER_ROLE_SETUP)
    game = Game(players, enable_r4_payoff_ledger=True)
    game.run_one_round()
    assert all(
        event["event_type"] not in {"terminal_result", "r4_payoff_event"}
        for event in game.event_log
    )
    game.run_game(max_rounds=5)
    assert all(
        event["event_type"] not in {"terminal_result", "r4_payoff_event"}
        for event in game.event_log
    )
    print("test_payoff_no_leakage.py passed")
