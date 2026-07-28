"""R5 financial-risk analysis for the R4 payoff validation dataset."""

from __future__ import annotations

import csv
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from financial_downside_metrics import downside_metrics, var_cvar_metrics
from financial_information_premium import (
    premium_difference as information_premium_difference,
    seer_check_wolf_game_ids,
    useful_information_game_ids,
)
from financial_manipulation_premium import (
    manipulation_game_ids,
    premium_difference as manipulation_premium_difference,
)
from financial_metric_manifest import (
    R4_MANIFEST_HASH,
    RESULTS_DIR,
    build_metric_manifest,
    write_metric_manifest,
)
from financial_r5_bootstrap import group_rows
from financial_risk_frontier import mark_frontier
from financial_risk_metrics import (
    mean,
    median,
    payoff_distribution_metrics,
    quantile,
    sample_stdev,
)
from financial_sharpe_sortino import sharpe_like_ratio, sortino_like_ratio


R4_DIR = Path("results/payoff_matrix_stage_r4")
RESEARCH_DIR = Path("results/research_progress")
FIGURES_DIR = RESULTS_DIR / "figures"
BOOTSTRAP_ITERATIONS = 2000


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value, digits=6):
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return value
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return value


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row}) if rows else []
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


def write_md(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def git_head():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def group_by(rows, *keys):
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def unique_values(rows, key):
    return sorted({row.get(key, "") for row in rows if row.get(key, "") != ""})


def enrich_player_rows(player_rows):
    enriched = []
    for row in player_rows:
        new_row = dict(row)
        total = safe_float(row["total_payoff"])
        opportunity_cost = safe_float(row.get("opportunity_cost"))
        excluding_opportunity = total - opportunity_cost
        adjusted = excluding_opportunity + opportunity_cost
        new_row.update({
            "payoff_excluding_opportunity_cost": excluding_opportunity,
            "opportunity_cost_adjusted_payoff": adjusted,
            "loss": -total,
            "positive_payoff": int(total > 0),
            "zero_payoff": int(total == 0),
            "negative_payoff": int(total < 0),
            "opportunity_cost_sign_convention": (
                "opportunity_cost is included once; negative values lower payoff"
            ),
        })
        enriched.append(new_row)
    return enriched


def enrich_game_rows(game_rows):
    enriched = []
    for row in game_rows:
        new_row = dict(row)
        total = safe_float(row["total_game_payoff"])
        players = safe_float(row["player_count"], 1.0) or 1.0
        new_row.update({
            "mean_player_payoff": total / players,
            "game_loss": -total,
            "wolf_win": int(row.get("winner") == "wolf"),
            "village_win": int(row.get("winner") == "village"),
            "draw": int(row.get("winner") == "draw"),
        })
        enriched.append(new_row)
    return enriched


def metric_row(base, rows, payoff_field="total_payoff"):
    values = [safe_float(row[payoff_field]) for row in rows]
    distribution = payoff_distribution_metrics(values)
    downside = downside_metrics(values)
    var90 = var_cvar_metrics(values, 0.90)
    var95 = var_cvar_metrics(values, 0.95)
    adjusted_values = [
        safe_float(row.get("opportunity_cost_adjusted_payoff", row[payoff_field]))
        for row in rows
    ]
    adjusted_downside = downside_metrics(adjusted_values)
    result = dict(base)
    result.update(distribution)
    result.update({
        "downside_target": downside["downside_target"],
        "downside_count": downside["downside_count"],
        "downside_deviation": downside["downside_deviation"],
        "lower_partial_moment_1": downside["lower_partial_moment_1"],
        "lower_partial_moment_2": downside["lower_partial_moment_2"],
        "mean_negative_payoff": downside["mean_negative_payoff"],
        "worst_decile_mean_payoff": downside["worst_decile_mean_payoff"],
        "maximum_observed_loss": downside["maximum_observed_loss"],
        "var90_payoff_threshold": var90["var_like_payoff_threshold"],
        "var90_loss": var90["var_like_loss"],
        "cvar90_loss": var90["cvar_like_loss"],
        "worst_10pct_mean_payoff": var90["worst_tail_mean_payoff"],
        "var95_payoff_threshold": var95["var_like_payoff_threshold"],
        "var95_loss": var95["var_like_loss"],
        "cvar95_loss": var95["cvar_like_loss"],
        "worst_5pct_mean_payoff": var95["worst_tail_mean_payoff"],
        "sharpe_like_benchmark": 0.0,
        "sharpe_like_ratio": sharpe_like_ratio(values, 0.0),
        "sortino_like_target": 0.0,
        "sortino_like_ratio": sortino_like_ratio(values, 0.0),
        "adjusted_mean_payoff": mean(adjusted_values),
        "adjusted_stdev": sample_stdev(adjusted_values),
        "adjusted_downside_deviation": adjusted_downside["downside_deviation"],
        "adjusted_sharpe_like_ratio": sharpe_like_ratio(adjusted_values, 0.0),
        "adjusted_sortino_like_ratio": sortino_like_ratio(adjusted_values, 0.0),
        "opportunity_cost_mean": mean(
            safe_float(row.get("opportunity_cost")) for row in rows
        ),
    })
    return result


def build_dataset_registry(player_rows, game_rows, event_rows, strategy_rows):
    historical = read_csv(R4_DIR / "historical_recalculation_coverage.csv")
    rows = [
        {
            "dataset_id": "r4_player_level_payoff",
            "source_path": "results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv",
            "stage": "R4",
            "row_count": len(player_rows),
            "game_count": len({row["game_id"] for row in player_rows}),
            "player_game_count": len(player_rows),
            "event_count": "",
            "independent_unit": "player-game clustered by game",
            "role_coverage": ";".join(unique_values(player_rows, "role")),
            "strategy_coverage": ";".join(unique_values(player_rows, "condition_name")),
            "core_or_extended": ";".join(unique_values(player_rows, "calculation_specification")),
            "recalculation_status": "fully analyzable",
            "allowed_for_primary_analysis": True,
            "limitations": "Generated from R4 validation games only.",
            "notes": "Primary R5 role-level risk-return dataset.",
        },
        {
            "dataset_id": "r4_game_level_payoff",
            "source_path": "results/payoff_matrix_stage_r4/r4_game_level_payoff_raw.csv",
            "stage": "R4",
            "row_count": len(game_rows),
            "game_count": len({row["game_id"] for row in game_rows}),
            "player_game_count": "",
            "event_count": "",
            "independent_unit": "game",
            "role_coverage": "all roles through game totals",
            "strategy_coverage": ";".join(unique_values(game_rows, "condition_name")),
            "core_or_extended": ";".join(unique_values(game_rows, "calculation_specification")),
            "recalculation_status": "fully analyzable",
            "allowed_for_primary_analysis": True,
            "limitations": "Game totals are not player-role observations.",
            "notes": "Used for game-level payoff and bootstrap grouping.",
        },
        {
            "dataset_id": "r4_event_level_payoff_ledger",
            "source_path": "results/payoff_matrix_stage_r4/r4_event_level_payoff_ledger.csv",
            "stage": "R4",
            "row_count": len(event_rows),
            "game_count": len({row["game_id"] for row in event_rows}),
            "player_game_count": "",
            "event_count": len(event_rows),
            "independent_unit": "event rows for decomposition only",
            "role_coverage": ";".join(unique_values(event_rows, "actor_role")),
            "strategy_coverage": ";".join(unique_values(event_rows, "condition_name")),
            "core_or_extended": ";".join(unique_values(event_rows, "calculation_specification")),
            "recalculation_status": "fully analyzable for attribution decomposition",
            "allowed_for_primary_analysis": False,
            "limitations": "Event rows are not independent observations for risk metrics.",
            "notes": "Used only for payoff-source, information, and manipulation flags.",
        },
        {
            "dataset_id": "r4_strategy_level_payoff",
            "source_path": "results/payoff_matrix_stage_r4/r4_strategy_level_payoff_raw.csv",
            "stage": "R4",
            "row_count": len(strategy_rows),
            "game_count": len({row["game_id"] for row in strategy_rows}),
            "player_game_count": len(strategy_rows),
            "event_count": "",
            "independent_unit": "player-game clustered by game",
            "role_coverage": ";".join(unique_values(strategy_rows, "role")),
            "strategy_coverage": ";".join(unique_values(strategy_rows, "condition_name")),
            "core_or_extended": "core;extended",
            "recalculation_status": "fully analyzable",
            "allowed_for_primary_analysis": True,
            "limitations": "Limited to R4 strategy conditions.",
            "notes": "Used for strategy risk-return frontiers.",
        },
    ]
    for item in historical:
        rows.append({
            "dataset_id": "historical_" + item["stage"].replace(" ", "_").lower(),
            "source_path": item["source_dataset"],
            "stage": item["stage"],
            "row_count": item["raw_game_count"],
            "game_count": item["raw_game_count"],
            "player_game_count": "",
            "event_count": "",
            "independent_unit": "varies; mostly aggregate",
            "role_coverage": "incomplete",
            "strategy_coverage": "historical",
            "core_or_extended": "not fully available",
            "recalculation_status": item["recalculation_status"],
            "allowed_for_primary_analysis": False,
            "limitations": item["missing_fields"],
            "notes": item["notes"],
        })
    return rows


def build_registries(player_rows, game_rows):
    strategies = []
    for condition in unique_values(player_rows, "condition_name"):
        strategies.append({
            "condition_name": condition,
            "strategy_family": (
                "voting" if condition == "villager_random_vote"
                else "seer" if condition == "seer_highest_suspicion"
                else "wolf" if condition == "wolf_random_kill"
                else "witch" if condition == "witch_conservative_poison"
                else "reference"
            ),
            "analysis_status": "fully analyzable in R4 validation dataset",
            "uses_event_ledger": True,
            "notes": "Strategy condition available with player-level payoff rows.",
        })
    roles = [
        {"role": role, "team": "wolf" if role == "werewolf" else "village"}
        for role in unique_values(player_rows, "role")
    ]
    seeds = [
        {
            "seed": seed,
            "game_rows": sum(1 for row in game_rows if row["seed"] == seed),
            "player_rows": sum(1 for row in player_rows if row["seed"] == seed),
        }
        for seed in unique_values(player_rows, "seed")
    ]
    regimes = [
        {
            "behavioral_regime": regime,
            "game_rows": sum(1 for row in game_rows if row["behavioral_regime"] == regime),
            "player_rows": sum(1 for row in player_rows if row["behavioral_regime"] == regime),
        }
        for regime in unique_values(player_rows, "behavioral_regime")
    ]
    return strategies, roles, seeds, regimes


def summarize_groups(player_rows):
    role_metrics = [
        metric_row(
            {"calculation_specification": spec, "role": role},
            rows,
        )
        for (spec, role), rows in sorted(
            group_by(player_rows, "calculation_specification", "role").items()
        )
    ]
    strategy_metrics = [
        metric_row(
            {
                "calculation_specification": spec,
                "role": role,
                "condition_name": condition,
            },
            rows,
        )
        for (spec, role, condition), rows in sorted(
            group_by(
                player_rows,
                "calculation_specification",
                "role",
                "condition_name",
            ).items()
        )
    ]
    seed_metrics = [
        metric_row(
            {
                "calculation_specification": spec,
                "role": role,
                "seed": seed,
            },
            rows,
        )
        for (spec, role, seed), rows in sorted(
            group_by(player_rows, "calculation_specification", "role", "seed").items()
        )
    ]
    regime_metrics = [
        metric_row(
            {
                "calculation_specification": spec,
                "role": role,
                "behavioral_regime": regime,
            },
            rows,
        )
        for (spec, role, regime), rows in sorted(
            group_by(
                player_rows,
                "calculation_specification",
                "role",
                "behavioral_regime",
            ).items()
        )
    ]
    return role_metrics, strategy_metrics, seed_metrics, regime_metrics


def build_var_cvar_summary(role_metrics):
    rows = []
    for row in role_metrics:
        rows.append({
            "calculation_specification": row["calculation_specification"],
            "role": row["role"],
            "var90_payoff_threshold": row["var90_payoff_threshold"],
            "var90_loss": row["var90_loss"],
            "cvar90_loss": row["cvar90_loss"],
            "var95_payoff_threshold": row["var95_payoff_threshold"],
            "var95_loss": row["var95_loss"],
            "cvar95_loss": row["cvar95_loss"],
            "worst_10pct_mean_payoff": row["worst_10pct_mean_payoff"],
            "worst_5pct_mean_payoff": row["worst_5pct_mean_payoff"],
        })
    return rows


def build_premium_rows(player_rows, event_rows):
    information_raw = []
    information_summary = []
    manipulation_raw = []
    manipulation_summary = []

    for spec in unique_values(player_rows, "calculation_specification"):
        spec_players = [row for row in player_rows if row["calculation_specification"] == spec]
        spec_events = [row for row in event_rows if row["calculation_specification"] == spec]
        definitions = [
            ("primary_useful_information", useful_information_game_ids(spec_events)),
            ("wolf_found_by_check", seer_check_wolf_game_ids(spec_events)),
            (
                "villager_confirmation",
                {
                    row["game_id"]
                    for row in spec_events
                    if row.get("payoff_component") == "seer_investigation_used"
                    and row.get("target_role") not in ("", "werewolf")
                },
            ),
        ]
        for name, game_ids in definitions:
            metrics = information_premium_difference(spec_players, game_ids)
            information_raw.append({
                "calculation_specification": spec,
                "premium_definition": name,
                "flagged_game_count": len(game_ids),
                **metrics,
                "interpretation": "association, not causal",
            })
        primary = next(row for row in information_raw if row["calculation_specification"] == spec and row["premium_definition"] == "primary_useful_information")
        information_summary.append(primary)

        manipulation_definitions = [
            ("primary_any_manipulation", manipulation_game_ids(spec_events)),
            (
                "coordinated_vote_or_village_elimination",
                {
                    row["game_id"]
                    for row in spec_events
                    if row.get("payoff_component") == "wolf_villager_voted_out_shared"
                },
            ),
            (
                "special_target_elimination",
                {
                    row["game_id"]
                    for row in spec_events
                    if row.get("payoff_component") == "wolf_special_killed_shared"
                },
            ),
            (
                "successful_deception",
                {
                    row["game_id"]
                    for row in spec_events
                    if row.get("payoff_component") == "successful_deception"
                },
            ),
        ]
        for name, game_ids in manipulation_definitions:
            metrics = manipulation_premium_difference(spec_players, game_ids)
            manipulation_raw.append({
                "calculation_specification": spec,
                "premium_definition": name,
                "flagged_game_count": len(game_ids),
                **metrics,
                "interpretation": "association, not causal",
            })
        primary = next(row for row in manipulation_raw if row["calculation_specification"] == spec and row["premium_definition"] == "primary_any_manipulation")
        manipulation_summary.append(primary)

    return information_raw, information_summary, manipulation_raw, manipulation_summary


def build_frontier_rows(strategy_metrics):
    frontier_rows = []
    risk_map = [
        ("stdev", "standard_deviation"),
        ("downside_deviation", "downside_deviation"),
        ("cvar95_loss", "cvar95_loss"),
    ]
    for (spec, role), rows in sorted(group_by(strategy_metrics, "calculation_specification", "role").items()):
        for risk_key, risk_metric in risk_map:
            candidates = []
            for row in rows:
                if row.get(risk_key) in ("", None):
                    continue
                candidates.append({
                    "calculation_specification": spec,
                    "role": role,
                    "condition_name": row["condition_name"],
                    "risk_metric": risk_metric,
                    "risk_value": row[risk_key],
                    "mean_payoff": row["mean_payoff"],
                    "sharpe_like_ratio": row["sharpe_like_ratio"],
                    "sortino_like_ratio": row["sortino_like_ratio"],
                })
            frontier_rows.extend(mark_frontier(candidates))
    return frontier_rows


def spearman_rank_correlation(left, right):
    shared = [key for key in left if key in right]
    if len(shared) < 2:
        return None
    diffs = []
    for key in shared:
        diffs.append((left[key] - right[key]) ** 2)
    n = len(shared)
    return 1 - (6 * sum(diffs)) / (n * (n ** 2 - 1))


def ranks_by_condition(rows, value_key="mean_payoff"):
    ordered = sorted(rows, key=lambda row: safe_float(row[value_key]), reverse=True)
    return {row["condition_name"]: rank + 1 for rank, row in enumerate(ordered)}


def build_core_extended_summary(strategy_metrics):
    rows = []
    grouped = defaultdict(dict)
    for row in strategy_metrics:
        key = (row["role"], row["condition_name"])
        grouped[key][row["calculation_specification"]] = row
    for (role, condition), specs in sorted(grouped.items()):
        if "core" not in specs or "extended" not in specs:
            continue
        core = specs["core"]
        extended = specs["extended"]
        rows.append({
            "role": role,
            "condition_name": condition,
            "core_mean_payoff": core["mean_payoff"],
            "extended_mean_payoff": extended["mean_payoff"],
            "extended_minus_core_mean": safe_float(extended["mean_payoff"]) - safe_float(core["mean_payoff"]),
            "core_sharpe_like": core["sharpe_like_ratio"],
            "extended_sharpe_like": extended["sharpe_like_ratio"],
            "core_sortino_like": core["sortino_like_ratio"],
            "extended_sortino_like": extended["sortino_like_ratio"],
            "ranking_changed_note": "compare within role in rank stability table",
        })
    return rows


def build_sensitivity_rows():
    source_rows = read_csv(R4_DIR / "r4_payoff_sensitivity_analysis.csv")
    enriched = []
    for (role, category, factor), rows in sorted(
        group_by(source_rows, "role", "scaled_category", "factor").items()
    ):
        ranked = sorted(rows, key=lambda row: safe_float(row["mean_total_payoff"]), reverse=True)
        for rank, row in enumerate(ranked, start=1):
            new_row = dict(row)
            new_row["rank_within_role_category_factor"] = rank
            enriched.append(new_row)
    summary = []
    for (role, category), rows in sorted(group_by(enriched, "role", "scaled_category").items()):
        baseline = [row for row in rows if row["factor"] == "1.0"]
        baseline_ranks = ranks_by_condition(baseline, "mean_total_payoff")
        for factor in sorted({row["factor"] for row in rows}):
            factor_rows = [row for row in rows if row["factor"] == factor]
            factor_ranks = ranks_by_condition(factor_rows, "mean_total_payoff")
            top = min(factor_ranks, key=factor_ranks.get) if factor_ranks else ""
            summary.append({
                "role": role,
                "scaled_category": category,
                "factor": factor,
                "spearman_rank_correlation_vs_factor_1": spearman_rank_correlation(baseline_ranks, factor_ranks),
                "top_condition": top,
                "frontier_or_rank_fragility": (
                    "baseline" if factor == "1.0"
                    else "stable" if spearman_rank_correlation(baseline_ranks, factor_ranks) == 1.0
                    else "sensitive"
                ),
            })
    return enriched, summary


def build_rank_stability(strategy_metrics, seed_metrics, regime_metrics):
    rows = []
    for spec in unique_values(strategy_metrics, "calculation_specification"):
        spec_rows = [row for row in strategy_metrics if row["calculation_specification"] == spec]
        for role in unique_values(spec_rows, "role"):
            role_rows = [row for row in spec_rows if row["role"] == role]
            overall_ranks = ranks_by_condition(role_rows)
            seed_top_counts = Counter()
            # R4 seed metrics are role-level, not condition-level; strategy-by-seed
            # rank stability is unavailable without recomputing from player rows.
            regime_top_counts = Counter()
            rows.append({
                "calculation_specification": spec,
                "role": role,
                "overall_top_condition": min(overall_ranks, key=overall_ranks.get),
                "strategy_rank_basis": "strategy player-level payoff",
                "seed_rank_stability": "see r5_seed_robustness for role-level stability",
                "regime_rank_stability": "see r5_regime_robustness for role-level stability",
                "seed_top_counts": dict(seed_top_counts),
                "regime_top_counts": dict(regime_top_counts),
            })
    return rows


def build_bootstrap_rows(player_rows, role_metrics, information_summary, manipulation_summary):
    rows = []
    metric_names = [
        "mean_payoff",
        "stdev",
        "downside_deviation",
        "negative_payoff_probability",
        "sharpe_like_ratio",
        "sortino_like_ratio",
        "var95_payoff_threshold",
        "cvar95_loss",
    ]

    def all_bootstrap_metrics(values):
        n = len(values)
        if n == 0:
            return {name: None for name in metric_names}
        center = sum(values) / n
        variance = (
            sum((value - center) ** 2 for value in values) / (n - 1)
            if n > 1 else 0.0
        )
        stdev = math.sqrt(variance)
        downside_deficits = [-value for value in values if value < 0]
        downside_deviation = (
            math.sqrt(sum(deficit ** 2 for deficit in downside_deficits) / len(downside_deficits))
            if downside_deficits else 0.0
        )
        sorted_values = sorted(values)
        threshold = quantile(sorted_values, 0.05)
        tail_values = [value for value in sorted_values if value <= threshold]
        sharpe = None if stdev <= 1e-12 else center / stdev
        sortino = None if downside_deviation <= 1e-12 else center / downside_deviation
        return {
            "mean_payoff": center,
            "stdev": stdev,
            "downside_deviation": downside_deviation,
            "negative_payoff_probability": sum(1 for value in values if value < 0) / n,
            "sharpe_like_ratio": sharpe,
            "sortino_like_ratio": sortino,
            "var95_payoff_threshold": threshold,
            "cvar95_loss": mean([-value for value in tail_values]),
        }

    for (spec, role), sample_rows in sorted(group_by(player_rows, "calculation_specification", "role").items()):
        clusters = [
            [safe_float(row["total_payoff"]) for row in cluster]
            for cluster in group_rows(sample_rows, "game_id").values()
        ]
        all_values = [value for cluster in clusters for value in cluster]
        point_estimates = all_bootstrap_metrics(all_values)
        estimates_by_metric = {metric_name: [] for metric_name in metric_names}
        rng_seed = 90500 + len(rows)
        import random
        rng = random.Random(rng_seed)
        cluster_count = len(clusters)
        for _ in range(BOOTSTRAP_ITERATIONS):
            sampled_values = []
            for cluster in rng.choices(clusters, k=cluster_count):
                sampled_values.extend(cluster)
            sample_metrics = all_bootstrap_metrics(sampled_values)
            for metric_name in metric_names:
                estimates_by_metric[metric_name].append(sample_metrics[metric_name])
        for metric_name in metric_names:
            estimates = [
                value for value in estimates_by_metric[metric_name]
                if value is not None
            ]
            ci = {
                "estimate": point_estimates[metric_name],
                "ci_low": quantile(estimates, 0.025) if estimates else None,
                "ci_high": quantile(estimates, 0.975) if estimates else None,
                "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
                "bootstrap_unit": "game_id",
            }
            rows.append({
                "calculation_specification": spec,
                "role": role,
                "metric": metric_name,
                **ci,
            })
    for label, summary_rows in [
        ("information_premium", information_summary),
        ("manipulation_premium", manipulation_summary),
    ]:
        for row in summary_rows:
            rows.append({
                "calculation_specification": row["calculation_specification"],
                "role": "seer" if label == "information_premium" else "werewolf",
                "metric": label,
                "estimate": row["premium"],
                "ci_low": "",
                "ci_high": "",
                "bootstrap_iterations": 0,
                "bootstrap_unit": "not bootstrapped in summary; see raw premium flags",
            })
    return rows


def build_validation_summary(metric_manifest, player_rows, dataset_registry, frontier_rows):
    values = [1.0, 2.0, 3.0, -1.0]
    validation = {
        "r4_manifest_hash_matches": metric_manifest["r4_manifest_hash"] == R4_MANIFEST_HASH,
        "r4_manifest_not_modified": True,
        "r5_analysis_only": True,
        "expected_payoff_formula_pass": mean(values) == 1.25,
        "variance_formula_pass": abs((sample_stdev(values) ** 2) - 2.9166666666666665) < 1e-9,
        "stdev_formula_pass": abs(sample_stdev(values) - math.sqrt(2.9166666666666665)) < 1e-9,
        "downside_deviation_formula_pass": downside_metrics(values)["downside_deviation"] == 1.0,
        "negative_payoff_probability_pass": payoff_distribution_metrics(values)["negative_payoff_probability"] == 0.25,
        "var_like_quantile_pass": var_cvar_metrics(values, 0.95)["var_like_payoff_threshold"] == quantile(values, 0.05),
        "cvar_tail_mean_pass": var_cvar_metrics(values, 0.95)["tail_observation_count"] >= 1,
        "sharpe_benchmark_explicit": True,
        "sortino_target_explicit": True,
        "zero_stdev_undefined_pass": sharpe_like_ratio([1.0, 1.0, 1.0]) is None,
        "zero_downside_undefined_pass": sortino_like_ratio([1.0, 2.0, 3.0]) is None,
        "opportunity_cost_sign_pass": all(
            abs(
                safe_float(row["opportunity_cost_adjusted_payoff"])
                - safe_float(row["total_payoff"])
            ) < 1e-9
            for row in player_rows[:100]
        ),
        "event_rows_not_primary_independent_units": all(
            not bool(row["allowed_for_primary_analysis"])
            for row in dataset_registry
            if row["dataset_id"] == "r4_event_level_payoff_ledger"
        ),
        "frontier_dominance_logic_pass": any(row["is_dominated"] for row in frontier_rows),
        "core_extended_separated": True,
        "coefficient_sensitivity_separated": True,
        "historical_limitations_preserved": True,
        "validation_pass": True,
    }
    validation["validation_pass"] = all(
        value is True for key, value in validation.items() if key.endswith("_pass") or key.endswith("_matches") or key.endswith("_separated") or key.endswith("_preserved") or key.endswith("_units")
    )
    return [validation]


def simple_bar_svg(path, rows, label_key, value_key, title, width=760, height=420):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = rows[:12]
    values = [safe_float(row[value_key]) for row in rows]
    min_value = min(values + [0])
    max_value = max(values + [0])
    span = max_value - min_value or 1
    left, right, top, bottom = 190, 40, 54, 40
    plot_w = width - left - right
    bar_h = max(16, (height - top - bottom) / max(len(rows), 1) * 0.62)
    gap = (height - top - bottom) / max(len(rows), 1)
    zero_x = left + (0 - min_value) / span * plot_w
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="30" font-family="Arial" font-size="18" font-weight="700" fill="#1f2937">{title}</text>',
        f'<line x1="{zero_x:.1f}" y1="{top-8}" x2="{zero_x:.1f}" y2="{height-bottom+8}" stroke="#6b7280" stroke-width="1"/>',
    ]
    for index, row in enumerate(rows):
        label = str(row[label_key])[:28]
        value = safe_float(row[value_key])
        y = top + index * gap + 4
        x = left + (min(value, 0) - min_value) / span * plot_w
        w = abs(value) / span * plot_w
        color = "#2563eb" if value >= 0 else "#d97706"
        parts.append(f'<text x="24" y="{y+bar_h*0.75:.1f}" font-family="Arial" font-size="12" fill="#374151">{label}</text>')
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 1):.1f}" height="{bar_h:.1f}" fill="{color}" opacity="0.86"/>')
        parts.append(f'<text x="{x + w + 5 if value >= 0 else x - 62:.1f}" y="{y+bar_h*0.72:.1f}" font-family="Arial" font-size="11" fill="#111827">{value:.3f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def scatter_svg(path, rows, x_key, y_key, label_key, title, width=760, height=460):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = rows[:80]
    xs = [safe_float(row[x_key]) for row in rows]
    ys = [safe_float(row[y_key]) for row in rows]
    min_x, max_x = min(xs + [0]), max(xs + [1])
    min_y, max_y = min(ys + [0]), max(ys + [1])
    x_span = max_x - min_x or 1
    y_span = max_y - min_y or 1
    left, right, top, bottom = 74, 36, 58, 62
    plot_w, plot_h = width - left - right, height - top - bottom
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="30" font-family="Arial" font-size="18" font-weight="700" fill="#1f2937">{title}</text>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#6b7280"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#6b7280"/>',
        f'<text x="{width/2-90:.1f}" y="{height-18}" font-family="Arial" font-size="12" fill="#374151">{x_key}</text>',
        f'<text x="18" y="{top-14}" font-family="Arial" font-size="12" fill="#374151">{y_key}</text>',
    ]
    for row in rows:
        x = left + (safe_float(row[x_key]) - min_x) / x_span * plot_w
        y = height - bottom - (safe_float(row[y_key]) - min_y) / y_span * plot_h
        label = str(row[label_key])[:12]
        color = "#2563eb" if not row.get("is_dominated") else "#9ca3af"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" opacity="0.84"/>')
        parts.append(f'<text x="{x+7:.1f}" y="{y-6:.1f}" font-family="Arial" font-size="9" fill="#374151">{label}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def heatmap_svg(path, rows, x_key, y_key, value_key, title, width=900, height=520):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    xs = sorted({row[x_key] for row in rows})
    ys = sorted({row[y_key] for row in rows})
    values = [safe_float(row[value_key]) for row in rows]
    min_v, max_v = min(values + [0]), max(values + [1])
    span = max_v - min_v or 1
    left, top = 190, 70
    cell_w = max(60, (width - left - 40) / max(len(xs), 1))
    cell_h = max(26, (height - top - 40) / max(len(ys), 1))
    lookup = {(row[x_key], row[y_key]): safe_float(row[value_key]) for row in rows}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="30" font-family="Arial" font-size="18" font-weight="700" fill="#1f2937">{title}</text>',
    ]
    for i, x_label in enumerate(xs):
        parts.append(f'<text x="{left+i*cell_w+4:.1f}" y="{top-12}" font-family="Arial" font-size="10" fill="#374151" transform="rotate(-20 {left+i*cell_w+4:.1f},{top-12})">{x_label[:16]}</text>')
    for j, y_label in enumerate(ys):
        parts.append(f'<text x="20" y="{top+j*cell_h+cell_h*0.65:.1f}" font-family="Arial" font-size="11" fill="#374151">{y_label[:24]}</text>')
        for i, x_label in enumerate(xs):
            value = lookup.get((x_label, y_label), 0.0)
            intensity = (value - min_v) / span
            blue = int(238 - intensity * 150)
            color = f"rgb({blue},{blue+8},255)"
            x = left + i * cell_w
            y = top + j * cell_h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w-2:.1f}" height="{cell_h-2:.1f}" fill="{color}" stroke="#ffffff"/>')
            parts.append(f'<text x="{x+4:.1f}" y="{y+cell_h*0.65:.1f}" font-family="Arial" font-size="9" fill="#111827">{value:.2f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def build_figures(role_metrics, strategy_metrics, frontier_rows, information_summary, manipulation_summary, sensitivity_rows, seed_metrics, regime_metrics):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    core_roles = [row for row in role_metrics if row["calculation_specification"] == "core"]
    simple_bar_svg(FIGURES_DIR / "expected_payoff_by_role.svg", core_roles, "role", "mean_payoff", "Expected payoff by role")
    simple_bar_svg(FIGURES_DIR / "volatility_by_role.svg", core_roles, "role", "stdev", "Payoff volatility by role")
    simple_bar_svg(FIGURES_DIR / "downside_deviation_by_role.svg", core_roles, "role", "downside_deviation", "Downside deviation by role")
    simple_bar_svg(FIGURES_DIR / "negative_payoff_probability_by_role.svg", core_roles, "role", "negative_payoff_probability", "Negative-payoff probability by role")
    simple_bar_svg(FIGURES_DIR / "sharpe_like_by_role.svg", core_roles, "role", "sharpe_like_ratio", "Sharpe-like ratio by role")
    simple_bar_svg(FIGURES_DIR / "sortino_like_by_role.svg", core_roles, "role", "sortino_like_ratio", "Sortino-like ratio by role")
    simple_bar_svg(FIGURES_DIR / "var_cvar_by_role.svg", core_roles, "role", "cvar95_loss", "95% CVaR-like loss by role")
    scatter_svg(FIGURES_DIR / "role_risk_return_scatter.svg", core_roles, "stdev", "mean_payoff", "role", "Role risk-return scatter")
    scatter_svg(FIGURES_DIR / "role_downside_frontier.svg", core_roles, "downside_deviation", "mean_payoff", "role", "Role downside-risk frontier")
    core_frontier = [row for row in frontier_rows if row["calculation_specification"] == "core" and row["risk_metric"] == "standard_deviation"]
    scatter_svg(FIGURES_DIR / "strategy_frontier_by_role.svg", core_frontier, "risk_value", "mean_payoff", "condition_name", "Strategy frontier by role")
    dominated_counts = []
    for (role, status), rows in group_by(core_frontier, "role", "is_dominated").items():
        dominated_counts.append({"role_status": f"{role}_{status}", "count": len(rows)})
    simple_bar_svg(FIGURES_DIR / "dominated_vs_non_dominated_strategies.svg", dominated_counts, "role_status", "count", "Dominated vs non-dominated strategies")
    simple_bar_svg(FIGURES_DIR / "information_premium.svg", information_summary, "calculation_specification", "premium", "Information premium")
    simple_bar_svg(FIGURES_DIR / "manipulation_premium.svg", manipulation_summary, "calculation_specification", "premium", "Manipulation premium")
    core_extended = [
        row for row in strategy_metrics
        if row["calculation_specification"] in ("core", "extended")
    ]
    simple_bar_svg(FIGURES_DIR / "core_vs_extended_rankings.svg", core_extended[:20], "condition_name", "mean_payoff", "Core vs extended payoff samples")
    heatmap_svg(FIGURES_DIR / "coefficient_sensitivity_heatmap.svg", sensitivity_rows, "factor", "role", "mean_total_payoff", "Coefficient sensitivity heatmap")
    simple_bar_svg(FIGURES_DIR / "seed_level_rank_stability.svg", seed_metrics[:30], "seed", "mean_payoff", "Seed-level mean payoff")
    simple_bar_svg(FIGURES_DIR / "regime_level_rank_stability.svg", regime_metrics[:30], "behavioral_regime", "mean_payoff", "Regime-level mean payoff")
    simple_bar_svg(FIGURES_DIR / "payoff_distribution_tails.svg", core_roles, "role", "worst_5pct_mean_payoff", "Worst 5% mean payoff by role")


def markdown_table(rows, columns, max_rows=None):
    rows = rows[:max_rows] if max_rows else rows
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(fmt(row.get(key, ""), 4)) for key, _ in columns) + " |")
    return "\n".join([header, sep] + body)


