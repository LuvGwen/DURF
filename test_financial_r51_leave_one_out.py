from financial_r51_analysis import build_leave_one_out


def test_leave_one_seed_removes_exactly_one_seed():
    rows = [
        {
            "seed": "1",
            "behavioral_regime": "a",
            "payoff_specification": "core",
            "affected_role": "seer",
            "strategy_name": "seer_highest_suspicion",
            "total_payoff": 1.0,
            "opportunity_cost": 0.0,
        },
        {
            "seed": "2",
            "behavioral_regime": "a",
            "payoff_specification": "core",
            "affected_role": "seer",
            "strategy_name": "seer_highest_suspicion",
            "total_payoff": 2.0,
            "opportunity_cost": 0.0,
        },
    ]
    leave = build_leave_one_out(rows, "seed")
    assert {row["omitted_seed"] for row in leave} == {"1", "2"}
    assert all(row["rank"] == 1 for row in leave)
