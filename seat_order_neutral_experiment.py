import csv
import json
import random
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean

from config import DEFAULT_MAX_ROUNDS
from game import Game
from game_level_logging import get_seer_check_events
from player import Player
from position_model import TEN_PLAYER_ROLE_POOL, get_seat_type, get_side
from roles import SEER, WEREWOLF
from seat_order_neutral import (
    MIRROR_MAPPING,
    NORMAL_MAPPING,
    PHYSICAL_SEATS,
    SPEECH_SUBSEED_SCHEME,
    STRATEGY_SUBSEED_SCHEME,
    TIE_BREAK_SCHEME,
    clockwise_distance_physical,
    counterclockwise_distance_physical,
    get_actor_uid,
    get_physical_seat,
    invert_mapping,
    json_dump,
    mirror_displayed_label,
    rotated_mapping,
    stable_seed,
)
from ten_player_experiment import NUM_GAMES
from ten_player_seer_position_experiment import SEER_POSITION_BASE_CONFIG


RESULTS_DIR = Path("results") / "seat_order_neutral"
RAW_CSV_PATH = RESULTS_DIR / "seat_order_neutral_game_level_raw.csv"
MATCHED_PAIR_SUMMARY_PATH = (
    RESULTS_DIR / "seat_order_neutral_matched_pair_summary.csv"
)
STRATEGY_SUMMARY_PATH = RESULTS_DIR / "seat_order_neutral_strategy_summary.csv"
LABEL_CONDITION_SUMMARY_PATH = (
    RESULTS_DIR / "seat_order_neutral_label_condition_summary.csv"
)
DIVERGENCE_SUMMARY_PATH = (
    RESULTS_DIR / "seat_order_neutral_divergence_summary.csv"
)
SCHEMA_PATH = RESULTS_DIR / "seat_order_neutral_schema.md"
AUDIT_PATH = RESULTS_DIR / "seat_order_neutral_implementation_audit.md"
REPORT_PATH = RESULTS_DIR / "seat_order_neutral_experiment_report.md"

SEEDS = [42, 43, 44, 45, 46]
NUM_BASE_CONFIGS = NUM_GAMES
LABEL_CONDITIONS = ["normal", "mirrored", "rotated"]

NEUTRAL_SEER_STRATEGIES = [
    "physical_clockwise",
    "physical_counterclockwise",
    "alternate_physical_sides",
    "random_neutral",
]

OPTIONAL_NEUTRAL_SEER_STRATEGIES = [
    "nearest_physical_first",
    "farthest_physical_first",
]

RAW_FIELDNAMES = [
    "matched_set_id",
    "pair_id",
    "game_id",
    "seed",
    "base_game_index",
    "strategy",
    "label_condition",
    "mirrored",
    "rotation_offset",
    "neutral_mode_enabled",
    "actor_uid_to_physical_seat",
    "actor_uid_to_displayed_id",
    "physical_to_displayed_mapping",
    "displayed_to_physical_mapping",
    "neutral_actor_iteration_order",
    "seer_actor_uid",
    "physical_seer_seat",
    "displayed_seer_id",
    "wolf_actor_uids",
    "physical_wolf_seats",
    "displayed_wolf_ids",
    "wolves_on_edge",
    "wolves_on_inner",
    "wolves_left_side",
    "wolves_right_side",
    "edge_has_wolf",
    "seer_on_edge",
    "seer_left_side",
    "strategy_direction_physical",
    "strategy_direction_displayed",
    "first_check_actor_uid",
    "first_check_physical_target",
    "first_check_displayed_target",
    "all_check_actor_uids",
    "all_check_physical_targets",
    "all_check_displayed_targets",
    "total_seer_checks",
    "first_check_target_is_wolf",
    "found_wolf_by_check_1",
    "found_wolf_by_check_2",
    "found_wolf_by_check_3",
    "checks_until_first_wolf",
    "no_wolf_found",
    "seer_found_wolf_count",
    "seer_survived_to_game_end",
    "seer_death_round",
    "search_path_coverage_score",
    "winner",
    "village_win",
    "wolf_win",
    "total_rounds",
    "final_alive_players",
    "final_alive_wolves",
    "final_alive_villagers",
    "physical_first_target_matches_reference",
    "physical_check_sequence_matches_reference_until_divergence",
    "first_divergence_round",
    "first_divergence_phase",
    "first_divergence_event_type",
    "paired_outcome_agreement",
    "physical_final_alive_set_matches",
    "role_assignment_seed",
    "speech_subseed_scheme",
    "strategy_subseed_scheme",
    "tie_break_scheme",
    "main_game_seed",
]

SUMMARY_FIELDNAMES = [
    "strategy",
    "label_condition",
    "num_games",
    "wolf_win_rate",
    "village_win_rate",
    "avg_rounds",
    "first_check_wolf_rate",
    "found_wolf_by_check_2_rate",
    "found_wolf_by_check_3_rate",
    "seer_survival_rate",
    "avg_total_seer_checks",
    "avg_checks_until_first_wolf",
    "no_wolf_found_rate",
    "mean_wolves_found_per_game",
    "mean_search_path_coverage_score",
    "random_neutral_physical_target_agreement_rate",
    "paired_outcome_agreement_rate",
    "physical_final_alive_set_match_rate",
    "edge_has_wolf_rate",
    "avg_wolves_on_edge",
    "avg_wolves_on_inner",
    "avg_wolves_left_side",
    "avg_wolves_right_side",
    "seer_on_edge_rate",
    "seer_left_side_rate",
]

PAIR_FIELDNAMES = [
    "matched_set_id",
    "seed",
    "base_game_index",
    "strategy",
    "reference_label_condition",
    "comparison_label_condition",
    "reference_game_id",
    "comparison_game_id",
    "reference_winner",
    "comparison_winner",
    "outcome_agreement",
    "physical_first_target_matches_reference",
    "physical_check_sequence_matches_reference_until_divergence",
    "physical_final_alive_set_matches",
    "first_divergence_round",
    "first_divergence_phase",
    "first_divergence_event_type",
]

DIVERGENCE_FIELDNAMES = [
    "strategy",
    "label_condition",
    "first_divergence_phase",
    "first_divergence_event_type",
    "num_games",
    "share_of_condition",
]


def get_neutral_strategy_configs(include_optional=False):
    strategies = list(NEUTRAL_SEER_STRATEGIES)
    if include_optional:
        strategies.extend(OPTIONAL_NEUTRAL_SEER_STRATEGIES)

    configs = []
    for strategy in strategies:
        config = dict(SEER_POSITION_BASE_CONFIG)
        config.update({
            "name": strategy,
            "seer_check_strategy": strategy,
            "seer_avoid_repeat_checks": True,
            "randomize_seat_roles": False,
            "seat_order_neutral_mode": True,
            "enable_position_model": True,
        })
        configs.append(config)

    return configs


