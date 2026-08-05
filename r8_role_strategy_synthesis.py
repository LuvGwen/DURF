"""R8 role-strategy synthesis tables."""

from __future__ import annotations

from collections import defaultdict

from r8_common import ci_text, fmt_float, get_row, read_csv, safe_float


ROLE_STRATEGY_COLUMNS = [
    "role",
    "reference_policy",
    "strongest_tested_policy",
    "highest_mean_payoff_policy",
    "highest_sharpe_like_policy",
    "highest_sortino_like_policy",
    "lowest_downside_risk_policy",
    "village_win_rate",
    "wolf_win_rate",
    "mean_actor_payoff",
    "actor_payoff_ci",
    "primary_contrast",
    "primary_mean_difference",
    "primary_ci",
    "raw_p_value",
    "holm_adjusted_p_value",
    "effective_matched_set_count",
    "efficient_frontier_stdev",
    "efficient_frontier_downside",
    "efficient_frontier_cvar95",
    "strictly_dominated_policies",
    "evidence_grade",
    "recommendation",
    "gap_closed",
    "source_data",
]

STRATEGY_RISK_RETURN_COLUMNS = [
    "role",
    "policy",
    "game_count",
    "matched_set_count",
    "seed_count",
    "behavioral_regime_count",
    "village_win_rate",
    "wolf_win_rate",
    "mean_actor_payoff",
    "actor_payoff_ci",
    "stdev_payoff",
    "downside_deviation",
    "negative_payoff_probability",
    "var_like_90",
    "var_like_95",
    "cvar_like_90",
    "cvar_like_95",
    "sharpe_like_ratio",
    "sortino_like_ratio",
    "frontier_stdev",
    "frontier_downside",
    "frontier_cvar95",
    "source_data",
]

SUMMARY_FILES = {
    "Hunter": "results/targeted_strategy_stage_r61/r61_hunter_policy_summary.csv",
    "Seer": "results/targeted_strategy_stage_r61/r61_seer_policy_summary.csv",
    "Witch": "results/targeted_strategy_stage_r61/r61_witch_policy_summary.csv",
    "Werewolf": "results/targeted_strategy_stage_r61/r61_wolf_policy_summary.csv",
    "Villager": "results/targeted_strategy_stage_r61/r61_villager_policy_summary.csv",
}

MODULE_NAME = {
    "Hunter": "hunter",
    "Seer": "seer",
    "Witch": "witch",
    "Werewolf": "wolf",
    "Villager": "villager",
}

REFERENCE_POLICY = {
    "Hunter": "reference",
    "Seer": "private_only",
    "Witch": "reference",
    "Werewolf": "reference",
    "Villager": "reference",
}


def _numeric(row: dict[str, str], key: str) -> float:
    value = safe_float(row.get(key, ""), None)
    if value is None:
        return float("-inf")
    return value


def _min_numeric(rows: list[dict[str, str]], key: str) -> dict[str, str]:
    return min(rows, key=lambda row: safe_float(row.get(key, ""), float("inf")))


def _max_numeric(rows: list[dict[str, str]], key: str) -> dict[str, str]:
    return max(rows, key=lambda row: _numeric(row, key))


def _frontier(rows: list[dict[str, str]], flag: str) -> str:
    policies = [row["policy"] for row in rows if row.get(flag) == "True"]
    return ";".join(policies) if policies else "none"


def _strictly_dominated(rows: list[dict[str, str]]) -> str:
    dominated = []
    for row in rows:
        if row.get("frontier_stdev") == "False" and row.get("frontier_downside") == "False" and row.get("frontier_cvar95") == "False":
            dominated.append(row["policy"])
    return ";".join(dominated) if dominated else "none"


def _primary_contrast(role: str, strongest_policy: str) -> dict[str, str] | None:
    if strongest_policy == REFERENCE_POLICY[role]:
        return None
    contrasts = read_csv("results/targeted_strategy_stage_r61/r61_global_primary_contrasts.csv")
    try:
        return get_row(contrasts, module=MODULE_NAME[role], candidate_policy=strongest_policy)
    except KeyError:
        return None


