from research_configuration import recommended_game_kwargs, recommended_research_configuration


def main():
    manifest = recommended_research_configuration()
    kwargs = recommended_game_kwargs()
    assert manifest["configuration_name"] == "recommended_research_configuration"
    assert manifest["historical_default_unchanged"] is True
    assert kwargs["enable_r61_villager_voting_policy"] is True
    assert kwargs["r61_villager_voting_policy"] == "trust_weighted"
    assert kwargs["enable_bow_r3"] is False
    assert kwargs["enable_ml_wolf_kill_policy"] is False
    print("test_r62_recommended_configuration.py passed")


if __name__ == "__main__":
    main()