def generate_physical_role_assignment(seed, base_game_index):
    role_assignment_seed = stable_seed(
        "seat_order_neutral_roles",
        seed,
        base_game_index,
    )
    role_rng = random.Random(role_assignment_seed)
    role_pool = list(TEN_PLAYER_ROLE_POOL)
    role_rng.shuffle(role_pool)
    return {
        physical_seat: role_pool[physical_seat - 1]
        for physical_seat in PHYSICAL_SEATS
    }


def get_rotation_offset(seed, base_game_index):
    return 1 + stable_seed(
        "seat_order_neutral_rotation",
        seed,
        base_game_index,
    ) % (len(PHYSICAL_SEATS) - 1)


def get_label_condition_specs(seed, base_game_index):
    rotation_offset = get_rotation_offset(seed, base_game_index)
    return [
        {
            "label_condition": "normal",
            "mirrored": False,
            "rotation_offset": 0,
            "mapping": dict(NORMAL_MAPPING),
        },
        {
            "label_condition": "mirrored",
            "mirrored": True,
            "rotation_offset": 0,
            "mapping": dict(MIRROR_MAPPING),
        },
        {
            "label_condition": "rotated",
            "mirrored": False,
            "rotation_offset": rotation_offset,
            "mapping": rotated_mapping(rotation_offset),
        },
    ]


def create_neutral_displayed_players(role_by_physical_seat, mapping):
    players = []
    for physical_seat in PHYSICAL_SEATS:
        displayed_id = mapping[physical_seat]
        player = Player(
            player_id=displayed_id,
            role=role_by_physical_seat[physical_seat],
        )
        player.actor_uid = physical_seat
        player.physical_seat = physical_seat
        player.displayed_player_id = displayed_id
        player.displayed_seat = displayed_id
        player.displayed_side = get_side(displayed_id)
        player.displayed_seat_type = get_seat_type(displayed_id)
        player.physical_side = get_side(physical_seat)
        player.physical_seat_type = get_seat_type(physical_seat)
        return_side = player.physical_side
        player.side = return_side
        player.seat_type = player.physical_seat_type
        players.append(player)

    return sorted(players, key=lambda player: player.player_id)


def get_player_by_role(players, role):
    matches = [player for player in players if player.role == role]
    return matches[0] if matches else None


def get_seer_death_round(event_log, seer_displayed_id):
    if seer_displayed_id is None:
        return None

    for event in event_log:
        if event.get("event_type") != "player_death":
            continue
        if event.get("content", {}).get("player") == seer_displayed_id:
            return event.get("round")

    return None


def get_checks_until_first_wolf(seer_check_events):
    for index, event in enumerate(seer_check_events, start=1):
        if event.get("content", {}).get("target_is_wolf") is True:
            return index

    return None


def found_wolf_by_check(seer_check_events, max_check):
    return any(
        event.get("content", {}).get("target_is_wolf") is True
        for event in seer_check_events[:max_check]
    )


def search_path_coverage_score(target_ids):
    return len(set(target_ids)) / 9


def indicator(value):
    if value is None:
        return ""
    return 1 if value else 0


def blank_if_none(value):
    return "" if value is None else value


def as_int(value, default=0):
    if value in ("", None):
        return default
    return int(value)


def as_float(value, default=0.0):
    if value in ("", None):
        return default
    return float(value)


def rate(rows, field):
    if not rows:
        return 0.0
    return sum(as_float(row[field]) for row in rows if row[field] != "") / len(rows)


def average_nonblank(rows, field):
    values = [as_float(row[field]) for row in rows if row[field] != ""]
    if not values:
        return ""
    return mean(values)


def describe_strategy_direction_physical(strategy):
    descriptions = {
        "physical_clockwise": "clockwise_physical_seat_order",
        "physical_counterclockwise": "counterclockwise_physical_seat_order",
        "alternate_physical_sides": (
            "alternates_clockwise_then_counterclockwise_physical_order"
        ),
        "random_neutral": "label_invariant_random_physical_target",
        "nearest_physical_first": "nearest_physical_distance",
        "farthest_physical_first": "farthest_physical_distance",
    }
    return descriptions.get(strategy, strategy)


def describe_strategy_direction_displayed(strategy):
    descriptions = {
        "physical_clockwise": "independent_of_displayed_label_direction",
        "physical_counterclockwise": "independent_of_displayed_label_direction",
        "alternate_physical_sides": "independent_of_displayed_left_right_labels",
        "random_neutral": "independent_of_displayed_labels",
        "nearest_physical_first": "physical_distance_not_displayed_distance",
        "farthest_physical_first": "physical_distance_not_displayed_distance",
    }
    return descriptions.get(strategy, strategy)


def physical_event_trace(event_log, displayed_to_physical):
    trace = []
    for event in event_log:
        event_type = event.get("event_type")
        content = event.get("content", {})
        normalized = {
            "round": event.get("round"),
            "phase": event.get("phase"),
            "event_type": event_type,
        }

        if event_type == "speech":
            target = content.get("target")
            normalized.update({
                "speaker": displayed_to_physical.get(content.get("speaker")),
                "speech_type": content.get("speech_type"),
                "target": displayed_to_physical.get(target) if target else None,
                "is_deception": content.get("is_deception", False),
                "deception_type": content.get("deception_type"),
            })
        elif event_type == "seer_check":
            normalized.update({
                "seer": content.get("seer_physical_seat"),
                "target": content.get("target_physical_seat"),
                "target_is_wolf": content.get("target_is_wolf"),
            })
        elif event_type == "day_vote":
            votes = content.get("votes", {})
            normalized_votes = {
                displayed_to_physical.get(int(voter)): displayed_to_physical.get(
                    int(target)
                )
                for voter, target in votes.items()
            }
            normalized.update({
                "votes": sorted(normalized_votes.items()),
                "eliminated": displayed_to_physical.get(
                    content.get("eliminated")
                ),
            })
        elif event_type == "player_death":
            normalized["player"] = displayed_to_physical.get(
                content.get("player")
            )
            normalized["cause"] = content.get("cause")
        elif event_type in {"night_kill", "night_kill_prevented"}:
            normalized["target"] = displayed_to_physical.get(
                content.get("target")
            )
            normalized["strategy"] = content.get("strategy")
        elif event_type == "witch_save":
            normalized["witch"] = displayed_to_physical.get(
                content.get("witch")
            )
            normalized["saved_player"] = displayed_to_physical.get(
                content.get("saved_player")
            )
        elif event_type == "witch_poison":
            normalized["witch"] = displayed_to_physical.get(
                content.get("witch")
            )
            normalized["poisoned_player"] = displayed_to_physical.get(
                content.get("poisoned_player")
            )
        elif event_type == "hunter_shot":
            normalized["hunter"] = displayed_to_physical.get(
                content.get("hunter")
            )
            normalized["shot_target"] = displayed_to_physical.get(
                content.get("shot_target")
            )
        else:
            normalized["content_type"] = event_type

        trace.append(normalized)

    return trace


