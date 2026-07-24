import random

from bow_lexicon import DEFAULT_NUM_TOKENS
from deception_credibility import (
    count_accusations_by_speaker,
    count_recent_self_defenses,
    count_recent_trust_building,
)
from roles import HUNTER, SEER, VILLAGER, WITCH
from risk_preference import clamp, get_risk_multiplier
from seat_order_neutral import SPEECH_SUBSEED_SCHEME, get_actor_uid, stable_seed
from speech_action import generate_bow_tokens


DECEPTION_TYPES = [
    "false_accuse",
    "false_defend",
    "false_role_claim",
    "deflect_suspicion",
    "trust_building",
]

EXPERIMENT_WOLF_DECEPTION_STRATEGIES = [
    "mixed",
    "adaptive",
] + DECEPTION_TYPES

DECEPTION_STRATEGY_ALIASES = {
    "false_accuse_only": "false_accuse",
    "false_defend_only": "false_defend",
    "false_role_claim_only": "false_role_claim",
    "deflect_suspicion_only": "deflect_suspicion",
    "trust_building_only": "trust_building",
}

SUPPORTED_WOLF_DECEPTION_STRATEGIES = (
    EXPERIMENT_WOLF_DECEPTION_STRATEGIES
    + list(DECEPTION_STRATEGY_ALIASES)
)

DECEPTION_TO_SPEECH_TYPE = {
    "false_accuse": "accuse",
    "false_defend": "defend",
    "false_role_claim": "claim_role",
    "deflect_suspicion": "question",
    "trust_building": "trust",
}

FALSE_CLAIM_ROLES = [
    SEER,
    WITCH,
    HUNTER,
    VILLAGER,
]


def build_deception_rng(wolf, game_state):
    suspicion_bucket = int(wolf.suspicion_score * 1000)
    alive_count = len(game_state.get_alive_players())
    if getattr(game_state, "seat_order_neutral_mode", False):
        seed = stable_seed(
            SPEECH_SUBSEED_SCHEME,
            "wolf_deception",
            getattr(game_state, "neutral_seed", None),
            getattr(game_state, "base_game_index", None),
            game_state.round_number,
            get_actor_uid(wolf),
            suspicion_bucket,
            alive_count,
        )
        return random.Random(seed)

    seed = (
        game_state.round_number * 2027
        + wolf.player_id * 7919
        + suspicion_bucket * 53
        + alive_count * 149
    )
    return random.Random(seed)


def get_alive_non_wolves(game_state):
    return [
        player for player in game_state.players
        if player.alive and not player.is_wolf()
    ]


def get_alive_wolf_teammates(wolf, game_state):
    return [
        player for player in game_state.players
        if (
            player.alive
            and player.is_wolf()
            and player.player_id != wolf.player_id
        )
    ]


def deception_pressure(player):
    return (player.suspicion_score + player.p_wolf) / 2.0


def get_most_pressured_teammate(wolf, game_state):
    teammates = get_alive_wolf_teammates(wolf, game_state)

    if not teammates:
        return None

    return max(teammates, key=deception_pressure)


def get_best_false_accuse_target(game_state):
    non_wolves = get_alive_non_wolves(game_state)

    if not non_wolves:
        return None

    return max(non_wolves, key=deception_pressure)


def count_wrong_accusation_penalties(event_log, speaker_id):
    if event_log is None:
        return 0

    penalty_count = 0

    for event in event_log:
        if event.get("event_type") != "wrong_accusation_penalty":
            continue

        for penalty in event.get("content", {}).get("penalties", []):
            if penalty.get("speaker") == speaker_id:
                penalty_count += 1

    return penalty_count


def count_self_defense_costs(event_log, speaker_id):
    if event_log is None:
        return 0

    cost_count = 0

    for event in event_log:
        if event.get("event_type") != "self_defense_credibility_cost":
            continue

        if event.get("content", {}).get("speaker") == speaker_id:
            cost_count += 1

    return cost_count


