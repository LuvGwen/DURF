"""Downside-risk, VaR-like, and CVaR-like metrics for R5."""

from __future__ import annotations

import math

from financial_risk_metrics import clean_values, mean, quantile


def downside_metrics(values, target=0.0):
    values = clean_values(values)
    downside_deficits = [target - value for value in values if value < target]
    n = len(values)
    if not values:
        return {
            "downside_target": target,
            "downside_count": 0,
            "downside_deviation": None,
            "lower_partial_moment_1": None,
            "lower_partial_moment_2": None,
            "mean_negative_payoff": None,
            "worst_decile_mean_payoff": None,
            "maximum_observed_loss": None,
            "negative_payoff_probability": None,
        }
    if downside_deficits:
        downside_deviation = math.sqrt(
            sum(deficit ** 2 for deficit in downside_deficits)
            / len(downside_deficits)
        )
    else:
        downside_deviation = 0.0
    negative_payoffs = [value for value in values if value < 0]
    worst_decile_cutoff = quantile(values, 0.10)
    worst_decile_values = [value for value in values if value <= worst_decile_cutoff]
    return {
        "downside_target": target,
        "downside_count": len(downside_deficits),
        "downside_deviation": downside_deviation,
        "lower_partial_moment_1": (
            sum(downside_deficits) / n if n else None
        ),
        "lower_partial_moment_2": (
            sum(deficit ** 2 for deficit in downside_deficits) / n if n else None
        ),
        "mean_negative_payoff": mean(negative_payoffs),
        "worst_decile_mean_payoff": mean(worst_decile_values),
        "maximum_observed_loss": -min(values),
        "negative_payoff_probability": len(negative_payoffs) / n,
    }


def var_cvar_metrics(values, confidence=0.95):
    values = clean_values(values)
    if not values:
        return {
            "confidence_level": confidence,
            "var_like_payoff_threshold": None,
            "var_like_loss": None,
            "cvar_like_loss": None,
            "lower_tail_payoff_quantile": None,
            "worst_tail_mean_payoff": None,
            "tail_observation_count": 0,
        }
    tail_probability = round(1.0 - confidence, 10)
    threshold = quantile(values, tail_probability)
    tail_values = [value for value in values if value <= threshold]
    return {
        "confidence_level": confidence,
        "var_like_payoff_threshold": threshold,
        "var_like_loss": -threshold,
        "cvar_like_loss": mean([-value for value in tail_values]),
        "lower_tail_payoff_quantile": threshold,
        "worst_tail_mean_payoff": mean(tail_values),
        "tail_observation_count": len(tail_values),
    }
