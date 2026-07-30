from game_state import GameState
from player import Player
from r61_witch_joint_policies import (
    R61_WITCH_JOINT_POLICIES,
    perform_r61_witch_poison,
    perform_r61_witch_save,
)
from roles import VILLAGER, WEREWOLF, WITCH


def main():
    assert R61_WITCH_JOINT_POLICIES
    players = [Player(1, WEREWOLF), Player(2, VILLAGER), Player(3, WITCH)]
    players[0].suspicion_score = 1.0
    state = GameState(players)
    saved, save_event = perform_r61_witch_save(state, 2, "aggressive_full")
    assert saved is True
    poison_id, poison_event = perform_r61_witch_poison(
        state,
        "aggressive_full",
        excluded_witch_ids={save_event["witch"]},
    )
    assert poison_id is None
    assert poison_event is None
    print("test_r61_witch_joint_policies.py passed")


if __name__ == "__main__":
    main()
