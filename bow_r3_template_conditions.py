"""R3 live utterance rendering and template-shift diagnostics.

This module converts already-observable structured speech events into
deterministic text used by guarded BoW policies. It does not inspect true
roles, future outcomes, seeds, game ids, or evaluator-only labels.
"""

import csv
from pathlib import Path

from bow_tokenizer import tokenize


R3_TEMPLATE_CONDITIONS = [
    "in_distribution_templates",
    "unseen_template_families",
    "paraphrased_template_families",
]

R3_TEMPLATE_CONDITION_REGISTRY = [
    {
        "template_condition": "in_distribution_templates",
        "description": "Surface forms similar to R2 primary template families.",
        "ood_category": "in_distribution",
    },
    {
        "template_condition": "unseen_template_families",
        "description": "Held-out surface forms not used for R2 training.",
        "ood_category": "strong_template_shift",
    },
    {
        "template_condition": "paraphrased_template_families",
        "description": "Rule-based paraphrases preserving speech semantics.",
        "ood_category": "mild_template_shift",
    },
]

R3_BEHAVIORAL_REGIMES = [
    "baseline_speech",
    "herding_enabled",
    "deception_enabled",
    "heterogeneous_risk",
    "strong_village_information",
    "weak_village_information",
    "high_emotional_speech",
    "high_low_information_speech",
    "mixed_structured_speech",
    "unseen_speech_regime",
]

PRIMARY_TEMPLATES = {
    "accuse": "I suspect PLAYER_TARGET because the vote logic looks weak.",
    "defend": "I defend PLAYER_TARGET because the record looks honest.",
    "claim_role": "I have a role claim and want the village to hear it.",
    "deny": "I am not wolf, and that push is a misread.",
    "agree": "I agree with that read and support the pressure.",
    "question": "Why should we trust the evidence on PLAYER_TARGET?",
    "trust": "I trust PLAYER_TARGET for now because the plan is clear.",
    "neutral": "I am still listening and comparing the public record.",
}

DECEPTION_TEMPLATES = {
    "false_accuse": "I am certain PLAYER_TARGET is wolf; vote there now.",
    "false_defend": "PLAYER_TARGET looks clear, and that pressure is wrong.",
    "false_role_claim": "I claim ROLE_CLAIM, and that should guide this vote.",
    "deflect_suspicion": "Do not focus on me; PLAYER_TARGET is the better question.",
    "trust_building": "I trust PLAYER_TARGET, and we should coordinate together.",
}

UNSEEN_TEMPLATES = {
    "accuse": "The public trail points at PLAYER_TARGET, so test that slot.",
    "defend": "The case on PLAYER_TARGET is thin compared with the record.",
    "claim_role": "My claimed role should be weighed as public information.",
    "deny": "That read on me does not fit the sequence of play.",
    "agree": "That interpretation matches my current read of the table.",
    "question": "What concrete reason makes PLAYER_TARGET the best target?",
    "trust": "PLAYER_TARGET seems safe enough to coordinate with today.",
    "neutral": "My read is unsettled, so I want one more piece of evidence.",
}

UNSEEN_DECEPTION_TEMPLATES = {
    "false_accuse": "Everyone should push PLAYER_TARGET before the danger spreads.",
    "false_defend": "The suspicion on PLAYER_TARGET feels manufactured.",
    "false_role_claim": "My ROLE_CLAIM claim gives me authority in this vote.",
    "deflect_suspicion": "The push on me is a frame; shift attention to PLAYER_TARGET.",
    "trust_building": "PLAYER_TARGET and I can keep the vote organized.",
}

PARAPHRASE_REPLACEMENTS = [
    ("suspect", "doubt"),
    ("vote", "ballot"),
    ("logic", "reasoning"),
    ("record", "history"),
    ("pressure", "push"),
    ("trust", "read as safe"),
    ("wolf", "hidden threat"),
    ("evidence", "public signal"),
]


def load_r2_vocabulary(path=None):
    if path is None:
        path = Path("results/bow_speech_stage_r2/bow_vocabulary.csv")

    if not Path(path).exists():
        return set()

    with Path(path).open(newline="", encoding="utf-8") as handle:
        return {row["token"] for row in csv.DictReader(handle)}


def normalize_speech_type(content):
    speech_type = content.get("speech_type") or "neutral"
    if speech_type not in PRIMARY_TEMPLATES:
        return "neutral"
    return speech_type


