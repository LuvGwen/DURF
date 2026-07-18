from speaker_memory import get_average_trust_received


def calculate_trust_multiplier(
    game_state,
    speaker_id,
    min_multiplier=0.4,
    max_multiplier=1.4,
):
    average_trust = get_average_trust_received(game_state, speaker_id)

    return (
        min_multiplier
        + average_trust * (max_multiplier - min_multiplier)
    )


if __name__ == "__main__":
    from game_state import GameState
    from player import Player
    from roles import VILLAGER, WEREWOLF
    from speaker_memory import initialize_speaker_memory, update_speaker_trust

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, VILLAGER),
    ]
    state = GameState(players)
    initialize_speaker_memory(players)
    update_speaker_trust(players[1], 1, -0.2, "test_low_trust")

    print(calculate_trust_multiplier(state, 1))
