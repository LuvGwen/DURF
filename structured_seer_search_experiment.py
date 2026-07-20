import csv
import time
from itertools import combinations
from pathlib import Path
from statistics import mean

from config import DEFAULT_MAX_ROUNDS
from game_level_logging import (
    blank_if_none,
    get_seer,
    get_seer_check_events,
    get_seer_death_round,
    indicator,
    json_list,
    parse_json_list,
)
from roles import WEREWOLF
from seer_action import (
    HYBRID_SUSPICION_POSITION_LAMBDA,
    circular_seat_distance,
)
from simulation import run_simulation
from ten_player_experiment import NUM_GAMES
from ten_player_seer_position_experiment import SEER_POSITION_BASE_CONFIG


SEEDS = [42, 43, 44, 45, 46]

STRUCTURED_SEER_STRATEGIES = [
    "random",
    "default",
    "edge_first",
    "inner_first",
    "highest_p_wolf",
    "highest_suspicion",
    "left_to_right",
    "right_to_left",
    "alternate_sides",
    "nearest_first",
    "farthest_first",
    "coverage_balanced",
    "hybrid_suspicion_position",
    "information_gain_proxy",
]

RESULTS_DIR = Path("results") / "structured_seer_search"
GAME_LEVEL_RAW_PATH = RESULTS_DIR / "structured_seer_search_game_level_raw.csv"
SEED_SUMMARY_PATH = RESULTS_DIR / "structured_seer_search_seed_summary.csv"
STRATEGY_SUMMARY_PATH = (
    RESULTS_DIR / "structured_seer_search_strategy_summary.csv"
)
SCHEMA_PATH = RESULTS_DIR / "structured_seer_search_schema.md"
REPORT_PATH = RESULTS_DIR / "structured_seer_search_experiment_report.md"

STRUCTURED_GAME_LEVEL_FIELDNAMES = [
    "game_id",
    "seed",
    "game_index_within_seed",
    "strategy",
    "winner",
    "village_win",
    "wolf_win",
    "total_rounds",
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
    "first_check_target_distance_from_seer",
    "first_check_target_seat_type",
    "all_seer_check_targets_in_order",
    "all_seer_check_roles_in_order",
    "all_seer_check_distances_in_order",
    "total_seer_checks",
    "first_check_wolf",
    "found_wolf_by_check_1",
    "found_wolf_by_check_2",
    "found_wolf_by_check_3",
    "checks_until_first_wolf",
    "seer_found_any_wolf",
    "seer_found_wolf_count",
    "unique_seat_types_checked",
    "unique_sides_checked",
    "mean_pairwise_distance_between_checked_targets",
    "search_path_coverage_score",
    "seer_survived_to_game_end",
    "seer_death_round",
    "final_alive_players",
    "final_alive_wolves",
    "final_alive_villagers",
]

STRUCTURED_SUMMARY_FIELDNAMES = [
    "strategy",
    "seed",
    "num_games",
    "wolf_win_rate",
    "village_win_rate",
    "draw_rate",
    "first_check_wolf_rate",
    "found_wolf_by_check_1_rate",
    "found_wolf_by_check_2_rate",
    "found_wolf_by_check_3_rate",
    "mean_checks_until_first_wolf",
    "no_wolf_found_rate",
    "mean_wolves_found_per_game",
    "seer_survival_rate",
    "mean_total_seer_checks",
    "mean_search_path_coverage_score",
    "mean_unique_seat_types_checked",
    "mean_unique_sides_checked",
    "mean_pairwise_distance_between_checked_targets",
]

VALID_WINNERS = {"wolf", "village", "draw"}

