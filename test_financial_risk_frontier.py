from financial_risk_frontier import dominates, mark_frontier


def main():
    a = {"condition_name": "a", "mean_payoff": 2.0, "risk_value": 1.0}
    b = {"condition_name": "b", "mean_payoff": 1.0, "risk_value": 1.5}
    c = {"condition_name": "c", "mean_payoff": 2.5, "risk_value": 2.0}
    assert dominates(a, b)
    marked = mark_frontier([a, b, c])
    by_name = {row["condition_name"]: row for row in marked}
    assert by_name["b"]["is_dominated"]
    assert by_name["a"]["is_efficient"]
    assert by_name["c"]["is_efficient"]
    print("test_financial_risk_frontier.py passed")


if __name__ == "__main__":
    main()
