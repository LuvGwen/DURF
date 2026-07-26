import csv
import math
from collections import defaultdict

from ml_distribution_shift import summarize_shift_rows
from ml_feature_registry import FEATURE_COLUMNS
from ml_train_baselines import (
    as_float,
    fit_ridge_regression,
    mae,
    predict_ridge,
    rmse,
)
from ml_wolf_kill_model_freeze import STAGE15_WOLF_DATASET, read_csv_rows
from ml_wolf_kill_policy import PRIMARY_WOLF_KILL_POLICIES


PRIMARY_CONTRAST_POLICIES = [
    "frozen_ml",
    "frozen_hybrid_50_50",
    "frozen_ml_epsilon_010",
]


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            restval="",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def mean(values):
    values = [float(value) for value in values]
    return sum(values) / len(values) if values else 0.0


def stdev(values):
    values = [float(value) for value in values]
    if len(values) < 2:
        return 0.0
    value_mean = mean(values)
    return math.sqrt(
        sum((value - value_mean) ** 2 for value in values)
        / (len(values) - 1)
    )


def normal_ci(rate, n):
    if n <= 0:
        return 0.0, 0.0
    se = math.sqrt(rate * (1.0 - rate) / n)
    return rate - 1.96 * se, rate + 1.96 * se


def binom_two_sided_p(discordant_a, discordant_b):
    n = discordant_a + discordant_b
    if n == 0:
        return 1.0
    k = min(discordant_a, discordant_b)
    probability = 0.0
    for i in range(k + 1):
        probability += math.comb(n, i) * (0.5 ** n)
    return min(1.0, 2.0 * probability)


def holm_adjust(rows, p_key="raw_p_value"):
    ordered = sorted(
        enumerate(rows),
        key=lambda item: as_float(item[1].get(p_key), 1.0),
    )
    adjusted = [1.0 for _ in rows]
    m = len(rows)
    running_max = 0.0
    for rank, (index, row) in enumerate(ordered, start=1):
        raw = as_float(row.get(p_key), 1.0)
        value = min(1.0, raw * (m - rank + 1))
        running_max = max(running_max, value)
        adjusted[index] = running_max
    for row, adjusted_value in zip(rows, adjusted):
        row["holm_adjusted_p_value"] = adjusted_value
    return rows


def summarize_live_policies(game_rows):
    grouped = defaultdict(list)
    for row in game_rows:
        grouped[row["policy_name"]].append(row)
    output = []
    for policy_name in PRIMARY_WOLF_KILL_POLICIES:
        rows = grouped.get(policy_name, [])
        wolf_rate = mean(row["wolf_win"] for row in rows) if rows else 0.0
        lower, upper = normal_ci(wolf_rate, len(rows))
        output.append({
            "policy_name": policy_name,
            "games": len(rows),
            "wolf_wins": sum(int(row["wolf_win"]) for row in rows),
            "village_wins": sum(int(row["village_win"]) for row in rows),
            "draws": sum(int(row["draw"]) for row in rows),
            "wolf_win_rate": wolf_rate,
            "wolf_win_ci_low": lower,
            "wolf_win_ci_high": upper,
            "village_win_rate": (
                mean(row["village_win"] for row in rows) if rows else 0.0
            ),
            "avg_rounds": (
                mean(row["round_number"] for row in rows) if rows else 0.0
            ),
            "avg_successful_night_kills": mean(
                row["successful_night_kills"] for row in rows
            ) if rows else 0.0,
            "avg_special_role_kills": mean(
                row["special_role_kills"] for row in rows
            ) if rows else 0.0,
        })
    return output


