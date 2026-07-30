from game import Game, create_default_players


def main():
    game = Game(create_default_players())
    assert game.enable_r61_hunter_policy is False
    assert game.enable_r61_seer_reveal_policy is False
    assert game.enable_r61_witch_joint_policy is False
    assert game.enable_r61_wolf_aggression_policy is False
    assert game.enable_r61_villager_voting_policy is False
    print("test_r61_default_behavior.py passed")


if __name__ == "__main__":
    main()
