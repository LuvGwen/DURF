import random

from config import (
    DEFAULT_NUM_GAMES,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_RANDOM_SEED,
    DEFAULT_WITCH_POISON_THRESHOLD,
)
from game import Game, create_default_players
from game_level_logging import build_game_level_row
from roles import VILLAGE_TEAM, WOLF_TEAM
from speaker_memory import (
    get_average_speaker_trust,
    get_average_team_speaker_trust,
)


def average_payoff(payoffs, team=None):
    selected_payoffs = [
        payoff["total_payoff"]
        for payoff in payoffs.values()
        if team is None or payoff["team"] == team
    ]

    if not selected_payoffs:
        return None

    return sum(selected_payoffs) / len(selected_payoffs)


def average_non_none(values):
    numeric_values = [value for value in values if value is not None]

    if not numeric_values:
        return None

    return sum(numeric_values) / len(numeric_values)


def average_payoff_by_risk_preference(payoffs, players, risk_preference):
    player_by_id = {player.player_id: player for player in players}
    selected_payoffs = []

    for player_id, payoff in payoffs.items():
        player = player_by_id.get(player_id)

        if player is None:
            continue

        if getattr(player, "risk_preference", "neutral") != risk_preference:
            continue

        selected_payoffs.append(payoff["total_payoff"])

    if not selected_payoffs:
        return None

    return sum(selected_payoffs) / len(selected_payoffs)


def format_optional_float(value):
    if value is None:
        return "None"

    return f"{value:.2f}"


