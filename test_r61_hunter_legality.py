from game_state import GameState
from player import Player
from r61_hunter_policies import perform_r61_hunter_shot
from roles import HUNTER, VILLAGER, WEREWOLF


def main():
    players = [Player(1, WEREWOLF), Player(2, VILLAGER), Player(3, HUNTER)]
    state = GameState(players)
    state.kill_player(3)
    target_id, _ = perform_r61_hunter_shot(state, 3, "highest_suspicion")
    assert target_id != 3
    assert state.get_player_by_id(target_id).alive
    print("test_r61_hunter_legality.py passed")


if __name__ == "__main__":
    main()