STRATEGY_DEFINITIONS = {
    "random": (
        "Randomly chooses among alive, unchecked, non-self targets."
    ),
    "default": (
        "Uses the existing default random seer strategy, with the "
        "structured experiment repeat guard enabled."
    ),
    "edge_first": (
        "Uses the existing edge-first positional strategy."
    ),
    "inner_first": (
        "Uses the existing inner-first positional strategy."
    ),
    "highest_p_wolf": (
        "Checks the alive unchecked player with the highest current p_wolf."
    ),
    "highest_suspicion": (
        "Checks the alive unchecked player with the highest suspicion_score."
    ),
    "left_to_right": (
        "Checks alive unchecked targets in increasing seat-number order."
    ),
    "right_to_left": (
        "Checks alive unchecked targets in decreasing seat-number order."
    ),
    "alternate_sides": (
        "Alternates between the side opposite the seer and the seer's own "
        "side. Ties are broken by nearest circular distance, then lower seat."
    ),
    "nearest_first": (
        "Checks the alive unchecked target with minimum circular distance "
        "from the seer's seat."
    ),
    "farthest_first": (
        "Checks the alive unchecked target with maximum circular distance "
        "from the seer's seat."
    ),
    "coverage_balanced": (
        "Chooses the unchecked target that maximizes distance from already "
        "checked seats, then distance from the seer, then lower seat."
    ),
    "hybrid_suspicion_position": (
        "Scores targets as suspicion_score + "
        f"{HYBRID_SUSPICION_POSITION_LAMBDA:.2f} * coverage_bonus."
    ),
    "information_gain_proxy": (
        "Uses a visible-information proxy: 0.35 * unseen-side bonus + "
        "0.25 * unseen-seat-type bonus + 0.25 * normalized distance + "
        "0.15 * average(p_wolf, suspicion_score)."
    ),
}


def get_structured_seer_search_configs():
    configs = []

    for strategy in STRUCTURED_SEER_STRATEGIES:
        config = dict(SEER_POSITION_BASE_CONFIG)
        config["name"] = strategy
        config["seer_check_strategy"] = strategy
        config["randomize_seat_roles"] = True
        config["seer_avoid_repeat_checks"] = True
        configs.append(config)

    return configs


def get_first_truthy_index(values):
    for index, value in enumerate(values):
        if value:
            return index

    return None


def mean_pairwise_distance(target_ids):
    unique_target_ids = list(dict.fromkeys(target_ids))

    if len(unique_target_ids) < 2:
        return 0.0

    distances = [
        circular_seat_distance(first_target, second_target)
        for first_target, second_target in combinations(unique_target_ids, 2)
    ]
    return sum(distances) / len(distances)


def search_path_coverage_score(target_ids):
    unique_target_count = len(set(target_ids))
    return unique_target_count / 9


