from financial_r51_analysis import event_flag_sets, premium_bootstrap_ci


def test_premium_flags_separate_information_and_manipulation():
    events = [
        {"game_id": "g1", "payoff_component": "seer_investigation_used", "target_role": "werewolf"},
        {"game_id": "g2", "payoff_component": "wolf_villager_voted_out_shared", "target_role": "villager"},
    ]
    information, manipulation = event_flag_sets(events)
    assert "g1" in information["wolf_found_by_check"]
    assert "g2" in manipulation["primary_any_manipulation"]


def test_premium_bootstrap_ci_returns_bounds():
    records = [
        {"game_id": "g1", "mean_payoff": 2.0},
        {"game_id": "g2", "mean_payoff": 0.0},
        {"game_id": "g3", "mean_payoff": 1.0},
    ]
    low, high = premium_bootstrap_ci(records, {"g1"})
    assert low is not None
    assert high is not None
    assert low <= high
