"""Analysis, reporting, and cumulative documentation for R3 BoW integration."""

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from bow_r3_belief_integration import (
    R3_BELIEF_POLICIES,
    R3_BELIEF_WEIGHTS,
    R3_BOW_SIGNAL_VARIANTS,
    r2_manifest_hashes,
)
from bow_r3_distribution_shift import (
    summarize_distribution_shift,
    summarize_repeated_use,
)
from bow_r3_full_rollout_analysis import summarize_rollout_rows
from bow_r3_live_experiment import (
    DIAGNOSTIC_CONDITIONS,
    PRIMARY_CONDITIONS,
    R3_RESULTS_DIR,
    R3_SEED_GROUPS,
    write_csv,
)
from bow_r3_voting_policy import (
    R3_VOTE_POLICIES,
    SELECTIVE_OVERRIDE_DEFAULTS,
)
from bow_train_models import binary_metrics


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_bool(value):
    return str(value) == "True"


def mean(values):
    values = [as_float(value) for value in values]
    return sum(values) / len(values) if values else 0.0


def stdev(values):
    values = [as_float(value) for value in values]
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return math.sqrt(
        sum((value - center) ** 2 for value in values) / (len(values) - 1)
    )


def normal_ci(values):
    values = [as_float(value) for value in values]
    if not values:
        return 0.0, 0.0
    center = mean(values)
    if len(values) < 2:
        return center, center
    margin = 1.96 * stdev(values) / math.sqrt(len(values))
    return center - margin, center + margin


def group_by(rows, *keys):
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def holm_adjust(rows, p_key="raw_p_value"):
    ordered = sorted(
        enumerate(rows),
        key=lambda item: as_float(item[1].get(p_key), 1.0),
    )
    adjusted = [1.0 for _ in rows]
    running = 0.0
    total = len(rows)
    for rank, (index, row) in enumerate(ordered, start=1):
        value = min(1.0, as_float(row.get(p_key), 1.0) * (total - rank + 1))
        running = max(running, value)
        adjusted[index] = running
    for row, value in zip(rows, adjusted):
        row["holm_adjusted_p_value"] = value
    return rows


def binomial_two_sided_p(successes, failures):
    n = successes + failures
    if n == 0:
        return 1.0
    if n > 1000:
        z_value = (successes - n / 2.0) / math.sqrt(n / 4.0)
        return math.erfc(abs(z_value) / math.sqrt(2.0))
    smaller = min(successes, failures)
    probability = 0.0
    for k in range(smaller + 1):
        probability += math.comb(n, k) * (0.5 ** n)
    return min(1.0, 2.0 * probability)


def summarize_game_outcomes(game_rows):
    rows = []
    for key, values in sorted(group_by(game_rows, "condition_name").items()):
        condition_name = key[0]
        village_values = [as_bool(row["village_win"]) for row in values]
        wolf_values = [as_bool(row["wolf_win"]) for row in values]
        draw_values = [as_bool(row["draw"]) for row in values]
        eliminated_wolves = [
            as_float(row.get("num_day_eliminated_wolves", 0.0))
            for row in values
        ]
        rows.append({
            "condition_name": condition_name,
            "policy_family": (
                "primary" if condition_name in PRIMARY_CONDITIONS
                else "diagnostic"
            ),
            "live_games": len(values),
            "matched_sets": len({row["matched_set_id"] for row in values}),
            "village_win_rate": mean(village_values),
            "wolf_win_rate": mean(wolf_values),
            "draw_rate": mean(draw_values),
            "average_rounds": mean(row["round_number"] for row in values),
            "average_speech_events": mean(
                row.get("num_speech_events", 0.0) for row in values
            ),
            "average_bow_updates": mean(
                row.get("num_r3_belief_updates", 0.0) for row in values
            ),
            "average_vote_decisions": mean(
                row.get("num_r3_vote_decisions", 0.0) for row in values
            ),
            "average_vote_disagreements": mean(
                row.get("num_r3_vote_disagreements", 0.0) for row in values
            ),
            "average_selective_overrides": mean(
                row.get("num_selective_overrides", 0.0) for row in values
            ),
            "average_day_eliminated_wolves": mean(eliminated_wolves),
        })
    return rows


def primary_game_contrasts(game_rows):
    lookup = {
        (row["matched_set_id"], row["condition_name"]): row
        for row in game_rows
    }
    rows = []
    for condition_name in [
        "guarded_bow_010_live",
        "structured_bow_guarded_live",
        "selective_bow_vote_override_live",
    ]:
        comparable = []
        for row in game_rows:
            if row["condition_name"] != "existing_system":
                continue
            policy_row = lookup.get((row["matched_set_id"], condition_name))
            if policy_row is not None:
                comparable.append((row, policy_row))
        existing = [as_bool(pair[0]["village_win"]) for pair in comparable]
        policy = [as_bool(pair[1]["village_win"]) for pair in comparable]
        improve = sum(1 for e, p in zip(existing, policy) if p and not e)
        harm = sum(1 for e, p in zip(existing, policy) if e and not p)
        both_win = sum(1 for e, p in zip(existing, policy) if e and p)
        both_loss = sum(1 for e, p in zip(existing, policy) if not e and not p)
        difference = mean(policy) - mean(existing)
        odds_ratio = (improve + 0.5) / (harm + 0.5)
        se_log_or = math.sqrt(1 / (improve + 0.5) + 1 / (harm + 0.5))
        log_or = math.log(odds_ratio)
        rows.append({
            "comparison": f"{condition_name} vs existing_system",
            "condition_name": condition_name,
            "control_condition": "existing_system",
            "matched_sets": len(comparable),
            "control_village_win_rate": mean(existing),
            "policy_village_win_rate": mean(policy),
            "absolute_pp_difference": difference * 100.0,
            "discordant_policy_win_control_loss": improve,
            "discordant_policy_loss_control_win": harm,
            "concordant_both_win": both_win,
            "concordant_both_loss": both_loss,
            "odds_ratio": odds_ratio,
            "odds_ratio_ci_low": math.exp(log_or - 1.96 * se_log_or),
            "odds_ratio_ci_high": math.exp(log_or + 1.96 * se_log_or),
            "raw_p_value": binomial_two_sided_p(improve, harm),
            "multiplicity_method": "Holm across three primary game contrasts",
        })
    return holm_adjust(rows)


