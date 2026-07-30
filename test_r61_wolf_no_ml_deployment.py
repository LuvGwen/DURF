from r61_common_experiment import game_config_for


def main():
    for policy in ["reference", "aggressive_false_accuse", "deep_cover"]:
        config = game_config_for("wolf", policy, "mixed_strategies")
        assert config["enable_ml_wolf_kill_policy"] is False
        assert config["enable_ml_stage2b_policy"] is False
    print("test_r61_wolf_no_ml_deployment.py passed")


if __name__ == "__main__":
    main()
