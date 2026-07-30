from r61_common_experiment import MODULES, game_config_for


def main():
    for module, spec in MODULES.items():
        config = game_config_for(module, spec["reference"], "mixed_strategies")
        assert config["enable_bow_r3"] is False
    print("test_r61_no_bow_live_integration.py passed")


if __name__ == "__main__":
    main()
