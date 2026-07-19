import random


RISK_PREFERENCES = [
    "conservative",
    "neutral",
    "aggressive",
]

RISK_MULTIPLIERS = {
    "conservative": 0.80,
    "neutral": 1.00,
    "aggressive": 1.20,
}

HIGH_RISK_ACTION_MULTIPLIERS = {
    "conservative": 0.60,
    "neutral": 1.00,
    "aggressive": 1.40,
}

MIXED_WEIGHTS = {
    "conservative": 0.30,
    "neutral": 0.40,
    "aggressive": 0.30,
}

CONSERVATIVE_MAJORITY_WEIGHTS = {
    "conservative": 0.60,
    "neutral": 0.30,
    "aggressive": 0.10,
}

AGGRESSIVE_MAJORITY_WEIGHTS = {
    "conservative": 0.10,
    "neutral": 0.30,
    "aggressive": 0.60,
}


def clamp(value, lower=0.0, upper=1.0):
    return max(lower, min(upper, value))


def choose_weighted_preference(weights, rng):
    draw = rng.random()
    cumulative = 0.0

    for preference in RISK_PREFERENCES:
        cumulative += weights.get(preference, 0.0)

        if draw <= cumulative:
            return preference

    return "neutral"


def choose_role_based_preference(player, rng):
    if player.is_wolf():
        weights = {
            "conservative": 0.15,
            "neutral": 0.30,
            "aggressive": 0.55,
        }
    elif player.role in {"seer", "witch", "hunter"}:
        weights = {
            "conservative": 0.45,
            "neutral": 0.40,
            "aggressive": 0.15,
        }
    else:
        weights = MIXED_WEIGHTS

    return choose_weighted_preference(weights, rng)


def assign_risk_preferences(players, mode="mixed", seed=None):
    rng = random.Random(seed) if seed is not None else random

    if mode == "all_neutral":
        for player in players:
            player.risk_preference = "neutral"
        return players

    if mode == "mixed":
        weights = MIXED_WEIGHTS
    elif mode == "conservative_majority":
        weights = CONSERVATIVE_MAJORITY_WEIGHTS
    elif mode == "aggressive_majority":
        weights = AGGRESSIVE_MAJORITY_WEIGHTS
    elif mode == "role_based":
        for player in players:
            player.risk_preference = choose_role_based_preference(player, rng)
        return players
    else:
        raise ValueError(f"Unknown risk preference mode: {mode}")

    for player in players:
        player.risk_preference = choose_weighted_preference(weights, rng)

    return players


def get_risk_multiplier(player, high_risk=False):
    preference = getattr(player, "risk_preference", "neutral")

    if high_risk:
        return HIGH_RISK_ACTION_MULTIPLIERS.get(preference, 1.0)

    return RISK_MULTIPLIERS.get(preference, 1.0)
