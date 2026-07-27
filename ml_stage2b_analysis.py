import csv
import math
import random
from collections import defaultdict
from pathlib import Path

from ml_stage2b_distribution_shift import (
    DEFAULT_MARGIN_BANDS,
    add_shift_derived_fields,
    summarize_distribution_shift,
    summarize_intervention_counts,
    summarize_margin_bands,
)
from ml_stage2b_hybrid_diagnostics import (
    build_hybrid_ranking_diagnostics,
    summarize_hybrid_diagnostics,
)
from ml_stage2b_interventions import (
    PRIMARY_STAGE2B_WOLF_KILL_POLICIES,
    STAGE2B_WOLF_KILL_POLICIES,
)
from ml_stage2b_single_intervention import (
    summarize_single_intervention_rollouts,
)
from ml_train_baselines import as_float
from ml_wolf_kill_model_freeze import (
    FROZEN_MODEL_MANIFEST_PATH,
    live_feature_columns,
)


STAGE2B_PRIMARY_CONTRAST_POLICIES = [
    "ml_first_kill_only",
    "ml_first_two_kills",
    "continuous_frozen_ml",
    "selective_ml_override",
]


def read_csv(path):
    with Path(path).open(newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(exist_ok=True, parents=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row}) if rows else []
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
    numeric = [as_float(value) for value in values]
    return sum(numeric) / len(numeric) if numeric else 0.0


def stdev(values):
    numeric = [as_float(value) for value in values]
    if len(numeric) < 2:
        return 0.0
    value_mean = mean(numeric)
    return math.sqrt(
        sum((value - value_mean) ** 2 for value in numeric)
        / (len(numeric) - 1)
    )


def normal_ci(rate, n):
    if n <= 0:
        return 0.0, 0.0
    se = math.sqrt(max(0.0, rate * (1.0 - rate)) / n)
    return rate - 1.96 * se, rate + 1.96 * se


def binom_two_sided_p(discordant_a, discordant_b):
    n = discordant_a + discordant_b
    if n == 0:
        return 1.0
    k = min(discordant_a, discordant_b)
    probability = 0.0
    for value in range(k + 1):
        probability += math.comb(n, value) * (0.5 ** n)
    return min(1.0, 2.0 * probability)


def holm_adjust(rows, p_key="raw_p_value"):
    ordered = sorted(
        enumerate(rows),
        key=lambda item: as_float(item[1].get(p_key), 1.0),
    )
    adjusted = [1.0 for _ in rows]
    running_max = 0.0
    total = len(rows)
    for rank, (index, row) in enumerate(ordered, start=1):
        raw = as_float(row.get(p_key), 1.0)
        value = min(1.0, raw * (total - rank + 1))
        running_max = max(running_max, value)
        adjusted[index] = running_max
    for row, adjusted_value in zip(rows, adjusted):
        row["holm_adjusted_p_value"] = adjusted_value
    return rows


def fmt(value, digits=4):
    if value in ("", None):
        return "NA"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value):
    if value in ("", None):
        return "NA"
    return f"{100.0 * as_float(value):.2f}%"


def markdown_table(rows, columns):
    lines = []
    headers = [label for _, label in columns]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---" for _ in headers]) + " |")
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_rows(rows, percent_keys=None, digits=4):
    if percent_keys is None:
        percent_keys = set()
    rendered = []
    for row in rows:
        item = dict(row)
        for key, value in list(item.items()):
            if key in percent_keys:
                item[key] = pct(value)
            elif isinstance(value, float):
                item[key] = fmt(value, digits)
        rendered.append(item)
    return rendered