def template_for_content(content, template_condition):
    deception_type = content.get("deception_type")

    if template_condition == "unseen_template_families":
        if deception_type in UNSEEN_DECEPTION_TEMPLATES:
            return (
                UNSEEN_DECEPTION_TEMPLATES[deception_type],
                f"r3_unseen_{deception_type}",
            )
        speech_type = normalize_speech_type(content)
        return UNSEEN_TEMPLATES[speech_type], f"r3_unseen_{speech_type}"

    if deception_type in DECEPTION_TEMPLATES:
        return (
            DECEPTION_TEMPLATES[deception_type],
            f"r3_primary_{deception_type}",
        )

    speech_type = normalize_speech_type(content)
    return PRIMARY_TEMPLATES[speech_type], f"r3_primary_{speech_type}"


def apply_rule_based_paraphrase(text):
    output = text
    for old, new in PARAPHRASE_REPLACEMENTS:
        output = output.replace(old, new)
    return output


def apply_regime_surface_shift(text, behavioral_regime):
    if behavioral_regime == "high_emotional_speech":
        return f"{text} This is urgent!"
    if behavioral_regime == "high_low_information_speech":
        return "Maybe this is unclear, but I am unsure and waiting."
    if behavioral_regime == "unseen_speech_regime":
        return f"{text} The table signal feels noisy and unusual."
    return text


def classify_template_shift(template_condition, known_token_fraction):
    if template_condition == "in_distribution_templates":
        return "in_distribution"
    if template_condition == "paraphrased_template_families":
        return "mild_template_shift"
    if known_token_fraction < 0.50:
        return "strong_template_shift"
    return "mild_template_shift"


def render_r3_live_utterance(
    game_state,
    speech_event,
    template_condition="in_distribution_templates",
    behavioral_regime="baseline_speech",
    source_event_index=0,
):
    if template_condition not in R3_TEMPLATE_CONDITIONS:
        raise ValueError(f"Unknown R3 template condition: {template_condition}")

    text, template_id = template_for_content(speech_event, template_condition)
    if template_condition == "paraphrased_template_families":
        text = apply_rule_based_paraphrase(text)
        template_id = template_id.replace("primary", "paraphrased")

    text = apply_regime_surface_shift(text, behavioral_regime)
    target_id = speech_event.get("target")
    speaker_id = speech_event.get("speaker")
    false_claim_role = speech_event.get("false_claim_role") or "role"
    text = text.replace("ROLE_CLAIM", str(false_claim_role))
    text = text.replace(
        "PLAYER_TARGET",
        "PLAYER_TARGET" if target_id is not None else "PLAYER_OTHER",
    )

    tokens = tokenize(text, speaker_id=speaker_id, target_id=target_id)
    vocab = load_r2_vocabulary()
    known_count = sum(1 for token in tokens if token in vocab)
    known_fraction = known_count / len(tokens) if tokens else 0.0
    unknown_fraction = 1.0 - known_fraction if tokens else 0.0
    ngram_novelty = (
        sum(1 for token in tokens if "__" in token and token not in vocab)
        / len(tokens)
        if tokens else 0.0
    )
    ood_category = classify_template_shift(template_condition, known_fraction)

    return {
        "round": game_state.round_number,
        "phase": game_state.phase,
        "speaker": speaker_id,
        "target": target_id,
        "utterance_text": text,
        "tokens": tokens,
        "template_condition": template_condition,
        "template_family": template_id.rsplit("_", 1)[0],
        "template_id": template_id,
        "behavioral_regime": behavioral_regime,
        "source_event_index": source_event_index,
        "known_token_fraction": known_fraction,
        "unknown_token_fraction": unknown_fraction,
        "vocabulary_overlap": known_fraction,
        "ngram_novelty": ngram_novelty,
        "ood_category": ood_category,
        "missing_feature_count": 0,
    }


def template_condition_registry_rows():
    return [dict(row) for row in R3_TEMPLATE_CONDITION_REGISTRY]


def behavioral_regime_registry_rows():
    return [
        {
            "behavioral_regime": regime,
            "description": regime.replace("_", " "),
        }
        for regime in R3_BEHAVIORAL_REGIMES
    ]


if __name__ == "__main__":
    from game import Game

    game = Game(enable_bow_r3=False)
    event = {
        "speaker": 1,
        "speech_type": "accuse",
        "target": 2,
    }
    print(render_r3_live_utterance(game.state, event))
