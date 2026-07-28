"""Event objects used by the R4 payoff ledger."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class PayoffEvent:
    payoff_event_id: str
    game_id: str
    matched_set_id: str
    seed: int | str
    round: int
    phase: str
    actor_uid: int | str
    actor_role: str
    actor_team: str
    target_uid: int | str
    target_role: str
    event_type: str
    event_subtype: str
    payoff_component: str
    calculation_specification: str
    specification: str
    component_category: str
    team_or_individual: str
    immediate_or_terminal: str
    base_value: float
    multiplier: float
    final_value: float
    manifest_version: str
    manifest_hash: str
    source_action_id: str
    explanation: str
    order_index: int
    evaluator_only_fields: str
    validation_status: str = "PASS"

    def to_dict(self):
        row = asdict(self)
        row["base_value"] = f"{self.base_value:.10f}"
        row["multiplier"] = f"{self.multiplier:.10f}"
        row["final_value"] = f"{self.final_value:.10f}"
        return row
