"""Versioned payoff manifest for R4 role-specific payoff accounting."""

from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH


MANIFEST_VERSION = "r4_payoff_manifest_v1"
RESULTS_DIR = Path("results/payoff_matrix_stage_r4")


PROPOSAL_REFERENCE = [
    (VILLAGER, "team_win", 1.0, "Village team victory."),
    (VILLAGER, "wrongly_eliminated", -0.5, "Cost of being wrongly eliminated."),
    (SEER, "team_win", 1.2, "Village team victory with seer role premium."),
    (SEER, "investigation_used", 0.2, "Each legal investigation."),
    (
        SEER,
        "information_leads_to_wolf_elimination",
        0.3,
        "Checked information contributing to wolf elimination.",
    ),
    (SEER, "high_mortality_exposure_risk", -0.8, "Exposure or mortality risk."),
    (WITCH, "team_win", 1.2, "Village team victory with witch role premium."),
    (WITCH, "correct_poison", 0.4, "Poisoning a werewolf."),
    (WITCH, "correct_save", 0.3, "Saving a village-team night target."),
    (WITCH, "wasted_potion", -0.2, "Using a potion without useful effect."),
    (WITCH, "poison_villager", -0.5, "Poisoning a village-team player."),
    (HUNTER, "team_win", 1.2, "Village team victory with hunter role premium."),
    (HUNTER, "correct_death_shot", 0.4, "Hunter death shot kills a wolf."),
    (HUNTER, "shoot_villager", -0.5, "Hunter death shot kills village team."),
    (WEREWOLF, "team_win", 1.5, "Wolf team victory."),
    (
        WEREWOLF,
        "special_killed",
        0.5,
        "Shared wolf bonus when a special village role is killed.",
    ),
    (
        WEREWOLF,
        "villager_voted_out",
        0.3,
        "Shared wolf bonus when a village-team player is voted out.",
    ),
]


def component(
    component_id,
    role_scope,
    value,
    category,
    team_or_individual,
    immediate_or_terminal,
    trigger,
    specification="core",
    proposal_component=None,
    exclusion_rules="Do not award when the source action is invalid.",
    double_counting_rules="Award at most once per source action and actor.",
    opportunity_cost_rules="Not an opportunity-cost component.",
    normalization_rules="No normalization unless multiplier is supplied.",
):
    return {
        "component_id": component_id,
        "role_scope": list(role_scope),
        "base_value": value,
        "component_category": category,
        "team_or_individual": team_or_individual,
        "immediate_or_terminal": immediate_or_terminal,
        "trigger_definition": trigger,
        "specification": specification,
        "proposal_component": proposal_component or "",
        "exclusion_rules": exclusion_rules,
        "double_counting_rules": double_counting_rules,
        "opportunity_cost_rules": opportunity_cost_rules,
        "normalization_rules": normalization_rules,
    }


