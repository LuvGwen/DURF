from game_state import GameState
from player import Player
from r61_villager_voting_policies import (
    R61_VILLAGER_VOTING_POLICIES,
    choose_r61_villager_vote_target,
)
from roles import VILLAGER, WEREWOLF


def main():
    players = [Player(1, VILLAGER), Player(2, WEREWOLF), Player(3, VILLAGER)]
    state = GameState(players)
    for policy in R61_VILLAGER_VOTING_POLICIES:
        target = choose_r61_villager_vote_target(players[0], players, state, policy)
        assert target is not None
        assert target.player_id != players[0].player_id
        assert target.alive
    print("test_r61_villager_voting_policies.py passed")


if __name__ == "__main__":
    main()
