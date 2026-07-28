"""Expected payoff and volatility metrics for R5."""

from __future__ import annotations

import math


def clean_values(values):
    return [float(value) for value in values if value is not None]


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
    return (values[mid - 1] + values[mid]) / 2


def quantile(values, q):
    values = sorted(clean_values(values))
    if not values:
        return None
    if q <= 0:
        return values[0]
    if q >= 1:
        return values[-1]
    index = (len(values) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return values[low]
    return values[low] * (high - index) + values[high] * (index - low)


def trimmed_mean(values, trim_fraction=0.10):
    values = sorted(clean_values(values))
    if not values:
        return None
    trim_count = int(len(values) * trim_fraction)
    if trim_count * 2 >= len(values):
        return mean(values)
    return mean(values[trim_count: len(values) - trim_count])


def sample_variance(values):
    values = clean_values(values)
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def sample_stdev(values):
    return math.sqrt(sample_variance(values))


def standard_error(values):
    values = clean_values(values)
    if not values:
        return None
    return sample_stdev(values) / math.sqrt(len(values))


def median_absolute_deviation(values):
    values = clean_values(values)
    if not values:
        return None
    center = median(values)
    return median(abs(value - center) for value in values)


def interquartile_range(values):
    values = clean_values(values)
    if not values:
        return None
    return quantile(values, 0.75) - quantile(values, 0.25)


def coefficient_of_variation(values, near_zero=1e-9):
    center = mean(values)
    if center is None or abs(center) <= near_zero:
        return None
    return sample_stdev(values) / abs(center)


def payoff_distribution_metrics(values):
    values = clean_values(values)
    total = len(values)
    if total == 0:
        return {
            "observations": 0,
            "mean_payoff": None,
            "median_payoff": None,
            "trimmed_mean_payoff": None,
            "geometric_analogue": None,
            "geometric_analogue_note": "undefined because no observations",
            "standard_error": None,
            "positive_payoff_probability": None,
            "zero_payoff_probability": None,
            "negative_payoff_probability": None,
            "variance": None,
            "stdev": None,
            "median_absolute_deviation": None,
            "iqr": None,
            "coefficient_of_variation": None,
            "coefficient_of_variation_warning": "undefined because no observations",
        }
    center = mean(values)
    cv = coefficient_of_variation(values)
    return {
        "observations": total,
        "mean_payoff": center,
        "median_payoff": median(values),
        "trimmed_mean_payoff": trimmed_mean(values),
        "geometric_analogue": None,
        "geometric_analogue_note": (
            "not reported because game payoffs can be zero or negative"
        ),
        "standard_error": standard_error(values),
        "positive_payoff_probability": sum(1 for value in values if value > 0) / total,
        "zero_payoff_probability": sum(1 for value in values if value == 0) / total,
        "negative_payoff_probability": sum(1 for value in values if value < 0) / total,
        "variance": sample_variance(values),
        "stdev": sample_stdev(values),
        "median_absolute_deviation": median_absolute_deviation(values),
        "iqr": interquartile_range(values),
        "coefficient_of_variation": cv,
        "coefficient_of_variation_warning": (
            "" if cv is not None and abs(center) > 0.05
            else "interpret cautiously because mean is near zero"
        ),
    }
