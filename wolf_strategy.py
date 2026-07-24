import random

from roles import HUNTER, SEER, VILLAGER, WITCH
from seat_order_neutral import choose_neutral_candidate, neutral_tie_break_value


ROLE_THREAT = {
    SEER: 0.45,
    WITCH: 0.35,
    HUNTER: 0.25,
    VILLAGER: 0.05,
}

SUPPORTED_WOLF_KILL_STRATEGIES = [
    "random",
    "threat_based",
    "seer_first",
    "witch_first",
    "avoid_hunter",
    "low_suspicion",
]


def get_wolf_kill_candidates(game_state):
    return [
        player for player in game_state.players
        if player.alive and not player.is_wolf() and player.is_villager_team()
    ]


def calculate_threat_components(candidate, noise_level=0.05):
    role_threat = ROLE_THREAT.get(candidate.role, 0.05)
    information_threat = max(0.0, 0.20 * (1.0 - candidate.p_wolf))
    trust_threat = max(0.0, 0.20 * (1.0 - candidate.suspicion_score))

    survival_threat = 0.05
    if candidate.role == WITCH:
        if candidate.has_antidote:
            survival_threat += 0.05
        if candidate.has_poison:
            survival_threat += 0.05
    elif candidate.role == SEER:
        survival_threat += 0.05
    elif candidate.role == HUNTER:
        survival_threat += 0.03

    random_noise = random.uniform(0, noise_level)

    threat_score = (
        role_threat
        + information_threat
        + trust_threat
        + survival_threat
        + random_noise
    )

    return {
        "role_threat": role_threat,
        "information_threat": information_threat,
        "trust_threat": trust_threat,
        "survival_threat": survival_threat,
        "random_noise": random_noise,
        "threat_score": threat_score,
    }


def calculate_threat_score(candidate, noise_level=0.05):
    return calculate_threat_components(
        candidate,
        noise_level=noise_level,
    )["threat_score"]


def calculate_strategy_score(candidate, strategy, noise_level=0.05):
    components = calculate_threat_components(
        candidate,
        noise_level=noise_level,
    )

    if strategy == "threat_based":
        return components["threat_score"]

    if strategy == "seer_first":
        role_priority = 1.0 if candidate.role == SEER else 0.0
        return (
            role_priority
            + 0.10 * components["threat_score"]
            + components["random_noise"]
        )

    if strategy == "witch_first":
        role_priority = 1.0 if candidate.role == WITCH else 0.0
        return (
            role_priority
            + 0.10 * components["threat_score"]
            + components["random_noise"]
        )

    if strategy == "avoid_hunter":
        hunter_penalty = 1.0 if candidate.role == HUNTER else 0.0
        return components["threat_score"] - hunter_penalty

    if strategy == "low_suspicion":
        return (
            0.80 * (1.0 - candidate.suspicion_score)
            + 0.20 * (1.0 - candidate.p_wolf)
            + components["random_noise"]
        )

    raise ValueError(f"Unknown wolf kill strategy: {strategy}")


def choose_wolf_kill_target(
    game_state,
    strategy="threat_based",
    noise_level=0.05,
):
    candidates = get_wolf_kill_candidates(game_state)

    if not candidates:
        return None

    if strategy == "random":
        if getattr(game_state, "seat_order_neutral_mode", False):
            return choose_neutral_candidate(
                game_state,
                candidates,
                "wolf_random_kill",
                acting_player=None,
            )
        return random.choice(candidates)

    if strategy not in SUPPORTED_WOLF_KILL_STRATEGIES:
        raise ValueError(f"Unknown wolf kill strategy: {strategy}")

    scored_candidates = []
    for candidate in candidates:
        score = calculate_strategy_score(
            candidate,
            strategy=strategy,
            noise_level=noise_level,
        )
        if getattr(game_state, "seat_order_neutral_mode", False):
            tie_break = neutral_tie_break_value(
                game_state,
                "wolf_kill_tie",
                None,
                candidate,
            )
        else:
            tie_break = 0.0
        scored_candidates.append((score, tie_break, candidate))

    if getattr(game_state, "seat_order_neutral_mode", False):
        scored_candidates.sort(key=lambda item: (-item[0], item[1]))
    else:
        scored_candidates.sort(key=lambda item: item[0], reverse=True)

    return scored_candidates[0][2]


if __name__ == "__main__":
    from player import Player
    from game_state import GameState
    from roles import WEREWOLF, VILLAGER, SEER, WITCH, HUNTER

    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, SEER),
        Player(4, WITCH),
        Player(5, HUNTER),
    ]

    players[1].suspicion_score = 0.8
    players[2].p_wolf = 0.0
    players[3].p_wolf = 0.2

    state = GameState(players)

    for strategy in SUPPORTED_WOLF_KILL_STRATEGIES:
        target = choose_wolf_kill_target(
            state,
            strategy=strategy,
            noise_level=0.0,
        )

        print(
            f"{strategy} wolf target:",
            target.player_id,
            target.role,
        )
