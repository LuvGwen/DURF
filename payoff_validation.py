"""Validation helpers for the R4 payoff manifest and ledger."""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from payoff_manifest import build_manifest, component_lookup, manifest_hash


def validate_manifest(manifest=None):
    manifest = manifest or build_manifest()
    recomputed = manifest_hash(manifest)
    return {
        "manifest_version_present": bool(manifest.get("manifest_version")),
        "manifest_hash_stable": recomputed == manifest.get("manifest_hash"),
        "component_count": len(manifest.get("payoff_components", [])),
        "proposal_reference_count": len(manifest.get("proposal_reference", [])),
    }


def validate_event_rows(event_rows, manifest=None):
    manifest = manifest or build_manifest()
    components = component_lookup(manifest)
    ids = [row["payoff_event_id"] for row in event_rows]
    source_keys = [
        (
            row["actor_uid"],
            row["payoff_component"],
            row["source_action_id"],
            row["calculation_specification"],
        )
        for row in event_rows
    ]
    duplicate_source_keys = [
        key for key, count in Counter(source_keys).items()
        if count > 1
    ]
    invalid_role_pairs = []
    wrong_values = []
    for row in event_rows:
        component = components.get(row["payoff_component"])
        if component is None:
            invalid_role_pairs.append(row["payoff_event_id"])
            continue
        if row["actor_role"] not in component["role_scope"]:
            invalid_role_pairs.append(row["payoff_event_id"])
        expected = float(component["base_value"]) * float(row["multiplier"])
        if not math.isclose(expected, float(row["final_value"]), abs_tol=1e-9):
            wrong_values.append(row["payoff_event_id"])

    terminal_counts = Counter(
        (row["game_id"], row["actor_uid"], row["calculation_specification"])
        for row in event_rows
        if row["event_type"] == "terminal_result"
    )
    bad_terminal = [key for key, count in terminal_counts.items() if count != 1]

    return {
        "event_count": len(event_rows),
        "unique_event_ids": len(ids) == len(set(ids)),
        "duplicate_source_action_rewards": len(duplicate_source_keys),
        "invalid_role_event_pairs": len(invalid_role_pairs),
        "wrong_manifest_values": len(wrong_values),
        "terminal_payoff_once_per_player": len(bad_terminal) == 0,
    }


def validate_player_reconciliation(player_rows, event_rows):
    event_totals = defaultdict(float)
    category_totals = defaultdict(lambda: defaultdict(float))
    for row in event_rows:
        key = (
            row["game_id"],
            str(row["actor_uid"]),
            row["calculation_specification"],
        )
        value = float(row["final_value"])
        event_totals[key] += value
        category_totals[key][row["component_category"]] += value

    mismatches = []
    category_mismatches = []
    for row in player_rows:
        key = (
            row["game_id"],
            str(row["player_id"]),
            row["calculation_specification"],
        )
        total = float(row["total_payoff"])
        if not math.isclose(total, event_totals.get(key, 0.0), abs_tol=1e-9):
            mismatches.append(key)
        summed_categories = (
            float(row["terminal_team_payoff"])
            + float(row["individual_action_payoff"])
            + float(row["shared_wolf_team_bonus"])
            + float(row["survival_or_exposure_payoff"])
            + float(row["opportunity_cost"])
        )
        if not math.isclose(total, summed_categories, abs_tol=1e-9):
            category_mismatches.append(key)

    return {
        "player_rows": len(player_rows),
        "player_total_mismatches": len(mismatches),
        "player_category_mismatches": len(category_mismatches),
        "player_reconciliation_pass": (
            not mismatches and not category_mismatches
        ),
    }


def validate_game_reconciliation(game_rows, player_rows):
    player_totals = defaultdict(float)
    for row in player_rows:
        key = (row["game_id"], row["calculation_specification"])
        player_totals[key] += float(row["total_payoff"])

    mismatches = []
    for row in game_rows:
        key = (row["game_id"], row["calculation_specification"])
        if not math.isclose(
            float(row["total_game_payoff"]),
            player_totals.get(key, 0.0),
            abs_tol=1e-9,
        ):
            mismatches.append(key)

    return {
        "game_rows": len(game_rows),
        "game_total_mismatches": len(mismatches),
        "game_reconciliation_pass": not mismatches,
    }


def build_validation_summary(game_rows, player_rows, event_rows, manifest=None):
    manifest = manifest or build_manifest()
    summary = {}
    summary.update(validate_manifest(manifest))
    summary.update(validate_event_rows(event_rows, manifest))
    summary.update(validate_player_reconciliation(player_rows, event_rows))
    summary.update(validate_game_reconciliation(game_rows, player_rows))
    summary["validation_pass"] = all(
        [
            summary["manifest_hash_stable"],
            summary["unique_event_ids"],
            summary["duplicate_source_action_rewards"] == 0,
            summary["invalid_role_event_pairs"] == 0,
            summary["wrong_manifest_values"] == 0,
            summary["terminal_payoff_once_per_player"],
            summary["player_reconciliation_pass"],
            summary["game_reconciliation_pass"],
        ]
    )
    return summary


if __name__ == "__main__":
    print(validate_manifest())
