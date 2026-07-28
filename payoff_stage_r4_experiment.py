"""Run the R4 unified payoff validation experiment."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from config import (
    DEFAULT_MAX_ROUNDS,
    TEN_PLAYER_CREDIBILITY_COST_SCALE,
    TEN_PLAYER_INITIAL_P_WOLF,
    TEN_PLAYER_ROLE_SETUP,
    TEN_PLAYER_SPEECH_SIGNAL_SCALE,
)
from game import Game, create_default_players
from payoff_calculator import calculate_r4_payoff
from payoff_historical_recalculation import (
    build_historical_recalculated_payoffs,
    build_historical_recalculation_coverage,
)
from payoff_manifest import (
    PAYOFF_COMPONENTS,
    PROPOSAL_REFERENCE,
    RESULTS_DIR,
    build_manifest,
    write_manifest,
)


R4_SEEDS = list(range(600, 610))
R4_GAMES_PER_CELL = 8

R4_BEHAVIORAL_REGIMES = {
    "baseline_structured_speech": {},
    "deception_and_credibility": {
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
    },
    "risk_mixed": {
        "enable_risk_preference": True,
        "risk_preference_mode": "mixed",
    },
    "strong_village_information": {
        "seer_avoid_repeat_checks": True,
        "witch_poison_threshold": 0.10,
    },
    "low_information_noise": {
        "initial_p_wolf": 0.20,
        "speech_signal_scale": 0.40,
        "witch_poison_threshold": 0.30,
    },
}

R4_STRATEGY_CONDITIONS = {
    "reference_strategy_mix": {},
    "villager_random_vote": {"use_suspicion_voting": False},
    "seer_highest_suspicion": {"seer_check_strategy": "highest_suspicion"},
    "wolf_random_kill": {
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "random",
    },
    "witch_conservative_poison": {"witch_poison_threshold": 0.30},
}


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            restval="",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def current_payoff_inventory_rows():
    return [
        {
            "term_name": "final_win_bonus",
            "role": "all",
            "trigger": "terminal game winner in payoff.calculate_payoffs",
            "current_value": "+1.0 win / -1.0 loss / 0 draw",
            "source_code": "payoff.py",
            "source_report": "experiment_report.md; simulation.py summaries",
            "terminal_or_event_level": "terminal",
            "team_or_individual": "team",
            "may_be_double_counted": "yes, if mixed with role-specific terminal payoff",
            "proposal_conflict": "proposal has role-specific terminal values",
        },
        {
            "term_name": "role_action_bonus: night_kill",
            "role": "werewolf",
            "trigger": "night_kill event",
            "current_value": "+0.1 per wolf per night_kill",
            "source_code": "payoff.py",
            "source_report": "experiment_report.md",
            "terminal_or_event_level": "event",
            "team_or_individual": "team-like duplicated per wolf",
            "may_be_double_counted": "yes, wolf team event duplicated across wolves",
            "proposal_conflict": "proposal distinguishes special killed and villager voted out",
        },
        {
            "term_name": "role_action_bonus: seer_check",
            "role": "seer",
            "trigger": "seer_check target_is_wolf true/false",
            "current_value": "+0.2 wolf; +0.05 non-wolf",
            "source_code": "payoff.py; seer_action.py",
            "source_report": "seer_position_experiment_report.md",
            "terminal_or_event_level": "event",
            "team_or_individual": "individual",
            "may_be_double_counted": "possible with information attribution",
            "proposal_conflict": "proposal gives +0.2 each investigation and +0.3 attribution",
        },
        {
            "term_name": "role_action_bonus: witch_save",
            "role": "witch",
            "trigger": "witch_save event",
            "current_value": "+0.2",
            "source_code": "payoff.py; witch_action.py",
            "source_report": "risk_preference_experiment_report.md",
            "terminal_or_event_level": "event",
            "team_or_individual": "individual",
            "may_be_double_counted": "possible with team win",
            "proposal_conflict": "proposal anchor is +0.3 correct save",
        },
        {
            "term_name": "role_action_bonus/mistake_penalty: witch_poison",
            "role": "witch",
            "trigger": "witch_poison target_is_wolf true/false",
            "current_value": "+0.3 wolf; -0.3 non-wolf",
            "source_code": "payoff.py; witch_action.py",
            "source_report": "risk_preference_experiment_report.md",
            "terminal_or_event_level": "event",
            "team_or_individual": "individual",
            "may_be_double_counted": "no direct duplicate found",
            "proposal_conflict": "proposal anchors +0.4 correct poison and -0.5 poison villager",
        },
        {
            "term_name": "role_action_bonus/mistake_penalty: hunter_shot",
            "role": "hunter",
            "trigger": "hunter_shot target_is_wolf true/false",
            "current_value": "+0.3 wolf; -0.3 non-wolf",
            "source_code": "payoff.py; hunter_action.py",
            "source_report": "experiment_report.md",
            "terminal_or_event_level": "event",
            "team_or_individual": "individual",
            "may_be_double_counted": "possible with wolf elimination reward",
            "proposal_conflict": "proposal anchors +0.4 correct shot and -0.5 shoot villager",
        },
        {
            "term_name": "vote target quality",
            "role": "all voters",
            "trigger": "day_vote vote target team",
            "current_value": "+0.05 wolf target; -0.05 village target",
            "source_code": "payoff.py; voting.py",
            "source_report": "stage2_experiment_report.md",
            "terminal_or_event_level": "event",
            "team_or_individual": "individual",
            "may_be_double_counted": "possible with wolf villager-voted-out bonus",
            "proposal_conflict": "not explicit proposal anchor; retained as conservative core shaping",
        },
        {
            "term_name": "survival_bonus",
            "role": "all",
            "trigger": "player alive at terminal state",
            "current_value": "+0.2",
            "source_code": "payoff.py",
            "source_report": "simulation.py summaries",
            "terminal_or_event_level": "terminal",
            "team_or_individual": "individual",
            "may_be_double_counted": "possible with terminal team payoff",
            "proposal_conflict": "proposal mentions mortality/exposure risk but not +0.2 universal survival",
        },
        {
            "term_name": "credibility costs",
            "role": "speakers",
            "trigger": "accusation/self-defense credibility events",
            "current_value": "updates suspicion/p_wolf; not historical payoff total",
            "source_code": "deception_credibility.py",
            "source_report": "stage3_experiment_report.md",
            "terminal_or_event_level": "event",
            "team_or_individual": "individual",
            "may_be_double_counted": "yes, if combined with wrong vote/false accusation cost",
            "proposal_conflict": "not a proposal anchor; included only in extended R4 specification",
        },
    ]


def proposal_reference_rows(manifest):
    components = {
        item.get("proposal_component"): item
        for item in manifest["payoff_components"]
        if item.get("proposal_component")
    }
    rows = []
    for role, component_name, value, description in PROPOSAL_REFERENCE:
        match = None
        for proposal_component, component_row in components.items():
            if component_name.replace("_", " ") in proposal_component.lower():
                match = component_row
                break
        final_value = match["base_value"] if match else ""
        rows.append({
            "role": role,
            "payoff_component": component_name,
            "proposal_value": value,
            "proposal_description": description,
            "implementation_status": "implemented" if match else "documented_reference",
            "final_r4_value": final_value,
            "difference_from_proposal": (
                float(final_value) - float(value)
                if final_value != ""
                else ""
            ),
            "rationale": (
                "Matches proposal anchor or symmetric loss convention."
                if final_value == value
                else "Documented for traceability; not all proposal risk terms are primary core rewards."
            ),
            "evidence_source": "payoff_manifest.py",
            "notes": "Proposal value preserved; changes are explicit in final_r4_value.",
        })
    return rows


def component_registry_rows(manifest):
    return manifest["payoff_components"]


def role_payoff_matrix_rows(manifest):
    rows = []
    for component in manifest["payoff_components"]:
        for role in component["role_scope"]:
            rows.append({
                "role": role,
                "payoff_component": component["component_id"],
                "base_value": component["base_value"],
                "specification": component["specification"],
                "component_category": component["component_category"],
                "team_or_individual": component["team_or_individual"],
                "immediate_or_terminal": component["immediate_or_terminal"],
                "trigger_definition": component["trigger_definition"],
            })
    return rows


def write_event_attribution_rules(path):
    path.write_text(
        """# R4 Event Attribution Rules