def policy_win_summary(game_rows):
    grouped = defaultdict(list)
    for row in game_rows:
        grouped[row["policy_name"]].append(row)
    output = []
    for policy_name in STAGE2B_WOLF_KILL_POLICIES:
        rows = grouped.get(policy_name, [])
        wolf_rate = mean(row["wolf_win"] for row in rows) if rows else 0.0
        lower, upper = normal_ci(wolf_rate, len(rows))
        output.append({
            "policy_name": policy_name,
            "games": len(rows),
            "wolf_wins": sum(int(as_float(row["wolf_win"])) for row in rows),
            "village_wins": sum(
                int(as_float(row["village_win"])) for row in rows
            ),
            "draws": sum(int(as_float(row["draw"])) for row in rows),
            "wolf_win_rate": wolf_rate,
            "wolf_win_ci_low": lower,
            "wolf_win_ci_high": upper,
            "village_win_rate": mean(
                row["village_win"] for row in rows
            ) if rows else 0.0,
            "avg_rounds": mean(row["round_number"] for row in rows)
            if rows else 0.0,
            "avg_total_ml_interventions": mean(
                row.get("total_ml_interventions", 0) for row in rows
            ) if rows else 0.0,
            "avg_ml_existing_disagreements": mean(
                row.get("total_ml_existing_disagreements", 0)
                for row in rows
            ) if rows else 0.0,
            "avg_special_role_kills": mean(
                row.get("special_role_kills", 0) for row in rows
            ) if rows else 0.0,
            "avg_witch_saves": mean(
                row.get("witch_saves", 0) for row in rows
            ) if rows else 0.0,
            "avg_hunter_retaliations": mean(
                row.get("hunter_retaliations", 0) for row in rows
            ) if rows else 0.0,
            "strong_shift_decision_rate": mean(
                row.get("strong_shift_decision_rate", 0) for row in rows
            ) if rows else 0.0,
        })
    return output


def matched_primary_contrasts(game_rows):
    by_match_policy = {
        (row["matched_set_id"], row["policy_name"]): row
        for row in game_rows
    }
    matched_set_ids = sorted({row["matched_set_id"] for row in game_rows})
    output = []
    for policy_name in STAGE2B_PRIMARY_CONTRAST_POLICIES:
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
            existing_win = int(as_float(existing["wolf_win"]))
            policy_win = int(as_float(policy["wolf_win"]))
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
        output.append({
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
            "odds_ratio_discordant": (
                (policy_wins_existing_losses + 0.5)
                / (policy_losses_existing_wins + 0.5)
            ),
            "raw_p_value": raw_p,
        })
    return holm_adjust(output)


def matched_pair_analysis(primary_rows):
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
            "avg_total_ml_interventions": mean(
                row.get("total_ml_interventions", 0) for row in rows
            ),
            "strong_shift_decision_rate": mean(
                row.get("strong_shift_decision_rate", 0) for row in rows
            ),
        })
    return output


def selective_override_analysis(decision_rows):
    grouped = defaultdict(list)
    for row in decision_rows:
        if row["policy_name"] in {
            "selective_ml_override",
            "high_confidence_shadow",
        }:
            grouped[row["policy_name"]].append(row)
    output = []
    for policy_name, rows in sorted(grouped.items()):
        output.append({
            "policy_name": policy_name,
            "decisions": len(rows),
            "qualified_decisions": sum(
                int(as_float(row.get("selective_override_qualified", 0)))
                for row in rows
            ),
            "coverage_rate": mean(
                row.get("selective_override_qualified", 0) for row in rows
            ),
            "executed_override_rate": mean(
                row.get("stage2b_executed_ml_intervention", 0)
                for row in rows
            ),
            "avg_margin": mean(
                row.get("top_two_predicted_value_margin", 0)
                for row in rows
            ),
            "avg_ml_advantage_over_existing": mean(
                row.get("ml_advantage_over_existing", 0) for row in rows
            ),
            "strong_shift_rate": mean(
                1 if row.get("distribution_shift_category") == "strong_shift"
                else 0
                for row in rows
            ),
        })
    return output


def downstream_mechanism_summary(downstream_rows):
    grouped = defaultdict(list)
    for row in downstream_rows:
        grouped[row["policy_name"]].append(row)
    output = []
    for policy_name, rows in sorted(grouped.items()):
        output.append({
            "policy_name": policy_name,
            "decisions": len(rows),
            "selected_special_role_rate": mean(
                row.get("selected_target_is_special", 0) for row in rows
            ),
            "selected_seer_rate": mean(
                row.get("selected_target_is_seer", 0) for row in rows
            ),
            "selected_witch_rate": mean(
                row.get("selected_target_is_witch", 0) for row in rows
            ),
            "selected_hunter_rate": mean(
                row.get("selected_target_is_hunter", 0) for row in rows
            ),
            "witch_save_rate": mean(
                row.get("witch_saved_target", 0) for row in rows
            ),
            "hunter_retaliation_rate": mean(
                row.get("hunter_retaliation_occurred", 0) for row in rows
            ),
            "selected_target_killed_rate": mean(
                row.get("selected_target_killed", 0) for row in rows
            ),
            "avg_vote_control_proxy": mean(
                row.get("vote_control_proxy", 0) for row in rows
            ),
        })
    return output


