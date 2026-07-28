"""Guarded R3 BoW belief-integration policies.

The functions here use observable utterance text and existing public belief
state only. Evaluator-only labels such as true role, deception type, future
votes, and winners are intentionally absent from live feature inputs.
"""

import hashlib
import json
from pathlib import Path

from belief_update import SPEECH_P_WOLF_EFFECTS
from bow_feature_extractor import extract_bow_features


R3_BELIEF_POLICIES = [
    "existing_belief",
    "bow_shadow_belief",
    "guarded_bow_010",
    "guarded_bow_020",
    "structured_bow_guarded",
    "pure_bow_diagnostic",
]

R3_BOW_SIGNAL_VARIANTS = {
    "primary": {
        "werewolf": 0.50,
        "information": 0.40,
        "emotion": 0.10,
    },
    "no_emotion_bow": {
        "werewolf": 0.55,
        "information": 0.45,
        "emotion": 0.00,
    },
    "information_only_bow": {
        "werewolf": 0.00,
        "information": 1.00,
        "emotion": 0.00,
    },
    "werewolf_leaning_only": {
        "werewolf": 1.00,
        "information": 0.00,
        "emotion": 0.00,
    },
    "equal_weight_bow": {
        "werewolf": 1.0 / 3.0,
        "information": 1.0 / 3.0,
        "emotion": 1.0 / 3.0,
    },
}

R3_BELIEF_WEIGHTS = {
    "guarded_bow_010": {
        "existing": 0.90,
        "structured": 0.00,
        "bow": 0.10,
    },
    "guarded_bow_020": {
        "existing": 0.80,
        "structured": 0.00,
        "bow": 0.20,
    },
    "structured_bow_guarded": {
        "existing": 0.70,
        "structured": 0.20,
        "bow": 0.10,
    },
}


def clamp01(value):
    return max(0.0, min(1.0, float(value)))


