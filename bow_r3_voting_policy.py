"""R3 BoW-informed village voting policies."""


R3_VOTE_POLICIES = [
    "existing_vote",
    "bow_shadow_vote",
    "guarded_bow_vote_010",
    "structured_bow_vote",
    "pure_bow_vote_diagnostic",
    "selective_bow_vote_override",
]

SELECTIVE_OVERRIDE_DEFAULTS = {
    "candidate_margin_threshold": 0.08,
    "minimum_information_density": 0.12,
    "maximum_emotional_only_intensity": 0.55,
    "allowed_ood_categories": [
        "in_distribution",
        "mild_template_shift",
    ],
}


def clamp01(value):
    return max(0.0, min(1.0, float(value)))


def valid_candidates(voter, candidates):
    return [
        candidate for candidate in candidates
        if candidate.alive and candidate.player_id != voter.player_id
    ]


def candidate_existing_score(candidate):
    return clamp01(
        0.60 * candidate.suspicion_score + 0.40 * candidate.p_wolf
    )


def candidate_signal(candidate, signal_by_player):
    return signal_by_player.get(candidate.player_id, {})


def bow_signal_for_candidate(candidate, signal_by_player):
    return float(candidate_signal(candidate, signal_by_player).get(
        "bow_signal",
        0.5,
    ))


def structured_signal_for_candidate(candidate, signal_by_player):
    return float(candidate_signal(candidate, signal_by_player).get(
        "structured_signal",
        0.5,
    ))


def vote_policy_score(candidate, signal_by_player, policy_name):
    existing = candidate_existing_score(candidate)
    bow = bow_signal_for_candidate(candidate, signal_by_player)
    structured = structured_signal_for_candidate(candidate, signal_by_player)

    if policy_name == "pure_bow_vote_diagnostic":
        return bow

    if policy_name == "structured_bow_vote":
        return clamp01(0.70 * existing + 0.20 * structured + 0.10 * bow)

    return clamp01(0.90 * existing + 0.10 * bow)


def top_candidate(voter, candidates, signal_by_player, policy_name):
    scored = [
        (
            vote_policy_score(candidate, signal_by_player, policy_name),
            -candidate.player_id,
            candidate,
        )
        for candidate in valid_candidates(voter, candidates)
    ]
    if not scored:
        return None, 0.0, []
    scored.sort(reverse=True)
    return scored[0][2], scored[0][0], scored


def emotional_only_signal(signal):
    information_density = float(signal.get("bow_information_density_score", 0.0))
    emotional_intensity = float(signal.get("bow_emotional_intensity_score", 0.0))
    werewolf_leaning = float(signal.get("bow_werewolf_leaning_score", 0.5))
    return (
        emotional_intensity >= SELECTIVE_OVERRIDE_DEFAULTS[
            "maximum_emotional_only_intensity"
        ]
        and information_density < SELECTIVE_OVERRIDE_DEFAULTS[
            "minimum_information_density"
        ]
        and werewolf_leaning <= 0.55
    )


def selective_override_allowed(
    existing_target,
    bow_target,
    scored_candidates,
    signal_by_player,
    template_condition,
    selective_override_margin,
    selective_min_information_density,
):
    if existing_target is None or bow_target is None:
        return False, "missing_target"
    if existing_target.player_id == bow_target.player_id:
        return False, "same_target"
    if template_condition == "unseen_template_families":
        return False, "strong_template_shift"

    top_score = scored_candidates[0][0] if scored_candidates else 0.0
    runner_up_score = scored_candidates[1][0] if len(scored_candidates) > 1 else 0.0
    margin = top_score - runner_up_score
    signal = signal_by_player.get(bow_target.player_id, {})
    information_density = float(signal.get("bow_information_density_score", 0.0))
    ood_category = signal.get("ood_category", "in_distribution")

    if margin < selective_override_margin:
        return False, "insufficient_margin"
    if information_density < selective_min_information_density:
        return False, "low_information_density"
    if ood_category not in SELECTIVE_OVERRIDE_DEFAULTS["allowed_ood_categories"]:
        return False, "ood_guardrail"
    if emotional_only_signal(signal):
        return False, "emotional_only_signal"
    return True, "override_allowed"


