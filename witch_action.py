import random

from risk_preference import clamp
from roles import WITCH
from seat_order_neutral import choose_neutral_candidate, neutral_tie_break_value


def perform_witch_save(game_state, killed_player_id, save_probability=0.7):
    alive_witches = [
        player for player in game_state.players
        if player.alive and player.role == WITCH
    ]

    if not alive_witches:
        return False, None

    if getattr(game_state, "seat_order_neutral_mode", False):
        witch = choose_neutral_candidate(
            game_state,
            alive_witches,
            "witch_save_actor",
            acting_player=None,
        )
    else:
        witch = random.choice(alive_witches)

    if not witch.has_antidote:
        return False, None

    if killed_player_id is None:
        return False, None

    if random.random() >= save_probability:
        return False, None

    witch.has_antidote = False
    return True, {
        "witch": witch.player_id,
        "saved_player": killed_player_id,
        "used_antidote": True,
    }


def perform_witch_poison(
    game_state,
    suspicion_threshold=0.6,
    excluded_witch_ids=None,
    enable_risk_preference=False,
):
    if excluded_witch_ids is None:
        excluded_witch_ids = set()

    alive_witches = [
        player for player in game_state.players
        if (
            player.alive
            and player.role == WITCH
            and player.player_id not in excluded_witch_ids
        )
    ]

    if not alive_witches:
        return None, None

    if getattr(game_state, "seat_order_neutral_mode", False):
        witch = choose_neutral_candidate(
            game_state,
            alive_witches,
            "witch_poison_actor",
            acting_player=None,
        )
    else:
        witch = random.choice(alive_witches)

    if not witch.has_poison:
        return None, None

    threshold_used = suspicion_threshold

    if enable_risk_preference:
        preference = getattr(witch, "risk_preference", "neutral")

        if preference == "conservative":
            threshold_used += 0.15
        elif preference == "aggressive":
            threshold_used -= 0.10

        threshold_used = clamp(threshold_used, 0.0, 1.0)

    candidates = [
        player for player in game_state.players
        if player.alive and player.player_id != witch.player_id
    ]

    if not candidates:
        return None, None

    if getattr(game_state, "seat_order_neutral_mode", False):
        target = sorted(
            candidates,
            key=lambda player: (
                -player.suspicion_score,
                neutral_tie_break_value(
                    game_state,
                    "witch_poison_target_tie",
                    witch,
                    player,
                ),
            ),
        )[0]
    else:
        target = max(candidates, key=lambda player: player.suspicion_score)

    if target.suspicion_score < threshold_used:
        return None, None

    witch.has_poison = False
    event = {
        "witch": witch.player_id,
        "poisoned_player": target.player_id,
        "target_role": target.role,
        "target_is_wolf": target.is_wolf(),
        "target_suspicion": target.suspicion_score,
        "used_poison": True,
    }

    if enable_risk_preference:
        event["witch_risk_preference"] = getattr(
            witch,
            "risk_preference",
            "neutral",
        )
        event["poison_threshold_used"] = threshold_used

    return target.player_id, event


if __name__ == "__main__":
    from player import Player
    from game_state import GameState
    from roles import WEREWOLF, VILLAGER, WITCH

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, WITCH),
    ]

    state = GameState(players)

    saved, save_event = perform_witch_save(
        state,
        killed_player_id=2,
        save_probability=1.0,
    )
    print("Save:", saved, save_event)

    players[0].suspicion_score = 0.8
    poison_target_id, poison_event = perform_witch_poison(
        state,
        suspicion_threshold=0.6,
    )
    print("Poison:", poison_target_id, poison_event)

    for player in state.players:
        print(player.to_dict())