def matched_primary_contrasts(game_rows):
    by_match_policy = {
        (row["matched_set_id"], row["policy_name"]): row
        for row in game_rows
    }
    matched_set_ids = sorted({
        row["matched_set_id"] for row in game_rows
    })
    rows = []
    for policy_name in PRIMARY_CONTRAST_POLICIES:
        diffs = []
        policy_wins_existing_losses = 0
        policy_losses_existing_wins = 0
        both_win = 0
        both_loss = 0
        for matched_set_id in matched_set_ids:
            existing = by_match_policy.get((matched_set_id, "existing_rule"))
            policy = by_match_policy.get((matched_set_id, policy_name))
            if existing is None or policy is None:
                continue
            existing_win = int(existing["wolf_win"])
            policy_win = int(policy["wolf_win"])
            diffs.append(policy_win - existing_win)
            if policy_win == 1 and existing_win == 0:
                policy_wins_existing_losses += 1
            elif policy_win == 0 and existing_win == 1:
                policy_losses_existing_wins += 1
            elif policy_win == 1 and existing_win == 1:
                both_win += 1
            else:
                both_loss += 1
        effect = mean(diffs) if diffs else 0.0
        se = stdev(diffs) / math.sqrt(len(diffs)) if len(diffs) > 1 else 0.0
        raw_p = binom_two_sided_p(
            policy_wins_existing_losses,
            policy_losses_existing_wins,
        )
        odds_ratio = (
            (policy_wins_existing_losses + 0.5)
            / (policy_losses_existing_wins + 0.5)
        )
        rows.append({
            "contrast": f"{policy_name}_vs_existing_rule",
            "policy_name": policy_name,
            "matched_sets": len(diffs),
            "existing_rule_wolf_win_rate": mean(
                by_match_policy[(mid, "existing_rule")]["wolf_win"]
                for mid in matched_set_ids
                if (mid, "existing_rule") in by_match_policy
                and (mid, policy_name) in by_match_policy
            ),
            "policy_wolf_win_rate": mean(
                by_match_policy[(mid, policy_name)]["wolf_win"]
                for mid in matched_set_ids
                if (mid, "existing_rule") in by_match_policy
                and (mid, policy_name) in by_match_policy
            ),
            "absolute_difference": effect,
            "difference_ci_low": effect - 1.96 * se,
            "difference_ci_high": effect + 1.96 * se,
            "discordant_policy_win_existing_loss": (
                policy_wins_existing_losses
            ),
            "discordant_policy_loss_existing_win": (
                policy_losses_existing_wins
            ),
            "both_win": both_win,
            "both_loss": both_loss,
            "odds_ratio_discordant": odds_ratio,
            "raw_p_value": raw_p,
        })
    return holm_adjust(rows)


def matched_pair_rows(primary_rows):
    return [
        {
            "contrast": row["contrast"],
            "matched_sets": row["matched_sets"],
            "policy_win_existing_loss": row[
                "discordant_policy_win_existing_loss"
            ],
            "policy_loss_existing_win": row[
                "discordant_policy_loss_existing_win"
            ],
            "both_win": row["both_win"],
            "both_loss": row["both_loss"],
            "odds_ratio_discordant": row["odds_ratio_discordant"],
            "raw_p_value": row["raw_p_value"],
            "holm_adjusted_p_value": row["holm_adjusted_p_value"],
        }
        for row in primary_rows
    ]


def robustness_by_field(game_rows, field):
    grouped = defaultdict(list)
    for row in game_rows:
        grouped[(row[field], row["policy_name"])].append(row)
    output = []
    for (value, policy_name), rows in sorted(grouped.items()):
        output.append({
            field: value,
            "policy_name": policy_name,
            "games": len(rows),
            "wolf_win_rate": mean(row["wolf_win"] for row in rows),
            "avg_rounds": mean(row["round_number"] for row in rows),
            "avg_successful_night_kills": mean(
                row["successful_night_kills"] for row in rows
            ),
        })
    return output


