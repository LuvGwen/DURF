"""Historical compatibility inventory for R4 payoff recalculation."""

from __future__ import annotations

import csv
from pathlib import Path


HISTORICAL_SOURCES = [
    (
        "low-information baseline",
        "results/ablation_results.csv",
        ["winner", "round_number"],
        "partially recalculable",
        "No player-level event ledger.",
    ),
    (
        "speech/herding ablation",
        "results/ablation_results.csv",
        ["winner", "round_number"],
        "partially recalculable",
        "Aggregated rows lack event-level speech and vote identities.",
    ),
    (
        "witch threshold",
        "simulation.py output",
        ["num_witch_saves", "num_witch_poison"],
        "requires raw-event regeneration",
        "Console summaries are insufficient for R4 event attribution.",
    ),
    (
        "hunter action",
        "results/ablation_results.csv",
        ["total_hunter_shots"],
        "partially recalculable",
        "Hunter event targets are not preserved in aggregate ablation rows.",
    ),
    (
        "wolf strategy",
        "results/wolf_strategy_results.csv",
        ["wolf_win_rate", "village_win_rate"],
        "partially recalculable",
        "Strategy outcomes exist, but night-kill target roles are absent.",
    ),
    (
        "deception",
        "wolf_deception_experiment.py output",
        ["total_wolf_deceptions"],
        "requires raw-event regeneration",
        "No committed event-level deception ledger for every game.",
    ),
    (
        "risk preference",
        "results/ten_player_risk_preference_multi_seed_raw.csv",
        ["avg_payoff", "total_votes", "credibility_cost_events"],
        "partially recalculable",
        "Contains aggregate payoff/risk fields but not full action events.",
    ),
    (
        "seer position",
        "results/ten_player_seer_position_randomized_roles_game_level_raw.csv",
        ["winner", "first_check_found_wolf"],
        "partially recalculable",
        "Game-level seer fields exist; player event ledger is absent.",
    ),
    (
        "structured seer search",
        "results/structured_seer_search/structured_seer_search_game_level_raw.csv",
        ["winner", "wolves_discovered"],
        "partially recalculable",
        "Search path metrics exist, but non-seer event ledger is absent.",
    ),
    (
        "BoW R3 live",
        "results/bow_integration_stage_r3/r3_live_game_level_raw.csv",
        ["winner", "num_r3_vote_decisions"],
        "partially recalculable",
        "R3 raw has vote/belief rows but not complete role-action death ledger.",
    ),
]


def row_count(path):
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def header_fields(path):
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            return set(next(reader))
        except StopIteration:
            return set()


def build_historical_recalculation_coverage(root=Path(".")):
    rows = []
    for stage, source, required, status, notes in HISTORICAL_SOURCES:
        path = root / source
        fields = header_fields(path)
        present = [field for field in required if field in fields]
        missing = [field for field in required if field not in fields]
        source_exists = path.exists()
        if source.endswith(".csv") and source_exists:
            raw_count = row_count(path)
        else:
            raw_count = 0
        rows.append({
            "stage": stage,
            "source_dataset": source,
            "raw_game_count": raw_count,
            "required_fields_present": ";".join(present),
            "recalculation_status": status if source_exists else "not recalculable",
            "missing_fields": ";".join(missing),
            "core_payoff_available": str(status == "fully recalculable"),
            "extended_payoff_available": str(False),
            "regeneration_required": str(
                status == "requires raw-event regeneration"
                or status != "fully recalculable"
            ),
            "notes": notes if source_exists or not source.endswith(".csv") else "Source file missing.",
        })
    return rows


def build_historical_recalculated_payoffs(coverage_rows):
    rows = []
    for row in coverage_rows:
        rows.append({
            "stage": row["stage"],
            "source_dataset": row["source_dataset"],
            "recalculation_status": row["recalculation_status"],
            "calculation_specification": "core",
            "role": "all",
            "mean_total_payoff": "NA",
            "event_rows_reconstructed": 0,
            "notes": (
                "R4 does not invent missing event rows; historical sources "
                "are coverage-classified unless raw event logs are sufficient."
            ),
        })
    return rows


if __name__ == "__main__":
    for item in build_historical_recalculation_coverage():
        print(item)
