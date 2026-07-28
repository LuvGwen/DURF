from test_payoff_calculator import build_manual_game

from payoff_calculator import calculate_r4_payoff


if __name__ == "__main__":
    game = build_manual_game()
    first = calculate_r4_payoff(game, "manual", calculation_specification="core")
    second = calculate_r4_payoff(game, "manual", calculation_specification="core")
    assert first["event_rows"] == second["event_rows"]
    assert first["player_rows"] == second["player_rows"]
    print("test_payoff_reproducibility.py passed")
