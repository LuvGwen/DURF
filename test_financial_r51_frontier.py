from financial_r51_analysis import build_frontiers


def test_frontier_uses_actor_specific_role_column():
    metrics = [
        {
            "payoff_specification": "core",
            "affected_role": "seer",
            "strategy_name": "seer_highest_suspicion",
            "mean_payoff": 1.0,
            "stdev": 0.5,
            "downside_deviation": 0.2,
            "cvar95_loss": 0.4,
            "sharpe_like_ratio": 2.0,
            "sortino_like_ratio": 3.0,
        }
    ]
    frontier, dominated = build_frontiers(metrics)
    assert frontier
    assert not dominated
    assert all(row["affected_role"] == "seer" for row in frontier)