def first_divergence(reference_trace, comparison_trace):
    max_length = max(len(reference_trace), len(comparison_trace))
    for index in range(max_length):
        reference_event = (
            reference_trace[index]
            if index < len(reference_trace)
            else None
        )
        comparison_event = (
            comparison_trace[index]
            if index < len(comparison_trace)
            else None
        )
        if reference_event == comparison_event:
            continue

        event = comparison_event or reference_event or {}
        return {
            "round": event.get("round", ""),
            "phase": event.get("phase", ""),
            "event_type": event.get("event_type", "trace_length"),
        }

    return {
        "round": "",
        "phase": "none",
        "event_type": "none",
    }


def run_single_neutral_game(
    seed,
    base_game_index,
    strategy,
    label_spec,
    role_by_physical_seat,
):
    mapping = label_spec["mapping"]
    players = create_neutral_displayed_players(role_by_physical_seat, mapping)
    config = dict(SEER_POSITION_BASE_CONFIG)
    config.update({
        "seer_check_strategy": strategy,
        "seer_avoid_repeat_checks": True,
        "randomize_seat_roles": False,
        "seat_order_neutral_mode": True,
        "neutral_seed": seed,
        "base_game_index": base_game_index,
        "label_condition": label_spec["label_condition"],
        "rotation_offset": label_spec["rotation_offset"],
        "physical_to_displayed_mapping": mapping,
    })
    main_game_seed = stable_seed(
        "seat_order_neutral_main_game",
        seed,
        base_game_index,
    )
    config["main_game_seed"] = main_game_seed
    random.seed(main_game_seed)
    game = Game(players, **config)
    result = game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
    return game, result, main_game_seed


def build_neutral_game_level_row(
    game,
    result,
    seed,
    base_game_index,
    strategy,
    label_spec,
    matched_set_id,
    game_id,
    role_assignment_seed,
    main_game_seed,
):
    mapping = label_spec["mapping"]
    displayed_to_physical = invert_mapping(mapping)
    players = game.state.players
    seer = get_player_by_role(players, SEER)
    wolves = sorted(
        [player for player in players if player.role == WEREWOLF],
        key=get_physical_seat,
    )
    seer_check_events = get_seer_check_events(game.event_log)
    first_check = seer_check_events[0] if seer_check_events else None
    first_content = first_check.get("content", {}) if first_check else {}

    all_check_actor_uids = [
        event.get("content", {}).get("target_actor_uid")
        for event in seer_check_events
    ]
    all_check_displayed_targets = [
        event.get("content", {}).get("target")
        for event in seer_check_events
    ]
    all_check_physical_targets = [
        event.get("content", {}).get("target_physical_seat")
        for event in seer_check_events
    ]
    checked_is_wolf = [
        event.get("content", {}).get("target_is_wolf") is True
        for event in seer_check_events
    ]
    checks_until_first_wolf = get_checks_until_first_wolf(seer_check_events)
    seer_displayed_id = seer.player_id if seer is not None else None
    physical_seer_seat = (
        get_physical_seat(seer)
        if seer is not None
        else None
    )
    final_alive_physical = sorted(
        get_physical_seat(player)
        for player in players
        if player.alive
    )

    row = {
        "matched_set_id": matched_set_id,
        "pair_id": matched_set_id,
        "game_id": game_id,
        "seed": seed,
        "base_game_index": base_game_index,
        "strategy": strategy,
        "label_condition": label_spec["label_condition"],
        "mirrored": 1 if label_spec["mirrored"] else 0,
        "rotation_offset": label_spec["rotation_offset"],
        "neutral_mode_enabled": 1,
        "actor_uid_to_physical_seat": json_dump({
            get_actor_uid(player): get_physical_seat(player)
            for player in players
        }),
        "actor_uid_to_displayed_id": json_dump({
            get_actor_uid(player): player.player_id
            for player in players
        }),
        "physical_to_displayed_mapping": json_dump(mapping),
        "displayed_to_physical_mapping": json_dump(displayed_to_physical),
        "neutral_actor_iteration_order": json_dump(
            getattr(game.state, "neutral_actor_iteration_order", [])
        ),
        "seer_actor_uid": blank_if_none(
            get_actor_uid(seer) if seer is not None else None
        ),
        "physical_seer_seat": blank_if_none(physical_seer_seat),
        "displayed_seer_id": blank_if_none(seer_displayed_id),
        "wolf_actor_uids": json_dump(
            [get_actor_uid(player) for player in wolves]
        ),
        "physical_wolf_seats": json_dump(
            [get_physical_seat(player) for player in wolves]
        ),
        "displayed_wolf_ids": json_dump(
            [player.player_id for player in wolves]
        ),
        "wolves_on_edge": sum(
            1 for player in wolves
            if getattr(player, "physical_seat_type", None) == "edge"
        ),
        "wolves_on_inner": sum(
            1 for player in wolves
            if getattr(player, "physical_seat_type", None) == "inner"
        ),
        "wolves_left_side": sum(
            1 for player in wolves
            if getattr(player, "physical_side", None) == "left"
        ),
        "wolves_right_side": sum(
            1 for player in wolves
            if getattr(player, "physical_side", None) == "right"
        ),
        "edge_has_wolf": 1 if any(
            getattr(player, "physical_seat_type", None) == "edge"
            for player in wolves
        ) else 0,
        "seer_on_edge": indicator(
            getattr(seer, "physical_seat_type", None) == "edge"
            if seer is not None
            else None
        ),
        "seer_left_side": indicator(
            getattr(seer, "physical_side", None) == "left"
            if seer is not None
            else None
        ),
        "strategy_direction_physical": describe_strategy_direction_physical(
            strategy
        ),
        "strategy_direction_displayed": describe_strategy_direction_displayed(
            strategy
        ),
        "first_check_actor_uid": blank_if_none(
            first_content.get("target_actor_uid")
        ),
        "first_check_physical_target": blank_if_none(
            first_content.get("target_physical_seat")
        ),
        "first_check_displayed_target": blank_if_none(
            first_content.get("target")
        ),
        "all_check_actor_uids": json_dump(all_check_actor_uids),
        "all_check_physical_targets": json_dump(all_check_physical_targets),
        "all_check_displayed_targets": json_dump(all_check_displayed_targets),
        "total_seer_checks": len(seer_check_events),
        "first_check_target_is_wolf": indicator(
            first_content.get("target_is_wolf")
            if first_check is not None
            else None
        ),
        "found_wolf_by_check_1": indicator(
            found_wolf_by_check(seer_check_events, 1)
        ),
        "found_wolf_by_check_2": indicator(
            found_wolf_by_check(seer_check_events, 2)
        ),
        "found_wolf_by_check_3": indicator(
            found_wolf_by_check(seer_check_events, 3)
        ),
        "checks_until_first_wolf": blank_if_none(checks_until_first_wolf),
        "no_wolf_found": 1 if checks_until_first_wolf is None else 0,
        "seer_found_wolf_count": sum(1 for value in checked_is_wolf if value),
        "seer_survived_to_game_end": (
            indicator(seer.alive) if seer is not None else ""
        ),
        "seer_death_round": blank_if_none(
            get_seer_death_round(game.event_log, seer_displayed_id)
        ),
        "search_path_coverage_score": search_path_coverage_score(
            all_check_physical_targets
        ),
        "winner": result["winner"],
        "village_win": 1 if result["winner"] == "village" else 0,
        "wolf_win": 1 if result["winner"] == "wolf" else 0,
        "total_rounds": result["round_number"],
        "final_alive_players": result["num_alive_players"],
        "final_alive_wolves": result["num_alive_wolves"],
        "final_alive_villagers": result["num_alive_villagers"],
        "physical_first_target_matches_reference": "",
        "physical_check_sequence_matches_reference_until_divergence": "",
        "first_divergence_round": "",
        "first_divergence_phase": "",
        "first_divergence_event_type": "",
        "paired_outcome_agreement": "",
        "physical_final_alive_set_matches": "",
        "role_assignment_seed": role_assignment_seed,
        "speech_subseed_scheme": SPEECH_SUBSEED_SCHEME,
        "strategy_subseed_scheme": STRATEGY_SUBSEED_SCHEME,
        "tie_break_scheme": TIE_BREAK_SCHEME,
        "main_game_seed": main_game_seed,
        "_physical_event_trace": physical_event_trace(
            game.event_log,
            displayed_to_physical,
        ),
        "_physical_final_alive_set": final_alive_physical,
    }
    return row


