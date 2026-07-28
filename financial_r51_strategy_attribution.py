"""Strategy ownership definitions for the R5.1 attribution audit."""

from __future__ import annotations

from pathlib import Path


RESULTS_DIR = Path("results/financial_risk_stage_r51")
R4_DIR = Path("results/payoff_matrix_stage_r4")
R5_DIR = Path("results/financial_risk_stage_r5")
RESEARCH_DIR = Path("results/research_progress")

ROLE_ORDER = ["werewolf", "seer", "witch", "villager", "hunter"]
REFERENCE_CONDITION = "reference_strategy_mix"

STRATEGY_DEFINITIONS = {
    "reference_strategy_mix": {
        "strategy_id": "r51_reference_strategy_mix",
        "strategy_name": "reference_strategy_mix",
        "strategy_owner_role": "reference",
        "strategy_family": "reference",
        "valid_roles": ROLE_ORDER,
        "global_or_actor_specific": "reference_configuration",
        "source_stage": "R4",
        "source_code": "payoff_stage_r4_experiment.py",
        "source_dataset": "results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv",
        "core_payoff_compatible": True,
        "extended_payoff_compatible": True,
        "matched_comparison_available": True,
        "full_event_ledger_available": True,
        "primary_r51_eligible": False,
        "regeneration_required": False,
        "notes": "Baseline/mixed global configuration; not an actor-specific strategy.",
    },
    "villager_random_vote": {
        "strategy_id": "r51_villager_random_vote",
        "strategy_name": "villager_random_vote",
        "strategy_owner_role": "villager",
        "strategy_family": "voting",
        "valid_roles": ["villager"],
        "global_or_actor_specific": "actor_specific",
        "source_stage": "R4",
        "source_code": "payoff_stage_r4_experiment.py",
        "source_dataset": "results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv",
        "core_payoff_compatible": True,
        "extended_payoff_compatible": True,
        "matched_comparison_available": True,
        "full_event_ledger_available": True,
        "primary_r51_eligible": True,
        "regeneration_required": False,
        "notes": "Villager-owned voting-policy diagnostic condition.",
    },
    "seer_highest_suspicion": {
        "strategy_id": "r51_seer_highest_suspicion",
        "strategy_name": "seer_highest_suspicion",
        "strategy_owner_role": "seer",
        "strategy_family": "seer",
        "valid_roles": ["seer"],
        "global_or_actor_specific": "actor_specific",
        "source_stage": "R4",
        "source_code": "payoff_stage_r4_experiment.py",
        "source_dataset": "results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv",
        "core_payoff_compatible": True,
        "extended_payoff_compatible": True,
        "matched_comparison_available": True,
        "full_event_ledger_available": True,
        "primary_r51_eligible": True,
        "regeneration_required": False,
        "notes": "Seer-owned check-target policy diagnostic condition.",
    },
    "witch_conservative_poison": {
        "strategy_id": "r51_witch_conservative_poison",
        "strategy_name": "witch_conservative_poison",
        "strategy_owner_role": "witch",
        "strategy_family": "witch",
        "valid_roles": ["witch"],
        "global_or_actor_specific": "actor_specific",
        "source_stage": "R4",
        "source_code": "payoff_stage_r4_experiment.py",
        "source_dataset": "results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv",
        "core_payoff_compatible": True,
        "extended_payoff_compatible": True,
        "matched_comparison_available": True,
        "full_event_ledger_available": True,
        "primary_r51_eligible": True,
        "regeneration_required": False,
        "notes": "Witch-owned poison-threshold diagnostic condition.",
    },
    "wolf_random_kill": {
        "strategy_id": "r51_wolf_random_kill",
        "strategy_name": "wolf_random_kill",
        "strategy_owner_role": "werewolf",
        "strategy_family": "wolf",
        "valid_roles": ["werewolf"],
        "global_or_actor_specific": "actor_specific",
        "source_stage": "R4",
        "source_code": "payoff_stage_r4_experiment.py",
        "source_dataset": "results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv",
        "core_payoff_compatible": True,
        "extended_payoff_compatible": True,
        "matched_comparison_available": True,
        "full_event_ledger_available": True,
        "primary_r51_eligible": True,
        "regeneration_required": False,
        "notes": "Werewolf-owned night-kill diagnostic condition.",
    },
}