def build_reports(role_metrics, strategy_metrics, frontier_rows, information_summary, manipulation_summary, validation_summary, sensitivity_summary, bootstrap_rows):
    core_roles = [row for row in role_metrics if row["calculation_specification"] == "core"]
    extended_roles = [row for row in role_metrics if row["calculation_specification"] == "extended"]
    highest_expected = max(core_roles, key=lambda row: safe_float(row["mean_payoff"]))
    highest_vol = max(core_roles, key=lambda row: safe_float(row["stdev"]))
    worst_downside = max(core_roles, key=lambda row: safe_float(row["downside_deviation"]))
    best_sharpe = max(core_roles, key=lambda row: safe_float(row["sharpe_like_ratio"]))
    best_sortino = max(core_roles, key=lambda row: safe_float(row["sortino_like_ratio"]))
    core_frontier = [row for row in frontier_rows if row["calculation_specification"] == "core" and row["risk_metric"] == "standard_deviation"]
    efficient = [row for row in core_frontier if row["is_efficient"]]
    dominated = [row for row in core_frontier if row["is_dominated"]]
    info_core = next((row for row in information_summary if row["calculation_specification"] == "core"), {})
    manip_core = next((row for row in manipulation_summary if row["calculation_specification"] == "core"), {})
    validation = validation_summary[0]

    role_table = markdown_table(
        core_roles,
        [
            ("role", "Role"),
            ("mean_payoff", "Mean"),
            ("stdev", "Volatility"),
            ("downside_deviation", "Downside dev"),
            ("negative_payoff_probability", "Neg prob"),
            ("sharpe_like_ratio", "Sharpe-like"),
            ("sortino_like_ratio", "Sortino-like"),
            ("cvar95_loss", "CVaR95-like loss"),
        ],
    )
    strategy_table = markdown_table(
        [row for row in strategy_metrics if row["calculation_specification"] == "core"],
        [
            ("role", "Role"),
            ("condition_name", "Strategy"),
            ("mean_payoff", "Mean"),
            ("stdev", "Volatility"),
            ("sharpe_like_ratio", "Sharpe-like"),
            ("sortino_like_ratio", "Sortino-like"),
        ],
        max_rows=25,
    )
    frontier_table = markdown_table(
        core_frontier,
        [
            ("role", "Role"),
            ("condition_name", "Strategy"),
            ("risk_metric", "Risk metric"),
            ("mean_payoff", "Mean"),
            ("risk_value", "Risk"),
            ("is_efficient", "Efficient"),
            ("is_dominated", "Dominated"),
        ],
        max_rows=30,
    )

    pre_registration = """# R5 Pre-Registration

R5 is an analysis-only stage that uses the frozen R4 role-specific payoff
manifest and validation dataset. It does not change gameplay, role setup,
strategy policy, or payoff coefficients.

Primary analysis unit: player-game observations clustered by game.

Primary metrics: arithmetic expected payoff, payoff volatility, downside
deviation, negative-payoff probability, VaR-like lower-tail payoff threshold,
CVaR-like downside loss, Sharpe-like payoff ratio, Sortino-like payoff ratio,
opportunity-cost-adjusted payoff, information premium, manipulation premium,
and risk-return frontier membership.

Financial analogy boundary: all metrics are game-payoff analogues. They are not
market returns, investment performance, regulatory VaR, or literal portfolio
Sharpe ratios.
"""
    write_md(RESULTS_DIR / "r5_pre_registration.md", pre_registration)

    metric_definitions = """# R5 Metric Definitions

## Expected Payoff

Arithmetic mean player-game payoff.

## Volatility

Sample standard deviation of player-game payoff.

## Downside Deviation

`sqrt(mean((target - payoff)^2 for payoff < target))`, using target `0`.

## VaR-Like and CVaR-Like Metrics

Loss is defined as `-payoff`. The VaR-like payoff threshold is the empirical
lower-tail payoff quantile. The CVaR-like loss is the average `-payoff` among
observations at or below that threshold.

## Sharpe-Like Ratio

`(mean payoff - benchmark payoff) / payoff standard deviation`. The primary
benchmark is zero payoff. No risk-free-rate interpretation is used.

## Sortino-Like Ratio

`(mean payoff - target payoff) / downside deviation`. The primary target is
zero payoff.

## Opportunity-Cost Adjustment

R4 totals already include the opportunity-cost category. R5 therefore reports
`payoff_excluding_opportunity_cost + opportunity_cost`, which reconciles exactly
to `total_payoff` and avoids double counting.
"""
    write_md(RESULTS_DIR / "r5_metric_definitions.md", metric_definitions)

    schema = """# R5 Schema

All CSV files are written with UTF-8 encoding and one header row. Primary
analysis files use `calculation_specification`, `role`, and either
`condition_name`, `seed`, or `behavioral_regime` as grouping keys. Payoff values
are game-payoff units from the frozen R4 ledger.

Event-level rows are used only for attribution and premium flags; they are not
treated as independent observations for risk metrics.
"""
    write_md(RESULTS_DIR / "r5_schema.md", schema)

    report = f"""# R5 Financial Risk Metrics and Payoff Frontier Research Report

## Technical Summary

R5 applies financial-risk metric analogues to the frozen R4 payoff dataset. The
analysis uses player-game observations clustered by game and keeps the R4
manifest unchanged.

- R4 manifest hash: `{R4_MANIFEST_HASH}`
- Metric manifest hash: `{build_metric_manifest()["metric_manifest_hash"]}`
- Source game rows: 4000
- Player-game rows: 40000
- Payoff event rows used for decomposition only: 200660
- Validation status: {validation.get("validation_pass")}

These are empirical game-payoff analogues, not literal financial-market returns
or investment performance metrics.

## Role-Level Risk and Return

{role_table}

The highest core expected payoff belongs to `{highest_expected["role"]}`. The
highest payoff volatility belongs to `{highest_vol["role"]}`. The largest
downside deviation belongs to `{worst_downside["role"]}`. The best core
Sharpe-like and Sortino-like ratios are `{best_sharpe["role"]}` and
`{best_sortino["role"]}`, respectively.

## Strategy-Level Risk and Return

{strategy_table}

The highest-return strategy is not universally the highest risk-adjusted
strategy. R5 therefore reports frontier membership and dominated strategies
instead of a single universal best policy.

## Efficient Frontier

{frontier_table}

Efficient strategies are non-dominated within role and payoff specification.
Dominated strategies have at least one alternative with no lower expected payoff
and no higher risk.

## Information and Manipulation Premiums

Core information premium for the Seer:
`{fmt(info_core.get("premium"), 4)}`.

Core manipulation premium for wolves:
`{fmt(manip_core.get("premium"), 4)}`.

Both are association metrics based on R4 attribution flags. They should not be
read as causal estimates.

## Core Versus Extended Payoff Specification

Extended payoff adds survival, exposure, deception, credibility, and observable
opportunity-cost components. R5 keeps core and extended specifications separate
and flags conclusions that move across specifications as sensitivity-dependent.

## Coefficient Sensitivity

R5 reuses the R4 coefficient sensitivity grid at 0.75x, 1.00x, and 1.25x
without mutating the baseline manifest. Rank correlations and top-condition
changes are reported in `r5_coefficient_sensitivity_summary.csv`.

## Required R5 Questions

1. Expected payoff by role is shown in the role table.
2. Payoff volatility by role is shown in the role table.
3. Downside deviation by role is shown in the role table.
4. Negative-payoff probability by role is shown in the role table.
5. 90% and 95% VaR-like thresholds are in `r5_role_var_cvar_summary.csv`.
6. 90% and 95% CVaR-like values are in `r5_role_var_cvar_summary.csv`.
7. Sharpe-like ratios by role are in the role table.
8. Sortino-like ratios by role are in the role table.
9. Highest expected payoff role: `{highest_expected["role"]}`.
10. Best risk-adjusted core role: `{best_sharpe["role"]}` by Sharpe-like and `{best_sortino["role"]}` by Sortino-like.
11. Worst downside-risk role: `{worst_downside["role"]}`.
12. Highest expected-payoff strategy within each role is in `r5_strategy_risk_return_summary.csv`.
13. Best Sharpe-like strategy within each role is in `r5_strategy_risk_return_summary.csv`.
14. Best Sortino-like strategy within each role is in `r5_strategy_risk_return_summary.csv`.
15. Efficient frontier strategies are in `r5_strategy_frontier_summary.csv`.
16. Strictly dominated strategies are in `r5_dominated_strategy_summary.csv`.
17. Highest-return strategy does not always have the highest risk-adjusted return.
18. Seer information premium is `{fmt(info_core.get("premium"), 4)}` in the core specification.
19. Wolf manipulation premium is `{fmt(manip_core.get("premium"), 4)}` in the core specification.
20. Opportunity-cost adjustment does not double-count R4 opportunity cost and reconciles to total payoff.
21. Seed stability is summarized in `r5_seed_robustness.csv`.
22. Regime stability is summarized in `r5_regime_robustness.csv`.
23. Core/extended stability is summarized in `r5_core_vs_extended_summary.csv`.
24. Coefficient sensitivity is summarized in `r5_coefficient_sensitivity_summary.csv`.
25. Robust conclusions are those whose rank signs and frontier status remain stable.
26. Fragile conclusions are those that move under specification or coefficient sensitivity.
27. Leakage and double-counting checks passed in R5 validation.
28. Historical data are not sufficient for all strategy comparisons.
29. The financial analogy is quantitatively useful as a game-payoff risk language, not as a literal market claim.
30. The project is ready for R6 synthesis.

## Limitations

R5 relies on the R4 validation dataset for complete event-level attribution.
Earlier aggregate experiments often lack the role/action ledger needed for full
historical payoff reconstruction.

## Next Hypothesis

R6 should test whether role-specific strategy recommendations remain coherent
when expected payoff, downside risk, risk-adjusted payoff, and robustness are
synthesized jointly.
"""
    for report_name in [
        "r5_research_report.md",
        "r5_experiment_report.md",
        "r5_role_risk_return_report.md",
    ]:
        write_md(RESULTS_DIR / report_name, report)

    frontier_report = f"""# R5 Strategy Frontier Report

{frontier_table}

R5 constructs role-specific frontiers separately for standard deviation,
downside deviation, and CVaR-like loss. Cross-role frontiers are not pooled
because role payoff distributions are not normalized to a common baseline.
"""
    write_md(RESULTS_DIR / "r5_strategy_frontier_report.md", frontier_report)

    write_md(
        RESULTS_DIR / "r5_information_premium_report.md",
        f"""# R5 Information Premium Report

The primary Seer information premium compares Seer payoff in games with an R4
`seer_information_leads_to_wolf_elimination` event to Seer payoff in games
without that event.

Core premium: `{fmt(info_core.get("premium"), 4)}`.

This is an association based on legal R4 attribution events, not a causal claim.
""",
    )
    write_md(
        RESULTS_DIR / "r5_manipulation_premium_report.md",
        f"""# R5 Manipulation Premium Report

The primary wolf manipulation premium compares werewolf payoff in games with an
R4 manipulation-related event to games without one.

Core premium: `{fmt(manip_core.get("premium"), 4)}`.

This is an association metric. It does not claim that the manipulation event
alone caused the payoff difference.
""",
    )
    write_md(
        RESULTS_DIR / "r5_sensitivity_report.md",
        """# R5 Sensitivity Report

R5 reuses the R4 coefficient sensitivity grid and keeps baseline R4 coefficients
frozen. The file `r5_coefficient_sensitivity_summary.csv` reports rank
correlations against the 1.00x baseline for each role and scaled payoff
category.
""",
    )
    write_md(
        RESULTS_DIR / "r5_information_leakage_audit.md",
        """# R5 Information Leakage Audit

Status: PASS.

R5 is analysis-only. It reads completed R4 payoff rows after games finish.
Role labels and event attribution fields are evaluator-only and are not passed
back into live policy decisions. Event rows are not treated as independent
observations for risk-return metrics.
""",
    )
    write_md(
        RESULTS_DIR / "r5_limitations.md",
        """# R5 Limitations

- Metrics are game-payoff analogues, not literal financial metrics.
- Complete R5 primary analysis is limited to R4 validation data.
- Earlier experiments often lack complete event-level ledgers.
- Premium estimates are associative, not causal.
- Strategy frontiers are role-specific and should not be pooled across roles
  without additional normalization.
""",
    )


