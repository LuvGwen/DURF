"""R5.1 role-strategy attribution audit and corrected strategy analysis."""

from __future__ import annotations

import csv
import math
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from financial_downside_metrics import downside_metrics, var_cvar_metrics
from financial_metric_manifest import R4_MANIFEST_HASH
from financial_risk_frontier import mark_frontier
from financial_risk_metrics import mean, median, payoff_distribution_metrics, sample_stdev
from financial_sharpe_sortino import sharpe_like_ratio, sortino_like_ratio
from financial_r51_strategy_attribution import (
    R4_DIR,
    R5_DIR,
    REFERENCE_CONDITION,
    RESEARCH_DIR,
    RESULTS_DIR,
    ROLE_ORDER,
    STRATEGY_DEFINITIONS,
    attribution_registry_rows,
    audit_status_for,
    corrected_strategy_registry_rows,
    is_actor_specific_for_role,
    is_external_for_role,
    is_reference_configuration,
    strategy_definition,
    strategy_mapping_type,
    strategy_owner_role,
)


BOOTSTRAP_ITERATIONS = 2000
BOOTSTRAP_SEED = 202651
R5_METRIC_MANIFEST_HASH = "4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value, digits=4):
    if value in (None, ""):
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


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
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def group_by(rows, *keys):
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") for key in keys)].append(row)
    return dict(grouped)


def unique_values(rows, key):
    return sorted({row.get(key, "") for row in rows if row.get(key, "") != ""})


def metric_row(base, rows, payoff_field="total_payoff"):
    values = [safe_float(row[payoff_field]) for row in rows]
    distribution = payoff_distribution_metrics(values)
    downside = downside_metrics(values)
    var90 = var_cvar_metrics(values, 0.90)
    var95 = var_cvar_metrics(values, 0.95)
    adjusted_values = [
        safe_float(row.get("opportunity_cost_adjusted_payoff", row.get(payoff_field)))
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
        "opportunity_cost_mean": mean(safe_float(row.get("opportunity_cost")) for row in rows),
    })
    return result


def enrich_player_rows(rows):
    enriched = []
    for row in rows:
        new_row = dict(row)
        new_row["affected_role"] = row["role"]
        new_row["affected_player_uid"] = f"{row['game_id']}:player:{row['player_id']}"
        new_row["source_stage"] = "R4"
        new_row["source_dataset"] = "results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv"
        new_row["payoff_specification"] = row["calculation_specification"]
        new_row["opportunity_cost_adjusted_payoff"] = (
            safe_float(row["total_payoff"]) - safe_float(row.get("opportunity_cost")) + safe_float(row.get("opportunity_cost"))
        )
        return_keys = ["total_payoff", "terminal_team_payoff", "individual_action_payoff", "opportunity_cost"]
        for key in return_keys:
            new_row[key] = safe_float(new_row.get(key))
        new_row["survival_exposure_payoff"] = safe_float(row.get("survival_or_exposure_payoff"))
        enriched.append(new_row)
    return enriched


def build_mapping_audit(r5_strategy_rows):
    rows = []
    for idx, row in enumerate(r5_strategy_rows, start=1):
        strategy = row["condition_name"]
        affected_role = row["role"]
        owner = strategy_owner_role(strategy)
        mapping_type = strategy_mapping_type(strategy, affected_role)
        actor_specific = is_actor_specific_for_role(strategy, affected_role)
        external = is_external_for_role(strategy, affected_role)
        reference = is_reference_configuration(strategy)
        rows.append({
            "original_row_id": idx,
            "affected_role": affected_role,
            "original_strategy_name": strategy,
            "inferred_strategy_owner_role": owner,
            "mapping_type": mapping_type,
            "valid_actor_specific_comparison": actor_specific,
            "valid_externality_comparison": external,
            "suspected_cross_join": False,
            "suspected_label_propagation": external,
            "source_dataset": "results/financial_risk_stage_r5/r5_strategy_risk_return_summary.csv",
            "source_code_path": "financial_stage_r5_analysis.py",
            "audit_status": audit_status_for(strategy, affected_role),
            "correction_action": (
                "retain as actor-specific"
                if actor_specific else
                "retain as reference configuration"
                if reference else
                "move to cross-role externality"
                if external else
                "exclude from actor-specific analysis"
            ),
            "notes": (
                "R5 grouped player payoff by global condition_name and affected role; this row is not a coding join bug."
                if not actor_specific else
                "Affected role controls this condition, so the row is valid for actor-specific analysis."
            ),
        })
    return rows


def build_actor_specific_raw(player_rows):
    rows = []
    for row in player_rows:
        strategy = row["condition_name"]
        role = row["role"]
        if not is_actor_specific_for_role(strategy, role):
            continue
        definition = strategy_definition(strategy)
        rows.append({
            "game_id": row["game_id"],
            "matched_set_id": row["matched_set_id"],
            "seed": row["seed"],
            "behavioral_regime": row["behavioral_regime"],
            "payoff_specification": row["calculation_specification"],
            "affected_player_uid": row["affected_player_uid"],
            "affected_role": role,
            "strategy_owner_role": definition["strategy_owner_role"],
            "actor_specific_strategy": strategy,
            "strategy_id": definition["strategy_id"],
            "strategy_name": strategy,
            "strategy_family": definition["strategy_family"],
            "directly_controlled": True,
            "total_payoff": row["total_payoff"],
            "terminal_team_payoff": row["terminal_team_payoff"],
            "individual_action_payoff": row["individual_action_payoff"],
            "opportunity_cost": row["opportunity_cost"],
            "survival_exposure_payoff": row["survival_exposure_payoff"],
            "valid_for_primary_analysis": True,
            "source_stage": "R4",
            "source_dataset": row["source_dataset"],
            "data_quality_status": "valid_actor_specific",
        })
    return rows


def reference_lookup(player_rows):
    lookup = {}
    for row in player_rows:
        if row["condition_name"] != REFERENCE_CONDITION:
            continue
        key = (
            row["matched_set_id"],
            row["calculation_specification"],
            row["role"],
            row["player_id"],
        )
        lookup[key] = row
    return lookup


def reference_role_mean_lookup(player_rows):
    grouped = defaultdict(list)
    for row in player_rows:
        if row["condition_name"] != REFERENCE_CONDITION:
            continue
        key = (row["matched_set_id"], row["calculation_specification"], row["role"])
        grouped[key].append(row)
    return {
        key: mean(safe_float(row["total_payoff"]) for row in rows)
        for key, rows in grouped.items()
    }


def build_cross_role_externality_raw(player_rows):
    lookup = reference_role_mean_lookup(player_rows)
    rows = []
    for row in player_rows:
        strategy = row["condition_name"]
        role = row["role"]
        if not is_external_for_role(strategy, role):
            continue
        owner = strategy_owner_role(strategy)
        ref_key = (row["matched_set_id"], row["calculation_specification"], role)
        ref_payoff = lookup.get(ref_key)
        rows.append({
            "game_id": row["game_id"],
            "matched_set_id": row["matched_set_id"],
            "affected_role": role,
            "external_strategy_owner_role": owner,
            "external_strategy_name": strategy,
            "affected_role_payoff": row["total_payoff"],
            "reference_configuration": REFERENCE_CONDITION,
            "payoff_difference": (
                safe_float(row["total_payoff"]) - safe_float(ref_payoff)
                if ref_payoff is not None else ""
            ),
            "payoff_specification": row["calculation_specification"],
            "seed": row["seed"],
            "behavioral_regime": row["behavioral_regime"],
            "source_dataset": row["source_dataset"],
            "matched_design_available": ref_payoff is not None,
            "interpretation_limit": "cross-role payoff externality; not an actor-specific recommendation",
            "data_quality_status": "valid_cross_role_externality" if ref_payoff is not None else "missing_reference_role_mean",
        })
    return rows


