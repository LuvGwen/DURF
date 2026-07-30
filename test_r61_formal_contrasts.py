from r61_common_experiment import build_primary_contrasts


def main():
    rows = []
    for index in range(5):
        base = {
            "module": "hunter",
            "matched_set_id": f"m{index}",
            "seed": 520,
            "behavioral_regime": "baseline",
            "village_win": 0,
            "wolf_win": 1,
        }
        rows.append({**base, "policy": "reference", "actor_payoff": 0.0})
        rows.append({**base, "policy": "random_shot", "actor_payoff": 0.2})
        rows.append({**base, "policy": "no_shot", "actor_payoff": -0.1})
        rows.append({**base, "policy": "highest_suspicion", "actor_payoff": 0.1})
        rows.append({**base, "policy": "highest_p_wolf", "actor_payoff": 0.1})
        rows.append({**base, "policy": "conservative_threshold", "actor_payoff": 0.0})
    contrasts = build_primary_contrasts("hunter", rows)
    assert contrasts
    assert all("holm_adjusted_p_value" in row for row in contrasts)
    print("test_r61_formal_contrasts.py passed")


if __name__ == "__main__":
    main()