def run_simulation(
    num_games=100,
    max_rounds=20,
    seed=None,
    use_suspicion_voting=True,
    enable_suspicion_update=True,
    enable_seer=True,
    enable_witch=True,
    enable_hunter=None,
    enable_speech=True,
    enable_herding=None,
    herding_alpha=None,
    herding_beta=None,
    herding_gamma=None,
    enable_role_prior=None,
    role_prior_alpha=None,
    role_prior_beta=None,
    role_prior_gamma=None,
    role_prior_delta=None,
    enable_wolf_strategy=None,
    wolf_kill_strategy=None,
    wolf_kill_noise_level=None,
    enable_wolf_deception=None,
    wolf_deception_strategy=None,
    wolf_deception_policy=None,
    enable_deception_credibility=None,
    enable_speaker_memory=None,
    enable_last_words=False,
    enable_risk_preference=False,
    risk_preference_mode="mixed",
    speaker_memory_weight=None,
    trust_vote_weight=None,
    enable_trust_weighted_speech=None,
    trust_speech_min_multiplier=None,
    trust_speech_max_multiplier=None,
    enable_trust_weighted_herding=None,
    trust_herding_min_multiplier=None,
    trust_herding_max_multiplier=None,
    role_setup=None,
    initial_p_wolf=None,
    speech_signal_scale=1.0,
    credibility_cost_scale=1.0,
    witch_poison_threshold=DEFAULT_WITCH_POISON_THRESHOLD,
    witch_save_probability=0.7,
    seer_check_strategy="default",
    seer_avoid_repeat_checks=False,
    enable_position_model=False,
    randomize_seat_roles=False,
    seat_order_neutral_mode=False,
    neutral_seed=None,
    base_game_index=None,
    label_condition=None,
    rotation_offset=0,
    physical_to_displayed_mapping=None,
    main_game_seed=None,
    include_game_level_log=False,
    game_level_log_builder=None,
):
    if wolf_deception_strategy is None and wolf_deception_policy is not None:
        wolf_deception_strategy = wolf_deception_policy

    if speaker_memory_weight is None and trust_vote_weight is not None:
        speaker_memory_weight = trust_vote_weight

    if seed is not None:
        random.seed(seed)

    results = []

    for i in range(num_games):
        players = create_default_players(
            role_setup=role_setup,
            initial_p_wolf=initial_p_wolf,
        )
        game = Game(
            players,
            use_suspicion_voting=use_suspicion_voting,
            enable_suspicion_update=enable_suspicion_update,
            enable_seer=enable_seer,
            enable_witch=enable_witch,
            enable_hunter=enable_hunter,
            enable_speech=enable_speech,
            enable_herding=enable_herding,
            herding_alpha=herding_alpha,
            herding_beta=herding_beta,
            herding_gamma=herding_gamma,
            enable_role_prior=enable_role_prior,
            role_prior_alpha=role_prior_alpha,
            role_prior_beta=role_prior_beta,
            role_prior_gamma=role_prior_gamma,
            role_prior_delta=role_prior_delta,
            enable_wolf_strategy=enable_wolf_strategy,
            wolf_kill_strategy=wolf_kill_strategy,
            wolf_kill_noise_level=wolf_kill_noise_level,
            enable_wolf_deception=enable_wolf_deception,
            wolf_deception_strategy=wolf_deception_strategy,
            enable_deception_credibility=enable_deception_credibility,
            enable_speaker_memory=enable_speaker_memory,
            enable_last_words=enable_last_words,
            enable_risk_preference=enable_risk_preference,
            risk_preference_mode=risk_preference_mode,
            speaker_memory_weight=speaker_memory_weight,
            enable_trust_weighted_speech=enable_trust_weighted_speech,
            trust_speech_min_multiplier=trust_speech_min_multiplier,
            trust_speech_max_multiplier=trust_speech_max_multiplier,
            enable_trust_weighted_herding=enable_trust_weighted_herding,
            trust_herding_min_multiplier=trust_herding_min_multiplier,
            trust_herding_max_multiplier=trust_herding_max_multiplier,
            speech_signal_scale=speech_signal_scale,
            credibility_cost_scale=credibility_cost_scale,
            witch_poison_threshold=witch_poison_threshold,
            witch_save_probability=witch_save_probability,
            seer_check_strategy=seer_check_strategy,
            seer_avoid_repeat_checks=seer_avoid_repeat_checks,
            enable_position_model=enable_position_model,
            randomize_seat_roles=randomize_seat_roles,
            seat_order_neutral_mode=seat_order_neutral_mode,
            neutral_seed=neutral_seed,
            base_game_index=(
                base_game_index
                if base_game_index is not None
                else i + 1
            ),
            label_condition=label_condition,
            rotation_offset=rotation_offset,
            physical_to_displayed_mapping=physical_to_displayed_mapping,
            main_game_seed=main_game_seed,
        )
        result = game.run_game(max_rounds=max_rounds)
        seer_check_events = [
            event for event in game.event_log
            if event["event_type"] == "seer_check"
        ]
        num_witch_saves = sum(
            1 for event in game.event_log
            if event["event_type"] == "witch_save"
        )
        num_witch_poison = sum(
            1 for event in game.event_log
            if event["event_type"] == "witch_poison"
        )
        num_night_kill_prevented = sum(
            1 for event in game.event_log
            if event["event_type"] == "night_kill_prevented"
        )
        num_seer_checks = sum(
            1 for event in game.event_log
            if event["event_type"] == "seer_check"
        )
        num_seer_found_wolves = sum(
            1 for event in seer_check_events
            if event.get("content", {}).get("target_is_wolf") is True
        )
        num_edge_seer_checks = sum(
            1 for event in seer_check_events
            if event.get("content", {}).get("target_seat_type") == "edge"
        )
        num_inner_seer_checks = sum(
            1 for event in seer_check_events
            if event.get("content", {}).get("target_seat_type") == "inner"
        )
        num_edge_wolf_seer_checks = sum(
            1 for event in seer_check_events
            if (
                event.get("content", {}).get("target_seat_type") == "edge"
                and event.get("content", {}).get("target_is_wolf") is True
            )
        )
        num_inner_wolf_seer_checks = sum(
            1 for event in seer_check_events
            if (
                event.get("content", {}).get("target_seat_type") == "inner"
                and event.get("content", {}).get("target_is_wolf") is True
            )
        )
        num_opposite_side_seer_checks = sum(
            1 for event in seer_check_events
            if (
                event.get("content", {}).get("seer_side") is not None
                and event.get("content", {}).get("target_side") is not None
                and event.get("content", {}).get("seer_side")
                != event.get("content", {}).get("target_side")
            )
        )
        num_same_side_seer_checks = sum(
            1 for event in seer_check_events
            if (
                event.get("content", {}).get("seer_side") is not None
                and event.get("content", {}).get("target_side") is not None
                and event.get("content", {}).get("seer_side")
                == event.get("content", {}).get("target_side")
            )
        )
        first_seer_check = seer_check_events[0] if seer_check_events else None
        first_check_is_edge = (
            1 if (
                first_seer_check is not None
                and first_seer_check.get("content", {}).get(
                    "target_seat_type"
                ) == "edge"
            )
            else 0
        )
        first_check_found_wolf = (
            1 if (
                first_seer_check is not None
                and first_seer_check.get("content", {}).get(
                    "target_is_wolf"
                ) is True
            )
            else 0
        )
        seer_survived = any(
            player.role == "seer" and player.alive
            for player in game.state.players
        )
        wolves = [player for player in game.state.players if player.is_wolf()]
        seers = [
            player for player in game.state.players
            if player.role == "seer"
        ]
        wolves_on_edge = sum(
            1 for player in wolves
            if getattr(player, "seat_type", None) == "edge"
        )
        wolves_on_inner = sum(
            1 for player in wolves
            if getattr(player, "seat_type", None) == "inner"
        )
        wolves_left_side = sum(
            1 for player in wolves
            if getattr(player, "side", None) == "left"
        )
        wolves_right_side = sum(
            1 for player in wolves
            if getattr(player, "side", None) == "right"
        )
        edge_has_wolf = wolves_on_edge > 0
        seer = seers[0] if seers else None
        seer_on_edge = (
            getattr(seer, "seat_type", None) == "edge"
            if seer is not None
            else False
        )
        seer_left_side = (
            getattr(seer, "side", None) == "left"
            if seer is not None
            else False
        )
        seat_role_assignment_logged = any(
            event["event_type"] == "seat_role_assignment"
            for event in game.event_log
        )
        num_hunter_shots = sum(
            1 for event in game.event_log
            if event["event_type"] == "hunter_shot"
        )
        num_wolf_deceptions = sum(
            1 for event in game.event_log
            if (
                event["event_type"] == "speech"
                and event.get("content", {}).get("is_deception")
            )
        )
        num_aggressive_wolf_deceptions = sum(
            1 for event in game.event_log
            if (
                event["event_type"] == "speech"
                and event.get("content", {}).get("is_deception")
                and event.get("content", {}).get(
                    "wolf_risk_preference",
                    event.get("content", {}).get("speaker_risk_preference"),
                ) == "aggressive"
            )
        )
        num_conservative_wolf_deceptions = sum(
            1 for event in game.event_log
            if (
                event["event_type"] == "speech"
                and event.get("content", {}).get("is_deception")
                and event.get("content", {}).get(
                    "wolf_risk_preference",
                    event.get("content", {}).get("speaker_risk_preference"),
                ) == "conservative"
            )
        )
        num_accusation_pressure_costs = sum(
            1 for event in game.event_log
            if event["event_type"] == "accusation_pressure_cost"
        )
        num_wrong_accusation_penalties = sum(
            len(event.get("content", {}).get("penalties", []))
            for event in game.event_log
            if event["event_type"] == "wrong_accusation_penalty"
        )
        num_self_defense_credibility_costs = sum(
            1 for event in game.event_log
            if event["event_type"] == "self_defense_credibility_cost"
        )
        num_speaker_trust_updates = sum(
            1 for event in game.event_log
            if event["event_type"] == "speaker_trust_update"
        )
        num_vote_outcome_trust_updates = sum(
            len(event.get("content", {}).get(
                "vote_outcome_trust_events",
                [],
            ))
            for event in game.event_log
            if event["event_type"] == "day_vote"
        )
        num_total_votes = sum(
            len(event.get("content", {}).get("votes", {}))
            for event in game.event_log
            if event["event_type"] == "day_vote"
        )
        num_aggressive_votes = 0
        num_conservative_votes = 0

        for event in game.event_log:
            if event["event_type"] != "day_vote":
                continue

            voter_risk_preferences = event.get("content", {}).get(
                "voter_risk_preference",
                {},
            )

            num_aggressive_votes += sum(
                1 for preference in voter_risk_preferences.values()
                if preference == "aggressive"
            )
            num_conservative_votes += sum(
                1 for preference in voter_risk_preferences.values()
                if preference == "conservative"
            )

        num_aggressive_witch_poison = sum(
            1 for event in game.event_log
            if (
                event["event_type"] == "witch_poison"
                and event.get("content", {}).get(
                    "witch_risk_preference"
                ) == "aggressive"
            )
        )
        num_conservative_witch_poison = sum(
            1 for event in game.event_log
            if (
                event["event_type"] == "witch_poison"
                and event.get("content", {}).get(
                    "witch_risk_preference"
                ) == "conservative"
            )
        )
        last_word_events = [
            event for event in game.event_log
            if event["event_type"] == "last_words"
        ]
        num_last_words = len(last_word_events)
        num_voted_out_last_words = sum(
            1 for event in last_word_events
            if event.get("content", {}).get("cause_of_death") == "voted_out"
        )
        num_night1_kill_last_words = sum(
            1 for event in last_word_events
            if (
                event.get("content", {}).get("cause_of_death")
                == "night_kill"
                and event.get("round") == 1
            )
        )
        num_wolf_last_words = sum(
            1 for event in last_word_events
            if event.get("content", {}).get("speaker_role") == "werewolf"
        )
        num_village_team_last_words = (
            num_last_words - num_wolf_last_words
        )
        num_correct_last_words_accusations = sum(
            1 for event in last_word_events
            if event.get("content", {}).get("target_is_wolf") is True
        )
        num_wrong_last_words_accusations = sum(
            1 for event in last_word_events
            if event.get("content", {}).get("target_is_wolf") is False
        )
        deception_type_counts = {}
        trust_speech_multipliers = []

        for event in game.event_log:
            if event["event_type"] != "speech":
                continue

            content = event.get("content", {})
            try:
                trust_speech_multiplier = float(
                    content.get("trust_speech_multiplier", 1.0)
                )
            except (TypeError, ValueError):
                trust_speech_multiplier = 1.0

            trust_speech_multipliers.append(trust_speech_multiplier)

            if not content.get("is_deception"):
                continue

            deception_type = content.get("deception_type", "unknown")
            deception_type_counts[deception_type] = (
                deception_type_counts.get(deception_type, 0) + 1
            )

        wolf_kill_events = [
            event for event in game.event_log
            if event["event_type"] in {
                "night_kill",
                "night_kill_prevented",
            }
        ]
        num_wolf_kill_attempts = len(wolf_kill_events)
        num_strategic_wolf_kills = sum(
            1 for event in wolf_kill_events
            if event.get("content", {}).get("strategy") != "random"
        )
        payoffs = result.get("payoffs", {})
        average_game_payoff = average_payoff(payoffs)
        wolf_average_payoff = average_payoff(payoffs, team="wolf")
        village_average_payoff = average_payoff(payoffs, team="village")
        conservative_average_payoff = average_payoff_by_risk_preference(
            payoffs,
            game.state.players,
            "conservative",
        )
        neutral_average_payoff = average_payoff_by_risk_preference(
            payoffs,
            game.state.players,
            "neutral",
        )
        aggressive_average_payoff = average_payoff_by_risk_preference(
            payoffs,
            game.state.players,
            "aggressive",
        )
        risk_preference_counts = {
            "conservative": 0,
            "neutral": 0,
            "aggressive": 0,
        }

        for player in game.state.players:
            preference = getattr(player, "risk_preference", "neutral")
            if preference not in risk_preference_counts:
                preference = "neutral"
            risk_preference_counts[preference] += 1

        herding_pressures = []
        role_prior_scores = []

        for event in game.event_log:
            if event["event_type"] != "day_vote":
                continue

            pressure_by_player = event.get("content", {}).get(
                "herding_pressure",
                {},
            )
            herding_pressures.extend(pressure_by_player.values())

            role_prior_by_player = event.get("content", {}).get(
                "role_prior_scores",
                {},
            )
            role_prior_scores.extend(role_prior_by_player.values())

        if herding_pressures:
            average_herding_pressure = (
                sum(herding_pressures) / len(herding_pressures)
            )
        else:
            average_herding_pressure = 0.0

        average_trust_weighted_herding_pressure = average_herding_pressure

        if role_prior_scores:
            average_role_prior_score = (
                sum(role_prior_scores) / len(role_prior_scores)
            )
        else:
            average_role_prior_score = 0.0

        average_speaker_trust = get_average_speaker_trust(game.state)
        average_wolf_speaker_trust = get_average_team_speaker_trust(
            game.state,
            WOLF_TEAM,
        )
        average_village_speaker_trust = get_average_team_speaker_trust(
            game.state,
            VILLAGE_TEAM,
        )
        average_trust_speech_multiplier = (
            sum(trust_speech_multipliers) / len(trust_speech_multipliers)
            if trust_speech_multipliers
            else 1.0
        )

        game_result = {
            "game_id": i + 1,
            "winner": result["winner"],
            "round_number": result["round_number"],
            "num_alive_players": result["num_alive_players"],
            "num_alive_wolves": result["num_alive_wolves"],
            "num_alive_villagers": result["num_alive_villagers"],
            "num_events": len(game.event_log),
            "num_witch_saves": num_witch_saves,
            "num_witch_poison": num_witch_poison,
            "num_night_kill_prevented": num_night_kill_prevented,
            "num_seer_checks": num_seer_checks,
            "num_seer_found_wolves": num_seer_found_wolves,
            "num_edge_seer_checks": num_edge_seer_checks,
            "num_inner_seer_checks": num_inner_seer_checks,
            "num_edge_wolf_seer_checks": num_edge_wolf_seer_checks,
            "num_inner_wolf_seer_checks": num_inner_wolf_seer_checks,
            "num_opposite_side_seer_checks": (
                num_opposite_side_seer_checks
            ),
            "num_same_side_seer_checks": num_same_side_seer_checks,
            "has_seer_check": bool(seer_check_events),
            "first_check_is_edge": first_check_is_edge,
            "first_check_found_wolf": first_check_found_wolf,
            "seer_survived": seer_survived,
            "wolves_on_edge": wolves_on_edge,
            "wolves_on_inner": wolves_on_inner,
            "wolves_left_side": wolves_left_side,
            "wolves_right_side": wolves_right_side,
            "edge_has_wolf": edge_has_wolf,
            "seer_on_edge": seer_on_edge,
            "seer_left_side": seer_left_side,
            "seat_role_assignment_logged": seat_role_assignment_logged,
            "num_hunter_shots": num_hunter_shots,
            "num_wolf_deceptions": num_wolf_deceptions,
            "num_aggressive_wolf_deceptions": (
                num_aggressive_wolf_deceptions
            ),
            "num_conservative_wolf_deceptions": (
                num_conservative_wolf_deceptions
            ),
            "num_accusation_pressure_costs": (
                num_accusation_pressure_costs
            ),
            "num_wrong_accusation_penalties": (
                num_wrong_accusation_penalties
            ),
            "num_self_defense_credibility_costs": (
                num_self_defense_credibility_costs
            ),
            "num_speaker_trust_updates": num_speaker_trust_updates,
            "num_vote_outcome_trust_updates": (
                num_vote_outcome_trust_updates
            ),
            "risk_preference_counts": risk_preference_counts,
            "conservative_count": risk_preference_counts["conservative"],
            "neutral_count": risk_preference_counts["neutral"],
            "aggressive_count": risk_preference_counts["aggressive"],
            "conservative_average_payoff": conservative_average_payoff,
            "neutral_average_payoff": neutral_average_payoff,
            "aggressive_average_payoff": aggressive_average_payoff,
            "num_total_votes": num_total_votes,
            "num_aggressive_votes": num_aggressive_votes,
            "num_conservative_votes": num_conservative_votes,
            "num_aggressive_witch_poison": num_aggressive_witch_poison,
            "num_conservative_witch_poison": (
                num_conservative_witch_poison
            ),
            "num_last_words": num_last_words,
            "num_voted_out_last_words": num_voted_out_last_words,
            "num_night1_kill_last_words": num_night1_kill_last_words,
            "num_wolf_last_words": num_wolf_last_words,
            "num_village_team_last_words": (
                num_village_team_last_words
            ),
            "num_correct_last_words_accusations": (
                num_correct_last_words_accusations
            ),
            "num_wrong_last_words_accusations": (
                num_wrong_last_words_accusations
            ),
            "deception_type_counts": deception_type_counts,
            "num_wolf_kill_attempts": num_wolf_kill_attempts,
            "num_strategic_wolf_kills": num_strategic_wolf_kills,
            "average_payoff": average_game_payoff,
            "wolf_average_payoff": wolf_average_payoff,
            "village_average_payoff": village_average_payoff,
            "average_herding_pressure": average_herding_pressure,
            "average_trust_weighted_herding_pressure": (
                average_trust_weighted_herding_pressure
            ),
            "average_role_prior_score": average_role_prior_score,
            "average_speaker_trust": average_speaker_trust,
            "average_wolf_speaker_trust": average_wolf_speaker_trust,
            "average_village_speaker_trust": average_village_speaker_trust,
            "average_trust_received": average_speaker_trust,
            "average_wolf_trust_received": average_wolf_speaker_trust,
            "average_village_trust_received": average_village_speaker_trust,
            "average_trust_speech_multiplier": (
                average_trust_speech_multiplier
            ),
        }

        if include_game_level_log:
            if game_level_log_builder is None:
                game_level_log_builder = build_game_level_row

            game_result["game_level_log"] = game_level_log_builder(
                game,
                result,
                seed=seed,
                game_index_within_seed=i + 1,
                strategy=seer_check_strategy,
            )

        results.append(game_result)

    return results