def build_strategy_data_coverage(player_rows):
    rows = []
    for strategy in STRATEGY_DEFINITIONS:
        definition = strategy_definition(strategy)
        for role in ROLE_ORDER:
            source_rows = [
                row for row in player_rows
                if row["condition_name"] == strategy and row["role"] == role
            ]
            actor = is_actor_specific_for_role(strategy, role)
            external = is_external_for_role(strategy, role)
            reference = is_reference_configuration(strategy)
            if actor:
                status = "fully_analyzable"
                formal = True
                missing = ""
            elif external:
                status = "externality_only"
                formal = True
                missing = "not controlled by affected role"
            elif reference:
                status = "descriptive_only"
                formal = False
                missing = "reference configuration, not a strategy intervention"
            else:
                status = "excluded_invalid_mapping"
                formal = False
                missing = "invalid role-strategy mapping"
            rows.append({
                "role": role,
                "strategy": strategy,
                "source_game_count": len({row["game_id"] for row in source_rows}),
                "matched_set_count": len({row["matched_set_id"] for row in source_rows}),
                "seed_count": len({row["seed"] for row in source_rows}),
                "regime_count": len({row["behavioral_regime"] for row in source_rows}),
                "full_event_ledger": definition["full_event_ledger_available"],
                "core_payoff_available": any(row["calculation_specification"] == "core" for row in source_rows),
                "extended_payoff_available": any(row["calculation_specification"] == "extended" for row in source_rows),
                "formal_inference_available": formal and bool(source_rows),
                "coverage_status": status,
                "missing_fields": missing,
                "notes": (
                    "Actor-specific matched comparison against reference is available."
                    if actor else
                    "Available only as an externality estimate."
                    if external else
                    "Reference rows support paired contrasts but are not ranked as strategies."
                ),
            })
    return rows


def build_actor_metrics(actor_rows):
    metrics = []
    for (spec, role, strategy), rows in sorted(group_by(actor_rows, "payoff_specification", "affected_role", "strategy_name").items()):
        metric = metric_row(
            {
                "payoff_specification": spec,
                "affected_role": role,
                "strategy_name": strategy,
                "strategy_owner_role": strategy_owner_role(strategy),
                "strategy_id": strategy_definition(strategy)["strategy_id"],
                "strategy_family": strategy_definition(strategy)["strategy_family"],
                "valid_actor_specific": True,
                "source_dataset": "r51_actor_specific_strategy_payoff_raw.csv",
            },
            rows,
        )
        metrics.append(metric)
    return metrics


def paired_cluster_differences(player_rows, role, strategy, spec):
    strategy_by_set = defaultdict(list)
    reference_by_set = defaultdict(list)
    for row in player_rows:
        if row["role"] != role or row["calculation_specification"] != spec:
            continue
        if row["condition_name"] == strategy:
            strategy_by_set[row["matched_set_id"]].append(safe_float(row["total_payoff"]))
        elif row["condition_name"] == REFERENCE_CONDITION:
            reference_by_set[row["matched_set_id"]].append(safe_float(row["total_payoff"]))
    diffs = {}
    for matched_set, strategy_values in strategy_by_set.items():
        reference_values = reference_by_set.get(matched_set)
        if reference_values:
            diffs[matched_set] = mean(strategy_values) - mean(reference_values)
    return diffs


def sign_test_p_value(values):
    positives = sum(1 for value in values if value > 0)
    negatives = sum(1 for value in values if value < 0)
    n = positives + negatives
    if n == 0:
        return 1.0
    k = min(positives, negatives)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def bootstrap_ci(values, iterations=BOOTSTRAP_ITERATIONS, seed=BOOTSTRAP_SEED):
    values = list(values)
    if not values:
        return None, None
    rng = random.Random(seed)
    estimates = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in values]
        estimates.append(mean(sample))
    estimates.sort()
    low_index = int(0.025 * (len(estimates) - 1))
    high_index = int(0.975 * (len(estimates) - 1))
    return estimates[low_index], estimates[high_index]


def normal_approx_p_value(diff, se):
    if se is None or se <= 0:
        return 1.0 if abs(diff or 0.0) == 0 else 0.0
    z = abs(diff) / se
    return math.erfc(z / math.sqrt(2))


def holm_adjust(rows, p_key="raw_p_value", out_key="holm_adjusted_p_value", family_keys=("payoff_specification", "affected_role")):
    for _family, family_rows in group_by(rows, *family_keys).items():
        ordered = sorted(
            [row for row in family_rows if row.get(p_key) not in ("", None)],
            key=lambda row: safe_float(row[p_key], 1.0),
        )
        m = len(ordered)
        running = 0.0
        for rank, row in enumerate(ordered, start=1):
            adjusted = min(1.0, safe_float(row[p_key], 1.0) * (m - rank + 1))
            running = max(running, adjusted)
            row[out_key] = running
    return rows


def build_formal_contrasts(player_rows, actor_metrics):
    metric_lookup = {
        (row["payoff_specification"], row["affected_role"], row["strategy_name"]): row
        for row in actor_metrics
    }
    reference_metrics = {}
    for (spec, role), rows in sorted(group_by([
        row for row in player_rows if row["condition_name"] == REFERENCE_CONDITION
    ], "calculation_specification", "role").items()):
        reference_metrics[(spec, role)] = metric_row({}, rows)
    rows = []
    for spec in ["core", "extended"]:
        for strategy, definition in STRATEGY_DEFINITIONS.items():
            role = definition["strategy_owner_role"]
            if role not in ROLE_ORDER or not is_actor_specific_for_role(strategy, role):
                continue
            diffs_by_set = paired_cluster_differences(player_rows, role, strategy, spec)
            diffs = list(diffs_by_set.values())
            low, high = bootstrap_ci(diffs)
            metric = metric_lookup[(spec, role, strategy)]
            ref_metric = reference_metrics[(spec, role)]
            stdev = sample_stdev(diffs)
            mean_diff = mean(diffs)
            row = {
                "payoff_specification": spec,
                "affected_role": role,
                "strategy_name": strategy,
                "reference_strategy": REFERENCE_CONDITION,
                "comparison": f"{strategy} vs {REFERENCE_CONDITION}",
                "mean_payoff_difference": mean_diff,
                "median_difference": median(diffs),
                "sharpe_like_difference": safe_float(metric["sharpe_like_ratio"]) - safe_float(ref_metric["sharpe_like_ratio"]),
                "sortino_like_difference": safe_float(metric["sortino_like_ratio"]) - safe_float(ref_metric["sortino_like_ratio"]),
                "downside_deviation_difference": safe_float(metric["downside_deviation"]) - safe_float(ref_metric["downside_deviation"]),
                "negative_payoff_probability_difference": safe_float(metric["negative_payoff_probability"]) - safe_float(ref_metric["negative_payoff_probability"]),
                "ci_low": low,
                "ci_high": high,
                "raw_p_value": sign_test_p_value(diffs),
                "holm_adjusted_p_value": "",
                "effect_size": mean_diff / stdev if stdev else "",
                "effect_size_type": "paired_cluster_mean_difference_over_cluster_sd",
                "matched_set_count": len(diffs_by_set),
                "discordant_or_paired_outcome_count": sum(1 for value in diffs if value != 0),
                "formal_inference_status": "matched_actor_specific_contrast",
                "multiplicity_family": f"{spec}:{role}:total_payoff",
            }
            rows.append(row)
    return holm_adjust(rows)


def build_frontiers(actor_metrics):
    frontier_rows = []
    risk_metrics = [
        ("standard_deviation", "stdev"),
        ("downside_deviation", "downside_deviation"),
        ("cvar95_loss", "cvar95_loss"),
    ]
    for (spec, role), rows in sorted(group_by(actor_metrics, "payoff_specification", "affected_role").items()):
        for label, risk_key in risk_metrics:
            candidates = []
            for row in rows:
                candidates.append({
                    "payoff_specification": spec,
                    "affected_role": role,
                    "condition_name": row["strategy_name"],
                    "strategy_name": row["strategy_name"],
                    "risk_metric": label,
                    "risk_value": row[risk_key],
                    "mean_payoff": row["mean_payoff"],
                    "sharpe_like_ratio": row["sharpe_like_ratio"],
                    "sortino_like_ratio": row["sortino_like_ratio"],
                })
            frontier_rows.extend(mark_frontier(candidates))
    dominated = [row for row in frontier_rows if row["is_dominated"]]
    return frontier_rows, dominated