def file_sha256(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def r2_manifest_hashes(results_dir=None):
    if results_dir is None:
        results_dir = Path("results") / "bow_speech_stage_r2"
    results_dir = Path(results_dir)
    vocabulary_manifest_path = results_dir / "bow_vocabulary_manifest.json"
    score_manifest_path = results_dir / "bow_score_definition_manifest.json"
    vocabulary_manifest = load_json(vocabulary_manifest_path)
    score_manifest = load_json(score_manifest_path)
    return {
        "r2_vocabulary_hash": vocabulary_manifest.get("vocabulary_hash"),
        "r2_vocabulary_manifest_file_hash": file_sha256(
            vocabulary_manifest_path
        ),
        "r2_score_definition_hash": file_sha256(score_manifest_path),
        "r2_tokenizer_version": vocabulary_manifest.get(
            "tokenizer_version",
        ),
        "r2_score_feature_extractor_version": score_manifest.get(
            "feature_extractor_version",
        ),
    }


def compute_bow_signal(features, signal_variant="primary"):
    if signal_variant not in R3_BOW_SIGNAL_VARIANTS:
        raise ValueError(f"Unknown R3 BoW signal variant: {signal_variant}")
    weights = R3_BOW_SIGNAL_VARIANTS[signal_variant]
    return clamp01(
        weights["werewolf"] * features["bow_werewolf_leaning_score"]
        + weights["information"] * features["bow_information_density_score"]
        + weights["emotion"] * features["bow_emotional_intensity_score"]
    )


def structured_speech_signal(speech_event):
    speech_type = speech_event.get("speech_type", "neutral")
    effect = SPEECH_P_WOLF_EFFECTS.get(speech_type, 0.0)
    return clamp01(0.5 + 2.0 * effect)


def belief_target_id(speech_event):
    return speech_event.get("target") or speech_event.get("speaker")


def blended(existing_value, bow_signal, structured_signal, policy_name):
    if policy_name == "pure_bow_diagnostic":
        return bow_signal
    if policy_name in R3_BELIEF_WEIGHTS:
        weights = R3_BELIEF_WEIGHTS[policy_name]
        return clamp01(
            weights["existing"] * existing_value
            + weights["structured"] * structured_signal
            + weights["bow"] * bow_signal
        )
    return existing_value


def policy_shadow_values(existing_value, bow_signal, structured_signal):
    output = {
        "shadow_existing_belief": existing_value,
        "shadow_pure_bow_diagnostic": bow_signal,
    }
    for policy_name in [
        "guarded_bow_010",
        "guarded_bow_020",
        "structured_bow_guarded",
    ]:
        output[f"shadow_{policy_name}"] = blended(
            existing_value,
            bow_signal,
            structured_signal,
            policy_name,
        )
    return output


def apply_r3_belief_policy(
    game_state,
    speech_event,
    utterance_row,
    policy_name="existing_belief",
    signal_variant="primary",
):
    if policy_name not in R3_BELIEF_POLICIES:
        raise ValueError(f"Unknown R3 belief policy: {policy_name}")

    target_id = belief_target_id(speech_event)
    target = game_state.get_player_by_id(target_id)
    features = extract_bow_features(
        utterance_row["utterance_text"],
        tokens=utterance_row.get("tokens"),
        speaker_id=speech_event.get("speaker"),
        target_id=speech_event.get("target"),
    )
    bow_signal = compute_bow_signal(features, signal_variant=signal_variant)
    structured_signal = structured_speech_signal(speech_event)
    before_p_wolf = target.p_wolf
    before_suspicion = target.suspicion_score
    after_p_wolf = blended(
        before_p_wolf,
        bow_signal,
        structured_signal,
        policy_name,
    )
    after_suspicion = blended(
        before_suspicion,
        bow_signal,
        structured_signal,
        policy_name,
    )
    live_applied = policy_name in {
        "guarded_bow_010",
        "guarded_bow_020",
        "structured_bow_guarded",
        "pure_bow_diagnostic",
    }

    if live_applied:
        target.p_wolf = after_p_wolf
        target.suspicion_score = after_suspicion
    else:
        after_p_wolf = before_p_wolf
        after_suspicion = before_suspicion

    signal_extremity = abs(bow_signal - 0.5) * 2.0
    shadow_values = policy_shadow_values(
        before_p_wolf,
        bow_signal,
        structured_signal,
    )
    listener_ids = [
        player.player_id
        for player in game_state.get_alive_players()
        if player.player_id != speech_event.get("speaker")
    ]

    return {
        "policy_name": policy_name,
        "signal_variant": signal_variant,
        "speaker": speech_event.get("speaker"),
        "speech_target": speech_event.get("target"),
        "belief_target": target_id,
        "listener_ids": listener_ids,
        "utterance_text": utterance_row["utterance_text"],
        "template_condition": utterance_row["template_condition"],
        "template_family": utterance_row["template_family"],
        "template_id": utterance_row["template_id"],
        "behavioral_regime": utterance_row["behavioral_regime"],
        "known_token_fraction": utterance_row["known_token_fraction"],
        "unknown_token_fraction": utterance_row["unknown_token_fraction"],
        "vocabulary_overlap": utterance_row["vocabulary_overlap"],
        "ngram_novelty": utterance_row["ngram_novelty"],
        "ood_category": utterance_row["ood_category"],
        "missing_feature_count": utterance_row["missing_feature_count"],
        "bow_signal": bow_signal,
        "structured_signal": structured_signal,
        "bow_werewolf_leaning_score": (
            features["bow_werewolf_leaning_score"]
        ),
        "bow_emotional_intensity_score": (
            features["bow_emotional_intensity_score"]
        ),
        "bow_information_density_score": (
            features["bow_information_density_score"]
        ),
        "token_count": features["token_count"],
        "unique_token_count": features["unique_token_count"],
        "before_p_wolf": before_p_wolf,
        "after_p_wolf": after_p_wolf,
        "before_suspicion": before_suspicion,
        "after_suspicion": after_suspicion,
        "p_wolf_delta": after_p_wolf - before_p_wolf,
        "suspicion_delta": after_suspicion - before_suspicion,
        "proposed_guarded_adjustment": (
            shadow_values["shadow_guarded_bow_010"] - before_p_wolf
        ),
        "proposed_pure_bow_adjustment": bow_signal - before_p_wolf,
        "signal_extremity": signal_extremity,
        "score_extremity": signal_extremity,
        "normalization_distance": signal_extremity,
        "live_applied": live_applied,
        **shadow_values,
    }


def manifest_policy_definitions():
    return {
        "belief_policies": R3_BELIEF_POLICIES,
        "bow_signal_variants": R3_BOW_SIGNAL_VARIANTS,
        "belief_weights": R3_BELIEF_WEIGHTS,
    }


if __name__ == "__main__":
    from game import Game
    from bow_r3_template_conditions import render_r3_live_utterance

    game = Game(enable_bow_r3=False)
    speech = {"speaker": 1, "speech_type": "accuse", "target": 2}
    row = render_r3_live_utterance(game.state, speech)
    print(apply_r3_belief_policy(game.state, speech, row, "guarded_bow_010"))
