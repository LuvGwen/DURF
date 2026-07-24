from roles import HUNTER
from seat_order_neutral import neutral_tie_break_value


def perform_hunter_shot(game_state, dead_player_id):
    try:
        hunter = game_state.get_player_by_id(dead_player_id)
    except ValueError:
        return None, None

    if hunter.role != HUNTER:
        return None, None

    candidates = [
        player for player in game_state.players
        if player.alive and player.player_id != hunter.player_id
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
                    "hunter_shot_target_tie",
                    hunter,
                    player,
                ),
            ),
        )[0]
    else:
        target = max(candidates, key=lambda player: player.suspicion_score)

    return target.player_id, {
        "hunter": hunter.player_id,
        "shot_target": target.player_id,
        "target_role": target.role,
        "target_is_wolf": target.is_wolf(),
        "target_suspicion": target.suspicion_score,
    }


if __name__ == "__main__":
    from player import Player
    from game_state import GameState
    from roles import WEREWOLF, VILLAGER, HUNTER

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, HUNTER),
    ]

    state = GameState(players)

    players[0].suspicion_score = 0.8
    players[1].suspicion_score = 0.2

    state.kill_player(3)

    target_id, event = perform_hunter_shot(state, dead_player_id=3)

    print(target_id)
    print(event)
