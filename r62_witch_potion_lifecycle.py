"""R6.2 Witch potion lifecycle reconstruction utilities."""

from __future__ import annotations

from roles import HUNTER, SEER, WEREWOLF, WITCH, WOLF_TEAM, VILLAGE_TEAM


SPECIAL_VILLAGE_ROLES = {SEER, WITCH, HUNTER}


def get_witch_player(game):
    witches = [player for player in game.state.players if player.role == WITCH]
    return witches[0] if witches else None


def player_by_id(game, player_id):
    if player_id in ("", None):
        return None
    try:
        return game.state.get_player_by_id(int(player_id))
    except (TypeError, ValueError):
        return None


def player_team(player):
    if player is None:
        return ""
    return WOLF_TEAM if player.is_wolf() else VILLAGE_TEAM


def death_event_for_player(game, player_id):
    for event in game.event_log:
        if event.get("event_type") != "player_death":
            continue
        if event.get("content", {}).get("player") == player_id:
            return event
    return None


def witch_payoff(game, witch_id):
    payoff = game.payoffs.get(witch_id) or game.payoffs.get(str(witch_id))
    if payoff:
        return payoff.get("total_payoff", 0.0)
    return 0.0


def save_category(target):
    if target is None:
        return "invalid_save_attempt"
    if target.is_wolf():
        return "save_wolf"
    if target.role in SPECIAL_VILLAGE_ROLES:
        return "save_special_role"
    return "save_regular_villager"


def poison_category(target):
    if target is None:
        return "invalid_poison_attempt"
    if target.role == WEREWOLF or target.is_wolf():
        return "correct_poison_wolf"
    if target.role in SPECIAL_VILLAGE_ROLES:
        return "poison_special_role"
    return "poison_regular_villager"


def is_primary_save_waste(category):
    return category in {"save_wolf", "unnecessary_save", "invalid_save_attempt"}


def is_primary_poison_waste(category):
    return category in {
        "poison_regular_villager",
        "poison_special_role",
        "invalid_poison_attempt",
    }


def is_extended_save_waste(row):
    return bool(
        row["primary_save_waste"]
        or row["save_available_at_death"]
        or row["save_available_at_game_end"]
        or row["missed_save_opportunities"]
    )


def is_extended_poison_waste(row):
    return bool(
        row["primary_poison_waste"]
        or row["poison_available_at_death"]
        or row["poison_available_at_game_end"]
        or row["missed_poison_opportunities"]
    )