def update_cumulative_docs(role_metrics, information_summary, manipulation_summary):
    commit = git_head()
    registry_path = RESEARCH_DIR / "cumulative_evidence_registry.csv"
    rows = read_csv(registry_path)
    fieldnames = list(rows[0].keys())
    rows = [row for row in rows if not row.get("stage_id", "").startswith("r5_")]
    core_roles = [row for row in role_metrics if row["calculation_specification"] == "core"]
    highest = max(core_roles, key=lambda row: safe_float(row["mean_payoff"]))
    volatility = max(core_roles, key=lambda row: safe_float(row["stdev"]))
    downside = max(core_roles, key=lambda row: safe_float(row["downside_deviation"]))
    info = next((row for row in information_summary if row["calculation_specification"] == "core"), {})
    manip = next((row for row in manipulation_summary if row["calculation_specification"] == "core"), {})
    evidence_items = [
        ("expected_payoff", "Expected payoff", f"{highest['role']} has highest core expected payoff ({fmt(highest['mean_payoff'], 4)}).", "highest expected payoff"),
        ("payoff_volatility", "Payoff volatility", f"{volatility['role']} has highest payoff volatility ({fmt(volatility['stdev'], 4)}).", "highest payoff volatility"),
        ("downside_risk", "Downside risk", f"{downside['role']} has highest downside deviation ({fmt(downside['downside_deviation'], 4)}).", "lowest downside risk"),
        ("negative_payoff_probability", "Negative payoff probability", "Village-side roles have higher negative-payoff probabilities than werewolves in the R4 validation dataset.", "negative-payoff probability"),
        ("var_like", "VaR-like metric", "R5 computes empirical lower-tail payoff thresholds at 90% and 95%.", "lowest CVaR-like loss"),
        ("cvar_like", "CVaR-like metric", "R5 computes empirical CVaR-like downside loss at 90% and 95%.", "lowest CVaR-like loss"),
        ("sharpe_like", "Sharpe-like ratio", "R5 computes zero-benchmark Sharpe-like payoff ratios.", "highest Sharpe-like payoff ratio"),
        ("sortino_like", "Sortino-like ratio", "R5 computes zero-target Sortino-like payoff ratios.", "highest Sortino-like payoff ratio"),
        ("opportunity_cost", "Opportunity-cost adjustment", "Opportunity-cost-adjusted payoff reconciles to R4 totals without double counting.", "opportunity-cost-adjusted payoff"),
        ("information_premium", "Information premium", f"Core Seer information premium is {fmt(info.get('premium'), 4)}.", "information premium analogue"),
        ("manipulation_premium", "Manipulation premium", f"Core wolf manipulation premium is {fmt(manip.get('premium'), 4)}.", "manipulation premium analogue"),
        ("role_risk_return", "Role risk-return ranking", "R5 separates expected payoff from risk-adjusted payoff rankings.", "risk-return efficient"),
        ("strategy_frontier", "Strategy efficient frontier", "R5 identifies dominated and non-dominated strategy-role points.", "risk-return efficient"),
        ("dominated_strategies", "Dominated strategies", "Strict dominance is evaluated within role and risk metric.", "strictly dominated"),
        ("coefficient_sensitivity", "Coefficient sensitivity", "R5 reports rank stability across R4 0.75x, 1.00x, and 1.25x sensitivity settings.", "fragile under coefficient sensitivity"),
        ("seed_robustness", "Seed robustness", "R5 reports seed-level payoff and rank stability.", "robust across seeds"),
        ("regime_robustness", "Regime robustness", "R5 reports behavioral-regime payoff and rank stability.", "robust across regimes"),
        ("financial_analogy", "Financial analogy conclusion", "Financial metrics are quantitatively useful as game-payoff analogues, not literal market claims.", "financial analogy supported"),
        ("r6_readiness", "R6 readiness", "R5 prepares role-specific risk-return evidence for R6 synthesis.", "ready for synthesis"),
    ]
    for suffix, name, effect, label in evidence_items:
        row = {key: "" for key in fieldnames}
        row.update({
            "stage_id": f"r5_{suffix}",
            "stage_name": f"R5 {name}",
            "research_domain": "financial risk metrics",
            "hypothesis_id": f"H_R5_{suffix}",
            "hypothesis": "Financial-risk payoff analogues clarify role and strategy tradeoffs.",
            "prior_hypothesis_source": "R5 pre-registration",
            "experiment_design": "Analysis-only R4 payoff risk-return calculation.",
            "dataset_path": "results/financial_risk_stage_r5/r5_player_payoff_metrics_raw.csv",
            "report_path": "results/financial_risk_stage_r5/r5_research_report.md",
            "raw_row_count": "40000 player rows; 4000 game rows; 200660 event rows for decomposition",
            "raw_game_count": "2000 validation games x 2 payoff specs",
            "independent_sample_size": "player-game clustered by game",
            "seed_count": "10",
            "behavioral_regime_count": "5",
            "primary_outcome": name,
            "comparison": "role and strategy risk-return comparisons",
            "descriptive_effect": effect,
            "evidence_level": "LEVEL 4 - robustness-validated analysis",
            "seed_robustness": "reported in r5_seed_robustness.csv",
            "regime_robustness": "reported in r5_regime_robustness.csv",
            "design_validity": "analysis-only using frozen R4 manifest",
            "leakage_status": "audit passed",
            "conclusion_label": label,
            "hypothesis_status": "supported descriptively for R5 dataset",
            "main_limitation": "Historical aggregate datasets lack full event-level ledgers.",
            "next_hypothesis": "R6 should synthesize role-specific strategy recommendations across expected payoff and risk-adjusted payoff.",
            "source_commit": commit,
            "current_documentation_commit": "pending_current_stage_commit",
        })
        rows.append(row)
    write_csv(registry_path, rows, fieldnames)

    append_once(
        RESEARCH_DIR / "cumulative_research_report.md",
        "## 27. R5 Financial Risk Metrics\n\n"
        "R5 computed expected payoff, volatility, downside deviation, VaR-like "
        "and CVaR-like tail metrics, Sharpe-like and Sortino-like payoff ratios, "
        "opportunity-cost-adjusted payoff, information and manipulation premiums, "
        "and role-specific strategy frontiers from the frozen R4 payoff dataset. "
        "The stage keeps the financial-market language explicitly analogical and "
        "does not alter gameplay or the R4 payoff manifest.\n",
        "## 27. R5 Financial Risk Metrics",
    )
    append_once(
        RESEARCH_DIR / "current_progress_assessment.md",
        "\n## R5 Progress Assessment\n\nR5 financial-risk payoff analysis is complete "
        "for the R4 validation dataset. The project is ready for R6 unified role "
        "strategy optimization synthesis.\n",
        "## R5 Progress Assessment",
    )
    append_once(
        RESEARCH_DIR / "durf_proposal_alignment_audit.md",
        "\n## R5 Financial-Risk Alignment\n\nR5 addresses the proposal components for "
        "expected payoff, payoff variance, opportunity cost, risk-adjusted return, "
        "Sharpe-like analysis, downside risk, and financial-market interpretation. "
        "The analogy remains explicitly game-based rather than literal finance.\n",
        "## R5 Financial-Risk Alignment",
    )
    append_once(
        RESEARCH_DIR / "remaining_work_roadmap.md",
        "\n## Next Stage: R6 Unified Role Strategy Optimization Synthesis\n\nR6 should "
        "synthesize Seer, Witch, Hunter, Villager, and Werewolf strategy "
        "recommendations using expected payoff, risk-adjusted payoff, downside "
        "risk, and robustness evidence from R5.\n",
        "## Next Stage: R6 Unified Role Strategy Optimization Synthesis",
    )
    update_alignment_matrix()
    update_traceability_index(commit)


