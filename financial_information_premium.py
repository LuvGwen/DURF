"""Information-premium analogues for R5."""

from __future__ import annotations

from financial_risk_metrics import mean


INFORMATION_COMPONENTS = {
    "seer_information_leads_to_wolf_elimination",
    "seer_investigation_used",
}


def useful_information_game_ids(event_rows):
    return {
        row["game_id"]
        for row in event_rows
        if row.get("payoff_component") == "seer_information_leads_to_wolf_elimination"
    }


def seer_check_wolf_game_ids(event_rows):
    return {
        row["game_id"]
        for row in event_rows
        if row.get("payoff_component") == "seer_investigation_used"
        and row.get("target_role") == "werewolf"
    }


def premium_difference(player_rows, flagged_game_ids, role="seer", payoff_field="total_payoff"):
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
