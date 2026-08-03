from run_recommended_configuration import run_recommended_configuration


def main():
    game, result = run_recommended_configuration(seed=6202)
    assert result["game_over"] is True
    assert game.enable_r61_villager_voting_policy is True
    assert game.r61_villager_voting_policy == "trust_weighted"
    print("test_r62_configuration_activation.py passed")


if __name__ == "__main__":
    main()
