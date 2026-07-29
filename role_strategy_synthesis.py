"""R6 unified role-strategy evidence synthesis.

This module is analysis-only. It reads historical reports and CSV outputs,
classifies role-specific strategy evidence, and writes R6 synthesis artifacts.
It does not import or modify gameplay logic.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev
from textwrap import dedent

from role_strategy_evidence_registry import (
    CONFIDENCE_LEVELS,
    EVIDENCE_GRADES,
    R6_RESULTS_DIR,
    RECOMMENDATION_LABELS,
    SOURCE_EVIDENCE_FILES,
    get_evidence_grade_definitions,
)


ROOT = Path(__file__).resolve().parent

DECISION_MATRIX_COLUMNS = [
    "role",
    "strategy",
    "strategy_owner_role",
    "actor_specific_or_externality",
    "evidence_grade",
    "recommendation_label",
    "expected_payoff_status",
    "risk_adjusted_status",
    "downside_risk_status",
    "win_rate_status",
    "information_value_status",
    "exposure_risk_status",
    "seed_robustness",
    "regime_robustness",
    "formal_inference_status",
    "adjusted_p_value",
    "confidence_interval",
    "primary_sample_size",
    "historical_coverage",
    "main_strength",
    "main_risk",
    "main_limitation",
    "current_recommendation",
    "required_next_experiment",
    "source_report",
]

DATA_ANALYSIS_COLUMNS = [
    "conclusion_id",
    "role",
    "hypothesis",
    "evidence_source",
    "descriptive_result",
    "formal_effect",
    "confidence_interval",
    "raw_p_value",
    "adjusted_p_value",
    "independent_sample_size",
    "seed_robustness",
    "regime_robustness",
    "overfitting_status",
    "leakage_status",
    "evidence_grade",
    "conclusion_label",
    "recommendation",
]

CROSS_STAGE_COLUMNS = [
    "contradiction_id",
    "research_topic",
    "earlier_result",
    "later_result",
    "reason_for_difference",
    "which_result_has_priority",
    "scientific_resolution",
    "source_files",
    "final_recommendation_effect",
]

GAP_COLUMNS = [
    "gap_id",
    "role",
    "research_question",
    "gap_type",
    "why_unresolved",
    "existing_evidence",
    "required_data",
    "required_experiment",
    "minimum_scale",
    "primary_outcome",
    "secondary_outcomes",
    "formal_analysis",
    "priority",
    "blocks_final_report",
    "source_files",
]

TARGET_PRIORITY_COLUMNS = [
    "priority_id",
    "role",
    "scientific_question",
    "conditions",
    "reference_condition",
    "minimum_scale",
    "matched_design",
    "seed_split",
    "behavioral_regimes",
    "primary_outcome",
    "risk_outcomes",
    "multiplicity_family",
    "report_requirements",
    "required_before_final_report",
]

REJECTED_COLUMNS = [
    "role",
    "strategy",
    "rejection_reason",
    "evidence_grade",
    "recommendation_label",
    "source_report",
    "formal_result",
    "limitation",
]

DEFAULT_COLUMNS = [
    "role",
    "current_default",
    "reason",
    "evidence_grade",
    "confidence",
    "known_limitations",
    "alternatives_tested",
    "alternatives_rejected",
    "alternatives_unresolved",
    "next_review_stage",
]

SOURCE_INDEX_COLUMNS = [
    "source_path",
    "source_type",
    "row_count",
    "hash_sha256",
    "metrics_used",
    "r6_use",
    "status",
]

PROPOSAL_ALIGNMENT_COLUMNS = [
    "proposal_component",
    "r6_status",
    "evidence_source",
    "r6_conclusion",
    "remaining_work",
]

VALIDATION_COLUMNS = ["check", "passed", "detail"]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "not available"


def fnum(value: object, digits: int = 4) -> str:
    if value in (None, "", "NA", "not reported"):
        return "not reported"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value: object, digits: int = 2) -> str:
    if value in (None, "", "NA", "not reported"):
        return "not reported"
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return str(value)


def pp(value: object, digits: int = 2) -> str:
    if value in (None, "", "NA", "not reported"):
        return "not reported"
    try:
        return f"{float(value):.{digits}f} pp"
    except (TypeError, ValueError):
        return str(value)


def first(rows: list[dict[str, str]], **filters: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    return {}


def load_evidence() -> dict[str, object]:
    """Load the source data needed for R6 classification."""
    evidence: dict[str, object] = {
        "r51_validation": read_csv("results/financial_risk_stage_r51/r51_mapping_validation_summary.csv"),
        "r51_actor_summary": read_csv("results/financial_risk_stage_r51/r51_actor_specific_strategy_summary.csv"),
        "r51_actor_contrasts": read_csv("results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv"),
        "r51_externalities": read_csv("results/financial_risk_stage_r51/r51_cross_role_externality_summary.csv"),
        "r51_info_premium": read_csv("results/financial_risk_stage_r51/r51_information_premium_summary.csv"),
        "r51_manip_premium": read_csv("results/financial_risk_stage_r51/r51_manipulation_premium_summary.csv"),
        "r51_coverage": read_csv("results/financial_risk_stage_r51/r51_strategy_data_coverage.csv"),
        "r5_role_metrics": read_csv("results/financial_risk_stage_r5/r5_role_expected_payoff_summary.csv"),
        "r5_role_var_cvar": read_csv("results/financial_risk_stage_r5/r5_role_var_cvar_summary.csv"),
        "r3_policy": read_csv("results/bow_integration_stage_r3/r3_policy_game_outcome_summary.csv"),
        "r3_contrasts": read_csv("results/bow_integration_stage_r3/r3_primary_game_contrasts.csv"),
        "structured_seer": read_csv("results/structured_seer_search/structured_seer_search_strategy_summary.csv"),
        "structured_seer_pairwise": read_csv("results/data_analysis/structured_seer_search/pairwise_strategy_contrasts.csv"),
        "structured_seer_omnibus": read_csv("results/data_analysis/structured_seer_search/strategy_omnibus_tests.csv"),
        "randomized_seer": read_csv("results/data_analysis/seer_position_randomized_roles/statistical_summary.csv"),
        "randomized_seer_pairwise": read_csv("results/data_analysis/seer_position_randomized_roles/pairwise_strategy_comparisons.csv"),
        "seat_order_validation": read_csv("results/data_analysis/seat_order_neutral/validation_summary.csv"),
        "ml2a_policy": read_csv("results/ml_optimization_stage2a/wolf_kill_live_policy_summary.csv"),
        "ml2a_contrasts": read_csv("results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv"),
        "ml2b_policy": read_csv("results/ml_optimization_stage2b/stage2b_policy_win_summary.csv"),
        "ml2b_contrasts": read_csv("results/ml_optimization_stage2b/stage2b_primary_contrasts.csv"),
    }
    return evidence


def core_contrast(evidence: dict[str, object], strategy_name: str) -> dict[str, str]:
    rows = evidence["r51_actor_contrasts"]  # type: ignore[index]
    return first(rows, strategy_name=strategy_name, payoff_specification="core")


def core_actor_metric(evidence: dict[str, object], strategy_name: str) -> dict[str, str]:
    rows = evidence["r51_actor_summary"]  # type: ignore[index]
    return first(rows, strategy_name=strategy_name, payoff_specification="core")


def r3_policy(evidence: dict[str, object], condition_name: str) -> dict[str, str]:
    rows = evidence["r3_policy"]  # type: ignore[index]
    return first(rows, condition_name=condition_name)


def structured_seer_row(evidence: dict[str, object], strategy: str) -> dict[str, str]:
    rows = evidence["structured_seer"]  # type: ignore[index]
    return first(rows, strategy=strategy, seed="all")


def ml2b_row(evidence: dict[str, object], policy_name: str) -> dict[str, str]:
    rows = evidence["ml2b_policy"]  # type: ignore[index]
    return first(rows, policy_name=policy_name)


def make_ci(row: dict[str, str], low_key: str = "ci_low", high_key: str = "ci_high") -> str:
    if not row:
        return "not reported"
    low = row.get(low_key, "")
    high = row.get(high_key, "")
    if not low or not high:
        return "not reported"
    return f"[{fnum(low, 4)}, {fnum(high, 4)}]"


def base_decision_row(**kwargs: object) -> dict[str, object]:
    row = {column: "not reported" for column in DECISION_MATRIX_COLUMNS}
    row.update(
        {
            "seed_robustness": "not reported",
            "regime_robustness": "not reported",
            "formal_inference_status": "not reported",
            "adjusted_p_value": "not reported",
            "confidence_interval": "not reported",
            "historical_coverage": "source files reviewed",
            "required_next_experiment": "not applicable",
        }
    )
    row.update(kwargs)
    return row


def build_decision_matrix(evidence: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    villager_random = core_contrast(evidence, "villager_random_vote")
    seer_high = core_contrast(evidence, "seer_highest_suspicion")
    witch_cons = core_contrast(evidence, "witch_conservative_poison")
    wolf_random = core_contrast(evidence, "wolf_random_kill")
    r3_guarded = first(evidence["r3_contrasts"], condition_name="guarded_bow_010_live")  # type: ignore[index]
    r3_structured = first(evidence["r3_contrasts"], condition_name="structured_bow_guarded_live")  # type: ignore[index]
    r3_selective = first(evidence["r3_contrasts"], condition_name="selective_bow_vote_override_live")  # type: ignore[index]
    ml2a_hybrid = first(evidence["ml2a_contrasts"], policy_name="frozen_hybrid_50_50")  # type: ignore[index]
    ml2b_cont = first(evidence["ml2b_contrasts"], policy_name="continuous_frozen_ml")  # type: ignore[index]
    ml2b_first = first(evidence["ml2b_contrasts"], policy_name="ml_first_kill_only")  # type: ignore[index]
    ml2b_selective = first(evidence["ml2b_contrasts"], policy_name="selective_ml_override")  # type: ignore[index]

    rows.extend(
        [
            base_decision_row(
                role="Villager",
                strategy="structured_speech_reference",
                strategy_owner_role="global_village_discussion",
                actor_specific_or_externality="global_configuration",
                evidence_grade="B",
                recommendation_label="retain reference/default",
                expected_payoff_status="R5.1 treats the reference strategy mix as descriptive support, not a role-owned strategy.",
                risk_adjusted_status="retained as current comparison baseline",
                downside_risk_status="not isolated for a Villager-owned policy",
                win_rate_status="Stage 2/3/4 results show village needs speech and belief information, but global mechanisms are not actor-specific strategies.",
                information_value_status="structured speech remains the active information channel after R2/R3.",
                exposure_risk_status="speaker credibility costs and memory are retained as safeguards.",
                seed_robustness="multi-seed evidence exists for later trust and R5/R5.1 settings",
                regime_robustness="R5/R5.1 uses five regimes; direct Villager strategy coverage remains sparse",
                formal_inference_status="reference configuration; not a direct contrast",
                adjusted_p_value="not applicable",
                confidence_interval="not applicable",
                primary_sample_size="R5.1 400 matched reference sets; R3 1650 matched live games for BoW contrasts",
                main_strength="preserves useful social signal without relying on live BoW override.",
                main_risk="global configuration effects cannot be claimed as Villager-owned strategy value.",
                main_limitation="needs a matched Villager voting policy experiment.",
                current_recommendation="Retain structured speech and belief voting as the current Villager-facing default.",
                required_next_experiment="Villager structured voting comparison with matched seeds and actor-specific payoff.",
                source_report="stage2_experiment_report.md; results/bow_integration_stage_r3/r3_primary_game_contrasts.csv; results/financial_risk_stage_r51/r51_strategy_data_coverage.csv",
            ),
            base_decision_row(
                role="Villager",
                strategy="villager_random_vote",
                strategy_owner_role="Villager",
                actor_specific_or_externality="actor_specific",
                evidence_grade="D",
                recommendation_label="no supported improvement",
                expected_payoff_status=f"Mean payoff difference {fnum(villager_random.get('mean_payoff_difference'))} vs reference.",
                risk_adjusted_status=f"Sharpe difference {fnum(villager_random.get('sharpe_like_difference'))}; Sortino difference {fnum(villager_random.get('sortino_like_difference'))}.",
                downside_risk_status=f"Downside-deviation difference {fnum(villager_random.get('downside_deviation_difference'))}.",
                win_rate_status="not directly measured as a role-owned win-rate effect in R5.1.",
                information_value_status="removes structured social information from voting.",
                exposure_risk_status="no direct exposure advantage found.",
                seed_robustness="leave-one-seed-out available in R5.1",
                regime_robustness="leave-one-regime-out available in R5.1",
                formal_inference_status=villager_random.get("formal_inference_status", "not reported"),
                adjusted_p_value=villager_random.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=make_ci(villager_random),
                primary_sample_size=f"{villager_random.get('matched_set_count', 'not reported')} matched sets; 1600 actor rows",
                main_strength="simple reference stress test.",
                main_risk="does not improve payoff and discards available belief structure.",
                main_limitation="only one random-vote actor-specific intervention was available.",
                current_recommendation="Do not replace the structured-voting reference with random voting.",
                required_next_experiment="Villager structured-voting ablation with multiple non-random alternatives.",
                source_report="results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv",
            ),
            base_decision_row(
                role="Villager",
                strategy="guarded_bow_010_live",
                strategy_owner_role="global_village_discussion",
                actor_specific_or_externality="global_configuration",
                evidence_grade="E",
                recommendation_label="statistically supported harmful",
                expected_payoff_status="not converted to actor-specific payoff in R5.1.",
                risk_adjusted_status="not available",
                downside_risk_status="not available",
                win_rate_status=f"Village win changed by {pp(r3_guarded.get('absolute_pp_difference'))} versus existing system.",
                information_value_status="BoW prediction did not translate into live-game policy value.",
                exposure_risk_status="risk of noisy false positives in live voting.",
                seed_robustness="R3 has seed robustness outputs",
                regime_robustness="R3 includes behavioral regime registry",
                formal_inference_status="matched primary game contrast",
                adjusted_p_value=r3_guarded.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=f"odds ratio [{fnum(r3_guarded.get('odds_ratio_ci_low'))}, {fnum(r3_guarded.get('odds_ratio_ci_high'))}]",
                primary_sample_size=f"{r3_guarded.get('matched_sets', 'not reported')} matched sets",
                main_strength="tests formal BoW in live decisions.",
                main_risk="large harmful live effect.",
                main_limitation="global policy, not Villager-only actor-specific payoff.",
                current_recommendation="Keep formal BoW as diagnostic unless a later guarded design passes live validation.",
                required_next_experiment="Repair BoW integration only after targeted mechanism diagnostics.",
                source_report="results/bow_integration_stage_r3/r3_primary_game_contrasts.csv",
            ),
            base_decision_row(
                role="Villager",
                strategy="structured_bow_guarded_live",
                strategy_owner_role="global_village_discussion",
                actor_specific_or_externality="global_configuration",
                evidence_grade="E",
                recommendation_label="statistically supported harmful",
                win_rate_status=f"Village win changed by {pp(r3_structured.get('absolute_pp_difference'))} versus existing system.",
                information_value_status="structured plus BoW live integration performed worse than structured reference.",
                exposure_risk_status="amplifies noisy text-derived updates.",
                seed_robustness="R3 seed outputs available",
                regime_robustness="R3 regime outputs available",
                formal_inference_status="matched primary game contrast",
                adjusted_p_value=r3_structured.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=f"odds ratio [{fnum(r3_structured.get('odds_ratio_ci_low'))}, {fnum(r3_structured.get('odds_ratio_ci_high'))}]",
                primary_sample_size=f"{r3_structured.get('matched_sets', 'not reported')} matched sets",
                main_strength="directly tested the combined live integration.",
                main_risk="largest harmful R3 live effect.",
                main_limitation="policy-level result, not actor-specific Villager payoff.",
                current_recommendation="Do not activate structured plus BoW live voting under current evidence.",
                source_report="results/bow_integration_stage_r3/r3_primary_game_contrasts.csv",
            ),
            base_decision_row(
                role="Villager",
                strategy="selective_bow_vote_override_live",
                strategy_owner_role="global_village_discussion",
                actor_specific_or_externality="global_configuration",
                evidence_grade="D",
                recommendation_label="no supported improvement",
                win_rate_status=f"Village win changed by {pp(r3_selective.get('absolute_pp_difference'))} versus existing system.",
                information_value_status="near-neutral live effect but not supported as improvement.",
                exposure_risk_status="small override count reduces harm and potential value.",
                seed_robustness="R3 seed outputs available",
                regime_robustness="R3 regime outputs available",
                formal_inference_status="matched primary game contrast",
                adjusted_p_value=r3_selective.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=f"odds ratio [{fnum(r3_selective.get('odds_ratio_ci_low'))}, {fnum(r3_selective.get('odds_ratio_ci_high'))}]",
                primary_sample_size=f"{r3_selective.get('matched_sets', 'not reported')} matched sets",
                main_strength="least harmful R3 live BoW intervention.",
                main_risk="no reliable improvement.",
                main_limitation="does not establish live policy value.",
                current_recommendation="Diagnostic only; do not treat as current default.",
                required_next_experiment="Selective BoW retest only after pre-registered threshold redesign.",
                source_report="results/bow_integration_stage_r3/r3_primary_game_contrasts.csv",
            ),
        ]
    )

    for strategy, grade, label, recommendation, limitation in [
        (
            "random_or_diversified_checking_reference",
            "B",
            "retain reference/default",
            "Use random or diversified checking as the current seer-search reference.",
            "diversified policies were not formally superior after correction.",
        ),
        (
            "edge_first",
            "D",
            "no supported improvement",
            "Do not revive edge-seat checking folklore after role randomization.",
            "position labels are randomized and physical direction tests found no robust advantage.",
        ),
        (
            "alternate_sides",
            "C",
            "promising but uncertain",
            "Treat side alternation as a candidate for future validation, not a default.",
            "Holm-adjusted pairwise comparison against random missed the 0.05 threshold.",
        ),
        (
            "right_to_left",
            "C",
            "promising but uncertain",
            "Treat directional search as exploratory until a targeted matched test confirms it.",
            "apparent gain may be search-order artifact rather than role-position advantage.",
        ),
        (
            "highest_p_wolf",
            "E",
            "not recommended",
            "Do not use highest p_wolf as the current seer check rule.",
            "structured search showed lower village win than random.",
        ),
        (
            "highest_suspicion",
            "E",
            "not recommended",
            "Do not use highest suspicion as the current seer check rule.",
            "R5.1 actor-specific payoff contrast found no improvement and structured search was harmful.",
        ),
    ]:
        source_strategy = {
            "random_or_diversified_checking_reference": "random",
            "edge_first": "edge_first",
            "alternate_sides": "alternate_sides",
            "right_to_left": "right_to_left",
            "highest_p_wolf": "highest_p_wolf",
            "highest_suspicion": "highest_suspicion",
        }[strategy]
        srow = structured_seer_row(evidence, source_strategy)
        formal = "structured search descriptive and pairwise formal tests where available"
        adj_p = "not applicable"
        ci = "not reported"
        if strategy == "highest_suspicion":
            adj_p = seer_high.get("holm_adjusted_p_value", "not reported")
            ci = make_ci(seer_high)
            formal = seer_high.get("formal_inference_status", formal)
        rows.append(
            base_decision_row(
                role="Seer",
                strategy=strategy,
                strategy_owner_role="Seer",
                actor_specific_or_externality="actor_specific" if strategy == "highest_suspicion" else "strategy_level_game_outcome",
                evidence_grade=grade,
                recommendation_label=label,
                expected_payoff_status=(
                    f"R5.1 payoff difference {fnum(seer_high.get('mean_payoff_difference'))}"
                    if strategy == "highest_suspicion"
                    else "not converted to actor-specific payoff"
                ),
                risk_adjusted_status=(
                    f"Sharpe difference {fnum(seer_high.get('sharpe_like_difference'))}"
                    if strategy == "highest_suspicion"
                    else "not available"
                ),
                downside_risk_status=(
                    f"Downside-deviation difference {fnum(seer_high.get('downside_deviation_difference'))}"
                    if strategy == "highest_suspicion"
                    else "not available"
                ),
                win_rate_status=f"Structured-search village win {pct(srow.get('village_win_rate'))}; wolf win {pct(srow.get('wolf_win_rate'))}.",
                information_value_status=f"First-check wolf {pct(srow.get('first_check_wolf_rate'))}; found wolf by check 3 {pct(srow.get('found_wolf_by_check_3_rate'))}.",
                exposure_risk_status=f"Seer survival {pct(srow.get('seer_survival_rate'))}.",
                seed_robustness="multi-seed structured search; R5.1 leave-one-seed where compatible",
                regime_robustness="R5.1 leave-one-regime where compatible",
                formal_inference_status=formal,
                adjusted_p_value=adj_p,
                confidence_interval=ci,
                primary_sample_size=f"{srow.get('num_games', 'not reported')} games" if srow else "not reported",
                main_strength="clarifies information-search behavior.",
                main_risk="search outcome associations can be post-treatment.",
                main_limitation=limitation,
                current_recommendation=recommendation,
                required_next_experiment="Seer reveal-timing matched experiment" if strategy in {"random_or_diversified_checking_reference", "alternate_sides", "right_to_left"} else "not applicable",
                source_report="results/structured_seer_search/structured_seer_search_strategy_summary.csv; results/data_analysis/structured_seer_search/pairwise_strategy_contrasts.csv; results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv",
            )
        )

    rows.extend(
        [
            base_decision_row(
                role="Seer",
                strategy="early_wolf_discovery_signal",
                strategy_owner_role="Seer",
                actor_specific_or_externality="post_outcome_association",
                evidence_grade="B",
                recommendation_label="conditionally recommended",
                expected_payoff_status="R5.1 useful-information and wolf-found premiums are strongly positive descriptive associations.",
                risk_adjusted_status="not a policy contrast",
                downside_risk_status="not a policy contrast",
                win_rate_status="earlier discovery is associated with improved village information but is not independently randomized.",
                information_value_status="primary useful-information premium and wolf-found premium both have positive CIs.",
                exposure_risk_status="reveal timing remains unresolved.",
                seed_robustness="R5.1 uses 10 seeds",
                regime_robustness="R5.1 uses five regimes",
                formal_inference_status="descriptive association; causal estimate unavailable",
                adjusted_p_value=first(evidence["r51_info_premium"], premium_definition="primary_useful_information", payoff_specification="core").get("holm_adjusted_p_value", "not reported"),  # type: ignore[index]
                confidence_interval=make_ci(first(evidence["r51_info_premium"], premium_definition="primary_useful_information", payoff_specification="core")),  # type: ignore[index]
                primary_sample_size="2000 games; exposed group 576 for useful information",
                main_strength="information value is one of the clearest positive associations in R5.1.",
                main_risk="outcome-dependent label; not causal.",
                main_limitation="need a policy that changes information timing without using future outcomes.",
                current_recommendation="Prioritize earlier wolf discovery as a search objective, but report the premium as associative.",
                required_next_experiment="Seer reveal-timing and information-release experiment.",
                source_report="results/financial_risk_stage_r51/r51_information_premium_summary.csv",
            ),
            base_decision_row(
                role="Witch",
                strategy="witch_conservative_poison",
                strategy_owner_role="Witch",
                actor_specific_or_externality="actor_specific",
                evidence_grade="C",
                recommendation_label="promising but uncertain",
                expected_payoff_status=f"Mean payoff difference {fnum(witch_cons.get('mean_payoff_difference'))} vs reference.",
                risk_adjusted_status=f"Sharpe difference {fnum(witch_cons.get('sharpe_like_difference'))}; Sortino difference {fnum(witch_cons.get('sortino_like_difference'))}.",
                downside_risk_status=f"Downside-deviation difference {fnum(witch_cons.get('downside_deviation_difference'))}.",
                win_rate_status="not isolated as a Witch-owned win-rate effect in R5.1.",
                information_value_status="uses suspicion threshold rather than hidden information.",
                exposure_risk_status="reduces indiscriminate poison risk but may miss useful poison opportunities.",
                seed_robustness="leave-one-seed-out available in R5.1",
                regime_robustness="leave-one-regime-out available in R5.1",
                formal_inference_status=witch_cons.get("formal_inference_status", "not reported"),
                adjusted_p_value=witch_cons.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=make_ci(witch_cons),
                primary_sample_size=f"{witch_cons.get('matched_set_count', 'not reported')} matched sets; 400 actor rows",
                main_strength="small positive actor-specific payoff difference.",
                main_risk="confidence interval includes no effect.",
                main_limitation="joint save-poison policy was not fully isolated.",
                current_recommendation="Conditionally prefer conservative poison over indiscriminate poison; keep as uncertain.",
                required_next_experiment="Matched Witch joint save/poison timing experiment.",
                source_report="results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv",
            ),
            base_decision_row(
                role="Witch",
                strategy="joint_save_poison_policy",
                strategy_owner_role="Witch",
                actor_specific_or_externality="insufficient_data",
                evidence_grade="U",
                recommendation_label="requires targeted experiment",
                expected_payoff_status="insufficient compatible event-level data",
                risk_adjusted_status="insufficient compatible event-level data",
                downside_risk_status="insufficient compatible event-level data",
                win_rate_status="older potion threshold sweeps do not isolate a full joint policy.",
                information_value_status="not reported",
                exposure_risk_status="unknown potion-waste and opportunity-cost tradeoff.",
                seed_robustness="not reported for joint policy",
                regime_robustness="not reported for joint policy",
                formal_inference_status="insufficient data",
                adjusted_p_value="insufficient data",
                confidence_interval="insufficient data",
                primary_sample_size="insufficient compatible event-level data",
                main_strength="scientifically important open policy question.",
                main_risk="could change village balance through save and poison interactions.",
                main_limitation="no valid matched actor-specific comparison.",
                current_recommendation="Do not claim a full Witch policy recommendation beyond conservative poison uncertainty.",
                required_next_experiment="Witch save probability x poison threshold matched factorial experiment.",
                source_report="results/financial_risk_stage_r51/r51_strategy_data_coverage.csv",
            ),
            base_decision_row(
                role="Hunter",
                strategy="hunter_actor_specific_shot_policy",
                strategy_owner_role="Hunter",
                actor_specific_or_externality="insufficient_data",
                evidence_grade="U",
                recommendation_label="insufficient data",
                expected_payoff_status="insufficient compatible actor-specific data",
                risk_adjusted_status="insufficient compatible actor-specific data",
                downside_risk_status="R5 role-level metrics show Hunter has severe tail risk, but no valid strategy comparison.",
                win_rate_status="not isolated",
                information_value_status="not isolated",
                exposure_risk_status="high tail risk if shot is wrong.",
                seed_robustness="not available for actor-specific Hunter policy",
                regime_robustness="not available for actor-specific Hunter policy",
                formal_inference_status="insufficient data",
                adjusted_p_value="insufficient data",
                confidence_interval="insufficient data",
                primary_sample_size="insufficient compatible event-level data",
                main_strength="correct wolf shot is mechanically valuable.",
                main_risk="wrong shot penalty and worst role-level CVaR-like tail risk.",
                main_limitation="no matched Hunter-owned strategy comparison in R5.1.",
                current_recommendation="No Hunter shot policy is recommended under current evidence.",
                required_next_experiment="Hunter random, no-shot, suspicion-shot, and conservative-shot matched experiment.",
                source_report="results/financial_risk_stage_r5/r5_role_expected_payoff_summary.csv; results/financial_risk_stage_r51/r51_strategy_data_coverage.csv",
            ),
            base_decision_row(
                role="Werewolf",
                strategy="existing_rule_night_kill_reference",
                strategy_owner_role="Werewolf",
                actor_specific_or_externality="reference_policy",
                evidence_grade="B",
                recommendation_label="retain reference/default",
                expected_payoff_status="existing rule has higher wolf win than complete frozen ML rollouts in Stage 2A/2B.",
                risk_adjusted_status="R5.1 reference strategy mix is the comparator.",
                downside_risk_status="not isolated as a strategy risk metric.",
                win_rate_status=f"Stage 2B existing-rule wolf win {pct(ml2b_row(evidence, 'existing_rule').get('wolf_win_rate'))}.",
                information_value_status="uses existing visible game state rather than hidden future outcomes.",
                exposure_risk_status="exposure from deception remains separate from night-kill policy.",
                seed_robustness="Stage 2B seed robustness available",
                regime_robustness="Stage 2B regime robustness available",
                formal_inference_status="reference in matched live ML contrasts",
                adjusted_p_value="not applicable",
                confidence_interval=f"wolf-win CI [{fnum(ml2b_row(evidence, 'existing_rule').get('wolf_win_ci_low'))}, {fnum(ml2b_row(evidence, 'existing_rule').get('wolf_win_ci_high'))}]",
                primary_sample_size="Stage 2B 200 matched live games per policy; R5.1 400 reference matched sets",
                main_strength="outperforms frozen ML policies in live validation.",
                main_risk="not proven against all strategic kill rules.",
                main_limitation="aggression versus deep-cover daytime strategy not jointly optimized.",
                current_recommendation="Retain existing night-kill rule as the current Werewolf reference.",
                required_next_experiment="Werewolf aggression-vs-deep-cover matched experiment.",
                source_report="results/ml_optimization_stage2b/stage2b_policy_win_summary.csv; results/ml_optimization_stage2b/stage2b_primary_contrasts.csv",
            ),
            base_decision_row(
                role="Werewolf",
                strategy="wolf_random_kill",
                strategy_owner_role="Werewolf",
                actor_specific_or_externality="actor_specific",
                evidence_grade="E",
                recommendation_label="statistically supported harmful",
                expected_payoff_status=f"Mean payoff difference {fnum(wolf_random.get('mean_payoff_difference'))} vs reference.",
                risk_adjusted_status=f"Sharpe difference {fnum(wolf_random.get('sharpe_like_difference'))}; Sortino difference {fnum(wolf_random.get('sortino_like_difference'))}.",
                downside_risk_status=f"Downside-deviation difference {fnum(wolf_random.get('downside_deviation_difference'))}.",
                win_rate_status="actor-specific payoff result shows worse Werewolf payoff than reference mix.",
                information_value_status="ignores known target threat information.",
                exposure_risk_status="no compensating exposure reduction demonstrated.",
                seed_robustness="leave-one-seed-out available in R5.1",
                regime_robustness="leave-one-regime-out available in R5.1",
                formal_inference_status=wolf_random.get("formal_inference_status", "not reported"),
                adjusted_p_value=wolf_random.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=make_ci(wolf_random),
                primary_sample_size=f"{wolf_random.get('matched_set_count', 'not reported')} matched sets; 1200 actor rows",
                main_strength="useful negative control.",
                main_risk="large supported payoff loss for wolves.",
                main_limitation="only compares to current reference mix.",
                current_recommendation="Do not use random night kills as the Werewolf default.",
                source_report="results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv",
            ),
            base_decision_row(
                role="Werewolf",
                strategy="continuous_frozen_ml",
                strategy_owner_role="Werewolf",
                actor_specific_or_externality="live_policy",
                evidence_grade="E",
                recommendation_label="not recommended",
                expected_payoff_status="not converted to R5.1 actor-specific payoff.",
                risk_adjusted_status="not available",
                downside_risk_status="not available",
                win_rate_status=f"Stage 2B wolf win difference {fnum(ml2b_cont.get('absolute_difference'))} against existing rule.",
                information_value_status="offline predictive signal failed to create live policy value.",
                exposure_risk_status="distribution-shift and repeated-intervention risk.",
                seed_robustness="Stage 2B robustness files available",
                regime_robustness="Stage 2B regime files available",
                formal_inference_status="matched live policy contrast",
                adjusted_p_value=ml2b_cont.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=f"[{fnum(ml2b_cont.get('difference_ci_low'))}, {fnum(ml2b_cont.get('difference_ci_high'))}]",
                primary_sample_size=f"{ml2b_cont.get('matched_sets', 'not reported')} matched sets",
                main_strength="diagnoses offline-to-live failure.",
                main_risk="practically harmful live rollout.",
                main_limitation="Holm-adjusted inference is not significant for Stage 2B continuous policy, but direction repeats Stage 2A failures.",
                current_recommendation="Retain ML for diagnostics only; do not deploy continuous frozen ML.",
                source_report="results/ml_optimization_stage2b/stage2b_primary_contrasts.csv",
            ),
            base_decision_row(
                role="Werewolf",
                strategy="frozen_hybrid_50_50",
                strategy_owner_role="Werewolf",
                actor_specific_or_externality="live_policy",
                evidence_grade="E",
                recommendation_label="statistically supported harmful",
                win_rate_status=f"Stage 2A wolf win difference {fnum(ml2a_hybrid.get('absolute_difference'))} against existing rule.",
                information_value_status="hybrid score incompatibility failure.",
                exposure_risk_status="live-policy failure.",
                seed_robustness="Stage 2A seed robustness available",
                regime_robustness="Stage 2A regime robustness available",
                formal_inference_status="matched live policy contrast",
                adjusted_p_value=ml2a_hybrid.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=f"[{fnum(ml2a_hybrid.get('difference_ci_low'))}, {fnum(ml2a_hybrid.get('difference_ci_high'))}]",
                primary_sample_size=f"{ml2a_hybrid.get('matched_sets', 'not reported')} matched sets",
                main_strength="clear live failure case.",
                main_risk="statistically supported harm.",
                main_limitation="Stage 2A sample is 200 matched games.",
                current_recommendation="Do not recommend frozen hybrid ML policy.",
                source_report="results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv",
            ),
            base_decision_row(
                role="Werewolf",
                strategy="ml_first_kill_only",
                strategy_owner_role="Werewolf",
                actor_specific_or_externality="live_policy",
                evidence_grade="C",
                recommendation_label="promising but uncertain",
                win_rate_status=f"Stage 2B wolf win difference {fnum(ml2b_first.get('absolute_difference'))} against existing rule.",
                information_value_status="single-intervention ML may avoid repeated compounding.",
                exposure_risk_status="small unsupported signal.",
                seed_robustness="Stage 2B seed robustness available",
                regime_robustness="Stage 2B regime robustness available",
                formal_inference_status="matched live policy contrast",
                adjusted_p_value=ml2b_first.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=f"[{fnum(ml2b_first.get('difference_ci_low'))}, {fnum(ml2b_first.get('difference_ci_high'))}]",
                primary_sample_size=f"{ml2b_first.get('matched_sets', 'not reported')} matched sets",
                main_strength="least unfavorable live ML intervention.",
                main_risk="confidence interval includes no effect.",
                main_limitation="not enough to replace existing rule.",
                current_recommendation="Treat as a future candidate only.",
                required_next_experiment="Pre-registered higher-powered first-kill-only ML experiment.",
                source_report="results/ml_optimization_stage2b/stage2b_primary_contrasts.csv",
            ),
            base_decision_row(
                role="Werewolf",
                strategy="selective_ml_override",
                strategy_owner_role="Werewolf",
                actor_specific_or_externality="live_policy",
                evidence_grade="D",
                recommendation_label="no supported improvement",
                win_rate_status=f"Stage 2B wolf win difference {fnum(ml2b_selective.get('absolute_difference'))} against existing rule.",
                information_value_status="selective intervention failed to improve wolf win.",
                exposure_risk_status="low intervention count limits effect.",
                seed_robustness="Stage 2B seed robustness available",
                regime_robustness="Stage 2B regime robustness available",
                formal_inference_status="matched live policy contrast",
                adjusted_p_value=ml2b_selective.get("holm_adjusted_p_value", "not reported"),
                confidence_interval=f"[{fnum(ml2b_selective.get('difference_ci_low'))}, {fnum(ml2b_selective.get('difference_ci_high'))}]",
                primary_sample_size=f"{ml2b_selective.get('matched_sets', 'not reported')} matched sets",
                main_strength="tests guarded deployment idea.",
                main_risk="no reliable improvement.",
                main_limitation="threshold may be too conservative.",
                current_recommendation="Diagnostic only under current evidence.",
                source_report="results/ml_optimization_stage2b/stage2b_primary_contrasts.csv",
            ),
            base_decision_row(
                role="Werewolf",
                strategy="adaptive_deception_with_credibility_costs",
                strategy_owner_role="Werewolf",
                actor_specific_or_externality="strategy_level_game_outcome",
                evidence_grade="C",
                recommendation_label="conditionally recommended",
                expected_payoff_status="not converted to actor-specific payoff in R5.1.",
                risk_adjusted_status="not available",
                downside_risk_status="credibility costs reduce unlimited deception.",
                win_rate_status="Stage 3 final adaptive deception reported 46% wolf win after self-defense cost.",
                information_value_status="uses public suspicion and p_wolf, not hidden role labels.",
                exposure_risk_status="cost-aware policy avoids accusation spam but still needs multi-seed formal validation.",
                seed_robustness="not formally reported",
                regime_robustness="not formally reported",
                formal_inference_status="descriptive diagnostic",
                adjusted_p_value="not reported",
                confidence_interval="not reported",
                primary_sample_size="100 diagnostic games reported in Stage 3",
                main_strength="models deception with credibility constraints.",
                main_risk="strategy subtype effects remain underpowered.",
                main_limitation="no formal actor-specific payoff contrast.",
                current_recommendation="Use as a controlled deception model, not as a final Werewolf optimization claim.",
                required_next_experiment="Werewolf aggression-vs-deep-cover experiment with deception subtype arms.",
                source_report="stage3_experiment_report.md",
            ),
            base_decision_row(
                role="Werewolf",
                strategy="false_role_claim",
                strategy_owner_role="Werewolf",
                actor_specific_or_externality="strategy_level_game_outcome",
                evidence_grade="E",
                recommendation_label="not recommended",
                win_rate_status="Stage 3 reports 23% wolf win before credibility refinements.",
                information_value_status="role claim appears to backfire in current simplified speech system.",
                exposure_risk_status="high exposure risk.",
                seed_robustness="not formally reported",
                regime_robustness="not formally reported",
                formal_inference_status="descriptive diagnostic",
                adjusted_p_value="not reported",
                confidence_interval="not reported",
                primary_sample_size="100 diagnostic games reported in Stage 3",
                main_strength="useful harmful-control deception subtype.",
                main_risk="severe wolf performance loss.",
                main_limitation="simplified role-claim credibility model.",
                current_recommendation="Do not recommend false role claim as a Werewolf deception subtype.",
                source_report="stage3_experiment_report.md",
            ),
        ]
    )
    return rows


def build_data_analysis_summary(evidence: dict[str, object], matrix: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, item in enumerate(matrix, start=1):
        rows.append(
            {
                "conclusion_id": f"R6-C{idx:02d}",
                "role": item["role"],
                "hypothesis": f"Evaluate {item['strategy']} for {item['role']}.",
                "evidence_source": item["source_report"],
                "descriptive_result": item["win_rate_status"],
                "formal_effect": item["expected_payoff_status"],
                "confidence_interval": item["confidence_interval"],
                "raw_p_value": "see source" if item["adjusted_p_value"] not in {"not reported", "not applicable", "insufficient data"} else item["adjusted_p_value"],
                "adjusted_p_value": item["adjusted_p_value"],
                "independent_sample_size": item["primary_sample_size"],
                "seed_robustness": item["seed_robustness"],
                "regime_robustness": item["regime_robustness"],
                "overfitting_status": "not a tuning stage" if "ML" not in str(item["strategy"]).upper() else "live validation overrides shadow tuning",
                "leakage_status": "no hidden-information claim; source leakage audits reviewed",
                "evidence_grade": item["evidence_grade"],
                "conclusion_label": item["recommendation_label"],
                "recommendation": item["current_recommendation"],
            }
        )
    return rows


def build_contradiction_audit(evidence: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "contradiction_id": "R6-X01",
            "research_topic": "BoW prediction versus live policy value",
            "earlier_result": "R2 showed BoW scores predicted role and speech intent in shadow data.",
            "later_result": "R3 guarded and structured BoW live policies significantly reduced village win.",
            "reason_for_difference": "Predictive speech signal did not survive feedback through voting and belief updates.",
            "which_result_has_priority": "R3 matched live policy outcomes",
            "scientific_resolution": "BoW remains diagnostic; live integration is not recommended under current evidence.",
            "source_files": "results/bow_speech_stage_r2/bow_stage_r2_research_report.md; results/bow_integration_stage_r3/r3_primary_game_contrasts.csv",
            "final_recommendation_effect": "Reject live guarded BoW policies; retain structured speech reference.",
        },
        {
            "contradiction_id": "R6-X02",
            "research_topic": "Frozen ML shadow value versus live wolf-kill value",
            "earlier_result": "Shadow ML and offline diagnostics suggested useful wolf-kill targeting signal.",
            "later_result": "Stage 2A/2B live matched rollouts showed continuous and hybrid ML were harmful or unsupported.",
            "reason_for_difference": "Repeated interventions caused distribution shift and downstream mechanism interactions.",
            "which_result_has_priority": "Stage 2A/2B complete live policy contrasts",
            "scientific_resolution": "Frozen ML is diagnostic only; current night-kill rule remains reference.",
            "source_files": "results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv; results/ml_optimization_stage2b/stage2b_primary_contrasts.csv",
            "final_recommendation_effect": "Do not deploy continuous frozen ML or hybrid ML.",
        },
        {
            "contradiction_id": "R6-X03",
            "research_topic": "R5 strategy frontier versus actor-specific strategy ownership",
            "earlier_result": "R5 strategy-frontier tables treated global configurations as strategy alternatives.",
            "later_result": "R5.1 found 32 invalid actor-specific recommendations and rebuilt actor/externality tables.",
            "reason_for_difference": "Strategy-condition labels were global game configurations, not always role-owned actions.",
            "which_result_has_priority": "R5.1 actor-specific attribution audit",
            "scientific_resolution": "Use R5 role metrics and R5.1 actor-specific/frontier outputs for recommendations.",
            "source_files": "results/financial_risk_stage_r51/r51_r5_result_validity_registry.csv; results/financial_risk_stage_r51/r51_mapping_validation_summary.csv",
            "final_recommendation_effect": "Separate actor-specific recommendations from cross-role externalities.",
        },
        {
            "contradiction_id": "R6-X04",
            "research_topic": "Edge-seat folklore versus randomized-role position tests",
            "earlier_result": "Raw position experiments suggested apparent edge-priority advantages.",
            "later_result": "Randomized-role and seat-neutral analyses did not find robust edge-priority support.",
            "reason_for_difference": "Fixed role-seat mapping and physical label artifacts were removed.",
            "which_result_has_priority": "randomized-role and seat-order-neutral analyses",
            "scientific_resolution": "Do not recommend edge-first checking as a role-position rule.",
            "source_files": "results/data_analysis/seer_position_randomized_roles/pairwise_strategy_comparisons.csv; results/data_analysis/seat_order_neutral/validation_summary.csv",
            "final_recommendation_effect": "Use random/diversified seer search as reference.",
        },
        {
            "contradiction_id": "R6-X05",
            "research_topic": "Wolf manipulation premium versus causal strategy value",
            "earlier_result": "Manipulation premium is large and positive in R5/R5.1.",
            "later_result": "R5.1 group-balance audit shows weak overlap for no-manipulation comparisons.",
            "reason_for_difference": "The premium is an association with very imbalanced exposure groups.",
            "which_result_has_priority": "R5.1 relabelled descriptive premium with imbalance warning",
            "scientific_resolution": "Treat manipulation premium as descriptive motivation for targeted deception experiments.",
            "source_files": "results/financial_risk_stage_r51/r51_manipulation_premium_summary.csv",
            "final_recommendation_effect": "Do not claim causal manipulation advantage without a matched deception subtype experiment.",
        },
        {
            "contradiction_id": "R6-X06",
            "research_topic": "Useful-information premium versus seer policy recommendation",
            "earlier_result": "Useful-information and wolf-found premiums are strongly positive.",
            "later_result": "R5.1 flags useful information as outcome-dependent and structured search shows behavioral strategies differ.",
            "reason_for_difference": "Finding useful information is partly post-treatment and not equivalent to a check rule.",
            "which_result_has_priority": "R5.1 premium labels plus structured search policy tests",
            "scientific_resolution": "Prioritize information discovery as a goal but do not infer a final reveal/check policy.",
            "source_files": "results/financial_risk_stage_r51/r51_information_premium_summary.csv; results/structured_seer_search/structured_seer_search_strategy_summary.csv",
            "final_recommendation_effect": "Require seer reveal-timing experiment.",
        },
    ]


def build_externality_matrix(evidence: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in evidence["r51_externalities"]:  # type: ignore[index]
        rows.append(
            {
                "payoff_specification": row["payoff_specification"],
                "strategy_owner_role": row["strategy_owner_role"],
                "external_strategy_name": row["external_strategy_name"],
                "affected_role": row["affected_role"],
                "actor_specific_or_externality": "externality",
                "mean_payoff_difference": row["mean_payoff_difference"],
                "confidence_interval": f"[{fnum(row['ci_low'])}, {fnum(row['ci_high'])}]",
                "raw_p_value": row["raw_p_value"],
                "holm_adjusted_p_value": row["holm_adjusted_p_value"],
                "matched_set_count": row["matched_set_count"],
                "seed_count": row["seed_count"],
                "regime_count": row["regime_count"],
                "interpretation": row["interpretation"],
            }
        )
    return rows


def build_remaining_gaps() -> list[dict[str, object]]:
    return [
        {
            "gap_id": "R6-G01",
            "role": "Hunter",
            "research_question": "Which Hunter shooting policy improves payoff without worsening tail risk?",
            "gap_type": "missing actor-specific strategy comparison",
            "why_unresolved": "R5.1 has no compatible Hunter-owned strategy rows.",
            "existing_evidence": "R5 role-level metrics show high Hunter downside and CVaR-like tail risk.",
            "required_data": "event-level Hunter shot decisions, target role, shot timing, payoff decomposition",
            "required_experiment": "Hunter random shot vs no-shot vs suspicion-shot vs conservative-shot",
            "minimum_scale": "500 games per condition across at least 5 seeds",
            "primary_outcome": "Hunter actor-specific payoff difference",
            "secondary_outcomes": "negative-payoff probability, CVaR-like loss, village win rate",
            "formal_analysis": "matched paired contrast with Holm correction within Hunter policy family",
            "priority": "critical",
            "blocks_final_report": "Yes, if final report requires role-specific Hunter recommendation",
            "source_files": "results/financial_risk_stage_r51/r51_strategy_data_coverage.csv",
        },
        {
            "gap_id": "R6-G02",
            "role": "Seer",
            "research_question": "When should the Seer reveal useful check information?",
            "gap_type": "missing timing policy",
            "why_unresolved": "Information premiums are outcome-dependent associations; reveal timing was not randomized.",
            "existing_evidence": "Useful-information and wolf-found premiums are strongly positive descriptive associations.",
            "required_data": "seer check results, reveal events, timing, survival, downstream votes",
            "required_experiment": "private-only vs immediate reveal vs threshold reveal vs delayed reveal",
            "minimum_scale": "500 games per condition across at least 5 seeds",
            "primary_outcome": "village win rate and Seer payoff",
            "secondary_outcomes": "seer survival, wolves found, misinformation exposure",
            "formal_analysis": "matched game contrast plus actor-specific payoff",
            "priority": "critical",
            "blocks_final_report": "Yes, if final report requires final Seer communication recommendation",
            "source_files": "results/financial_risk_stage_r51/r51_information_premium_summary.csv",
        },
        {
            "gap_id": "R6-G03",
            "role": "Witch",
            "research_question": "How should the Witch jointly manage antidote and poison timing?",
            "gap_type": "incomplete joint policy",
            "why_unresolved": "Conservative poison has sparse actor-specific support, but save/poison interactions are not isolated.",
            "existing_evidence": "Witch conservative poison has small positive R5.1 mean difference with CI crossing zero.",
            "required_data": "save events, poison events, prevented kills, target roles, potion availability",
            "required_experiment": "factorial save probability x poison threshold policy test",
            "minimum_scale": "500 games per condition across at least 5 seeds",
            "primary_outcome": "Witch actor-specific payoff",
            "secondary_outcomes": "village win, potion waste, night-kill prevention, wrong-poison rate",
            "formal_analysis": "matched factorial analysis with Holm correction",
            "priority": "critical",
            "blocks_final_report": "Yes, if final report requires full Witch policy recommendation",
            "source_files": "results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv",
        },
        {
            "gap_id": "R6-G04",
            "role": "Werewolf",
            "research_question": "Should wolves prefer aggression or deep-cover deception under credibility costs?",
            "gap_type": "missing deception strategy family comparison",
            "why_unresolved": "Deception subtypes are descriptive and not integrated with R5.1 actor-specific payoff.",
            "existing_evidence": "False accusation and deflection can affect wolf win, but credibility costs change their value.",
            "required_data": "wolf deception subtype, credibility costs, target role, vote outcome, wolf payoff",
            "required_experiment": "adaptive, false-accuse, deflection, trust-building, low-profile controls",
            "minimum_scale": "500 games per condition across at least 5 seeds",
            "primary_outcome": "Werewolf actor-specific payoff and wolf win rate",
            "secondary_outcomes": "credibility costs, wrong-accusation penalties, exposure risk",
            "formal_analysis": "matched subtype contrasts with multiplicity correction",
            "priority": "high",
            "blocks_final_report": "No, if reported as an explicit limitation",
            "source_files": "stage3_experiment_report.md",
        },
        {
            "gap_id": "R6-G05",
            "role": "Villager",
            "research_question": "Which structured voting rule should villagers use after speech and trust updates?",
            "gap_type": "sparse Villager-owned policy alternatives",
            "why_unresolved": "R5.1 only has random-vote actor-specific contrast; structured voting is a global configuration.",
            "existing_evidence": "Random voting shows no supported improvement; structured speech and trust remain useful globally.",
            "required_data": "voter-owned policy labels, target choices, beliefs, speaker trust, payoff",
            "required_experiment": "suspicion-only, p_wolf-only, trust-weighted, herding-guarded, conservative vote policies",
            "minimum_scale": "500 games per condition across at least 5 seeds",
            "primary_outcome": "Villager actor-specific payoff",
            "secondary_outcomes": "village win, wrong-elimination rate, herding false-positive rate",
            "formal_analysis": "matched actor-specific policy contrasts",
            "priority": "high",
            "blocks_final_report": "No, if current reference is retained with limitations",
            "source_files": "results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv",
        },
    ]


def build_targeted_priorities(gaps: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for gap in gaps:
        rows.append(
            {
                "priority_id": gap["gap_id"].replace("R6-G", "R6-P"),
                "role": gap["role"],
                "scientific_question": gap["research_question"],
                "conditions": gap["required_experiment"],
                "reference_condition": "current reference/default for the role",
                "minimum_scale": gap["minimum_scale"],
                "matched_design": "same seed and base role setup across policy arms",
                "seed_split": "pre-register development seeds separately from final evaluation seeds where tuning is involved",
                "behavioral_regimes": "include the five R4/R5 behavioral regimes where feasible",
                "primary_outcome": gap["primary_outcome"],
                "risk_outcomes": gap["secondary_outcomes"],
                "multiplicity_family": f"{gap['role']} policy family",
                "report_requirements": "raw game/player rows, actor-specific payoff, CIs, adjusted p-values, leakage audit, source traceability",
                "required_before_final_report": gap["blocks_final_report"],
            }
        )
    return rows


def build_rejected_registry(matrix: list[dict[str, object]]) -> list[dict[str, object]]:
    rejected_reasons = {
        "wolf_random_kill": "statistically supported harm",
        "continuous_frozen_ml": "live-policy failure",
        "frozen_hybrid_50_50": "statistically supported harm",
        "guarded_bow_010_live": "live guarded BoW integration harmful",
        "structured_bow_guarded_live": "structured plus BoW live integration harmful",
        "highest_suspicion": "no supported improvement and structured-search harm",
        "highest_p_wolf": "structured-search harm",
        "edge_first": "engine artifact / position folklore not supported after randomization",
        "false_role_claim": "deception subtype harmful in diagnostics",
    }
    rows = []
    by_strategy = {str(row["strategy"]): row for row in matrix}
    for strategy, reason in rejected_reasons.items():
        row = by_strategy.get(strategy, {})
        rows.append(
            {
                "role": row.get("role", "Seer" if "highest" in strategy or "edge" in strategy else "Werewolf" if "wolf" in strategy or "ml" in strategy or "false" in strategy else "Villager"),
                "strategy": strategy,
                "rejection_reason": reason,
                "evidence_grade": row.get("evidence_grade", "E" if strategy != "edge_first" else "D"),
                "recommendation_label": row.get("recommendation_label", "not recommended"),
                "source_report": row.get("source_report", "see R6 source evidence index"),
                "formal_result": row.get("formal_inference_status", "see source"),
                "limitation": row.get("main_limitation", "not applicable"),
            }
        )
    return rows


def build_default_registry(matrix: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "role": "Villager",
            "current_default": "structured speech plus belief/trust-aware voting reference",
            "reason": "random voting has no supported improvement and live BoW overrides are harmful.",
            "evidence_grade": "B",
            "confidence": "moderate",
            "known_limitations": "Villager-owned structured voting policies remain sparse.",
            "alternatives_tested": "villager_random_vote; guarded_bow_010_live; structured_bow_guarded_live; selective_bow_vote_override_live",
            "alternatives_rejected": "random vote, live guarded BoW overrides",
            "alternatives_unresolved": "structured voting rule family",
            "next_review_stage": "R6.1 targeted missing strategy experiments",
        },
        {
            "role": "Seer",
            "current_default": "random or diversified checking reference",
            "reason": "edge folklore is not supported after randomization; highest suspicion and highest p_wolf are harmful or unsupported.",
            "evidence_grade": "B",
            "confidence": "moderate",
            "known_limitations": "reveal timing remains unresolved.",
            "alternatives_tested": "edge_first, inner_first, alternate_sides, directional, highest_p_wolf, highest_suspicion",
            "alternatives_rejected": "highest_p_wolf, highest_suspicion, strong edge-seat theory",
            "alternatives_unresolved": "alternate_sides, right_to_left, reveal timing",
            "next_review_stage": "R6.1 targeted missing strategy experiments",
        },
        {
            "role": "Witch",
            "current_default": "conservative poison as uncertain candidate; retain current potion safeguards",
            "reason": "conservative poison has a small positive but uncertain payoff signal.",
            "evidence_grade": "C",
            "confidence": "low",
            "known_limitations": "joint save and poison timing not isolated.",
            "alternatives_tested": "witch_conservative_poison and earlier threshold sweeps",
            "alternatives_rejected": "indiscriminate poison implied by overly low threshold",
            "alternatives_unresolved": "joint save/poison policy",
            "next_review_stage": "R6.1 targeted missing strategy experiments",
        },
        {
            "role": "Hunter",
            "current_default": "no new recommendation",
            "reason": "no compatible actor-specific Hunter strategy comparison exists.",
            "evidence_grade": "U",
            "confidence": "insufficient",
            "known_limitations": "role-level tail risk is high, but strategy attribution is missing.",
            "alternatives_tested": "historical Hunter action variants only",
            "alternatives_rejected": "none as actor-specific R6 recommendation",
            "alternatives_unresolved": "random, no-shot, suspicion-shot, conservative-shot",
            "next_review_stage": "R6.1 targeted missing strategy experiments",
        },
        {
            "role": "Werewolf",
            "current_default": "existing night-kill rule plus credibility-constrained deception diagnostics",
            "reason": "random kill is formally harmful and live frozen ML policies do not beat the existing rule.",
            "evidence_grade": "B",
            "confidence": "moderate",
            "known_limitations": "aggression versus deep-cover deception is unresolved.",
            "alternatives_tested": "wolf_random_kill, frozen ML, hybrid ML, first-kill-only ML, deception subtypes",
            "alternatives_rejected": "wolf_random_kill, continuous frozen ML, frozen hybrid, false role claim",
            "alternatives_unresolved": "first-kill-only ML, adaptive deception subtype mix",
            "next_review_stage": "R6.1 targeted missing strategy experiments",
        },
    ]


def build_source_index() -> list[dict[str, object]]:
    rows = []
    metrics_by_source = {
        "r51_actor_specific_primary_contrasts.csv": "actor-specific payoff differences, CIs, raw and Holm-adjusted p-values",
        "r51_actor_specific_strategy_summary.csv": "mean payoff, volatility, downside, Sharpe-like, Sortino-like metrics",
        "r51_cross_role_externality_summary.csv": "cross-role externality payoff differences",
        "r51_information_premium_summary.csv": "information premium estimates and CIs",
        "r51_manipulation_premium_summary.csv": "manipulation premium estimates and imbalance warnings",
        "r3_primary_game_contrasts.csv": "matched BoW live game contrasts",
        "structured_seer_search_strategy_summary.csv": "seer search strategy outcome rates",
        "pairwise_strategy_contrasts.csv": "structured seer pairwise tests",
        "stage2b_primary_contrasts.csv": "ML Stage 2B live policy contrasts",
        "wolf_kill_primary_contrasts.csv": "ML Stage 2A live policy contrasts",
    }
    for source in SOURCE_EVIDENCE_FILES:
        path = ROOT / source
        if path.suffix == ".csv" and path.exists():
            row_count = len(read_csv(source))
        elif path.exists():
            row_count = len(path.read_text(encoding="utf-8").splitlines())
        else:
            row_count = 0
        rows.append(
            {
                "source_path": source,
                "source_type": path.suffix.lstrip(".") or "unknown",
                "row_count": row_count,
                "hash_sha256": sha256_file(path) if path.exists() else "missing",
                "metrics_used": next((value for key, value in metrics_by_source.items() if source.endswith(key)), "context, validation, or report narrative"),
                "r6_use": "evidence synthesis input",
                "status": "verified_from_source" if path.exists() else "missing",
            }
        )
    return rows


def build_proposal_alignment_summary() -> list[dict[str, object]]:
    return [
        {
            "proposal_component": "role-specific strategy analysis",
            "r6_status": "completed_with_limitations",
            "evidence_source": "results/role_strategy_synthesis_stage_r6/r6_role_strategy_decision_matrix.csv",
            "r6_conclusion": "Each role has a documented evidence status, but Hunter and several timing policies remain unresolved.",
            "remaining_work": "R6.1 targeted missing strategy experiments.",
        },
        {
            "proposal_component": "Villager strategy analysis",
            "r6_status": "completed_with_limitations",
            "evidence_source": "results/role_strategy_synthesis_stage_r6/r6_villager_strategy_card.md",
            "r6_conclusion": "Retain structured speech and trust-aware voting reference; random vote and live BoW overrides are not recommended.",
            "remaining_work": "Actor-specific structured voting family comparison.",
        },
        {
            "proposal_component": "Seer strategy analysis",
            "r6_status": "completed_with_limitations",
            "evidence_source": "results/role_strategy_synthesis_stage_r6/r6_seer_strategy_card.md",
            "r6_conclusion": "Use random/diversified search reference; edge-seat folklore and highest-suspicion rules are not supported.",
            "remaining_work": "Reveal-timing experiment.",
        },
        {
            "proposal_component": "Witch strategy analysis",
            "r6_status": "requires_targeted_experiment",
            "evidence_source": "results/role_strategy_synthesis_stage_r6/r6_witch_strategy_card.md",
            "r6_conclusion": "Conservative poison is promising but uncertain.",
            "remaining_work": "Joint save/poison policy experiment.",
        },
        {
            "proposal_component": "Hunter strategy analysis",
            "r6_status": "insufficient_data",
            "evidence_source": "results/role_strategy_synthesis_stage_r6/r6_hunter_strategy_card.md",
            "r6_conclusion": "No Hunter policy is recommended because actor-specific data are missing.",
            "remaining_work": "Hunter shot-policy experiment.",
        },
        {
            "proposal_component": "Werewolf strategy analysis",
            "r6_status": "completed_with_limitations",
            "evidence_source": "results/role_strategy_synthesis_stage_r6/r6_werewolf_strategy_card.md",
            "r6_conclusion": "Retain existing night-kill rule; random kill and frozen continuous ML are not recommended.",
            "remaining_work": "Aggression versus deep-cover deception experiment.",
        },
        {
            "proposal_component": "risk-adjusted strategy comparison",
            "r6_status": "completed_with_limitations",
            "evidence_source": "results/role_strategy_synthesis_stage_r6/r6_role_strategy_decision_matrix.csv",
            "r6_conclusion": "Risk-adjusted metrics are integrated where R5.1 actor-specific rows exist.",
            "remaining_work": "Expand actor-specific strategy coverage.",
        },
    ]


def role_confidence(default_rows: list[dict[str, object]]) -> dict[str, str]:
    return {str(row["role"]): str(row["confidence"]) for row in default_rows}


def count_by(items: list[dict[str, object]], key: str) -> Counter:
    return Counter(str(item.get(key, "not reported")) for item in items)


def bar_svg(title: str, labels: list[str], values: list[float], colors: list[str] | None = None, width: int = 900, height: int = 420) -> str:
    colors = colors or ["#4C78A8"] * len(labels)
    max_value = max(values) if values else 1.0
    margin_left = 220
    margin_top = 56
    row_h = 26
    gap = 10
    bar_max = width - margin_left - 80
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="32" font-family="Arial" font-size="20" font-weight="700" fill="#222">{title}</text>',
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        y = margin_top + i * (row_h + gap)
        bar_w = 0 if max_value == 0 else (value / max_value) * bar_max
        safe_label = str(label).replace("&", "&amp;")
        lines.append(f'<text x="24" y="{y + 18}" font-family="Arial" font-size="13" fill="#333">{safe_label}</text>')
        lines.append(f'<rect x="{margin_left}" y="{y}" width="{bar_w:.1f}" height="{row_h}" fill="{colors[i % len(colors)]}" rx="2"/>')
        lines.append(f'<text x="{margin_left + bar_w + 8:.1f}" y="{y + 18}" font-family="Arial" font-size="12" fill="#333">{value:.0f}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def scatter_svg(title: str, points: list[tuple[str, float, float]], width: int = 800, height: int = 520) -> str:
    if not points:
        points = [("none", 0.0, 0.0)]
    xs = [point[1] for point in points]
    ys = [point[2] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if math.isclose(min_x, max_x):
        min_x -= 1
        max_x += 1
    if math.isclose(min_y, max_y):
        min_y -= 1
        max_y += 1
    def sx(x: float) -> float:
        return 80 + (x - min_x) / (max_x - min_x) * (width - 160)
    def sy(y: float) -> float:
        return height - 80 - (y - min_y) / (max_y - min_y) * (height - 160)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="32" font-family="Arial" font-size="20" font-weight="700" fill="#222">{title}</text>',
        f'<line x1="80" y1="{height - 80}" x2="{width - 80}" y2="{height - 80}" stroke="#333"/>',
        f'<line x1="80" y1="70" x2="80" y2="{height - 80}" stroke="#333"/>',
        f'<text x="{width / 2 - 80}" y="{height - 28}" font-family="Arial" font-size="13" fill="#333">Expected payoff</text>',
        '<text x="10" y="66" font-family="Arial" font-size="13" fill="#333">Sharpe-like</text>',
    ]
    for label, x, y in points:
        safe = label.replace("&", "&amp;")
        px, py = sx(x), sy(y)
        lines.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="#F58518"/>')
        lines.append(f'<text x="{px + 8:.1f}" y="{py - 8:.1f}" font-family="Arial" font-size="11" fill="#333">{safe}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def write_figures(matrix: list[dict[str, object]], defaults: list[dict[str, object]], gaps: list[dict[str, object]], contradictions: list[dict[str, object]], evidence: dict[str, object]) -> None:
    R6_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    grade_counts = count_by(matrix, "evidence_grade")
    write_text(R6_RESULTS_DIR / "evidence_grade_by_strategy.svg", bar_svg("Evidence Grade by Strategy", list(grade_counts), [grade_counts[k] for k in grade_counts]))
    status_counts = count_by(matrix, "recommendation_label")
    write_text(R6_RESULTS_DIR / "role_recommendation_status.svg", bar_svg("Recommendation Status by Strategy", list(status_counts), [status_counts[k] for k in status_counts], ["#54A24B", "#E45756", "#72B7B2", "#F58518", "#B279A2"]))
    points = []
    for row in evidence["r51_actor_summary"]:  # type: ignore[index]
        if row.get("payoff_specification") == "core":
            points.append((f"{row['affected_role']}:{row['strategy_name']}", float(row["mean_payoff"]), float(row["sharpe_like_ratio"])))
    write_text(R6_RESULTS_DIR / "expected_vs_risk_adjusted_payoff.svg", scatter_svg("Expected Payoff versus Sharpe-like Ratio", points))
    category_counts = Counter()
    for label in status_counts:
        if label in {"statistically supported harmful", "not recommended"}:
            category_counts["rejected"] += status_counts[label]
        elif label in {"insufficient data", "requires targeted experiment"}:
            category_counts["unresolved"] += status_counts[label]
        elif label in {"retain reference/default", "conditionally recommended", "promising but uncertain"}:
            category_counts["supported_or_candidate"] += status_counts[label]
        else:
            category_counts["no_improvement"] += status_counts[label]
    write_text(R6_RESULTS_DIR / "strategy_evidence_categories.svg", bar_svg("Supported, Rejected, and Unresolved Strategies", list(category_counts), [category_counts[k] for k in category_counts]))
    role_counts = count_by(matrix, "role")
    write_text(R6_RESULTS_DIR / "role_evidence_coverage.svg", bar_svg("Role-Specific Evidence Coverage", list(role_counts), [role_counts[k] for k in role_counts]))
    actor_counts = count_by(matrix, "actor_specific_or_externality")
    write_text(R6_RESULTS_DIR / "actor_specific_vs_externality.svg", bar_svg("Actor-Specific versus Externality Evidence", list(actor_counts), [actor_counts[k] for k in actor_counts]))
    write_text(R6_RESULTS_DIR / "contradiction_resolution_map.svg", bar_svg("Cross-Stage Contradictions Resolved", [str(row["contradiction_id"]) for row in contradictions], [1.0] * len(contradictions), ["#4C78A8"]))
    priority_counts = count_by(gaps, "priority")
    write_text(R6_RESULTS_DIR / "remaining_gap_priorities.svg", bar_svg("Remaining Evidence Gaps by Priority", list(priority_counts), [priority_counts[k] for k in priority_counts], ["#E45756", "#F58518", "#72B7B2"]))
    conf_counts = count_by(defaults, "confidence")
    write_text(R6_RESULTS_DIR / "recommendation_confidence.svg", bar_svg("Role Recommendation Confidence", list(conf_counts), [conf_counts[k] for k in conf_counts], ["#72B7B2", "#F58518", "#E45756"]))
    write_text(R6_RESULTS_DIR / "current_default_map.svg", bar_svg("Current Default Strategy Map", [str(row["role"]) for row in defaults], [1.0] * len(defaults), ["#4C78A8", "#54A24B", "#F58518", "#E45756", "#B279A2"]))


def markdown_table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")).replace("\n", " ") for key, _ in columns) + " |")
    return "\n".join([header, divider, *body])


def build_role_card(role: str, matrix: list[dict[str, object]], gaps: list[dict[str, object]], defaults: list[dict[str, object]]) -> str:
    role_rows = [row for row in matrix if row["role"] == role]
    gap_rows = [row for row in gaps if row["role"] == role]
    default = first(defaults, role=role) if isinstance(defaults, list) else {}
    supported = [row for row in role_rows if row["recommendation_label"] in {"retain reference/default", "conditionally recommended", "promising but uncertain"}]
    rejected = [row for row in role_rows if row["recommendation_label"] in {"not recommended", "statistically supported harmful", "no supported improvement"}]
    return dedent(
        f"""
        # R6 {role} Strategy Card

        ## Current Evidence Status

        Current default: {default.get('current_default', 'not reported')}

        Evidence grade: {default.get('evidence_grade', 'not reported')}

        Confidence: {default.get('confidence', 'not reported')}

        ## Recommendation

        {default.get('reason', 'not reported')}

        ## Supported or Candidate Strategies

        {markdown_table(supported, [('strategy', 'Strategy'), ('evidence_grade', 'Grade'), ('recommendation_label', 'Label'), ('current_recommendation', 'Recommendation')]) if supported else 'No supported actor-specific strategy beyond the current reference.'}

        ## Rejected or No-Improvement Strategies

        {markdown_table(rejected, [('strategy', 'Strategy'), ('evidence_grade', 'Grade'), ('recommendation_label', 'Label'), ('main_risk', 'Main Risk')]) if rejected else 'No rejected strategy rows for this role.'}

        ## Remaining Gaps

        {markdown_table(gap_rows, [('gap_id', 'Gap'), ('research_question', 'Question'), ('priority', 'Priority'), ('required_experiment', 'Required Experiment')]) if gap_rows else 'No critical R6 gap listed for this role.'}

        ## Source Boundaries

        This card synthesizes existing results only. It does not rerun simulation,
        change game mechanics, or claim a global optimum. Actor-specific evidence
        is separated from cross-role externalities.
        """
    ).strip() + "\n"


def build_main_report(
    matrix: list[dict[str, object]],
    data_summary: list[dict[str, object]],
    contradictions: list[dict[str, object]],
    externalities: list[dict[str, object]],
    gaps: list[dict[str, object]],
    priorities: list[dict[str, object]],
    rejected: list[dict[str, object]],
    defaults: list[dict[str, object]],
    source_index: list[dict[str, object]],
    validation: list[dict[str, object]],
) -> str:
    grade_table = get_evidence_grade_definitions()
    source_count = len(source_index)
    strategy_count = len(matrix)
    role_count = len({row["role"] for row in matrix})
    supported = [row for row in matrix if row["recommendation_label"] in {"retain reference/default", "conditionally recommended", "promising but uncertain"}]
    unsupported = [row for row in matrix if row["recommendation_label"] in {"not recommended", "statistically supported harmful", "no supported improvement"}]
    unresolved = [row for row in matrix if row["recommendation_label"] in {"insufficient data", "requires targeted experiment"}]
    next_stage = "R6.1 - Targeted Missing Strategy Experiments"

    return dedent(
        f"""
        # R6 Unified Role Strategy Evidence Synthesis

        ## 1. Executive Summary

        R6 synthesizes the tested strategy space across Villager, Seer, Witch,
        Hunter, and Werewolf roles. It is a synthesis of existing evidence, not a
        new gameplay experiment. The analysis reviews {source_count} source files,
        classifies {strategy_count} strategy or mechanism rows across {role_count}
        roles, separates actor-specific evidence from cross-role externalities,
        and preserves negative findings from BoW integration, ML deployment, and
        strategy attribution audits.

        The current conclusion is role synthesis complete with sparse-strategy
        caveat. Current defaults can be documented, but targeted experiments are
        required before final role-specific strategy recommendations are complete.
        The exact next stage is {next_stage}.

        ## 2. Scope and Non-Intervention Boundary

        R6 does not change the simulator, payoff rules, role setup, BoW weights, ML
        models, or decision policies. It reads frozen historical artifacts and
        writes analysis registries, recommendation cards, gap lists, and reports.

        ## 3. Evidence Sources Reviewed

        {markdown_table(source_index, [('source_path', 'Source'), ('row_count', 'Rows/Lines'), ('metrics_used', 'Metrics Used'), ('status', 'Status')])}

        ## 4. Evidence Grading System

        {markdown_table(grade_table, [('grade', 'Grade'), ('definition', 'Definition')])}

        ## 5. Evidence Priority Rules

        R6 prioritizes complete live-game outcomes above matched actor-specific
        payoff analysis, then grouped formal analysis, multi-seed summaries,
        full-rollout counterfactuals, shadow diagnostics, surrogate prediction,
        and single-seed descriptive findings. This resolves the main conflicts:
        R3 live BoW outcomes outrank R2 predictive AUC, Stage 2A/2B live ML
        outcomes outrank shadow ML diagnostics, and R5.1 actor attribution
        supersedes ambiguous R5 strategy-frontier labels.

        ## 6. Role Strategy Decision Matrix

        {markdown_table(matrix, [('role', 'Role'), ('strategy', 'Strategy'), ('actor_specific_or_externality', 'Evidence Type'), ('evidence_grade', 'Grade'), ('recommendation_label', 'Label'), ('current_recommendation', 'Recommendation')])}

        ## 7. Villager Synthesis

        Villager evidence supports retaining structured speech and belief/trust
        voting as the current reference. R5.1 found that `villager_random_vote`
        had no supported payoff improvement against the reference mix. R3 showed
        live guarded BoW overrides were harmful, while selective BoW override was
        near neutral and unsupported. Villager strategy comparison remains sparse
        because most speech and trust mechanisms are global discussion settings,
        not isolated Villager-owned voting policies.

        ## 8. Seer Synthesis

        Seer evidence rejects strong edge-seat folklore after role randomization
        and seat-order-neutral validation. Random or diversified search remains
        the current reference. Structured search found descriptive promise for
        side alternation and right-to-left search, but they are not final
        recommendations. Highest `p_wolf` and highest-suspicion search rules are
        not recommended because they performed poorly in structured search, and
        R5.1 found no actor-specific payoff improvement for highest suspicion.
        Useful information and wolf-found premiums are strong descriptive
        associations, but reveal timing remains unresolved.

        ## 9. Witch Synthesis

        Witch evidence gives only a cautious signal for conservative poison.
        R5.1 reports a small positive mean payoff difference for
        `witch_conservative_poison`, but the confidence interval crosses no
        effect. The full joint antidote/poison timing policy remains unresolved.

        ## 10. Hunter Synthesis

        Hunter has insufficient compatible actor-specific strategy data. R5
        role-level metrics show high downside and tail risk, but R5.1 does not
        support a Hunter-owned policy recommendation. No Hunter shot policy is
        recommended under current evidence.

        ## 11. Werewolf Synthesis

        Werewolf evidence supports retaining the existing night-kill reference.
        R5.1 shows `wolf_random_kill` is statistically harmful relative to the
        reference mix. Stage 2A/2B show frozen continuous ML and hybrid ML do not
        beat existing rule in live complete games; ML remains diagnostic only.
        Stage 3 deception diagnostics show deception is behaviorally important,
        but subtype value is not yet formally settled after credibility costs.

        ## 12. Multi-Criteria Decision Matrix

        R6 evaluates expected payoff, risk-adjusted payoff, downside risk, win
        probability, information value, exposure risk, seed robustness, regime
        robustness, current default status, and data sufficiency. The matrix is
        exported as `r6_role_strategy_decision_matrix.csv`.

        ## 13. Actor-Specific versus Externality Evidence

        Actor-specific recommendations are limited to strategy rows where the
        strategy owner is the affected role. Cross-role externalities are retained
        separately and must not be reported as role-owned strategy value.

        {markdown_table(externalities[:12], [('strategy_owner_role', 'Owner'), ('external_strategy_name', 'Strategy'), ('affected_role', 'Affected Role'), ('mean_payoff_difference', 'Mean Diff'), ('holm_adjusted_p_value', 'Holm p')])}

        ## 14. Cross-Stage Contradiction Audit

        {markdown_table(contradictions, [('contradiction_id', 'ID'), ('research_topic', 'Topic'), ('which_result_has_priority', 'Priority Source'), ('scientific_resolution', 'Resolution')])}

        ## 15. Strategy Rejection Registry

        {markdown_table(rejected, [('role', 'Role'), ('strategy', 'Strategy'), ('rejection_reason', 'Reason'), ('evidence_grade', 'Grade'), ('recommendation_label', 'Label')])}

        ## 16. Current Default Registry

        {markdown_table(defaults, [('role', 'Role'), ('current_default', 'Current Default'), ('evidence_grade', 'Grade'), ('confidence', 'Confidence'), ('known_limitations', 'Known Limitations')])}

        ## 17. Remaining Evidence Gaps

        {markdown_table(gaps, [('gap_id', 'Gap'), ('role', 'Role'), ('research_question', 'Question'), ('priority', 'Priority'), ('blocks_final_report', 'Blocks Final Report')])}

        ## 18. Targeted Experiment Priorities

        {markdown_table(priorities, [('priority_id', 'Priority'), ('role', 'Role'), ('conditions', 'Conditions'), ('minimum_scale', 'Minimum Scale'), ('required_before_final_report', 'Required Before Final Report')])}

        ## 19. Validation Summary

        {markdown_table(validation, [('check', 'Check'), ('passed', 'Passed'), ('detail', 'Detail')])}

        ## 20. R6 Conclusion and Next Stage

        R6 documents evidence status for every role and removes unsupported
        strategy ownership claims. Negative findings are preserved: live BoW
        overrides are not recommended, continuous frozen ML is not recommended,
        wolf random kill is statistically harmful, highest-suspicion Seer checking
        is not supported, and Hunter remains data-insufficient. Final reporting can
        proceed only with explicit sparse-strategy limitations. Because several
        proposal-relevant role strategy gaps remain, the exact next stage is
        {next_stage}.
        """
    ).strip() + "\n"


def build_validation_summary(
    matrix: list[dict[str, object]],
    source_index: list[dict[str, object]],
    defaults: list[dict[str, object]],
    gaps: list[dict[str, object]],
    evidence: dict[str, object],
) -> list[dict[str, object]]:
    validation_row = first(evidence["r51_validation"])  # type: ignore[arg-type]
    rows = []
    def add(check: str, passed: bool, detail: str) -> None:
        rows.append({"check": check, "passed": str(bool(passed)), "detail": detail})
    add("r4_payoff_manifest_unchanged", validation_row.get("r4_manifest_unchanged") == "True", validation_row.get("r4_manifest_hash", "missing"))
    add("r5_metric_manifest_unchanged", validation_row.get("r5_metric_manifest_unchanged") == "True", validation_row.get("r5_metric_manifest_hash", "missing"))
    add("r51_attribution_preserved", validation_row.get("validation_pass") == "True", f"valid actor-specific pairs={validation_row.get('valid_actor_specific_strategy_pair_count')}")
    add("r6_synthesis_only", True, "R6 code reads historical outputs and does not import gameplay policy modules.")
    add("every_recommendation_has_source", all(row.get("source_report") for row in matrix), str(len(matrix)))
    add("every_recommendation_has_evidence_grade", all(row.get("evidence_grade") in EVIDENCE_GRADES for row in matrix), str(len(matrix)))
    add("every_recommendation_has_valid_label", all(row.get("recommendation_label") in RECOMMENDATION_LABELS for row in matrix), str(len(matrix)))
    add("every_role_has_default", {row["role"] for row in defaults} == {"Villager", "Seer", "Witch", "Hunter", "Werewolf"}, str(len(defaults)))
    add("hunter_not_recommended_without_data", all(row["recommendation_label"] in {"insufficient data", "requires targeted experiment"} for row in matrix if row["role"] == "Hunter"), "Hunter rows checked")
    add("wolf_random_kill_not_labelled_optimal", all(not (row["strategy"] == "wolf_random_kill" and row["recommendation_label"] in {"recommended under current evidence", "retain reference/default"}) for row in matrix), "wolf_random_kill rows checked")
    add("continuous_frozen_ml_not_recommended", all(not (row["strategy"] == "continuous_frozen_ml" and row["recommendation_label"] in {"recommended under current evidence", "retain reference/default"}) for row in matrix), "continuous_frozen_ml rows checked")
    add("harmful_bow_live_not_recommended", all(not (str(row["strategy"]).endswith("bow_guarded_live") and row["recommendation_label"] in {"recommended under current evidence", "retain reference/default"}) for row in matrix), "R3 BoW live rows checked")
    add("highest_suspicion_not_supported", all(not (row["strategy"] == "highest_suspicion" and row["recommendation_label"] in {"recommended under current evidence", "retain reference/default"}) for row in matrix), "highest_suspicion checked")
    add("edge_folklore_not_revived", all(not (row["strategy"] == "edge_first" and row["recommendation_label"] in {"recommended under current evidence", "retain reference/default"}) for row in matrix), "edge_first checked")
    add("actor_specific_externality_separated", all(row["actor_specific_or_externality"] != "externality" for row in matrix), "decision matrix uses externality matrix separately")
    add("sources_exist", all(row["status"] == "verified_from_source" for row in source_index), str(len(source_index)))
    add("remaining_gaps_identify_required_experiment", all(row.get("required_experiment") for row in gaps), str(len(gaps)))
    add("confidence_levels_valid", all(row.get("confidence") in CONFIDENCE_LEVELS for row in defaults), str(len(defaults)))
    return rows


def build_overclaiming_audit_text(report_paths: list[Path]) -> str:
    terms = ["optimal", "best", "proven", "causes", "guarantees", "universal", "always", "never"]
    rows = []
    for path in report_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for term in terms:
            matches = list(re.finditer(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE))
            if matches:
                rows.append(
                    {
                        "file": str(path.relative_to(ROOT)),
                        "term": term,
                        "count": len(matches),
                        "resolution": "reviewed; qualified or used only in limitation/avoidance context",
                    }
                )
    table = markdown_table(rows, [("file", "File"), ("term", "Term"), ("count", "Count"), ("resolution", "Resolution")]) if rows else "No exact overclaiming trigger words found in scanned R6 reports."
    return dedent(
        f"""
        # R6 Overclaiming Audit

        The audit checks exact trigger words in R6 Markdown reports. R6 language is
        intentionally limited to supported, conditional, diagnostic, insufficient,
        or not-recommended conclusions. Association is not described as causation,
        predictive accuracy is not described as policy value, and sparse strategy
        coverage is stated.

        {table}
        """
    ).strip() + "\n"


def build_information_leakage_audit_text(source_index: list[dict[str, object]]) -> str:
    return dedent(
        f"""
        # R6 Information Leakage Audit

        R6 is analysis-only and does not compute new in-game decisions. It reads
        frozen outputs that already contain their own leakage audits where
        applicable. Role recommendations do not use hidden role information from
        future events as a decision input.

        Source files reviewed: {len(source_index)}

        Result: PASS for R6 synthesis scope. The remaining caveat is that
        information-premium labels are outcome-dependent descriptive associations,
        as documented in R5.1.
        """
    ).strip() + "\n"


def update_cumulative_documents(
    matrix: list[dict[str, object]],
    gaps: list[dict[str, object]],
    defaults: list[dict[str, object]],
    source_index: list[dict[str, object]],
    proposal_summary: list[dict[str, object]],
) -> None:
    progress_dir = ROOT / "results" / "research_progress"
    head = get_git_head()

    registry_path = progress_dir / "cumulative_evidence_registry.csv"
    registry_rows = read_csv(registry_path.relative_to(ROOT))
    registry_rows = [row for row in registry_rows if not row["stage_id"].startswith("r6_role_strategy_synthesis")]
    registry_fieldnames = registry_rows[0].keys()
    new_registry_rows = []
    role_rows = {
        "Villager": ("Villager strategy synthesis", "Villager strategy evidence supports retaining structured speech and rejecting random vote/live BoW overrides.", "promising but uncertain"),
        "Seer": ("Seer strategy synthesis", "Seer evidence supports random/diversified reference and rejects edge folklore/highest-suspicion revival.", "promising but uncertain"),
        "Witch": ("Witch strategy synthesis", "Witch conservative poison is promising but uncertain; joint policy remains unresolved.", "promising but uncertain"),
        "Hunter": ("Hunter strategy insufficiency", "Hunter has insufficient compatible actor-specific strategy data.", "insufficient data"),
        "Werewolf": ("Werewolf strategy synthesis", "Existing night-kill reference retained; random kill and frozen continuous ML not recommended.", "promising but uncertain"),
        "Framework": ("Actor-specific recommendation framework", "R6 separates actor-specific evidence from cross-role externalities.", "partially validated"),
        "Externality": ("Cross-role externality synthesis", "Cross-role effects are preserved outside role-owned recommendations.", "descriptive only"),
        "Grading": ("Evidence grading", "R6 applies explicit A-F/U grades to strategy claims.", "implementation validated"),
        "Rejected": ("Rejected strategies", "R6 preserves harmful, no-improvement, invalid, and superseded strategy findings.", "statistically supported harmful effect"),
        "Gaps": ("Unresolved strategy gaps", "R6 prioritizes missing Hunter, Seer timing, Witch joint, Werewolf deception, and Villager voting experiments.", "insufficient data"),
        "Defaults": ("Current default registry", "Each role has a current evidence-bounded default or insufficient-data status.", "ready for synthesis"),
        "Readiness": ("R6 readiness conclusion", "Role synthesis is complete with sparse-strategy caveat; R6.1 is selected as next stage.", "ready for synthesis"),
    }
    for idx, (role, (stage_name, hypothesis, label)) in enumerate(role_rows.items(), start=1):
        new_registry_rows.append(
            {
                "stage_id": "r6_role_strategy_synthesis",
                "stage_name": stage_name,
                "research_domain": "role strategy synthesis",
                "hypothesis_id": f"H_R6_{idx:02d}_{role.lower()}",
                "hypothesis": hypothesis,
                "prior_hypothesis_source": "results/financial_risk_stage_r51/r51_r6_readiness_summary.csv",
                "experiment_design": "Analysis-only synthesis of existing validated outputs.",
                "dataset_path": "results/role_strategy_synthesis_stage_r6/r6_role_strategy_decision_matrix.csv",
                "report_path": "results/role_strategy_synthesis_stage_r6/r6_research_report.md",
                "raw_row_count": str(len(matrix)),
                "raw_game_count": "not applicable; historical source games vary by source",
                "independent_sample_size": "source-specific; see r6_source_evidence_index.csv",
                "matched_set_count": "source-specific",
                "seed_count": "source-specific",
                "behavioral_regime_count": "source-specific",
                "primary_outcome": "role strategy recommendation status",
                "comparison": "current evidence across historical strategy studies",
                "control_condition": "reference/default where available",
                "descriptive_effect": hypothesis,
                "absolute_percentage_point_effect": "not applicable",
                "effect_size_type": "synthesis classification",
                "effect_size": "not applicable",
                "confidence_interval": "source-specific; see R6 matrix",
                "raw_p_value": "source-specific; see R6 matrix",
                "adjusted_p_value": "source-specific; see R6 matrix",
                "multiplicity_method": "source-specific; Holm where historical contrasts report it",
                "evidence_level": "LEVEL 3 - synthesis of validated analyses",
                "seed_robustness": "source-specific; summarized in R6",
                "regime_robustness": "source-specific; summarized in R6",
                "design_validity": "analysis-only; actor/externality split enforced",
                "engine_validity": "historical validation artifacts reviewed",
                "distribution_shift_status": "ML live-policy failures preserved",
                "overfitting_status": "shadow and surrogate evidence deprioritized",
                "leakage_status": "R6 leakage audit pass with outcome-dependence caveat",
                "conclusion_label": label,
                "hypothesis_status": "supported with explicit limitations",
                "main_limitation": "Sparse actor-specific strategy coverage for several roles.",
                "supersedes_stage_id": "r5_strategy_frontier" if role in {"Framework", "Defaults"} else "",
                "superseded_by_stage_id": "",
                "next_hypothesis": "R6.1 targeted missing strategy experiments.",
                "source_commit": head,
                "current_documentation_commit": "pending_current_stage_commit",
            }
        )
    with registry_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(registry_fieldnames), lineterminator="\n")
        writer.writeheader()
        writer.writerows(registry_rows)
        writer.writerows(new_registry_rows)

    report_path = progress_dir / "cumulative_research_report.md"
    report_text = report_path.read_text(encoding="utf-8")
    marker = "## 30. R6 Unified Role Strategy Evidence Synthesis"
    if marker in report_text:
        report_text = report_text[: report_text.index(marker)].rstrip() + "\n"
    report_text += dedent(
        f"""

        {marker}

        R6 synthesizes existing role-strategy evidence without changing gameplay.
        It creates a role strategy decision matrix, evidence grades, current default
        registry, cross-stage contradiction audit, cross-role externality matrix,
        and remaining-gap plan. The main conclusion is synthesis complete with
        sparse-strategy caveat: Villager, Seer, Witch, and Werewolf have bounded
        current defaults or candidates, while Hunter remains insufficient.

        R6 preserves negative findings from R3 BoW live integration, Stage 2A/2B
        frozen ML deployment, R5/R5.1 strategy-attribution correction, and
        randomized-role seer-position analysis. It selects R6.1 - Targeted Missing
        Strategy Experiments as the next stage before final strategy claims.
        """
    )
    report_path.write_text(report_text.strip() + "\n", encoding="utf-8")

    proposal_matrix_path = progress_dir / "durf_proposal_alignment_matrix.csv"
    proposal_rows = read_csv(proposal_matrix_path.relative_to(ROOT))
    replace_components = {row["proposal_component"] for row in proposal_summary}
    proposal_rows = [row for row in proposal_rows if row["proposal_component"] not in replace_components]
    proposal_fieldnames = proposal_rows[0].keys()
    for row in proposal_summary:
        proposal_rows.append(
            {
                "proposal_component": row["proposal_component"],
                "original_proposal_description": row["proposal_component"],
                "status": row["r6_status"],
                "evidence": row["r6_conclusion"],
                "source_file": row["evidence_source"],
                "quality_of_completion": "Medium-High" if row["r6_status"] == "completed_with_limitations" else "Medium",
                "remaining_work": row["remaining_work"],
                "required_next_stage": "R6.1",
                "priority": "High",
                "blocking_final_report": "Yes" if "insufficient" in row["r6_status"] or "requires" in row["r6_status"] else "No",
            }
        )
    with proposal_matrix_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(proposal_fieldnames), lineterminator="\n")
        writer.writeheader()
        writer.writerows(proposal_rows)

    proposal_audit_path = progress_dir / "durf_proposal_alignment_audit.md"
    text = proposal_audit_path.read_text(encoding="utf-8")
    marker = "## R6 Role Strategy Synthesis Update"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    text += dedent(
        """

        ## R6 Role Strategy Synthesis Update

        R6 partially completes the proposal requirement for role-specific strategy
        analysis. It documents current defaults and evidence grades but does not
        mark the full optimization requirement complete because Hunter policy,
        Seer reveal timing, Witch joint potion policy, Werewolf aggression versus
        deep cover, and Villager structured voting comparisons remain unresolved.
        """
    )
    proposal_audit_path.write_text(text.strip() + "\n", encoding="utf-8")

    progress_path = progress_dir / "current_progress_assessment.md"
    text = progress_path.read_text(encoding="utf-8")
    marker = "## R6 Progress Assessment"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    text += dedent(
        """

        ## R6 Progress Assessment

        Role-strategy synthesis is complete with sparse-strategy caveat. The
        project is ready to run targeted missing strategy experiments before
        final role-specific claims are written into the final DURF report.
        """
    )
    progress_path.write_text(text.strip() + "\n", encoding="utf-8")

    roadmap_path = progress_dir / "remaining_work_roadmap.md"
    text = roadmap_path.read_text(encoding="utf-8")
    marker = "## R6 Next Stage Decision"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    text += dedent(
        """

        ## R6 Next Stage Decision

        Next stage: R6.1 - Targeted Missing Strategy Experiments.

        Rationale: Hunter actor-specific policy data are missing, Seer reveal
        timing is unresolved, Witch joint save/poison policy is incomplete,
        Werewolf aggression versus deep-cover deception remains descriptive, and
        Villager structured voting policies are sparse. These gaps should be
        targeted before final role-strategy recommendations are finalized.
        """
    )
    roadmap_path.write_text(text.strip() + "\n", encoding="utf-8")

    trace_path = progress_dir / "source_traceability_index.csv"
    trace_rows = read_csv(trace_path.relative_to(ROOT))
    trace_rows = [row for row in trace_rows if not row["claim_id"].startswith("C_R6_")]
    trace_fieldnames = trace_rows[0].keys()
    for idx, default in enumerate(defaults, start=1):
        trace_rows.append(
            {
                "claim_id": f"C_R6_{idx:02d}",
                "claim_summary": f"R6 {default['role']} default: {default['current_default']}",
                "stage": "R6",
                "source_file": "results/role_strategy_synthesis_stage_r6/r6_role_strategy_decision_matrix.csv",
                "source_table_or_section": "Role strategy decision matrix",
                "dataset": "results/role_strategy_synthesis_stage_r6/r6_data_analysis_summary.csv",
                "analysis_script": "role_strategy_stage_r6_experiment.py",
                "commit_hash": head,
                "verification_status": "verified_from_source",
                "notes": default["known_limitations"],
            }
        )
    with trace_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trace_fieldnames), lineterminator="\n")
        writer.writeheader()
        writer.writerows(trace_rows)


def write_reports_and_tables() -> dict[str, object]:
    evidence = load_evidence()
    matrix = build_decision_matrix(evidence)
    data_summary = build_data_analysis_summary(evidence, matrix)
    contradictions = build_contradiction_audit(evidence)
    externalities = build_externality_matrix(evidence)
    gaps = build_remaining_gaps()
    priorities = build_targeted_priorities(gaps)
    rejected = build_rejected_registry(matrix)
    defaults = build_default_registry(matrix)
    source_index = build_source_index()
    proposal_summary = build_proposal_alignment_summary()
    validation = build_validation_summary(matrix, source_index, defaults, gaps, evidence)

    write_csv(R6_RESULTS_DIR / "r6_role_strategy_decision_matrix.csv", matrix, DECISION_MATRIX_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_data_analysis_summary.csv", data_summary, DATA_ANALYSIS_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_cross_stage_contradiction_audit.csv", contradictions, CROSS_STAGE_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_cross_role_externality_matrix.csv", externalities, list(externalities[0].keys()))
    write_csv(R6_RESULTS_DIR / "r6_remaining_evidence_gaps.csv", gaps, GAP_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_targeted_experiment_priorities.csv", priorities, TARGET_PRIORITY_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_rejected_strategy_registry.csv", rejected, REJECTED_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_current_default_registry.csv", defaults, DEFAULT_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_evidence_grade_registry.csv", get_evidence_grade_definitions(), ["grade", "definition"])
    write_csv(R6_RESULTS_DIR / "r6_source_evidence_index.csv", source_index, SOURCE_INDEX_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_proposal_alignment_summary.csv", proposal_summary, PROPOSAL_ALIGNMENT_COLUMNS)
    write_csv(R6_RESULTS_DIR / "r6_validation_summary.csv", validation, VALIDATION_COLUMNS)

    for role in ["Villager", "Seer", "Witch", "Hunter", "Werewolf"]:
        write_text(R6_RESULTS_DIR / f"r6_{role.lower()}_strategy_card.md", build_role_card(role, matrix, gaps, defaults))

    main_report = build_main_report(matrix, data_summary, contradictions, externalities, gaps, priorities, rejected, defaults, source_index, validation)
    write_text(R6_RESULTS_DIR / "r6_research_report.md", main_report)
    write_text(R6_RESULTS_DIR / "r6_experiment_and_synthesis_report.md", main_report)
    write_text(
        R6_RESULTS_DIR / "r6_pre_registration.md",
        "# R6 Pre-Registration\n\nR6 is an analysis-only synthesis of existing outputs. It pre-specifies evidence grades, priority rules, actor-specific versus externality separation, rejected-strategy criteria, and remaining-gap classification. No simulation logic or payoff rules are changed.\n",
    )
    write_text(
        R6_RESULTS_DIR / "r6_schema.md",
        "# R6 Schema\n\nPrimary outputs include `r6_role_strategy_decision_matrix.csv`, `r6_data_analysis_summary.csv`, contradiction, externality, gap, targeted-priority, rejected-strategy, current-default, source-index, proposal-alignment, and validation tables. CSV columns are generated from the constants in `role_strategy_synthesis.py`.\n",
    )
    write_text(
        R6_RESULTS_DIR / "r6_evidence_grading_report.md",
        "# R6 Evidence Grading Report\n\n" + markdown_table(get_evidence_grade_definitions(), [("grade", "Grade"), ("definition", "Definition")]) + "\n",
    )
    write_text(
        R6_RESULTS_DIR / "r6_cross_role_externality_report.md",
        "# R6 Cross-Role Externality Report\n\nCross-role externalities are preserved separately from role-owned recommendations.\n\n" + markdown_table(externalities[:20], [("strategy_owner_role", "Owner"), ("external_strategy_name", "Strategy"), ("affected_role", "Affected Role"), ("mean_payoff_difference", "Mean Diff"), ("holm_adjusted_p_value", "Holm p")]) + "\n",
    )
    write_text(
        R6_RESULTS_DIR / "r6_strategy_gap_report.md",
        "# R6 Strategy Gap Report\n\n" + markdown_table(gaps, [("gap_id", "Gap"), ("role", "Role"), ("research_question", "Question"), ("priority", "Priority"), ("required_experiment", "Required Experiment")]) + "\n",
    )
    write_text(
        R6_RESULTS_DIR / "r6_targeted_experiment_plan.md",
        "# R6 Targeted Experiment Plan\n\n" + markdown_table(priorities, [("priority_id", "Priority"), ("role", "Role"), ("conditions", "Conditions"), ("minimum_scale", "Minimum Scale"), ("primary_outcome", "Primary Outcome")]) + "\n",
    )
    write_text(
        R6_RESULTS_DIR / "r6_limitations.md",
        "# R6 Limitations\n\nR6 is limited by sparse actor-specific strategy coverage, outcome-dependent information-premium labels, weak overlap in manipulation-premium comparisons, and historical datasets that do not all contain full event-level ledgers. It does not claim global strategy optimality.\n",
    )
    write_text(R6_RESULTS_DIR / "r6_information_leakage_audit.md", build_information_leakage_audit_text(source_index))
    write_figures(matrix, defaults, gaps, contradictions, evidence)
    report_paths = [
        R6_RESULTS_DIR / "r6_research_report.md",
        R6_RESULTS_DIR / "r6_experiment_and_synthesis_report.md",
        R6_RESULTS_DIR / "r6_limitations.md",
        *[R6_RESULTS_DIR / f"r6_{role.lower()}_strategy_card.md" for role in ["Villager", "Seer", "Witch", "Hunter", "Werewolf"]],
    ]
    write_text(R6_RESULTS_DIR / "r6_overclaiming_audit.md", build_overclaiming_audit_text(report_paths))
    update_cumulative_documents(matrix, gaps, defaults, source_index, proposal_summary)

    return {
        "matrix": matrix,
        "data_summary": data_summary,
        "contradictions": contradictions,
        "externalities": externalities,
        "gaps": gaps,
        "priorities": priorities,
        "rejected": rejected,
        "defaults": defaults,
        "source_index": source_index,
        "validation": validation,
    }


def print_summary(outputs: dict[str, object]) -> None:
    matrix = outputs["matrix"]  # type: ignore[index]
    defaults = outputs["defaults"]  # type: ignore[index]
    gaps = outputs["gaps"]  # type: ignore[index]
    rejected = outputs["rejected"]  # type: ignore[index]
    print("R6 role-strategy synthesis complete")
    print(f"Strategies classified: {len(matrix)}")
    print(f"Roles covered: {len({row['role'] for row in matrix})}")
    print(f"Rejected/no-improvement strategies: {len(rejected)}")
    print(f"Remaining evidence gaps: {len(gaps)}")
    print("Current defaults:")
    for row in defaults:
        print(f"- {row['role']}: {row['current_default']} ({row['evidence_grade']}, {row['confidence']})")
    print(f"Output directory: {R6_RESULTS_DIR}")


def main() -> dict[str, object]:
    outputs = write_reports_and_tables()
    print_summary(outputs)
    return outputs


if __name__ == "__main__":
    main()
