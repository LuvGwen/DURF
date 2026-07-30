from game_state import GameState
from player import Player
from r61_hunter_policies import R61_HUNTER_POLICIES, perform_r61_hunter_shot
from roles import HUNTER, VILLAGER, WEREWOLF


def main():
    players = [Player(1, WEREWOLF), Player(2, VILLAGER), Player(3, HUNTER)]
    players[0].suspicion_score = 0.8
    players[1].p_wolf = 0.7
    state = GameState(players)
    state.kill_player(3)
    for policy in R61_HUNTER_POLICIES:
        target_id, event = perform_r61_hunter_shot(state, 3, policy)
        assert event is not None
        if target_id is not None:
            assert target_id in {1, 2}
            assert event["abstained"] is False
    print("test_r61_hunter_policies.py passed")


if __name__ == "__main__":
    main()
