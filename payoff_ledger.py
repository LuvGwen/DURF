"""R4 event-level payoff ledger."""

from __future__ import annotations

from collections import defaultdict

from payoff_events import PayoffEvent


class PayoffLedger:
    def __init__(self, manifest, game_id, matched_set_id="", seed=""):
        self.manifest = manifest
        self.game_id = str(game_id)
        self.matched_set_id = str(matched_set_id or "")
        self.seed = seed
        self.events = []
        self._component_lookup = {
            item["component_id"]: item
            for item in manifest["payoff_components"]
        }

    def component(self, component_id):
        try:
            return self._component_lookup[component_id]
        except KeyError as exc:
            raise ValueError(f"Unknown payoff component: {component_id}") from exc

    def add(
        self,
        component_id,
        actor,
        round_number,
        phase,
        source_action_id,
        explanation,
        target=None,
        event_type="payoff",
        event_subtype="",
        multiplier=1.0,
        order_index=None,
        evaluator_only_fields=None,
        calculation_specification="core",
    ):
        component = self.component(component_id)
        if actor.role not in component["role_scope"]:
            raise ValueError(
                f"Role {actor.role} cannot receive {component_id}"
            )
        if order_index is None:
            order_index = len(self.events)
        final_value = float(component["base_value"]) * float(multiplier)
        event = PayoffEvent(
            payoff_event_id=(
                f"{self.game_id}__{calculation_specification}__"
                f"{len(self.events) + 1:06d}"
            ),
            game_id=self.game_id,
            matched_set_id=self.matched_set_id,
            seed=self.seed,
            round=round_number,
            phase=phase,
            actor_uid=actor.player_id,
            actor_role=actor.role,
            actor_team=actor.team,
            target_uid=getattr(target, "player_id", ""),
            target_role=getattr(target, "role", ""),
            event_type=event_type,
            event_subtype=event_subtype or component_id,
            payoff_component=component_id,
            calculation_specification=calculation_specification,
            specification=component["specification"],
            component_category=component["component_category"],
            team_or_individual=component["team_or_individual"],
            immediate_or_terminal=component["immediate_or_terminal"],
            base_value=float(component["base_value"]),
            multiplier=float(multiplier),
            final_value=final_value,
            manifest_version=self.manifest["manifest_version"],
            manifest_hash=self.manifest["manifest_hash"],
            source_action_id=str(source_action_id),
            explanation=explanation,
            order_index=order_index,
            evaluator_only_fields=";".join(evaluator_only_fields or []),
        )
        self.events.append(event)
        return event

    def rows(self):
        return [event.to_dict() for event in self.events]

    def totals_by_player(self):
        totals = defaultdict(float)
        for event in self.events:
            totals[event.actor_uid] += event.final_value
        return dict(totals)

    def totals_by_player_and_category(self):
        totals = defaultdict(lambda: defaultdict(float))
        for event in self.events:
            totals[event.actor_uid][event.component_category] += event.final_value
        return totals

    def validate_unique_ids(self):
        ids = [event.payoff_event_id for event in self.events]
        return len(ids) == len(set(ids))

    def duplicate_component_sources(self):
        counts = defaultdict(int)
        for event in self.events:
            key = (
                event.actor_uid,
                event.payoff_component,
                event.source_action_id,
                event.specification,
            )
            counts[key] += 1
        return {key: count for key, count in counts.items() if count > 1}
