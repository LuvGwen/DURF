from types import SimpleNamespace

from game_state import GameState
from payoff_calculator import calculate_r4_payoff
from player import Player
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH


def build_manual_game():
    players = [
        Player(1, WEREWOLF),
        Player(2, WEREWOLF),
        Player(3, VILLAGER),
        Player(4, SEER),
        Player(5, WITCH),
        Player(6, HUNTER),
    ]
    state = GameState(players)
    players[2].alive = False
    players[5].alive = False
    state.game_over = True
    state.winner = "village"
    state.round_number = 2
    event_log = [
        {
            "round": 1,
            "phase": "night",
            "event_type": "seer_check",
            "content": {"seer": 4, "target": 1, "target_is_wolf": True},
        },
        {
            "round": 1,
            "phase": "night",
            "event_type": "witch_save",
            "content": {"witch": 5, "saved_player": 3},
        },
        {
            "round": 1,
            "phase": "night",
            "event_type": "witch_poison",
            "content": {"witch": 5, "poisoned_player": 2, "target_is_wolf": True},
        },
        {
            "round": 1,
            "phase": "day",
            "event_type": "hunter_shot",
            "content": {"hunter": 6, "shot_target": 1, "target_is_wolf": True},
        },
        {
            "round": 1,
            "phase": "day",
            "event_type": "day_vote",
            "content": {"votes": {3: 1, 4: 1, 5: 1}, "eliminated": 1},
        },
    ]
    return SimpleNamespace(state=state, event_log=event_log)


if __name__ == "__main__":
    game = build_manual_game()
    result = calculate_r4_payoff(game, "manual", calculation_specification="core")
    rows = result["event_rows"]
    components = [row["payoff_component"] for row in rows]
    assert "seer_investigation_used" in components
    assert "seer_information_leads_to_wolf_elimination" in components
    assert "witch_correct_save" in components
    assert "witch_correct_poison" in components
    assert "hunter_correct_shot" in components
    player_total = sum(float(row["total_payoff"]) for row in result["player_rows"])
    game_total = float(result["game_row"]["total_game_payoff"])
    assert abs(player_total - game_total) < 1e-9
    print("test_payoff_calculator.py passed")
