"""Grouped bootstrap helpers for R5."""

from __future__ import annotations

import random
from collections import defaultdict

from financial_risk_metrics import quantile


def group_rows(rows, group_key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[group_key]].append(row)
    return dict(grouped)


def grouped_bootstrap_ci(
    rows,
    group_key,
    metric_fn,
    iterations=2000,
    seed=202605,
    alpha=0.05,
):
    grouped = group_rows(rows, group_key)
    groups = list(grouped.values())
    if not groups:
        return {
            "estimate": None,
            "ci_low": None,
            "ci_high": None,
            "bootstrap_iterations": iterations,
            "bootstrap_unit": group_key,
        }
    rng = random.Random(seed)
    estimates = []
    for _ in range(iterations):
        sample_rows = []
        for _ in groups:
            sample_rows.extend(rng.choice(groups))
        estimates.append(metric_fn(sample_rows))
    estimates = [value for value in estimates if value is not None]
    estimate = metric_fn(rows)
    return {
        "estimate": estimate,
        "ci_low": quantile(estimates, alpha / 2) if estimates else None,
        "ci_high": quantile(estimates, 1 - alpha / 2) if estimates else None,
        "bootstrap_iterations": iterations,
        "bootstrap_unit": group_key,
    }


def grouped_value_bootstrap_ci(
    value_clusters,
    metric_fn,
    iterations=2000,
    seed=202605,
    alpha=0.05,
    bootstrap_unit="game_id",
):
    clusters = [list(cluster) for cluster in value_clusters if cluster]
    if not clusters:
        return {
            "estimate": None,
            "ci_low": None,
            "ci_high": None,
            "bootstrap_iterations": iterations,
            "bootstrap_unit": bootstrap_unit,
        }
    all_values = [value for cluster in clusters for value in cluster]
    estimate = metric_fn(all_values)
    rng = random.Random(seed)
    estimates = []
    cluster_count = len(clusters)
    for _ in range(iterations):
        sampled_values = []
        for _ in range(cluster_count):
            sampled_values.extend(clusters[rng.randrange(cluster_count)])
        estimates.append(metric_fn(sampled_values))
    estimates = [value for value in estimates if value is not None]
    return {
        "estimate": estimate,
        "ci_low": quantile(estimates, alpha / 2) if estimates else None,
        "ci_high": quantile(estimates, 1 - alpha / 2) if estimates else None,
        "bootstrap_iterations": iterations,
        "bootstrap_unit": bootstrap_unit,
    }
