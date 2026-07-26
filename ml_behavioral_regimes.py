from copy import deepcopy

from config import DEFAULT_HERDING_ALPHA, DEFAULT_HERDING_BETA, DEFAULT_HERDING_GAMMA
from ten_player_seer_position_experiment import SEER_POSITION_BASE_CONFIG


BEHAVIORAL_REGIMES = [
    {
        "behavioral_regime_id": "baseline_rule_policy",
        "description": "Structured ten-player rule policy with speech disabled.",
        "split_level": "A_in_distribution",
        "config_updates": {
            "enable_speech": False,
            "enable_herding": False,
            "enable_wolf_deception": False,
            "enable_deception_credibility": False,
            "enable_speaker_memory": False,
            "enable_risk_preference": False,
            "seer_check_strategy": "information_gain_proxy",
            "wolf_kill_strategy": "seer_first",
            "use_suspicion_voting": True,
        },
    },
    {
        "behavioral_regime_id": "randomized_legal_policy",
        "description": "Random legal voting, random seer checks, and random wolf kills.",
        "split_level": "A_in_distribution",
        "config_updates": {
            "enable_speech": False,
            "enable_herding": False,
            "enable_wolf_strategy": False,
            "enable_wolf_deception": False,
            "enable_deception_credibility": False,
            "enable_speaker_memory": False,
            "enable_risk_preference": False,
            "seer_check_strategy": "random",
            "use_suspicion_voting": False,
        },
    },
    {
        "behavioral_regime_id": "mixed_rule_policy",
        "description": "Mixed social-deduction mechanisms without wolf deception.",
        "split_level": "A_in_distribution",
        "config_updates": {
            "enable_speech": True,
            "enable_herding": True,
            "enable_role_prior": True,
            "enable_wolf_strategy": True,
            "enable_wolf_deception": False,
            "enable_deception_credibility": False,
            "enable_speaker_memory": True,
            "trust_vote_weight": 0.20,
            "seer_check_strategy": "highest_p_wolf",
            "wolf_kill_strategy": "threat_based",
            "use_suspicion_voting": True,
        },
    },
    {
        "behavioral_regime_id": "seat_order_neutral_policy",
        "description": "Seat-order-neutral source games with deterministic physical-seat tie breaking.",
        "split_level": "A_in_distribution",
        "config_updates": {
            "enable_speech": False,
            "enable_herding": False,
            "enable_wolf_deception": False,
            "enable_deception_credibility": False,
            "enable_speaker_memory": False,
            "enable_risk_preference": False,
            "seat_order_neutral_mode": True,
            "neutral_seed": 42,
            "seer_check_strategy": "random_neutral",
            "wolf_kill_strategy": "random",
            "use_suspicion_voting": False,
        },
    },
    {
        "behavioral_regime_id": "speech_and_herding_policy",
        "description": "Speech and herding enabled without role prior, deception, or risk preferences.",
        "split_level": "A_in_distribution",
        "config_updates": {
            "enable_speech": True,
            "enable_herding": True,
            "enable_role_prior": False,
            "enable_wolf_strategy": True,
            "enable_wolf_deception": False,
            "enable_deception_credibility": False,
            "enable_speaker_memory": True,
            "trust_vote_weight": 0.15,
            "seer_check_strategy": "highest_suspicion",
            "wolf_kill_strategy": "threat_based",
            "use_suspicion_voting": True,
        },
    },
    {
        "behavioral_regime_id": "deception_enabled_policy",
        "description": "Adaptive wolf deception with credibility and speaker memory enabled.",
        "split_level": "C_out_of_distribution",
        "config_updates": {
            "enable_speech": True,
            "enable_herding": True,
            "enable_role_prior": True,
            "enable_wolf_strategy": True,
            "enable_wolf_deception": True,
            "wolf_deception_strategy": "adaptive",
            "enable_deception_credibility": True,
            "enable_speaker_memory": True,
            "trust_vote_weight": 0.20,
            "seer_check_strategy": "information_gain_proxy",
            "wolf_kill_strategy": "seer_first",
            "use_suspicion_voting": True,
        },
    },
    {
        "behavioral_regime_id": "risk_heterogeneous_policy",
        "description": "Role-based risk preferences with speech and herding enabled.",
        "split_level": "C_out_of_distribution",
        "config_updates": {
            "enable_speech": True,
            "enable_herding": True,
            "enable_role_prior": True,
            "enable_wolf_strategy": True,
            "enable_wolf_deception": True,
            "wolf_deception_strategy": "adaptive",
            "enable_deception_credibility": True,
            "enable_speaker_memory": True,
            "enable_risk_preference": True,
            "risk_preference_mode": "role_based",
            "trust_vote_weight": 0.20,
            "seer_check_strategy": "coverage_balanced",
            "wolf_kill_strategy": "low_suspicion",
            "use_suspicion_voting": True,
        },
    },
]


CONTINUATION_POLICIES = [
    {
        "continuation_policy_id": "baseline_rule_policy",
        "description": "Rule policy without speech/deception continuation.",
        "config_updates": BEHAVIORAL_REGIMES[0]["config_updates"],
    },
    {
        "continuation_policy_id": "randomized_legal_policy",
        "description": "Random legal continuation where supported.",
        "config_updates": BEHAVIORAL_REGIMES[1]["config_updates"],
    },
    {
        "continuation_policy_id": "mixed_rule_policy",
        "description": "Mixed speech/herding continuation without deception.",
        "config_updates": BEHAVIORAL_REGIMES[2]["config_updates"],
    },
    {
        "continuation_policy_id": "seat_order_neutral_policy",
        "description": "Seat-order-neutral deterministic tie-breaking continuation where supported.",
        "config_updates": BEHAVIORAL_REGIMES[3]["config_updates"],
    },
    {
        "continuation_policy_id": "speech_and_herding_policy",
        "description": "Speech and herding continuation without deception.",
        "config_updates": BEHAVIORAL_REGIMES[4]["config_updates"],
    },
    {
        "continuation_policy_id": "deception_enabled_policy",
        "description": "Adaptive wolf deception continuation.",
        "config_updates": BEHAVIORAL_REGIMES[5]["config_updates"],
    },
    {
        "continuation_policy_id": "risk_heterogeneous_policy",
        "description": "Risk-heterogeneous continuation with adaptive wolf deception.",
        "config_updates": BEHAVIORAL_REGIMES[6]["config_updates"],
    },
]


def get_stage15_base_config():
    config = dict(SEER_POSITION_BASE_CONFIG)
    config.update({
        "enable_position_model": True,
        "randomize_seat_roles": True,
        "seer_avoid_repeat_checks": True,
        "enable_hunter": True,
        "enable_witch": True,
        "enable_seer": True,
        "enable_suspicion_update": True,
        "herding_alpha": DEFAULT_HERDING_ALPHA,
        "herding_beta": DEFAULT_HERDING_BETA,
        "herding_gamma": DEFAULT_HERDING_GAMMA,
    })
    return config


def get_behavioral_regimes():
    return deepcopy(BEHAVIORAL_REGIMES)


def get_continuation_policies():
    return deepcopy(CONTINUATION_POLICIES)


def build_config_for_regime(regime):
    config = get_stage15_base_config()
    config.update(regime.get("config_updates", {}))
    return config