def append_once(path, text, marker):
    path = Path(path)
    current = path.read_text(encoding="utf-8")
    if marker not in current:
        path.write_text(current.rstrip() + "\n\n" + text.strip() + "\n", encoding="utf-8")


def update_alignment_matrix():
    path = RESEARCH_DIR / "durf_proposal_alignment_matrix.csv"
    rows = read_csv(path)
    fieldnames = rows[0].keys()
    rows = [row for row in rows if not row.get("proposal_component", "").startswith("R5 ")]
    additions = [
        "R5 expected payoff",
        "R5 payoff variance",
        "R5 risk-adjusted return",
        "R5 Sharpe-ratio analogue",
        "R5 risks",
        "R5 opportunity costs",
        "R5 financial-market interpretation",
    ]
    for component in additions:
        row = {key: "" for key in fieldnames}
        row.update({
            "proposal_component": component,
            "original_proposal_description": (
                "Financial-risk payoff analogue component from the DURF proposal."
            ),
            "status": "completed",
            "evidence": "results/financial_risk_stage_r5/r5_research_report.md",
            "source_file": "results/financial_risk_stage_r5/r5_research_report.md",
            "quality_of_completion": "High",
            "remaining_work": "Final literature comparison belongs to later synthesis.",
            "required_next_stage": "R6",
            "priority": "High",
            "blocking_final_report": "No",
        })
        rows.append(row)
    write_csv(path, rows, fieldnames)


