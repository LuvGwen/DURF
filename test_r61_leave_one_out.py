from r61_common_experiment import leave_one_out_rows


def main():
    rows = []
    for seed in [520, 521]:
        for policy in ["reference", "random_shot"]:
            rows.append({
                "module": "hunter",
                "policy": policy,
                "seed": seed,
                "behavioral_regime": "baseline",
                "village_win": 1,
                "wolf_win": 0,
                "actor_payoff": 0.1,
            })
    output = leave_one_out_rows("hunter", rows, "seed")
    assert output
    print("test_r61_leave_one_out.py passed")


if __name__ == "__main__":
    main()
