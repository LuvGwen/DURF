"""R6.1 Werewolf aggression versus deep-cover policy presets."""

from __future__ import annotations


R61_WOLF_AGGRESSION_POLICIES = [
    "reference",
    "aggressive_false_accuse",
    "aggressive_kill_restrained_deception",
    "threat_adaptive",
    "deep_cover",
    "minimal_deception",
]


POLICY_GAME_OVERRIDES = {
    "reference": {
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "threat_based",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
    },
    "aggressive_false_accuse": {
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "seer_first",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "false_accuse_only",
        "enable_deception_credibility": True,
    },
    "aggressive_kill_restrained_deception": {
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "seer_first",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "credibility_cost_scale": 1.0,
    },
    "threat_adaptive": {
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "threat_based",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
    },
    "deep_cover": {
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "low_suspicion",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "trust_building_only",
        "enable_deception_credibility": True,
    },
    "minimal_deception": {
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "low_suspicion",
        "enable_wolf_deception": False,
        "enable_deception_credibility": True,
    },
}


def get_r61_wolf_aggression_overrides(policy_name="reference"):
    return dict(POLICY_GAME_OVERRIDES.get(
        policy_name,
        POLICY_GAME_OVERRIDES["reference"],
    ))


if __name__ == "__main__":
    for policy in R61_WOLF_AGGRESSION_POLICIES:
        print(policy, get_r61_wolf_aggression_overrides(policy))
