"""Deterministic tokenizer for R2 Bag-of-Words speech analysis."""

import re
from collections import Counter


TOKENIZER_VERSION = "r2_english_tokenizer_v1"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "i",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "so",
    "that",
    "the",
    "then",
    "this",
    "to",
    "we",
    "with",
    "you",
}

NEGATION_TERMS = {"no", "not", "never", "none", "cannot"}
ROLE_NORMALIZATION = {
    "werewolf": "wolf",
    "werewolves": "wolf",
    "wolves": "wolf",
    "villagers": "village",
    "villager": "village",
}
PLAYER_PLACEHOLDERS = {
    "player_self",
    "player_target",
    "player_other",
    "player_ref",
}


def normalize_player_references(text, speaker_id=None, target_id=None):
    normalized = str(text)

    if speaker_id is not None:
        normalized = re.sub(
            rf"\b(player|seat|p)\s*#?{int(speaker_id)}\b",
            " PLAYER_SELF ",
            normalized,
            flags=re.IGNORECASE,
        )

    if target_id is not None:
        normalized = re.sub(
            rf"\b(player|seat|p)\s*#?{int(target_id)}\b",
            " PLAYER_TARGET ",
            normalized,
            flags=re.IGNORECASE,
        )

    normalized = re.sub(
        r"\b(player|seat|p)\s*#?\d+\b",
        " PLAYER_OTHER ",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"\b\d+\b",
        " NUMBER ",
        normalized,
    )
    return normalized


def normalize_text(text, speaker_id=None, target_id=None):
    text = normalize_player_references(
        text,
        speaker_id=speaker_id,
        target_id=target_id,
    )
    text = text.replace("PLAYER_SELF", " player_self ")
    text = text.replace("PLAYER_TARGET", " player_target ")
    text = text.replace("PLAYER_OTHER", " player_other ")
    text = re.sub(r"[!?]+", " ! ", text)
    text = re.sub(r"[^A-Za-z_!]+", " ", text)
    text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def tokenize(
    text,
    speaker_id=None,
    target_id=None,
    include_bigrams=True,
    remove_stopwords=True,
):
    normalized = normalize_text(
        text,
        speaker_id=speaker_id,
        target_id=target_id,
    )
    unigrams = re.findall(r"[a-z_!]+", normalized)
    cleaned = []

    for token in unigrams:
        if token == "!":
            cleaned.append("exclamation")
            continue
        if token == "number":
            continue

        token = ROLE_NORMALIZATION.get(token, token)
        if remove_stopwords and token in STOPWORDS and token not in NEGATION_TERMS:
            continue
        cleaned.append(token)

    if not include_bigrams:
        return cleaned

    bigrams = [
        f"{left}__{right}"
        for left, right in zip(cleaned, cleaned[1:])
    ]
    return cleaned + bigrams


def token_counts(text, **kwargs):
    return Counter(tokenize(text, **kwargs))


def build_vocabulary(
    tokenized_rows,
    min_document_frequency=2,
    max_document_frequency_ratio=0.95,
    max_vocabulary_size=300,
    training_split="train",
):
    document_frequency = Counter()
    total_counts = Counter()
    training_rows = [
        row for row in tokenized_rows
        if row.get("dataset_split") == training_split
    ]
    total_documents = len(training_rows)

    for row in training_rows:
        tokens = row.get("tokens", [])
        if isinstance(tokens, str):
            tokens = tokens.split()
        unique_tokens = set(tokens)
        document_frequency.update(unique_tokens)
        total_counts.update(tokens)

    max_document_frequency = max(
        min_document_frequency,
        int(total_documents * max_document_frequency_ratio),
    )
    candidates = [
        token for token, frequency in document_frequency.items()
        if (
            frequency >= min_document_frequency
            and frequency <= max_document_frequency
            and token not in {"number"}
        )
    ]
    candidates.sort(
        key=lambda token: (
            -document_frequency[token],
            -total_counts[token],
            token,
        )
    )
    vocabulary = candidates[:max_vocabulary_size]
    return {
        "tokens": vocabulary,
        "document_frequency": dict(document_frequency),
        "total_counts": dict(total_counts),
        "training_document_count": total_documents,
        "min_document_frequency": min_document_frequency,
        "max_document_frequency_ratio": max_document_frequency_ratio,
        "max_vocabulary_size": max_vocabulary_size,
        "tokenizer_version": TOKENIZER_VERSION,
    }


if __name__ == "__main__":
    sample = "Player 3 is not a wolf, but Seat 4 looks very suspicious!"
    print(tokenize(sample, target_id=3))
