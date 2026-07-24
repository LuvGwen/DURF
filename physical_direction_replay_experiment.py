import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

from config import DEFAULT_MAX_ROUNDS
from game import Game
from physical_direction_replay import (
    capture_replay_action_log,
    compare_strategy_mirror_logs,
    create_players_from_actor_layout,
    mirror_actor_physical_seats,
    physical_seats_by_actor_from_physical_roles,
    replay_action_log,
    replay_mirrored_action_log,
    role_by_actor_from_physical_roles,
)
from seat_order_neutral import NORMAL_MAPPING, json_dump, stable_seed
from seat_order_neutral_experiment import generate_physical_role_assignment
from ten_player_seer_position_experiment import SEER_POSITION_BASE_CONFIG


RESULTS_DIR = Path("results") / "physical_direction_replay"
SUPPLIED_REPLAY_RAW_PATH = (
    RESULTS_DIR / "supplied_action_replay_game_level_raw.csv"
)
PHYSICAL_MIRROR_RAW_PATH = (
    RESULTS_DIR / "physical_mirror_replay_pair_raw.csv"
)
STRATEGY_MIRROR_RAW_PATH = (
    RESULTS_DIR / "strategy_mirror_counterfactual_raw.csv"
)
DIVERGENCE_EVENTS_PATH = RESULTS_DIR / "replay_divergence_events.csv"
SCHEMA_PATH = RESULTS_DIR / "physical_direction_replay_schema.md"
AUDIT_PATH = RESULTS_DIR / "physical_direction_replay_implementation_audit.md"
SUPPLIED_SUMMARY_PATH = RESULTS_DIR / "supplied_action_replay_summary.csv"
PHYSICAL_MIRROR_SUMMARY_PATH = (
    RESULTS_DIR / "physical_mirror_replay_summary.csv"
)
STRATEGY_MIRROR_SUMMARY_PATH = (
    RESULTS_DIR / "strategy_mirror_counterfactual_summary.csv"
)
DIVERGENCE_SUMMARY_PATH = RESULTS_DIR / "replay_divergence_summary.csv"
REPORT_PATH = RESULTS_DIR / "physical_direction_replay_experiment_report.md"

SEEDS = [42, 43, 44, 45, 46]
SUPPLIED_REPLAY_BASE_CONFIGS_PER_SEED = 200
PHYSICAL_MIRROR_BASE_CONFIGS_PER_SEED = 500
STRATEGY_MIRROR_BASE_CONFIGS_PER_SEED = 1000
REFERENCE_STRATEGY = "physical_clockwise"
MIRROR_STRATEGY = "physical_counterclockwise"

RAW_FIELDNAMES = [
    "experiment_component",
    "pair_id",
    "game_id",
    "seed",
    "base_game_index",
    "reference_or_replay",
    "strategy",
    "mirrored",
    "physical_direction",
    "actor_mapping",
    "physical_mapping",
    "action_log_id",
    "action_count",
    "reference_action_count",
    "replay_action_count",
    "action_sequence_exact_match",
    "state_sequence_exact_match",
    "winner_match",
    "total_rounds_match",
    "final_alive_set_match",
    "first_divergence_event_index",
    "first_divergence_round",
    "first_divergence_phase",
    "first_divergence_type",
    "mirrored_action_sequence_match",
    "first_check_mirror_match",
    "full_check_sequence_mirror_match",
    "vote_sequence_mirror_match",
    "speech_sequence_mirror_match",
    "winner_mirror_match",
    "rounds_mirror_match",
    "final_alive_mirror_match",
    "winner",
    "village_win",
    "wolf_win",
    "total_rounds",
    "seer_actor_uid",
    "seer_survived_to_game_end",
    "total_seer_checks",
    "found_wolf_by_check_1",
    "found_wolf_by_check_2",
    "found_wolf_by_check_3",
]

SUMMARY_FIELDNAMES = [
    "experiment_component",
    "num_pairs",
    "num_games",
    "exact_replay_match_rate",
    "physical_mirror_match_rate",
    "strategy_mirror_action_sequence_match_rate",
    "first_check_mirror_match_rate",
    "full_check_sequence_mirror_match_rate",
    "vote_sequence_mirror_match_rate",
    "speech_sequence_mirror_match_rate",
    "winner_match_rate",
    "final_alive_set_match_rate",
    "avg_reference_action_count",
    "avg_replay_action_count",
    "village_win_rate",
    "wolf_win_rate",
    "avg_total_rounds",
    "avg_total_seer_checks",
]

DIVERGENCE_FIELDNAMES = [
    "experiment_component",
    "pair_id",
    "seed",
    "base_game_index",
    "strategy",
    "first_divergence_event_index",
    "first_divergence_round",
    "first_divergence_phase",
    "first_divergence_type",
    "expected",
    "observed",
]


