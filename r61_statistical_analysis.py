"""Formal paired summaries for R6.1 matched policy comparisons."""

from __future__ import annotations

import math
import random
from collections import defaultdict


def mean(values):
    values = [float(value) for value in values if value not in (None, "")]
    return sum(values) / len(values) if values else None


def stdev(values):
    values = [float(value) for value in values if value not in (None, "")]
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return math.sqrt(
        sum((value - center) ** 2 for value in values) / (len(values) - 1)
    )


def normal_ci(values, z=1.96):
    values = [float(value) for value in values if value not in (None, "")]
    if not values:
        return None, None
    center = mean(values)
    se = stdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0
    return center - z * se, center + z * se


def paired_differences(rows, reference_policy, candidate_policy, metric_key):
    by_key = {}
    for row in rows:
        key = row["matched_set_id"]
        by_key.setdefault(key, {})[row["policy"]] = row

    differences = []
    for policy_rows in by_key.values():
        if (
            reference_policy not in policy_rows
            or candidate_policy not in policy_rows
        ):
            continue
        candidate_value = float(policy_rows[candidate_policy][metric_key])
        reference_value = float(policy_rows[reference_policy][metric_key])
        differences.append(candidate_value - reference_value)

    return differences


def permutation_p_value(differences, iterations=2000, seed=2026061):
    differences = [float(value) for value in differences]
    if not differences:
        return None
    observed = abs(mean(differences))
    rng = random.Random(seed)
    more_extreme = 0
    nonzero = [value for value in differences if value != 0.0]
    if not nonzero:
        return 1.0
    for _ in range(iterations):
        signed = [
            value if rng.random() < 0.5 else -value
            for value in nonzero
        ]
        if abs(mean(signed)) >= observed:
            more_extreme += 1
    return (more_extreme + 1) / (iterations + 1)


def paired_contrast(
    rows,
    module,
    reference_policy,
    candidate_policy,
    metric_key="actor_payoff",
    permutation_iterations=2000,
):
    differences = paired_differences(
        rows,
        reference_policy,
        candidate_policy,
        metric_key,
    )
    center = mean(differences)
    diff_stdev = stdev(differences)
    ci_low, ci_high = normal_ci(differences)
    p_value = permutation_p_value(
        differences,
        iterations=permutation_iterations,
        seed=2026061 + len(candidate_policy) + len(module),
    )
    return {
        "module": module,
        "reference_policy": reference_policy,
        "candidate_policy": candidate_policy,
        "metric": metric_key,
        "matched_set_count": len(differences),
        "mean_difference": center,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "difference_stdev": diff_stdev,
        "effect_size_dz": (
            center / diff_stdev
            if diff_stdev not in (None, 0.0) and center is not None
            else None
        ),
        "raw_p_value": p_value,
    }


def holm_adjust(rows, p_key="raw_p_value", out_key="holm_adjusted_p_value"):
    valid = [
        (index, row)
        for index, row in enumerate(rows)
        if row.get(p_key) not in (None, "")
    ]
    ordered = sorted(valid, key=lambda item: float(item[1][p_key]))
    total = len(ordered)
    adjusted_values = [None] * len(rows)
    running_max = 0.0
    for rank, (index, row) in enumerate(ordered, start=1):
        adjusted = min(1.0, (total - rank + 1) * float(row[p_key]))
        running_max = max(running_max, adjusted)
        adjusted_values[index] = running_max
    for index, row in enumerate(rows):
        row[out_key] = adjusted_values[index]
    return rows


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return dict(grouped)


def mean_by_group(rows, group_key, metric_key):
    output = []
    for group, group_rows in sorted(group_by(rows, group_key).items()):
        values = [float(row[metric_key]) for row in group_rows]
        output.append({
            group_key: group,
            "n": len(values),
            f"mean_{metric_key}": mean(values),
            f"stdev_{metric_key}": stdev(values),
        })
    return output


if __name__ == "__main__":
    print(permutation_p_value([1, -1, 0.5, 0.2], iterations=100))
