import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

from config import DEFAULT_MAX_ROUNDS
from game import Game
from game_level_logging import get_seer_check_events
from player import Player
from position_model import TEN_PLAYER_ROLE_POOL, get_seat_type, get_side
from roles import SEER, WEREWOLF
from seer_action import circular_seat_distance
from ten_player_seer_position_experiment import SEER_POSITION_BASE_CONFIG


RESULTS_DIR = Path("results") / "seat_order_symmetry"
RAW_CSV_PATH = RESULTS_DIR / "seat_order_symmetry_game_level_raw.csv"
PAIR_SUMMARY_CSV_PATH = RESULTS_DIR / "seat_order_symmetry_pair_summary.csv"
STRATEGY_SUMMARY_CSV_PATH = (
    RESULTS_DIR / "seat_order_symmetry_strategy_summary.csv"
)
SCHEMA_PATH = RESULTS_DIR / "seat_order_symmetry_schema.md"
AUDIT_PATH = RESULTS_DIR / "seat_order_asymmetry_code_audit.md"
REPORT_PATH = RESULTS_DIR / "seat_order_symmetry_experiment_report.md"

SEEDS = [42, 43, 44, 45, 46]
NUM_BASE_CONFIGS = 500
PHYSICAL_SEATS = list(range(1, 11))
NORMAL_MAPPING = {seat: seat for seat in PHYSICAL_SEATS}
MIRROR_MAPPING = {seat: 11 - seat for seat in PHYSICAL_SEATS}

SEAT_ORDER_STRATEGIES = [
    "left_to_right",
    "right_to_left",
    "alternate_sides",
    "random",
    "nearest_first",
    "farthest_first",
]

RAW_FIELDNAMES = [
    "pair_id",
    "game_id",
    "seed",
    "base_game_index",
    "strategy",
    "orientation",
    "mirrored",
    "clockwise_direction",
    "physical_to_displayed_seat_mapping",
    "physical_seer_seat",
    "displayed_seer_seat",
    "physical_wolf_seats",
    "displayed_wolf_seats",
    "wolves_on_edge",
    "wolves_on_inner",
    "wolves_left_side",
    "wolves_right_side",
    "edge_has_wolf",
    "seer_on_edge",
    "seer_left_side",
    "winner",
    "village_win",
    "wolf_win",
    "total_rounds",
    "first_check_physical_target",
    "first_check_displayed_target",
    "first_check_target_is_wolf",
    "all_check_physical_targets",
    "all_check_displayed_targets",
    "total_seer_checks",
    "found_wolf_by_check_1",
    "found_wolf_by_check_2",
    "found_wolf_by_check_3",
    "checks_until_first_wolf",
    "seer_survived_to_game_end",
    "seer_death_round",
    "strategy_direction_relative_to_physical_layout",
    "strategy_direction_relative_to_displayed_labels",
    "first_target_physical_distance",
    "first_target_displayed_order_rank",
]

PAIR_FIELDNAMES = [
    "pair_id",
    "seed",
    "base_game_index",
    "strategy",
    "normal_game_id",
    "mirrored_game_id",
    "normal_winner",
    "mirrored_winner",
    "normal_village_win",
    "mirrored_village_win",
    "paired_village_win_difference",
    "outcome_agreement",
    "normal_first_check_target_is_wolf",
    "mirrored_first_check_target_is_wolf",
    "normal_first_check_physical_target",
    "mirrored_first_check_physical_target",
    "normal_seer_survived",
    "mirrored_seer_survived",
]

STRATEGY_FIELDNAMES = [
    "strategy",
    "orientation",
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
    "mean_first_target_physical_distance",
    "mean_first_target_displayed_order_rank",
    "edge_has_wolf_rate",
    "avg_wolves_on_edge",
    "avg_wolves_on_inner",
    "avg_wolves_left_side",
    "avg_wolves_right_side",
    "seer_on_edge_rate",
    "seer_left_side_rate",
]

