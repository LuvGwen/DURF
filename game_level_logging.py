import csv
import json

from roles import SEER, WEREWOLF


GAME_LEVEL_FIELDNAMES = [
    "game_id",
    "seed",
    "game_index_within_seed",
    "strategy",
    "winner",
    "village_win",
    "wolf_win",
    "seer_seat",
    "seer_side",
    "seer_seat_type",
    "wolf_seats",
    "wolves_on_edge",
    "wolves_on_inner",
    "wolves_left_side",
    "wolves_right_side",
    "first_check_target",
    "first_check_target_role",
    "first_check_target_is_wolf",
    "first_check_target_seat_type",
    "first_check_target_side",
    "all_seer_check_targets_in_order",
    "all_seer_check_roles_in_order",
    "total_seer_checks",
    "seer_found_any_wolf",
    "seer_found_wolf_count",
    "first_check_wolf",
    "seer_survived_to_game_end",
    "seer_death_round",
    "total_rounds",
    "final_alive_players",
    "final_alive_wolves",
    "final_alive_villagers",
]


GAME_LEVEL_SCHEMA = [
    (
        "game_id",
        "string",
        "Unique strategy/seed/game identifier.",
        "No",
        "Plain text.",
    ),
    ("seed", "integer", "Random seed used for the run.", "No", "Plain text."),
    (
        "game_index_within_seed",
        "integer",
        "One-based game index for this seed and strategy.",
        "No",
        "Plain text.",
    ),
    (
        "strategy",
        "string",
        "Seer checking strategy.",
        "No",
        "One of the configured seer_check_strategy values.",
    ),
    (
        "winner",
        "string",
        "Final game winner.",
        "No",
        "Allowed values: wolf, village, draw.",
    ),
    (
        "village_win",
        "integer",
        "Indicator for village victory.",
        "No",
        "1 if winner is village, otherwise 0.",
    ),
    (
        "wolf_win",
        "integer",
        "Indicator for wolf victory.",
        "No",
        "1 if winner is wolf, otherwise 0.",
    ),
    (
        "seer_seat",
        "integer",
        "Seat number occupied by the seer.",
        "Yes",
        "Blank if no seer exists.",
    ),
    (
        "seer_side",
        "string",
        "Position-model side for the seer seat.",
        "Yes",
        "Allowed values: left, right, or blank.",
    ),
    (
        "seer_seat_type",
        "string",
        "Position-model seat type for the seer seat.",
        "Yes",
        "Allowed values: edge, inner, or blank.",
    ),
    (
        "wolf_seats",
        "JSON list",
        "Seat numbers occupied by wolves.",
        "No",
        "Serialized as a JSON array of integers.",
    ),
    (
        "wolves_on_edge",
        "integer",
        "Number of wolves in edge seats.",
        "No",
        "Computed from final seat-role assignment.",
    ),
    (
        "wolves_on_inner",
        "integer",
        "Number of wolves in inner seats.",
        "No",
        "Computed from final seat-role assignment.",
    ),
    (
        "wolves_left_side",
        "integer",
        "Number of wolves on the left side.",
        "No",
        "Computed from final seat-role assignment.",
    ),
    (
        "wolves_right_side",
        "integer",
        "Number of wolves on the right side.",
        "No",
        "Computed from final seat-role assignment.",
    ),
    (
        "first_check_target",
        "integer",
        "Seat checked by the first seer action.",
        "Yes",
        "Blank if no seer check occurred.",
    ),
    (
        "first_check_target_role",
        "string",
        "Role of the first checked target.",
        "Yes",
        "Blank if no seer check occurred.",
    ),
    (
        "first_check_target_is_wolf",
        "integer",
        "Whether the first checked target was a wolf.",
        "Yes",
        "1 for true, 0 for false, blank if no seer check occurred.",
    ),
    (
        "first_check_target_seat_type",
        "string",
        "Seat type of the first checked target.",
        "Yes",
        "Allowed values: edge, inner, or blank.",
    ),
    (
        "first_check_target_side",
        "string",
        "Side of the first checked target.",
        "Yes",
        "Allowed values: left, right, or blank.",
    ),
    (
        "all_seer_check_targets_in_order",
        "JSON list",
        "All seer check targets in event-log order.",
        "No",
        "Serialized as a JSON array of integers.",
    ),
    (
        "all_seer_check_roles_in_order",
        "JSON list",
        "Roles checked by the seer in event-log order.",
        "No",
        "Serialized as a JSON array of strings.",
    ),
    (
        "total_seer_checks",
        "integer",
        "Number of seer_check events in the game.",
        "No",
        "Plain text.",
    ),
    (
        "seer_found_any_wolf",
        "integer",
        "Whether any seer check found a wolf.",
        "No",
        "1 for true, 0 for false.",
    ),
    (
        "seer_found_wolf_count",
        "integer",
        "Number of seer checks that found wolves.",
        "No",
        "Plain text.",
    ),
    (
        "first_check_wolf",
        "integer",
        "Whether the first seer check found a wolf.",
        "Yes",
        "1 for true, 0 for false, blank if no seer check occurred.",
    ),
    (
        "seer_survived_to_game_end",
        "integer",
        "Whether the seer was alive at game end.",
        "Yes",
        "1 for true, 0 for false, blank if no seer exists.",
    ),
    (
        "seer_death_round",
        "integer",
        "Round in which the seer died.",
        "Yes",
        "Blank if the seer survived or no seer exists.",
    ),
    (
        "total_rounds",
        "integer",
        "Final round_number from GameState summary.",
        "No",
        "Plain text.",
    ),
    (
        "final_alive_players",
        "integer",
        "Number of alive players at game end.",
        "No",
        "Plain text.",
    ),
    (
        "final_alive_wolves",
        "integer",
        "Number of alive wolves at game end.",
        "No",
        "Plain text.",
    ),
    (
        "final_alive_villagers",
        "integer",
        "Number of alive village-team players at game end.",
        "No",
        "Plain text.",
    ),
]


