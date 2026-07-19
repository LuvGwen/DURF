from roles import VILLAGE_TEAM


def can_give_last_words(
    player,
    game_state,
    cause_of_death,
    enable_last_words,
):
    if not enable_last_words:
        return False

    if player is None:
        return False

    if getattr(player, "has_given_last_words", False):
        return False

    if cause_of_death == "voted_out":
        return True

    if (
        cause_of_death == "night_kill"
        and game_state.round_number == 1
    ):
        return True

    return False


def choose_village_team_last_words_target(player, game_state):
    candidates = [
        candidate for candidate in game_state.get_alive_players()
        if candidate.player_id != player.player_id
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda candidate: (
            candidate.p_wolf,
            candidate.suspicion_score,
        ),
    )


def choose_wolf_last_words_target(player, game_state):
    candidates = [
        candidate for candidate in game_state.get_alive_players()
        if (
            candidate.player_id != player.player_id
            and candidate.team == VILLAGE_TEAM
        )
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda candidate: (
            candidate.p_wolf,
            candidate.suspicion_score,
        ),
    )


def generate_last_words(player, game_state, cause_of_death=None):
    if player.is_wolf():
        target = choose_wolf_last_words_target(player, game_state)
        tokens = [
            "last_words",
            "suspicious",
            "trust_me",
            "misleading",
        ]
    else:
        target = choose_village_team_last_words_target(player, game_state)
        tokens = [
            "last_words",
            "suspicious",
            "watch",
            "vote",
        ]

    if target is None:
        tokens = ["last_words", "uncertain"]

    return {
        "type": "last_words",
        "speaker": player.player_id,
        "speaker_role": player.role,
        "speech_type": "last_words",
        "target": target.player_id if target is not None else None,
        "target_role": target.role if target is not None else None,
        "target_is_wolf": (
            target.is_wolf() if target is not None else None
        ),
        "tokens": tokens,
        "cause_of_death": cause_of_death,
    }