PAYOFF_COMPONENTS = [
    component(
        "villager_team_win",
        [VILLAGER],
        1.0,
        "terminal_team_payoff",
        "team",
        "terminal",
        "Villager role is on the winning village team.",
        proposal_component="Villager team win",
    ),
    component(
        "villager_team_loss",
        [VILLAGER],
        -1.0,
        "terminal_team_payoff",
        "team",
        "terminal",
        "Villager role is on the losing village team.",
        proposal_component="Symmetric villager loss",
    ),
    component(
        "special_village_team_win",
        [SEER, WITCH, HUNTER],
        1.2,
        "terminal_team_payoff",
        "team",
        "terminal",
        "Seer, witch, or hunter is on the winning village team.",
        proposal_component="Special village team win",
    ),
    component(
        "special_village_team_loss",
        [SEER, WITCH, HUNTER],
        -1.2,
        "terminal_team_payoff",
        "team",
        "terminal",
        "Seer, witch, or hunter is on the losing village team.",
        proposal_component="Symmetric special-role village loss",
    ),
    component(
        "wolf_team_win",
        [WEREWOLF],
        1.5,
        "terminal_team_payoff",
        "team",
        "terminal",
        "Werewolf is on the winning wolf team.",
        proposal_component="Werewolf team win",
    ),
    component(
        "wolf_team_loss",
        [WEREWOLF],
        -1.5,
        "terminal_team_payoff",
        "team",
        "terminal",
        "Werewolf is on the losing wolf team.",
        proposal_component="Symmetric werewolf loss",
    ),
    component(
        "draw_terminal",
        [VILLAGER, SEER, WITCH, HUNTER, WEREWOLF],
        0.0,
        "terminal_team_payoff",
        "team",
        "terminal",
        "Game ends in a draw under the max-round rule.",
        proposal_component="Draw convention",
    ),
    component(
        "correct_vote_for_wolf",
        [VILLAGER, SEER, WITCH, HUNTER],
        0.05,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Village-team voter targets a live werewolf in a day vote.",
    ),
    component(
        "incorrect_vote_for_villager",
        [VILLAGER, SEER, WITCH, HUNTER],
        -0.05,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Village-team voter targets a village-team player in a day vote.",
    ),
    component(
        "wrongly_eliminated",
        [VILLAGER, SEER, WITCH, HUNTER],
        -0.5,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Village-team player is eliminated by day vote.",
        proposal_component="Villager wrongly eliminated risk/cost",
    ),
    component(
        "seer_investigation_used",
        [SEER],
        0.2,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Seer performs one legal night check.",
        proposal_component="Seer each investigation",
    ),
    component(
        "seer_information_leads_to_wolf_elimination",
        [SEER],
        0.3,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Checked wolf is eliminated by day vote within the attribution window.",
        proposal_component="Seer information leading to wolf elimination",
        double_counting_rules=(
            "Award once per checked wolf and seer; separate from the check-use "
            "reward because the later elimination is an attribution event."
        ),
    ),
    component(
        "witch_correct_save",
        [WITCH],
        0.3,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Witch uses antidote on a village-team night target that would die.",
        proposal_component="Witch correct save",
    ),
    component(
        "witch_wasted_potion",
        [WITCH],
        -0.2,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Witch uses a potion on a target that does not satisfy the correct-use rule.",
        proposal_component="Witch wasted potion",
    ),
    component(
        "witch_correct_poison",
        [WITCH],
        0.4,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Witch poison kills a werewolf.",
        proposal_component="Witch correct poison",
    ),
    component(
        "witch_poison_villager",
        [WITCH],
        -0.5,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Witch poison kills a village-team player.",
        proposal_component="Witch poison villager",
    ),
    component(
        "hunter_correct_shot",
        [HUNTER],
        0.4,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Legal hunter death shot kills a werewolf.",
        proposal_component="Hunter correct death shot",
    ),
    component(
        "hunter_shoot_villager",
        [HUNTER],
        -0.5,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Legal hunter death shot kills a village-team player.",
        proposal_component="Hunter shoot villager",
    ),
    component(
        "wolf_special_killed_shared",
        [WEREWOLF],
        0.5,
        "shared_wolf_team_bonus",
        "team_shared",
        "immediate",
        "A special village role dies from night kill or vote elimination.",
        proposal_component="Werewolf special killed",
        normalization_rules="Split equally across all wolves in the game.",
    ),
    component(
        "wolf_villager_voted_out_shared",
        [WEREWOLF],
        0.3,
        "shared_wolf_team_bonus",
        "team_shared",
        "immediate",
        "A village-team player is eliminated by day vote.",
        proposal_component="Werewolf villager voted out",
        normalization_rules="Split equally across all wolves in the game.",
    ),
    component(
        "survives_game",
        [VILLAGER, SEER, WITCH, HUNTER, WEREWOLF],
        0.05,
        "survival_or_exposure_payoff",
        "individual",
        "terminal",
        "Player survives to game end.",
        specification="extended",
    ),
    component(
        "death_with_unused_potion",
        [WITCH],
        -0.05,
        "opportunity_cost",
        "individual",
        "terminal",
        "Witch dies with at least one usable potion remaining.",
        specification="extended",
        opportunity_cost_rules="Observable from final witch potion state.",
    ),
    component(
        "false_public_accusation",
        [VILLAGER, SEER, WITCH, HUNTER, WEREWOLF],
        -0.05,
        "survival_or_exposure_payoff",
        "individual",
        "immediate",
        "Speech accusation targets a player later revealed as village-team.",
        specification="extended",
    ),
    component(
        "correct_public_accusation",
        [VILLAGER, SEER, WITCH, HUNTER, WEREWOLF],
        0.05,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Speech accusation targets a player later revealed as werewolf.",
        specification="extended",
    ),
    component(
        "successful_deception",
        [WEREWOLF],
        0.05,
        "individual_action_payoff",
        "individual",
        "immediate",
        "Wolf deceptive speech targets a village player who is eliminated that day.",
        specification="extended",
    ),
    component(
        "accusation_pressure_cost",
        [VILLAGER, SEER, WITCH, HUNTER, WEREWOLF],
        -0.02,
        "survival_or_exposure_payoff",
        "individual",
        "immediate",
        "Credibility module applies accusation pressure cost.",
        specification="extended",
    ),
    component(
        "wrong_accusation_cost",
        [VILLAGER, SEER, WITCH, HUNTER, WEREWOLF],
        -0.10,
        "survival_or_exposure_payoff",
        "individual",
        "immediate",
        "Credibility module applies wrong-accusation penalty.",
        specification="extended",
    ),
    component(
        "self_defense_cost",
        [VILLAGER, SEER, WITCH, HUNTER, WEREWOLF],
        -0.04,
        "survival_or_exposure_payoff",
        "individual",
        "immediate",
        "Credibility module applies repeated self-defense or trust-building cost.",
        specification="extended",
    ),
]


