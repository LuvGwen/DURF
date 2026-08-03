from research_configuration import recommended_game_kwargs, recommended_research_configuration


def main():
    manifest = recommended_research_configuration()
    rejected = set(manifest["rejected_alternatives"])
    assert "hunter_no_shot" in rejected
    assert "wolf_deep_cover" in rejected
    assert "wolf_random_kill" in rejected
    kwargs = recommended_game_kwargs()
    assert kwargs["enable_r61_hunter_policy"] is False
    assert kwargs["enable_r61_wolf_aggression_policy"] is False
    print("test_r62_rejected_policies_disabled.py passed")


if __name__ == "__main__":
    main()