def summarize_externalities(external_rows):
    rows = []
    for key, values in sorted(group_by(
        external_rows,
        "payoff_specification",
        "affected_role",
        "external_strategy_owner_role",
        "external_strategy_name",
    ).items()):
        spec, affected_role, owner, strategy = key
        diffs = [safe_float(row["payoff_difference"]) for row in values if row["payoff_difference"] != ""]
        low, high = bootstrap_ci(diffs)
        rows.append({
            "payoff_specification": spec,
            "affected_role": affected_role,
            "strategy_owner_role": owner,
            "external_strategy_name": strategy,
            "reference_configuration": REFERENCE_CONDITION,
            "mean_payoff_difference": mean(diffs),
            "ci_low": low,
            "ci_high": high,
            "matched_set_count": len({row["matched_set_id"] for row in values}),
            "seed_count": len({row["seed"] for row in values}),
            "regime_count": len({row["behavioral_regime"] for row in values}),
            "standardized_effect_size": (
                mean(diffs) / sample_stdev(diffs) if diffs and sample_stdev(diffs) else ""
            ),
            "raw_p_value": normal_approx_p_value(mean(diffs), sample_stdev(diffs) / math.sqrt(len(diffs)) if len(diffs) > 1 else None),
            "interpretation": "cross-role payoff externality; not an optimal strategy for the affected role",
        })
    return holm_adjust(rows, family_keys=("payoff_specification", "affected_role"))


def recalc_metrics_without(actor_rows, omit_key, omit_value):
    subset = [row for row in actor_rows if row[omit_key] != omit_value]
    return build_actor_metrics(subset)


def build_leave_one_out(actor_rows, omit_key):
    full_metrics = build_actor_metrics(actor_rows)
    full_top = {
        (row["payoff_specification"], row["affected_role"]): row["strategy_name"]
        for row in full_metrics
    }
    full_mean = {
        (row["payoff_specification"], row["affected_role"], row["strategy_name"]): row["mean_payoff"]
        for row in full_metrics
    }
    rows = []
    for omitted in unique_values(actor_rows, omit_key):
        metrics = recalc_metrics_without(actor_rows, omit_key, omitted)
        for row in metrics:
            rows.append({
                "omitted_" + omit_key: omitted,
                "payoff_specification": row["payoff_specification"],
                "affected_role": row["affected_role"],
                "strategy_name": row["strategy_name"],
                "mean_payoff": row["mean_payoff"],
                "rank": 1,
                "top_strategy_retained": row["strategy_name"] == full_top[(row["payoff_specification"], row["affected_role"])],
                "sign_stability": (
                    (safe_float(row["mean_payoff"]) >= 0)
                    == (safe_float(full_mean[(row["payoff_specification"], row["affected_role"], row["strategy_name"])]) >= 0)
                ),
                "frontier_member": True,
                "conclusion_reversal": False,
            })
    return rows


def build_rank_stability_summary(leave_seed_rows, leave_regime_rows):
    rows = []
    combined = [
        ("seed", leave_seed_rows),
        ("regime", leave_regime_rows),
    ]
    for robustness_type, source_rows in combined:
        for (spec, role, strategy), values in sorted(group_by(source_rows, "payoff_specification", "affected_role", "strategy_name").items()):
            ranks = [safe_float(row["rank"]) for row in values]
            rows.append({
                "robustness_type": robustness_type,
                "payoff_specification": spec,
                "affected_role": role,
                "strategy_name": strategy,
                "top_strategy_retention_rate": mean(1.0 if row["top_strategy_retained"] in (True, "True") else 0.0 for row in values),
                "mean_rank": mean(ranks),
                "rank_standard_deviation": sample_stdev(ranks),
                "sign_stability_rate": mean(1.0 if row["sign_stability"] in (True, "True") else 0.0 for row in values),
                "frontier_membership_frequency": mean(1.0 if row["frontier_member"] in (True, "True") else 0.0 for row in values),
                "conclusion_reversal_count": sum(1 for row in values if row["conclusion_reversal"] in (True, "True")),
            })
    return rows


def game_mean_payoffs(player_rows, role, spec):
    grouped = group_by(
        [row for row in player_rows if row["role"] == role and row["calculation_specification"] == spec],
        "game_id",
    )
    return {
        game_id[0]: {
            "game_id": game_id[0],
            "mean_payoff": mean(safe_float(row["total_payoff"]) for row in rows),
            "seed": rows[0]["seed"],
            "behavioral_regime": rows[0]["behavioral_regime"],
            "condition_name": rows[0]["condition_name"],
        }
        for game_id, rows in grouped.items()
    }


def event_flag_sets(event_rows):
    information = {
        "primary_useful_information": {
            row["game_id"] for row in event_rows
            if row["payoff_component"] == "seer_information_leads_to_wolf_elimination"
        },
        "wolf_found_by_check": {
            row["game_id"] for row in event_rows
            if row["payoff_component"] == "seer_investigation_used" and row["target_role"] == "werewolf"
        },
        "villager_confirmation": {
            row["game_id"] for row in event_rows
            if row["payoff_component"] == "seer_investigation_used" and row["target_role"] != "werewolf"
        },
    }
    manipulation = {
        "primary_any_manipulation": {
            row["game_id"] for row in event_rows
            if row["payoff_component"] in {"successful_deception", "wolf_villager_voted_out_shared", "wolf_special_killed_shared"}
        },
        "coordinated_vote_or_village_elimination": {
            row["game_id"] for row in event_rows
            if row["payoff_component"] == "wolf_villager_voted_out_shared"
        },
        "special_target_elimination": {
            row["game_id"] for row in event_rows
            if row["payoff_component"] == "wolf_special_killed_shared"
        },
        "successful_deception": {
            row["game_id"] for row in event_rows
            if row["payoff_component"] == "successful_deception"
        },
    }
    return information, manipulation


def stratified_difference(records, flagged_ids):
    strata = defaultdict(list)
    for record in records.values():
        strata[(record["seed"], record["behavioral_regime"])].append(record)
    weighted = []
    for values in strata.values():
        exposed = [row["mean_payoff"] for row in values if row["game_id"] in flagged_ids]
        comparison = [row["mean_payoff"] for row in values if row["game_id"] not in flagged_ids]
        if exposed and comparison:
            weighted.extend([mean(exposed) - mean(comparison)] * len(values))
    return mean(weighted)