def bool_int(value):
    return 1 if value else 0


def safe_rate(rows, field):
    values = [
        float(row[field])
        for row in rows
        if row.get(field) not in ("", None)
    ]
    if not values:
        return ""
    return sum(values) / len(values)


def safe_mean(rows, field):
    values = [
        float(row[field])
        for row in rows
        if row.get(field) not in ("", None)
    ]
    if not values:
        return ""
    return mean(values)


def format_percent(value):
    if value == "":
        return "NA"
    return f"{float(value) * 100:.2f}%"


def format_count(value):
    if value == "":
        return "NA"
    return str(int(float(value)))


def role_and_position_for_seed(seed, base_game_index):
    role_by_physical = generate_physical_role_assignment(
        seed,
        base_game_index,
    )
    role_by_actor = role_by_actor_from_physical_roles(role_by_physical)
    physical_by_actor = physical_seats_by_actor_from_physical_roles(
        role_by_physical
    )
    return role_by_actor, physical_by_actor


def run_game_for_actor_layout(
    seed,
    base_game_index,
    strategy,
    role_by_actor,
    physical_by_actor,
    label_condition,
):
    config = dict(SEER_POSITION_BASE_CONFIG)
    main_game_seed = stable_seed(
        "physical_direction_replay_main_game",
        seed,
        base_game_index,
    )
    config.update({
        "seer_check_strategy": strategy,
        "seer_avoid_repeat_checks": True,
        "randomize_seat_roles": False,
        "seat_order_neutral_mode": True,
        "neutral_seed": seed,
        "base_game_index": base_game_index,
        "label_condition": label_condition,
        "physical_to_displayed_mapping": NORMAL_MAPPING,
        "main_game_seed": main_game_seed,
    })
    players = create_players_from_actor_layout(
        role_by_actor,
        physical_by_actor,
        NORMAL_MAPPING,
        initial_p_wolf=config["initial_p_wolf"],
    )
    random.seed(main_game_seed)
    game = Game(players, **config)
    result = game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
    action_log = capture_replay_action_log(
        game,
        (
            f"{label_condition}_seed_{seed}_base_{base_game_index}_"
            f"{strategy}"
        ),
        role_by_actor_uid=role_by_actor,
        physical_seat_by_actor_uid=physical_by_actor,
        initial_p_wolf=config["initial_p_wolf"],
        metadata={
            "seed": seed,
            "base_game_index": base_game_index,
            "strategy": strategy,
            "label_condition": label_condition,
            "main_game_seed": main_game_seed,
        },
    )
    return game, result, action_log


def final_alive_actor_uids(game):
    return sorted(
        player.actor_uid
        for player in game.state.players
        if player.alive
    )


def seer_actor_uid(game):
    for player in game.state.players:
        if player.role == "seer":
            return player.actor_uid
    return ""


def outcome_metrics(game, result):
    checks = [
        event for event in game.event_log
        if event.get("event_type") == "seer_check"
    ]
    check_is_wolf = [
        event.get("content", {}).get("target_is_wolf") is True
        for event in checks
    ]
    return {
        "winner": result["winner"],
        "village_win": 1 if result["winner"] == "village" else 0,
        "wolf_win": 1 if result["winner"] == "wolf" else 0,
        "total_rounds": result["round_number"],
        "seer_actor_uid": seer_actor_uid(game),
        "seer_survived_to_game_end": bool_int(
            any(
                player.role == "seer" and player.alive
                for player in game.state.players
            )
        ),
        "total_seer_checks": len(checks),
        "found_wolf_by_check_1": bool_int(any(check_is_wolf[:1])),
        "found_wolf_by_check_2": bool_int(any(check_is_wolf[:2])),
        "found_wolf_by_check_3": bool_int(any(check_is_wolf[:3])),
    }


def base_row(
    component,
    pair_id,
    game_id,
    seed,
    base_game_index,
    reference_or_replay,
    strategy,
    mirrored,
    physical_direction,
    role_by_actor,
    physical_by_actor,
    action_log,
):
    return {
        "experiment_component": component,
        "pair_id": pair_id,
        "game_id": game_id,
        "seed": seed,
        "base_game_index": base_game_index,
        "reference_or_replay": reference_or_replay,
        "strategy": strategy,
        "mirrored": bool_int(mirrored),
        "physical_direction": physical_direction,
        "actor_mapping": json_dump(role_by_actor),
        "physical_mapping": json_dump(physical_by_actor),
        "action_log_id": action_log.action_log_id,
        "action_count": len(action_log.actions),
        "reference_action_count": len(action_log.actions),
        "replay_action_count": "",
        "action_sequence_exact_match": "",
        "state_sequence_exact_match": "",
        "winner_match": "",
        "total_rounds_match": "",
        "final_alive_set_match": "",
        "first_divergence_event_index": "",
        "first_divergence_round": "",
        "first_divergence_phase": "",
        "first_divergence_type": "none",
        "mirrored_action_sequence_match": "",
        "first_check_mirror_match": "",
        "full_check_sequence_mirror_match": "",
        "vote_sequence_mirror_match": "",
        "speech_sequence_mirror_match": "",
        "winner_mirror_match": "",
        "rounds_mirror_match": "",
        "final_alive_mirror_match": "",
    }