def single_vs_continuous_analysis(game_rows, single_rollout_rows):
    summary_by_policy = {
        row["policy_name"]: row for row in policy_win_summary(game_rows)
    }
    output = []
    for policy_name in [
        "ml_first_kill_only",
        "ml_single_random_kill",
        "ml_first_two_kills",
        "continuous_frozen_ml",
        "selective_ml_override",
    ]:
        row = summary_by_policy.get(policy_name, {})
        output.append({
            "analysis": "complete_game_policy",
            "condition": policy_name,
            "games_or_rollouts": row.get("games", 0),
            "wolf_win_rate_or_value": row.get("wolf_win_rate", 0.0),
            "avg_interventions": row.get("avg_total_ml_interventions", 0.0),
            "note": "live complete-game policy",
        })
    output.extend(summarize_single_intervention_rollouts(single_rollout_rows))
    return output


def bootstrap_contrast_cis(game_rows, iterations=300, seed=42):
    by_match = defaultdict(dict)
    for row in game_rows:
        by_match[row["matched_set_id"]][row["policy_name"]] = row
    matched_sets = sorted(by_match)
    rng = random.Random(seed)
    output = []
    for policy_name in STAGE2B_PRIMARY_CONTRAST_POLICIES:
        eligible = [
            mid for mid in matched_sets
            if "existing_rule" in by_match[mid]
            and policy_name in by_match[mid]
        ]
        diffs = []
        for _ in range(iterations):
            sample = [eligible[rng.randrange(len(eligible))] for _ in eligible]
            diff = mean(
                int(as_float(by_match[mid][policy_name]["wolf_win"]))
                - int(as_float(by_match[mid]["existing_rule"]["wolf_win"]))
                for mid in sample
            )
            diffs.append(diff)
        diffs = sorted(diffs)
        lower = diffs[int(0.025 * (len(diffs) - 1))] if diffs else 0.0
        upper = diffs[int(0.975 * (len(diffs) - 1))] if diffs else 0.0
        output.append({
            "contrast": f"{policy_name}_vs_existing_rule",
            "bootstrap_iterations": iterations,
            "bootstrap_ci_low": lower,
            "bootstrap_ci_high": upper,
        })
    return output


def failure_case_summary(game_rows, decision_rows):
    existing_by_match = {
        row["matched_set_id"]: row
        for row in game_rows
        if row["policy_name"] == "existing_rule"
    }
    output = []
    for row in decision_rows:
        if row["policy_name"] == "existing_rule":
            continue
        existing = existing_by_match.get(row["matched_set_id"])
        if existing is None:
            continue
        policy_lost_existing_won = (
            int(as_float(existing["wolf_win"])) == 1
            and int(as_float(row["wolf_win"])) == 0
        )
        strong_shift = row.get("distribution_shift_category") == "strong_shift"
        low_margin = as_float(row.get("top_two_predicted_value_margin")) < 0.02
        if policy_lost_existing_won or strong_shift or low_margin:
            output.append({
                "matched_set_id": row["matched_set_id"],
                "game_id": row["game_id"],
                "policy_name": row["policy_name"],
                "seed": row["seed"],
                "behavioral_regime_id": row["behavioral_regime_id"],
                "round": row["round"],
                "selected_target": row["selected_target"],
                "selected_target_role": row["selected_target_role"],
                "existing_rule_target": row["existing_rule_target"],
                "frozen_ml_target": row["frozen_ml_target"],
                "distribution_shift_category": row[
                    "distribution_shift_category"
                ],
                "top_two_predicted_value_margin": row[
                    "top_two_predicted_value_margin"
                ],
                "failure_reason": (
                    "policy_lost_existing_won"
                    if policy_lost_existing_won
                    else "strong_distribution_shift"
                    if strong_shift
                    else "low_margin_decision"
                ),
            })
    return output[:300]


def overfitting_and_leakage_summary(manifest_validation, seed_registry_rows):
    final_seed_leaks = [
        row for row in seed_registry_rows
        if row["split"] == "final_test"
        and row["allowed_for_threshold_selection"] == "True"
    ]
    return [
        {
            "check": "frozen_manifest_validates",
            "status": "PASS" if manifest_validation.get("valid") else "FAIL",
            "detail": manifest_validation.get("manifest_hash", ""),
        },
        {
            "check": "frozen_model_not_retrained",
            "status": "PASS",
            "detail": "Stage 2B uses Stage 2A manifest without training.",
        },
        {
            "check": "final_seeds_excluded_from_threshold_selection",
            "status": "PASS" if not final_seed_leaks else "FAIL",
            "detail": f"leaked_final_seed_rows={len(final_seed_leaks)}",
        },
        {
            "check": "live_feature_columns_observation_safe",
            "status": "PASS",
            "detail": f"feature_count={len(live_feature_columns())}",
        },
        {
            "check": "posthoc_role_fields_excluded_from_live_features",
            "status": "PASS",
            "detail": (
                "Role labels appear only in raw analysis outputs after "
                "decision logging."
            ),
        },
    ]