def summarize_results(results):
    if not results:
        raise ValueError("No simulation results to summarize.")

    total_games = len(results)
    wolf_wins = sum(1 for result in results if result["winner"] == "wolf")
    village_wins = sum(1 for result in results if result["winner"] == "village")
    draws = sum(1 for result in results if result["winner"] == "draw")
    average_rounds = (
        sum(result["round_number"] for result in results) / total_games
    )
    average_alive_players = (
        sum(result["num_alive_players"] for result in results) / total_games
    )
    total_witch_saves = sum(
        result["num_witch_saves"] for result in results
    )
    total_witch_poison = sum(
        result["num_witch_poison"] for result in results
    )
    total_aggressive_witch_poison = sum(
        result.get("num_aggressive_witch_poison", 0)
        for result in results
    )
    total_conservative_witch_poison = sum(
        result.get("num_conservative_witch_poison", 0)
        for result in results
    )
    total_night_kill_prevented = sum(
        result["num_night_kill_prevented"] for result in results
    )
    total_seer_checks = sum(
        result["num_seer_checks"] for result in results
    )
    total_seer_found_wolves = sum(
        result.get("num_seer_found_wolves", 0) for result in results
    )
    total_edge_seer_checks = sum(
        result.get("num_edge_seer_checks", 0) for result in results
    )
    total_inner_seer_checks = sum(
        result.get("num_inner_seer_checks", 0) for result in results
    )
    total_edge_wolf_seer_checks = sum(
        result.get("num_edge_wolf_seer_checks", 0) for result in results
    )
    total_inner_wolf_seer_checks = sum(
        result.get("num_inner_wolf_seer_checks", 0) for result in results
    )
    total_opposite_side_seer_checks = sum(
        result.get("num_opposite_side_seer_checks", 0)
        for result in results
    )
    total_same_side_seer_checks = sum(
        result.get("num_same_side_seer_checks", 0) for result in results
    )
    games_with_seer_checks = sum(
        1 for result in results
        if result.get("has_seer_check")
    )
    first_check_edge_count = sum(
        result.get("first_check_is_edge", 0) for result in results
    )
    first_check_found_wolf_count = sum(
        result.get("first_check_found_wolf", 0) for result in results
    )
    seer_survived_games = sum(
        1 for result in results
        if result.get("seer_survived")
    )
    total_wolves_on_edge = sum(
        result.get("wolves_on_edge", 0) for result in results
    )
    total_wolves_on_inner = sum(
        result.get("wolves_on_inner", 0) for result in results
    )
    total_wolves_left_side = sum(
        result.get("wolves_left_side", 0) for result in results
    )
    total_wolves_right_side = sum(
        result.get("wolves_right_side", 0) for result in results
    )
    games_edge_has_wolf = sum(
        1 for result in results
        if result.get("edge_has_wolf")
    )
    games_seer_on_edge = sum(
        1 for result in results
        if result.get("seer_on_edge")
    )
    games_seer_left_side = sum(
        1 for result in results
        if result.get("seer_left_side")
    )
    games_with_seat_role_assignment = sum(
        1 for result in results
        if result.get("seat_role_assignment_logged")
    )
    total_hunter_shots = sum(
        result["num_hunter_shots"] for result in results
    )
    total_wolf_deceptions = sum(
        result["num_wolf_deceptions"] for result in results
    )
    total_aggressive_wolf_deceptions = sum(
        result.get("num_aggressive_wolf_deceptions", 0)
        for result in results
    )
    total_conservative_wolf_deceptions = sum(
        result.get("num_conservative_wolf_deceptions", 0)
        for result in results
    )
    total_accusation_pressure_costs = sum(
        result["num_accusation_pressure_costs"] for result in results
    )
    total_wrong_accusation_penalties = sum(
        result["num_wrong_accusation_penalties"] for result in results
    )
    total_self_defense_credibility_costs = sum(
        result["num_self_defense_credibility_costs"] for result in results
    )
    total_speaker_trust_updates = sum(
        result["num_speaker_trust_updates"] for result in results
    )
    total_vote_outcome_trust_updates = sum(
        result.get("num_vote_outcome_trust_updates", 0)
        for result in results
    )
    conservative_count = sum(
        result.get("conservative_count", 0) for result in results
    )
    neutral_count = sum(
        result.get("neutral_count", 0) for result in results
    )
    aggressive_count = sum(
        result.get("aggressive_count", 0) for result in results
    )
    conservative_average_payoff = average_non_none(
        result.get("conservative_average_payoff") for result in results
    )
    neutral_average_payoff = average_non_none(
        result.get("neutral_average_payoff") for result in results
    )
    aggressive_average_payoff = average_non_none(
        result.get("aggressive_average_payoff") for result in results
    )
    total_votes = sum(
        result.get("num_total_votes", 0) for result in results
    )
    aggressive_votes = sum(
        result.get("num_aggressive_votes", 0) for result in results
    )
    conservative_votes = sum(
        result.get("num_conservative_votes", 0) for result in results
    )
    total_last_words = sum(
        result.get("num_last_words", 0) for result in results
    )
    total_voted_out_last_words = sum(
        result.get("num_voted_out_last_words", 0)
        for result in results
    )
    total_night1_kill_last_words = sum(
        result.get("num_night1_kill_last_words", 0)
        for result in results
    )
    total_wolf_last_words = sum(
        result.get("num_wolf_last_words", 0) for result in results
    )
    total_village_team_last_words = sum(
        result.get("num_village_team_last_words", 0)
        for result in results
    )
    total_correct_last_words_accusations = sum(
        result.get("num_correct_last_words_accusations", 0)
        for result in results
    )
    total_wrong_last_words_accusations = sum(
        result.get("num_wrong_last_words_accusations", 0)
        for result in results
    )
    total_deception_type_counts = {}

    for result in results:
        for deception_type, count in result.get(
            "deception_type_counts",
            {},
        ).items():
            total_deception_type_counts[deception_type] = (
                total_deception_type_counts.get(deception_type, 0) + count
            )

    total_wolf_kill_attempts = sum(
        result["num_wolf_kill_attempts"] for result in results
    )
    total_strategic_wolf_kills = sum(
        result["num_strategic_wolf_kills"] for result in results
    )
    average_total_payoff = average_non_none(
        result["average_payoff"] for result in results
    )
    average_wolf_payoff = average_non_none(
        result["wolf_average_payoff"] for result in results
    )
    average_village_payoff = average_non_none(
        result["village_average_payoff"] for result in results
    )
    average_herding_pressure = (
        sum(result["average_herding_pressure"] for result in results)
        / total_games
    )
    average_trust_weighted_herding_pressure = (
        sum(
            result.get(
                "average_trust_weighted_herding_pressure",
                result["average_herding_pressure"],
            )
            for result in results
        )
        / total_games
    )
    average_role_prior_score = (
        sum(result["average_role_prior_score"] for result in results)
        / total_games
    )
    average_speaker_trust = (
        sum(result["average_speaker_trust"] for result in results)
        / total_games
    )
    average_wolf_speaker_trust = (
        sum(result["average_wolf_speaker_trust"] for result in results)
        / total_games
    )
    average_village_speaker_trust = (
        sum(result["average_village_speaker_trust"] for result in results)
        / total_games
    )
    average_trust_speech_multiplier = (
        sum(result["average_trust_speech_multiplier"] for result in results)
        / total_games
    )

    return {
        "total_games": total_games,
        "wolf_wins": wolf_wins,
        "village_wins": village_wins,
        "draws": draws,
        "wolf_win_rate": wolf_wins / total_games,
        "village_win_rate": village_wins / total_games,
        "draw_rate": draws / total_games,
        "average_rounds": average_rounds,
        "average_alive_players": average_alive_players,
        "total_witch_saves": total_witch_saves,
        "total_witch_poison": total_witch_poison,
        "total_aggressive_witch_poison": total_aggressive_witch_poison,
        "total_conservative_witch_poison": (
            total_conservative_witch_poison
        ),
        "total_night_kill_prevented": total_night_kill_prevented,
        "total_seer_checks": total_seer_checks,
        "total_seer_found_wolves": total_seer_found_wolves,
        "seer_found_wolf_rate": (
            total_seer_found_wolves / total_seer_checks
            if total_seer_checks
            else 0.0
        ),
        "total_edge_seer_checks": total_edge_seer_checks,
        "total_inner_seer_checks": total_inner_seer_checks,
        "edge_check_rate": (
            total_edge_seer_checks / total_seer_checks
            if total_seer_checks
            else 0.0
        ),
        "inner_check_rate": (
            total_inner_seer_checks / total_seer_checks
            if total_seer_checks
            else 0.0
        ),
        "total_edge_wolf_seer_checks": total_edge_wolf_seer_checks,
        "total_inner_wolf_seer_checks": total_inner_wolf_seer_checks,
        "total_opposite_side_seer_checks": (
            total_opposite_side_seer_checks
        ),
        "total_same_side_seer_checks": total_same_side_seer_checks,
        "opposite_side_check_rate": (
            total_opposite_side_seer_checks / total_seer_checks
            if total_seer_checks
            else 0.0
        ),
        "same_side_check_rate": (
            total_same_side_seer_checks / total_seer_checks
            if total_seer_checks
            else 0.0
        ),
        "average_seer_checks_per_game": total_seer_checks / total_games,
        "seer_survival_rate": seer_survived_games / total_games,
        "games_with_seer_checks": games_with_seer_checks,
        "first_check_edge_rate": (
            first_check_edge_count / games_with_seer_checks
            if games_with_seer_checks
            else 0.0
        ),
        "first_check_found_wolf_rate": (
            first_check_found_wolf_count / games_with_seer_checks
            if games_with_seer_checks
            else 0.0
        ),
        "total_wolves_on_edge": total_wolves_on_edge,
        "total_wolves_on_inner": total_wolves_on_inner,
        "total_wolves_left_side": total_wolves_left_side,
        "total_wolves_right_side": total_wolves_right_side,
        "avg_wolves_on_edge": total_wolves_on_edge / total_games,
        "avg_wolves_on_inner": total_wolves_on_inner / total_games,
        "avg_wolves_left_side": total_wolves_left_side / total_games,
        "avg_wolves_right_side": total_wolves_right_side / total_games,
        "edge_has_wolf_rate": games_edge_has_wolf / total_games,
        "seer_on_edge_rate": games_seer_on_edge / total_games,
        "seer_left_side_rate": games_seer_left_side / total_games,
        "seat_role_assignment_games": games_with_seat_role_assignment,
        "total_hunter_shots": total_hunter_shots,
        "total_wolf_deceptions": total_wolf_deceptions,
        "total_aggressive_wolf_deceptions": (
            total_aggressive_wolf_deceptions
        ),
        "total_conservative_wolf_deceptions": (
            total_conservative_wolf_deceptions
        ),
        "total_accusation_pressure_costs": (
            total_accusation_pressure_costs
        ),
        "total_wrong_accusation_penalties": (
            total_wrong_accusation_penalties
        ),
        "total_self_defense_credibility_costs": (
            total_self_defense_credibility_costs
        ),
        "total_speaker_trust_updates": total_speaker_trust_updates,
        "total_vote_outcome_trust_updates": (
            total_vote_outcome_trust_updates
        ),
        "conservative_count": conservative_count,
        "neutral_count": neutral_count,
        "aggressive_count": aggressive_count,
        "conservative_avg_payoff": conservative_average_payoff,
        "neutral_avg_payoff": neutral_average_payoff,
        "aggressive_avg_payoff": aggressive_average_payoff,
        "total_votes": total_votes,
        "aggressive_votes": aggressive_votes,
        "conservative_votes": conservative_votes,
        "total_last_words": total_last_words,
        "total_voted_out_last_words": total_voted_out_last_words,
        "total_night1_kill_last_words": total_night1_kill_last_words,
        "total_wolf_last_words": total_wolf_last_words,
        "total_village_team_last_words": total_village_team_last_words,
        "total_correct_last_words_accusations": (
            total_correct_last_words_accusations
        ),
        "total_wrong_last_words_accusations": (
            total_wrong_last_words_accusations
        ),
        "total_deception_type_counts": total_deception_type_counts,
        "total_wolf_kill_attempts": total_wolf_kill_attempts,
        "total_strategic_wolf_kills": total_strategic_wolf_kills,
        "average_witch_saves_per_game": total_witch_saves / total_games,
        "average_witch_poison_per_game": total_witch_poison / total_games,
        "average_hunter_shots_per_game": total_hunter_shots / total_games,
        "average_wolf_deceptions_per_game": (
            total_wolf_deceptions / total_games
        ),
        "average_accusation_pressure_costs_per_game": (
            total_accusation_pressure_costs / total_games
        ),
        "average_wrong_accusation_penalties_per_game": (
            total_wrong_accusation_penalties / total_games
        ),
        "average_self_defense_credibility_costs_per_game": (
            total_self_defense_credibility_costs / total_games
        ),
        "average_speaker_trust_updates_per_game": (
            total_speaker_trust_updates / total_games
        ),
        "average_vote_outcome_trust_updates_per_game": (
            total_vote_outcome_trust_updates / total_games
        ),
        "average_last_words_per_game": total_last_words / total_games,
        "average_wolf_kill_attempts_per_game": (
            total_wolf_kill_attempts / total_games
        ),
        "average_payoff": average_total_payoff,
        "average_wolf_payoff": average_wolf_payoff,
        "average_village_payoff": average_village_payoff,
        "average_herding_pressure": average_herding_pressure,
        "average_trust_weighted_herding_pressure": (
            average_trust_weighted_herding_pressure
        ),
        "average_role_prior_score": average_role_prior_score,
        "average_speaker_trust": average_speaker_trust,
        "average_wolf_speaker_trust": average_wolf_speaker_trust,
        "average_village_speaker_trust": average_village_speaker_trust,
        "average_trust_received": average_speaker_trust,
        "average_wolf_trust_received": average_wolf_speaker_trust,
        "average_village_trust_received": average_village_speaker_trust,
        "average_trust_speech_multiplier": (
            average_trust_speech_multiplier
        ),
    }


