import random

from bow_lexicon import BOW_LEXICON, DEFAULT_NUM_TOKENS, SPEECH_TYPES
from seat_order_neutral import SPEECH_SUBSEED_SCHEME, get_actor_uid, stable_seed


TARGETED_SPEECH_TYPES = {
    "accuse",
    "agree",
    "question",
    "trust",
}


def build_speech_rng(player, game_state):
    suspicion_bucket = int(player.suspicion_score * 1000)
    alive_count = len(game_state.get_alive_players())
    if getattr(game_state, "seat_order_neutral_mode", False):
        seed = stable_seed(
            SPEECH_SUBSEED_SCHEME,
            getattr(game_state, "neutral_seed", None),
            getattr(game_state, "base_game_index", None),
            game_state.round_number,
            get_actor_uid(player),
            suspicion_bucket,
            alive_count,
        )
        return random.Random(seed)

    seed = (
        game_state.round_number * 1009
        + player.player_id * 9173
        + suspicion_bucket * 37
        + alive_count * 101
    )
    return random.Random(seed)


def choose_speech_type(player, rng=None):
    if rng is None:
        rng = random

    if player.suspicion_score >= 0.6:
        return rng.choice(["defend", "deny", "accuse"])

    if player.suspicion_score >= 0.3:
        return rng.choice(["defend", "question", "accuse", "neutral"])

    return rng.choice(SPEECH_TYPES)


def choose_speech_target(player, game_state, speech_type, rng=None):
    if speech_type not in TARGETED_SPEECH_TYPES:
        return None

    if rng is None:
        rng = random

    candidates = [
        candidate for candidate in game_state.players
        if candidate.alive and candidate.player_id != player.player_id
    ]

    if not candidates:
        return None

    return rng.choice(candidates).player_id


def get_high_p_wolf_target(player, game_state):
    candidates = [
        candidate for candidate in game_state.players
        if candidate.alive and candidate.player_id != player.player_id
    ]

    if not candidates:
        return None

    target = max(
        candidates,
        key=lambda candidate: (
            candidate.p_wolf,
            candidate.suspicion_score,
        ),
    )

    if target.p_wolf <= 0.0 and target.suspicion_score <= 0.0:
        return None

    return target


def apply_risk_preference_to_speech_type(
    player,
    game_state,
    speech_type,
    rng,
):
    preference = getattr(player, "risk_preference", "neutral")

    if preference == "conservative" and speech_type == "accuse":
        if rng.random() < 0.40:
            return "question"

    if preference == "aggressive" and speech_type != "accuse":
        if get_high_p_wolf_target(player, game_state) is not None:
            if rng.random() < 0.20:
                return "accuse"

    return speech_type


def generate_bow_tokens(speech_type, num_tokens=DEFAULT_NUM_TOKENS, rng=None):
    if rng is None:
        rng = random

    words = BOW_LEXICON.get(speech_type, BOW_LEXICON["neutral"])

    if num_tokens >= len(words):
        return rng.sample(words, len(words))

    return rng.sample(words, num_tokens)


def generate_speech_action(
    player,
    game_state,
    num_tokens=DEFAULT_NUM_TOKENS,
    enable_risk_preference=False,
):
    rng = build_speech_rng(player, game_state)
    speech_type = choose_speech_type(player, rng=rng)

    if enable_risk_preference:
        speech_type = apply_risk_preference_to_speech_type(
            player,
            game_state,
            speech_type,
            rng,
        )

    target = choose_speech_target(player, game_state, speech_type, rng=rng)
    tokens = generate_bow_tokens(
        speech_type,
        num_tokens=num_tokens,
        rng=rng,
    )

    return {
        "speaker": player.player_id,
        "speech_type": speech_type,
        "target": target,
        "tokens": tokens,
        "text": " ".join(tokens),
        "speaker_suspicion": player.suspicion_score,
        "speaker_risk_preference": getattr(
            player,
            "risk_preference",
            "neutral",
        ),
    }


if __name__ == "__main__":
    from game_state import GameState
    from player import Player
    from roles import SEER, VILLAGER, WEREWOLF

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, SEER),
    ]
    state = GameState(players)

    for player in state.get_alive_players():
        print(generate_speech_action(player, state))