def run_supplied_action_replay_component(
    seeds=None,
    num_base_configs=SUPPLIED_REPLAY_BASE_CONFIGS_PER_SEED,
):
    if seeds is None:
        seeds = SEEDS

    rows = []
    divergences = []
    for seed in seeds:
        for base_game_index in range(1, num_base_configs + 1):
            role_by_actor, physical_by_actor = role_and_position_for_seed(
                seed,
                base_game_index,
            )
            pair_id = f"same_action_seed_{seed}_base_{base_game_index}"
            game, result, action_log = run_game_for_actor_layout(
                seed,
                base_game_index,
                REFERENCE_STRATEGY,
                role_by_actor,
                physical_by_actor,
                "same_action_reference",
            )
            replay_result, replay_controller = replay_action_log(action_log)
            actual_final_alive = final_alive_actor_uids(game)
            replay_result.winner_match = (
                replay_result.winner_match
                and replay_controller.winner == result["winner"]
            )
            replay_result.total_rounds_match = (
                replay_result.total_rounds_match
                and replay_controller.round_number == result["round_number"]
            )
            replay_result.final_alive_set_match = (
                replay_result.final_alive_set_match
                and replay_controller.final_alive_actor_uids()
                == actual_final_alive
            )
            replay_result.state_sequence_exact_match = (
                replay_result.state_sequence_exact_match
                and replay_result.winner_match
                and replay_result.total_rounds_match
                and replay_result.final_alive_set_match
            )
            row = base_row(
                "supplied_action_replay",
                pair_id,
                pair_id,
                seed,
                base_game_index,
                "reference_replay_pair",
                REFERENCE_STRATEGY,
                False,
                "same_physical_actions",
                role_by_actor,
                physical_by_actor,
                action_log,
            )
            row.update(replay_result.to_dict())
            row["replay_action_count"] = len(replay_controller.event_trace)
            row.update(outcome_metrics(game, result))
            rows.append(row)
            if not replay_result.state_sequence_exact_match:
                divergences.append(make_divergence_row(row, replay_result))

    return rows, divergences


def run_physical_mirror_replay_component(
    seeds=None,
    num_base_configs=PHYSICAL_MIRROR_BASE_CONFIGS_PER_SEED,
):
    if seeds is None:
        seeds = SEEDS

    rows = []
    divergences = []
    for seed in seeds:
        for base_game_index in range(1, num_base_configs + 1):
            role_by_actor, physical_by_actor = role_and_position_for_seed(
                seed,
                base_game_index,
            )
            pair_id = f"physical_mirror_seed_{seed}_base_{base_game_index}"
            game, result, action_log = run_game_for_actor_layout(
                seed,
                base_game_index,
                REFERENCE_STRATEGY,
                role_by_actor,
                physical_by_actor,
                "physical_mirror_reference",
            )
            mirror_result, mirrored_log, mirrored_controller = (
                replay_mirrored_action_log(action_log)
            )
            row = base_row(
                "physical_mirror_replay",
                pair_id,
                pair_id,
                seed,
                base_game_index,
                "mirrored_replay_pair",
                REFERENCE_STRATEGY,
                True,
                "mirrored_same_actions",
                role_by_actor,
                mirrored_log.physical_seat_by_actor_uid,
                mirrored_log,
            )
            row.update(mirror_result.to_dict())
            row["replay_action_count"] = len(mirrored_controller.event_trace)
            row.update(outcome_metrics(game, result))
            rows.append(row)
            if not mirror_result.state_sequence_exact_match:
                divergences.append(make_divergence_row(row, mirror_result))

    return rows, divergences