SCHEMA_ROWS = [
    ("pair_id", "string", "Shared identifier for a normal/mirrored pair."),
    ("game_id", "string", "Unique game identifier including orientation."),
    ("seed", "integer", "Top-level experimental seed."),
    ("base_game_index", "integer", "One-based paired base configuration index."),
    ("strategy", "string", "Seer checking strategy."),
    (
        "orientation",
        "string",
        "normal or mirrored displayed seat orientation.",
    ),
    (
        "mirrored",
        "integer",
        "1 when the physical-to-displayed seat map is mirrored, else 0.",
    ),
    (
        "clockwise_direction",
        "string",
        "Whether displayed labels increase clockwise or counter-clockwise.",
    ),
    (
        "physical_to_displayed_seat_mapping",
        "JSON object",
        "Map from stable physical seat identity to displayed player_id.",
    ),
    (
        "physical_seer_seat",
        "integer",
        "Stable physical seat occupied by the seer.",
    ),
    (
        "displayed_seer_seat",
        "integer",
        "Displayed player_id occupied by the seer under this orientation.",
    ),
    (
        "physical_wolf_seats",
        "JSON list",
        "Stable physical seats occupied by wolves.",
    ),
    (
        "displayed_wolf_seats",
        "JSON list",
        "Displayed player_ids occupied by wolves under this orientation.",
    ),
    (
        "wolves_on_edge",
        "integer",
        "Number of wolves in displayed edge seats.",
    ),
    (
        "wolves_on_inner",
        "integer",
        "Number of wolves in displayed inner seats.",
    ),
    (
        "wolves_left_side",
        "integer",
        "Number of wolves on the displayed left side.",
    ),
    (
        "wolves_right_side",
        "integer",
        "Number of wolves on the displayed right side.",
    ),
    (
        "edge_has_wolf",
        "integer",
        "1 if any displayed edge seat contains a wolf.",
    ),
    (
        "seer_on_edge",
        "integer",
        "1 if the displayed seer seat is an edge seat.",
    ),
    (
        "seer_left_side",
        "integer",
        "1 if the displayed seer seat is on the left side.",
    ),
    ("winner", "string", "Final winner: wolf, village, or draw."),
    ("village_win", "integer", "1 if village won, otherwise 0."),
    ("wolf_win", "integer", "1 if wolves won, otherwise 0."),
    ("total_rounds", "integer", "Final GameState round_number."),
    (
        "first_check_physical_target",
        "integer",
        "Physical seat checked by the first seer action.",
    ),
    (
        "first_check_displayed_target",
        "integer",
        "Displayed seat checked by the first seer action.",
    ),
    (
        "first_check_target_is_wolf",
        "integer",
        "1 if first check found a wolf, 0 if not, blank if no check.",
    ),
    (
        "all_check_physical_targets",
        "JSON list",
        "All seer check targets converted to physical seats.",
    ),
    (
        "all_check_displayed_targets",
        "JSON list",
        "All seer check targets as displayed player_ids.",
    ),
    ("total_seer_checks", "integer", "Count of seer_check events."),
    (
        "found_wolf_by_check_1",
        "integer",
        "1 if a wolf was found within the first check.",
    ),
    (
        "found_wolf_by_check_2",
        "integer",
        "1 if a wolf was found within the first two checks.",
    ),
    (
        "found_wolf_by_check_3",
        "integer",
        "1 if a wolf was found within the first three checks.",
    ),
    (
        "checks_until_first_wolf",
        "integer",
        "Ordinal check that first found a wolf; blank if none.",
    ),
    (
        "seer_survived_to_game_end",
        "integer",
        "1 if seer was alive at game end, otherwise 0.",
    ),
    (
        "seer_death_round",
        "integer",
        "Round in which the seer died; blank if survived.",
    ),
    (
        "strategy_direction_relative_to_physical_layout",
        "string",
        "How the displayed-label rule maps onto physical layout.",
    ),
    (
        "strategy_direction_relative_to_displayed_labels",
        "string",
        "How the rule behaves in displayed numeric labels.",
    ),
    (
        "first_target_physical_distance",
        "integer",
        "Circular distance between physical seer and first physical target.",
    ),
    (
        "first_target_displayed_order_rank",
        "integer",
        "First target rank in the strategy's displayed-seat ordering.",
    ),
]


def stable_seed(*parts):
    text = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % (2 ** 32)


def mirror_seat(seat):
    return MIRROR_MAPPING[seat]


def invert_mapping(mapping):
    return {displayed: physical for physical, displayed in mapping.items()}


