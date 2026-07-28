"""R4 payoff calculator from a completed game event log."""

from __future__ import annotations

from collections import defaultdict

from payoff_ledger import PayoffLedger
from payoff_manifest import build_manifest
from roles import HUNTER, SEER, VILLAGER, WEREWOLF, WITCH, WOLF_TEAM


SPECIAL_VILLAGE_ROLES = {SEER, WITCH, HUNTER}
VILLAGE_ROLES = {VILLAGER, SEER, WITCH, HUNTER}


def safe_get_player(game_state, player_id):
    try:
        return game_state.get_player_by_id(int(player_id))
    except (ValueError, TypeError):
        return None


def event_source_id(game_id, index, event_type, suffix=""):
    extra = f":{suffix}" if suffix else ""
    return f"{game_id}:event:{index}:{event_type}{extra}"


def terminal_component(player, winner):
    if winner == "draw":
        return "draw_terminal"
    if player.role == WEREWOLF:
        return "wolf_team_win" if winner == WOLF_TEAM else "wolf_team_loss"
    if player.role == VILLAGER:
        return (
            "villager_team_win"
            if player.team == winner
            else "villager_team_loss"
        )
    return (
        "special_village_team_win"
        if player.team == winner
        else "special_village_team_loss"
    )


def all_wolves(game_state):
    return [player for player in game_state.players if player.role == WEREWOLF]


def add_shared_wolf_bonus(
    ledger,
    game_state,
    component_id,
    source_action_id,
    event,
    target,
    explanation,
    calculation_specification,
):
    wolves = all_wolves(game_state)
    if not wolves:
        return
    multiplier = 1.0 / len(wolves)
    for wolf in wolves:
        ledger.add(
            component_id,
            wolf,
            event["round"],
            event["phase"],
            source_action_id=source_action_id,
            explanation=explanation,
            target=target,
            event_type=event["event_type"],
            event_subtype="shared_equal_split",
            multiplier=multiplier,
            order_index=event.get("_r4_order_index", 0),
            evaluator_only_fields=["target_role", "target_team"],
            calculation_specification=calculation_specification,
        )


def day_vote_eliminations(events):
    eliminated_by_event_index = {}
    for index, event in enumerate(events):
        if event["event_type"] != "day_vote":
            continue
        eliminated = event.get("content", {}).get("eliminated")
        if eliminated is not None:
            eliminated_by_event_index[index] = eliminated
    return eliminated_by_event_index


def seer_attribution_events(game, game_id, ledger, calculation_specification):
    checked_wolves = {}
    for index, event in enumerate(game.event_log):
        if event["event_type"] != "seer_check":
            continue
        content = event.get("content", {})
        if not content.get("target_is_wolf"):
            continue
        seer = safe_get_player(game.state, content.get("seer"))
        target = safe_get_player(game.state, content.get("target"))
        if seer is None or target is None:
            continue
        checked_wolves[(seer.player_id, target.player_id)] = {
            "seer": seer,
            "target": target,
            "round": event["round"],
            "event_index": index,
        }

    awarded = set()
    for index, event in enumerate(game.event_log):
        if event["event_type"] != "day_vote":
            continue
        eliminated = event.get("content", {}).get("eliminated")
        for key, record in checked_wolves.items():
            if key in awarded:
                continue
            if record["target"].player_id != eliminated:
                continue
            if event["round"] - record["round"] > 2:
                continue
            ledger.add(
                "seer_information_leads_to_wolf_elimination",
                record["seer"],
                event["round"],
                event["phase"],
                source_action_id=event_source_id(
                    game_id,
                    index,
                    "day_vote",
                    f"seer_attribution:{record['event_index']}",
                ),
                explanation=(
                    "Checked wolf was eliminated by day vote within two rounds."
                ),
                target=record["target"],
                event_type="seer_attribution",
                event_subtype="direct_attribution",
                order_index=index,
                evaluator_only_fields=["target_role", "target_is_wolf"],
                calculation_specification=calculation_specification,
            )
            awarded.add(key)