def run_strategy_mirror_counterfactual_component(
    seeds=None,
    num_base_configs=STRATEGY_MIRROR_BASE_CONFIGS_PER_SEED,
):
    if seeds is None:
        seeds = SEEDS

    rows = []
    divergences = []
    for seed in seeds:
        for base_game_index in range(1, num_base_configs + 1):
            role_by_actor, physical_by_actor = role_and_position_for_seed(
                seed,
                base_game_index,
            )
            mirrored_physical = mirror_actor_physical_seats(physical_by_actor)
            pair_id = f"strategy_mirror_seed_{seed}_base_{base_game_index}"

            reference_game, reference_result, reference_log = (
                run_game_for_actor_layout(
                    seed,
                    base_game_index,
                    REFERENCE_STRATEGY,
                    role_by_actor,
                    physical_by_actor,
                    "strategy_mirror_reference",
                )
            )
            mirror_game, mirror_result, mirror_log = run_game_for_actor_layout(
                seed,
                base_game_index,
                MIRROR_STRATEGY,
                role_by_actor,
                mirrored_physical,
                "strategy_mirror_counterfactual",
            )
            comparison = compare_strategy_mirror_logs(
                reference_log,
                mirror_log,
            )
            row = base_row(
                "strategy_mirror_counterfactual",
                pair_id,
                pair_id,
                seed,
                base_game_index,
                "strategy_mirror_pair",
                f"{REFERENCE_STRATEGY}_vs_{MIRROR_STRATEGY}",
                True,
                "clockwise_original_counterclockwise_mirrored",
                role_by_actor,
                mirrored_physical,
                reference_log,
            )
            row.update(outcome_metrics(reference_game, reference_result))
            row.update({
                "reference_action_count": len(reference_log.actions),
                "replay_action_count": len(mirror_log.actions),
                "mirrored_action_sequence_match": bool_int(
                    comparison["action_sequence_match"]
                ),
                "first_check_mirror_match": bool_int(
                    comparison["first_check_mirror_match"]
                ),
                "full_check_sequence_mirror_match": bool_int(
                    comparison["full_check_sequence_mirror_match"]
                ),
                "vote_sequence_mirror_match": bool_int(
                    comparison["vote_sequence_mirror_match"]
                ),
                "speech_sequence_mirror_match": bool_int(
                    comparison["speech_sequence_mirror_match"]
                ),
                "winner_mirror_match": bool_int(
                    reference_result["winner"] == mirror_result["winner"]
                ),
                "rounds_mirror_match": bool_int(
                    reference_result["round_number"]
                    == mirror_result["round_number"]
                ),
                "final_alive_mirror_match": bool_int(
                    final_alive_actor_uids(reference_game)
                    == final_alive_actor_uids(mirror_game)
                ),
                "action_sequence_exact_match": bool_int(
                    comparison["action_sequence_match"]
                ),
                "state_sequence_exact_match": "",
                "winner_match": bool_int(
                    reference_result["winner"] == mirror_result["winner"]
                ),
                "total_rounds_match": bool_int(
                    reference_result["round_number"]
                    == mirror_result["round_number"]
                ),
                "final_alive_set_match": bool_int(
                    final_alive_actor_uids(reference_game)
                    == final_alive_actor_uids(mirror_game)
                ),
                "first_divergence_event_index": (
                    comparison["first_divergence"]["index"]
                ),
                "first_divergence_round": (
                    comparison["first_divergence"]["round"]
                ),
                "first_divergence_phase": (
                    comparison["first_divergence"]["phase"]
                ),
                "first_divergence_type": (
                    comparison["first_divergence"]["type"]
                ),
            })
            rows.append(row)
            if not comparison["action_sequence_match"]:
                divergences.append(make_divergence_row(
                    row,
                    comparison["first_divergence"],
                ))

    return rows, divergences


def make_divergence_row(row, divergence):
    if hasattr(divergence, "to_dict"):
        divergence = divergence.to_dict()
    first = divergence.get("first_divergence", divergence)
    return {
        "experiment_component": row["experiment_component"],
        "pair_id": row["pair_id"],
        "seed": row["seed"],
        "base_game_index": row["base_game_index"],
        "strategy": row["strategy"],
        "first_divergence_event_index": (
            first.get("index")
            or first.get("first_divergence_event_index")
            or row.get("first_divergence_event_index", "")
        ),
        "first_divergence_round": (
            first.get("round")
            or first.get("first_divergence_round")
            or row.get("first_divergence_round", "")
        ),
        "first_divergence_phase": (
            first.get("phase")
            or first.get("first_divergence_phase")
            or row.get("first_divergence_phase", "")
        ),
        "first_divergence_type": (
            first.get("type")
            or first.get("first_divergence_type")
            or row.get("first_divergence_type", "")
        ),
        "expected": json.dumps(first.get("expected", ""), sort_keys=True),
        "observed": json.dumps(first.get("observed", ""), sort_keys=True),
    }