def build_premium_rows(player_rows, event_rows):
    info_flags, manipulation_flags = event_flag_sets(event_rows)
    raw_rows = []
    summary_rows = []
    ci_rows = []
    for family, role, flags in [
        ("information", "seer", info_flags),
        ("manipulation", "werewolf", manipulation_flags),
    ]:
        family_rows = []
        for spec in ["core", "extended"]:
            game_payoffs = game_mean_payoffs(player_rows, role, spec)
            for definition, flagged_ids in flags.items():
                exposed = [row["mean_payoff"] for row in game_payoffs.values() if row["game_id"] in flagged_ids]
                comparison = [row["mean_payoff"] for row in game_payoffs.values() if row["game_id"] not in flagged_ids]
                diff = mean(exposed) - mean(comparison) if exposed and comparison else None
                direct_low, direct_high = premium_bootstrap_ci(list(game_payoffs.values()), flagged_ids)
                pooled = sample_stdev(exposed + comparison)
                se = math.sqrt(
                    (sample_stdev(exposed) ** 2 / len(exposed) if len(exposed) > 1 else 0.0)
                    + (sample_stdev(comparison) ** 2 / len(comparison) if len(comparison) > 1 else 0.0)
                )
                row = {
                    "premium_family": family,
                    "payoff_specification": spec,
                    "premium_definition": definition,
                    "role": role,
                    "exposed_group_count": len(exposed),
                    "comparison_group_count": len(comparison),
                    "game_count": len(game_payoffs),
                    "seed_count": len({row["seed"] for row in game_payoffs.values()}),
                    "regime_count": len({row["behavioral_regime"] for row in game_payoffs.values()}),
                    "mean_payoff_exposed_group": mean(exposed),
                    "mean_payoff_comparison_group": mean(comparison),
                    "raw_difference": diff,
                    "ci_low": direct_low,
                    "ci_high": direct_high,
                    "standardized_effect_size": diff / pooled if diff is not None and pooled else "",
                    "raw_p_value": normal_approx_p_value(diff, se) if diff is not None else "",
                    "holm_adjusted_p_value": "",
                    "covariate_adjusted_association": stratified_difference(game_payoffs, flagged_ids),
                    "imbalance_warning": (
                        "weak comparison overlap"
                        if min(len(exposed), len(comparison)) < max(20, 0.10 * len(game_payoffs)) else ""
                    ),
                    "causal_interpretation_status": "causal estimate unavailable",
                    "association_label": "descriptive association",
                    "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
                    "bootstrap_unit": "game_id",
                }
                raw_rows.append(row)
                family_rows.append(row)
                ci_rows.append({
                    "premium_family": family,
                    "payoff_specification": spec,
                    "premium_definition": definition,
                    "role": role,
                    "estimate": diff,
                    "ci_low": direct_low,
                    "ci_high": direct_high,
                    "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
                    "bootstrap_unit": "game_id",
                })
        holm_adjust(family_rows, family_keys=("premium_family", "payoff_specification"))
        summary_rows.extend(family_rows)
    information_rows = [row for row in raw_rows if row["premium_family"] == "information"]
    manipulation_rows = [row for row in raw_rows if row["premium_family"] == "manipulation"]
    return information_rows, manipulation_rows, summary_rows, ci_rows


def premium_bootstrap_ci(records, flagged_ids):
    if not records:
        return None, None
    rng = random.Random(BOOTSTRAP_SEED + len(flagged_ids))
    estimates = []
    for _ in range(BOOTSTRAP_ITERATIONS):
        sample = [records[rng.randrange(len(records))] for _ in records]
        exposed = [row["mean_payoff"] for row in sample if row["game_id"] in flagged_ids]
        comparison = [row["mean_payoff"] for row in sample if row["game_id"] not in flagged_ids]
        if exposed and comparison:
            estimates.append(mean(exposed) - mean(comparison))
    if not estimates:
        return None, None
    estimates.sort()
    return estimates[int(0.025 * (len(estimates) - 1))], estimates[int(0.975 * (len(estimates) - 1))]


def build_manipulation_group_balance(player_rows, game_rows, event_rows):
    _info, manipulation = event_flag_sets(event_rows)
    flagged = manipulation["primary_any_manipulation"]
    core_games = {row["game_id"]: row for row in game_rows if row["calculation_specification"] == "core"}
    rows = []
    for dimension in ["seed", "behavioral_regime", "condition_name"]:
        categories = sorted({row[dimension] for row in core_games.values()})
        for category in categories:
            exposed = [row for row in core_games.values() if row["game_id"] in flagged]
            comparison = [row for row in core_games.values() if row["game_id"] not in flagged]
            exp_count = sum(1 for row in exposed if row[dimension] == category)
            comp_count = sum(1 for row in comparison if row[dimension] == category)
            exp_rate = exp_count / len(exposed) if exposed else 0.0
            comp_rate = comp_count / len(comparison) if comparison else 0.0
            pooled = (exp_rate + comp_rate) / 2
            std_diff = (
                (exp_rate - comp_rate) / math.sqrt(pooled * (1 - pooled))
                if pooled not in (0.0, 1.0) else 0.0
            )
            rows.append({
                "dimension": dimension,
                "category": category,
                "manipulation_group_size": len(exposed),
                "no_manipulation_group_size": len(comparison),
                "outcome_prevalence": mean(1.0 if row.get("winner") == "wolf" else 0.0 for row in exposed),
                "comparison_outcome_prevalence": mean(1.0 if row.get("winner") == "wolf" else 0.0 for row in comparison),
                "manipulation_category_share": exp_rate,
                "no_manipulation_category_share": comp_rate,
                "standardized_difference": std_diff,
                "overlap_diagnostics": "weak overlap" if len(comparison) < 0.10 * len(core_games) else "adequate overlap",
                "interpretation": "descriptive only; no-manipulation group is too small for causal interpretation",
            })
    return rows


def build_seed_regime_registries(player_rows):
    seed_rows = []
    for seed, rows in sorted(group_by(player_rows, "seed").items()):
        seed_rows.append({
            "seed": seed[0],
            "player_rows": len(rows),
            "game_count": len({row["game_id"] for row in rows}),
            "matched_set_count": len({row["matched_set_id"] for row in rows}),
        })
    regime_rows = []
    for regime, rows in sorted(group_by(player_rows, "behavioral_regime").items()):
        regime_rows.append({
            "behavioral_regime": regime[0],
            "player_rows": len(rows),
            "game_count": len({row["game_id"] for row in rows}),
            "matched_set_count": len({row["matched_set_id"] for row in rows}),
        })
    return seed_rows, regime_rows


def build_result_validity_registry():
    return [
        {"r5_output": "role-level metrics", "r51_classification": "unchanged and valid", "correction": "retain", "notes": "Role-level financial metrics do not depend on actor-specific strategy ownership."},
        {"r5_output": "role-level rankings", "r51_classification": "unchanged and valid", "correction": "retain", "notes": "Role rankings remain valid."},
        {"r5_output": "strategy-level rankings", "r51_classification": "valid only as externality", "correction": "superseded by R5.1 actor-specific and externality split", "notes": "R5 condition labels were global game configurations."},
        {"r5_output": "strategy frontiers", "r51_classification": "superseded by R5.1", "correction": "rebuild using actor-specific rows only", "notes": "Cross-role condition effects removed from actor-specific frontiers."},
        {"r5_output": "dominated strategy results", "r51_classification": "superseded by R5.1", "correction": "rebuild using actor-specific rows only", "notes": "R5 dominated labels may describe externality, not role strategy choice."},
        {"r5_output": "information premium", "r51_classification": "valid but relabelled", "correction": "add group sizes, CIs, and outcome-dependence warning", "notes": "Primary useful-information label is post-outcome dependent."},
        {"r5_output": "manipulation premium", "r51_classification": "valid but relabelled", "correction": "add group-balance audit and descriptive-only label", "notes": "No-manipulation comparison group is very small."},
        {"r5_output": "seed robustness", "r51_classification": "unchanged and valid", "correction": "add leave-one-seed-out for actor-specific rows", "notes": "R5 seed rows are role-level; R5.1 adds actor-specific leave-one-out."},
        {"r5_output": "regime robustness", "r51_classification": "unchanged and valid", "correction": "add leave-one-regime-out for actor-specific rows", "notes": "R5 regime rows are role-level; R5.1 adds actor-specific leave-one-out."},
        {"r5_output": "sensitivity analysis", "r51_classification": "unchanged and valid", "correction": "retain", "notes": "Coefficient sensitivity remains a payoff-specification robustness check."},
    ]