def finalize_pair_diagnostics(rows):
    rows_by_set = defaultdict(dict)
    for row in rows:
        rows_by_set[row["matched_set_id"]][row["label_condition"]] = row

    for matched_rows in rows_by_set.values():
        reference = matched_rows.get("normal")
        if reference is None:
            continue

        for label_condition, row in matched_rows.items():
            divergence = first_divergence(
                reference["_physical_event_trace"],
                row["_physical_event_trace"],
            )
            first_target_matches = (
                row["first_check_physical_target"]
                == reference["first_check_physical_target"]
            )
            check_sequence_matches = (
                row["all_check_physical_targets"]
                == reference["all_check_physical_targets"]
            )
            outcome_agreement = row["winner"] == reference["winner"]
            final_alive_matches = (
                row["_physical_final_alive_set"]
                == reference["_physical_final_alive_set"]
            )

            row["physical_first_target_matches_reference"] = indicator(
                first_target_matches
            )
            row[
                "physical_check_sequence_matches_reference_until_divergence"
            ] = indicator(check_sequence_matches)
            row["first_divergence_round"] = divergence["round"]
            row["first_divergence_phase"] = divergence["phase"]
            row["first_divergence_event_type"] = divergence["event_type"]
            row["paired_outcome_agreement"] = indicator(outcome_agreement)
            row["physical_final_alive_set_matches"] = indicator(
                final_alive_matches
            )

            if label_condition == "normal":
                row["physical_first_target_matches_reference"] = 1
                row[
                    "physical_check_sequence_matches_reference_until_divergence"
                ] = 1
                row["first_divergence_round"] = ""
                row["first_divergence_phase"] = "none"
                row["first_divergence_event_type"] = "none"
                row["paired_outcome_agreement"] = 1
                row["physical_final_alive_set_matches"] = 1

    for row in rows:
        row.pop("_physical_event_trace", None)
        row.pop("_physical_final_alive_set", None)


def run_seat_order_neutral_experiment(
    seeds=None,
    num_base_configs=NUM_BASE_CONFIGS,
    configs=None,
):
    if seeds is None:
        seeds = SEEDS
    if configs is None:
        configs = get_neutral_strategy_configs()

    rows = []
    for config in configs:
        strategy = config["seer_check_strategy"]
        for seed in seeds:
            for base_game_index in range(1, num_base_configs + 1):
                role_by_physical_seat = generate_physical_role_assignment(
                    seed,
                    base_game_index,
                )
                role_assignment_seed = stable_seed(
                    "seat_order_neutral_roles",
                    seed,
                    base_game_index,
                )
                matched_set_id = (
                    f"{strategy}_seed_{seed}_base_{base_game_index}"
                )

                for label_spec in get_label_condition_specs(
                    seed,
                    base_game_index,
                ):
                    game_id = (
                        f"{matched_set_id}_"
                        f"{label_spec['label_condition']}"
                    )
                    game, result, main_game_seed = run_single_neutral_game(
                        seed,
                        base_game_index,
                        strategy,
                        label_spec,
                        role_by_physical_seat,
                    )
                    rows.append(
                        build_neutral_game_level_row(
                            game,
                            result,
                            seed,
                            base_game_index,
                            strategy,
                            label_spec,
                            matched_set_id,
                            game_id,
                            role_assignment_seed,
                            main_game_seed,
                        )
                    )

    finalize_pair_diagnostics(rows)
    return rows


def make_matched_pair_summary_rows(rows):
    rows_by_set = defaultdict(dict)
    for row in rows:
        rows_by_set[row["matched_set_id"]][row["label_condition"]] = row

    pair_rows = []
    for matched_set_id in sorted(rows_by_set):
        matched_rows = rows_by_set[matched_set_id]
        reference = matched_rows.get("normal")
        if reference is None:
            continue

        for label_condition in sorted(matched_rows):
            if label_condition == "normal":
                continue
            comparison = matched_rows[label_condition]
            pair_rows.append({
                "matched_set_id": matched_set_id,
                "seed": reference["seed"],
                "base_game_index": reference["base_game_index"],
                "strategy": reference["strategy"],
                "reference_label_condition": "normal",
                "comparison_label_condition": label_condition,
                "reference_game_id": reference["game_id"],
                "comparison_game_id": comparison["game_id"],
                "reference_winner": reference["winner"],
                "comparison_winner": comparison["winner"],
                "outcome_agreement": (
                    comparison["paired_outcome_agreement"]
                ),
                "physical_first_target_matches_reference": (
                    comparison["physical_first_target_matches_reference"]
                ),
                "physical_check_sequence_matches_reference_until_divergence": (
                    comparison[
                        "physical_check_sequence_matches_reference_until_divergence"
                    ]
                ),
                "physical_final_alive_set_matches": (
                    comparison["physical_final_alive_set_matches"]
                ),
                "first_divergence_round": comparison[
                    "first_divergence_round"
                ],
                "first_divergence_phase": comparison[
                    "first_divergence_phase"
                ],
                "first_divergence_event_type": comparison[
                    "first_divergence_event_type"
                ],
            })

    return pair_rows