def build_structured_game_level_row(
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
    seer_id = seer.player_id if seer is not None else None
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
    checked_is_wolf = [
        event.get("content", {}).get("target_is_wolf") is True
        for event in seer_check_events
    ]
    checked_distances = [
        circular_seat_distance(seer_id, target_id)
        for target_id in checked_targets
        if seer_id is not None and target_id is not None
    ]
    checked_seat_types = [
        event.get("content", {}).get("target_seat_type")
        for event in seer_check_events
    ]
    checked_sides = [
        event.get("content", {}).get("target_side")
        for event in seer_check_events
    ]
    first_wolf_index = get_first_truthy_index(checked_is_wolf)
    checks_until_first_wolf = (
        first_wolf_index + 1
        if first_wolf_index is not None
        else None
    )
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
        "total_rounds": result["round_number"],
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
        "first_check_target_distance_from_seer": (
            checked_distances[0] if checked_distances else ""
        ),
        "first_check_target_seat_type": blank_if_none(
            first_content.get("target_seat_type")
        ),
        "all_seer_check_targets_in_order": json_list(checked_targets),
        "all_seer_check_roles_in_order": json_list(checked_roles),
        "all_seer_check_distances_in_order": json_list(checked_distances),
        "total_seer_checks": len(seer_check_events),
        "first_check_wolf": indicator(
            first_content.get("target_is_wolf")
            if first_check is not None
            else None
        ),
        "found_wolf_by_check_1": (
            1 if any(checked_is_wolf[:1]) else 0
        ),
        "found_wolf_by_check_2": (
            1 if any(checked_is_wolf[:2]) else 0
        ),
        "found_wolf_by_check_3": (
            1 if any(checked_is_wolf[:3]) else 0
        ),
        "checks_until_first_wolf": blank_if_none(
            checks_until_first_wolf
        ),
        "seer_found_any_wolf": 1 if any(checked_is_wolf) else 0,
        "seer_found_wolf_count": sum(1 for value in checked_is_wolf if value),
        "unique_seat_types_checked": len({
            seat_type for seat_type in checked_seat_types if seat_type
        }),
        "unique_sides_checked": len({
            side for side in checked_sides if side
        }),
        "mean_pairwise_distance_between_checked_targets": (
            mean_pairwise_distance(checked_targets)
        ),
        "search_path_coverage_score": search_path_coverage_score(
            checked_targets
        ),
        "seer_survived_to_game_end": (
            indicator(seer.alive) if seer is not None else ""
        ),
        "seer_death_round": get_seer_death_round(
            game.event_log,
            seer_id,
        ),
        "final_alive_players": result["num_alive_players"],
        "final_alive_wolves": result["num_alive_wolves"],
        "final_alive_villagers": result["num_alive_villagers"],
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


def as_float(value, default=0.0):
    if value in (None, ""):
        return default

    return float(value)


def as_int(value, default=0):
    if value in (None, ""):
        return default

    return int(value)


def summarize_structured_rows(rows, strategy, seed="all"):
    total_games = len(rows)

    if total_games == 0:
        raise ValueError("No structured seer search rows to summarize.")

    checks_until_first_wolf = [
        as_int(row["checks_until_first_wolf"])
        for row in rows
        if row["checks_until_first_wolf"] not in (None, "")
    ]

    return {
        "strategy": strategy,
        "seed": seed,
        "num_games": total_games,
        "wolf_win_rate": (
            sum(as_int(row["wolf_win"]) for row in rows) / total_games
        ),
        "village_win_rate": (
            sum(as_int(row["village_win"]) for row in rows) / total_games
        ),
        "draw_rate": (
            sum(1 for row in rows if row["winner"] == "draw")
            / total_games
        ),
        "first_check_wolf_rate": (
            sum(as_int(row["first_check_wolf"]) for row in rows)
            / total_games
        ),
        "found_wolf_by_check_1_rate": (
            sum(as_int(row["found_wolf_by_check_1"]) for row in rows)
            / total_games
        ),
        "found_wolf_by_check_2_rate": (
            sum(as_int(row["found_wolf_by_check_2"]) for row in rows)
            / total_games
        ),
        "found_wolf_by_check_3_rate": (
            sum(as_int(row["found_wolf_by_check_3"]) for row in rows)
            / total_games
        ),
        "mean_checks_until_first_wolf": (
            mean(checks_until_first_wolf)
            if checks_until_first_wolf
            else ""
        ),
        "no_wolf_found_rate": (
            sum(
                1 for row in rows
                if as_int(row["seer_found_any_wolf"]) == 0
            ) / total_games
        ),
        "mean_wolves_found_per_game": (
            sum(as_int(row["seer_found_wolf_count"]) for row in rows)
            / total_games
        ),
        "seer_survival_rate": (
            sum(as_int(row["seer_survived_to_game_end"]) for row in rows)
            / total_games
        ),
        "mean_total_seer_checks": (
            sum(as_int(row["total_seer_checks"]) for row in rows)
            / total_games
        ),
        "mean_search_path_coverage_score": (
            sum(
                as_float(row["search_path_coverage_score"])
                for row in rows
            ) / total_games
        ),
        "mean_unique_seat_types_checked": (
            sum(as_int(row["unique_seat_types_checked"]) for row in rows)
            / total_games
        ),
        "mean_unique_sides_checked": (
            sum(as_int(row["unique_sides_checked"]) for row in rows)
            / total_games
        ),
        "mean_pairwise_distance_between_checked_targets": (
            sum(
                as_float(
                    row["mean_pairwise_distance_between_checked_targets"]
                )
                for row in rows
            ) / total_games
        ),
    }


def summarize_by_strategy_and_seed(rows, strategies=None, seeds=None):
    if strategies is None:
        strategies = STRUCTURED_SEER_STRATEGIES

    if seeds is None:
        seeds = SEEDS

    seed_summary_rows = []
    strategy_summary_rows = []

    for strategy in strategies:
        strategy_rows = [
            row for row in rows
            if row["strategy"] == strategy
        ]
        strategy_summary_rows.append(
            summarize_structured_rows(
                strategy_rows,
                strategy=strategy,
                seed="all",
            )
        )

        for seed in seeds:
            seed_rows = [
                row for row in strategy_rows
                if as_int(row["seed"]) == seed
            ]
            seed_summary_rows.append(
                summarize_structured_rows(
                    seed_rows,
                    strategy=strategy,
                    seed=seed,
                )
            )

    return seed_summary_rows, strategy_summary_rows


def validate_structured_game_level_rows(
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
        targets = parse_json_list(row.get("all_seer_check_targets_in_order"))
        roles = parse_json_list(row.get("all_seer_check_roles_in_order"))
        distances = parse_json_list(
            row.get("all_seer_check_distances_in_order")
        )

        if targets is None or roles is None or distances is None:
            errors.append(
                f"Invalid search-path JSON for {row.get('game_id')}."
            )
            break

        if len(targets) != len(roles) or len(targets) != len(distances):
            errors.append(
                f"Search-path length mismatch for {row.get('game_id')}."
            )
            break

        if len(targets) != int(row.get("total_seer_checks", 0)):
            errors.append(
                f"total_seer_checks mismatch for {row.get('game_id')}."
            )
            break

        if len(targets) != len(set(targets)):
            errors.append(
                f"Duplicate seer check target for {row.get('game_id')}."
            )
            break

        seer_seat = row.get("seer_seat")
        if seer_seat not in (None, ""):
            seer_seat = int(seer_seat)
            if any(target == seer_seat for target in targets):
                errors.append(
                    f"Seer self-check found for {row.get('game_id')}."
                )
                break

        if any(distance < 1 or distance > 5 for distance in distances):
            errors.append(
                f"Invalid check distance for {row.get('game_id')}."
            )
            break

        coverage_score = float(row.get("search_path_coverage_score", 0.0))
        if coverage_score < 0.0 or coverage_score > 1.0:
            errors.append(
                f"Invalid coverage score for {row.get('game_id')}."
            )
            break

    return {
        "row_count": len(rows),
        "unique_game_ids": len(game_ids) == len(set(game_ids)),
        "valid": not errors,
        "errors": errors,
    }


def run_structured_seer_search_experiment(
    num_games=NUM_GAMES,
    seeds=None,
    configs=None,
):
    if seeds is None:
        seeds = SEEDS

    if configs is None:
        configs = get_structured_seer_search_configs()

    raw_rows = []

    for config in configs:
        condition = config["name"]
        strategy = config["seer_check_strategy"]
        simulation_kwargs = {
            key: value for key, value in config.items()
            if key != "name"
        }

        for seed in seeds:
            print(
                f"Running strategy={condition} seed={seed} "
                f"games={num_games}"
            )
            results = run_simulation(
                num_games=num_games,
                max_rounds=DEFAULT_MAX_ROUNDS,
                seed=seed,
                include_game_level_log=True,
                game_level_log_builder=build_structured_game_level_row,
                **simulation_kwargs,
            )
            raw_rows.extend(
                result["game_level_log"] for result in results
            )

    strategies = [config["seer_check_strategy"] for config in configs]
    seed_summary_rows, strategy_summary_rows = summarize_by_strategy_and_seed(
        raw_rows,
        strategies=strategies,
        seeds=seeds,
    )
    return raw_rows, seed_summary_rows, strategy_summary_rows


def write_structured_schema(path):
    with path.open("w") as file:
        file.write("# Structured Seer Search Game-Level Schema\n\n")
        file.write(
            "This dataset contains one row per completed 10-player "
            "randomized-role game. List-like fields use compact JSON "
            "serialization. `search_path_coverage_score` is defined as "
            "`unique_checked_targets / 9`, because the seer has nine "
            "possible non-self targets in a 10-player game.\n\n"
        )
        file.write("## Strategy Definitions\n\n")

        for strategy in STRUCTURED_SEER_STRATEGIES:
            file.write(f"- `{strategy}`: {STRATEGY_DEFINITIONS[strategy]}\n")

        file.write("\n## Columns\n\n")
        file.write("| column | description |\n")
        file.write("|---|---|\n")

        descriptions = {
            "game_id": "Unique strategy/seed/game identifier.",
            "seed": "Random seed used for this run.",
            "game_index_within_seed": "One-based game index within seed.",
            "strategy": "Seer search strategy.",
            "winner": "Final game winner: wolf, village, or draw.",
            "village_win": "Indicator for village victory.",
            "wolf_win": "Indicator for wolf victory.",
            "total_rounds": "Final GameState round number.",
            "seer_seat": "Seat number occupied by the seer.",
            "seer_side": "Seer's side from the position model.",
            "seer_seat_type": "Seer's edge/inner seat type.",
            "wolf_seats": "JSON list of wolf seat ids.",
            "wolves_on_edge": "Number of wolves in edge seats.",
            "wolves_on_inner": "Number of wolves in inner seats.",
            "wolves_left_side": "Number of wolves on the left side.",
            "wolves_right_side": "Number of wolves on the right side.",
            "first_check_target": "First seer check target seat.",
            "first_check_target_role": "Role of first checked target.",
            "first_check_target_is_wolf": (
                "Indicator that first checked target was a wolf."
            ),
            "first_check_target_distance_from_seer": (
                "Circular seat distance from seer to first target."
            ),
            "first_check_target_seat_type": (
                "Seat type of first checked target."
            ),
            "all_seer_check_targets_in_order": (
                "JSON list of checked seats in event-log order."
            ),
            "all_seer_check_roles_in_order": (
                "JSON list of checked roles in event-log order."
            ),
            "all_seer_check_distances_in_order": (
                "JSON list of circular distances in event-log order."
            ),
            "total_seer_checks": "Number of seer_check events.",
            "first_check_wolf": "Same as first_check_target_is_wolf.",
            "found_wolf_by_check_1": (
                "Indicator that a wolf was found by check 1."
            ),
            "found_wolf_by_check_2": (
                "Indicator that a wolf was found by check 2."
            ),
            "found_wolf_by_check_3": (
                "Indicator that a wolf was found by check 3."
            ),
            "checks_until_first_wolf": (
                "One-based check index for first wolf found; blank if none."
            ),
            "seer_found_any_wolf": "Indicator that any checked target was wolf.",
            "seer_found_wolf_count": "Number of checked wolves.",
            "unique_seat_types_checked": (
                "Number of distinct checked seat types."
            ),
            "unique_sides_checked": "Number of distinct checked sides.",
            "mean_pairwise_distance_between_checked_targets": (
                "Mean circular distance among checked target pairs."
            ),
            "search_path_coverage_score": (
                "unique_checked_targets / 9."
            ),
            "seer_survived_to_game_end": "Indicator that seer survived.",
            "seer_death_round": "Round in which seer died; blank if alive.",
            "final_alive_players": "Final number of alive players.",
            "final_alive_wolves": "Final number of alive wolves.",
            "final_alive_villagers": (
                "Final number of alive village-team players."
            ),
        }

        for column in STRUCTURED_GAME_LEVEL_FIELDNAMES:
            file.write(f"| {column} | {descriptions[column]} |\n")


def format_percent(value):
    return f"{value * 100:.2f}%"


def format_number(value):
    if value in (None, ""):
        return "NA"

    return f"{value:.2f}" if isinstance(value, float) else str(value)


def write_report(
    path,
    strategy_summary_rows,
    validation,
    runtime_seconds,
    num_games,
    seeds,
):
    with path.open("w") as file:
        file.write("# Structured Seer Search Experiment Report\n\n")
        file.write("## Overview\n\n")
        file.write(
            "This experiment compares random, positional, behavioral, and "
            "structured sequential seer search strategies in the existing "
            "10-player randomized-role Werewolf simulation. Game rules, role "
            "composition, speech, voting, night actions, and payoff rules are "
            "unchanged from the previous randomized-role seer-position setup.\n\n"
        )
        file.write("## Design\n\n")
        file.write(f"- Strategies: {len(STRUCTURED_SEER_STRATEGIES)}\n")
        file.write(f"- Seeds: {', '.join(str(seed) for seed in seeds)}\n")
        file.write(f"- Games per strategy per seed: {num_games}\n")
        file.write(
            f"- Total games: "
            f"{len(STRUCTURED_SEER_STRATEGIES) * len(seeds) * num_games}\n"
        )
        file.write("- Seat-role assignment: randomized each game\n")
        file.write(
            "- Repeat check guard: enabled for this experiment only\n\n"
        )
        file.write("## Strategy Definitions\n\n")

        for strategy in STRUCTURED_SEER_STRATEGIES:
            file.write(f"- `{strategy}`: {STRATEGY_DEFINITIONS[strategy]}\n")

        file.write("\n## Descriptive Strategy Summary\n\n")
        file.write(
            "| strategy | village win | wolf win | first check wolf | "
            "found by check 2 | found by check 3 | mean checks until "
            "first wolf | no wolf found | wolves found/game | "
            "seer survival | mean checks | coverage |\n"
        )
        file.write(
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
            "---:|---:|---:|\n"
        )

        for row in strategy_summary_rows:
            file.write(
                f"| {row['strategy']} | "
                f"{format_percent(row['village_win_rate'])} | "
                f"{format_percent(row['wolf_win_rate'])} | "
                f"{format_percent(row['first_check_wolf_rate'])} | "
                f"{format_percent(row['found_wolf_by_check_2_rate'])} | "
                f"{format_percent(row['found_wolf_by_check_3_rate'])} | "
                f"{format_number(row['mean_checks_until_first_wolf'])} | "
                f"{format_percent(row['no_wolf_found_rate'])} | "
                f"{row['mean_wolves_found_per_game']:.2f} | "
                f"{format_percent(row['seer_survival_rate'])} | "
                f"{row['mean_total_seer_checks']:.2f} | "
                f"{row['mean_search_path_coverage_score']:.2f} |\n"
            )

        file.write("\n## Validation\n\n")
        file.write(f"- Row count: {validation['row_count']}\n")
        file.write(
            f"- Unique game ids: {validation['unique_game_ids']}\n"
        )
        file.write(f"- Validation passed: {validation['valid']}\n")

        if validation["errors"]:
            file.write("- Validation errors:\n")
            for error in validation["errors"]:
                file.write(f"  - {error}\n")
        else:
            file.write(
                "- No invalid winners, duplicate game ids, duplicate seer "
                "check targets, self-checks, distance errors, or row-count "
                "mismatches were detected.\n"
            )

        file.write("\n## Notes\n\n")
        file.write(
            "This report contains descriptive results only. Formal "
            "hypothesis tests, confidence intervals, and effect-size "
            "estimation are intentionally deferred to the next Data "
            "Analytics stage.\n"
        )
        file.write(f"\nRuntime: {runtime_seconds:.2f} seconds.\n")


def export_structured_results(
    raw_rows,
    seed_summary_rows,
    strategy_summary_rows,
    validation,
    runtime_seconds,
    num_games,
    seeds,
):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(
        GAME_LEVEL_RAW_PATH,
        raw_rows,
        STRUCTURED_GAME_LEVEL_FIELDNAMES,
    )
    write_csv(
        SEED_SUMMARY_PATH,
        seed_summary_rows,
        STRUCTURED_SUMMARY_FIELDNAMES,
    )
    write_csv(
        STRATEGY_SUMMARY_PATH,
        strategy_summary_rows,
        STRUCTURED_SUMMARY_FIELDNAMES,
    )
    write_structured_schema(SCHEMA_PATH)
    write_report(
        REPORT_PATH,
        strategy_summary_rows,
        validation,
        runtime_seconds,
        num_games,
        seeds,
    )


def print_strategy_summary(strategy_summary_rows):
    print("Structured seer search strategy summary")
    print("---------------------------------------")

    for row in strategy_summary_rows:
        print(
            f"{row['strategy']} | "
            f"Wolf: {row['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {row['village_win_rate'] * 100:.2f}% | "
            f"First check wolf: "
            f"{row['first_check_wolf_rate'] * 100:.2f}% | "
            f"Found by check 3: "
            f"{row['found_wolf_by_check_3_rate'] * 100:.2f}% | "
            f"Mean checks: {row['mean_total_seer_checks']:.2f} | "
            f"Coverage: {row['mean_search_path_coverage_score']:.2f}"
        )


def main():
    start_time = time.monotonic()
    configs = get_structured_seer_search_configs()
    raw_rows, seed_summary_rows, strategy_summary_rows = (
        run_structured_seer_search_experiment(
            num_games=NUM_GAMES,
            seeds=SEEDS,
            configs=configs,
        )
    )
    runtime_seconds = time.monotonic() - start_time
    expected_count = len(configs) * len(SEEDS) * NUM_GAMES
    validation = validate_structured_game_level_rows(
        raw_rows,
        expected_count=expected_count,
        valid_strategies=STRUCTURED_SEER_STRATEGIES,
        valid_seeds=SEEDS,
    )
    export_structured_results(
        raw_rows,
        seed_summary_rows,
        strategy_summary_rows,
        validation,
        runtime_seconds,
        num_games=NUM_GAMES,
        seeds=SEEDS,
    )
    print_strategy_summary(strategy_summary_rows)
    print(f"\nGame-level rows: {validation['row_count']}")
    print(f"Game-level validation passed: {validation['valid']}")

    if validation["errors"]:
        print("Game-level validation errors:")
        for error in validation["errors"]:
            print(error)

    print(f"\nRuntime: {runtime_seconds:.2f} seconds")
    print(f"Wrote {GAME_LEVEL_RAW_PATH}")
    print(f"Wrote {SEED_SUMMARY_PATH}")
    print(f"Wrote {STRATEGY_SUMMARY_PATH}")
    print(f"Wrote {SCHEMA_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