def add_core_events(game, ledger, game_id, calculation_specification):
    for index, event in enumerate(game.event_log):
        event["_r4_order_index"] = index
        event_type = event["event_type"]
        content = event.get("content", {})

        if event_type == "seer_check":
            seer = safe_get_player(game.state, content.get("seer"))
            target = safe_get_player(game.state, content.get("target"))
            if seer is not None and seer.role == SEER:
                ledger.add(
                    "seer_investigation_used",
                    seer,
                    event["round"],
                    event["phase"],
                    event_source_id(game_id, index, event_type),
                    "Seer performed one legal night check.",
                    target=target,
                    event_type=event_type,
                    event_subtype=content.get("seer_check_strategy", "check"),
                    order_index=index,
                    evaluator_only_fields=["target_role", "target_is_wolf"],
                    calculation_specification=calculation_specification,
                )

        elif event_type == "witch_save":
            witch = safe_get_player(game.state, content.get("witch"))
            saved = safe_get_player(game.state, content.get("saved_player"))
            if witch is not None and witch.role == WITCH and saved is not None:
                component_id = (
                    "witch_correct_save"
                    if saved.team != WOLF_TEAM
                    else "witch_wasted_potion"
                )
                ledger.add(
                    component_id,
                    witch,
                    event["round"],
                    event["phase"],
                    event_source_id(game_id, index, event_type),
                    "Antidote use evaluated by saved target team.",
                    target=saved,
                    event_type=event_type,
                    order_index=index,
                    evaluator_only_fields=["target_role", "target_team"],
                    calculation_specification=calculation_specification,
                )

        elif event_type == "witch_poison":
            witch = safe_get_player(game.state, content.get("witch"))
            target = safe_get_player(game.state, content.get("poisoned_player"))
            if witch is not None and witch.role == WITCH and target is not None:
                component_id = (
                    "witch_correct_poison"
                    if content.get("target_is_wolf")
                    else "witch_poison_villager"
                )
                ledger.add(
                    component_id,
                    witch,
                    event["round"],
                    event["phase"],
                    event_source_id(game_id, index, event_type),
                    "Poison use evaluated by target team.",
                    target=target,
                    event_type=event_type,
                    order_index=index,
                    evaluator_only_fields=["target_role", "target_is_wolf"],
                    calculation_specification=calculation_specification,
                )

        elif event_type == "hunter_shot":
            hunter = safe_get_player(game.state, content.get("hunter"))
            target = safe_get_player(game.state, content.get("shot_target"))
            if hunter is not None and hunter.role == HUNTER and target is not None:
                component_id = (
                    "hunter_correct_shot"
                    if content.get("target_is_wolf")
                    else "hunter_shoot_villager"
                )
                ledger.add(
                    component_id,
                    hunter,
                    event["round"],
                    event["phase"],
                    event_source_id(game_id, index, event_type),
                    "Hunter shot evaluated by target team.",
                    target=target,
                    event_type=event_type,
                    order_index=index,
                    evaluator_only_fields=["target_role", "target_is_wolf"],
                    calculation_specification=calculation_specification,
                )

        elif event_type == "night_kill":
            target = safe_get_player(game.state, content.get("target"))
            if target is not None and target.role in SPECIAL_VILLAGE_ROLES:
                add_shared_wolf_bonus(
                    ledger,
                    game.state,
                    "wolf_special_killed_shared",
                    event_source_id(game_id, index, event_type),
                    event,
                    target,
                    "Special village role killed at night; shared wolf bonus.",
                    calculation_specification,
                )

        elif event_type == "day_vote":
            votes = content.get("votes", {})
            eliminated = safe_get_player(game.state, content.get("eliminated"))
            for voter_id, target_id in votes.items():
                voter = safe_get_player(game.state, voter_id)
                target = safe_get_player(game.state, target_id)
                if voter is None or target is None or voter.team == WOLF_TEAM:
                    continue
                component_id = (
                    "correct_vote_for_wolf"
                    if target.team == WOLF_TEAM
                    else "incorrect_vote_for_villager"
                )
                ledger.add(
                    component_id,
                    voter,
                    event["round"],
                    event["phase"],
                    event_source_id(
                        game_id,
                        index,
                        event_type,
                        f"vote:{voter.player_id}->{target.player_id}",
                    ),
                    "Village-side vote evaluated by target team.",
                    target=target,
                    event_type=event_type,
                    event_subtype="vote_target_quality",
                    order_index=index,
                    evaluator_only_fields=["target_role", "target_team"],
                    calculation_specification=calculation_specification,
                )

            if eliminated is not None and eliminated.team != WOLF_TEAM:
                ledger.add(
                    "wrongly_eliminated",
                    eliminated,
                    event["round"],
                    event["phase"],
                    event_source_id(game_id, index, event_type, "eliminated"),
                    "Village-team player was eliminated by day vote.",
                    target=eliminated,
                    event_type=event_type,
                    event_subtype="wrongly_eliminated",
                    order_index=index,
                    evaluator_only_fields=["target_role", "target_team"],
                    calculation_specification=calculation_specification,
                )
                add_shared_wolf_bonus(
                    ledger,
                    game.state,
                    "wolf_villager_voted_out_shared",
                    event_source_id(
                        game_id,
                        index,
                        event_type,
                        "wolf_vote_bonus",
                    ),
                    event,
                    eliminated,
                    "Village-team player voted out; shared wolf bonus.",
                    calculation_specification,
                )
                if eliminated.role in SPECIAL_VILLAGE_ROLES:
                    add_shared_wolf_bonus(
                        ledger,
                        game.state,
                        "wolf_special_killed_shared",
                        event_source_id(
                            game_id,
                            index,
                            event_type,
                            "special_vote_bonus",
                        ),
                        event,
                        eliminated,
                        "Special village role voted out; shared wolf bonus.",
                        calculation_specification,
                    )

    seer_attribution_events(
        game,
        game_id,
        ledger,
        calculation_specification,
    )


