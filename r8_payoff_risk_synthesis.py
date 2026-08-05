"""R8 payoff and financial-risk synthesis tables."""

from __future__ import annotations

from collections import defaultdict

from r8_common import ci_text, fmt_float, get_row, read_csv, safe_float


ROLE_PAYOFF_COLUMNS = [
    "role",
    "calculation_specification",
    "observations",
    "mean_payoff",
    "median_payoff",
    "stdev",
    "downside_deviation",
    "negative_payoff_probability",
    "var90_loss",
    "var95_loss",
    "cvar90_loss",
    "cvar95_loss",
    "sharpe_like_ratio",
    "sortino_like_ratio",
    "opportunity_cost_adjusted_mean_payoff",
    "mean_payoff_bootstrap_ci",
    "stdev_bootstrap_ci",
    "downside_deviation_bootstrap_ci",
    "sharpe_like_bootstrap_ci",
    "sortino_like_bootstrap_ci",
    "rank_mean_payoff",
    "rank_lowest_volatility",
    "rank_lowest_downside",
    "rank_lowest_negative_probability",
    "rank_sharpe_like",
    "rank_sortino_like",
    "source_data",
]

FINANCIAL_ANALOGY_COLUMNS = [
    "analogy_component",
    "simulation_measure",
    "financial_risk_analogue",
    "supported_use",
    "unsupported_or_limited_use",
    "validation_status",
    "source_data",
]


def _core_role_rows() -> list[dict[str, str]]:
    rows = read_csv("results/financial_risk_stage_r5/r5_role_expected_payoff_summary.csv")
    return [row for row in rows if row.get("calculation_specification") == "core"]


def _rank(rows: list[dict[str, str]], key: str, reverse: bool = True) -> dict[str, int]:
    sorted_rows = sorted(rows, key=lambda row: safe_float(row.get(key, ""), float("-inf") if reverse else float("inf")), reverse=reverse)
    return {row["role"]: index for index, row in enumerate(sorted_rows, start=1)}


def _bootstrap_ci(role: str, metric: str) -> str:
    rows = read_csv("results/financial_risk_stage_r5/r5_bootstrap_confidence_intervals.csv")
    try:
        row = get_row(rows, role=role, metric=metric, calculation_specification="core")
    except KeyError:
        return "not_reported"
    return ci_text(row["ci_low"], row["ci_high"])


def build_final_role_payoff_table() -> list[dict[str, str]]:
    rows = _core_role_rows()
    ranks = {
        "mean": _rank(rows, "mean_payoff", True),
        "vol": _rank(rows, "stdev", False),
        "downside": _rank(rows, "downside_deviation", False),
        "negative": _rank(rows, "negative_payoff_probability", False),
        "sharpe": _rank(rows, "sharpe_like_ratio", True),
        "sortino": _rank(rows, "sortino_like_ratio", True),
    }
    output = []
    for row in rows:
        role = row["role"]
        output.append(
            {
                "role": role,
                "calculation_specification": "core",
                "observations": row["observations"],
                "mean_payoff": fmt_float(row["mean_payoff"], 4),
                "median_payoff": fmt_float(row["median_payoff"], 4),
                "stdev": fmt_float(row["stdev"], 4),
                "downside_deviation": fmt_float(row["downside_deviation"], 4),
                "negative_payoff_probability": fmt_float(row["negative_payoff_probability"], 4),
                "var90_loss": fmt_float(row["var90_loss"], 4),
                "var95_loss": fmt_float(row["var95_loss"], 4),
                "cvar90_loss": fmt_float(row["cvar90_loss"], 4),
                "cvar95_loss": fmt_float(row["cvar95_loss"], 4),
                "sharpe_like_ratio": fmt_float(row["sharpe_like_ratio"], 4),
                "sortino_like_ratio": fmt_float(row["sortino_like_ratio"], 4),
                "opportunity_cost_adjusted_mean_payoff": fmt_float(row["adjusted_mean_payoff"], 4),
                "mean_payoff_bootstrap_ci": _bootstrap_ci(role, "mean_payoff"),
                "stdev_bootstrap_ci": _bootstrap_ci(role, "stdev"),
                "downside_deviation_bootstrap_ci": _bootstrap_ci(role, "downside_deviation"),
                "sharpe_like_bootstrap_ci": _bootstrap_ci(role, "sharpe_like_ratio"),
                "sortino_like_bootstrap_ci": _bootstrap_ci(role, "sortino_like_ratio"),
                "rank_mean_payoff": str(ranks["mean"][role]),
                "rank_lowest_volatility": str(ranks["vol"][role]),
                "rank_lowest_downside": str(ranks["downside"][role]),
                "rank_lowest_negative_probability": str(ranks["negative"][role]),
                "rank_sharpe_like": str(ranks["sharpe"][role]),
                "rank_sortino_like": str(ranks["sortino"][role]),
                "source_data": "results/financial_risk_stage_r5/r5_role_expected_payoff_summary.csv",
            }
        )
    return sorted(output, key=lambda row: int(row["rank_mean_payoff"]))


