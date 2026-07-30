"""Financial-style risk metrics used by R6.1 role-strategy experiments."""

from __future__ import annotations

import math


def clean_values(values):
    return [float(value) for value in values if value not in (None, "")]


def mean(values):
    values = clean_values(values)
    return sum(values) / len(values) if values else None


def median(values):
    values = sorted(clean_values(values))
    if not values:
        return None
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def sample_stdev(values):
    values = clean_values(values)
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return math.sqrt(
        sum((value - center) ** 2 for value in values) / (len(values) - 1)
    )


def quantile(values, q):
    values = sorted(clean_values(values))
    if not values:
        return None
    if q <= 0:
        return values[0]
    if q >= 1:
        return values[-1]
    index = (len(values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[lower]
    return values[lower] * (upper - index) + values[upper] * (index - lower)


def downside_deviation(values, threshold=0.0):
    values = clean_values(values)
    if not values:
        return None
    losses = [min(0.0, value - threshold) for value in values]
    return math.sqrt(sum(loss * loss for loss in losses) / len(values))


def cvar_like(values, confidence=0.95):
    values = clean_values(values)
    if not values:
        return None
    cutoff = quantile(values, 1.0 - confidence)
    tail = [value for value in values if value <= cutoff]
    return mean(tail)


def payoff_risk_metrics(values):
    values = clean_values(values)
    if not values:
        return {
            "observations": 0,
            "mean_payoff": None,
            "median_payoff": None,
            "stdev_payoff": None,
            "downside_deviation": None,
            "negative_payoff_probability": None,
            "var_like_90": None,
            "var_like_95": None,
            "cvar_like_90": None,
            "cvar_like_95": None,
            "sharpe_like_ratio": None,
            "sortino_like_ratio": None,
        }

    center = mean(values)
    stdev = sample_stdev(values)
    downside = downside_deviation(values)

    return {
        "observations": len(values),
        "mean_payoff": center,
        "median_payoff": median(values),
        "stdev_payoff": stdev,
        "downside_deviation": downside,
        "negative_payoff_probability": (
            sum(1 for value in values if value < 0) / len(values)
        ),
        "var_like_90": quantile(values, 0.10),
        "var_like_95": quantile(values, 0.05),
        "cvar_like_90": cvar_like(values, 0.90),
        "cvar_like_95": cvar_like(values, 0.95),
        "sharpe_like_ratio": (
            center / stdev if stdev not in (None, 0.0) else None
        ),
        "sortino_like_ratio": (
            center / downside if downside not in (None, 0.0) else None
        ),
    }


def frontier_membership(rows, risk_key):
    frontier = []
    for row in rows:
        row_mean = float(row.get("mean_actor_payoff", 0.0))
        row_risk = float(row.get(risk_key, 0.0))
        dominated = False
        for other in rows:
            if other is row:
                continue
            other_mean = float(other.get("mean_actor_payoff", 0.0))
            other_risk = float(other.get(risk_key, 0.0))
            if (
                other_mean >= row_mean
                and other_risk <= row_risk
                and (other_mean > row_mean or other_risk < row_risk)
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(row["policy"])
    return frontier


if __name__ == "__main__":
    print(payoff_risk_metrics([1, -1, 0.5, -0.2]))