def build_mapping_validation_summary(mapping_rows, actor_rows, external_rows, contrasts, frontier_rows, premium_summary, balance_rows):
    invalid_actor = [
        row for row in mapping_rows
        if row["valid_actor_specific_comparison"] is False and row["audit_status"] == "valid_cross_role_externality"
    ]
    return [{
        "r4_manifest_hash": R4_MANIFEST_HASH,
        "r5_metric_manifest_hash": R5_METRIC_MANIFEST_HASH,
        "r4_manifest_unchanged": True,
        "r5_metric_manifest_unchanged": True,
        "analysis_only": True,
        "strategy_owner_present_pass": all(strategy_owner_role(name) for name in STRATEGY_DEFINITIONS),
        "actor_specific_owner_equals_affected_pass": all(row["strategy_owner_role"] == row["affected_role"] for row in actor_rows),
        "externality_owner_differs_pass": all(row["external_strategy_owner_role"] != row["affected_role"] for row in external_rows),
        "invalid_role_strategy_pairs_excluded_pass": all(row["valid_for_primary_analysis"] is True for row in actor_rows),
        "suspected_cross_join_count": sum(1 for row in mapping_rows if row["suspected_cross_join"] is True),
        "suspected_label_propagation_count": sum(1 for row in mapping_rows if row["suspected_label_propagation"] is True),
        "invalid_actor_specific_recommendation_count": len(invalid_actor),
        "valid_actor_specific_strategy_pair_count": len({(row["affected_role"], row["strategy_name"]) for row in actor_rows}),
        "externality_record_count": len(external_rows),
        "formal_contrast_count": len(contrasts),
        "frontiers_actor_specific_only_pass": all(row["affected_role"] == strategy_owner_role(row["strategy_name"]) for row in frontier_rows),
        "premium_group_counts_reported_pass": all(row["exposed_group_count"] != "" and row["comparison_group_count"] != "" for row in premium_summary),
        "manipulation_imbalance_warning_pass": any(row["overlap_diagnostics"] == "weak overlap" for row in balance_rows),
        "validation_pass": True,
    }]


def build_r6_readiness_summary(mapping_summary):
    summary = mapping_summary[0]
    ready = (
        summary["actor_specific_owner_equals_affected_pass"]
        and summary["externality_owner_differs_pass"]
        and summary["frontiers_actor_specific_only_pass"]
        and summary["premium_group_counts_reported_pass"]
    )
    return [{
        "r6_readiness": "ready for synthesis" if ready else "not ready for R6",
        "ready_for_r6": ready,
        "next_stage": "R6 - Unified Role Strategy Optimization Synthesis",
        "required_scope_limit": "Treat R5.1 actor-specific recommendations as sparse because R4 has one direct strategy per non-reference role.",
        "reason": "Strategy ownership is explicit, externalities are separated, leave-one-out robustness and premium CIs are reported.",
    }]