def estimate_false_accuse_risk(wolf, game_state, event_log=None):
    accusation_count = (
        count_accusations_by_speaker(event_log, wolf.player_id)
        if event_log is not None
        else 0
    )
    wrong_penalty_count = count_wrong_accusation_penalties(
        event_log,
        wolf.player_id,
    )
    wolf_pressure = deception_pressure(wolf)

    return (
        0.10 * accusation_count
        + 0.18 * wrong_penalty_count
        + wolf_pressure
    )


def estimate_self_defense_risk(wolf, event_log=None):
    if event_log is None:
        return deception_pressure(wolf)

    recent_self_defenses = count_recent_self_defenses(
        event_log,
        wolf.player_id,
    )
    self_defense_costs = count_self_defense_costs(event_log, wolf.player_id)

    return (
        0.12 * recent_self_defenses
        + 0.16 * self_defense_costs
        + deception_pressure(wolf)
    )


def estimate_trust_building_risk(wolf, event_log=None):
    if event_log is None:
        return deception_pressure(wolf)

    recent_trust_building = count_recent_trust_building(
        event_log,
        wolf.player_id,
    )

    return (
        0.10 * recent_trust_building
        + deception_pressure(wolf)
    )


def choose_adaptive_deception_type(
    wolf,
    game_state,
    event_log=None,
    rng=None,
):
    if rng is None:
        rng = random

    wolf_pressure = deception_pressure(wolf)
    teammate = get_most_pressured_teammate(wolf, game_state)
    teammate_pressure = deception_pressure(teammate) if teammate else 0.0
    accuse_target = get_best_false_accuse_target(game_state)
    target_pressure = deception_pressure(accuse_target) if accuse_target else 0.0
    false_accuse_risk = estimate_false_accuse_risk(
        wolf,
        game_state,
        event_log=event_log,
    )
    self_defense_risk = estimate_self_defense_risk(
        wolf,
        event_log=event_log,
    )
    trust_building_risk = estimate_trust_building_risk(
        wolf,
        event_log=event_log,
    )

    if teammate_pressure >= 0.65 and wolf_pressure < 0.25:
        return "false_defend"

    if false_accuse_risk >= 0.35:
        if self_defense_risk >= 0.30:
            if accuse_target is not None and target_pressure >= 0.18:
                return "false_accuse"
            if trust_building_risk < 0.35:
                return "trust_building"
        if wolf_pressure < 0.10 and rng.random() < 0.20:
            return "trust_building"
        return "deflect_suspicion"

    if self_defense_risk >= 0.30:
        if accuse_target is not None and target_pressure >= 0.14:
            return "false_accuse"
        if trust_building_risk < 0.35:
            return "trust_building"

    if wolf_pressure >= 0.35 and target_pressure <= 0.0:
        return "deflect_suspicion"

    if accuse_target is not None and target_pressure >= 0.12:
        return "false_accuse"

    if rng.random() < 0.20:
        return "trust_building"

    return "deflect_suspicion"


def choose_deception_type(
    wolf,
    game_state,
    strategy="mixed",
    event_log=None,
    rng=None,
):
    if rng is None:
        rng = random

    strategy = DECEPTION_STRATEGY_ALIASES.get(strategy, strategy)

    if strategy in DECEPTION_TYPES:
        return strategy

    if strategy == "adaptive":
        return choose_adaptive_deception_type(
            wolf,
            game_state,
            event_log=event_log,
            rng=rng,
        )

    if strategy != "mixed":
        raise ValueError(f"Unknown wolf deception strategy: {strategy}")

    teammates = get_alive_wolf_teammates(wolf, game_state)

    if wolf.suspicion_score >= 0.4:
        return rng.choice([
            "deflect_suspicion",
            "false_accuse",
            "false_role_claim",
        ])

    if teammates:
        return rng.choice(DECEPTION_TYPES)

    return rng.choice([
        "false_accuse",
        "false_role_claim",
        "deflect_suspicion",
        "trust_building",
    ])