VALID_WINNERS = {"wolf", "village", "draw"}


def json_list(values):
    return json.dumps(list(values), separators=(",", ":"))


def blank_if_none(value):
    if value is None:
        return ""

    return value


def indicator(value):
    if value is None:
        return ""

    return 1 if value else 0


def get_seer(players):
    seers = [player for player in players if player.role == SEER]
    return seers[0] if seers else None


def get_seer_death_round(event_log, seer_id):
    if seer_id is None:
        return ""

    for event in event_log:
        if event.get("event_type") != "player_death":
            continue

        if event.get("content", {}).get("player") == seer_id:
            return blank_if_none(event.get("round"))

    return ""


def get_seer_check_events(event_log):
    return [
        event for event in event_log
        if event.get("event_type") == "seer_check"
    ]


def build_game_level_row(
    game,
    result,
    seed,
    game_index_within_seed,
    strategy,
):
    players = game.state.players
    wolves = sorted(
        [player for player in players if player.role == WEREWOLF],
        key=lambda player: player.player_id,
    )
    seer = get_seer(players)
    seer_check_events = get_seer_check_events(game.event_log)
    first_check = seer_check_events[0] if seer_check_events else None
    first_content = first_check.get("content", {}) if first_check else {}
    checked_targets = [
        event.get("content", {}).get("target")
        for event in seer_check_events
    ]
    checked_roles = [
        event.get("content", {}).get("target_role")
        for event in seer_check_events
    ]
    wolf_check_count = sum(
        1 for event in seer_check_events
        if event.get("content", {}).get("target_is_wolf") is True
    )
    seer_id = seer.player_id if seer is not None else None
    seed_label = "none" if seed is None else str(seed)
    strategy_label = "default" if strategy is None else str(strategy)

    return {
        "game_id": (
            f"{strategy_label}_seed_{seed_label}_"
            f"game_{game_index_within_seed}"
        ),
        "seed": blank_if_none(seed),
        "game_index_within_seed": game_index_within_seed,
        "strategy": strategy_label,
        "winner": result["winner"],
        "village_win": 1 if result["winner"] == "village" else 0,
        "wolf_win": 1 if result["winner"] == "wolf" else 0,
        "seer_seat": blank_if_none(seer_id),
        "seer_side": (
            blank_if_none(getattr(seer, "side", None))
            if seer is not None
            else ""
        ),
        "seer_seat_type": (
            blank_if_none(getattr(seer, "seat_type", None))
            if seer is not None
            else ""
        ),
        "wolf_seats": json_list(player.player_id for player in wolves),
        "wolves_on_edge": sum(
            1 for player in wolves
            if getattr(player, "seat_type", None) == "edge"
        ),
        "wolves_on_inner": sum(
            1 for player in wolves
            if getattr(player, "seat_type", None) == "inner"
        ),
        "wolves_left_side": sum(
            1 for player in wolves
            if getattr(player, "side", None) == "left"
        ),
        "wolves_right_side": sum(
            1 for player in wolves
            if getattr(player, "side", None) == "right"
        ),
        "first_check_target": blank_if_none(
            first_content.get("target")
        ),
        "first_check_target_role": blank_if_none(
            first_content.get("target_role")
        ),
        "first_check_target_is_wolf": indicator(
            first_content.get("target_is_wolf")
            if first_check is not None
            else None
        ),
        "first_check_target_seat_type": blank_if_none(
            first_content.get("target_seat_type")
        ),
        "first_check_target_side": blank_if_none(
            first_content.get("target_side")
        ),
        "all_seer_check_targets_in_order": json_list(checked_targets),
        "all_seer_check_roles_in_order": json_list(checked_roles),
        "total_seer_checks": len(seer_check_events),
        "seer_found_any_wolf": 1 if wolf_check_count > 0 else 0,
        "seer_found_wolf_count": wolf_check_count,
        "first_check_wolf": indicator(
            first_content.get("target_is_wolf")
            if first_check is not None
            else None
        ),
        "seer_survived_to_game_end": (
            indicator(seer.alive) if seer is not None else ""
        ),
        "seer_death_round": get_seer_death_round(
            game.event_log,
            seer_id,
        ),
        "total_rounds": result["round_number"],
        "final_alive_players": result["num_alive_players"],
        "final_alive_wolves": result["num_alive_wolves"],
        "final_alive_villagers": result["num_alive_villagers"],
    }


