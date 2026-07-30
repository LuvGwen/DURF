from r61_wolf_aggression_policies import (
    R61_WOLF_AGGRESSION_POLICIES,
    get_r61_wolf_aggression_overrides,
)


def main():
    for policy in R61_WOLF_AGGRESSION_POLICIES:
        overrides = get_r61_wolf_aggression_overrides(policy)
        assert "enable_wolf_strategy" in overrides
        assert "wolf_kill_strategy" in overrides
    print("test_r61_wolf_aggression_policies.py passed")


if __name__ == "__main__":
    main()