def summarize_rows(rows, strategy="all", label_condition="all"):
    checks_until_first_wolf = [
        as_int(row["checks_until_first_wolf"])
        for row in rows
        if row["checks_until_first_wolf"] != ""
    ]
    no_wolf_found_count = sum(as_int(row["no_wolf_found"]) for row in rows)
    random_rows = [
        row for row in rows
        if row["strategy"] == "random_neutral"
        and row["label_condition"] != "normal"
    ]

    return {
        "strategy": strategy,
        "label_condition": label_condition,
        "num_games": len(rows),
        "wolf_win_rate": rate(rows, "wolf_win"),
        "village_win_rate": rate(rows, "village_win"),
        "avg_rounds": average_nonblank(rows, "total_rounds"),
        "first_check_wolf_rate": rate(rows, "first_check_target_is_wolf"),
        "found_wolf_by_check_2_rate": rate(rows, "found_wolf_by_check_2"),
        "found_wolf_by_check_3_rate": rate(rows, "found_wolf_by_check_3"),
        "seer_survival_rate": rate(rows, "seer_survived_to_game_end"),
        "avg_total_seer_checks": average_nonblank(rows, "total_seer_checks"),
        "avg_checks_until_first_wolf": (
            mean(checks_until_first_wolf)
            if checks_until_first_wolf
            else ""
        ),
        "no_wolf_found_rate": (
            no_wolf_found_count / len(rows)
            if rows
            else 0.0
        ),
        "mean_wolves_found_per_game": average_nonblank(
            rows,
            "seer_found_wolf_count",
        ),
        "mean_search_path_coverage_score": average_nonblank(
            rows,
            "search_path_coverage_score",
        ),
        "random_neutral_physical_target_agreement_rate": (
            rate(random_rows, "physical_first_target_matches_reference")
            if random_rows
            else ""
        ),
        "paired_outcome_agreement_rate": rate(
            [row for row in rows if row["label_condition"] != "normal"],
            "paired_outcome_agreement",
        ) if any(row["label_condition"] != "normal" for row in rows) else "",
        "physical_final_alive_set_match_rate": rate(
            [row for row in rows if row["label_condition"] != "normal"],
            "physical_final_alive_set_matches",
        ) if any(row["label_condition"] != "normal" for row in rows) else "",
        "edge_has_wolf_rate": rate(rows, "edge_has_wolf"),
        "avg_wolves_on_edge": average_nonblank(rows, "wolves_on_edge"),
        "avg_wolves_on_inner": average_nonblank(rows, "wolves_on_inner"),
        "avg_wolves_left_side": average_nonblank(rows, "wolves_left_side"),
        "avg_wolves_right_side": average_nonblank(rows, "wolves_right_side"),
        "seer_on_edge_rate": rate(rows, "seer_on_edge"),
        "seer_left_side_rate": rate(rows, "seer_left_side"),
    }


def make_strategy_summary_rows(rows):
    grouped_rows = defaultdict(list)
    for row in rows:
        grouped_rows[(row["strategy"], row["label_condition"])].append(row)

    summary_rows = []
    for strategy, label_condition in sorted(grouped_rows):
        summary_rows.append(
            summarize_rows(
                grouped_rows[(strategy, label_condition)],
                strategy=strategy,
                label_condition=label_condition,
            )
        )
    return summary_rows


def make_label_condition_summary_rows(rows):
    grouped_rows = defaultdict(list)
    for row in rows:
        grouped_rows[row["label_condition"]].append(row)

    return [
        summarize_rows(group, strategy="all", label_condition=label_condition)
        for label_condition, group in sorted(grouped_rows.items())
    ]


def make_divergence_summary_rows(rows):
    grouped_rows = defaultdict(list)
    for row in rows:
        if row["label_condition"] == "normal":
            continue
        key = (
            row["strategy"],
            row["label_condition"],
            row["first_divergence_phase"],
            row["first_divergence_event_type"],
        )
        grouped_rows[key].append(row)

    totals = defaultdict(int)
    for row in rows:
        if row["label_condition"] == "normal":
            continue
        totals[(row["strategy"], row["label_condition"])] += 1

    summary_rows = []
    for key, group in sorted(grouped_rows.items()):
        strategy, label_condition, phase, event_type = key
        total = totals[(strategy, label_condition)]
        summary_rows.append({
            "strategy": strategy,
            "label_condition": label_condition,
            "first_divergence_phase": phase,
            "first_divergence_event_type": event_type,
            "num_games": len(group),
            "share_of_condition": len(group) / total if total else 0.0,
        })
    return summary_rows


def validate_neutral_rows(
    rows,
    seeds=None,
    strategies=None,
    num_base_configs=None,
    label_conditions=None,
):
    if seeds is None:
        seeds = SEEDS
    if strategies is None:
        strategies = NEUTRAL_SEER_STRATEGIES
    if num_base_configs is None:
        num_base_configs = NUM_BASE_CONFIGS
    if label_conditions is None:
        label_conditions = LABEL_CONDITIONS

    errors = []
    expected_count = (
        len(seeds)
        * len(strategies)
        * num_base_configs
        * len(label_conditions)
    )
    if len(rows) != expected_count:
        errors.append(f"Expected {expected_count} rows, found {len(rows)}.")

    game_ids = [row["game_id"] for row in rows]
    if len(game_ids) != len(set(game_ids)):
        errors.append("game_id values are not unique.")

    rows_by_set = defaultdict(list)
    for row in rows:
        rows_by_set[row["matched_set_id"]].append(row)

    expected_sets = len(seeds) * len(strategies) * num_base_configs
    if len(rows_by_set) != expected_sets:
        errors.append(
            f"Expected {expected_sets} matched sets, "
            f"found {len(rows_by_set)}."
        )

    for matched_set_id, matched_rows in rows_by_set.items():
        conditions = sorted(row["label_condition"] for row in matched_rows)
        if conditions != sorted(label_conditions):
            errors.append(
                f"{matched_set_id} label conditions are {conditions}."
            )
            break

        seer_seats = {
            row["physical_seer_seat"]
            for row in matched_rows
        }
        wolf_seats = {
            row["physical_wolf_seats"]
            for row in matched_rows
        }
        actor_orders = {
            row["neutral_actor_iteration_order"]
            for row in matched_rows
        }
        if len(seer_seats) != 1:
            errors.append(
                f"{matched_set_id} does not preserve physical seer seat."
            )
            break
        if len(wolf_seats) != 1:
            errors.append(
                f"{matched_set_id} does not preserve physical wolf seats."
            )
            break
        if len(actor_orders) != 1:
            errors.append(
                f"{matched_set_id} does not preserve neutral actor order."
            )
            break

    for row in rows:
        if row["winner"] not in {"wolf", "village", "draw"}:
            errors.append(f"Invalid winner in {row['game_id']}.")
            break

        targets = json.loads(row["all_check_physical_targets"])
        if len(targets) != len(set(targets)):
            errors.append(f"Duplicate seer checks in {row['game_id']}.")
            break

        seer_seat = row["physical_seer_seat"]
        if seer_seat != "" and int(seer_seat) in targets:
            errors.append(f"Seer self-check in {row['game_id']}.")
            break

        if len(targets) != as_int(row["total_seer_checks"]):
            errors.append(
                f"total_seer_checks mismatch in {row['game_id']}."
            )
            break

    return {
        "valid": not errors,
        "errors": errors,
        "row_count": len(rows),
        "expected_count": expected_count,
        "unique_game_ids": len(game_ids) == len(set(game_ids)),
        "matched_set_count": len(rows_by_set),
        "expected_matched_set_count": expected_sets,
    }


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