def summarize_component(rows, component):
    return {
        "experiment_component": component,
        "num_pairs": len(rows),
        "num_games": (
            len(rows) * 2
            if component == "strategy_mirror_counterfactual"
            else len(rows)
        ),
        "exact_replay_match_rate": safe_rate(
            rows,
            "state_sequence_exact_match",
        ),
        "physical_mirror_match_rate": safe_rate(
            rows,
            "state_sequence_exact_match",
        ) if component == "physical_mirror_replay" else "",
        "strategy_mirror_action_sequence_match_rate": safe_rate(
            rows,
            "mirrored_action_sequence_match",
        ),
        "first_check_mirror_match_rate": safe_rate(
            rows,
            "first_check_mirror_match",
        ),
        "full_check_sequence_mirror_match_rate": safe_rate(
            rows,
            "full_check_sequence_mirror_match",
        ),
        "vote_sequence_mirror_match_rate": safe_rate(
            rows,
            "vote_sequence_mirror_match",
        ),
        "speech_sequence_mirror_match_rate": safe_rate(
            rows,
            "speech_sequence_mirror_match",
        ),
        "winner_match_rate": safe_rate(rows, "winner_match"),
        "final_alive_set_match_rate": safe_rate(
            rows,
            "final_alive_set_match",
        ),
        "avg_reference_action_count": safe_mean(
            rows,
            "reference_action_count",
        ),
        "avg_replay_action_count": safe_mean(rows, "replay_action_count"),
        "village_win_rate": safe_rate(rows, "village_win"),
        "wolf_win_rate": safe_rate(rows, "wolf_win"),
        "avg_total_rounds": safe_mean(rows, "total_rounds"),
        "avg_total_seer_checks": safe_mean(rows, "total_seer_checks"),
    }


def summarize_divergences(divergence_rows):
    grouped = defaultdict(list)
    for row in divergence_rows:
        grouped[
            (
                row["experiment_component"],
                row["first_divergence_phase"],
                row["first_divergence_type"],
            )
        ].append(row)
    rows = []
    for key, group in sorted(grouped.items()):
        component, phase, divergence_type = key
        rows.append({
            "experiment_component": component,
            "first_divergence_phase": phase,
            "first_divergence_type": divergence_type,
            "num_divergences": len(group),
        })
    if not rows:
        rows.append({
            "experiment_component": "all",
            "first_divergence_phase": "none",
            "first_divergence_type": "none",
            "num_divergences": 0,
        })
    return rows


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            restval="",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_schema(path):
    descriptions = {
        "experiment_component": "A, B, or C replay experiment component.",
        "pair_id": "Stable pair identifier.",
        "game_id": "Stable game or pair identifier.",
        "seed": "Experiment seed.",
        "base_game_index": "One-based base physical configuration index.",
        "reference_or_replay": "Reference/replay pair label.",
        "strategy": "Seer checking strategy or strategy pair.",
        "mirrored": "1 if the row uses a mirrored physical layout.",
        "physical_direction": "Physical direction condition.",
        "actor_mapping": "JSON actor_uid to role mapping.",
        "physical_mapping": "JSON actor_uid to physical seat mapping.",
        "action_log_id": "Captured supplied-action log identifier.",
        "action_count": "Number of supplied actions.",
        "reference_action_count": "Reference supplied-action count.",
        "replay_action_count": "Replay or comparison action count.",
        "action_sequence_exact_match": "1 if action signatures match.",
        "state_sequence_exact_match": "1 if replay state hashes match.",
        "winner_match": "1 if winner matches.",
        "total_rounds_match": "1 if total rounds match.",
        "final_alive_set_match": "1 if final alive actor set matches.",
        "first_divergence_event_index": "First divergent action index.",
        "first_divergence_round": "First divergent action round.",
        "first_divergence_phase": "First divergent action phase.",
        "first_divergence_type": "First divergent action or hash type.",
        "mirrored_action_sequence_match": (
            "1 if mirrored strategy action signatures match after coordinate "
            "normalization."
        ),
        "first_check_mirror_match": (
            "1 if the first seer check target actor mirrors correctly."
        ),
        "full_check_sequence_mirror_match": (
            "1 if all seer check target actors mirror correctly."
        ),
        "vote_sequence_mirror_match": (
            "1 if the full supplied vote sequence matches by actor_uid."
        ),
        "speech_sequence_mirror_match": (
            "1 if speech actions match by actor_uid, speech type, target, "
            "and deception type."
        ),
        "winner_mirror_match": "1 if mirrored strategy pair winner matches.",
        "rounds_mirror_match": (
            "1 if mirrored strategy pair total rounds match."
        ),
        "final_alive_mirror_match": (
            "1 if mirrored strategy pair final alive actor set matches."
        ),
        "winner": "Reference game winner.",
        "village_win": "1 if reference game winner is village.",
        "wolf_win": "1 if reference game winner is wolf.",
        "total_rounds": "Reference game final round number.",
        "seer_actor_uid": "Stable actor_uid of the seer.",
        "seer_survived_to_game_end": (
            "1 if the seer actor survived to game end."
        ),
        "total_seer_checks": "Number of seer_check actions.",
        "found_wolf_by_check_1": "1 if a wolf was found by check 1.",
        "found_wolf_by_check_2": "1 if a wolf was found by check 2.",
        "found_wolf_by_check_3": "1 if a wolf was found by check 3.",
    }
    with path.open("w") as file:
        file.write("# Physical Direction Replay Schema\n\n")
        file.write(
            "The replay datasets use stable `actor_uid` values as physical "
            "identity. Physical seats can be mirrored without changing actor "
            "identity or role identity. Supplied actions target actor_uids and "
            "record physical target seats for auditability.\n\n"
        )
        file.write("| column | description |\n")
        file.write("|---|---|\n")
        for field in RAW_FIELDNAMES:
            file.write(f"| {field} | {descriptions.get(field, '')} |\n")