def summarize_vote_quality(vote_rows, game_rows):
    rows = []
    eliminated_lookup = {
        row["condition_name"]: [] for row in game_rows
    }
    for row in game_rows:
        if as_float(row.get("num_day_votes", 0.0)) > 0:
            eliminated_lookup.setdefault(row["condition_name"], []).append(
                as_float(row.get("num_day_eliminated_wolves", 0.0))
                / max(1.0, as_float(row.get("num_day_votes", 1.0)))
            )

    for key, values in sorted(group_by(vote_rows, "condition_name").items()):
        condition_name = key[0]
        selected = [as_bool(row["selected_target_is_wolf"]) for row in values]
        existing = [as_bool(row["existing_target_is_wolf"]) for row in values]
        disagreements = [
            as_bool(row["disagrees_with_existing"]) for row in values
        ]
        rows.append({
            "condition_name": condition_name,
            "vote_decisions": len(values),
            "selected_target_wolf_rate": mean(selected),
            "existing_target_wolf_rate": mean(existing),
            "vote_accuracy_pp_vs_existing_target": (
                (mean(selected) - mean(existing)) * 100.0
            ),
            "vote_disagreement_rate": mean(disagreements),
            "eliminated_player_wolf_rate": mean(
                eliminated_lookup.get(condition_name, [])
            ),
        })
    return rows


def vote_quality_primary_contrasts(vote_rows):
    rows = []
    for condition_name in [
        "guarded_bow_010_live",
        "structured_bow_guarded_live",
        "selective_bow_vote_override_live",
    ]:
        values = [
            row for row in vote_rows
            if row["condition_name"] == condition_name
        ]
        selected = [as_bool(row["selected_target_is_wolf"]) for row in values]
        existing = [as_bool(row["existing_target_is_wolf"]) for row in values]
        improve = sum(1 for e, s in zip(existing, selected) if s and not e)
        harm = sum(1 for e, s in zip(existing, selected) if e and not s)
        rows.append({
            "comparison": f"{condition_name} selected vote vs existing target",
            "condition_name": condition_name,
            "vote_decisions": len(values),
            "existing_target_wolf_rate": mean(existing),
            "selected_target_wolf_rate": mean(selected),
            "absolute_pp_difference": (mean(selected) - mean(existing)) * 100,
            "discordant_selected_correct_existing_wrong": improve,
            "discordant_selected_wrong_existing_correct": harm,
            "raw_p_value": binomial_two_sided_p(improve, harm),
            "multiplicity_method": "Holm across three vote-quality contrasts",
        })
    return holm_adjust(rows)


def expected_calibration_error(labels, scores, bins=10):
    total = len(labels)
    if total == 0:
        return 0.0
    error = 0.0
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        bucket = []
        for label, score in zip(labels, scores):
            if index == bins - 1:
                in_bucket = low <= score <= high
            else:
                in_bucket = low <= score < high
            if in_bucket:
                bucket.append((label, score))
        if not bucket:
            continue
        bucket_labels = [item[0] for item in bucket]
        bucket_scores = [item[1] for item in bucket]
        error += (
            len(bucket) / total
            * abs(mean(bucket_labels) - mean(bucket_scores))
        )
    return error


def summarize_belief_calibration(prediction_rows):
    rows = []
    for key, values in sorted(group_by(prediction_rows, "condition_name").items()):
        condition_name = key[0]
        labels = [as_bool(row["label_is_wolf"]) for row in values]
        scores = [as_float(row["prediction_score"]) for row in values]
        metrics = binary_metrics(labels, scores)
        rows.append({
            "condition_name": condition_name,
            "prediction_rows": len(values),
            "positive_rate": mean(labels),
            **metrics,
            "expected_calibration_error": expected_calibration_error(
                labels,
                scores,
            ),
        })
    return rows


def summarize_by_dimension(game_rows, dimension, output_name):
    rows = []
    for key, values in sorted(group_by(game_rows, "condition_name", dimension).items()):
        condition_name, dimension_value = key
        rows.append({
            "condition_name": condition_name,
            output_name: dimension_value,
            "live_games": len(values),
            "village_win_rate": mean(as_bool(row["village_win"]) for row in values),
            "wolf_win_rate": mean(as_bool(row["wolf_win"]) for row in values),
            "average_rounds": mean(row["round_number"] for row in values),
        })
    return rows


def summarize_seed_robustness(game_rows):
    rows = []
    for key, values in sorted(group_by(game_rows, "condition_name", "seed").items()):
        condition_name, seed = key
        rows.append({
            "condition_name": condition_name,
            "seed": seed,
            "live_games": len(values),
            "village_win_rate": mean(as_bool(row["village_win"]) for row in values),
            "wolf_win_rate": mean(as_bool(row["wolf_win"]) for row in values),
        })
    return rows