def reconstruct_witch_lifecycle(module, policy, matched_set, game, result):
    witch = get_witch_player(game)
    game_id = f"{module}_{policy}_{matched_set['matched_set_id']}"
    if witch is None:
        return {
            "game_id": game_id,
            "matched_set_id": matched_set["matched_set_id"],
            "seed": matched_set["seed"],
            "regime": matched_set["behavioral_regime"],
            "policy": policy,
            "witch_uid": "",
            "reconstructable": False,
            "missing_reason": "witch_not_found",
        }

    witch_id = witch.player_id
    death = death_event_for_player(game, witch_id)
    save_event = None
    poison_event = None
    legal_save_opportunities = 0
    missed_save_opportunities = 0
    legal_poison_opportunities = 0
    missed_poison_opportunities = 0
    save_available = True
    poison_available = True
    witch_alive = True

    for event in game.event_log:
        event_type = event.get("event_type")
        content = event.get("content", {})

        if event_type in {"night_kill", "night_kill_prevented"}:
            if witch_alive and save_available:
                legal_save_opportunities += 1
                if event_type == "night_kill":
                    missed_save_opportunities += 1

        if event_type == "witch_save" and content.get("witch") == witch_id:
            save_event = event
            save_available = False

        if event_type in {"witch_poison", "night_kill", "night_kill_prevented"}:
            if witch_alive and poison_available:
                legal_poison_opportunities += 1
                if event_type != "witch_poison":
                    missed_poison_opportunities += 1

        if event_type == "witch_poison" and content.get("witch") == witch_id:
            poison_event = event
            poison_available = False

        if event_type == "player_death":
            if content.get("player") == witch_id:
                witch_alive = False

    save_target = (
        player_by_id(game, save_event.get("content", {}).get("saved_player"))
        if save_event else None
    )
    poison_target = (
        player_by_id(game, poison_event.get("content", {}).get("poisoned_player"))
        if poison_event else None
    )
    save_event_category = save_category(save_target) if save_event else ""
    poison_event_category = poison_category(poison_target) if poison_event else ""

    save_used = save_event is not None
    poison_used = poison_event is not None
    save_available_at_death = int((not save_used) and death is not None)
    poison_available_at_death = int((not poison_used) and death is not None)
    save_available_at_game_end = int((not save_used) and death is None)
    poison_available_at_game_end = int((not poison_used) and death is None)
    primary_save_waste = int(save_used and is_primary_save_waste(save_event_category))
    primary_poison_waste = int(
        poison_used and is_primary_poison_waste(poison_event_category)
    )

    row = {
        "game_id": game_id,
        "matched_set_id": matched_set["matched_set_id"],
        "seed": matched_set["seed"],
        "regime": matched_set["behavioral_regime"],
        "policy": policy,
        "witch_uid": witch_id,
        "reconstructable": True,
        "missing_reason": "",
        "save_available_start": 1,
        "poison_available_start": 1,
        "save_used": int(save_used),
        "poison_used": int(poison_used),
        "save_round": save_event.get("round") if save_event else "",
        "poison_round": poison_event.get("round") if poison_event else "",
        "save_target_uid": save_target.player_id if save_target else "",
        "poison_target_uid": poison_target.player_id if poison_target else "",
        "save_target_team": player_team(save_target),
        "poison_target_team": player_team(poison_target),
        "save_target_role": save_target.role if save_target else "",
        "poison_target_role": poison_target.role if poison_target else "",
        "save_event_category": save_event_category,
        "poison_event_category": poison_event_category,
        "save_available_at_death": save_available_at_death,
        "poison_available_at_death": poison_available_at_death,
        "save_available_at_game_end": save_available_at_game_end,
        "poison_available_at_game_end": poison_available_at_game_end,
        "legal_save_opportunities": legal_save_opportunities,
        "legal_poison_opportunities": legal_poison_opportunities,
        "missed_save_opportunities": missed_save_opportunities,
        "missed_poison_opportunities": missed_poison_opportunities,
        "primary_save_waste": primary_save_waste,
        "primary_poison_waste": primary_poison_waste,
        "witch_total_payoff": witch_payoff(game, witch_id),
        "village_win": int(result["winner"] == VILLAGE_TEAM),
    }
    row["extended_save_waste"] = int(is_extended_save_waste(row))
    row["extended_poison_waste"] = int(is_extended_poison_waste(row))
    row["total_primary_potion_waste_count"] = (
        row["primary_save_waste"] + row["primary_poison_waste"]
    )
    row["total_extended_potion_waste_count"] = (
        row["extended_save_waste"] + row["extended_poison_waste"]
    )
    row["total_potion_waste_cost"] = potion_waste_cost(row)
    return row


def potion_waste_cost(row):
    cost = 0.0
    if row.get("primary_save_waste"):
        cost -= 0.2
    if row.get("primary_poison_waste"):
        # Wrong poison uses the proposal-aligned poison-villager penalty.
        cost -= 0.5
    return cost


WITCH_LIFECYCLE_FIELDS = [
    "game_id",
    "matched_set_id",
    "seed",
    "regime",
    "policy",
    "witch_uid",
    "reconstructable",
    "missing_reason",
    "save_available_start",
    "poison_available_start",
    "save_used",
    "poison_used",
    "save_round",
    "poison_round",
    "save_target_uid",
    "poison_target_uid",
    "save_target_team",
    "poison_target_team",
    "save_target_role",
    "poison_target_role",
    "save_event_category",
    "poison_event_category",
    "save_available_at_death",
    "poison_available_at_death",
    "save_available_at_game_end",
    "poison_available_at_game_end",
    "legal_save_opportunities",
    "legal_poison_opportunities",
    "missed_save_opportunities",
    "missed_poison_opportunities",
    "primary_save_waste",
    "primary_poison_waste",
    "extended_save_waste",
    "extended_poison_waste",
    "total_primary_potion_waste_count",
    "total_extended_potion_waste_count",
    "total_potion_waste_cost",
    "witch_total_payoff",
    "village_win",
]
