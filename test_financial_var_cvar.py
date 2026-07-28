from financial_downside_metrics import var_cvar_metrics
from financial_risk_metrics import quantile


def main():
    values = [-5.0, -2.0, 0.0, 1.0, 3.0]
    metrics = var_cvar_metrics(values, confidence=0.90)
    assert metrics["var_like_payoff_threshold"] == quantile(values, 0.10)
    assert metrics["cvar_like_loss"] >= metrics["var_like_loss"]
    assert metrics["tail_observation_count"] >= 1
    print("test_financial_var_cvar.py passed")


if __name__ == "__main__":
    main()
