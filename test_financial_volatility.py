import math

from financial_risk_metrics import interquartile_range, median_absolute_deviation, sample_stdev, sample_variance


def main():
    values = [1.0, 2.0, 3.0, 4.0]
    assert abs(sample_variance(values) - 1.6666666666666667) < 1e-12
    assert abs(sample_stdev(values) - math.sqrt(1.6666666666666667)) < 1e-12
    assert median_absolute_deviation(values) == 1.0
    assert interquartile_range(values) == 1.5
    print("test_financial_volatility.py passed")


if __name__ == "__main__":
    main()