def secondary_outcomes(game_rows):
    grouped = defaultdict(list)
    for row in game_rows:
        grouped[row["policy_name"]].append(row)
    output = []
    for policy_name, rows in sorted(grouped.items()):
        attempts = sum(int(row["night_kill_attempts"]) for row in rows)
        output.append({
            "policy_name": policy_name,
            "games": len(rows),
            "avg_total_rounds": mean(row["total_rounds"] for row in rows),
            "successful_night_kill_rate": (
                sum(int(row["successful_night_kills"]) for row in rows)
                / attempts if attempts else 0.0
            ),
            "special_role_kill_rate": (
                sum(int(row["special_role_kills"]) for row in rows)
                / attempts if attempts else 0.0
            ),
            "seer_kill_rate": (
                sum(int(row["seer_kills"]) for row in rows) / attempts
                if attempts else 0.0
            ),
            "witch_kill_rate": (
                sum(int(row["witch_kills"]) for row in rows) / attempts
                if attempts else 0.0
            ),
            "hunter_kill_rate": (
                sum(int(row["hunter_kills"]) for row in rows) / attempts
                if attempts else 0.0
            ),
            "witch_save_rate": (
                sum(int(row["witch_saves"]) for row in rows) / attempts
                if attempts else 0.0
            ),
            "hunter_retaliation_rate": (
                sum(int(row["hunter_retaliations"]) for row in rows)
                / attempts if attempts else 0.0
            ),
            "avg_wolf_survival_count": mean(
                row["wolf_survival_count"] for row in rows
            ),
            "avg_vote_control_proxy": mean(
                row["vote_control_proxy"] for row in rows
            ),
        })
    return output


def policy_agreement(decision_rows):
    grouped = defaultdict(list)
    for row in decision_rows:
        grouped[row["policy_name"]].append(row)
    output = []
    for policy_name, rows in sorted(grouped.items()):
        output.append({
            "policy_name": policy_name,
            "decision_rows": len(rows),
            "ml_existing_agreement_rate": mean(
                row["ml_existing_agree"] for row in rows
            ) if rows else 0.0,
            "hybrid_existing_agreement_rate": mean(
                row["hybrid_existing_agree"] for row in rows
            ) if rows else 0.0,
            "ml_hybrid_agreement_rate": mean(
                row["ml_hybrid_agree"] for row in rows
            ) if rows else 0.0,
            "low_margin_rate": mean(
                1 if as_float(row["top_two_predicted_value_margin"]) < 0.02
                else 0
                for row in rows
            ) if rows else 0.0,
            "avg_legal_candidates": mean(
                row["number_of_legal_candidates"] for row in rows
            ) if rows else 0.0,
        })
    return output


def distribution_shift_summary(shift_rows):
    rows = summarize_shift_rows(shift_rows)
    by_policy_category = defaultdict(list)
    for row in shift_rows:
        by_policy_category[
            (row["policy_name"], row.get("candidate_distribution_shift_category", "unknown"))
        ].append(row)
    for (policy_name, category), category_rows in sorted(by_policy_category.items()):
        rows.append({
            "distribution_shift_category": f"{policy_name}:{category}",
            "rows": len(category_rows),
            "wolf_win_rate": mean(row["wolf_win"] for row in category_rows),
            "avg_standardized_feature_distance": mean(
                row["standardized_feature_distance"] for row in category_rows
            ),
            "avg_max_abs_z": mean(
                row["maximum_absolute_z_score"] for row in category_rows
            ),
            "avg_fraction_outside_training_minmax": mean(
                row["fraction_features_outside_training_minmax"]
                for row in category_rows
            ),
            "avg_prediction_extremity": mean(
                row["prediction_extremity"] for row in category_rows
            ),
        })
    return rows