def json_dump(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def blank_if_none(value):
    return "" if value is None else value


def indicator(value):
    if value is None:
        return ""

    return 1 if value else 0


def generate_physical_role_assignment(seed, base_game_index):
    role_rng = random.Random(stable_seed("roles", seed, base_game_index))
    role_pool = list(TEN_PLAYER_ROLE_POOL)
    role_rng.shuffle(role_pool)
    return {
        physical_seat: role_pool[physical_seat - 1]
        for physical_seat in PHYSICAL_SEATS
    }


def create_displayed_players(role_by_physical_seat, mapping):
    players = []

    for physical_seat in PHYSICAL_SEATS:
        displayed_seat = mapping[physical_seat]
        player = Player(
            player_id=displayed_seat,
            role=role_by_physical_seat[physical_seat],
        )
        player.physical_seat = physical_seat
        player.displayed_seat = displayed_seat
        players.append(player)

    return sorted(players, key=lambda player: player.player_id)


def get_orientation_specs():
    return [
        {
            "orientation": "normal",
            "mirrored": False,
            "clockwise_direction": "clockwise",
            "mapping": NORMAL_MAPPING,
        },
        {
            "orientation": "mirrored",
            "mirrored": True,
            "clockwise_direction": "counter_clockwise",
            "mapping": MIRROR_MAPPING,
        },
    ]


def get_game_config(strategy):
    config = dict(SEER_POSITION_BASE_CONFIG)
    config.update({
        "seer_check_strategy": strategy,
        "seer_avoid_repeat_checks": True,
        "randomize_seat_roles": False,
    })
    return config


def get_player_by_role(players, role):
    matches = [player for player in players if player.role == role]
    return matches[0] if matches else None


def get_seer_death_round(event_log, seer_id):
    if seer_id is None:
        return None

    for event in event_log:
        if event.get("event_type") != "player_death":
            continue
        if event.get("content", {}).get("player") == seer_id:
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


def get_displayed_order(strategy, seer_displayed_seat):
    candidates = [
        seat for seat in PHYSICAL_SEATS
        if seat != seer_displayed_seat
    ]

    if strategy == "right_to_left":
        return sorted(candidates, reverse=True)

    if strategy == "nearest_first":
        return sorted(
            candidates,
            key=lambda seat: (
                circular_seat_distance(seer_displayed_seat, seat),
                seat,
            ),
        )

    if strategy == "farthest_first":
        return sorted(
            candidates,
            key=lambda seat: (
                -circular_seat_distance(seer_displayed_seat, seat),
                seat,
            ),
        )

    if strategy == "alternate_sides":
        seer_side = get_side(seer_displayed_seat)
        opposite_side = "right" if seer_side == "left" else "left"
        preferred = [
            seat for seat in candidates
            if get_side(seat) == opposite_side
        ]
        fallback = [
            seat for seat in candidates
            if get_side(seat) != opposite_side
        ]
        return sorted(
            preferred,
            key=lambda seat: (
                circular_seat_distance(seer_displayed_seat, seat),
                seat,
            ),
        ) + sorted(
            fallback,
            key=lambda seat: (
                circular_seat_distance(seer_displayed_seat, seat),
                seat,
            ),
        )

    return sorted(candidates)


def get_displayed_order_rank(strategy, seer_displayed_seat, target_displayed_seat):
    if target_displayed_seat is None:
        return None

    displayed_order = get_displayed_order(strategy, seer_displayed_seat)
    try:
        return displayed_order.index(target_displayed_seat) + 1
    except ValueError:
        return None


def describe_displayed_direction(strategy):
    descriptions = {
        "left_to_right": "increasing_displayed_labels",
        "right_to_left": "decreasing_displayed_labels",
        "alternate_sides": "opposite_display_side_then_same_side",
        "random": "random_displayed_target",
        "nearest_first": "nearest_displayed_circular_distance",
        "farthest_first": "farthest_displayed_circular_distance",
    }
    return descriptions.get(strategy, strategy)


def describe_physical_direction(strategy, mapping):
    physical_by_display_ascending = sorted(
        PHYSICAL_SEATS,
        key=lambda physical_seat: mapping[physical_seat],
    )

    if strategy == "left_to_right":
        if physical_by_display_ascending == PHYSICAL_SEATS:
            return "increasing_physical_seats"
        if physical_by_display_ascending == list(reversed(PHYSICAL_SEATS)):
            return "decreasing_physical_seats"
        return "display_increasing_custom_physical_order"

    if strategy == "right_to_left":
        physical_order = list(reversed(physical_by_display_ascending))
        if physical_order == PHYSICAL_SEATS:
            return "increasing_physical_seats"
        if physical_order == list(reversed(PHYSICAL_SEATS)):
            return "decreasing_physical_seats"
        return "display_decreasing_custom_physical_order"

    if strategy == "alternate_sides":
        return "display_side_rule_mapped_to_physical_layout"

    if strategy == "nearest_first":
        return "nearest_physical_distance_with_display_label_tiebreak"

    if strategy == "farthest_first":
        return "farthest_physical_distance_with_display_label_tiebreak"

    if strategy == "random":
        return "random_physical_target_after_display_mapping"

    return strategy


def run_single_orientation_game(
    seed,
    base_game_index,
    strategy,
    orientation_spec,
    role_by_physical_seat,
):
    mapping = orientation_spec["mapping"]
    players = create_displayed_players(role_by_physical_seat, mapping)
    config = get_game_config(strategy)

    random.seed(stable_seed("game", seed, base_game_index, strategy))
    game = Game(players, **config)
    result = game.run_game(max_rounds=DEFAULT_MAX_ROUNDS)
    return game, result


def build_symmetry_row(
    game,
    result,
    pair_id,
    game_id,
    seed,
    base_game_index,
    strategy,
    orientation_spec,
):
    mapping = orientation_spec["mapping"]
    displayed_to_physical = invert_mapping(mapping)
    players = game.state.players
    seer = get_player_by_role(players, SEER)
    wolves = [player for player in players if player.role == WEREWOLF]
    seer_check_events = get_seer_check_events(game.event_log)
    first_check = seer_check_events[0] if seer_check_events else None
    first_content = first_check.get("content", {}) if first_check else {}

    displayed_targets = [
        event.get("content", {}).get("target")
        for event in seer_check_events
    ]
    physical_targets = [
        displayed_to_physical[target]
        for target in displayed_targets
        if target in displayed_to_physical
    ]
    checks_until_first_wolf = get_checks_until_first_wolf(seer_check_events)

    displayed_seer_seat = seer.player_id if seer is not None else None
    physical_seer_seat = (
        displayed_to_physical[displayed_seer_seat]
        if displayed_seer_seat is not None
        else None
    )
    wolves_on_edge = sum(
        1 for player in wolves
        if get_seat_type(player.player_id) == "edge"
    )
    wolves_on_inner = sum(
        1 for player in wolves
        if get_seat_type(player.player_id) == "inner"
    )
    wolves_left_side = sum(
        1 for player in wolves
        if get_side(player.player_id) == "left"
    )
    wolves_right_side = sum(
        1 for player in wolves
        if get_side(player.player_id) == "right"
    )
    seer_on_edge = (
        get_seat_type(displayed_seer_seat) == "edge"
        if displayed_seer_seat is not None
        else None
    )
    seer_left_side = (
        get_side(displayed_seer_seat) == "left"
        if displayed_seer_seat is not None
        else None
    )
    first_displayed_target = first_content.get("target")
    first_physical_target = (
        displayed_to_physical[first_displayed_target]
        if first_displayed_target in displayed_to_physical
        else None
    )
    first_target_physical_distance = (
        circular_seat_distance(physical_seer_seat, first_physical_target)
        if (
            physical_seer_seat is not None
            and first_physical_target is not None
        )
        else None
    )

    return {
        "pair_id": pair_id,
        "game_id": game_id,
        "seed": seed,
        "base_game_index": base_game_index,
        "strategy": strategy,
        "orientation": orientation_spec["orientation"],
        "mirrored": 1 if orientation_spec["mirrored"] else 0,
        "clockwise_direction": orientation_spec["clockwise_direction"],
        "physical_to_displayed_seat_mapping": json_dump(mapping),
        "physical_seer_seat": blank_if_none(physical_seer_seat),
        "displayed_seer_seat": blank_if_none(displayed_seer_seat),
        "physical_wolf_seats": json_dump(
            sorted(displayed_to_physical[player.player_id] for player in wolves)
        ),
        "displayed_wolf_seats": json_dump(
            sorted(player.player_id for player in wolves)
        ),
        "wolves_on_edge": wolves_on_edge,
        "wolves_on_inner": wolves_on_inner,
        "wolves_left_side": wolves_left_side,
        "wolves_right_side": wolves_right_side,
        "edge_has_wolf": 1 if wolves_on_edge > 0 else 0,
        "seer_on_edge": indicator(seer_on_edge),
        "seer_left_side": indicator(seer_left_side),
        "winner": result["winner"],
        "village_win": 1 if result["winner"] == "village" else 0,
        "wolf_win": 1 if result["winner"] == "wolf" else 0,
        "total_rounds": result["round_number"],
        "first_check_physical_target": blank_if_none(first_physical_target),
        "first_check_displayed_target": blank_if_none(first_displayed_target),
        "first_check_target_is_wolf": indicator(
            first_content.get("target_is_wolf")
            if first_check is not None
            else None
        ),
        "all_check_physical_targets": json_dump(physical_targets),
        "all_check_displayed_targets": json_dump(displayed_targets),
        "total_seer_checks": len(seer_check_events),
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
        "seer_survived_to_game_end": (
            indicator(seer.alive) if seer is not None else ""
        ),
        "seer_death_round": blank_if_none(
            get_seer_death_round(game.event_log, displayed_seer_seat)
        ),
        "strategy_direction_relative_to_physical_layout": (
            describe_physical_direction(strategy, mapping)
        ),
        "strategy_direction_relative_to_displayed_labels": (
            describe_displayed_direction(strategy)
        ),
        "first_target_physical_distance": blank_if_none(
            first_target_physical_distance
        ),
        "first_target_displayed_order_rank": blank_if_none(
            get_displayed_order_rank(
                strategy,
                displayed_seer_seat,
                first_displayed_target,
            )
        ),
    }


def run_seat_order_symmetry_experiment(
    seeds=None,
    num_base_configs=NUM_BASE_CONFIGS,
    strategies=None,
):
    if seeds is None:
        seeds = SEEDS
    if strategies is None:
        strategies = SEAT_ORDER_STRATEGIES

    rows = []
    orientation_specs = get_orientation_specs()

    for strategy in strategies:
        for seed in seeds:
            for base_game_index in range(1, num_base_configs + 1):
                role_by_physical_seat = generate_physical_role_assignment(
                    seed,
                    base_game_index,
                )
                pair_id = (
                    f"{strategy}_seed_{seed}_base_{base_game_index}"
                )

                for orientation_spec in orientation_specs:
                    game_id = (
                        f"{pair_id}_{orientation_spec['orientation']}"
                    )
                    game, result = run_single_orientation_game(
                        seed,
                        base_game_index,
                        strategy,
                        orientation_spec,
                        role_by_physical_seat,
                    )
                    rows.append(
                        build_symmetry_row(
                            game,
                            result,
                            pair_id,
                            game_id,
                            seed,
                            base_game_index,
                            strategy,
                            orientation_spec,
                        )
                    )

    return rows


def make_pair_summary_rows(rows):
    rows_by_pair = defaultdict(dict)

    for row in rows:
        rows_by_pair[row["pair_id"]][row["orientation"]] = row

    pair_rows = []
    for pair_id in sorted(rows_by_pair):
        pair = rows_by_pair[pair_id]
        normal = pair.get("normal")
        mirrored = pair.get("mirrored")

        if normal is None or mirrored is None:
            continue

        pair_rows.append({
            "pair_id": pair_id,
            "seed": normal["seed"],
            "base_game_index": normal["base_game_index"],
            "strategy": normal["strategy"],
            "normal_game_id": normal["game_id"],
            "mirrored_game_id": mirrored["game_id"],
            "normal_winner": normal["winner"],
            "mirrored_winner": mirrored["winner"],
            "normal_village_win": normal["village_win"],
            "mirrored_village_win": mirrored["village_win"],
            "paired_village_win_difference": (
                mirrored["village_win"] - normal["village_win"]
            ),
            "outcome_agreement": (
                1 if normal["winner"] == mirrored["winner"] else 0
            ),
            "normal_first_check_target_is_wolf": (
                normal["first_check_target_is_wolf"]
            ),
            "mirrored_first_check_target_is_wolf": (
                mirrored["first_check_target_is_wolf"]
            ),
            "normal_first_check_physical_target": (
                normal["first_check_physical_target"]
            ),
            "mirrored_first_check_physical_target": (
                mirrored["first_check_physical_target"]
            ),
            "normal_seer_survived": normal["seer_survived_to_game_end"],
            "mirrored_seer_survived": (
                mirrored["seer_survived_to_game_end"]
            ),
        })

    return pair_rows


def rate(rows, key):
    if not rows:
        return 0.0

    return sum(float(row[key]) for row in rows if row[key] != "") / len(rows)


def average_nonblank(rows, key):
    values = [float(row[key]) for row in rows if row[key] != ""]
    if not values:
        return ""

    return mean(values)


def make_strategy_summary_rows(rows):
    grouped_rows = defaultdict(list)

    for row in rows:
        grouped_rows[(row["strategy"], row["orientation"])].append(row)

    summary_rows = []
    for strategy, orientation in sorted(grouped_rows):
        group = grouped_rows[(strategy, orientation)]
        no_wolf_found_count = sum(
            1 for row in group
            if row["checks_until_first_wolf"] == ""
        )
        summary_rows.append({
            "strategy": strategy,
            "orientation": orientation,
            "num_games": len(group),
            "wolf_win_rate": rate(group, "wolf_win"),
            "village_win_rate": rate(group, "village_win"),
            "avg_rounds": average_nonblank(group, "total_rounds"),
            "first_check_wolf_rate": rate(
                group,
                "first_check_target_is_wolf",
            ),
            "found_wolf_by_check_2_rate": rate(
                group,
                "found_wolf_by_check_2",
            ),
            "found_wolf_by_check_3_rate": rate(
                group,
                "found_wolf_by_check_3",
            ),
            "seer_survival_rate": rate(group, "seer_survived_to_game_end"),
            "avg_total_seer_checks": average_nonblank(
                group,
                "total_seer_checks",
            ),
            "avg_checks_until_first_wolf": average_nonblank(
                group,
                "checks_until_first_wolf",
            ),
            "no_wolf_found_rate": no_wolf_found_count / len(group),
            "mean_first_target_physical_distance": average_nonblank(
                group,
                "first_target_physical_distance",
            ),
            "mean_first_target_displayed_order_rank": average_nonblank(
                group,
                "first_target_displayed_order_rank",
            ),
            "edge_has_wolf_rate": rate(group, "edge_has_wolf"),
            "avg_wolves_on_edge": average_nonblank(
                group,
                "wolves_on_edge",
            ),
            "avg_wolves_on_inner": average_nonblank(
                group,
                "wolves_on_inner",
            ),
            "avg_wolves_left_side": average_nonblank(
                group,
                "wolves_left_side",
            ),
            "avg_wolves_right_side": average_nonblank(
                group,
                "wolves_right_side",
            ),
            "seer_on_edge_rate": rate(group, "seer_on_edge"),
            "seer_left_side_rate": rate(group, "seer_left_side"),
        })

    return summary_rows


def validate_symmetry_rows(rows, seeds=None, strategies=None, num_base_configs=None):
    if seeds is None:
        seeds = SEEDS
    if strategies is None:
        strategies = SEAT_ORDER_STRATEGIES
    if num_base_configs is None:
        num_base_configs = NUM_BASE_CONFIGS

    errors = []
    expected_count = len(seeds) * len(strategies) * num_base_configs * 2
    if len(rows) != expected_count:
        errors.append(f"Expected {expected_count} rows, found {len(rows)}.")

    game_ids = [row["game_id"] for row in rows]
    if len(game_ids) != len(set(game_ids)):
        errors.append("game_id values are not unique.")

    rows_by_pair = defaultdict(list)
    for row in rows:
        rows_by_pair[row["pair_id"]].append(row)

    expected_pairs = len(seeds) * len(strategies) * num_base_configs
    if len(rows_by_pair) != expected_pairs:
        errors.append(
            f"Expected {expected_pairs} pair_id values, "
            f"found {len(rows_by_pair)}."
        )

    for pair_id, pair_rows in rows_by_pair.items():
        if len(pair_rows) != 2:
            errors.append(f"{pair_id} has {len(pair_rows)} rows.")
            break

        orientations = sorted(row["orientation"] for row in pair_rows)
        if orientations != ["mirrored", "normal"]:
            errors.append(f"{pair_id} orientations are {orientations}.")
            break

        physical_seers = {
            row["physical_seer_seat"] for row in pair_rows
        }
        physical_wolves = {
            row["physical_wolf_seats"] for row in pair_rows
        }
        if len(physical_seers) != 1:
            errors.append(f"{pair_id} does not preserve physical seer seat.")
            break
        if len(physical_wolves) != 1:
            errors.append(f"{pair_id} does not preserve physical wolf seats.")
            break

    for row in rows:
        physical_targets = json.loads(row["all_check_physical_targets"])
        displayed_targets = json.loads(row["all_check_displayed_targets"])
        if len(physical_targets) != len(displayed_targets):
            errors.append(f"{row['game_id']} has inconsistent target logs.")
            break
        if len(physical_targets) != len(set(physical_targets)):
            errors.append(f"{row['game_id']} has duplicate seer checks.")
            break

    return errors


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


def format_float(value):
    if value == "":
        return "NA"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_schema(path):
    with path.open("w") as file:
        file.write("# Seat-Order Symmetry Game-Level Schema\n\n")
        file.write(
            "This dataset contains one row per completed 10-player game. "
            "Each base configuration is run twice: once with normal displayed "
            "seat labels and once with mirrored displayed labels. Stable "
            "physical seats preserve the underlying role assignment across "
            "each pair.\n\n"
        )
        file.write("| column | data_type | description |\n")
        file.write("|---|---|---|\n")
        for column, data_type, description in SCHEMA_ROWS:
            file.write(f"| {column} | {data_type} | {description} |\n")


def write_code_audit(path):
    with path.open("w") as file:
        file.write("# Seat-Order Asymmetry Code Audit\n\n")
        file.write(
            "This audit identifies code paths that may depend on numeric "
            "seat labels, player-list order, or deterministic tie-breaking. "
            "The symmetry experiment does not change these mechanisms; it "
            "measures whether they alter outcomes under mirrored labels.\n\n"
        )
        file.write("| file | function or code path | behavior | likely bias |\n")
        file.write("|---|---|---|---|\n")
        audit_rows = [
            (
                "seer_action.py",
                "choose_left_to_right_target",
                "Sorts candidate player_id values in ascending order.",
                "Favors lower displayed labels.",
            ),
            (
                "seer_action.py",
                "choose_right_to_left_target",
                "Sorts candidate player_id values in descending order.",
                "Favors higher displayed labels.",
            ),
            (
                "seer_action.py",
                "choose_alternate_sides_target",
                "Uses displayed left/right side and tie-breaks by lower player_id.",
                "Depends on displayed side labels and lower-seat tie-breaks.",
            ),
            (
                "seer_action.py",
                "choose_nearest_first_target",
                "Tie-breaks equal circular distances by lower player_id.",
                "Favors lower displayed labels.",
            ),
            (
                "seer_action.py",
                "choose_farthest_first_target",
                "Tie-breaks equal circular distances by lower player_id.",
                "Favors lower displayed labels.",
            ),
            (
                "seer_action.py",
                "coverage_balanced, hybrid, information_gain_proxy",
                "Use lower player_id as deterministic final tie-break.",
                "Favors lower displayed labels when scores tie.",
            ),
            (
                "position_model.py",
                "get_side, get_seat_type",
                "Classifies side and edge/inner from numeric player_id.",
                "Position labels are display-label dependent.",
            ),
            (
                "position_model.py",
                "assign_random_roles_to_seats",
                "Shuffles roles but applies side/seat_type by player_id.",
                "Role is randomized, side remains numeric-seat based.",
            ),
            (
                "game.py",
                "day_phase",
                "Speech and voting iterate alive_players in game_state order.",
                "Player list order can affect event order and tied decisions.",
            ),
            (
                "game_state.py",
                "get_alive_players and related helpers",
                "Return players in the original state.players order.",
                "List order can propagate to downstream choices.",
            ),
            (
                "voting.py",
                "choose_vote_target",
                "Stable sort after score calculation.",
                "Exact score ties favor earlier candidate order.",
            ),
            (
                "wolf_strategy.py",
                "choose_wolf_kill_target",
                "Stable sort after threat scoring.",
                "Exact score ties favor earlier candidate order.",
            ),
            (
                "witch_action.py",
                "perform_witch_poison",
                "max by suspicion_score.",
                "Exact score ties favor earlier candidate order.",
            ),
            (
                "hunter_action.py",
                "perform_hunter_shot",
                "max by suspicion_score.",
                "Exact score ties favor earlier candidate order.",
            ),
            (
                "speech_action.py",
                "build_speech_rng",
                "Includes player_id in deterministic speech RNG seed.",
                "Displayed numeric label can affect speech act randomness.",
            ),
        ]
        for row in audit_rows:
            file.write("| " + " | ".join(row) + " |\n")

        file.write("\n## Critical Implementation Checks\n\n")
        checks = [
            (
                "Does any global mechanism iterate through players ascending "
                "seat-number order?",
                "Yes. Player lists are usually stored and queried in "
                "ascending displayed player_id order in these experiments.",
            ),
            (
                "Does any tie-break favor lower seats?",
                "Yes. Several deterministic seer strategies and some "
                "stable-sort or max paths favor lower displayed labels on "
                "exact ties.",
            ),
            (
                "Does any action order depend on the original player list?",
                "Yes. Day speech, voting, and several candidate scans inherit "
                "game_state.players order.",
            ),
            (
                "Does left/right side classification depend asymmetrically "
                "on numeric labels?",
                "Yes. Seats 1-5 are left and 6-10 are right.",
            ),
            (
                "Could player IDs affect RNG sequence or event resolution?",
                "Yes. Speech RNG explicitly uses player_id and event order can "
                "follow player-list order.",
            ),
            (
                "Could mirroring change random number consumption?",
                "The experiment seeds paired normal/mirrored games with the "
                "same game RNG seed, but different displayed labels can still "
                "change branch choices and therefore downstream consumption.",
            ),
        ]
        for question, answer in checks:
            file.write(f"- **{question}** {answer}\n")


def make_pair_diff_rows(pair_rows):
    grouped = defaultdict(list)
    for row in pair_rows:
        grouped[row["strategy"]].append(row)

    diff_rows = []
    for strategy in sorted(grouped):
        group = grouped[strategy]
        diff_rows.append({
            "strategy": strategy,
            "pair_count": len(group),
            "paired_outcome_agreement_rate": rate(
                group,
                "outcome_agreement",
            ),
            "mean_paired_village_win_difference": average_nonblank(
                group,
                "paired_village_win_difference",
            ),
        })
    return diff_rows


def write_report(path, strategy_rows, pair_rows, validation_errors):
    pair_diff_rows = make_pair_diff_rows(pair_rows)
    summary_by_key = {
        (row["strategy"], row["orientation"]): row
        for row in strategy_rows
    }

    with path.open("w") as file:
        file.write("# Seat-Order Symmetry and Mirror Validation Report\n\n")
        file.write(
            "This experiment tests whether seer-position findings persist "
            "when randomized roles are held fixed at stable physical seats "
            "but displayed numeric labels are mirrored. Player IDs remain "
            "displayed seat labels; physical seats are recorded separately.\n\n"
        )
        file.write("## Mirror Definition\n\n")
        file.write(
            "Normal orientation maps physical seat `i` to displayed seat `i`. "
            "Mirrored orientation maps physical seat `i` to displayed seat "
            "`11 - i`, so `1<->10`, `2<->9`, `3<->8`, `4<->7`, and `5<->6`.\n\n"
        )
        file.write("## Experiment Scale\n\n")
        total_games = sum(row["num_games"] for row in strategy_rows)
        file.write(f"- Seeds: {SEEDS}\n")
        file.write(f"- Base configurations per seed/strategy: {NUM_BASE_CONFIGS}\n")
        file.write(f"- Strategies: {', '.join(SEAT_ORDER_STRATEGIES)}\n")
        file.write(f"- Total game rows: {total_games}\n\n")

        file.write("## Strategy and Orientation Summary\n\n")
        file.write(
            "| strategy | orientation | games | wolf_win_rate | "
            "village_win_rate | avg_rounds | first_check_wolf_rate | "
            "found_wolf_by_check_2 | found_wolf_by_check_3 | "
            "seer_survival_rate | avg_seer_checks |\n"
        )
        file.write(
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )
        for row in strategy_rows:
            file.write(
                f"| {row['strategy']} | {row['orientation']} | "
                f"{row['num_games']} | "
                f"{row['wolf_win_rate'] * 100:.2f}% | "
                f"{row['village_win_rate'] * 100:.2f}% | "
                f"{row['avg_rounds']:.2f} | "
                f"{row['first_check_wolf_rate'] * 100:.2f}% | "
                f"{row['found_wolf_by_check_2_rate'] * 100:.2f}% | "
                f"{row['found_wolf_by_check_3_rate'] * 100:.2f}% | "
                f"{row['seer_survival_rate'] * 100:.2f}% | "
                f"{row['avg_total_seer_checks']:.2f} |\n"
            )

        file.write("\n## Seat-Role Randomization Checks\n\n")
        file.write(
            "| strategy | orientation | edge_has_wolf_rate | "
            "avg_wolves_on_edge | avg_wolves_on_inner | "
            "avg_wolves_left_side | avg_wolves_right_side | "
            "seer_on_edge_rate | seer_left_side_rate |\n"
        )
        file.write("|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in strategy_rows:
            file.write(
                f"| {row['strategy']} | {row['orientation']} | "
                f"{row['edge_has_wolf_rate'] * 100:.2f}% | "
                f"{row['avg_wolves_on_edge']:.2f} | "
                f"{row['avg_wolves_on_inner']:.2f} | "
                f"{row['avg_wolves_left_side']:.2f} | "
                f"{row['avg_wolves_right_side']:.2f} | "
                f"{row['seer_on_edge_rate'] * 100:.2f}% | "
                f"{row['seer_left_side_rate'] * 100:.2f}% |\n"
            )

        file.write("\n## Paired Normal vs Mirrored Differences\n\n")
        file.write(
            "| strategy | pair_count | paired_outcome_agreement_rate | "
            "mean_paired_village_win_difference |\n"
        )
        file.write("|---|---:|---:|---:|\n")
        for row in pair_diff_rows:
            file.write(
                f"| {row['strategy']} | {row['pair_count']} | "
                f"{row['paired_outcome_agreement_rate'] * 100:.2f}% | "
                f"{row['mean_paired_village_win_difference']:.4f} |\n"
            )

        file.write("\n## Left-to-Right vs Right-to-Left\n\n")
        for orientation in ("normal", "mirrored"):
            left = summary_by_key.get(("left_to_right", orientation))
            right = summary_by_key.get(("right_to_left", orientation))
            if left and right:
                diff = (
                    left["village_win_rate"]
                    - right["village_win_rate"]
                )
                file.write(
                    f"- {orientation}: left_to_right village win rate "
                    f"{left['village_win_rate'] * 100:.2f}% vs "
                    f"right_to_left {right['village_win_rate'] * 100:.2f}% "
                    f"(difference {diff * 100:.2f} percentage points).\n"
                )

        file.write("\n## Validation\n\n")
        if validation_errors:
            file.write("Validation errors were found:\n")
            for error in validation_errors:
                file.write(f"- {error}\n")
        else:
            file.write(
                "All validation checks passed: expected row count, unique "
                "game IDs, exactly two orientation rows per pair, preserved "
                "physical seer and wolf seats within pairs, and no duplicate "
                "seer checks.\n"
            )

        file.write("\n## Interpretation Notes\n\n")
        file.write(
            "This report is descriptive and implementation-focused. It does "
            "not perform formal statistical inference. The paired dataset is "
            "designed for downstream analysis of whether apparent positional "
            "advantages are physical-layout effects or displayed-label/order "
            "artifacts.\n"
        )


def export_results(rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pair_rows = make_pair_summary_rows(rows)
    strategy_rows = make_strategy_summary_rows(rows)
    validation_errors = validate_symmetry_rows(rows)

    write_csv(RAW_CSV_PATH, rows, RAW_FIELDNAMES)
    write_csv(PAIR_SUMMARY_CSV_PATH, pair_rows, PAIR_FIELDNAMES)
    write_csv(STRATEGY_SUMMARY_CSV_PATH, strategy_rows, STRATEGY_FIELDNAMES)
    write_schema(SCHEMA_PATH)
    write_code_audit(AUDIT_PATH)
    write_report(REPORT_PATH, strategy_rows, pair_rows, validation_errors)

    return pair_rows, strategy_rows, validation_errors


def print_strategy_summary(strategy_rows):
    print("Seat-order symmetry strategy summary")
    print("------------------------------------")
    for row in strategy_rows:
        print(
            f"{row['strategy']} | {row['orientation']} | "
            f"Wolf: {row['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {row['village_win_rate'] * 100:.2f}% | "
            f"First check wolf: "
            f"{row['first_check_wolf_rate'] * 100:.2f}% | "
            f"Seer survival: {row['seer_survival_rate'] * 100:.2f}%"
        )


def main():
    rows = run_seat_order_symmetry_experiment()
    pair_rows, strategy_rows, validation_errors = export_results(rows)

    print_strategy_summary(strategy_rows)
    print()
    print(f"Raw rows: {len(rows)}")
    print(f"Pair rows: {len(pair_rows)}")
    print(f"Validation errors: {len(validation_errors)}")
    for error in validation_errors:
        print(f"- {error}")


if __name__ == "__main__":
    main()