## Seer Information Attribution

The core ledger awards `seer_information_leads_to_wolf_elimination` only when
the same seer checked a wolf and that checked wolf was eliminated by day vote
within two rounds. The basic check reward remains separate from this later
attribution event.

## Witch Correct Save

The core ledger treats an antidote as correct when it is legally used on a
village-team night-kill target who would otherwise die. Saving a wolf or using a
potion without the legal target condition is treated as wasted potion.

## Hunter Correct Shot

The core ledger treats a hunter shot as correct only when the legal death shot
targets a werewolf. Shots into village-team players receive the proposal
wrong-shot penalty.

## Wolf Shared Rewards

Wolf special-kill and village-vote-elimination bonuses are team-shared and split
equally across all wolves. This prevents multiplying one team event by the wolf
count while preserving player-level totals.

## Opportunity Costs

Primary R4 opportunity costs use only observable rule-based states. Speculative
counterfactual full-rollout costs are excluded from the core ledger and deferred
to R5 risk-adjusted analysis.
""",
        encoding="utf-8",
    )


def base_game_kwargs():
    return {
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": True,
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "threat_based",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "mixed",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "enable_last_words": False,
        "enable_risk_preference": False,
        "risk_preference_mode": "mixed",
        "initial_p_wolf": TEN_PLAYER_INITIAL_P_WOLF,
        "speech_signal_scale": TEN_PLAYER_SPEECH_SIGNAL_SCALE,
        "credibility_cost_scale": TEN_PLAYER_CREDIBILITY_COST_SCALE,
        "enable_position_model": True,
        "randomize_seat_roles": True,
        "enable_r4_payoff_ledger": False,
    }


def merged_game_kwargs(condition_name, regime_name):
    kwargs = base_game_kwargs()
    kwargs.update(R4_BEHAVIORAL_REGIMES[regime_name])
    kwargs.update(R4_STRATEGY_CONDITIONS[condition_name])
    return kwargs


def run_r4_validation_experiment(output_dir=RESULTS_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = write_manifest(output_dir / "r4_payoff_manifest.json")
    write_csv(output_dir / "current_payoff_inventory.csv", current_payoff_inventory_rows())
    write_csv(output_dir / "proposal_payoff_reference.csv", proposal_reference_rows(manifest))
    write_csv(output_dir / "r4_payoff_component_registry.csv", component_registry_rows(manifest))
    write_csv(output_dir / "r4_role_payoff_matrix.csv", role_payoff_matrix_rows(manifest))
    write_event_attribution_rules(output_dir / "r4_event_attribution_rules.md")

    seed_rows = [{"seed": seed, "seed_group": "r4_validation"} for seed in R4_SEEDS]
    regime_rows = [
        {"behavioral_regime": name, "config_overrides": str(overrides)}
        for name, overrides in R4_BEHAVIORAL_REGIMES.items()
    ]
    write_csv(output_dir / "r4_seed_registry.csv", seed_rows)
    write_csv(output_dir / "r4_behavioral_regime_registry.csv", regime_rows)

    game_rows = []
    player_rows = []
    event_rows = []

    for seed in R4_SEEDS:
        for regime_name in R4_BEHAVIORAL_REGIMES:
            for condition_name in R4_STRATEGY_CONDITIONS:
                for game_index in range(1, R4_GAMES_PER_CELL + 1):
                    game_seed = (
                        seed * 1_000_000
                        + list(R4_BEHAVIORAL_REGIMES).index(regime_name) * 10_000
                        + list(R4_STRATEGY_CONDITIONS).index(condition_name) * 100
                        + game_index
                    )
                    random.seed(game_seed)
                    kwargs = merged_game_kwargs(condition_name, regime_name)
                    initial_p_wolf = kwargs.pop(
                        "initial_p_wolf",
                        TEN_PLAYER_INITIAL_P_WOLF,
                    )
                    players = create_default_players(
                        role_setup=TEN_PLAYER_ROLE_SETUP,
                        initial_p_wolf=initial_p_wolf,
                    )
                    game_id = (
                        f"r4_seed{seed}_{regime_name}_{condition_name}_"
                        f"{game_index:02d}"
                    )
                    game = Game(
                        players,
                        label_condition=condition_name,
                        main_game_seed=game_seed,
                        base_game_index=game_index,
                        **kwargs,
                    )
                    game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
                    for calculation_specification in ["core", "extended"]:
                        result = calculate_r4_payoff(
                            game,
                            game_id=game_id,
                            matched_set_id=(
                                f"r4_seed{seed}_{regime_name}_{game_index:02d}"
                            ),
                            seed=seed,
                            calculation_specification=calculation_specification,
                            manifest=manifest,
                            condition_name=condition_name,
                            behavioral_regime=regime_name,
                        )
                        game_row = result["game_row"]
                        game_rows.append(game_row)
                        for row in result["player_rows"]:
                            row["condition_name"] = condition_name
                            row["behavioral_regime"] = regime_name
                            player_rows.append(row)
                        for row in result["event_rows"]:
                            row["condition_name"] = condition_name
                            row["behavioral_regime"] = regime_name
                            event_rows.append(row)

    write_csv(output_dir / "r4_game_level_payoff_raw.csv", game_rows)
    write_csv(output_dir / "r4_player_level_payoff_raw.csv", player_rows)
    write_csv(output_dir / "r4_event_level_payoff_ledger.csv", event_rows)

    strategy_rows = []
    for row in player_rows:
        strategy_rows.append({
            "game_id": row["game_id"],
            "seed": row["seed"],
            "behavioral_regime": row["behavioral_regime"],
            "condition_name": row["condition_name"],
            "calculation_specification": row["calculation_specification"],
            "role": row["role"],
            "team": row["team"],
            "total_payoff": row["total_payoff"],
            "terminal_team_payoff": row["terminal_team_payoff"],
            "individual_action_payoff": row["individual_action_payoff"],
            "shared_wolf_team_bonus": row["shared_wolf_team_bonus"],
            "survival_or_exposure_payoff": row["survival_or_exposure_payoff"],
            "opportunity_cost": row["opportunity_cost"],
        })
    write_csv(output_dir / "r4_strategy_level_payoff_raw.csv", strategy_rows)

    coverage_rows = build_historical_recalculation_coverage()
    write_csv(output_dir / "historical_recalculation_coverage.csv", coverage_rows)
    write_csv(
        output_dir / "r4_historical_recalculated_payoffs.csv",
        build_historical_recalculated_payoffs(coverage_rows),
    )

    from payoff_stage_r4_analysis import analyze_r4_outputs

    return analyze_r4_outputs(output_dir=output_dir)


if __name__ == "__main__":
    artifacts = run_r4_validation_experiment()
    scale = artifacts["scale"]
    print("R4 payoff matrix validation complete")
    print(f"Output directory: {RESULTS_DIR}")
    print(f"Validation games: {scale['validation_game_count']}")
    print(f"Seeds: {scale['seed_count']}")
    print(f"Regimes: {scale['regime_count']}")
    print(f"Payoff event rows: {scale['event_row_count']}")
    print(f"Manifest hash: {scale['manifest_hash']}")
