from financial_downside_metrics import downside_metrics


def main():
    metrics = downside_metrics([1.0, -2.0, -4.0, 3.0], target=0.0)
    assert metrics["downside_count"] == 2
    assert abs(metrics["downside_deviation"] - ((4 + 16) / 2) ** 0.5) < 1e-12
    assert metrics["negative_payoff_probability"] == 0.5
    assert metrics["mean_negative_payoff"] == -3.0
    print("test_financial_downside_metrics.py passed")


if __name__ == "__main__":
    main()