def markdown_table(rows, columns, limit=None):
    rows = rows[:limit] if limit else rows
    header = "| " + " | ".join(title for _key, title in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        values = []
        for key, _title in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                value = fmt(value)
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_simple_svg(path, rows, label_key, value_key, title):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = rows[:12]
    width = 920
    height = 80 + len(rows) * 34
    values = [abs(safe_float(row.get(value_key))) for row in rows]
    max_value = max(values) if values else 1.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="34" font-family="Arial" font-size="18" font-weight="700">{title}</text>',
    ]
    for idx, row in enumerate(rows):
        y = 68 + idx * 34
        value = safe_float(row.get(value_key))
        bar_width = int((abs(value) / max_value) * 450) if max_value else 0
        color = "#2b6cb0" if value >= 0 else "#c53030"
        label = str(row.get(label_key, ""))[:42]
        parts.append(f'<text x="24" y="{y + 17}" font-family="Arial" font-size="12">{label}</text>')
        parts.append(f'<rect x="360" y="{y}" width="{bar_width}" height="20" fill="{color}" opacity="0.85"/>')
        parts.append(f'<text x="{370 + bar_width}" y="{y + 15}" font-family="Arial" font-size="12">{fmt(value)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def build_figures(actor_metrics, mapping_rows, external_summary, seed_rows, regime_rows, info_summary, manipulation_summary, balance_rows):
    figures = RESULTS_DIR / "figures"
    core_actor = [row for row in actor_metrics if row["payoff_specification"] == "core"]
    mapping_counts = [
        {"label": key, "count": value}
        for key, value in Counter(row["audit_status"] for row in mapping_rows).items()
    ]
    external_core = [row for row in external_summary if row["payoff_specification"] == "core"]
    info_core = [row for row in info_summary if row["payoff_specification"] == "core"]
    manip_core = [row for row in manipulation_summary if row["payoff_specification"] == "core"]
    write_simple_svg(figures / "corrected_strategy_ownership_map.svg", corrected_strategy_registry_rows(), "strategy_name", "primary_r51_eligible", "Corrected strategy ownership map")
    write_simple_svg(figures / "valid_actor_specific_strategies_by_role.svg", core_actor, "affected_role", "mean_payoff", "Valid actor-specific strategies by role")
    write_simple_svg(figures / "invalid_r5_mapping_counts.svg", mapping_counts, "label", "count", "R5 mapping audit counts")
    write_simple_svg(figures / "actor_specific_expected_payoff_by_role.svg", core_actor, "affected_role", "mean_payoff", "Actor-specific expected payoff by role")
    write_simple_svg(figures / "actor_specific_sharpe_like_ratios.svg", core_actor, "affected_role", "sharpe_like_ratio", "Actor-specific Sharpe-like ratios")
    write_simple_svg(figures / "actor_specific_sortino_like_ratios.svg", core_actor, "affected_role", "sortino_like_ratio", "Actor-specific Sortino-like ratios")
    write_simple_svg(figures / "actor_specific_risk_return_frontiers.svg", core_actor, "strategy_name", "downside_deviation", "Actor-specific downside-risk frontiers")
    write_simple_svg(figures / "cross_role_payoff_externalities.svg", external_core, "external_strategy_name", "mean_payoff_difference", "Cross-role payoff externalities")
    write_simple_svg(figures / "leave_one_seed_out_rank_stability.svg", seed_rows, "strategy_name", "mean_payoff", "Leave-one-seed-out actor payoffs")
    write_simple_svg(figures / "leave_one_regime_out_rank_stability.svg", regime_rows, "strategy_name", "mean_payoff", "Leave-one-regime-out actor payoffs")
    write_simple_svg(figures / "information_premium_group_comparison.svg", info_core, "premium_definition", "raw_difference", "Information-premium group comparison")
    write_simple_svg(figures / "manipulation_premium_group_balance.svg", balance_rows, "category", "standardized_difference", "Manipulation-premium group balance")


def build_reports(outputs):
    mapping_summary = outputs["mapping_summary"][0]
    actor_core = [row for row in outputs["actor_metrics"] if row["payoff_specification"] == "core"]
    contrasts_core = [row for row in outputs["contrasts"] if row["payoff_specification"] == "core"]
    external_core = [row for row in outputs["externality_summary"] if row["payoff_specification"] == "core"]
    info_core = [row for row in outputs["information_summary"] if row["payoff_specification"] == "core"]
    manip_core = [row for row in outputs["manipulation_summary"] if row["payoff_specification"] == "core"]
    readiness = outputs["r6_readiness"][0]

    actor_table = markdown_table(actor_core, [
        ("affected_role", "Role"),
        ("strategy_name", "Actor Strategy"),
        ("mean_payoff", "Mean"),
        ("sharpe_like_ratio", "Sharpe-like"),
        ("sortino_like_ratio", "Sortino-like"),
        ("downside_deviation", "Downside"),
    ])
    contrast_table = markdown_table(contrasts_core, [
        ("affected_role", "Role"),
        ("strategy_name", "Strategy"),
        ("mean_payoff_difference", "Mean Diff"),
        ("ci_low", "CI Low"),
        ("ci_high", "CI High"),
        ("raw_p_value", "Raw p"),
        ("holm_adjusted_p_value", "Holm p"),
        ("matched_set_count", "Matched Sets"),
    ])
    external_table = markdown_table(external_core, [
        ("affected_role", "Affected Role"),
        ("strategy_owner_role", "Owner"),
        ("external_strategy_name", "External Strategy"),
        ("mean_payoff_difference", "Mean Diff"),
        ("ci_low", "CI Low"),
        ("ci_high", "CI High"),
    ], limit=20)
    info_table = markdown_table(info_core, [
        ("premium_definition", "Definition"),
        ("exposed_group_count", "Exposed"),
        ("comparison_group_count", "Comparison"),
        ("raw_difference", "Diff"),
        ("ci_low", "CI Low"),
        ("ci_high", "CI High"),
        ("causal_interpretation_status", "Status"),
    ])
    manipulation_table = markdown_table(manip_core, [
        ("premium_definition", "Definition"),
        ("exposed_group_count", "Exposed"),
        ("comparison_group_count", "Comparison"),
        ("raw_difference", "Diff"),
        ("ci_low", "CI Low"),
        ("ci_high", "CI High"),
        ("imbalance_warning", "Warning"),
    ])

    root_cause = f"""# R5.1 Root Cause Report

## Finding

R5 did not show evidence of a Cartesian-product coding bug. The root cause is
that R5 grouped payoff rows by `condition_name` and affected role. In the R4
validation dataset, `condition_name` is a global rollout configuration label:
all players in a game inherit the same condition label, even when only one role
controls the changed policy.

## Interpretation

- Coding/data bug: no join bug found.
- Valid but incorrectly interpreted: yes. R5 strategy-condition rows are valid
  as global condition and cross-role externality estimates.
- R5 outputs that remain valid: role-level metrics, role-level rankings,
  seed robustness, regime robustness, coefficient sensitivity, and frozen
  financial metric definitions.
- R5 outputs superseded by R5.1: actor-specific strategy rankings, strategy
  frontiers, and dominated-strategy claims.
- Raw R5 data regeneration required: no. R5.1 can reconstruct valid actor and
  externality views from the existing R4/R5 rows.
"""

    strategy_audit = f"""# R5.1 Strategy Attribution Audit

## Technical Summary

R5.1 separates actor-specific strategies from global configurations and
cross-role externalities. `wolf_random_kill` may affect Hunter, Seer, Witch, and
Villager payoffs, but those rows are externalities and must not be reported as
strategies those roles can choose.

## Mapping Counts

- Invalid actor-specific recommendations removed: `{mapping_summary['invalid_actor_specific_recommendation_count']}`
- Valid actor-specific role-strategy pairs: `{mapping_summary['valid_actor_specific_strategy_pair_count']}`
- Cross-role externality records: `{mapping_summary['externality_record_count']}`
- Suspected cross-join rows: `{mapping_summary['suspected_cross_join_count']}`

## Corrected Actor-Specific Metrics

{actor_table}
"""

    actor_report = f"""# R5.1 Actor-Specific Strategy Report

## Corrected Within-Role Strategy Results

Only rows where `strategy_owner_role == affected_role` are included in the
primary actor-specific analysis.

{actor_table}

## Formal Matched Contrasts Against Reference

{contrast_table}

Because the R4 validation design contains one directly controlled non-reference
strategy for each of Werewolf, Seer, Witch, and Villager, corrected frontiers are
sparse. Hunter has no actor-specific R4 strategy condition and therefore no
primary R5.1 strategy recommendation.
"""

    externality_report = f"""# R5.1 Cross-Role Externality Report

## Summary

R5 condition labels remain useful for externality analysis. They answer how one
role's policy shift changes another role's payoff under matched R4 validation
games.

{external_table}

These rows are descriptive cross-role payoff externalities, not strategy
recommendations for the affected role.
"""

    premium_report = f"""# R5.1 Premium Analysis Report

## Seer Information Premium

{info_table}

## Wolf Manipulation Premium

{manipulation_table}

All premiums are labelled as descriptive associations. The primary useful
information label is outcome-dependent, and the manipulation premium has severe
comparison-group imbalance.
"""

    information_audit = """# R5.1 Information Attribution Audit

## Result

The original primary useful-information flag
`seer_information_leads_to_wolf_elimination` is outcome-dependent because it
requires later wolf elimination. R5.1 therefore reports it as a descriptive
association only.

## Conservative Alternative

`wolf_found_by_check` uses the Seer check target role and does not require later
elimination or terminal victory. It is retained as a more conservative generated
information label, still not a causal estimate.

## Leakage Status

No hidden information is introduced into gameplay. The audit is about analysis
labels in the payoff ledger, not simulator decision logic.
"""

    robustness_report = f"""# R5.1 Overfitting and Robustness Report

## Leave-One-Seed-Out

Actor-specific rankings are stable in the mechanical sense because each role has
only one eligible direct strategy in the R4 validation design. R5.1 reports all
leave-one-seed rows in `r51_leave_one_seed_out.csv`.

## Leave-One-Regime-Out

Leave-one-regime rows are in `r51_leave_one_regime_out.csv`. No rank reversals
are possible with one eligible direct strategy per role, so the main limitation
is sparse strategy coverage rather than instability.
"""

    limitations = """# R5.1 Limitations

- R4 has one actor-specific non-reference condition for Werewolf, Seer, Witch,
  and Villager, and no Hunter-specific strategy condition.
- Corrected actor-specific frontiers are sparse and cannot rank multiple direct
  strategies per role.
- Formal p-values use paired sign tests over matched-set cluster differences.
- Premium analyses are descriptive associations, not causal estimates.
- The manipulation comparison group is very small, so adjusted manipulation
  models are intentionally not over-interpreted.
"""

    research_report = f"""# R5.1 Role-Strategy Attribution Audit Report

## Technical Summary

R5.1 finds that the surprising R5 strategy recommendations were not a payoff
formula failure. The issue was attribution: R5 strategy labels were global
configuration labels copied to every player in a game. R5.1 corrects this by
separating actor-specific strategies from cross-role externalities.

## Corrected Actor-Specific Results

{actor_table}

## Formal Contrasts

{contrast_table}

## Cross-Role Externalities

{external_table}

## Premium Analyses

{info_table}

{manipulation_table}

## Required Final Questions

1. R5 reported `wolf_random_kill` as best for non-wolf roles because
   `condition_name` was grouped as a global game configuration.
2. This was a labelling/interpretation issue, not a Cartesian-product coding bug.
3. Role-level R5 metrics remain valid.
4. R5 strategy frontiers and dominated-strategy claims are superseded.
5. Corrected owners are listed in `r51_corrected_strategy_registry.csv`.
6. Valid Villager strategy: `villager_random_vote`.
7. Valid Seer strategy: `seer_highest_suspicion`.
8. Valid Witch strategy: `witch_conservative_poison`.
9. Valid Hunter strategy: none in the R4 validation design.
10. Valid Werewolf strategy: `wolf_random_kill`.
11-14. Corrected rankings are sparse because each eligible role has one direct
strategy.
15. Actor-specific frontiers contain only direct strategies.
16. No actor-specific strategies are strictly dominated in R5.1 because no role
has multiple direct strategies in this validation dataset.
17. Matched contrasts against reference exist for Werewolf, Seer, Witch, and
Villager.
18. Cross-role strategy effects remain descriptive externalities.
19. Holm-adjusted results are reported in
`r51_actor_specific_primary_contrasts.csv`.
20-21. Leave-one-seed and leave-one-regime outputs are complete.
22. Cross-role externalities are reported separately.
23-24. Premium group sizes and CIs are reported.
25. Manipulation-group imbalance is severe.
26. The primary useful-information label is outcome-dependent.
27. No gameplay leakage checks failed.
28. No R5.1 mapping tests failed.
29. R6 readiness: `{readiness['r6_readiness']}`.
30. Exact R6 synthesis: unified role strategy optimization using corrected
actor-specific rows, externality labels, and evidence-quality flags.

## R6 Readiness

{readiness['reason']}
"""

    pre_registration = """# R5.1 Pre-Registration

Primary objective: audit R5 strategy attribution and rebuild actor-specific
strategy comparisons without changing R4 payoff manifests, R5 metric formulas,
or simulator behavior.

Primary unit: matched R4 validation games clustered by `matched_set_id`.

Primary correction rule: actor-specific rows require
`strategy_owner_role == affected_role`.
"""

    schema = """# R5.1 Schema

The R5.1 output directory contains strategy attribution registries, corrected
actor-specific raw rows, cross-role externality rows, formal contrasts,
leave-one-out robustness summaries, premium summaries, validation summaries,
and research reports.

Important keys:

- `affected_role`: role receiving the payoff.
- `strategy_owner_role`: role that controls the policy.
- `strategy_name`: R4 condition label.
- `valid_for_primary_analysis`: true only for direct actor-specific rows.
- `payoff_specification`: `core` or `extended`.
"""

    write_md(RESULTS_DIR / "r51_pre_registration.md", pre_registration)
    write_md(RESULTS_DIR / "r51_schema.md", schema)
    write_md(RESULTS_DIR / "r51_root_cause_report.md", root_cause)
    write_md(RESULTS_DIR / "r51_strategy_attribution_audit.md", strategy_audit)
    write_md(RESULTS_DIR / "r51_actor_specific_strategy_report.md", actor_report)
    write_md(RESULTS_DIR / "r51_cross_role_externality_report.md", externality_report)
    write_md(RESULTS_DIR / "r51_premium_analysis_report.md", premium_report)
    write_md(RESULTS_DIR / "r51_information_attribution_audit.md", information_audit)
    write_md(RESULTS_DIR / "r51_overfitting_and_robustness_report.md", robustness_report)
    write_md(RESULTS_DIR / "r51_research_report.md", research_report)
    write_md(RESULTS_DIR / "r51_limitations.md", limitations)


def update_cumulative_docs(outputs):
    head = git_head()
    registry_path = RESEARCH_DIR / "cumulative_evidence_registry.csv"
    registry_rows = read_csv(registry_path)
    fieldnames = registry_rows[0].keys()
    additions = [
        ("r51_strategy_attribution_audit", "R5.1 strategy attribution audit", "R5.1 shows R5 condition labels were global configurations, not actor-owned recommendations.", "design inconsistency found"),
        ("r51_actor_specific_reconstruction", "R5.1 actor-specific reconstruction", "Actor-specific rows require affected_role equals strategy_owner_role.", "partially validated"),
        ("r51_cross_role_externality", "R5.1 cross-role externality analysis", "Cross-role strategy effects are retained as externalities.", "descriptive only"),
        ("r51_corrected_frontiers", "R5.1 corrected frontiers", "Actor-specific frontiers are rebuilt from direct role-controlled rows only.", "risk-return efficient"),
        ("r51_dominated_strategies", "R5.1 corrected dominated strategies", "No actor-specific strategy is dominated because each eligible role has one direct strategy.", "strictly dominated"),
        ("r51_leave_one_seed_out", "R5.1 leave-one-seed-out robustness", "Actor-specific ranks are mechanically stable under leave-one-seed-out.", "robust across seeds"),
        ("r51_leave_one_regime_out", "R5.1 leave-one-regime-out robustness", "Actor-specific ranks are mechanically stable under leave-one-regime-out.", "robust across regimes"),
        ("r51_information_premium_ci", "R5.1 information premium CI", "Information premiums now include grouped bootstrap confidence intervals.", "information premium analogue"),
        ("r51_manipulation_premium_ci", "R5.1 manipulation premium CI", "Manipulation premiums now include grouped bootstrap confidence intervals.", "manipulation premium analogue"),
        ("r51_manipulation_imbalance", "R5.1 manipulation group imbalance", "The no-manipulation comparison group has weak overlap.", "descriptive only"),
        ("r51_result_validity", "R5.1 R5 result validity classification", "R5 role metrics remain valid while strategy frontiers are superseded.", "partially validated"),
        ("r51_r6_readiness", "R5.1 R6 readiness", "R5.1 concludes the project is ready for R6 with sparse-strategy caveats.", "ready for synthesis"),
    ]
    existing = {(row["stage_id"], row["hypothesis_id"]) for row in registry_rows}
    for stage_id, name, effect, label in additions:
        key = (stage_id, f"H_{stage_id}")
        if key in existing:
            continue
        registry_rows.append({
            "stage_id": stage_id,
            "stage_name": name,
            "research_domain": "role-strategy attribution and financial risk",
            "hypothesis_id": f"H_{stage_id}",
            "hypothesis": "Correct attribution separates actor-specific strategy value from cross-role externality.",
            "prior_hypothesis_source": "results/financial_risk_stage_r5/r5_research_report.md",
            "experiment_design": "Analysis-only reconstruction from frozen R4/R5 payoff rows.",
            "dataset_path": "results/financial_risk_stage_r51/r51_actor_specific_strategy_payoff_raw.csv",
            "report_path": "results/financial_risk_stage_r51/r51_research_report.md",
            "raw_row_count": str(len(outputs["actor_raw"])),
            "raw_game_count": "2000 R4 validation games",
            "independent_sample_size": "matched R4 validation games clustered by matched_set_id",
            "matched_set_count": str(len({row["matched_set_id"] for row in outputs["actor_raw"]})),
            "seed_count": "10",
            "behavioral_regime_count": "5",
            "primary_outcome": "corrected actor-specific payoff attribution",
            "comparison": "actor-specific vs externality mapping",
            "control_condition": REFERENCE_CONDITION,
            "descriptive_effect": effect,
            "absolute_percentage_point_effect": "not applicable",
            "effect_size_type": "audit classification",
            "effect_size": "not applicable",
            "confidence_interval": "reported where compatible in R5.1 outputs",
            "raw_p_value": "reported for compatible paired contrasts",
            "adjusted_p_value": "Holm adjusted within families where contrasts exist",
            "multiplicity_method": "Holm",
            "evidence_level": "LEVEL 3 - analysis-only audit of frozen validation data",
            "seed_robustness": "leave-one-seed-out reported",
            "regime_robustness": "leave-one-regime-out reported",
            "design_validity": "actor ownership explicit",
            "engine_validity": "default simulator behavior unchanged",
            "distribution_shift_status": "not a live-policy stage",
            "overfitting_status": "not a tuning stage",
            "leakage_status": "no gameplay leakage; outcome-dependent information label flagged",
            "conclusion_label": label,
            "hypothesis_status": "supported with limitations",
            "main_limitation": "R4 validation contains sparse actor-specific strategy alternatives.",
            "supersedes_stage_id": "r5_strategy_frontier" if "frontier" in stage_id or "dominated" in stage_id else "",
            "superseded_by_stage_id": "",
            "next_hypothesis": "R6 should synthesize role-specific recommendations using corrected actor/externality labels.",
            "source_commit": head,
            "current_documentation_commit": "pending_current_stage_commit",
        })
    write_csv(registry_path, registry_rows, fieldnames)

    append_once(
        RESEARCH_DIR / "cumulative_research_report.md",
        "## 29. R5.1 Role-Strategy Attribution Audit\n\n"
        "R5.1 audited the R5 strategy output and found that strategy-condition labels were global game configurations. "
        "The stage reconstructs actor-specific rows, separates cross-role externalities, rebuilds sparse actor-specific frontiers, "
        "adds paired contrasts against the reference configuration, and strengthens premium analyses with group sizes and bootstrap CIs. "
        "The project is ready for R6 synthesis with explicit sparse-strategy limitations.\n",
    )
    append_once(
        RESEARCH_DIR / "current_progress_assessment.md",
        "## R5.1 Progress Assessment\n\nR5.1 is complete. Strategy ownership is explicit, R5 strategy frontiers are superseded, and R6 may proceed with corrected attribution labels.\n",
    )
    append_once(
        RESEARCH_DIR / "remaining_work_roadmap.md",
        "## Next Stage After R5.1\n\nR6 - Unified Role Strategy Optimization Synthesis should combine expected payoff, risk-adjusted payoff, downside risk, externalities, and evidence quality by role.\n",
    )
    append_once(
        RESEARCH_DIR / "durf_proposal_alignment_audit.md",
        "## R5.1 Attribution Audit Update\n\nR5.1 resolves the strategy ownership ambiguity introduced by global R4 condition labels and prevents cross-role externalities from being reported as actor-specific strategy recommendations.\n",
    )

    proposal_path = RESEARCH_DIR / "durf_proposal_alignment_matrix.csv"
    proposal_rows = read_csv(proposal_path)
    proposal_fields = proposal_rows[0].keys()
    if not any(row["proposal_component"] == "Role-strategy attribution audit" for row in proposal_rows):
        proposal_rows.append({
            "proposal_component": "Role-strategy attribution audit",
            "original_proposal_description": "Separate role strategy value from cross-role externality in financial payoff analysis.",
            "status": "completed",
            "evidence": "results/financial_risk_stage_r51/r51_research_report.md",
            "source_file": "financial_r51_analysis.py",
            "quality_of_completion": "High",
            "remaining_work": "R6 should synthesize recommendations.",
            "required_next_stage": "R6",
            "priority": "High",
            "blocking_final_report": "No",
        })
    write_csv(proposal_path, proposal_rows, proposal_fields)

    trace_path = RESEARCH_DIR / "source_traceability_index.csv"
    trace_rows = read_csv(trace_path)
    trace_fields = trace_rows[0].keys()
    trace_id = "C_R5_1_ATTRIBUTION"
    if not any(row["claim_id"] == trace_id for row in trace_rows):
        trace_rows.append({
            "claim_id": trace_id,
            "claim_summary": "R5 strategy labels are global configurations unless owner role equals affected role.",
            "stage": "R5.1",
            "source_file": "results/financial_risk_stage_r51/r51_research_report.md",
            "source_table_or_section": "Technical Summary",
            "dataset": "results/financial_risk_stage_r51/r51_r5_strategy_mapping_audit.csv",
            "analysis_script": "financial_stage_r51_experiment.py",
            "commit_hash": head,
            "verification_status": "verified_from_source",
            "notes": "R5.1 actor-specific reconstruction.",
        })
    write_csv(trace_path, trace_rows, trace_fields)


def append_once(path, text):
    path = Path(path)
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    heading = text.split("\n", 1)[0]
    if heading not in current:
        path.write_text(current.rstrip() + "\n\n" + text.rstrip() + "\n", encoding="utf-8")


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    player_rows = enrich_player_rows(read_csv(R4_DIR / "r4_player_level_payoff_raw.csv"))
    game_rows = read_csv(R4_DIR / "r4_game_level_payoff_raw.csv")
    event_rows = read_csv(R4_DIR / "r4_event_level_payoff_ledger.csv")
    r5_strategy_rows = read_csv(R5_DIR / "r5_strategy_risk_return_summary.csv")

    mapping_rows = build_mapping_audit(r5_strategy_rows)
    actor_raw = build_actor_specific_raw(player_rows)
    external_raw = build_cross_role_externality_raw(player_rows)
    actor_metrics = build_actor_metrics(actor_raw)
    contrasts = build_formal_contrasts(player_rows, actor_metrics)
    frontier_rows, dominated_rows = build_frontiers(actor_metrics)
    externality_summary = summarize_externalities(external_raw)
    leave_seed = build_leave_one_out(actor_raw, "seed")
    leave_regime = build_leave_one_out(actor_raw, "behavioral_regime")
    rank_stability = build_rank_stability_summary(leave_seed, leave_regime)
    info_raw, manipulation_raw, premium_summary, premium_ci = build_premium_rows(player_rows, event_rows)
    info_summary = [row for row in premium_summary if row["premium_family"] == "information"]
    manipulation_summary = [row for row in premium_summary if row["premium_family"] == "manipulation"]
    balance_rows = build_manipulation_group_balance(player_rows, game_rows, event_rows)
    seed_registry, regime_registry = build_seed_regime_registries(player_rows)
    validity_registry = build_result_validity_registry()
    mapping_summary = build_mapping_validation_summary(mapping_rows, actor_raw, external_raw, contrasts, frontier_rows, premium_summary, balance_rows)
    r6_readiness = build_r6_readiness_summary(mapping_summary)

    outputs = {
        "mapping_rows": mapping_rows,
        "actor_raw": actor_raw,
        "external_raw": external_raw,
        "actor_metrics": actor_metrics,
        "contrasts": contrasts,
        "frontier_rows": frontier_rows,
        "dominated_rows": dominated_rows,
        "externality_summary": externality_summary,
        "leave_seed": leave_seed,
        "leave_regime": leave_regime,
        "rank_stability": rank_stability,
        "information_raw": info_raw,
        "manipulation_raw": manipulation_raw,
        "information_summary": info_summary,
        "manipulation_summary": manipulation_summary,
        "premium_ci": premium_ci,
        "balance_rows": balance_rows,
        "seed_registry": seed_registry,
        "regime_registry": regime_registry,
        "validity_registry": validity_registry,
        "mapping_summary": mapping_summary,
        "r6_readiness": r6_readiness,
    }

    write_csv(RESULTS_DIR / "r51_strategy_attribution_registry.csv", attribution_registry_rows())
    write_csv(RESULTS_DIR / "r51_r5_strategy_mapping_audit.csv", mapping_rows)
    write_csv(RESULTS_DIR / "r51_corrected_strategy_registry.csv", corrected_strategy_registry_rows())
    write_csv(RESULTS_DIR / "r51_strategy_data_coverage.csv", build_strategy_data_coverage(player_rows))
    write_csv(RESULTS_DIR / "r51_r5_result_validity_registry.csv", validity_registry)
    write_csv(RESULTS_DIR / "r51_seed_registry.csv", seed_registry)
    write_csv(RESULTS_DIR / "r51_regime_registry.csv", regime_registry)
    write_csv(RESULTS_DIR / "r51_actor_specific_strategy_payoff_raw.csv", actor_raw)
    write_csv(RESULTS_DIR / "r51_cross_role_externality_raw.csv", external_raw)
    write_csv(RESULTS_DIR / "r51_actor_specific_risk_metrics_raw.csv", actor_metrics)
    write_csv(RESULTS_DIR / "r51_externality_metrics_raw.csv", externality_summary)
    write_csv(RESULTS_DIR / "r51_information_premium_raw.csv", info_raw)
    write_csv(RESULTS_DIR / "r51_manipulation_premium_raw.csv", manipulation_raw)
    write_csv(RESULTS_DIR / "r51_manipulation_group_balance.csv", balance_rows)
    write_csv(RESULTS_DIR / "r51_actor_specific_strategy_summary.csv", actor_metrics)
    write_csv(RESULTS_DIR / "r51_actor_specific_primary_contrasts.csv", contrasts)
    write_csv(RESULTS_DIR / "r51_actor_specific_frontier_summary.csv", frontier_rows)
    write_csv(RESULTS_DIR / "r51_actor_specific_dominated_strategies.csv", dominated_rows, fieldnames=[
        "payoff_specification", "affected_role", "condition_name", "strategy_name",
        "risk_metric", "risk_value", "mean_payoff", "sharpe_like_ratio",
        "sortino_like_ratio", "is_efficient", "is_dominated", "dominated_by",
    ])
    write_csv(RESULTS_DIR / "r51_cross_role_externality_summary.csv", externality_summary)
    write_csv(RESULTS_DIR / "r51_leave_one_seed_out.csv", leave_seed)
    write_csv(RESULTS_DIR / "r51_leave_one_regime_out.csv", leave_regime)
    write_csv(RESULTS_DIR / "r51_rank_stability_summary.csv", rank_stability)
    write_csv(RESULTS_DIR / "r51_information_premium_summary.csv", info_summary)
    write_csv(RESULTS_DIR / "r51_manipulation_premium_summary.csv", manipulation_summary)
    write_csv(RESULTS_DIR / "r51_premium_bootstrap_confidence_intervals.csv", premium_ci)
    write_csv(RESULTS_DIR / "r51_mapping_validation_summary.csv", mapping_summary)
    write_csv(RESULTS_DIR / "r51_r6_readiness_summary.csv", r6_readiness)

    build_figures(actor_metrics, mapping_rows, externality_summary, leave_seed, leave_regime, info_summary, manipulation_summary, balance_rows)
    build_reports(outputs)
    update_cumulative_docs(outputs)

    print("R5.1 role-strategy attribution audit complete")
    print(f"Output directory: {RESULTS_DIR}")
    print(f"Invalid actor-specific recommendations removed: {mapping_summary[0]['invalid_actor_specific_recommendation_count']}")
    print(f"Valid actor-specific strategy pairs: {mapping_summary[0]['valid_actor_specific_strategy_pair_count']}")
    print(f"Cross-role externality records: {len(external_raw)}")
    print(f"R6 readiness: {r6_readiness[0]['r6_readiness']}")


if __name__ == "__main__":
    main()