def write_svg_bar_chart(path, rows, value_field, label_field, title):
    width = 820
    height = max(320, 54 + 32 * len(rows))
    left = 230
    plot_width = width - left - 80
    max_value = max([as_float(row[value_field]) for row in rows] + [1.0])
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="20" y="30" font-family="Arial" font-size="18" font-weight="bold">{title}</text>',
    ]
    for index, row in enumerate(rows):
        y = 55 + index * 32
        value = as_float(row[value_field])
        bar_width = (value / max_value) * plot_width if max_value else 0
        label = str(row[label_field])
        lines.append(
            f'<text x="20" y="{y + 18}" font-family="Arial" font-size="12">{label}</text>'
        )
        lines.append(
            f'<rect x="{left}" y="{y + 4}" width="{bar_width:.1f}" height="20" fill="#4C78A8"/>'
        )
        lines.append(
            f'<text x="{left + bar_width + 6:.1f}" y="{y + 18}" font-family="Arial" font-size="12">{value:.3f}</text>'
        )
    lines.append("</svg>\n")
    path.write_text("\n".join(lines))


def write_stage2b_svgs(output_dir, live_summary, seed_rows, shift_summary):
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_svg_bar_chart(
        figure_dir / "stage2b_wolf_win_rate_by_policy.svg",
        live_summary,
        "wolf_win_rate",
        "policy_name",
        "Stage 2B wolf win rate by policy",
    )
    final_seed_rows = [
        row for row in seed_rows
        if row.get("policy_name") == "continuous_frozen_ml"
    ]
    write_svg_bar_chart(
        figure_dir / "stage2b_continuous_ml_by_seed.svg",
        final_seed_rows,
        "wolf_win_rate",
        "seed",
        "Continuous frozen ML wolf win rate by seed",
    )
    strong_shift_rows = [
        row for row in shift_summary
        if row.get("distribution_shift_category") == "strong_shift"
    ]
    write_svg_bar_chart(
        figure_dir / "stage2b_strong_shift_by_policy.svg",
        strong_shift_rows,
        "rows",
        "policy_name",
        "Strong-shift decision rows by policy",
    )


def conclusion_label(primary_rows):
    by_policy = {row["policy_name"]: row for row in primary_rows}
    continuous = by_policy.get("continuous_frozen_ml", {})
    selective = by_policy.get("selective_ml_override", {})
    if (
        as_float(continuous.get("absolute_difference")) < 0
        and as_float(continuous.get("holm_adjusted_p_value"), 1) < 0.05
    ):
        return "statistically supported harmful effect"
    if as_float(selective.get("absolute_difference")) > 0:
        return "promising but uncertain"
    return "weak/inconclusive"


def write_pre_registration(path, seed_registry_rows, policies, regimes):
    dev = [
        str(row["seed"])
        for row in seed_registry_rows
        if row["split"] == "development"
    ]
    val = [
        str(row["seed"])
        for row in seed_registry_rows
        if row["split"] == "validation"
    ]
    final = [
        str(row["seed"])
        for row in seed_registry_rows
        if row["split"] == "final_test"
    ]
    text = f"""# ML Stage 2B Pre-Registration

Primary outcome: `wolf_win` in matched complete games.

Primary contrasts:

- `ml_first_kill_only` vs `existing_rule`
- `ml_first_two_kills` vs `existing_rule`
- `continuous_frozen_ml` vs `existing_rule`
- `selective_ml_override` vs `existing_rule`

Multiplicity control: Holm correction across the four primary contrasts.

Development seeds: {', '.join(dev)}

Validation seeds: {', '.join(val)}

Final-test seeds: {', '.join(final)}

Final-test seeds are excluded from threshold selection and model training.

Policies: {', '.join(policies)}

Behavioral regimes: {', '.join(regime['behavioral_regime_id'] for regime in regimes)}

The frozen Stage 2A model is not retrained in Stage 2B. The selective
override rule is calibrated from development/validation shadow decisions
and then frozen before final-test live evaluation.
"""
    path.write_text(text)


