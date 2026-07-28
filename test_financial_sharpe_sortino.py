from financial_sharpe_sortino import sharpe_like_ratio, sortino_like_ratio


def main():
    values = [1.0, 2.0, -1.0, 0.0]
    assert sharpe_like_ratio(values, benchmark=0.0) is not None
    assert sortino_like_ratio(values, target=0.0) is not None
    assert sharpe_like_ratio([1.0, 1.0, 1.0]) is None
    assert sortino_like_ratio([1.0, 2.0, 3.0]) is None
    print("test_financial_sharpe_sortino.py passed")


if __name__ == "__main__":
    main()