def build_shadow_recommendations(voter, candidates, signal_by_player):
    recommendations = {}
    for policy_name in [
        "guarded_bow_vote_010",
        "structured_bow_vote",
        "pure_bow_vote_diagnostic",
    ]:
        target, score, _ = top_candidate(
            voter,
            candidates,
            signal_by_player,
            policy_name,
        )
        recommendations[policy_name] = {
            "target": target.player_id if target is not None else None,
            "score": score,
        }
    return recommendations


def choose_r3_vote_target(
    voter,
    candidates,
    game_state,
    policy_name="existing_vote",
    existing_target=None,
    signal_by_player=None,
    template_condition="in_distribution_templates",
    selective_override_margin=0.08,
    selective_min_information_density=0.12,
):
    if policy_name not in R3_VOTE_POLICIES:
        raise ValueError(f"Unknown R3 vote policy: {policy_name}")
    signal_by_player = signal_by_player or {}
    existing_id = existing_target.player_id if existing_target is not None else None
    selected_target = existing_target
    selected_reason = "existing_vote"
    selected_score = (
        candidate_existing_score(existing_target)
        if existing_target is not None
        else 0.0
    )
    shadow_recommendations = build_shadow_recommendations(
        voter,
        candidates,
        signal_by_player,
    )
    bow_target, bow_score, scored = top_candidate(
        voter,
        candidates,
        signal_by_player,
        "guarded_bow_vote_010",
    )

    if policy_name == "bow_shadow_vote":
        selected_reason = "shadow_only_existing_executed"
    elif policy_name in {
        "guarded_bow_vote_010",
        "structured_bow_vote",
        "pure_bow_vote_diagnostic",
    }:
        selected_target, selected_score, _ = top_candidate(
            voter,
            candidates,
            signal_by_player,
            policy_name,
        )
        selected_reason = policy_name
    elif policy_name == "selective_bow_vote_override":
        allowed, reason = selective_override_allowed(
            existing_target,
            bow_target,
            scored,
            signal_by_player,
            template_condition,
            selective_override_margin,
            selective_min_information_density,
        )
        if allowed:
            selected_target = bow_target
            selected_score = bow_score
        selected_reason = reason

    selected_id = (
        selected_target.player_id if selected_target is not None else None
    )
    selected_signal = signal_by_player.get(selected_id, {})
    return selected_target, {
        "policy_name": policy_name,
        "voter": voter.player_id,
        "existing_target": existing_id,
        "selected_target": selected_id,
        "bow_guarded_target": (
            shadow_recommendations["guarded_bow_vote_010"]["target"]
        ),
        "structured_bow_target": (
            shadow_recommendations["structured_bow_vote"]["target"]
        ),
        "pure_bow_target": (
            shadow_recommendations["pure_bow_vote_diagnostic"]["target"]
        ),
        "selected_reason": selected_reason,
        "selected_score": selected_score,
        "disagrees_with_existing": selected_id != existing_id,
        "template_condition": template_condition,
        "ood_category": selected_signal.get("ood_category", ""),
        "selected_bow_signal": selected_signal.get("bow_signal", 0.5),
        "selected_information_density": selected_signal.get(
            "bow_information_density_score",
            0.0,
        ),
        "selected_emotional_intensity": selected_signal.get(
            "bow_emotional_intensity_score",
            0.0,
        ),
        "selective_override_margin": selective_override_margin,
        "selective_min_information_density": (
            selective_min_information_density
        ),
        "shadow_recommendations": shadow_recommendations,
    }


def manifest_policy_definitions():
    return {
        "vote_policies": R3_VOTE_POLICIES,
        "selective_override_defaults": SELECTIVE_OVERRIDE_DEFAULTS,
    }


if __name__ == "__main__":
    from player import Player
    from roles import SEER, VILLAGER, WEREWOLF
    from game_state import GameState

    voter = Player(1, VILLAGER)
    wolf = Player(2, WEREWOLF)
    seer = Player(3, SEER)
    state = GameState([voter, wolf, seer])
    target, event = choose_r3_vote_target(
        voter,
        state.players,
        state,
        policy_name="pure_bow_vote_diagnostic",
        existing_target=seer,
        signal_by_player={2: {"bow_signal": 0.9}},
    )
    print(target.player_id, event["selected_reason"])
