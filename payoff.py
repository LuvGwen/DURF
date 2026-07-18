from roles import WOLF_TEAM, VILLAGE_TEAM


def safe_get_player(game_state, player_id):
    try:
        return game_state.get_player_by_id(player_id)
    except ValueError:
        return None


def calculate_payoffs(game):
    game_state = game.state
    payoffs = {}

    for player in game_state.players:
        if game_state.winner == "draw":
            final_win_bonus = 0.0
        elif player.team == game_state.winner:
            final_win_bonus = 1.0
        else:
            final_win_bonus = -1.0

        payoffs[player.player_id] = {
            "role": player.role,
            "team": player.team,
            "alive": player.alive,
            "final_win_bonus": final_win_bonus,
            "role_action_bonus": 0.0,
            "survival_bonus": 0.2 if player.alive else 0.0,
            "mistake_penalty": 0.0,
            "total_payoff": 0.0,
        }

    for event in game.event_log:
        event_type = event["event_type"]
        content = event["content"]

        if event_type == "night_kill":
            for player in game_state.players:
                if player.team == WOLF_TEAM:
                    payoffs[player.player_id]["role_action_bonus"] += 0.1

        elif event_type == "seer_check":
            seer_id = content.get("seer")
            if seer_id in payoffs:
                if content.get("target_is_wolf"):
                    payoffs[seer_id]["role_action_bonus"] += 0.2
                else:
                    payoffs[seer_id]["role_action_bonus"] += 0.05

        elif event_type == "witch_save":
            witch_id = content.get("witch")
            if witch_id in payoffs:
                payoffs[witch_id]["role_action_bonus"] += 0.2

        elif event_type == "witch_poison":
            witch_id = content.get("witch")
            if witch_id in payoffs:
                if content.get("target_is_wolf"):
                    payoffs[witch_id]["role_action_bonus"] += 0.3
                else:
                    payoffs[witch_id]["mistake_penalty"] += 0.3

        elif event_type == "hunter_shot":
            hunter_id = content.get("hunter")
            if hunter_id in payoffs:
                if content.get("target_is_wolf"):
                    payoffs[hunter_id]["role_action_bonus"] += 0.3
                else:
                    payoffs[hunter_id]["mistake_penalty"] += 0.3

        elif event_type == "day_vote":
            votes = content.get("votes", {})

            for voter_id, target_id in votes.items():
                target = safe_get_player(game_state, target_id)

                if voter_id not in payoffs or target is None:
                    continue

                if target.is_wolf():
                    payoffs[voter_id]["role_action_bonus"] += 0.05
                else:
                    payoffs[voter_id]["mistake_penalty"] += 0.05

    for payoff in payoffs.values():
        payoff["total_payoff"] = (
            payoff["final_win_bonus"]
            + payoff["role_action_bonus"]
            + payoff["survival_bonus"]
            - payoff["mistake_penalty"]
        )

    return payoffs


if __name__ == "__main__":
    from game import Game, create_default_players

    players = create_default_players()
    game = Game(players)
    result = game.run_game(max_rounds=20)

    payoffs = calculate_payoffs(game)

    print("Winner:", game.state.winner)
    print("Payoffs:")
    for player_id, payoff in payoffs.items():
        print(player_id, payoff)
