def safe_get_player(game_state, player_id):
    try:
        return game_state.get_player_by_id(player_id)
    except ValueError:
        return None


def update_suspicion_after_vote(game_state, votes, eliminated_id):
    if not votes:
        return

    for voter_id, target_id in votes.items():
        voter = safe_get_player(game_state, voter_id)
        target = safe_get_player(game_state, target_id)

        if voter is None or target is None:
            continue

        target.update_suspicion(0.05)

        if target.is_wolf():
            voter.update_suspicion(-0.03)
        else:
            voter.update_suspicion(0.03)

    eliminated = safe_get_player(game_state, eliminated_id)

    if eliminated is None:
        return

    for voter_id, target_id in votes.items():
        if target_id != eliminated_id:
            continue

        voter = safe_get_player(game_state, voter_id)

        if voter is None:
            continue

        if eliminated.is_wolf():
            voter.update_suspicion(-0.07)
        else:
            voter.update_suspicion(0.07)


if __name__ == "__main__":
    from player import Player
    from game_state import GameState
    from roles import WEREWOLF, VILLAGER, SEER

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, SEER),
    ]

    state = GameState(players)

    votes = {
        2: 1,
        3: 1,
        1: 2,
    }

    update_suspicion_after_vote(state, votes, eliminated_id=1)

    for player in state.players:
        print(player.player_id, player.role, player.suspicion_score)
