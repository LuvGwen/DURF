"""Transparent BoW feature extraction for R2 speech quantification."""

from collections import Counter

from bow_lexicon import CORE_LEXICON_BY_TOKEN, CORE_LEXICON_VERSION
from bow_tokenizer import NEGATION_TERMS, PLAYER_PLACEHOLDERS, tokenize


FEATURE_EXTRACTOR_VERSION = "r2_bow_feature_extractor_v1"
VAGUE_TOKENS = {"maybe", "unsure", "unclear", "possible", "wait", "think"}
CAUSAL_TOKENS = {"because", "reason", "logic", "evidence", "pattern"}


def clamp01(value):
    return max(0.0, min(1.0, float(value)))


def unigram_tokens(tokens):
    return [token for token in tokens if "__" not in token]


def count_semantic_group(tokens, semantic_group):
    return sum(
        1 for token in tokens
        if CORE_LEXICON_BY_TOKEN.get(token, {}).get("semantic_group")
        == semantic_group
    )


def extract_bow_features(
    text,
    tokens=None,
    speaker_id=None,
    target_id=None,
):
    if tokens is None:
        tokens = tokenize(text, speaker_id=speaker_id, target_id=target_id)

    token_counter = Counter(tokens)
    unigrams = unigram_tokens(tokens)
    unigram_count = len(unigrams)
    unique_unigram_count = len(set(unigrams))
    denominator = max(1, unigram_count)
    lexicon_items = [
        (token, CORE_LEXICON_BY_TOKEN[token], count)
        for token, count in token_counter.items()
        if token in CORE_LEXICON_BY_TOKEN
    ]

    wolf_weight_sum = sum(
        row["werewolf_leaning_weight"] * count
        for token, row, count in lexicon_items
    )
    intensity_sum = sum(
        row["intensity_weight"] * count
        for token, row, count in lexicon_items
    )
    information_sum = sum(
        row["information_weight"] * count
        for token, row, count in lexicon_items
    )
    exclamation_count = token_counter.get("exclamation", 0)
    vague_count = sum(token_counter[token] for token in VAGUE_TOKENS)
    causal_count = sum(token_counter[token] for token in CAUSAL_TOKENS)
    placeholder_count = sum(
        token_counter[token] for token in PLAYER_PLACEHOLDERS
    )
    unique_ratio = unique_unigram_count / denominator

    werewolf_leaning_score = clamp01(
        0.5 + wolf_weight_sum / (2.0 * denominator)
    )
    emotional_intensity_score = clamp01(
        (intensity_sum + exclamation_count * 0.20) / denominator
    )
    information_density_score = clamp01(
        (
            information_sum / denominator
            + unique_ratio * 0.20
            + min(0.20, placeholder_count * 0.05)
            + min(0.15, causal_count * 0.05)
            - min(0.20, vague_count * 0.04)
        )
    )

    return {
        "bow_werewolf_leaning_score": werewolf_leaning_score,
        "bow_emotional_intensity_score": emotional_intensity_score,
        "bow_information_density_score": information_density_score,
        "token_count": len(tokens),
        "unique_token_count": len(set(tokens)),
        "unigram_count": unigram_count,
        "unique_unigram_count": unique_unigram_count,
        "type_token_ratio": unique_ratio,
        "negation_count": sum(token_counter[token] for token in NEGATION_TERMS),
        "accusation_lexicon_count": count_semantic_group(
            unigrams,
            "accusation",
        ),
        "defense_lexicon_count": count_semantic_group(unigrams, "defense"),
        "trust_lexicon_count": count_semantic_group(unigrams, "trust"),
        "role_claim_count": count_semantic_group(unigrams, "role_claim"),
        "certainty_count": count_semantic_group(unigrams, "certainty"),
        "uncertainty_count": count_semantic_group(unigrams, "uncertainty"),
        "emotional_term_count": count_semantic_group(
            unigrams,
            "emotional_intensity",
        ),
        "evidence_term_count": count_semantic_group(unigrams, "evidence"),
        "manipulation_term_count": count_semantic_group(
            unigrams,
            "deception",
        ) + count_semantic_group(unigrams, "misinformation"),
        "player_reference_count": placeholder_count,
        "exclamation_count": exclamation_count,
        "vague_word_count": vague_count,
        "causal_connector_count": causal_count,
    }


def score_definition_manifest():
    return {
        "feature_extractor_version": FEATURE_EXTRACTOR_VERSION,
        "core_lexicon_version": CORE_LEXICON_VERSION,
        "score_ranges": {
            "bow_werewolf_leaning_score": "[0, 1]",
            "bow_emotional_intensity_score": "[0, 1]",
            "bow_information_density_score": "[0, 1]",
        },
        "formulas": {
            "bow_werewolf_leaning_score": (
                "clip01(0.5 + sum(token.werewolf_leaning_weight * count) "
                "/ (2 * unigram_count))"
            ),
            "bow_emotional_intensity_score": (
                "clip01((sum(token.intensity_weight * count) + "
                "0.20 * exclamation_count) / unigram_count)"
            ),
            "bow_information_density_score": (
                "clip01(mean information weight + 0.20 * type-token ratio + "
                "player-reference, causal-connector bonuses - vague-word "
                "penalty)"
            ),
        },
        "normalization": (
            "All primary scores are clipped to [0, 1]. Empty utterances use "
            "a denominator of 1 and therefore remain valid."
        ),
    }


if __name__ == "__main__":
    sample = "I suspect PLAYER_TARGET because the vote history is suspicious!"
    print(extract_bow_features(sample))
