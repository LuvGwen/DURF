"""Manipulation-premium analogues for R5."""

from __future__ import annotations

from financial_risk_metrics import mean


MANIPULATION_COMPONENTS = {
    "successful_deception",
    "wolf_villager_voted_out_shared",
    "wolf_special_killed_shared",
}


def manipulation_game_ids(event_rows):
    return {
        row["game_id"]
        for row in event_rows
        if row.get("payoff_component") in MANIPULATION_COMPONENTS
    }


def premium_difference(player_rows, flagged_game_ids, role="werewolf", payoff_field="total_payoff"):
    with_event = [
        float(row[payoff_field])
        for row in player_rows
        if row.get("role") == role and row.get("game_id") in flagged_game_ids
    ]
    without_event = [
        float(row[payoff_field])
        for row in player_rows
        if row.get("role") == role and row.get("game_id") not in flagged_game_ids
    ]
    return {
        "with_event_observations": len(with_event),
        "without_event_observations": len(without_event),
        "mean_with_event": mean(with_event),
        "mean_without_event": mean(without_event),
        "premium": (
            mean(with_event) - mean(without_event)
            if with_event and without_event
            else None
        ),
    }