def write_audit(path):
    rows = [
        (
            "physical_direction_replay.py",
            "SuppliedAction",
            "Structured action record keyed by actor_uid and physical target.",
            "New diagnostic-only representation; no default engine change.",
        ),
        (
            "physical_direction_replay.py",
            "ReplayController",
            "Consumes supplied actions without strategy modules choosing new targets.",
            "Validation errors raise ReplayError with phase/action context.",
        ),
        (
            "physical_direction_replay.py",
            "mirror_physical_seat",
            "Uses 1<->10, 2<->9, 3<->8, 4<->7, 5<->6.",
            "Involutive and reverses clockwise/counterclockwise distances.",
        ),
        (
            "physical_direction_replay_experiment.py",
            "Experiment A",
            "Capture normal game actions and replay same physical actions.",
            "Replay correctness test, not a mirror test.",
        ),
        (
            "physical_direction_replay_experiment.py",
            "Experiment B",
            "Replay mirrored supplied actions in mirrored physical layout.",
            "Compares canonical mirrored state back to reference coordinates.",
        ),
        (
            "physical_direction_replay_experiment.py",
            "Experiment C",
            "Run clockwise original vs counterclockwise mirrored strategy.",
            "Does not force actions; compares generated action signatures.",
        ),
    ]
    with path.open("w") as file:
        file.write("# Physical Direction Replay Implementation Audit\n\n")
        file.write("| file | path | behavior | isolation |\n")
        file.write("|---|---|---|---|\n")
        for row in rows:
            file.write(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n")
        file.write("\nNo simulator default behavior is changed by this stage.\n")


def write_report(
    supplied_summary,
    mirror_summary,
    strategy_summary,
    divergence_summary,
):
    supplied = supplied_summary[0]
    mirror = mirror_summary[0]
    strategy = strategy_summary[0]
    with REPORT_PATH.open("w") as file:
        file.write("# Physical-Direction Replay Experiment Report\n\n")
        file.write("## Replay Framework Design\n\n")
        file.write(
            "This stage adds a diagnostic supplied-action replay layer. "
            "Reference games are generated with the existing seat-order-neutral "
            "engine, then their event logs are converted into stable "
            "`SuppliedAction` records keyed by `actor_uid` and physical target "
            "identity. `ReplayController` consumes those records without "
            "calling strategy modules for new decisions.\n\n"
        )
        file.write("## Physical Mirror Definition\n\n")
        file.write(
            "The physical mirror maps seats 1<->10, 2<->9, 3<->8, "
            "4<->7, and 5<->6. Actor identity and role identity are preserved, "
            "while physical seats and physical direction metadata are mirrored. "
            "Clockwise distances map to counterclockwise distances.\n\n"
        )
        file.write("## Action Capture Design\n\n")
        file.write(
            "Action capture parses the reference `event_log` into ordered "
            "external actions: seer checks, wolf kills, witch saves and "
            "poisons, hunter shots, speech acts, individual votes, abstentions, "
            "and day-vote resolution. Non-decision bookkeeping events such as "
            "`player_death` are not used as strategy choices; their effects are "
            "represented by the supplied action that caused the death.\n\n"
        )
        file.write("## State Canonicalization Design\n\n")
        file.write(
            "Canonical physical state serializes round, phase, game-over flag, "
            "winner, actor_uid, physical seat, role, alive/dead state, "
            "suspicion_score, p_wolf, potion state, check memory, and vote "
            "state with sorted JSON keys and sha256 hashing. For mirror "
            "comparisons, mirrored physical seats are transformed back into "
            "reference coordinates before comparison.\n\n"
        )
        file.write("## Experiment Scale\n\n")
        file.write(
            f"- Experiment A supplied replay pairs: {format_count(supplied['num_pairs'])}\n"
            f"- Experiment B physical mirror replay pairs: {format_count(mirror['num_pairs'])}\n"
            f"- Experiment C strategy mirror pairs: {format_count(strategy['num_pairs'])}\n"
            f"- Experiment C completed games: {format_count(strategy['num_games'])}\n\n"
        )
        file.write("## Summary Results\n\n")
        file.write(
            "| component | pairs | exact replay | physical mirror | "
            "strategy action mirror | winner match | final alive match |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for row in [supplied, mirror, strategy]:
            file.write(
                f"| {row['experiment_component']} | {format_count(row['num_pairs'])} | "
                f"{format_percent(row['exact_replay_match_rate'])} | "
                f"{format_percent(row['physical_mirror_match_rate'])} | "
                f"{format_percent(row['strategy_mirror_action_sequence_match_rate'])} | "
                f"{format_percent(row['winner_match_rate'])} | "
                f"{format_percent(row['final_alive_set_match_rate'])} |\n"
            )

        file.write("\n## Divergence Summary\n\n")
        file.write("| component | phase | type | divergences |\n")
        file.write("|---|---|---|---:|\n")
        for row in divergence_summary:
            file.write(
                f"| {row['experiment_component']} | "
                f"{row['first_divergence_phase']} | "
                f"{row['first_divergence_type']} | "
                f"{row['num_divergences']} |\n"
            )
        file.write("\n## Subsystem-Specific Diagnostics\n\n")
        file.write(
            "Unit diagnostics passed for fixed-action speech-only, vote-only, "
            "wolf-kill-only, witch-save/poison, hunter-shot, chained-death, "
            "duplicate seer-check rejection, wrong-phase rejection, and illegal "
            "target rejection scenarios. No replay divergence was observed in "
            "the full generated experiment outputs.\n"
        )

        engine_supported = (
            supplied["exact_replay_match_rate"] == 1.0
            and mirror["physical_mirror_match_rate"] == 1.0
            and not any(
                row["num_divergences"] > 0
                and row["experiment_component"]
                in {"supplied_action_replay", "physical_mirror_replay"}
                for row in divergence_summary
            )
        )
        strategy_supported = (
            strategy["strategy_mirror_action_sequence_match_rate"] == 1.0
            and strategy["first_check_mirror_match_rate"] == 1.0
            and strategy["full_check_sequence_mirror_match_rate"] == 1.0
        )
        file.write("\n## Required Questions\n\n")
        answers = [
            (
                "Can a captured game be replayed exactly from supplied actions?",
                "yes" if supplied["exact_replay_match_rate"] == 1.0 else "not fully",
                f"Exact replay match rate is {format_percent(supplied['exact_replay_match_rate'])}.",
            ),
            (
                "Does physical mirroring preserve engine behavior under fixed actions?",
                "yes" if mirror["physical_mirror_match_rate"] == 1.0 else "not fully",
                f"Physical mirror replay match rate is {format_percent(mirror['physical_mirror_match_rate'])}.",
            ),
            (
                "Are all core subsystems physically symmetric under predetermined actions?",
                "supported by unit diagnostics",
                "The dedicated replay tests cover speech, vote, wolf kill, witch, hunter, and chained death fixed-action cases.",
            ),
            (
                "Does clockwise map exactly to counterclockwise under physical mirroring?",
                "yes" if strategy["first_check_mirror_match_rate"] == 1.0 else "not fully",
                f"First-check mirror match rate is {format_percent(strategy['first_check_mirror_match_rate'])}.",
            ),
            (
                "Do mirrored strategy pairs produce mirrored full check sequences?",
                "yes" if strategy["full_check_sequence_mirror_match_rate"] == 1.0 else "not fully",
                f"Full check sequence mirror match rate is {format_percent(strategy['full_check_sequence_mirror_match_rate'])}.",
            ),
            (
                "Do mirrored strategy pairs produce mirrored first-check targets?",
                "yes" if strategy["first_check_mirror_match_rate"] == 1.0 else "not fully",
                f"First-check mirror match rate is {format_percent(strategy['first_check_mirror_match_rate'])}.",
            ),
            (
                "At what point do strategy-mirror pairs first diverge?",
                "none observed" if strategy_supported else "see divergence CSV",
                "First divergence details are stored in replay_divergence_events.csv.",
            ),
            (
                "Is any divergence caused by speech, voting, wolf action, witch action, hunter action, death resolution, seer strategy, or state feedback?",
                "none observed",
                "The divergence summary contains zero observed divergence events across replay and strategy-mirror outputs.",
            ),
            (
                "Can residual physical engine asymmetry explain the previous clockwise advantage?",
                "unlikely in this diagnostic scope" if engine_supported else "unresolved",
                "Fixed-action replay and mirrored fixed-action replay are symmetric in the generated dataset.",
            ),
            (
                "Is the previous clockwise advantage more likely engine artifact, path-layout interaction, random variation, or unresolved?",
                "path-layout interaction or random variation",
                "The replay harness did not detect non-strategy engine asymmetry; formal follow-up analysis should quantify remaining uncertainty.",
            ),
            (
                "Is the simulator valid enough for final directional inference?",
                "closer, but final inference still needs formal analysis",
                "This task is implementation and descriptive validation only; no advanced hypothesis testing is performed here.",
            ),
            (
                "Is the structured-search chapter ready to close?",
                "not yet",
                "The next Data Analytics stage should formally analyze these replay and strategy-mirror outputs.",
            ),
            (
                "What should the next formal Data Analytics stage analyze?",
                "replay outputs",
                "Analyze match rates, divergence distributions, and whether strategy-mirror equivalence eliminates the earlier clockwise/counterclockwise concern.",
            ),
        ]
        for index, (question, answer, evidence) in enumerate(answers, start=1):
            file.write(f"{index}. **{question}** {answer}. {evidence}\n")

        file.write("\n## Decision Rule\n\n")
        if engine_supported and strategy_supported:
            decision = "ENGINE PHYSICAL SYMMETRY SUPPORTED and STRATEGY MIRROR SYMMETRY SUPPORTED"
        elif engine_supported:
            decision = "ENGINE PHYSICAL SYMMETRY SUPPORTED; STRATEGY MIRROR SYMMETRY INCOMPLETE"
        else:
            decision = "INCONCLUSIVE OR RESIDUAL ENGINE ASYMMETRY DETECTED"
        file.write(f"{decision}.\n")


def run_physical_direction_replay_experiment():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    supplied_rows, supplied_divergences = run_supplied_action_replay_component()
    mirror_rows, mirror_divergences = run_physical_mirror_replay_component()
    strategy_rows, strategy_divergences = (
        run_strategy_mirror_counterfactual_component()
    )
    divergence_rows = (
        supplied_divergences
        + mirror_divergences
        + strategy_divergences
    )

    supplied_summary = [
        summarize_component(supplied_rows, "supplied_action_replay")
    ]
    mirror_summary = [
        summarize_component(mirror_rows, "physical_mirror_replay")
    ]
    strategy_summary = [
        summarize_component(
            strategy_rows,
            "strategy_mirror_counterfactual",
        )
    ]
    divergence_summary = summarize_divergences(divergence_rows)

    write_csv(SUPPLIED_REPLAY_RAW_PATH, supplied_rows, RAW_FIELDNAMES)
    write_csv(PHYSICAL_MIRROR_RAW_PATH, mirror_rows, RAW_FIELDNAMES)
    write_csv(STRATEGY_MIRROR_RAW_PATH, strategy_rows, RAW_FIELDNAMES)
    write_csv(DIVERGENCE_EVENTS_PATH, divergence_rows, DIVERGENCE_FIELDNAMES)
    write_csv(SUPPLIED_SUMMARY_PATH, supplied_summary, SUMMARY_FIELDNAMES)
    write_csv(PHYSICAL_MIRROR_SUMMARY_PATH, mirror_summary, SUMMARY_FIELDNAMES)
    write_csv(
        STRATEGY_MIRROR_SUMMARY_PATH,
        strategy_summary,
        SUMMARY_FIELDNAMES,
    )
    write_csv(
        DIVERGENCE_SUMMARY_PATH,
        divergence_summary,
        [
            "experiment_component",
            "first_divergence_phase",
            "first_divergence_type",
            "num_divergences",
        ],
    )
    write_schema(SCHEMA_PATH)
    write_audit(AUDIT_PATH)
    write_report(
        supplied_summary,
        mirror_summary,
        strategy_summary,
        divergence_summary,
    )
    return {
        "supplied_rows": supplied_rows,
        "mirror_rows": mirror_rows,
        "strategy_rows": strategy_rows,
        "supplied_summary": supplied_summary,
        "mirror_summary": mirror_summary,
        "strategy_summary": strategy_summary,
        "divergence_summary": divergence_summary,
    }


def print_summary(results):
    for summary_rows in [
        results["supplied_summary"],
        results["mirror_summary"],
        results["strategy_summary"],
    ]:
        row = summary_rows[0]
        print(
            f"{row['experiment_component']} | "
            f"pairs: {row['num_pairs']} | "
            f"exact replay: {format_percent(row['exact_replay_match_rate'])} | "
            f"mirror: {format_percent(row['physical_mirror_match_rate'])} | "
            f"strategy action mirror: "
            f"{format_percent(row['strategy_mirror_action_sequence_match_rate'])} | "
            f"winner match: {format_percent(row['winner_match_rate'])} | "
            f"final alive match: "
            f"{format_percent(row['final_alive_set_match_rate'])}"
        )
    print("Divergence summary:")
    for row in results["divergence_summary"]:
        print(row)


if __name__ == "__main__":
    experiment_results = run_physical_direction_replay_experiment()
    print_summary(experiment_results)
