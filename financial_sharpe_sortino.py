"""Sharpe-like and Sortino-like payoff ratios for R5."""

from __future__ import annotations

from financial_downside_metrics import downside_metrics
from financial_risk_metrics import mean, sample_stdev


def sharpe_like_ratio(values, benchmark=0.0, near_zero=1e-12):
    stdev = sample_stdev(values)
    if stdev is None or stdev <= near_zero:
        return None
    return (mean(values) - benchmark) / stdev


def sortino_like_ratio(values, target=0.0, near_zero=1e-12):
    downside_deviation = downside_metrics(values, target)["downside_deviation"]
    if downside_deviation is None or downside_deviation <= near_zero:
        return None
    return (mean(values) - target) / downside_deviation


def ratio_metrics(values, benchmark=0.0, target=0.0):
    return {
        "sharpe_like_benchmark": benchmark,
        "sharpe_like_ratio": sharpe_like_ratio(values, benchmark),
        "sortino_like_target": target,
        "sortino_like_ratio": sortino_like_ratio(values, target),
    }