def build_role_ranking_summary(role_payoff_rows: list[dict[str, str]]) -> dict[str, str]:
    def pick(rank_key: str) -> str:
        return min(role_payoff_rows, key=lambda row: int(row[rank_key]))["role"]

    highest_return = pick("rank_mean_payoff")
    highest_sharpe = pick("rank_sharpe_like")
    return {
        "highest_expected_payoff": highest_return,
        "lowest_volatility": pick("rank_lowest_volatility"),
        "lowest_downside_risk": pick("rank_lowest_downside"),
        "lowest_negative_payoff_probability": pick("rank_lowest_negative_probability"),
        "highest_sharpe_like_ratio": highest_sharpe,
        "highest_sortino_like_ratio": pick("rank_sortino_like"),
        "worst_cvar95_like_tail_risk": max(role_payoff_rows, key=lambda row: safe_float(row["cvar95_loss"], 0.0))["role"],
        "highest_return_is_highest_sharpe": "yes" if highest_return == highest_sharpe else "no",
    }


def build_financial_analogy_final_table() -> list[dict[str, str]]:
    return [
        {
            "analogy_component": "p_wolf",
            "simulation_measure": "dynamic belief that a target is a wolf",
            "financial_risk_analogue": "dynamic risk score",
            "supported_use": "Useful for explaining how agents update perceived adversarial risk.",
            "unsupported_or_limited_use": "Not calibrated to real-world default probabilities or market probabilities.",
            "validation_status": "supported_as_analogy_only",
            "source_data": "belief_update.py; results/financial_risk_stage_r5/r5_research_report.md",
        },
        {
            "analogy_component": "payoff",
            "simulation_measure": "frozen R4 role/action payoff ledger",
            "financial_risk_analogue": "return or utility payoff",
            "supported_use": "Valid within the game ledger and unchanged manifest.",
            "unsupported_or_limited_use": "Not money-valued and not externally priced.",
            "validation_status": "formula_validated",
            "source_data": "results/payoff_matrix_stage_r4/r4_payoff_manifest.json",
        },
        {
            "analogy_component": "downside deviation and VaR/CVaR-like metrics",
            "simulation_measure": "loss-tail summaries of game payoff",
            "financial_risk_analogue": "downside risk and tail risk",
            "supported_use": "Reveals role and strategy tail exposure beyond mean payoff.",
            "unsupported_or_limited_use": "No claim that game payoffs follow financial-return distributions.",
            "validation_status": "formula_validated",
            "source_data": "results/financial_risk_stage_r5/r5_metric_validation_summary.csv",
        },
        {
            "analogy_component": "deception",
            "simulation_measure": "wolf false accusation, deflection, and manipulation events",
            "financial_risk_analogue": "adversarial manipulation and misinformation risk",
            "supported_use": "Useful conceptual bridge to manipulation risk and reputation controls.",
            "unsupported_or_limited_use": "Does not model real strategic markets or legal enforcement.",
            "validation_status": "supported_as_analogy_only",
            "source_data": "results/financial_risk_stage_r51/r51_manipulation_premium_summary.csv",
        },
        {
            "analogy_component": "speaker memory",
            "simulation_measure": "speaker-specific trust scores and credibility costs",
            "financial_risk_analogue": "reputation-weighted information control",
            "supported_use": "Explains why credibility-weighted signals can dampen manipulation.",
            "unsupported_or_limited_use": "Trust scores are synthetic and not learned from human discourse.",
            "validation_status": "supported_with_synthetic_limitations",
            "source_data": "speaker_memory.py; trust_update.py; results/targeted_strategy_stage_r61/r61_villager_policy_summary.csv",
        },
    ]


def build_frontier_membership_summary() -> dict[str, str]:
    rows = read_csv("results/financial_risk_stage_r5/r5_strategy_frontier_summary.csv")
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row.get("calculation_specification") == "core" and row.get("is_efficient") == "True":
            grouped[row["risk_metric"]].append(f"{row['role']}:{row['condition_name']}")
    return {
        "standard_deviation_frontier": ";".join(grouped.get("standard_deviation", [])) or "not_reported",
        "downside_deviation_frontier": ";".join(grouped.get("downside_deviation", [])) or "not_reported",
        "cvar95_frontier": ";".join(grouped.get("cvar95_loss", [])) or "not_reported",
    }