def current_git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def manifest_payload(source_commit=None):
    return {
        "manifest_version": MANIFEST_VERSION,
        "proposal_reference": [
            {
                "role": role,
                "payoff_component": component_name,
                "proposal_value": value,
                "proposal_description": description,
            }
            for role, component_name, value, description in PROPOSAL_REFERENCE
        ],
        "role_definitions": {
            VILLAGER: {"team": "village", "special_role": False},
            SEER: {"team": "village", "special_role": True},
            WITCH: {"team": "village", "special_role": True},
            HUNTER: {"team": "village", "special_role": True},
            WEREWOLF: {"team": "wolf", "special_role": False},
        },
        "payoff_components": deepcopy(PAYOFF_COMPONENTS),
        "normalization_rules": {
            "shared_wolf_team_bonus": (
                "Shared wolf bonuses are split equally across wolves so the "
                "team-level value is not multiplied by wolf count."
            ),
            "total_payoff": (
                "total_payoff = terminal_team_payoff + individual_action_payoff "
                "+ shared_wolf_team_bonus + survival_or_exposure_payoff "
                "+ opportunity_cost"
            ),
        },
        "source_commit": source_commit or current_git_commit(),
    }


def manifest_hash(payload):
    clean_payload = deepcopy(payload)
    clean_payload.pop("manifest_hash", None)
    encoded = json.dumps(clean_payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_manifest(source_commit=None):
    payload = manifest_payload(source_commit=source_commit)
    payload["manifest_hash"] = manifest_hash(payload)
    return payload


def component_lookup(manifest=None):
    manifest = manifest or build_manifest()
    return {
        item["component_id"]: item
        for item in manifest["payoff_components"]
    }


def write_manifest(path=RESULTS_DIR / "r4_payoff_manifest.json"):
    manifest = build_manifest()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    manifest = write_manifest()
    print(manifest["manifest_version"])
    print(manifest["manifest_hash"])