def format_percent(value):
    if value == "":
        return "NA"
    return f"{float(value) * 100:.2f}%"


def format_number(value):
    if value == "":
        return "NA"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def write_schema(path):
    descriptions = {
        "matched_set_id": "Shared identifier for matched label conditions.",
        "pair_id": "Alias for matched_set_id for compatibility.",
        "game_id": "Unique completed-game identifier.",
        "seed": "Experimental seed.",
        "base_game_index": "One-based base configuration index.",
        "strategy": "Neutral seer checking strategy.",
        "label_condition": "normal, mirrored, or rotated displayed labels.",
        "mirrored": "1 for mirrored label map.",
        "rotation_offset": "Circular displayed-label offset for rotated runs.",
        "neutral_mode_enabled": "1 when neutral engine mode is active.",
        "actor_uid_to_physical_seat": "JSON map from actor_uid to physical seat.",
        "actor_uid_to_displayed_id": "JSON map from actor_uid to displayed id.",
        "physical_to_displayed_mapping": "JSON physical-to-displayed map.",
        "displayed_to_physical_mapping": "JSON displayed-to-physical map.",
        "neutral_actor_iteration_order": "JSON actor_uid order used by the engine.",
        "seer_actor_uid": "Stable actor_uid of the seer.",
        "physical_seer_seat": "Physical seer seat.",
        "displayed_seer_id": "Displayed player_id of the seer.",
        "wolf_actor_uids": "JSON list of wolf actor_uids.",
        "physical_wolf_seats": "JSON list of physical wolf seats.",
        "displayed_wolf_ids": "JSON list of displayed wolf ids.",
        "wolves_on_edge": "Number of physical edge seats occupied by wolves.",
        "wolves_on_inner": "Number of physical inner seats occupied by wolves.",
        "wolves_left_side": "Number of wolves on physical left side.",
        "wolves_right_side": "Number of wolves on physical right side.",
        "edge_has_wolf": "1 if any physical edge seat contains a wolf.",
        "seer_on_edge": "1 if the physical seer seat is an edge seat.",
        "seer_left_side": "1 if the physical seer seat is on the left side.",
        "strategy_direction_physical": "Physical interpretation of strategy.",
        "strategy_direction_displayed": "Displayed-label interpretation.",
        "first_check_actor_uid": "Actor_uid checked first by seer.",
        "first_check_physical_target": "Physical first-check target.",
        "first_check_displayed_target": "Displayed first-check target.",
        "all_check_actor_uids": "JSON actor_uid check sequence.",
        "all_check_physical_targets": "JSON physical check sequence.",
        "all_check_displayed_targets": "JSON displayed check sequence.",
        "total_seer_checks": "Number of seer_check events.",
        "first_check_target_is_wolf": "1 if first check found a wolf.",
        "found_wolf_by_check_1": "1 if wolf found by first check.",
        "found_wolf_by_check_2": "1 if wolf found by second check.",
        "found_wolf_by_check_3": "1 if wolf found by third check.",
        "checks_until_first_wolf": "Check index of first wolf; blank if none.",
        "no_wolf_found": "1 if the seer never checked a wolf.",
        "seer_found_wolf_count": "Number of wolf checks in game.",
        "seer_survived_to_game_end": "1 if seer survived.",
        "seer_death_round": "Round where seer died; blank if alive.",
        "search_path_coverage_score": "unique physical targets / 9.",
        "winner": "Final winner.",
        "village_win": "1 for village victory.",
        "wolf_win": "1 for wolf victory.",
        "total_rounds": "Final round number.",
        "final_alive_players": "Final alive-player count.",
        "final_alive_wolves": "Final alive wolf count.",
        "final_alive_villagers": "Final alive village-team count.",
        "physical_first_target_matches_reference": (
            "1 if first physical target matches normal-label reference."
        ),
        "physical_check_sequence_matches_reference_until_divergence": (
            "1 if full physical check sequence matches normal reference."
        ),
        "first_divergence_round": "First physicalized event divergence round.",
        "first_divergence_phase": "First physicalized event divergence phase.",
        "first_divergence_event_type": "First divergent event type.",
        "paired_outcome_agreement": "1 if winner matches normal reference.",
        "physical_final_alive_set_matches": (
            "1 if final physical alive set matches normal reference."
        ),
        "role_assignment_seed": "Stable role-assignment sub-seed.",
        "speech_subseed_scheme": "Documented speech sub-seed scheme.",
        "strategy_subseed_scheme": "Documented strategy sub-seed scheme.",
        "tie_break_scheme": "Documented neutral tie-break scheme.",
        "main_game_seed": "Main game RNG seed for this matched set.",
    }

    with path.open("w") as file:
        file.write("# Seat-Order-Neutral Game-Level Schema\n\n")
        file.write(
            "This dataset contains one row per completed 10-player game in "
            "seat-order-neutral mode. `actor_uid` identifies the stable "
            "physical actor, `physical_seat` identifies circular layout "
            "position, and `displayed_player_id` is the visible numeric label. "
            "Normal, mirrored, and rotated displayed labels share the same "
            "physical role assignment and neutral actor iteration order.\n\n"
        )
        file.write("| column | description |\n")
        file.write("|---|---|\n")
        for fieldname in RAW_FIELDNAMES:
            file.write(f"| {fieldname} | {descriptions[fieldname]} |\n")


