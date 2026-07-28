from test_payoff_calculator import build_manual_game

from payoff_calculator import calculate_r4_payoff
from payoff_validation import build_validation_summary


if __name__ == "__main__":
    game = build_manual_game()
    result = calculate_r4_payoff(game, "manual", calculation_specification="core")
    validation = build_validation_summary(
        [result["game_row"]],
        result["player_rows"],
        result["event_rows"],
        result["manifest"],
    )
    assert validation["unique_event_ids"]
    assert validation["duplicate_source_action_rewards"] == 0
    assert validation["terminal_payoff_once_per_player"]
    assert validation["validation_pass"]
    print("test_payoff_no_double_counting.py passed")
