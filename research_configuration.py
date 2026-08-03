"""Explicit research configuration manifests for R6.2."""

from __future__ import annotations

import hashlib
import json

from config import TEN_PLAYER_ROLE_SETUP


R4_MANIFEST_HASH = "eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd"
R5_METRIC_MANIFEST_HASH = "4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf"


def configuration_hash(config):
    payload = {
        key: value for key, value in config.items()
        if key != "configuration_hash"
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def historical_default_configuration(source_commit=""):
    config = {
        "configuration_name": "historical_default_configuration",
        "configuration_version": "r62_v1",
        "purpose": "Preserve project historical simulator behavior.",
        "historical_default_unchanged": True,
        "role_composition": list(TEN_PLAYER_ROLE_SETUP),
        "activation": "implicit legacy defaults only",
        "notes": "This manifest records defaults; it does not modify code.",
        "source_commit": source_commit,
    }
    config["configuration_hash"] = configuration_hash(config)
    return config


def recommended_research_configuration(source_commit=""):
    components = {
        "villager_voting_policy": {
            "value": "trust_weighted_structured",
            "evidence_source": "R6.1",
            "evidence_grade": "A",
            "confidence": "high within tested strategy space",
            "status": "statistically supported improvement",
        },
        "seer_checking_policy": {
            "value": "random_or_diversified_reference",
            "evidence_source": "R6 and R6.1",
            "evidence_grade": "B",
            "confidence": "moderate",
            "status": "retain reference; reject highest_suspicion/highest_p_wolf/edge-seat theory",
        },
        "seer_reveal_policy": {
            "value": "private_reference",
            "evidence_source": "R6.1 and R6.2",
            "evidence_grade": "B",
            "confidence": "moderate for current reference",
            "status": "immediate_reveal remains experimental candidate",
        },
        "witch_joint_policy": {
            "value": "reference",
            "evidence_source": "R6.1 and R6.2",
            "evidence_grade": "B",
            "confidence": "low to moderate",
            "status": "aggressive_full remains experimental candidate with waste warning",
        },
        "hunter_policy": {
            "value": "reference",
            "evidence_source": "R6.1",
            "evidence_grade": "B",
            "confidence": "moderate",
            "status": "no_shot and conservative_threshold rejected",
        },
        "werewolf_night_kill_policy": {
            "value": "threat_based",
            "evidence_source": "R6.1",
            "evidence_grade": "B",
            "confidence": "moderate",
            "status": "reference/threat_adaptive retained; random kill and deep_cover rejected",
        },
        "werewolf_deception_policy": {
            "value": "adaptive_with_credibility_costs",
            "evidence_source": "Stage 3 through R6.1",
            "evidence_grade": "B",
            "confidence": "moderate",
            "status": "credibility-constrained deception only",
        },
        "speech_policy": {
            "value": "structured_speech_enabled",
            "evidence_source": "Stage 2 through R6",
            "evidence_grade": "B",
            "confidence": "moderate",
            "status": "live BoW contribution disabled",
        },
        "herding_policy": {
            "value": "guarded_configurable",
            "evidence_source": "Stage 4 and R6.1",
            "evidence_grade": "C",
            "confidence": "low to moderate",
            "status": "trust-weighted voting is primary recommendation",
        },
        "bow_mode": {
            "value": "shadow_diagnostics_only",
            "evidence_source": "R3 and R6",
            "evidence_grade": "E for live deployment",
            "confidence": "high rejection for live override",
            "status": "disabled for live decisions",
        },
        "ml_mode": {
            "value": "diagnostic_only",
            "evidence_source": "ML Stage 2A/2B and R6",
            "evidence_grade": "E for deployment",
            "confidence": "moderate",
            "status": "continuous and hybrid ML disabled",
        },
    }
    config = {
        "configuration_name": "recommended_research_configuration",
        "configuration_version": "r62_v1",
        "purpose": "Explicit opt-in research configuration for final analysis inputs.",
        "historical_default_unchanged": True,
        "role_composition": list(TEN_PLAYER_ROLE_SETUP),
        "components": components,
        "unresolved_candidates": [
            "seer_immediate_reveal",
            "witch_aggressive_full",
            "villager_guarded_herding",
        ],
        "rejected_alternatives": [
            "villager_random_vote",
            "live_guarded_bow",
            "structured_plus_bow_live",
            "seer_highest_suspicion",
            "seer_highest_p_wolf",
            "edge_seat_checking_theory",
            "hunter_no_shot",
            "hunter_conservative_threshold",
            "wolf_random_kill",
            "wolf_deep_cover",
            "continuous_frozen_ml",
            "hybrid_frozen_ml",
        ],
        "payoff_manifest_hash": R4_MANIFEST_HASH,
        "financial_metric_manifest_hash": R5_METRIC_MANIFEST_HASH,
        "source_commit": source_commit,
        "explicit_activation_command": "python3 run_recommended_configuration.py",
    }
    config["configuration_hash"] = configuration_hash(config)
    return config


def experimental_candidate_configuration(source_commit=""):
    config = {
        "configuration_name": "experimental_candidate_configuration",
        "configuration_version": "r62_v1",
        "purpose": "Promising but uncertain components requiring future inference.",
        "historical_default_unchanged": True,
        "role_composition": list(TEN_PLAYER_ROLE_SETUP),
        "candidates": {
            "seer_reveal_policy": "immediate_reveal",
            "witch_joint_policy": "aggressive_full",
            "villager_herding_policy": "guarded_herding",
        },
        "source_commit": source_commit,
    }
    config["configuration_hash"] = configuration_hash(config)
    return config


def recommended_game_kwargs():
    return {
        "role_setup": TEN_PLAYER_ROLE_SETUP,
        "initial_p_wolf": 0.30,
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": True,
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "threat_based",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "trust_vote_weight": 0.20,
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": True,
        "witch_poison_threshold": 0.15,
        "witch_save_probability": 0.70,
        "seer_check_strategy": "alternate_sides",
        "seer_avoid_repeat_checks": True,
        "enable_position_model": True,
        "randomize_seat_roles": True,
        "enable_bow_r3": False,
        "enable_ml_wolf_kill_policy": False,
        "enable_ml_stage2b_policy": False,
        "enable_r61_villager_voting_policy": True,
        "r61_villager_voting_policy": "trust_weighted",
        "enable_r61_seer_reveal_policy": False,
        "enable_r61_witch_joint_policy": False,
        "enable_r61_hunter_policy": False,
        "enable_r61_wolf_aggression_policy": False,
    }