def feature_coefficients(manifest):
    rows = []
    ranges = manifest.get("training_feature_ranges", {})
    for feature, coefficient in zip(
        manifest["feature_order"],
        manifest["coefficients"],
    ):
        if coefficient > 0:
            sign = "pushes_toward_kill"
        elif coefficient < 0:
            sign = "pushes_away_from_kill"
        else:
            sign = "neutral"
        rows.append({
            "feature": feature,
            "coefficient": coefficient,
            "standardized_coefficient_magnitude": abs(coefficient),
            "coefficient_sign": sign,
            "training_min": ranges.get(feature, {}).get("min", 0.0),
            "training_max": ranges.get(feature, {}).get("max", 0.0),
            "training_missing_count": ranges.get(feature, {}).get(
                "missing_count",
                0,
            ),
            "strategic_interpretation": interpret_feature(feature, sign),
        })
    return sorted(
        rows,
        key=lambda row: row["standardized_coefficient_magnitude"],
        reverse=True,
    )


def interpret_feature(feature, sign):
    if "suspicion" in feature or "p_wolf" in feature:
        family = "risk/suspicion signal"
    elif "trust" in feature or "support" in feature or "conflict" in feature:
        family = "relationship or trust signal"
    elif "vote" in feature:
        family = "voting-history signal"
    elif "seat" in feature or "side" in feature or "distance" in feature:
        family = "position signal"
    elif "speech" in feature or "accus" in feature or "defense" in feature:
        family = "speech and accusation signal"
    elif "survival" in feature or "alive" in feature:
        family = "survival/game-state signal"
    else:
        family = "general public feature"
    return f"{family}; {sign}; not a causal interpretation"


def feature_stability_rows(manifest):
    return [
        {
            "feature": feature,
            "coefficient": coefficient,
            "stability_method": "single frozen Stage 1.5 train split",
            "coefficient_stdev_across_development_folds": "NA",
            "stability_note": (
                "Stage 2A did not refit the primary frozen model; "
                "fold stability is deferred to a larger follow-up."
            ),
        }
        for feature, coefficient in zip(
            manifest["feature_order"],
            manifest["coefficients"],
        )
    ]


def ablation_diagnostics():
    rows = read_csv_rows(STAGE15_WOLF_DATASET)
    train_rows = [row for row in rows if row.get("split_name") == "train"]
    final_rows = [row for row in rows if row.get("split_name") == "final_test"]
    ablations = {
        "full_feature_set": list(FEATURE_COLUMNS),
        "remove_physical_position_features": [
            feature for feature in FEATURE_COLUMNS
            if not any(token in feature for token in ["seat", "side", "distance"])
        ],
        "remove_identifier_like_features": [
            feature for feature in FEATURE_COLUMNS
            if "uid" not in feature and "id" not in feature
        ],
        "remove_role_probability_features": [
            feature for feature in FEATURE_COLUMNS
            if "p_wolf" not in feature and "known_wolf" not in feature
        ],
        "remove_influence_features": [
            feature for feature in FEATURE_COLUMNS
            if "influence" not in feature and "vote" not in feature
        ],
        "remove_suspicion_features": [
            feature for feature in FEATURE_COLUMNS
            if "suspicion" not in feature
        ],
        "remove_trust_features": [
            feature for feature in FEATURE_COLUMNS
            if "trust" not in feature and "support" not in feature
        ],
    }
    output = []
    actual = [
        as_float(row["full_rollout_mean_team_win_rate"])
        for row in final_rows
    ]
    for name, features in ablations.items():
        model = fit_ridge_regression(
            train_rows,
            "full_rollout_mean_team_win_rate",
            feature_columns=features,
        )
        predictions = predict_ridge(model, final_rows)
        output.append({
            "ablation": name,
            "feature_count": len(features),
            "final_test_rmse": rmse(actual, predictions),
            "final_test_mae": mae(actual, predictions),
            "diagnostic_only": 1,
        })
    return output


