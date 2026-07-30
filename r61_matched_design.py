"""Matched design utilities for R6.1 targeted role-strategy experiments."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


DEVELOPMENT_SEEDS = list(range(500, 510))
VALIDATION_SEEDS = list(range(510, 515))
FINAL_SEEDS = list(range(520, 540))
OOD_STRESS_SEEDS = list(range(540, 550))

BEHAVIORAL_REGIMES = [
    "baseline",
    "speech_enabled",
    "herding_enabled",
    "deception_enabled",
    "heterogeneous_risk",
    "strong_village_information",
    "weak_village_information",
    "high_emotional_speech",
    "low_information_speech",
    "mixed_strategies",
]

R61_MATCHED_SETS_PER_MODULE = 1000
REPLICATES_PER_SEED_REGIME = 5


def stable_int_seed(*parts):
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:12], 16)


def generate_r61_matched_sets(
    seeds=None,
    regimes=None,
    replicates_per_seed_regime=REPLICATES_PER_SEED_REGIME,
):
    if seeds is None:
        seeds = FINAL_SEEDS
    if regimes is None:
        regimes = BEHAVIORAL_REGIMES

    rows = []
    for seed in seeds:
        for regime in regimes:
            for replicate_index in range(1, replicates_per_seed_regime + 1):
                matched_set_id = (
                    f"r61_seed{seed}_{regime}_rep{replicate_index:02d}"
                )
                rows.append({
                    "matched_set_id": matched_set_id,
                    "seed": seed,
                    "seed_split": "final_evaluation",
                    "behavioral_regime": regime,
                    "replicate_index": replicate_index,
                    "game_seed": stable_int_seed(
                        "r61",
                        seed,
                        regime,
                        replicate_index,
                    ),
                })
    return rows


def validate_seed_isolation():
    final_or_stress = set(FINAL_SEEDS) | set(OOD_STRESS_SEEDS)
    development_or_validation = set(DEVELOPMENT_SEEDS) | set(VALIDATION_SEEDS)
    return not bool(final_or_stress & development_or_validation)


def write_seed_registry(path):
    rows = []
    for split, seeds, role in [
        ("development", DEVELOPMENT_SEEDS, "policy design only"),
        ("validation", VALIDATION_SEEDS, "smoke validation only"),
        ("final_evaluation", FINAL_SEEDS, "formal matched inference"),
        ("ood_stress", OOD_STRESS_SEEDS, "future stress testing"),
    ]:
        for seed in seeds:
            rows.append({"seed": seed, "seed_split": split, "usage": role})
    write_csv(path, rows, ["seed", "seed_split", "usage"])


def write_regime_registry(path):
    rows = [
        {
            "behavioral_regime": regime,
            "description": describe_behavioral_regime(regime),
        }
        for regime in BEHAVIORAL_REGIMES
    ]
    write_csv(path, rows, ["behavioral_regime", "description"])


def describe_behavioral_regime(regime):
    descriptions = {
        "baseline": "Roles active with no speech, herding, deception, or trust memory.",
        "speech_enabled": "Structured speech enabled without herding or deception.",
        "herding_enabled": "Speech plus herding pressure enabled.",
        "deception_enabled": "Adaptive wolf deception with credibility costs enabled.",
        "heterogeneous_risk": "Mixed player risk preferences enabled.",
        "strong_village_information": "Trust, role priors, repeat-safe seer checks, and stronger village information.",
        "weak_village_information": "Lower speech signal and weaker trust/information environment.",
        "high_emotional_speech": "Stronger speech and herding effects.",
        "low_information_speech": "Speech exists but suspicion update and trust memory are weak.",
        "mixed_strategies": "Combined speech, trust, herding, role prior, deception, and risk preference.",
    }
    return descriptions.get(regime, "")


def write_csv(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            restval="",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    rows = generate_r61_matched_sets()
    print(len(rows), rows[0], validate_seed_isolation())
