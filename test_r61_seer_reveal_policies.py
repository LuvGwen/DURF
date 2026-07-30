from game import Game
from player import Player
from r61_seer_reveal_policies import (
    R61_SEER_REVEAL_POLICIES,
    maybe_apply_r61_seer_reveal,
)
from roles import SEER, VILLAGER, WEREWOLF


def main():
    game = Game([Player(1, WEREWOLF), Player(2, SEER), Player(3, VILLAGER)])
    event = {
        "seer": 2,
        "target": 1,
        "target_role": WEREWOLF,
        "target_is_wolf": True,
        "round": 1,
    }
    assert R61_SEER_REVEAL_POLICIES
    reveal = maybe_apply_r61_seer_reveal(game, event, "reveal_first_wolf")
    assert reveal is not None
    assert reveal["target_is_wolf"] is True
    assert reveal["uses_hidden_information"] is False
    print("test_r61_seer_reveal_policies.py passed")


if __name__ == "__main__":
    main()