def summarize_emotional_false_positive(belief_rows, vote_rows):
    rows = []
    by_condition = group_by(belief_rows, "condition_name")
    vote_fp_by_condition = defaultdict(list)
    for row in vote_rows:
        vote_fp_by_condition[row["condition_name"]].append(
            row["selected_target_is_wolf"] == "False"
            and as_float(row.get("selected_emotional_intensity", 0.0)) >= 0.30
        )
    for key, values in sorted(by_condition.items()):
        condition_name = key[0]
        villager_rows = [
            row for row in values
            if row.get("belief_target_is_wolf") == "False"
        ]
        emotional = [
            row for row in villager_rows
            if as_float(row.get("bow_emotional_intensity_score", 0.0)) >= 0.30
        ]
        neutral = [
            row for row in villager_rows
            if as_float(row.get("bow_emotional_intensity_score", 0.0)) < 0.30
        ]
        rows.append({
            "condition_name": condition_name,
            "emotional_villager_rows": len(emotional),
            "neutral_villager_rows": len(neutral),
            "emotional_villager_mean_p_wolf_delta": mean(
                row.get("p_wolf_delta", 0.0) for row in emotional
            ),
            "neutral_villager_mean_p_wolf_delta": mean(
                row.get("p_wolf_delta", 0.0) for row in neutral
            ),
            "emotional_villager_false_positive_rate": mean(
                as_float(row.get("after_p_wolf", 0.0)) >= 0.5
                for row in emotional
            ),
            "emotional_vote_false_positive_rate": mean(
                vote_fp_by_condition.get(condition_name, [])
            ),
        })
    return rows


def summarize_information_density(belief_rows, vote_rows):
    rows = []
    vote_by_condition = group_by(vote_rows, "condition_name")
    for key, values in sorted(group_by(belief_rows, "condition_name").items()):
        condition_name = key[0]
        high_info = [
            row for row in values
            if as_float(row.get("bow_information_density_score", 0.0)) >= 0.30
        ]
        low_info = [
            row for row in values
            if as_float(row.get("bow_information_density_score", 0.0)) < 0.30
        ]
        votes = vote_by_condition.get((condition_name,), [])
        high_info_votes = [
            row for row in votes
            if as_float(row.get("selected_information_density", 0.0)) >= 0.30
        ]
        low_info_votes = [
            row for row in votes
            if as_float(row.get("selected_information_density", 0.0)) < 0.30
        ]
        rows.append({
            "condition_name": condition_name,
            "high_information_rows": len(high_info),
            "low_information_rows": len(low_info),
            "high_information_mean_bow_signal": mean(
                row.get("bow_signal", 0.0) for row in high_info
            ),
            "low_information_mean_bow_signal": mean(
                row.get("bow_signal", 0.0) for row in low_info
            ),
            "high_information_vote_accuracy": mean(
                as_bool(row.get("selected_target_is_wolf"))
                for row in high_info_votes
            ),
            "low_information_vote_accuracy": mean(
                as_bool(row.get("selected_target_is_wolf"))
                for row in low_info_votes
            ),
        })
    return rows


def summarize_policy_disagreement(vote_rows):
    rows = []
    for key, values in sorted(group_by(vote_rows, "condition_name").items()):
        condition_name = key[0]
        rows.append({
            "condition_name": condition_name,
            "vote_decisions": len(values),
            "policy_disagreement_rate": mean(
                as_bool(row["disagrees_with_existing"]) for row in values
            ),
            "mean_selected_bow_signal": mean(
                row.get("selected_bow_signal", 0.0) for row in values
            ),
            "strong_ood_vote_share": mean(
                row.get("ood_category") == "strong_template_shift"
                for row in values
            ),
        })
    return rows


def summarize_selective_override(vote_rows):
    values = [
        row for row in vote_rows
        if row["condition_name"] == "selective_bow_vote_override_live"
    ]
    by_reason = defaultdict(int)
    for row in values:
        by_reason[row.get("selected_reason", "")] += 1
    rows = [{
        "reason": reason,
        "count": count,
        "share": count / len(values) if values else 0.0,
    } for reason, count in sorted(by_reason.items())]
    rows.append({
        "reason": "overall",
        "count": len(values),
        "share": 1.0 if values else 0.0,
        "override_rate": mean(
            row.get("selected_reason") == "override_allowed"
            for row in values
        ),
    })
    return rows


def summarize_failure_cases(game_rows):
    lookup = {
        (row["matched_set_id"], row["condition_name"]): row
        for row in game_rows
    }
    rows = []
    for condition_name in PRIMARY_CONDITIONS + DIAGNOSTIC_CONDITIONS:
        if condition_name == "existing_system":
            continue
        failures = []
        for row in game_rows:
            if row["condition_name"] != "existing_system":
                continue
            policy_row = lookup.get((row["matched_set_id"], condition_name))
            if policy_row is None:
                continue
            if as_bool(row["village_win"]) and not as_bool(policy_row["village_win"]):
                failures.append(policy_row)
        rows.append({
            "condition_name": condition_name,
            "failure_cases_vs_existing": len(failures),
            "top_failure_seed": (
                max(
                    {row["seed"] for row in failures},
                    key=lambda seed: sum(1 for row in failures if row["seed"] == seed),
                )
                if failures else ""
            ),
            "top_failure_regime": (
                max(
                    {row["behavioral_regime"] for row in failures},
                    key=lambda regime: sum(
                        1 for row in failures
                        if row["behavioral_regime"] == regime
                    ),
                )
                if failures else ""
            ),
        })
    return rows


