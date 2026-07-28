from bow_r3_distribution_shift import (
    summarize_distribution_shift,
    summarize_repeated_use,
)


if __name__ == "__main__":
    game_rows = [{
        "game_uid": "g1",
        "policy_name": "guarded",
        "template_condition": "in_distribution_templates",
        "behavioral_regime": "baseline",
    }]
    belief_rows = [{
        "game_uid": "g1",
        "policy_name": "guarded",
        "round": 1,
        "p_wolf_delta": 0.1,
        "ood_category": "in_distribution",
    }]
    vote_rows = [{
        "game_uid": "g1",
        "policy_name": "guarded",
        "round": 1,
        "disagrees_with_existing": "True",
    }]
    summary = summarize_distribution_shift(game_rows, belief_rows, vote_rows)
    assert summary[0]["vote_divergence_rate"] == 1.0
    print("PASS: distribution-shift vote divergence is deterministic")
    repeated = summarize_repeated_use(belief_rows, vote_rows)
    assert repeated[0]["bow_updates"] == 1
    print("PASS: repeated-use summary is deterministic")
    print("test_bow_r3_distribution_shift.py passed")
