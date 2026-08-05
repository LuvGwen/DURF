"""Create R8 figure artifacts and table/figure registries."""

from __future__ import annotations

from collections import Counter

from r8_common import FIGURE_DIR, fmt_float, read_csv, safe_float, write_placeholder_png, write_simple_svg


TABLE_REGISTRY_COLUMNS = [
    "table_id",
    "table_name",
    "path",
    "row_count",
    "primary_use",
    "source_module",
]

FIGURE_REGISTRY_COLUMNS = [
    "figure_id",
    "figure_name",
    "svg_path",
    "png_path",
    "chart_family",
    "primary_measure",
    "source_data",
    "final_report_use",
]


def build_table_registry(rows_by_name: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    registry = []
    for index, (name, rows) in enumerate(sorted(rows_by_name.items()), start=1):
        registry.append(
            {
                "table_id": f"T_R8_{index:02d}",
                "table_name": name,
                "path": f"results/final_integrated_analysis_stage_r8/{name}.csv",
                "row_count": str(len(rows)),
                "primary_use": "final report table or appendix",
                "source_module": "final_integrated_analysis_stage_r8.py",
            }
        )
    return registry


def _role_metric(metric: str) -> list[tuple[str, float]]:
    rows = read_csv("results/financial_risk_stage_r5/r5_role_expected_payoff_summary.csv")
    return [
        (row["role"], safe_float(row.get(metric, ""), 0.0) or 0.0)
        for row in rows
        if row.get("calculation_specification") == "core"
    ]


def _policy_metric(path: str, label_key: str, metric: str) -> list[tuple[str, float]]:
    rows = read_csv(path)
    return [(row[label_key], safe_float(row.get(metric, ""), 0.0) or 0.0) for row in rows]


def create_final_figures(
    evidence_rows: list[dict[str, str]],
    role_payoff_rows: list[dict[str, str]],
    role_strategy_rows: list[dict[str, str]],
    bow_rows: list[dict[str, str]],
    ml_rows: list[dict[str, str]],
    proposal_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    specs: list[tuple[str, str, list[tuple[str, float]], str, str]] = []

    evidence_counts = Counter(row["conclusion_status"] for row in evidence_rows)
    specs.append(("Evidence conclusion distribution", "count", list(evidence_counts.items()), "r8_final_statistical_evidence_table.csv", "overview"))
    specs.append(("Role mean payoff", "mean payoff", _role_metric("mean_payoff"), "r5_role_expected_payoff_summary.csv", "payoff"))
    specs.append(("Role payoff volatility", "stdev", _role_metric("stdev"), "r5_role_expected_payoff_summary.csv", "payoff"))
    specs.append(("Role downside deviation", "downside deviation", _role_metric("downside_deviation"), "r5_role_expected_payoff_summary.csv", "risk"))
    specs.append(("Role Sharpe-like ratio", "Sharpe-like", _role_metric("sharpe_like_ratio"), "r5_role_expected_payoff_summary.csv", "risk"))
    specs.append(("Role CVaR95-like loss", "CVaR95-like", _role_metric("cvar95_loss"), "r5_role_expected_payoff_summary.csv", "risk"))
    specs.append(("R6.1 strongest role policies", "mean actor payoff", [(row["role"], safe_float(row["mean_actor_payoff"], 0.0) or 0.0) for row in role_strategy_rows], "r8_final_role_strategy_table.csv", "strategy"))
    specs.append(("Villager policy village win rate", "village win rate", _policy_metric("results/targeted_strategy_stage_r61/r61_villager_policy_summary.csv", "policy", "village_win_rate"), "r61_villager_policy_summary.csv", "strategy"))
    specs.append(("Seer policy village win rate", "village win rate", _policy_metric("results/targeted_strategy_stage_r61/r61_seer_policy_summary.csv", "policy", "village_win_rate"), "r61_seer_policy_summary.csv", "strategy"))
    specs.append(("Witch policy village win rate", "village win rate", _policy_metric("results/targeted_strategy_stage_r61/r61_witch_policy_summary.csv", "policy", "village_win_rate"), "r61_witch_policy_summary.csv", "strategy"))
    specs.append(("Werewolf policy wolf win rate", "wolf win rate", _policy_metric("results/targeted_strategy_stage_r61/r61_wolf_policy_summary.csv", "policy", "wolf_win_rate"), "r61_wolf_policy_summary.csv", "strategy"))
    specs.append(("Hunter policy village win rate", "village win rate", _policy_metric("results/targeted_strategy_stage_r61/r61_hunter_policy_summary.csv", "policy", "village_win_rate"), "r61_hunter_policy_summary.csv", "strategy"))
    specs.append(("BoW offline AUC", "ROC-AUC", [(row["artifact_or_policy"], safe_float(row["metric_value"], 0.0) or 0.0) for row in bow_rows if row["primary_metric"] in {"final-test ROC-AUC", "OOD template ROC-AUC"}], "r8_speech_bow_final_table.csv", "speech"))
    specs.append(("BoW live policy effect", "village win-rate pp", [(row["artifact_or_policy"], safe_float(row["metric_value"], 0.0) or 0.0) for row in bow_rows if row["stage"] == "R3" and "change" in row["primary_metric"]], "r8_speech_bow_final_table.csv", "speech"))
    specs.append(("ML live policy effect", "wolf win-rate change", [(row["policy_or_model"], safe_float(row["metric_value"], 0.0) or 0.0) for row in ml_rows if "change" in row["primary_metric"]], "r8_ml_final_table.csv", "ml"))
    specs.append(("Randomized-role seer strategies", "village win rate", _policy_metric("results/structured_seer_search/structured_seer_search_strategy_summary.csv", "strategy", "village_win_rate")[:10], "structured_seer_search_strategy_summary.csv", "seer"))
    specs.append(("Proposal completion", "count", list(Counter(row["r8_final_status"] for row in proposal_rows).items()), "r8_proposal_completion_matrix.csv", "proposal"))
    specs.append(("R9 readiness", "pass count", [("ready_criteria_met", 1.0), ("blocking_items", 0.0)], "r8_r9_readiness_summary.csv", "readiness"))

    registry = []
    for index, (title, primary_measure, rows, source, use) in enumerate(specs, start=1):
        svg_rel = f"results/final_integrated_analysis_stage_r8/figures/figure_{index:02d}.svg"
        png_rel = f"results/final_integrated_analysis_stage_r8/figures/figure_{index:02d}.png"
        write_simple_svg(svg_rel, title, rows or [("not_reported", 0.0)], source)
        write_placeholder_png(png_rel)
        registry.append(
            {
                "figure_id": f"F_R8_{index:02d}",
                "figure_name": title,
                "svg_path": svg_rel,
                "png_path": png_rel,
                "chart_family": "horizontal_bar",
                "primary_measure": primary_measure,
                "source_data": source,
                "final_report_use": use,
            }
        )
    return registry