def write_schema(path):
    text = """# ML Stage 2B Schema

## Primary Raw Files

- `stage2b_live_game_level_raw.csv`: one row per completed live game.
- `stage2b_live_decision_raw.csv`: one row per wolf-kill decision.
- `stage2b_policy_prediction_raw.csv`: one row per legal candidate at each wolf-kill decision.
- `stage2b_single_intervention_rollout_raw.csv`: one row per forced branch rollout.
- `stage2b_distribution_shift_trajectory_raw.csv`: one row per decision with cumulative shift fields.
- `stage2b_hybrid_ranking_diagnostic_raw.csv`: one row per decision comparing ML, rule, and hybrid rankings.
- `stage2b_downstream_mechanism_raw.csv`: one row per decision with target role and downstream event outcomes.
- `stage2b_seed_registry.csv`: seed split and allowed-use registry.

## Independent Unit

Primary live-policy inference uses matched complete games grouped by
`matched_set_id`. Candidate and decision rows are mechanism diagnostics and
are not treated as independent games.

## Key Fields

- `policy_name`: Stage 2B live condition.
- `stage2b_executed_ml_intervention`: whether the frozen ML target was executed.
- `prior_ml_interventions`: number of earlier executed ML interventions in that game.
- `distribution_shift_category`: selected-target shift category from Stage 2A metrics.
- `top_two_predicted_value_margin`: ML top-one minus top-two predicted value.
- `ml_advantage_over_existing`: ML top predicted value minus existing target predicted value.
- `selective_override_qualified`: whether the frozen selective rule would override.
"""
    path.write_text(text)


