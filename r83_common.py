"""Shared utilities for R8.3 replication consistency auditing.

R8.3 is analysis-only. It reads frozen R8.2/R8.1/R6.2 artifacts and never
launches gameplay simulations.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results" / "replication_consistency_stage_r83"
R82_DIR = ROOT / "results" / "targeted_replication_stage_r82"
R81_DIR = ROOT / "results" / "project_overfitting_audit_stage_r81"
R8_DIR = ROOT / "results" / "final_integrated_analysis_stage_r8"
R62_DIR = ROOT / "results" / "metrics_integrity_stage_r62"
RESEARCH_DIR = ROOT / "results" / "research_progress"

R4_AUTHORITATIVE_HASH = "eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd"
R5_AUTHORITATIVE_HASH = "4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf"

R82_RAW_HASHES = {
    "results/targeted_replication_stage_r82/r82_game_level_raw.csv": (
        "53a592af91951cf520ac1ad677c4f947362d1c63e88b037ba1683c963d3d6c02"
    ),
    "results/targeted_replication_stage_r82/r82_action_raw.csv.gz": (
        "1dc64525979b76f715bab6f5984445c4441497c11d107789381801f4a44152d5"
    ),
    "results/targeted_replication_stage_r82/r82_primary_contrasts.csv": (
        "04ad59845df9c133b67a9f32cb1394930aab88999a5a25046158b97861e9edfb"
    ),
    "results/targeted_replication_stage_r82/r82_policy_summary.csv": (
        "59578777f020c565a18c2868c48dffa12f4576aefe45591f08066d9c38f45090"
    ),
}

R83_BOOTSTRAP_REPLICATES = 10000
R83_SIGN_FLIP_REPLICATES = 20000
PRIMARY_METRIC = "actor_payoff"

FROZEN_COMPARISONS = {
    "villager": {
        "role": "Villager",
        "reference": "reference",
        "candidate": "trust_weighted",
        "candidate_label": "trust_weighted",
    },
    "seer": {
        "role": "Seer",
        "reference": "private_only",
        "candidate": "immediate_reveal",
        "candidate_label": "immediate_reveal",
    },
    "witch": {
        "role": "Witch",
        "reference": "reference",
        "candidate": "aggressive_full",
        "candidate_label": "aggressive_full",
    },
}

CORRECTED_LAYER_FIELDS = [
    "artifact",
    "row_id",
    "previous_label",
    "audited_label",
    "changed",
    "reason",
    "authoritative_stage",
    "final_use_status",
    "source_file",
]


def fmt(value, digits=4):
    if value in ("", None):
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:.{digits}f}"


def read_csv(path):
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_gzip_csv(path):
    path = Path(path)
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            restval="",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean(values):
    values = [float(value) for value in values if value not in ("", None)]
    return sum(values) / len(values) if values else None


def stdev(values):
    values = [float(value) for value in values if value not in ("", None)]
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return (sum((value - center) ** 2 for value in values) / (len(values) - 1)) ** 0.5


def normal_ci(values, z=1.96):
    values = [float(value) for value in values if value not in ("", None)]
    if not values:
        return None, None
    se = stdev(values) / (len(values) ** 0.5) if len(values) > 1 else 0.0
    center = mean(values)
    return center - z * se, center + z * se


def percentile(values, pct):
    values = sorted(float(value) for value in values)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * pct
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def bootstrap_ci(values, replicates=R83_BOOTSTRAP_REPLICATES, seed=830001):
    values = [float(value) for value in values]
    rng = random.Random(seed)
    n = len(values)
    if not values:
        return None, None
    boot_means = []
    for _ in range(replicates):
        total = sum(values[rng.randrange(n)] for _ in range(n))
        boot_means.append(total / n)
    return percentile(boot_means, 0.025), percentile(boot_means, 0.975)


def sign_flip_p_value(values, replicates=R83_SIGN_FLIP_REPLICATES, seed=830101):
    """Two-sided matched sign-flip p-value using all matched differences.

    Zero differences are retained in the denominator. This is the R8.3
    correction for the R8.2 helper that used only nonzero differences when
    computing null means.
    """
    values = [float(value) for value in values]
    if not values:
        return None
    observed = abs(mean(values))
    rng = random.Random(seed)
    n = len(values)
    more_extreme = 0
    for _ in range(replicates):
        signed_mean = sum(
            value if rng.random() < 0.5 else -value
            for value in values
        ) / n
        if abs(signed_mean) >= observed:
            more_extreme += 1
    return (more_extreme + 1) / (replicates + 1)


def r82_buggy_nonzero_sign_flip_p_value(
    values,
    replicates=R83_SIGN_FLIP_REPLICATES,
    seed=830101,
):
    """Reproduce the R8.2 denominator bug for audit comparison only."""
    values = [float(value) for value in values]
    observed = abs(mean(values))
    nonzero = [value for value in values if value != 0.0]
    rng = random.Random(seed)
    if not nonzero:
        return 1.0, 0
    more_extreme = 0
    for _ in range(replicates):
        signed_mean = sum(
            value if rng.random() < 0.5 else -value
            for value in nonzero
        ) / len(nonzero)
        if abs(signed_mean) >= observed:
            more_extreme += 1
    return (more_extreme + 1) / (replicates + 1), len(nonzero)


def holm_adjust(rows, p_key="raw_p_value", out_key="Holm_adjusted_p_value"):
    ordered = sorted(
        [
            (index, row)
            for index, row in enumerate(rows)
            if row.get(p_key) not in ("", None)
        ],
        key=lambda item: float(item[1][p_key]),
    )
    total = len(ordered)
    adjusted = [None] * len(rows)
    running_max = 0.0
    for rank, (index, row) in enumerate(ordered, start=1):
        value = min(1.0, (total - rank + 1) * float(row[p_key]))
        running_max = max(running_max, value)
        adjusted[index] = running_max
    for index, row in enumerate(rows):
        row[out_key] = adjusted[index]
    return rows


def r82_game_rows():
    return read_csv(R82_DIR / "r82_game_level_raw.csv")


def r82_policy_summary():
    return read_csv(R82_DIR / "r82_policy_summary.csv")


def r82_primary_contrasts():
    return read_csv(R82_DIR / "r82_primary_contrasts.csv")


def r82_special_metrics():
    return read_csv(R82_DIR / "r82_special_module_metrics.csv")


def r82_action_rows():
    return read_gzip_csv(R82_DIR / "r82_action_raw.csv.gz")


def rows_by_key(rows, *keys):
    output = {}
    for row in rows:
        output[tuple(row[key] for key in keys)] = row
    return output


def paired_differences(module, metric=PRIMARY_METRIC):
    spec = FROZEN_COMPARISONS[module]
    grouped = defaultdict(dict)
    for row in r82_game_rows():
        if row["module"] != module:
            continue
        grouped[row["matched_set_id"]][row["policy"]] = float(row[metric])

    differences = []
    for matched_set_id, policy_rows in sorted(grouped.items()):
        if spec["reference"] not in policy_rows or spec["candidate"] not in policy_rows:
            continue
        differences.append({
            "matched_set_id": matched_set_id,
            "difference": policy_rows[spec["candidate"]] - policy_rows[spec["reference"]],
            "candidate_value": policy_rows[spec["candidate"]],
            "reference_value": policy_rows[spec["reference"]],
        })
    return differences


def support_rate(module, metric, group_key):
    spec = FROZEN_COMPARISONS[module]
    grouped = defaultdict(lambda: defaultdict(list))
    for row in r82_game_rows():
        if row["module"] != module:
            continue
        grouped[row[group_key]][row["policy"]].append(float(row[metric]))
    diffs = []
    for group_value, policy_rows in sorted(grouped.items()):
        if spec["candidate"] in policy_rows and spec["reference"] in policy_rows:
            diffs.append(
                mean(policy_rows[spec["candidate"]])
                - mean(policy_rows[spec["reference"]])
            )
    return {
        "support_rate": (
            sum(1 for diff in diffs if diff > 0) / len(diffs)
            if diffs
            else None
        ),
        "min_difference": min(diffs) if diffs else None,
        "max_difference": max(diffs) if diffs else None,
        "group_count": len(diffs),
    }


def witch_action_summary():
    counts = defaultdict(Counter)
    for row in r82_action_rows():
        if row["module"] != "witch":
            continue
        policy = row["policy"]
        event_type = row["event_type"]
        counts[policy][event_type] += 1
        if event_type == "witch_poison":
            if row["target_is_wolf"] == "True":
                counts[policy]["correct_poison"] += 1
            elif row["target_is_wolf"] == "False":
                counts[policy]["wrong_poison"] += 1
        if event_type == "witch_save":
            if row["target_is_wolf"] == "True":
                counts[policy]["saved_wolf"] += 1
            elif row["target_is_wolf"] == "False":
                counts[policy]["saved_nonwolf"] += 1
    return counts


def verify_r82_raw_hashes():
    rows = []
    for relative_path, expected in R82_RAW_HASHES.items():
        actual = sha256_file(ROOT / relative_path)
        rows.append({
            "file": relative_path,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "matches": str(actual == expected),
        })
    return rows


def verify_authoritative_manifest_hashes():
    forensic_rows = read_csv(R81_DIR / "r81_manifest_hash_forensic_audit.csv")
    current = [
        row for row in forensic_rows
        if row["stage"] == "current_manifest_like_inventory"
        and row["manifest_type"] in {"r4_payoff_manifest", "r5_metric_manifest"}
    ]
    return {
        row["manifest_type"]: row["final_authoritative_hash"]
        for row in current
    }


def conclusion_from_holm(diff, holm_p):
    if holm_p <= 0.05 and diff > 0:
        return "independently_replicated_confirmatory_supported"
    if holm_p <= 0.05 and diff < 0:
        return "confirmatory_harmful"
    if diff > 0:
        return "positive_direction_not_confirmatorily_replicated"
    return "reference_retained"


def read_original_research_csv(path):
    if not Path(path).exists():
        return []
    return read_csv(path)