def write_game_level_csv(path, rows):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=GAME_LEVEL_FIELDNAMES,
            extrasaction="ignore",
            restval="",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_game_level_schema(path):
    with path.open("w") as file:
        file.write(
            "# Ten-Player Seer Position Randomized Roles "
            "Game-Level Schema\n\n"
        )
        file.write(
            "This dataset contains one row per completed game from the "
            "10-player randomized-role seer-position experiment. "
            "List-like fields are serialized as compact JSON arrays.\n\n"
        )
        file.write(
            "| column | data_type | description | nullable | "
            "allowed_values_or_serialization |\n"
        )
        file.write("|---|---|---|---|---|\n")

        for column, data_type, description, nullable, serialization in (
            GAME_LEVEL_SCHEMA
        ):
            file.write(
                f"| {column} | {data_type} | {description} | "
                f"{nullable} | {serialization} |\n"
            )


def parse_json_list(value):
    try:
        parsed_value = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(parsed_value, list):
        return None

    return parsed_value


def validate_game_level_rows(
    rows,
    expected_count=None,
    valid_strategies=None,
    valid_seeds=None,
):
    errors = []

    if expected_count is not None and len(rows) != expected_count:
        errors.append(
            f"Expected {expected_count} rows, found {len(rows)} rows."
        )

    game_ids = [row.get("game_id") for row in rows]
    if len(game_ids) != len(set(game_ids)):
        errors.append("game_id values are not unique.")

    if valid_strategies is not None:
        strategy_set = set(valid_strategies)
        invalid_strategies = sorted({
            row.get("strategy") for row in rows
            if row.get("strategy") not in strategy_set
        })
        if invalid_strategies:
            errors.append(f"Invalid strategies: {invalid_strategies}.")

    if valid_seeds is not None:
        seed_set = {str(seed) for seed in valid_seeds}
        invalid_seeds = sorted({
            str(row.get("seed")) for row in rows
            if str(row.get("seed")) not in seed_set
        })
        if invalid_seeds:
            errors.append(f"Invalid seeds: {invalid_seeds}.")

    for row in rows:
        winner = row.get("winner")
        if winner not in VALID_WINNERS:
            errors.append(f"Invalid winner for {row.get('game_id')}: {winner}")
            break

    for row in rows:
        target_role = row.get("first_check_target_role")
        target_is_wolf = row.get("first_check_target_is_wolf")

        if target_role in (None, "") or target_is_wolf in (None, ""):
            continue

        expected_is_wolf = 1 if target_role == WEREWOLF else 0
        if int(target_is_wolf) != expected_is_wolf:
            errors.append(
                "First-check role consistency failed for "
                f"{row.get('game_id')}."
            )
            break

    for row in rows:
        wolf_seats = parse_json_list(row.get("wolf_seats"))
        if wolf_seats is None:
            errors.append(f"Invalid wolf_seats for {row.get('game_id')}.")
            break

        wolves_on_edge = int(row.get("wolves_on_edge", 0))
        wolves_on_inner = int(row.get("wolves_on_inner", 0))
        if wolves_on_edge + wolves_on_inner != len(wolf_seats):
            errors.append(
                "Wolf edge/inner consistency failed for "
                f"{row.get('game_id')}."
            )
            break

    return {
        "row_count": len(rows),
        "unique_game_ids": len(game_ids) == len(set(game_ids)),
        "valid": not errors,
        "errors": errors,
    }