def add_extended_events(game, ledger, game_id, calculation_specification):
    for player in game.state.players:
        if player.alive:
            ledger.add(
                "survives_game",
                player,
                game.state.round_number,
                "terminal",
                f"{game_id}:terminal:survival:{player.player_id}",
                "Player survived to game end.",
                target=player,
                event_type="terminal_survival",
                event_subtype="survives_game",
                order_index=10_000,
                calculation_specification=calculation_specification,
            )
        if (
            player.role == WITCH
            and not player.alive
            and (player.has_antidote or player.has_poison)
        ):
            ledger.add(
                "death_with_unused_potion",
                player,
                game.state.round_number,
                "terminal",
                f"{game_id}:terminal:unused_potion:{player.player_id}",
                "Witch died with at least one unused potion.",
                target=player,
                event_type="opportunity_cost",
                event_subtype="death_with_unused_potion",
                order_index=10_001,
                calculation_specification=calculation_specification,
            )

    for index, event in enumerate(game.event_log):
        event_type = event["event_type"]
        content = event.get("content", {})
        if event_type == "speech":
            speaker = safe_get_player(game.state, content.get("speaker"))
            target = safe_get_player(game.state, content.get("target"))
            if speaker is None or target is None:
                continue
            if content.get("speech_type") == "accuse" or content.get(
                "deception_type"
            ) == "false_accuse":
                component_id = (
                    "correct_public_accusation"
                    if target.team == WOLF_TEAM
                    else "false_public_accusation"
                )
                ledger.add(
                    component_id,
                    speaker,
                    event["round"],
                    event["phase"],
                    event_source_id(
                        game_id,
                        index,
                        event_type,
                        f"accuse:{speaker.player_id}->{target.player_id}",
                    ),
                    "Public accusation evaluated after target role is known.",
                    target=target,
                    event_type=event_type,
                    event_subtype="public_accusation_quality",
                    order_index=index,
                    evaluator_only_fields=["target_role", "target_team"],
                    calculation_specification=calculation_specification,
                )

            if speaker.team == WOLF_TEAM and content.get("is_deception"):
                same_round_eliminated = [
                    later.get("content", {}).get("eliminated")
                    for later in game.event_log[index + 1:]
                    if (
                        later["event_type"] == "day_vote"
                        and later["round"] == event["round"]
                    )
                ]
                if target.player_id in same_round_eliminated and target.team != WOLF_TEAM:
                    ledger.add(
                        "successful_deception",
                        speaker,
                        event["round"],
                        event["phase"],
                        event_source_id(
                            game_id,
                            index,
                            event_type,
                            "successful_deception",
                        ),
                        "Deceptive wolf speech targeted a village player eliminated that day.",
                        target=target,
                        event_type=event_type,
                        event_subtype=content.get("deception_type", "deception"),
                        order_index=index,
                        evaluator_only_fields=["target_role", "target_team"],
                        calculation_specification=calculation_specification,
                    )

        elif event_type == "accusation_pressure_cost":
            speaker = safe_get_player(game.state, content.get("speaker"))
            target = safe_get_player(game.state, content.get("target"))
            if speaker is not None:
                ledger.add(
                    "accusation_pressure_cost",
                    speaker,
                    event["round"],
                    event["phase"],
                    event_source_id(game_id, index, event_type),
                    "Credibility pressure cost from repeated or false accusation.",
                    target=target,
                    event_type=event_type,
                    order_index=index,
                    calculation_specification=calculation_specification,
                )

        elif event_type == "self_defense_credibility_cost":
            speaker = safe_get_player(game.state, content.get("speaker"))
            target = safe_get_player(game.state, content.get("target"))
            if speaker is not None:
                ledger.add(
                    "self_defense_cost",
                    speaker,
                    event["round"],
                    event["phase"],
                    event_source_id(game_id, index, event_type),
                    "Credibility cost from repeated self-defense or trust-building.",
                    target=target,
                    event_type=event_type,
                    order_index=index,
                    calculation_specification=calculation_specification,
                )

        elif event_type == "wrong_accusation_penalty":
            penalties = content.get("penalties", [])
            for penalty_index, penalty in enumerate(penalties):
                speaker = safe_get_player(game.state, penalty.get("speaker"))
                target = safe_get_player(game.state, penalty.get("target"))
                if speaker is None:
                    continue
                ledger.add(
                    "wrong_accusation_cost",
                    speaker,
                    event["round"],
                    event["phase"],
                    event_source_id(
                        game_id,
                        index,
                        event_type,
                        str(penalty_index),
                    ),
                    "Wrong accusation penalty after revealed village target.",
                    target=target,
                    event_type=event_type,
                    order_index=index,
                    evaluator_only_fields=["target_role", "target_team"],
                    calculation_specification=calculation_specification,
                )