def strategy_definition(strategy_name: str) -> dict[str, object]:
    """Return metadata for an R4/R5 condition label."""
    try:
        return STRATEGY_DEFINITIONS[strategy_name]
    except KeyError as exc:
        raise ValueError(f"Unknown strategy condition: {strategy_name}") from exc


def is_reference_configuration(strategy_name: str) -> bool:
    return strategy_name == REFERENCE_CONDITION


def strategy_owner_role(strategy_name: str) -> str:
    return str(strategy_definition(strategy_name)["strategy_owner_role"])


def is_actor_specific_for_role(strategy_name: str, affected_role: str) -> bool:
    definition = strategy_definition(strategy_name)
    return (
        not is_reference_configuration(strategy_name)
        and definition["strategy_owner_role"] == affected_role
        and affected_role in definition["valid_roles"]
    )


def is_external_for_role(strategy_name: str, affected_role: str) -> bool:
    owner = strategy_owner_role(strategy_name)
    return not is_reference_configuration(strategy_name) and owner != affected_role


def strategy_mapping_type(strategy_name: str, affected_role: str) -> str:
    if is_actor_specific_for_role(strategy_name, affected_role):
        return "actor_specific_strategy"
    if is_reference_configuration(strategy_name):
        return "global_game_configuration"
    if is_external_for_role(strategy_name, affected_role):
        return "cross_role_externality"
    return "invalid_result"


def audit_status_for(strategy_name: str, affected_role: str) -> str:
    mapping_type = strategy_mapping_type(strategy_name, affected_role)
    if mapping_type == "actor_specific_strategy":
        return "valid_actor_specific"
    if mapping_type == "global_game_configuration":
        return "valid_global_configuration"
    if mapping_type == "cross_role_externality":
        return "valid_cross_role_externality"
    return "invalid_mapping"


def corrected_strategy_registry_rows() -> list[dict[str, object]]:
    rows = []
    for definition in STRATEGY_DEFINITIONS.values():
        row = dict(definition)
        row["valid_roles"] = ";".join(definition["valid_roles"])
        rows.append(row)
    return rows


def attribution_registry_rows() -> list[dict[str, object]]:
    rows = []
    for strategy_name, definition in STRATEGY_DEFINITIONS.items():
        for affected_role in ROLE_ORDER:
            actor_specific = is_actor_specific_for_role(strategy_name, affected_role)
            reference = is_reference_configuration(strategy_name)
            external = is_external_for_role(strategy_name, affected_role)
            rows.append({
                "strategy_id": definition["strategy_id"],
                "strategy_name": strategy_name,
                "strategy_owner_role": definition["strategy_owner_role"],
                "affected_role": affected_role,
                "actor_specific_strategy": actor_specific,
                "global_game_configuration": reference,
                "external_strategy": external,
                "reference_configuration": reference,
                "applicable_roles": ";".join(definition["valid_roles"]),
                "directly_controlled_by_affected_role": actor_specific,
                "data_source": definition["source_dataset"],
                "matched_design_available": definition["matched_comparison_available"],
                "event_level_coverage": definition["full_event_ledger_available"],
                "primary_analysis_eligible": actor_specific,
                "notes": (
                    "Valid direct strategy for affected role."
                    if actor_specific else
                    "Reference configuration, not an actor-owned strategy."
                    if reference else
                    "Valid cross-role externality, not an actor-specific recommendation."
                    if external else
                    "Invalid or unknown mapping."
                ),
            })
    return rows