def print_summary(summary):
    print("Simulation summary")
    print("------------------")
    print(f"Total games: {summary['total_games']}")
    print(f"Wolf wins: {summary['wolf_wins']}")
    print(f"Village wins: {summary['village_wins']}")
    print(f"Draws: {summary['draws']}")
    print(f"Wolf win rate: {summary['wolf_win_rate']:.2%}")
    print(f"Village win rate: {summary['village_win_rate']:.2%}")
    print(f"Draw rate: {summary['draw_rate']:.2%}")
    print(f"Average rounds: {summary['average_rounds']:.2f}")
    print(f"Average alive players: {summary['average_alive_players']:.2f}")
    print(f"Total witch saves: {summary['total_witch_saves']}")
    print(f"Total witch poison: {summary['total_witch_poison']}")
    print(
        f"Total night kills prevented: "
        f"{summary['total_night_kill_prevented']}"
    )
    print(f"Total seer checks: {summary['total_seer_checks']}")
    print(f"Total hunter shots: {summary['total_hunter_shots']}")
    print(f"Total wolf deceptions: {summary['total_wolf_deceptions']}")
    print(
        f"Total accusation pressure costs: "
        f"{summary['total_accusation_pressure_costs']}"
    )
    print(
        f"Total wrong accusation penalties: "
        f"{summary['total_wrong_accusation_penalties']}"
    )
    print(
        f"Total self-defense credibility costs: "
        f"{summary['total_self_defense_credibility_costs']}"
    )
    print(f"Total speaker trust updates: {summary['total_speaker_trust_updates']}")
    print(
        f"Total vote outcome trust updates: "
        f"{summary['total_vote_outcome_trust_updates']}"
    )
    print(
        f"Total deception type counts: "
        f"{summary['total_deception_type_counts']}"
    )
    print(f"Total wolf kill attempts: {summary['total_wolf_kill_attempts']}")
    print(
        f"Total strategic wolf kills: "
        f"{summary['total_strategic_wolf_kills']}"
    )
    print(
        f"Average witch saves per game: "
        f"{summary['average_witch_saves_per_game']:.2f}"
    )
    print(
        f"Average witch poison per game: "
        f"{summary['average_witch_poison_per_game']:.2f}"
    )
    print(
        f"Average hunter shots per game: "
        f"{summary['average_hunter_shots_per_game']:.2f}"
    )
    print(
        f"Average wolf deceptions per game: "
        f"{summary['average_wolf_deceptions_per_game']:.2f}"
    )
    print(
        f"Average accusation pressure costs per game: "
        f"{summary['average_accusation_pressure_costs_per_game']:.2f}"
    )
    print(
        f"Average wrong accusation penalties per game: "
        f"{summary['average_wrong_accusation_penalties_per_game']:.2f}"
    )
    print(
        f"Average self-defense credibility costs per game: "
        f"{summary['average_self_defense_credibility_costs_per_game']:.2f}"
    )
    print(
        f"Average speaker trust updates per game: "
        f"{summary['average_speaker_trust_updates_per_game']:.2f}"
    )
    print(
        f"Average vote outcome trust updates per game: "
        f"{summary['average_vote_outcome_trust_updates_per_game']:.2f}"
    )
    print(
        f"Average wolf kill attempts per game: "
        f"{summary['average_wolf_kill_attempts_per_game']:.2f}"
    )
    print(
        f"Average payoff: "
        f"{format_optional_float(summary['average_payoff'])}"
    )
    print(
        f"Average wolf payoff: "
        f"{format_optional_float(summary['average_wolf_payoff'])}"
    )
    print(
        f"Average village payoff: "
        f"{format_optional_float(summary['average_village_payoff'])}"
    )
    print(
        f"Average herding pressure: "
        f"{summary['average_herding_pressure']:.2f}"
    )
    print(
        f"Average trust weighted herding pressure: "
        f"{summary['average_trust_weighted_herding_pressure']:.2f}"
    )
    print(
        f"Average role prior score: "
        f"{summary['average_role_prior_score']:.2f}"
    )
    print(f"Average speaker trust: {summary['average_speaker_trust']:.2f}")
    print(
        f"Average wolf speaker trust: "
        f"{summary['average_wolf_speaker_trust']:.2f}"
    )
    print(
        f"Average village speaker trust: "
        f"{summary['average_village_speaker_trust']:.2f}"
    )
    print(
        f"Average trust speech multiplier: "
        f"{summary['average_trust_speech_multiplier']:.2f}"
    )