def overfitting_diagnostics(shadow_summary, live_summary):
    shadow_by_policy = {
        row["policy_name"]: row for row in shadow_summary
    }
    live_by_policy = {
        row["policy_name"]: row for row in live_summary
    }
    existing_live = live_by_policy.get("existing_rule", {})
    output = []
    for policy_name in PRIMARY_CONTRAST_POLICIES:
        shadow = shadow_by_policy.get(policy_name, {})
        live = live_by_policy.get(policy_name, {})
        shadow_gain = as_float(
            shadow.get("mean_improvement_over_existing"),
            0.0,
        )
        live_gain = (
            as_float(live.get("wolf_win_rate"), 0.0)
            - as_float(existing_live.get("wolf_win_rate"), 0.0)
        )
        output.append({
            "policy_name": policy_name,
            "shadow_improvement": shadow_gain,
            "live_wolf_win_difference": live_gain,
            "shadow_live_gap": shadow_gain - live_gain,
            "overfitting_flag": 1 if shadow_gain - live_gain > 0.10 else 0,
            "classification": (
                "possible shadow overfit"
                if shadow_gain - live_gain > 0.10
                else "live harmful in this pilot"
                if live_gain < 0.0
                else "promising but uncertain"
            ),
        })
    return output


def failure_cases(game_rows, decision_rows):
    existing_by_match = {
        row["matched_set_id"]: row
        for row in game_rows
        if row["policy_name"] == "existing_rule"
    }
    rows = []
    for row in decision_rows:
        if row["policy_name"] == "existing_rule":
            continue
        existing = existing_by_match.get(row["matched_set_id"])
        if existing is None:
            continue
        if (
            int(existing["wolf_win"]) == 1
            and int(row["wolf_win"]) == 0
        ) or row["distribution_shift_category"] == "strong_shift":
            rows.append({
                "matched_set_id": row["matched_set_id"],
                "policy_name": row["policy_name"],
                "seed": row["seed"],
                "behavioral_regime_id": row["behavioral_regime_id"],
                "round": row["round"],
                "selected_target": row["selected_target"],
                "selected_target_role": row["selected_target_role"],
                "existing_rule_target": row["existing_rule_target"],
                "distribution_shift_category": row[
                    "distribution_shift_category"
                ],
                "top_two_predicted_value_margin": row[
                    "top_two_predicted_value_margin"
                ],
                "failure_reason": (
                    "policy_lost_existing_won"
                    if int(existing["wolf_win"]) == 1
                    and int(row["wolf_win"]) == 0
                    else "strong_distribution_shift"
                ),
            })
    return rows[:200]


def write_svg_bar_chart(path, rows, value_field, label_field, title):
    width = 760
    height = 360
    margin_left = 180
    margin_bottom = 60
    plot_width = width - margin_left - 40
    plot_height = height - 80
    max_value = max([as_float(row[value_field]) for row in rows] + [1.0])
    bar_height = plot_height / max(1, len(rows))
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="20" y="30" font-family="Arial" font-size="18" font-weight="bold">{title}</text>',
    ]
    for index, row in enumerate(rows):
        y = 55 + index * bar_height
        value = as_float(row[value_field])
        bar_width = (value / max_value) * plot_width if max_value else 0
        label = row[label_field]
        lines.append(
            f'<text x="20" y="{y + bar_height * 0.62:.1f}" font-family="Arial" font-size="12">{label}</text>'
        )
        lines.append(
            f'<rect x="{margin_left}" y="{y + 4:.1f}" width="{bar_width:.1f}" height="{bar_height - 8:.1f}" fill="#4C78A8"/>'
        )
        lines.append(
            f'<text x="{margin_left + bar_width + 6:.1f}" y="{y + bar_height * 0.62:.1f}" font-family="Arial" font-size="12">{value:.3f}</text>'
        )
    lines.append("</svg>\n")
    path.write_text("\n".join(lines))