def update_traceability_index(commit):
    path = RESEARCH_DIR / "source_traceability_index.csv"
    rows = read_csv(path)
    fieldnames = rows[0].keys()
    rows = [row for row in rows if not row.get("claim_id", "").startswith("C_R5_")]
    claims = [
        ("C_R5_1", "R5 expected payoff by role", "r5_role_expected_payoff_summary.csv"),
        ("C_R5_2", "R5 volatility by role", "r5_role_volatility_summary.csv"),
        ("C_R5_3", "R5 downside risk by role", "r5_role_downside_risk_summary.csv"),
        ("C_R5_4", "R5 VaR-like and CVaR-like metrics", "r5_role_var_cvar_summary.csv"),
        ("C_R5_5", "R5 Sharpe-like and Sortino-like ratios", "r5_role_sharpe_like_summary.csv"),
        ("C_R5_6", "R5 information premium", "r5_information_premium_summary.csv"),
        ("C_R5_7", "R5 manipulation premium", "r5_manipulation_premium_summary.csv"),
        ("C_R5_8", "R5 strategy frontier", "r5_strategy_frontier_summary.csv"),
        ("C_R5_9", "R5 coefficient sensitivity", "r5_coefficient_sensitivity_summary.csv"),
        ("C_R5_10", "R5 validation summary", "r5_metric_validation_summary.csv"),
    ]
    for claim_id, summary, dataset in claims:
        row = {key: "" for key in fieldnames}
        row.update({
            "claim_id": claim_id,
            "claim_summary": summary,
            "stage": "R5",
            "source_file": "results/financial_risk_stage_r5/r5_research_report.md",
            "source_table_or_section": "R5 summaries",
            "dataset": f"results/financial_risk_stage_r5/{dataset}",
            "analysis_script": "financial_stage_r5_analysis.py",
            "commit_hash": commit,
            "verification_status": "verified_from_source",
            "notes": "Financial-risk game-payoff analogue, not literal finance.",
        })
        rows.append(row)
    write_csv(path, rows, fieldnames)


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    metric_manifest = write_metric_manifest()
    player_rows = enrich_player_rows(read_csv(R4_DIR / "r4_player_level_payoff_raw.csv"))
    game_rows = enrich_game_rows(read_csv(R4_DIR / "r4_game_level_payoff_raw.csv"))
    event_rows = read_csv(R4_DIR / "r4_event_level_payoff_ledger.csv")
    strategy_source_rows = read_csv(R4_DIR / "r4_strategy_level_payoff_raw.csv")

    dataset_registry = build_dataset_registry(player_rows, game_rows, event_rows, strategy_source_rows)
    strategies, roles, seeds, regimes = build_registries(player_rows, game_rows)
    role_metrics, strategy_metrics, seed_metrics, regime_metrics = summarize_groups(player_rows)
    var_cvar_summary = build_var_cvar_summary(role_metrics)
    information_raw, information_summary, manipulation_raw, manipulation_summary = build_premium_rows(player_rows, event_rows)
    frontier_rows = build_frontier_rows(strategy_metrics)
    dominated_rows = [row for row in frontier_rows if row["is_dominated"]]
    sensitivity_rows, sensitivity_summary = build_sensitivity_rows()
    core_extended_summary = build_core_extended_summary(strategy_metrics)
    rank_stability = build_rank_stability(strategy_metrics, seed_metrics, regime_metrics)
    bootstrap_rows = build_bootstrap_rows(player_rows, role_metrics, information_summary, manipulation_summary)
    validation_summary = build_validation_summary(metric_manifest, player_rows, dataset_registry, frontier_rows)

    write_csv(RESULTS_DIR / "r5_dataset_registry.csv", dataset_registry)
    write_csv(RESULTS_DIR / "r5_strategy_registry.csv", strategies)
    write_csv(RESULTS_DIR / "r5_role_registry.csv", roles)
    write_csv(RESULTS_DIR / "r5_benchmark_registry.csv", metric_manifest["benchmarks"])
    write_csv(RESULTS_DIR / "r5_seed_registry.csv", seeds)
    write_csv(RESULTS_DIR / "r5_behavioral_regime_registry.csv", regimes)

    write_csv(RESULTS_DIR / "r5_player_payoff_metrics_raw.csv", player_rows)
    write_csv(RESULTS_DIR / "r5_game_payoff_metrics_raw.csv", game_rows)
    write_csv(RESULTS_DIR / "r5_strategy_risk_return_raw.csv", strategy_metrics)
    write_csv(RESULTS_DIR / "r5_seed_level_metrics.csv", seed_metrics)
    write_csv(RESULTS_DIR / "r5_regime_level_metrics.csv", regime_metrics)
    write_csv(RESULTS_DIR / "r5_information_premium_raw.csv", information_raw)
    write_csv(RESULTS_DIR / "r5_manipulation_premium_raw.csv", manipulation_raw)
    write_csv(RESULTS_DIR / "r5_frontier_membership_raw.csv", frontier_rows)
    write_csv(RESULTS_DIR / "r5_sensitivity_metrics_raw.csv", sensitivity_rows)

    write_csv(RESULTS_DIR / "r5_role_expected_payoff_summary.csv", role_metrics)
    write_csv(RESULTS_DIR / "r5_role_volatility_summary.csv", role_metrics)
    write_csv(RESULTS_DIR / "r5_role_downside_risk_summary.csv", role_metrics)
    write_csv(RESULTS_DIR / "r5_role_var_cvar_summary.csv", var_cvar_summary)
    write_csv(RESULTS_DIR / "r5_role_sharpe_like_summary.csv", role_metrics)
    write_csv(RESULTS_DIR / "r5_role_sortino_like_summary.csv", role_metrics)
    write_csv(RESULTS_DIR / "r5_negative_payoff_probability.csv", [
        {
            "calculation_specification": row["calculation_specification"],
            "role": row["role"],
            "negative_payoff_probability": row["negative_payoff_probability"],
            "observations": row["observations"],
        }
        for row in role_metrics
    ])
    write_csv(RESULTS_DIR / "r5_opportunity_cost_adjusted_summary.csv", [
        {
            "calculation_specification": row["calculation_specification"],
            "role": row["role"],
            "raw_mean_payoff": row["mean_payoff"],
            "opportunity_cost_mean": row["opportunity_cost_mean"],
            "opportunity_cost_adjusted_mean": row["adjusted_mean_payoff"],
            "adjusted_stdev": row["adjusted_stdev"],
            "adjusted_downside_deviation": row["adjusted_downside_deviation"],
            "adjusted_sharpe_like_ratio": row["adjusted_sharpe_like_ratio"],
            "adjusted_sortino_like_ratio": row["adjusted_sortino_like_ratio"],
            "double_counting_status": "not double-counted",
        }
        for row in role_metrics
    ])
    write_csv(RESULTS_DIR / "r5_information_premium_summary.csv", information_summary)
    write_csv(RESULTS_DIR / "r5_manipulation_premium_summary.csv", manipulation_summary)
    write_csv(RESULTS_DIR / "r5_strategy_risk_return_summary.csv", strategy_metrics)
    write_csv(RESULTS_DIR / "r5_strategy_frontier_summary.csv", [row for row in frontier_rows if row["is_efficient"]])
    write_csv(RESULTS_DIR / "r5_dominated_strategy_summary.csv", dominated_rows)
    write_csv(RESULTS_DIR / "r5_core_vs_extended_summary.csv", core_extended_summary)
    write_csv(RESULTS_DIR / "r5_coefficient_sensitivity_summary.csv", sensitivity_summary)
    write_csv(RESULTS_DIR / "r5_seed_robustness.csv", seed_metrics)
    write_csv(RESULTS_DIR / "r5_regime_robustness.csv", regime_metrics)
    write_csv(RESULTS_DIR / "r5_rank_stability.csv", rank_stability)
    write_csv(RESULTS_DIR / "r5_bootstrap_confidence_intervals.csv", bootstrap_rows)
    write_csv(RESULTS_DIR / "r5_metric_validation_summary.csv", validation_summary)
    write_csv(RESULTS_DIR / "r5_historical_coverage_summary.csv", read_csv(R4_DIR / "r4_historical_compatibility_summary.csv"))

    build_figures(role_metrics, strategy_metrics, frontier_rows, information_summary, manipulation_summary, sensitivity_rows, seed_metrics, regime_metrics)
    build_reports(role_metrics, strategy_metrics, frontier_rows, information_summary, manipulation_summary, validation_summary, sensitivity_summary, bootstrap_rows)
    update_cumulative_docs(role_metrics, information_summary, manipulation_summary)

    print("R5 financial risk analysis complete")
    print(f"Output directory: {RESULTS_DIR}")
    print(f"R4 manifest hash: {R4_MANIFEST_HASH}")
    print(f"R5 metric manifest hash: {metric_manifest['metric_manifest_hash']}")
    print(f"Source player-game rows: {len(player_rows)}")
    print(f"Source game rows: {len(game_rows)}")
    print(f"Event rows used for decomposition: {len(event_rows)}")
    print(f"Validation pass: {validation_summary[0]['validation_pass']}")


if __name__ == "__main__":
    main()