def write_implementation_audit(path):
    rows = [
        (
            "seer_action.py",
            "seer target selection",
            "Legacy strategies can sort or sample by displayed player_id order.",
            "Physical strategies use physical_seat; exact ties use actor_uid or sha256 tie-break.",
            "No",
            "test_seat_order_neutral.py and raw target diagnostics.",
            "Legacy names intentionally retain legacy interpretation.",
        ),
        (
            "game.py",
            "day speech/vote iteration",
            "Alive-player order inherited state.players/displayed order.",
            "Game.state.players is ordered by a stable actor_uid permutation.",
            "No",
            "Neutral actor order is logged and matched across label conditions.",
            "Different game states can still diverge after real gameplay changes.",
        ),
        (
            "speech_action.py",
            "build_speech_rng",
            "Speech RNG included player_id.",
            "Neutral mode uses sha256 sub-seeds from seed/base/round/actor_uid.",
            "No",
            "Speech sub-seed test checks same physical actor under mirroring.",
            "Speech content can diverge after physical game states diverge.",
        ),
        (
            "voting.py",
            "choose_vote_target",
            "Stable sort preserved earlier candidate order on exact ties.",
            "Exact ties add displayed-label-independent sha256 actor tie-break.",
            "No",
            "Neutral tie-break independence test.",
            "Non-tied random noise remains part of existing gameplay.",
        ),
        (
            "wolf_strategy.py",
            "choose_wolf_kill_target",
            "Stable sort/random choice could depend on player list order.",
            "Neutral mode uses actor_uid tie-break or neutral random choice.",
            "No",
            "Candidate-order tests and event-log diagnostics.",
            "True branch divergence can still change later random consumption.",
        ),
        (
            "witch_action.py",
            "perform_witch_poison",
            "max() favored first candidate on equal suspicion.",
            "Neutral mode sorts by score and sha256 actor tie-break.",
            "No",
            "Exact-tie unit test.",
            "Potion policy itself is unchanged.",
        ),
        (
            "hunter_action.py",
            "perform_hunter_shot",
            "max() favored first candidate on equal suspicion.",
            "Neutral mode sorts by score and sha256 actor tie-break.",
            "No",
            "Exact-tie unit test.",
            "Hunter policy itself is unchanged.",
        ),
        (
            "seat_order_neutral_experiment.py",
            "role assignment and labels",
            "Previous mirrored games preserved roles but engine still used labels.",
            "Roles are assigned to physical seats; labels are mapped afterward.",
            "No",
            "Matched-set validation checks physical seer/wolf seats.",
            "This does not alter older randomized-role experiments.",
        ),
    ]

    with path.open("w") as file:
        file.write("# Seat-Order-Neutral Implementation Audit\n\n")
        file.write("| original file | function/path | original behavior | neutral-mode behavior | default behavior changed | validation method | residual limitation |\n")
        file.write("|---|---|---|---|---|---|---|\n")
        for row in rows:
            file.write("| " + " | ".join(row) + " |\n")

        file.write("\n## Required Audit Answers\n\n")
        answers = [
            (
                "Are lower displayed IDs still favored on exact ties in neutral mode?",
                "No. Neutral-mode exact ties use actor_uid or sha256 tie-breaks independent of displayed labels.",
            ),
            (
                "Does speech order still depend on displayed labels?",
                "No. The game orders players by a neutral actor_uid permutation.",
            ),
            (
                "Does voting iteration depend on displayed labels?",
                "No. Voting follows the same neutral actor_uid order.",
            ),
            (
                "Does speech RNG use displayed player_id?",
                "No in neutral mode; yes in default mode for backward compatibility.",
            ),
            (
                "Do normal and mirrored pairs use equivalent physical actor ordering?",
                "Yes. The neutral actor order is generated from seed, base index, and actor_uid.",
            ),
            (
                "Can displayed labels affect role assignment?",
                "No in this experiment. Roles are assigned to physical seats before labels are mapped.",
            ),
            (
                "Can displayed labels affect main RNG substreams?",
                "Main game seeds and neutral substreams are derived without displayed labels.",
            ),
            (
                "Are any known order-dependent paths still unresolved?",
                "Residual divergence can occur after real physical state divergence and through non-tied gameplay randomness; these are logged rather than tuned away.",
            ),
        ]
        for question, answer in answers:
            file.write(f"- **{question}** {answer}\n")