def add_terminal_events(game, ledger, game_id, calculation_specification):
    for player in game.state.players:
        component_id = terminal_component(player, game.state.winner)
        ledger.add(
            component_id,
            player,
            game.state.round_number,
            "terminal",
            f"{game_id}:terminal:{player.player_id}",
            "Terminal team payoff separated from event/action payoff.",
            target=player,
            event_type="terminal_result",
            event_subtype=game.state.winner or "draw",
            order_index=20_000,
            calculation_specification=calculation_specification,
        )


def summarize_players(game, ledger, calculation_specification):
    category_totals = ledger.totals_by_player_and_category()
    total_by_player = ledger.totals_by_player()
    rows = []
    for player in game.state.players:
        categories = category_totals.get(player.player_id, {})
        row = {
            "game_id": ledger.game_id,
            "matched_set_id": ledger.matched_set_id,
            "seed": ledger.seed,
            "calculation_specification": calculation_specification,
            "player_id": player.player_id,
            "role": player.role,
            "team": player.team,
            "alive": player.alive,
            "terminal_team_payoff": categories.get(
                "terminal_team_payoff",
                0.0,
            ),
            "individual_action_payoff": categories.get(
                "individual_action_payoff",
                0.0,
            ),
            "shared_wolf_team_bonus": categories.get(
                "shared_wolf_team_bonus",
                0.0,
            ),
            "survival_or_exposure_payoff": categories.get(
                "survival_or_exposure_payoff",
                0.0,
            ),
            "opportunity_cost": categories.get("opportunity_cost", 0.0),
            "total_payoff": total_by_player.get(player.player_id, 0.0),
        }
        rows.append(row)
    return rows


def summarize_game(game, player_rows, ledger, condition_name="", regime=""):
    total_payoff = sum(float(row["total_payoff"]) for row in player_rows)
    return {
        "game_id": ledger.game_id,
        "matched_set_id": ledger.matched_set_id,
        "seed": ledger.seed,
        "condition_name": condition_name,
        "behavioral_regime": regime,
        "calculation_specification": (
            player_rows[0]["calculation_specification"] if player_rows else ""
        ),
        "winner": game.state.winner,
        "round_number": game.state.round_number,
        "player_count": len(player_rows),
        "event_payoff_row_count": len(ledger.events),
        "total_game_payoff": total_payoff,
        "wolf_total_payoff": sum(
            float(row["total_payoff"]) for row in player_rows
            if row["team"] == WOLF_TEAM
        ),
        "village_total_payoff": sum(
            float(row["total_payoff"]) for row in player_rows
            if row["team"] != WOLF_TEAM
        ),
    }


def calculate_r4_payoff(
    game,
    game_id,
    matched_set_id="",
    seed="",
    calculation_specification="core",
    manifest=None,
    condition_name="",
    behavioral_regime="",
):
    if calculation_specification not in {"core", "extended"}:
        raise ValueError("calculation_specification must be core or extended.")
    manifest = manifest or build_manifest()
    ledger = PayoffLedger(
        manifest,
        game_id=game_id,
        matched_set_id=matched_set_id,
        seed=seed,
    )
    add_terminal_events(game, ledger, game_id, calculation_specification)
    add_core_events(game, ledger, game_id, calculation_specification)
    if calculation_specification == "extended":
        add_extended_events(game, ledger, game_id, calculation_specification)

    player_rows = summarize_players(game, ledger, calculation_specification)
    game_row = summarize_game(
        game,
        player_rows,
        ledger,
        condition_name=condition_name,
        regime=behavioral_regime,
    )
    return {
        "ledger": ledger,
        "event_rows": ledger.rows(),
        "player_rows": player_rows,
        "game_row": game_row,
        "manifest": manifest,
    }


if __name__ == "__main__":
    from config import TEN_PLAYER_ROLE_SETUP
    from game import Game, create_default_players

    players = create_default_players(role_setup=TEN_PLAYER_ROLE_SETUP)
    game = Game(players)
    game.run_game()
    result = calculate_r4_payoff(game, "smoke_game", seed=0)
    print(result["game_row"])