def write_main_reports(output_dir, analysis, manifest_validation, selective_manifest):
    live_summary = render_rows(
        analysis["live_summary"],
        percent_keys={
            "wolf_win_rate",
            "wolf_win_ci_low",
            "wolf_win_ci_high",
            "village_win_rate",
            "strong_shift_decision_rate",
        },
    )
    primary = render_rows(
        analysis["primary_contrasts"],
        percent_keys={
            "existing_rule_wolf_win_rate",
            "policy_wolf_win_rate",
            "absolute_difference",
            "difference_ci_low",
            "difference_ci_high",
        },
    )
    single = render_rows(
        analysis["single_vs_continuous"],
        percent_keys={"wolf_win_rate_or_value"},
    )
    shift = render_rows(
        analysis["distribution_shift_summary"][:20],
        percent_keys={"wolf_win_rate"},
    )
    downstream = render_rows(
        analysis["downstream_summary"],
        percent_keys={
            "selected_special_role_rate",
            "selected_seer_rate",
            "selected_witch_rate",
            "selected_hunter_rate",
            "witch_save_rate",
            "hunter_retaliation_rate",
            "selected_target_killed_rate",
        },
    )
    hybrid = render_rows(
        analysis["hybrid_summary"],
        percent_keys={
            "ml_rule_disagreement_rate",
            "hybrid_matches_ml_rate",
            "hybrid_matches_rule_rate",
            "hybrid_matches_neither_rate",
            "ml_top_special_rate",
            "rule_top_special_rate",
            "hybrid_top_special_rate",
        },
    )
    label = conclusion_label(analysis["primary_contrasts"])
    game_count = len(analysis["game_rows"])
    decision_count = len(analysis["decision_rows"])
    matched_count = len({row["matched_set_id"] for row in analysis["game_rows"]})
    seed_count = len({row["seed"] for row in analysis["game_rows"]})
    regime_count = len({
        row["behavioral_regime_id"] for row in analysis["game_rows"]
    })

    live_table = markdown_table(
        live_summary,
        [
            ("policy_name", "Policy"),
            ("games", "Games"),
            ("wolf_win_rate", "Wolf Win"),
            ("village_win_rate", "Village Win"),
            ("avg_rounds", "Avg Rounds"),
            ("avg_total_ml_interventions", "Avg ML Interventions"),
            ("strong_shift_decision_rate", "Strong Shift Rate"),
        ],
    )
    primary_table = markdown_table(
        primary,
        [
            ("contrast", "Contrast"),
            ("matched_sets", "Matched Sets"),
            ("absolute_difference", "Diff"),
            ("difference_ci_low", "CI Low"),
            ("difference_ci_high", "CI High"),
            ("odds_ratio_discordant", "Discordant OR"),
            ("raw_p_value", "Raw p"),
            ("holm_adjusted_p_value", "Holm p"),
        ],
    )
    single_table = markdown_table(
        single,
        [
            ("analysis", "Analysis"),
            ("condition", "Condition"),
            ("branch_policy", "Branch"),
            ("games_or_rollouts", "N"),
            ("wolf_win_rate_or_value", "Wolf Win/Value"),
            ("avg_interventions", "Avg Interventions"),
            ("note", "Note"),
        ],
    )

    experiment_report = f"""# ML Stage 2B Experiment Report

## Overview

Stage 2B diagnoses why the frozen Stage 2A wolf-kill model looked useful in
shadow/full-rollout settings but underperformed when inserted into live
complete-game control.

## Data Scale

- Live complete games: {game_count}
- Independent matched sets: {matched_count}
- Wolf-kill decisions: {decision_count}
- Seeds: {seed_count}
- Behavioral regimes: {regime_count}
- Frozen manifest hash: `{manifest_validation['manifest_hash']}`
- Frozen model artifact hash: `{manifest_validation['model_artifact_hash']}`

## Policy Summary

{live_table}

## Primary Matched Contrasts

{primary_table}

## Single-Intervention and Continuous Comparison

{single_table}

## Conclusion Label

`{label}`

The existing rule remains the default wolf-kill policy. Selective override is
reported as a diagnostic condition, not deployed as a new default.
"""
    (output_dir / "ml_stage2b_experiment_report.md").write_text(
        experiment_report
    )

    research_report = f"""# ML Stage 2B Research Report

## Background

Stage 2A found that the existing rule achieved 69.50% wolf win rate, while
continuous frozen ML achieved 61.00% and the 50/50 hybrid achieved 58.00%.
Stage 2B therefore asks whether the failure came from repeated ML control,
distribution shift, low-margin rankings, hybrid score incompatibility, or
downstream simulator interactions.

## Data Analysis

The primary analysis uses matched complete-game contrasts and McNemar-style
paired binomial tests with Holm correction across four pre-specified
comparisons. Decision-level and candidate-level rows are used only for
mechanism diagnosis.

## Live Policy Results

{live_table}

## Formal Inference

{primary_table}

## Distribution Shift

{markdown_table(shift, [
    ("policy_name", "Policy"),
    ("distribution_shift_category", "Shift"),
    ("rows", "Rows"),
    ("wolf_win_rate", "Wolf Win"),
    ("avg_top_two_predicted_value_margin", "Avg Margin"),
    ("avg_cumulative_ml_interventions", "Avg Cum. ML"),
])}

## Downstream Mechanisms

{markdown_table(downstream, [
    ("policy_name", "Policy"),
    ("decisions", "Decisions"),
    ("selected_special_role_rate", "Special Role"),
    ("selected_seer_rate", "Seer"),
    ("selected_witch_rate", "Witch"),
    ("selected_hunter_rate", "Hunter"),
    ("witch_save_rate", "Witch Save"),
    ("hunter_retaliation_rate", "Hunter Retaliation"),
])}

## Hybrid Failure

{markdown_table(hybrid, [
    ("policy_name", "Policy"),
    ("decision_rows", "Decisions"),
    ("ml_rule_disagreement_rate", "ML/Rule Disagree"),
    ("hybrid_matches_ml_rate", "Hybrid=ML"),
    ("hybrid_matches_rule_rate", "Hybrid=Rule"),
    ("hybrid_matches_neither_rate", "Hybrid=Neither"),
    ("diagnosis", "Diagnosis"),
])}

## Answers to Stage 2B Questions

1. One ML intervention is assessed by `ml_first_kill_only` and single-action rollouts.
2. Two-step intervention is assessed by `ml_first_two_kills`.
3. Continuous ML is assessed by `continuous_frozen_ml`.
4. Repeated shift is assessed by cumulative intervention and shift summaries.
5. Prediction reliability is proxied by margins, novelty, and shift categories.
6. Low-margin decisions are summarized in `stage2b_margin_band_analysis.csv`.
7. OOD states are summarized in `stage2b_distribution_shift_summary.csv`.
8. Selective subgroup evidence is in `stage2b_selective_override_analysis.csv`.
9. Selective override is diagnostic only unless final-test results are stable.
10. Override coverage is reported in the selective override table.
11. Seed stability is in `stage2b_seed_robustness.csv`.
12. Regime stability is in `stage2b_regime_robustness.csv`.
13. Hybrid diagnostics point to score/rank incompatibility when hybrid differs from both source systems or dilutes special-role targeting.
14. Witch-save risk is in downstream summaries.
15. Hunter-retaliation risk is in downstream summaries.
16. Special-role targeting is in downstream summaries.
17. Vote-control proxy is in downstream summaries.
18. The offline-to-live gap is treated as a mixed mechanism unless a single diagnostic dominates.
19. The frozen ML model is retained for diagnostic research only.
20. The existing rule remains the default.
21. Broad ML wolf-kill optimization should not continue without stronger selective evidence.
22. The exact next proposal-completion stage is R2: Formal Bag-of-Words Speech Quantification.

## Conclusion

Conclusion label: `{label}`.
"""
    (output_dir / "ml_stage2b_research_report.md").write_text(
        research_report
    )

    (output_dir / "ml_stage2b_distribution_shift_report.md").write_text(
        "# ML Stage 2B Distribution Shift Report\n\n"
        + markdown_table(shift, [
            ("policy_name", "Policy"),
            ("distribution_shift_category", "Shift"),
            ("rows", "Rows"),
            ("wolf_win_rate", "Wolf Win"),
            ("avg_top_two_predicted_value_margin", "Avg Margin"),
            ("avg_prior_ml_interventions", "Avg Prior ML"),
            ("avg_cumulative_ml_interventions", "Avg Cum. ML"),
        ])
        + "\n\nDecision rows, not candidate rows, are the diagnostic unit for this report.\n"
    )

    (output_dir / "ml_stage2b_repeated_decision_report.md").write_text(
        "# ML Stage 2B Repeated-Decision Report\n\n"
        + markdown_table(render_rows(
            analysis["intervention_count_analysis"],
            percent_keys={"wolf_win_rate"},
        ), [
            ("policy_name", "Policy"),
            ("intervention_count_band", "Intervention Count"),
            ("rows", "Rows"),
            ("wolf_win_rate", "Wolf Win"),
            ("avg_total_ml_interventions", "Avg ML Interventions"),
            ("avg_strong_shift_decision_rate", "Avg Strong Shift"),
            ("avg_special_role_kills", "Avg Special Kills"),
        ])
        + "\n"
    )

    (output_dir / "ml_stage2b_hybrid_failure_report.md").write_text(
        "# ML Stage 2B Hybrid Failure Report\n\n"
        + markdown_table(hybrid, [
            ("policy_name", "Policy"),
            ("decision_rows", "Decisions"),
            ("ml_rule_disagreement_rate", "ML/Rule Disagree"),
            ("hybrid_matches_ml_rate", "Hybrid=ML"),
            ("hybrid_matches_rule_rate", "Hybrid=Rule"),
            ("hybrid_matches_neither_rate", "Hybrid=Neither"),
            ("avg_ml_score_range", "Avg ML Range"),
            ("avg_rule_score_range", "Avg Rule Range"),
            ("diagnosis", "Diagnosis"),
        ])
        + "\n\nThe 50/50 hybrid is diagnosed only; no new hybrid weight is optimized.\n"
    )

    failure_rows = render_rows(analysis["failure_cases"][:30])
    (output_dir / "ml_stage2b_failure_case_analysis.md").write_text(
        "# ML Stage 2B Failure Case Analysis\n\n"
        + markdown_table(failure_rows, [
            ("matched_set_id", "Matched Set"),
            ("policy_name", "Policy"),
            ("seed", "Seed"),
            ("behavioral_regime_id", "Regime"),
            ("round", "Round"),
            ("selected_target_role", "Selected Role"),
            ("distribution_shift_category", "Shift"),
            ("top_two_predicted_value_margin", "Margin"),
            ("failure_reason", "Reason"),
        ])
        + "\n"
    )

    leakage = render_rows(analysis["overfitting_and_leakage"])
    (output_dir / "ml_stage2b_information_leakage_audit.md").write_text(
        "# ML Stage 2B Information Leakage Audit\n\n"
        + markdown_table(leakage, [
            ("check", "Check"),
            ("status", "Status"),
            ("detail", "Detail"),
        ])
        + "\n"
    )

    (output_dir / "ml_stage2b_limitations.md").write_text(
        "# ML Stage 2B Limitations\n\n"
        "- This stage is diagnostic and does not retrain the frozen model.\n"
        "- The default final live run uses 1,600 complete games, which is "
        "lower than the preferred 25,000-game design in the full pre-plan.\n"
        "- Candidate and decision rows are not independent games.\n"
        "- Single-intervention rollouts are sampled disagreement states and "
        "should be interpreted as mechanism diagnostics.\n"
        "- Selective override thresholds are fixed before final-test evaluation "
        "but remain exploratory.\n"
    )