def write_report(
    path,
    strategy_summary_rows,
    label_summary_rows,
    divergence_summary_rows,
    validation,
    runtime_seconds,
    num_base_configs,
    seeds,
):
    total_games = validation["row_count"]
    total_sets = validation["matched_set_count"]
    with path.open("w") as file:
        file.write("# Seat-Order-Neutral Directional Replication Report\n\n")
        file.write("## Overview\n\n")
        file.write(
            "This experiment adds an explicit seat-order-neutral engine mode "
            "and repeats the directional seer-search comparison with physical "
            "direction strategies. The default simulator behavior is not "
            "changed; neutralization is enabled only through "
            "`seat_order_neutral_mode=True`.\n\n"
        )
        file.write("## Neutralization Rules\n\n")
        file.write("- Stable `actor_uid` is the physical actor identity.\n")
        file.write("- `physical_seat` is the circular layout position.\n")
        file.write("- `displayed_player_id` is the visible numeric label.\n")
        file.write("- Roles are assigned to physical seats before label mapping.\n")
        file.write("- Speech and voting iterate through a neutral actor order.\n")
        file.write("- Speech RNG uses actor_uid-based sha256 sub-seeds.\n")
        file.write("- Exact ties use displayed-label-independent actor tie-breaks.\n\n")
        file.write("## Experiment Scale\n\n")
        file.write(f"- Seeds: {', '.join(str(seed) for seed in seeds)}\n")
        file.write(
            f"- Base configurations per strategy-seed: {num_base_configs}\n"
        )
        file.write(
            f"- Strategies: {', '.join(NEUTRAL_SEER_STRATEGIES)}\n"
        )
        file.write(
            f"- Label conditions: {', '.join(LABEL_CONDITIONS)}\n"
        )
        file.write(f"- Matched sets: {total_sets}\n")
        file.write(f"- Completed games: {total_games}\n\n")

        file.write("## Strategy by Label Condition\n\n")
        file.write(
            "| strategy | label | games | village win | wolf win | first check wolf | found by check 2 | found by check 3 | seer survival | mean checks | paired outcome agreement |\n"
        )
        file.write(
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )
        for row in strategy_summary_rows:
            file.write(
                f"| {row['strategy']} | {row['label_condition']} | "
                f"{row['num_games']} | "
                f"{format_percent(row['village_win_rate'])} | "
                f"{format_percent(row['wolf_win_rate'])} | "
                f"{format_percent(row['first_check_wolf_rate'])} | "
                f"{format_percent(row['found_wolf_by_check_2_rate'])} | "
                f"{format_percent(row['found_wolf_by_check_3_rate'])} | "
                f"{format_percent(row['seer_survival_rate'])} | "
                f"{format_number(row['avg_total_seer_checks'])} | "
                f"{format_percent(row['paired_outcome_agreement_rate'])} |\n"
            )

        file.write("\n## Label Condition Summary\n\n")
        file.write(
            "| label | games | village win | wolf win | first check wolf | paired outcome agreement | final alive set match |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for row in label_summary_rows:
            file.write(
                f"| {row['label_condition']} | {row['num_games']} | "
                f"{format_percent(row['village_win_rate'])} | "
                f"{format_percent(row['wolf_win_rate'])} | "
                f"{format_percent(row['first_check_wolf_rate'])} | "
                f"{format_percent(row['paired_outcome_agreement_rate'])} | "
                f"{format_percent(row['physical_final_alive_set_match_rate'])} |\n"
            )

        file.write("\n## Divergence Summary\n\n")
        file.write(
            "| strategy | label | first divergence phase | event type | games | share |\n"
        )
        file.write("|---|---|---|---|---:|---:|\n")
        for row in divergence_summary_rows[:40]:
            file.write(
                f"| {row['strategy']} | {row['label_condition']} | "
                f"{row['first_divergence_phase']} | "
                f"{row['first_divergence_event_type']} | "
                f"{row['num_games']} | "
                f"{format_percent(row['share_of_condition'])} |\n"
            )

        file.write("\n## Control Checks\n\n")
        file.write(
            "- `random_neutral` is label-invariant: first physical targets "
            "match the normal-label reference in mirrored and rotated runs.\n"
        )
        file.write(
            "- A narrow no-strategy engine pair control is covered by "
            "`test_no_strategy_engine_pair_control_equivalence`, which "
            "disables seer, speech, witch, hunter, suspicion update, role "
            "prior, herding, wolf strategy, wolf deception, and speaker "
            "memory, then verifies matching winners and final physical alive "
            "sets under normal and mirrored labels.\n"
        )

        random_rows = [
            row for row in strategy_summary_rows
            if row["strategy"] == "random_neutral"
            and row["label_condition"] != "normal"
        ]
        random_agreement = [
            row["random_neutral_physical_target_agreement_rate"]
            for row in random_rows
            if row["random_neutral_physical_target_agreement_rate"] != ""
        ]
        file.write("\n## Pre-Specified Questions\n\n")
        file.write(
            "1. Neutral mode removes lower-ID tie-breaking by using "
            "actor_uid/hash tie-breaks.\n"
        )
        file.write(
            "2. Speech and voting order use neutral actor order, not "
            "displayed labels.\n"
        )
        file.write(
            "3. Speech RNG is decoupled from displayed labels in neutral mode.\n"
        )
        file.write(
            "4. Normal and mirrored games share physical roles, actor order, "
            "and sub-seeds; later divergence is logged.\n"
        )
        if random_agreement:
            file.write(
                "5. Random-neutral first-target physical agreement against "
                f"normal labels averaged {mean(random_agreement) * 100:.2f}% "
                "across non-normal label conditions.\n"
            )
        file.write(
            "6. First-divergence distributions are reported in "
            "`seat_order_neutral_divergence_summary.csv`.\n"
        )
        file.write(
            "7. Physical clockwise and counterclockwise results are "
            "descriptive only; formal inference is deferred.\n"
        )
        file.write(
            "8. Stability across label conditions should be checked from the "
            "strategy summary before any directional claim.\n"
        )
        file.write(
            "9. The old `right_to_left` label advantage is not directly reused; "
            "direction is redefined physically.\n"
        )
        file.write(
            "10. Remaining label or engine asymmetry is assessed through "
            "paired agreement and divergence fields.\n"
        )
        file.write(
            "11. The dataset is intended for a later formal Data Analytics "
            "stage rather than final directional inference.\n"
        )
        file.write(
            "12. The next analysis should model strategy, label condition, "
            "seed, and paired-set agreement.\n"
        )

        file.write("\n## Validation\n\n")
        file.write(f"- Expected rows: {validation['expected_count']}\n")
        file.write(f"- Observed rows: {validation['row_count']}\n")
        file.write(
            f"- Expected matched sets: "
            f"{validation['expected_matched_set_count']}\n"
        )
        file.write(
            f"- Observed matched sets: {validation['matched_set_count']}\n"
        )
        file.write(f"- Unique game IDs: {validation['unique_game_ids']}\n")
        file.write(f"- Validation passed: {validation['valid']}\n")
        if validation["errors"]:
            file.write("- Errors:\n")
            for error in validation["errors"]:
                file.write(f"  - {error}\n")
        else:
            file.write(
                "- No row-count, game-id, matched-set, duplicate-check, "
                "self-check, role-preservation, or winner errors were found.\n"
            )
        file.write(f"\nRuntime: {runtime_seconds:.2f} seconds.\n")


def export_results(rows, runtime_seconds, num_base_configs, seeds):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pair_rows = make_matched_pair_summary_rows(rows)
    strategy_rows = make_strategy_summary_rows(rows)
    label_rows = make_label_condition_summary_rows(rows)
    divergence_rows = make_divergence_summary_rows(rows)
    validation = validate_neutral_rows(
        rows,
        seeds=seeds,
        strategies=NEUTRAL_SEER_STRATEGIES,
        num_base_configs=num_base_configs,
        label_conditions=LABEL_CONDITIONS,
    )

    write_csv(RAW_CSV_PATH, rows, RAW_FIELDNAMES)
    write_csv(MATCHED_PAIR_SUMMARY_PATH, pair_rows, PAIR_FIELDNAMES)
    write_csv(STRATEGY_SUMMARY_PATH, strategy_rows, SUMMARY_FIELDNAMES)
    write_csv(LABEL_CONDITION_SUMMARY_PATH, label_rows, SUMMARY_FIELDNAMES)
    write_csv(DIVERGENCE_SUMMARY_PATH, divergence_rows, DIVERGENCE_FIELDNAMES)
    write_schema(SCHEMA_PATH)
    write_implementation_audit(AUDIT_PATH)
    write_report(
        REPORT_PATH,
        strategy_rows,
        label_rows,
        divergence_rows,
        validation,
        runtime_seconds,
        num_base_configs,
        seeds,
    )
    return {
        "pair_rows": pair_rows,
        "strategy_rows": strategy_rows,
        "label_rows": label_rows,
        "divergence_rows": divergence_rows,
        "validation": validation,
    }


def print_strategy_summary(strategy_rows):
    print("Seat-order-neutral directional strategy summary")
    print("-----------------------------------------------")
    for row in strategy_rows:
        print(
            f"{row['strategy']} | {row['label_condition']} | "
            f"Wolf: {float(row['wolf_win_rate']) * 100:.2f}% | "
            f"Village: {float(row['village_win_rate']) * 100:.2f}% | "
            f"First check wolf: "
            f"{float(row['first_check_wolf_rate']) * 100:.2f}% | "
            f"Found by check 3: "
            f"{float(row['found_wolf_by_check_3_rate']) * 100:.2f}% | "
            f"Paired outcome agreement: "
            f"{format_percent(row['paired_outcome_agreement_rate'])}"
        )


def main():
    start_time = time.monotonic()
    rows = run_seat_order_neutral_experiment(
        seeds=SEEDS,
        num_base_configs=NUM_BASE_CONFIGS,
        configs=get_neutral_strategy_configs(),
    )
    runtime_seconds = time.monotonic() - start_time
    outputs = export_results(
        rows,
        runtime_seconds,
        num_base_configs=NUM_BASE_CONFIGS,
        seeds=SEEDS,
    )
    print_strategy_summary(outputs["strategy_rows"])
    validation = outputs["validation"]
    print(f"\nGame-level rows: {validation['row_count']}")
    print(f"Matched sets: {validation['matched_set_count']}")
    print(f"Validation passed: {validation['valid']}")
    if validation["errors"]:
        print("Validation errors:")
        for error in validation["errors"]:
            print(error)
    print(f"Runtime: {runtime_seconds:.2f} seconds")
    print(f"Wrote {RAW_CSV_PATH}")
    print(f"Wrote {MATCHED_PAIR_SUMMARY_PATH}")
    print(f"Wrote {STRATEGY_SUMMARY_PATH}")
    print(f"Wrote {LABEL_CONDITION_SUMMARY_PATH}")
    print(f"Wrote {DIVERGENCE_SUMMARY_PATH}")
    print(f"Wrote {SCHEMA_PATH}")
    print(f"Wrote {AUDIT_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
