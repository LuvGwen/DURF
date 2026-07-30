from r61_risk_metrics import payoff_risk_metrics


def main():
    metrics = payoff_risk_metrics([1.0, -1.0, 0.5, -0.5])
    assert metrics["observations"] == 4
    assert metrics["downside_deviation"] is not None
    assert metrics["cvar_like_95"] is not None
    print("test_r61_risk_metrics.py passed")


if __name__ == "__main__":
    main()