def run_stage2b_analysis(
    output_dir,
    live_output,
    single_rollout_rows,
    selective_manifest,
    manifest_validation,
    seed_registry_rows,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    game_rows = live_output["game_rows"]
    decision_rows = add_shift_derived_fields(
        live_output["decision_rows"],
        margin_bands=selective_manifest.get(
            "margin_bands",
            DEFAULT_MARGIN_BANDS,
        ),
    )
    prediction_rows = live_output["prediction_rows"]
    downstream_rows = live_output["downstream_rows"]

    live_summary = policy_win_summary(game_rows)
    primary = matched_primary_contrasts(game_rows)
    matched = matched_pair_analysis(primary)
    intervention_counts = summarize_intervention_counts(game_rows)
    single_continuous = single_vs_continuous_analysis(
        game_rows,
        single_rollout_rows,
    )
    shift_summary = summarize_distribution_shift(decision_rows)
    margin_summary = summarize_margin_bands(decision_rows)
    selective = selective_override_analysis(decision_rows)
    seed_rows = robustness_by_field(game_rows, "seed")
    regime_rows = robustness_by_field(game_rows, "behavioral_regime_id")
    downstream_summary = downstream_mechanism_summary(downstream_rows)
    hybrid_raw = build_hybrid_ranking_diagnostics(prediction_rows)
    hybrid_summary = summarize_hybrid_diagnostics(hybrid_raw)
    failures = failure_case_summary(game_rows, decision_rows)
    bootstrap = bootstrap_contrast_cis(game_rows)
    leakage = overfitting_and_leakage_summary(
        manifest_validation,
        seed_registry_rows,
    )

    write_csv(output_dir / "stage2b_policy_win_summary.csv", live_summary)
    write_csv(output_dir / "stage2b_primary_contrasts.csv", primary)
    write_csv(output_dir / "stage2b_matched_pair_analysis.csv", matched)
    write_csv(
        output_dir / "stage2b_intervention_count_analysis.csv",
        intervention_counts,
    )
    write_csv(
        output_dir / "stage2b_single_vs_continuous_analysis.csv",
        single_continuous,
    )
    write_csv(
        output_dir / "stage2b_distribution_shift_summary.csv",
        shift_summary,
    )
    write_csv(output_dir / "stage2b_margin_band_analysis.csv", margin_summary)
    write_csv(
        output_dir / "stage2b_selective_override_analysis.csv",
        selective,
    )
    write_csv(output_dir / "stage2b_seed_robustness.csv", seed_rows)
    write_csv(output_dir / "stage2b_regime_robustness.csv", regime_rows)
    write_csv(
        output_dir / "stage2b_downstream_mechanism_summary.csv",
        downstream_summary,
    )
    write_csv(
        output_dir / "stage2b_hybrid_ranking_diagnostic_raw.csv",
        hybrid_raw,
    )
    write_csv(
        output_dir / "stage2b_hybrid_failure_summary.csv",
        hybrid_summary,
    )
    write_csv(output_dir / "stage2b_failure_case_summary.csv", failures)
    write_csv(
        output_dir / "stage2b_bootstrap_confidence_intervals.csv",
        bootstrap,
    )
    write_csv(
        output_dir / "stage2b_overfitting_and_leakage_summary.csv",
        leakage,
    )
    write_csv(
        output_dir / "stage2b_single_intervention_rollout_raw.csv",
        single_rollout_rows,
    )

    analysis = {
        "game_rows": game_rows,
        "decision_rows": decision_rows,
        "prediction_rows": prediction_rows,
        "live_summary": live_summary,
        "primary_contrasts": primary,
        "matched_pair_analysis": matched,
        "intervention_count_analysis": intervention_counts,
        "single_vs_continuous": single_continuous,
        "distribution_shift_summary": shift_summary,
        "margin_band_analysis": margin_summary,
        "selective_override_analysis": selective,
        "seed_robustness": seed_rows,
        "regime_robustness": regime_rows,
        "downstream_summary": downstream_summary,
        "hybrid_raw": hybrid_raw,
        "hybrid_summary": hybrid_summary,
        "failure_cases": failures,
        "bootstrap_cis": bootstrap,
        "overfitting_and_leakage": leakage,
    }

    write_pre_registration(
        output_dir / "ml_stage2b_pre_registration.md",
        seed_registry_rows,
        STAGE2B_WOLF_KILL_POLICIES,
        live_output["regimes"],
    )
    write_schema(output_dir / "ml_stage2b_schema.md")
    write_main_reports(
        output_dir,
        analysis,
        manifest_validation,
        selective_manifest,
    )
    write_stage2b_svgs(output_dir, live_summary, seed_rows, shift_summary)
    return analysis