def run_witch_threshold_sweep(
    thresholds,
    num_games=100,
    max_rounds=20,
    seed=None,
):
    sweep_results = []

    for threshold in thresholds:
        results = run_simulation(
            num_games=num_games,
            max_rounds=max_rounds,
            seed=seed,
            witch_poison_threshold=threshold,
        )
        summary = summarize_results(results)
        summary["witch_poison_threshold"] = threshold
        sweep_results.append(summary)

    return sweep_results


def print_threshold_sweep(sweep_results):
    print("Witch poison threshold sweep")
    print("----------------------------")

    for summary in sweep_results:
        threshold = summary["witch_poison_threshold"]
        wolf_rate = summary["wolf_win_rate"] * 100
        village_rate = summary["village_win_rate"] * 100
        draw_rate = summary["draw_rate"] * 100
        avg_rounds = summary["average_rounds"]
        witch_poison = summary["total_witch_poison"]
        witch_saves = summary["total_witch_saves"]
        hunter_shots = summary["total_hunter_shots"]

        print(
            f"Threshold: {threshold:.2f} | "
            f"Wolf: {wolf_rate:.2f}% | "
            f"Village: {village_rate:.2f}% | "
            f"Draw: {draw_rate:.2f}% | "
            f"Avg rounds: {avg_rounds:.2f} | "
            f"Witch poison: {witch_poison} | "
            f"Witch saves: {witch_saves} | "
            f"Hunter shots: {hunter_shots}"
        )


if __name__ == "__main__":
    results = run_simulation(
        num_games=DEFAULT_NUM_GAMES,
        max_rounds=DEFAULT_MAX_ROUNDS,
        seed=DEFAULT_RANDOM_SEED,
    )
    summary = summarize_results(results)
    print_summary(summary)

    print("\nFirst 5 game results:")
    for result in results[:5]:
        print(result)

    print("\n")
    thresholds = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    sweep_results = run_witch_threshold_sweep(
        thresholds=thresholds,
        num_games=500,
        max_rounds=20,
        seed=DEFAULT_RANDOM_SEED,
    )
    print_threshold_sweep(sweep_results)