def build_final_role_strategy_table() -> list[dict[str, str]]:
    decision_rows = read_csv("results/role_strategy_synthesis_stage_r6/r6_role_strategy_decision_matrix.csv")
    rows = []
    for role, source in SUMMARY_FILES.items():
        summaries = read_csv(source)
        strongest = _max_numeric(summaries, "mean_actor_payoff")
        mean_policy = strongest
        sharpe_policy = _max_numeric(summaries, "sharpe_like_ratio")
        sortino_policy = _max_numeric(summaries, "sortino_like_ratio")
        downside_policy = _min_numeric(summaries, "downside_deviation")
        contrast = _primary_contrast(role, strongest["policy"])
        try:
            decision = get_row(decision_rows, role=role)
            grade = decision["evidence_grade"]
        except KeyError:
            grade = "not_reported"
        rows.append(
            {
                "role": role,
                "reference_policy": REFERENCE_POLICY[role],
                "strongest_tested_policy": strongest["policy"],
                "highest_mean_payoff_policy": mean_policy["policy"],
                "highest_sharpe_like_policy": sharpe_policy["policy"],
                "highest_sortino_like_policy": sortino_policy["policy"],
                "lowest_downside_risk_policy": downside_policy["policy"],
                "village_win_rate": fmt_float(strongest["village_win_rate"], 4),
                "wolf_win_rate": fmt_float(strongest["wolf_win_rate"], 4),
                "mean_actor_payoff": fmt_float(strongest["mean_actor_payoff"], 4),
                "actor_payoff_ci": ci_text(strongest["actor_payoff_ci_low"], strongest["actor_payoff_ci_high"]),
                "primary_contrast": contrast["comparison"] if contrast and "comparison" in contrast else (
                    f"{strongest['policy']} vs {REFERENCE_POLICY[role]}" if contrast else "reference_policy_no_contrast"
                ),
                "primary_mean_difference": fmt_float(contrast["mean_difference"], 4) if contrast else "not_applicable",
                "primary_ci": ci_text(contrast["ci_low"], contrast["ci_high"]) if contrast else "not_applicable",
                "raw_p_value": contrast["raw_p_value"] if contrast else "not_applicable",
                "holm_adjusted_p_value": contrast["holm_adjusted_p_value"] if contrast else "not_applicable",
                "effective_matched_set_count": contrast["matched_set_count"] if contrast else strongest["matched_set_count"],
                "efficient_frontier_stdev": _frontier(summaries, "frontier_stdev"),
                "efficient_frontier_downside": _frontier(summaries, "frontier_downside"),
                "efficient_frontier_cvar95": _frontier(summaries, "frontier_cvar95"),
                "strictly_dominated_policies": _strictly_dominated(summaries),
                "evidence_grade": grade,
                "recommendation": f"Use {strongest['policy']} as the strongest tested {role} policy only within the validated configuration space.",
                "gap_closed": "yes",
                "source_data": source,
            }
        )
    return rows


def build_strategy_risk_return_table() -> list[dict[str, str]]:
    rows = []
    for role, source in SUMMARY_FILES.items():
        for row in read_csv(source):
            rows.append(
                {
                    "role": role,
                    "policy": row["policy"],
                    "game_count": row["game_count"],
                    "matched_set_count": row["matched_set_count"],
                    "seed_count": row["seed_count"],
                    "behavioral_regime_count": row["behavioral_regime_count"],
                    "village_win_rate": fmt_float(row["village_win_rate"], 4),
                    "wolf_win_rate": fmt_float(row["wolf_win_rate"], 4),
                    "mean_actor_payoff": fmt_float(row["mean_actor_payoff"], 4),
                    "actor_payoff_ci": ci_text(row["actor_payoff_ci_low"], row["actor_payoff_ci_high"]),
                    "stdev_payoff": fmt_float(row["stdev_payoff"], 4),
                    "downside_deviation": fmt_float(row["downside_deviation"], 4),
                    "negative_payoff_probability": fmt_float(row["negative_payoff_probability"], 4),
                    "var_like_90": fmt_float(row["var_like_90"], 4),
                    "var_like_95": fmt_float(row["var_like_95"], 4),
                    "cvar_like_90": fmt_float(row["cvar_like_90"], 4),
                    "cvar_like_95": fmt_float(row["cvar_like_95"], 4),
                    "sharpe_like_ratio": fmt_float(row["sharpe_like_ratio"], 4),
                    "sortino_like_ratio": fmt_float(row["sortino_like_ratio"], 4),
                    "frontier_stdev": row["frontier_stdev"],
                    "frontier_downside": row["frontier_downside"],
                    "frontier_cvar95": row["frontier_cvar95"],
                    "source_data": source,
                }
            )
    return rows


def summarize_role_strategy_rankings(role_strategy_rows: list[dict[str, str]]) -> dict[str, str]:
    grouped = defaultdict(list)
    for row in role_strategy_rows:
        grouped[row["strongest_tested_policy"]].append(row["role"])
    return {
        "roles_with_reference_as_strongest": ";".join(sorted(grouped.get("reference", []))) or "none",
        "roles_with_nonreference_strongest": ";".join(
            sorted(row["role"] for row in role_strategy_rows if row["strongest_tested_policy"] != row["reference_policy"])
        )
        or "none",
        "role_strategy_source": "results/targeted_strategy_stage_r61/*.csv",
    }