def write_stage2a_svgs(output_dir, live_summary, seed_rows, regime_rows, coeff_rows):
    svg_dir = output_dir / "figures"
    svg_dir.mkdir(exist_ok=True, parents=True)
    write_svg_bar_chart(
        svg_dir / "wolf_win_rate_by_policy.svg",
        live_summary,
        "wolf_win_rate",
        "policy_name",
        "Wolf win rate by policy",
    )
    write_svg_bar_chart(
        svg_dir / "policy_performance_by_seed.svg",
        [row for row in seed_rows if row["policy_name"] == "frozen_ml"],
        "wolf_win_rate",
        "seed",
        "Frozen ML wolf win rate by seed",
    )
    write_svg_bar_chart(
        svg_dir / "policy_performance_by_regime.svg",
        [row for row in regime_rows if row["policy_name"] == "frozen_ml"],
        "wolf_win_rate",
        "behavioral_regime_id",
        "Frozen ML wolf win rate by regime",
    )
    write_svg_bar_chart(
        svg_dir / "coefficient_magnitude.svg",
        coeff_rows[:15],
        "standardized_coefficient_magnitude",
        "feature",
        "Top frozen ridge coefficient magnitudes",
    )


def run_stage2a_analysis(output_dir, shadow_summary, live_output, manifest):
    game_rows = live_output["game_rows"]
    decision_rows = live_output["decision_rows"]
    shift_rows = live_output["shift_rows"]

    live_summary = summarize_live_policies(game_rows)
    primary = matched_primary_contrasts(game_rows)
    matched = matched_pair_rows(primary)
    seed_rows = robustness_by_field(game_rows, "seed")
    regime_rows = robustness_by_field(game_rows, "behavioral_regime_id")
    secondary = secondary_outcomes(game_rows)
    agreement = policy_agreement(decision_rows)
    shift_summary = distribution_shift_summary(shift_rows)
    coeff_rows = feature_coefficients(manifest)
    stability = feature_stability_rows(manifest)
    ablations = ablation_diagnostics()
    overfit = overfitting_diagnostics(shadow_summary, live_summary)
    failures = failure_cases(game_rows, decision_rows)

    write_csv(
        output_dir / "wolf_kill_live_policy_summary.csv",
        live_summary,
        sorted({key for row in live_summary for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_primary_contrasts.csv",
        primary,
        sorted({key for row in primary for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_matched_pair_analysis.csv",
        matched,
        sorted({key for row in matched for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_seed_robustness.csv",
        seed_rows,
        sorted({key for row in seed_rows for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_regime_robustness.csv",
        regime_rows,
        sorted({key for row in regime_rows for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_secondary_outcomes.csv",
        secondary,
        sorted({key for row in secondary for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_policy_agreement.csv",
        agreement,
        sorted({key for row in agreement for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_distribution_shift_summary.csv",
        shift_summary,
        sorted({key for row in shift_summary for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_feature_coefficients.csv",
        coeff_rows,
        sorted({key for row in coeff_rows for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_feature_stability.csv",
        stability,
        sorted({key for row in stability for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_ablation_diagnostics.csv",
        ablations,
        sorted({key for row in ablations for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_overfitting_diagnostics.csv",
        overfit,
        sorted({key for row in overfit for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_policy_failure_cases.csv",
        failures,
        sorted({key for row in failures for key in row}) if failures else [
            "matched_set_id",
            "policy_name",
            "failure_reason",
        ],
    )
    write_stage2a_svgs(
        output_dir,
        live_summary,
        seed_rows,
        regime_rows,
        coeff_rows,
    )
    return {
        "live_summary": live_summary,
        "primary_contrasts": primary,
        "matched_pair_rows": matched,
        "seed_rows": seed_rows,
        "regime_rows": regime_rows,
        "secondary_rows": secondary,
        "agreement_rows": agreement,
        "shift_summary": shift_summary,
        "coefficient_rows": coeff_rows,
        "stability_rows": stability,
        "ablation_rows": ablations,
        "overfitting_rows": overfit,
        "failure_rows": failures,
    }