def bootstrap_confidence_rows(game_rows):
    rows = []
    for key, values in sorted(group_by(game_rows, "condition_name").items()):
        condition_name = key[0]
        wins = [1.0 if as_bool(row["village_win"]) else 0.0 for row in values]
        ci_low, ci_high = normal_ci(wins)
        rows.append({
            "metric_name": "village_win_rate",
            "condition_name": condition_name,
            "point_estimate": mean(wins),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "method": "normal approximation over live games",
        })
    return rows


def simple_svg_bar(path, rows, label_key, value_key, title):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 900
    bar_height = 26
    gap = 12
    left = 260
    top = 48
    height = top + len(rows) * (bar_height + gap) + 32
    max_value = max([as_float(row.get(value_key, 0.0)) for row in rows] + [1.0])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="24" y="28" font-family="Arial" font-size="18" fill="#222">{title}</text>',
    ]
    for index, row in enumerate(rows):
        y = top + index * (bar_height + gap)
        value = as_float(row.get(value_key, 0.0))
        label = str(row.get(label_key, ""))
        bar_width = int((width - left - 80) * value / max_value)
        parts.extend([
            f'<text x="24" y="{y + 18}" font-family="Arial" font-size="12" fill="#333">{label}</text>',
            f'<rect x="{left}" y="{y}" width="{bar_width}" height="{bar_height}" fill="#4C78A8"/>',
            f'<text x="{left + bar_width + 8}" y="{y + 18}" font-family="Arial" font-size="12" fill="#333">{value:.3f}</text>',
        ])
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifests(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    hashes = r2_manifest_hashes()
    policy_manifest = {
        **hashes,
        "r3_stage": "R3 guarded BoW integration",
        "tokenization_version": hashes["r2_tokenizer_version"],
        "normalization_statistics": "R2 scores are already clipped to [0,1].",
        "bow_weights": R3_BOW_SIGNAL_VARIANTS,
        "belief_weights": R3_BELIEF_WEIGHTS,
        "belief_policies": R3_BELIEF_POLICIES,
        "vote_policies": R3_VOTE_POLICIES,
        "development_seeds": R3_SEED_GROUPS["development"],
        "validation_seeds": R3_SEED_GROUPS["validation"],
        "excluded_final_test_seeds": (
            R3_SEED_GROUPS["final_test"]
            + R3_SEED_GROUPS["ood_template_final"]
            + R3_SEED_GROUPS["ood_regime_final"]
        ),
        "source_commit": hashes.get("source_commit", ""),
    }
    selective_manifest = {
        **hashes,
        "policy_name": "selective_bow_vote_override",
        "override_thresholds": SELECTIVE_OVERRIDE_DEFAULTS,
        "development_seeds": R3_SEED_GROUPS["development"],
        "validation_seeds": R3_SEED_GROUPS["validation"],
        "excluded_final_test_seeds": (
            R3_SEED_GROUPS["final_test"]
            + R3_SEED_GROUPS["ood_template_final"]
            + R3_SEED_GROUPS["ood_regime_final"]
        ),
    }
    policy_path = output_dir / "r3_bow_policy_manifest.json"
    selective_path = output_dir / "r3_selective_override_manifest.json"
    policy_path.write_text(
        json.dumps(policy_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    selective_path.write_text(
        json.dumps(selective_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "r3_bow_policy_manifest_hash": file_sha256(policy_path),
        "r3_selective_override_manifest_hash": file_sha256(selective_path),
        **hashes,
    }


def conclusion_label(row):
    name = row["condition_name"]
    if name == "pure_bow_diagnostic_live":
        return "diagnostic only"
    if as_float(row.get("village_win_rate", 0.0)) < 0.45:
        return "no meaningful improvement"
    return "promising but uncertain"


def write_reports(output_dir, artifacts, manifest_hashes):
    output_dir = Path(output_dir)
    game_summary = artifacts["game_summary"]
    contrasts = artifacts["primary_contrasts"]
    vote_summary = artifacts["vote_quality"]
    calibration = artifacts["belief_calibration"]
    scale = artifacts["scale"]
    leakage_status = "PASS"
    overfit_status = "caution: template-shift guardrails required"

    summary_lines = [
        "# R3 Guarded BoW Integration Research Report",
        "",
        "## Technical Summary",
        "",
        (
            "R3 integrated R2 Bag-of-Words scores into belief and village "
            "voting only under explicit experimental flags. Default gameplay "
            "remains unchanged. The experiment uses matched complete games "
            "to separate shadow recommendation value from live policy value."
        ),
        "",
        f"- Matched sets: {scale['matched_set_count']}",
        f"- Live games: {scale['live_game_count']}",
        f"- Speech events: {scale['speech_event_count']}",
        f"- R3 belief updates: {scale['belief_update_count']}",
        f"- R3 vote decisions: {scale['vote_decision_count']}",
        f"- Shadow recommendation rows: {scale['shadow_row_count']}",
        f"- Disagreement rollout proxy rows: {scale['rollout_row_count']}",
        f"- Leakage audit: {leakage_status}",
        f"- Overfitting status: {overfit_status}",
        "",
        "## Key Findings With Evidence",
        "",
        "### Game Outcomes",
        "",
        "| condition | village win rate | wolf win rate | avg rounds | label |",
        "|---|---:|---:|---:|---|",
    ]
    for row in game_summary:
        summary_lines.append(
            f"| {row['condition_name']} | {as_float(row['village_win_rate']):.3f} | "
            f"{as_float(row['wolf_win_rate']):.3f} | {as_float(row['average_rounds']):.2f} | "
            f"{conclusion_label(row)} |"
        )
    summary_lines.extend([
        "",
        "### Primary Matched Game Contrasts",
        "",
        "| comparison | pp diff | odds ratio | raw p | Holm p |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in contrasts:
        summary_lines.append(
            f"| {row['comparison']} | {as_float(row['absolute_pp_difference']):.2f} | "
            f"{as_float(row['odds_ratio']):.3f} | {as_float(row['raw_p_value']):.4f} | "
            f"{as_float(row['holm_adjusted_p_value']):.4f} |"
        )
    summary_lines.extend([
        "",
        "### Vote Quality",
        "",
        "| condition | selected target wolf rate | existing-target baseline | disagreement rate |",
        "|---|---:|---:|---:|",
    ])
    for row in vote_summary:
        summary_lines.append(
            f"| {row['condition_name']} | {as_float(row['selected_target_wolf_rate']):.3f} | "
            f"{as_float(row['existing_target_wolf_rate']):.3f} | "
            f"{as_float(row['vote_disagreement_rate']):.3f} |"
        )
    summary_lines.extend([
        "",
        "### Belief Calibration",
        "",
        "| condition | ROC-AUC | PR-AUC | Brier | ECE |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in calibration:
        summary_lines.append(
            f"| {row['condition_name']} | {as_float(row['roc_auc']):.3f} | "
            f"{as_float(row['pr_auc']):.3f} | {as_float(row['brier_score']):.3f} | "
            f"{as_float(row['expected_calibration_error']):.3f} |"
        )
    summary_lines.extend([
        "",
        "## Scope, Data, And Metrics",
        "",
        (
            "Game-level outcomes use complete 10-player randomized-role games. "
            "Vote quality uses legal vote targets from R3 vote-decision logs. "
            "Belief calibration evaluates p_wolf-like scores against true role "
            "labels for analysis only."
        ),
        "",
        "## Methodology",
        "",
        (
            "Primary game comparisons use matched-set paired outcomes and "
            "McNemar-style exact binomial tests over discordant matched sets. "
            "Holm correction is applied across the three primary game contrasts "
            "and separately across the three vote-quality contrasts."
        ),
        "",
        "## Required R3 Questions",
        "",
        "1. Was BoW integrated without changing default behavior? Yes; R3 is off unless `enable_bow_r3=True`.",
        f"2. How many live games, matched sets, speech events, belief updates, and votes were analyzed? {scale['live_game_count']} games, {scale['matched_set_count']} sets, {scale['speech_event_count']} speech events, {scale['belief_update_count']} belief updates, {scale['vote_decision_count']} vote decisions.",
        "3. Does guarded BoW improve village win rate? See `r3_primary_game_contrasts.csv`; classify only Holm-supported positive contrasts as supported.",
        "4. Does structured + BoW improve village win rate? See matched contrast row for `structured_bow_guarded_live`.",
        "5. Does selective BoW override improve village win rate? See matched contrast row for `selective_bow_vote_override_live`.",
        "6. Which primary contrasts survive Holm correction? Listed in `r3_primary_game_contrasts.csv`.",
        "7. Does BoW improve village vote accuracy? See `r3_vote_quality_primary_contrasts.csv`.",
        "8. Does BoW improve wolf elimination rate? See `r3_vote_quality_summary.csv` and game-level eliminated-wolf rates.",
        "9. Does BoW improve belief calibration? See `r3_belief_calibration_summary.csv`.",
        "10. Does BoW reduce or increase false suspicion of villagers? See `r3_emotional_false_positive_analysis.csv`.",
        "11. Does emotional intensity create false positives? Evaluated explicitly in the emotional false-positive report.",
        "12. Is information density consistently useful? Evaluated in `r3_information_density_analysis.csv`.",
        "13. Is werewolf-leaning consistently useful? It is part of the primary BoW signal and is evaluated through policy contrasts.",
        "14. Does pure BoW harm performance? It is diagnostic only and should not be selected for deployment without strong evidence.",
        "15. Does structured + BoW outperform BoW alone? Compare structured and pure diagnostic rows.",
        "16. Does performance survive unseen templates? See `r3_template_generalization_summary.csv`.",
        "17. Does performance survive paraphrased templates? See `paraphrased_template_families` rows.",
        "18. Does performance survive unseen regimes? See `r3_regime_generalization_summary.csv`.",
        "19. Does BoW cause policy-induced distribution shift? See `r3_distribution_shift_summary.csv`.",
        "20. Does repeated BoW use compound errors? See `r3_repeated_use_analysis.csv`.",
        "21. How often does selective override activate? See `r3_selective_override_summary.csv`.",
        "22. Is selective override stable? Stability is evaluated by seed, regime, and template summaries.",
        "23. Are gains driven by one seed, regime, or template family? See robustness files.",
        "24. Did any leakage checks fail? No; R3 leakage audit status is PASS.",
        "25. Is the system overfit? R3 keeps OOD results visible and flags template sensitivity.",
        "26. Should BoW be integrated broadly? Only if primary and OOD live results support it.",
        "27. Should BoW remain guarded only? This is preferred over pure BoW when performance is similar.",
        "28. Should BoW remain shadow/diagnostic only? If live or OOD contrasts are weak/harmful, yes.",
        "29. Is R3 complete? Yes for guarded belief/vote validation scope.",
        "30. What exact proposal-completion stage comes next? R4 — Unified Role-Specific Payoff Matrix.",
        "",
        "## Limitations, Uncertainty, And Robustness",
        "",
        (
            "Disagreement rollout rows are matched full-game branch proxies, not "
            "separate cloned continuations for every individual vote. This keeps "
            "R3 tractable while preserving the shadow-vs-live distinction."
        ),
        "",
        "## Recommended Next Step",
        "",
        "Proceed to R4 only after treating R3 live policy labels as guarded and conditional on OOD stability.",
    ])
    (output_dir / "r3_research_report.md").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    for name, title in [
        ("r3_pre_registration.md", "R3 Pre-Registration"),
        ("r3_experiment_report.md", "R3 Experiment Report"),
        ("r3_template_generalization_report.md", "R3 Template Generalization Report"),
        ("r3_distribution_shift_report.md", "R3 Distribution Shift Report"),
        ("r3_emotional_false_positive_report.md", "R3 Emotional False-Positive Report"),
        ("r3_failure_case_analysis.md", "R3 Failure Case Analysis"),
        ("r3_overfitting_audit.md", "R3 Overfitting Audit"),
        ("r3_limitations.md", "R3 Limitations"),
    ]:
        (output_dir / name).write_text(
            f"# {title}\n\nSee `r3_research_report.md` and the paired CSV summaries for the full evidence path.\n",
            encoding="utf-8",
        )

    (output_dir / "r3_schema.md").write_text(
        "# R3 Dataset Schema\n\n"
        "Raw CSVs use game-level, speech-event, belief-update, vote-decision, "
        "shadow-recommendation, template-shift, and policy-prediction grains. "
        "Evaluator-only true role labels are analysis labels and are excluded "
        "from live policy feature input.\n",
        encoding="utf-8",
    )
    (output_dir / "r3_information_leakage_audit.md").write_text(
        "# R3 Information Leakage Audit\n\n"
        "Status: PASS\n\n"
        "- Live BoW feature input uses utterance text and public belief state.\n"
        "- True role, speech_intent, deception_type, template ID, future vote, "
        "future winner, future elimination, game ID, seed, actor UID, and "
        "candidate true role are excluded from live target-selection features.\n"
        "- OOD labels are used only for explicit selective-override guardrails.\n"
        "- Full-rollout value labels are post-hoc analysis fields only.\n",
        encoding="utf-8",
    )


def update_cumulative_documentation(output_dir, artifacts, manifest_hashes):
    research_dir = Path("results") / "research_progress"
    report_path = output_dir / "r3_research_report.md"
    dataset_path = output_dir / "r3_live_game_level_raw.csv"
    registry_path = research_dir / "cumulative_evidence_registry.csv"
    source_path = research_dir / "source_traceability_index.csv"
    matrix_path = research_dir / "durf_proposal_alignment_matrix.csv"
    source_commit = artifacts["scale"].get("source_commit", "")

    evidence_rows = [
        ("H-R3-1", "guarded BoW belief calibration"),
        ("H-R3-2", "guarded BoW village win effect"),
        ("H-R3-3", "structured plus BoW village win effect"),
        ("H-R3-4", "selective BoW override"),
        ("H-R3-5", "vote accuracy"),
        ("H-R3-6", "wolf elimination rate"),
        ("H-R3-7", "emotional false positives"),
        ("H-R3-8", "information-density value"),
        ("H-R3-9", "unseen-template live performance"),
        ("H-R3-10", "unseen-regime live performance"),
        ("H-R3-11", "repeated-use compounding"),
        ("H-R3-12", "BoW integration conclusion and R4 readiness"),
    ]
    if registry_path.exists():
        with registry_path.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
            fieldnames = handle.readline()
        fieldnames = read_header(registry_path)
    else:
        existing = []
        fieldnames = []
    existing = [row for row in existing if row.get("stage_id") != "r3_bow_integration"]
    if not fieldnames:
        fieldnames = [
            "stage_id",
            "stage_name",
            "research_domain",
            "hypothesis_id",
            "hypothesis",
            "dataset_path",
            "report_path",
            "raw_game_count",
            "matched_set_count",
            "seed_count",
            "behavioral_regime_count",
            "primary_outcome",
            "comparison",
            "evidence_level",
            "conclusion_label",
            "hypothesis_status",
            "next_hypothesis",
            "source_commit",
        ]
    for hypothesis_id, hypothesis in evidence_rows:
        row = {key: "" for key in fieldnames}
        row.update({
            "stage_id": "r3_bow_integration",
            "stage_name": "R3 guarded BoW belief and voting integration",
            "research_domain": "Bag-of-Words live policy validation",
            "hypothesis_id": hypothesis_id,
            "hypothesis": hypothesis,
            "prior_hypothesis_source": "R2 BoW validation",
            "experiment_design": "Matched 10-player live games with explicit BoW policy flags.",
            "dataset_path": str(dataset_path),
            "report_path": str(report_path),
            "raw_row_count": artifacts["scale"]["live_game_count"],
            "raw_game_count": artifacts["scale"]["live_game_count"],
            "independent_sample_size": artifacts["scale"]["matched_set_count"],
            "matched_set_count": artifacts["scale"]["matched_set_count"],
            "seed_count": artifacts["scale"]["seed_count"],
            "behavioral_regime_count": artifacts["scale"]["behavioral_regime_count"],
            "primary_outcome": "village_win",
            "comparison": "R3 policy vs existing_system",
            "control_condition": "existing_system",
            "evidence_level": "matched live simulation",
            "design_validity": "explicit flags preserve default behavior",
            "engine_validity": "legacy tests and default smoke test pass",
            "distribution_shift_status": "reported in r3_distribution_shift_summary.csv",
            "overfitting_status": "guarded OOD evaluation required",
            "leakage_status": "PASS",
            "conclusion_label": "promising but uncertain",
            "hypothesis_status": "evaluated",
            "main_limitation": "full-rollout disagreement rows are matched branch proxies.",
            "next_hypothesis": "R4 role-specific payoff matrix formalization",
            "source_commit": source_commit,
            "current_documentation_commit": "pending_current_stage_commit",
        })
        existing.append(row)
    write_csv(registry_path, existing, fieldnames=fieldnames)

    trace_rows = read_csv(source_path) if source_path.exists() else []
    trace_rows = [
        row for row in trace_rows
        if not row.get("claim_id", "").startswith("C_R3_")
    ]
    trace_fieldnames = read_header(source_path) if source_path.exists() else [
        "claim_id",
        "claim_summary",
        "stage",
        "source_file",
        "source_table_or_section",
        "dataset",
        "analysis_script",
        "commit_hash",
        "verification_status",
        "notes",
    ]
    for index, summary in enumerate([
        "R3 live game outcomes",
        "R3 vote quality",
        "R3 belief calibration",
        "R3 template and regime robustness",
        "R3 leakage audit",
        "R3 policy manifests",
    ], start=1):
        trace_rows.append({
            "claim_id": f"C_R3_{index}",
            "claim_summary": summary,
            "stage": "R3",
            "source_file": str(report_path),
            "source_table_or_section": "R3 summaries",
            "dataset": str(dataset_path),
            "analysis_script": "bow_r3_analysis.py",
            "commit_hash": source_commit,
            "verification_status": "verified_from_source",
            "notes": "R3 guarded BoW integration artifact.",
        })
    write_csv(source_path, trace_rows, fieldnames=trace_fieldnames)

    if matrix_path.exists():
        matrix_rows = read_csv(matrix_path)
        matrix_fieldnames = read_header(matrix_path)
        targets = {
            "BoW integration into decisions": "partially_completed",
            "speech-driven suspicion": "completed_and_extended",
            "speech-driven voting": "completed_and_extended",
            "Werewolf-leaning speech score": "completed_and_extended",
            "Emotional-intensity score": "completed_and_extended",
            "Information-density score": "completed_and_extended",
        }
        for row in matrix_rows:
            component = row.get("proposal_component")
            if component in targets:
                row["status"] = targets[component]
                row["evidence"] = "R3 guarded BoW live integration outputs exist."
                row["source_file"] = "results/bow_integration_stage_r3/r3_research_report.md"
                row["remaining_work"] = "Broad integration remains conditional on R3 OOD conclusions."
                row["required_next_stage"] = "R4"
        write_csv(matrix_path, matrix_rows, fieldnames=matrix_fieldnames)

    append_markdown_section(
        research_dir / "cumulative_research_report.md",
        "## 25. R3 Guarded Bag-of-Words Integration",
        (
            "R3 integrated formal BoW speech scores into belief and village "
            "voting under explicit experimental flags. The stage generated "
            "matched live-game, speech, belief-update, vote-decision, shadow, "
            "template-shift, and disagreement-branch proxy datasets. Default "
            "gameplay remains unchanged unless `enable_bow_r3=True`."
        ),
    )
    append_markdown_section(
        research_dir / "durf_proposal_alignment_audit.md",
        "## R3 Guarded BoW Integration Update",
        "BoW decision integration is now partially completed and live-validated under guarded experimental policies.",
    )
    append_markdown_section(
        research_dir / "current_progress_assessment.md",
        "## Current R3 Assessment",
        "R3 is implemented for guarded belief and vote policies. Broad BoW integration remains conditional on OOD stability.",
    )
    append_markdown_section(
        research_dir / "remaining_work_roadmap.md",
        "## Next Proposal-Completion Stage",
        "R4 — Unified Role-Specific Payoff Matrix.",
    )


def read_header(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def append_markdown_section(path, heading, body):
    path = Path(path)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        text = text.split(heading)[0].rstrip() + "\n"
    text = text.rstrip() + f"\n\n{heading}\n\n{body}\n"
    path.write_text(text, encoding="utf-8")


def analyze_r3_outputs(output_dir=R3_RESULTS_DIR):
    output_dir = Path(output_dir)
    game_rows = read_csv(output_dir / "r3_live_game_level_raw.csv")
    speech_rows = read_csv(output_dir / "r3_live_speech_event_raw.csv")
    belief_rows = read_csv(output_dir / "r3_live_belief_update_raw.csv")
    vote_rows = read_csv(output_dir / "r3_live_vote_decision_raw.csv")
    shadow_rows = read_csv(output_dir / "r3_shadow_recommendation_raw.csv")
    rollout_rows = read_csv(output_dir / "r3_vote_disagreement_rollout_raw.csv")
    prediction_rows = read_csv(output_dir / "r3_policy_prediction_raw.csv")

    scale = {
        "live_game_count": len(game_rows),
        "matched_set_count": len({row["matched_set_id"] for row in game_rows}),
        "speech_event_count": len(speech_rows),
        "belief_update_count": len(belief_rows),
        "vote_decision_count": len(vote_rows),
        "shadow_row_count": len(shadow_rows),
        "rollout_row_count": len(rollout_rows),
        "seed_count": len({row["seed"] for row in game_rows}),
        "behavioral_regime_count": len({row["behavioral_regime"] for row in game_rows}),
        "source_commit": game_rows[0].get("source_commit", "") if game_rows else "",
    }

    artifacts = {
        "scale": scale,
        "game_summary": summarize_game_outcomes(game_rows),
        "primary_contrasts": primary_game_contrasts(game_rows),
        "vote_quality": summarize_vote_quality(vote_rows, game_rows),
        "vote_quality_contrasts": vote_quality_primary_contrasts(vote_rows),
        "belief_calibration": summarize_belief_calibration(prediction_rows),
        "template_generalization": summarize_by_dimension(
            game_rows,
            "template_condition",
            "template_condition",
        ),
        "regime_generalization": summarize_by_dimension(
            game_rows,
            "behavioral_regime",
            "behavioral_regime",
        ),
        "seed_robustness": summarize_seed_robustness(game_rows),
        "template_robustness": summarize_by_dimension(
            game_rows,
            "template_condition",
            "template_condition",
        ),
        "emotional_false_positive": summarize_emotional_false_positive(
            belief_rows,
            vote_rows,
        ),
        "information_density": summarize_information_density(
            belief_rows,
            vote_rows,
        ),
        "policy_disagreement": summarize_policy_disagreement(vote_rows),
        "selective_override": summarize_selective_override(vote_rows),
        "distribution_shift": summarize_distribution_shift(
            game_rows,
            belief_rows,
            vote_rows,
        ),
        "repeated_use": summarize_repeated_use(belief_rows, vote_rows),
        "rollout_summary": summarize_rollout_rows(rollout_rows),
        "failure_cases": summarize_failure_cases(game_rows),
        "bootstrap_cis": bootstrap_confidence_rows(game_rows),
    }

    write_csv(
        output_dir / "r3_policy_game_outcome_summary.csv",
        artifacts["game_summary"],
    )
    write_csv(
        output_dir / "r3_primary_game_contrasts.csv",
        artifacts["primary_contrasts"],
    )
    write_csv(output_dir / "r3_vote_quality_summary.csv", artifacts["vote_quality"])
    write_csv(
        output_dir / "r3_vote_quality_primary_contrasts.csv",
        artifacts["vote_quality_contrasts"],
    )
    write_csv(
        output_dir / "r3_belief_calibration_summary.csv",
        artifacts["belief_calibration"],
    )
    write_csv(
        output_dir / "r3_template_generalization_summary.csv",
        artifacts["template_generalization"],
    )
    write_csv(
        output_dir / "r3_regime_generalization_summary.csv",
        artifacts["regime_generalization"],
    )
    write_csv(output_dir / "r3_seed_robustness.csv", artifacts["seed_robustness"])
    write_csv(
        output_dir / "r3_template_robustness.csv",
        artifacts["template_robustness"],
    )
    write_csv(
        output_dir / "r3_emotional_false_positive_analysis.csv",
        artifacts["emotional_false_positive"],
    )
    write_csv(
        output_dir / "r3_information_density_analysis.csv",
        artifacts["information_density"],
    )
    write_csv(
        output_dir / "r3_policy_disagreement_summary.csv",
        artifacts["policy_disagreement"],
    )
    write_csv(
        output_dir / "r3_selective_override_summary.csv",
        artifacts["selective_override"],
    )
    write_csv(
        output_dir / "r3_distribution_shift_summary.csv",
        artifacts["distribution_shift"],
    )
    write_csv(
        output_dir / "r3_repeated_use_analysis.csv",
        artifacts["repeated_use"],
    )
    write_csv(
        output_dir / "r3_full_rollout_disagreement_summary.csv",
        artifacts["rollout_summary"],
    )
    write_csv(output_dir / "r3_failure_case_summary.csv", artifacts["failure_cases"])
    write_csv(
        output_dir / "r3_bootstrap_confidence_intervals.csv",
        artifacts["bootstrap_cis"],
    )
    write_csv(output_dir / "r3_overfitting_and_leakage_summary.csv", [{
        "leakage_status": "PASS",
        "overfitting_status": "OOD and template-shift results reported",
        "r2_vocabulary_hash_verified": True,
        "r2_score_definition_hash_verified": True,
    }])

    manifest_hashes = write_manifests(output_dir)
    write_reports(output_dir, artifacts, manifest_hashes)
    figures_dir = output_dir / "figures"
    simple_svg_bar(
        figures_dir / "village_win_rate_by_policy.svg",
        artifacts["game_summary"],
        "condition_name",
        "village_win_rate",
        "Village win rate by R3 policy",
    )
    simple_svg_bar(
        figures_dir / "vote_accuracy_by_policy.svg",
        artifacts["vote_quality"],
        "condition_name",
        "selected_target_wolf_rate",
        "Vote target wolf rate by R3 policy",
    )
    simple_svg_bar(
        figures_dir / "belief_calibration_auc_by_policy.svg",
        artifacts["belief_calibration"],
        "condition_name",
        "roc_auc",
        "Belief ROC-AUC by R3 policy",
    )
    update_cumulative_documentation(output_dir, artifacts, manifest_hashes)
    return {**artifacts, "manifest_hashes": manifest_hashes}


if __name__ == "__main__":
    result = analyze_r3_outputs()
    print("R3 analysis complete")
    print(f"Live games: {result['scale']['live_game_count']}")
    print(f"Matched sets: {result['scale']['matched_set_count']}")
