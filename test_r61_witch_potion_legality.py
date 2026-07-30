from game_state import GameState
from player import Player
from r61_witch_joint_policies import perform_r61_witch_poison
from roles import VILLAGER, WEREWOLF, WITCH


def main():
    players = [Player(1, WEREWOLF), Player(2, VILLAGER), Player(3, WITCH)]
    players[0].suspicion_score = 1.0
    state = GameState(players)
    poison_id, event = perform_r61_witch_poison(state, "aggressive_full")
    assert poison_id == 1
    assert event is not None
    poison_id2, event2 = perform_r61_witch_poison(state, "aggressive_full")
    assert poison_id2 is None
    assert event2 is None
    print("test_r61_witch_potion_legality.py passed")


if __name__ == "__main__":
    main()
