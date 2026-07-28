from financial_risk_metrics import mean, payoff_distribution_metrics, trimmed_mean


def main():
    values = [1.0, 2.0, -1.0, 0.0]
    assert mean(values) == 0.5
    metrics = payoff_distribution_metrics(values)
    assert metrics["mean_payoff"] == 0.5
    assert metrics["positive_payoff_probability"] == 0.5
    assert metrics["zero_payoff_probability"] == 0.25
    assert metrics["negative_payoff_probability"] == 0.25
    assert trimmed_mean(values, 0.10) == 0.5
    print("test_financial_expected_payoff.py passed")


if __name__ == "__main__":
    main()