def choose_deception_target(
    wolf,
    game_state,
    deception_type,
    strategy="mixed",
    rng=None,
):
    if rng is None:
        rng = random

    non_wolves = get_alive_non_wolves(game_state)
    teammates = get_alive_wolf_teammates(wolf, game_state)

    if deception_type in {"false_accuse", "deflect_suspicion"}:
        if not non_wolves:
            return None
        if strategy == "adaptive":
            target = max(non_wolves, key=deception_pressure)
            if deception_pressure(target) >= 0.30:
                return target.player_id
        return rng.choice(non_wolves).player_id

    if deception_type == "false_defend":
        if teammates:
            if strategy == "adaptive":
                return max(teammates, key=deception_pressure).player_id
            return rng.choice(teammates).player_id
        if non_wolves:
            return rng.choice(non_wolves).player_id
        return None

    if deception_type == "trust_building":
        if not non_wolves:
            return None
        return rng.choice(non_wolves).player_id

    return None


def choose_false_claim_role(rng=None):
    if rng is None:
        rng = random

    return rng.choice(FALSE_CLAIM_ROLES)


def generate_deception_tokens(
    deception_type,
    speech_type,
    false_claim_role=None,
    num_tokens=DEFAULT_NUM_TOKENS,
    rng=None,
):
    tokens = generate_bow_tokens(
        speech_type,
        num_tokens=num_tokens,
        rng=rng,
    )

    if deception_type == "false_role_claim" and false_claim_role is not None:
        if false_claim_role not in tokens:
            tokens[-1] = false_claim_role

    return tokens


def generate_wolf_deception_action(
    wolf,
    game_state,
    strategy="mixed",
    event_log=None,
    num_tokens=DEFAULT_NUM_TOKENS,
    enable_risk_preference=False,
    base_deception_probability=1.0,
):
    strategy = DECEPTION_STRATEGY_ALIASES.get(strategy, strategy)
    rng = build_deception_rng(wolf, game_state)

    if enable_risk_preference:
        deception_probability = clamp(
            base_deception_probability
            * get_risk_multiplier(wolf, high_risk=True),
            0.0,
            1.0,
        )

        if rng.random() > deception_probability:
            return None
    else:
        deception_probability = base_deception_probability

    deception_type = choose_deception_type(
        wolf,
        game_state,
        strategy=strategy,
        event_log=event_log,
        rng=rng,
    )
    speech_type = DECEPTION_TO_SPEECH_TYPE[deception_type]
    target = choose_deception_target(
        wolf,
        game_state,
        deception_type,
        strategy=strategy,
        rng=rng,
    )
    false_claim_role = None

    if deception_type == "false_role_claim":
        false_claim_role = choose_false_claim_role(rng=rng)

    tokens = generate_deception_tokens(
        deception_type,
        speech_type,
        false_claim_role=false_claim_role,
        num_tokens=num_tokens,
        rng=rng,
    )

    event = {
        "speaker": wolf.player_id,
        "speech_type": speech_type,
        "deception_type": deception_type,
        "target": target,
        "tokens": tokens,
        "text": " ".join(tokens),
        "speaker_suspicion": wolf.suspicion_score,
        "is_deception": True,
        "deception_strategy": strategy,
        "false_claim_role": false_claim_role,
    }

    if enable_risk_preference:
        event["wolf_risk_preference"] = getattr(
            wolf,
            "risk_preference",
            "neutral",
        )
        event["deception_probability_used"] = deception_probability

    return event


def perform_wolf_deception(
    game_state,
    wolf,
    deception_policy="mixed",
    event_log=None,
    num_tokens=DEFAULT_NUM_TOKENS,
    enable_risk_preference=False,
):
    return generate_wolf_deception_action(
        wolf,
        game_state,
        strategy=deception_policy,
        event_log=event_log,
        num_tokens=num_tokens,
        enable_risk_preference=enable_risk_preference,
    )


if __name__ == "__main__":
    from game_state import GameState
    from player import Player
    from roles import SEER, VILLAGER, WEREWOLF

    players = [
        Player(1, WEREWOLF),
        Player(2, WEREWOLF),
        Player(3, VILLAGER),
        Player(4, SEER),
    ]
    state = GameState(players)

    wolf = state.get_alive_wolves()[0]

    for strategy in EXPERIMENT_WOLF_DECEPTION_STRATEGIES:
        print(generate_wolf_deception_action(
            wolf,
            state,
            strategy=strategy,
        ))
