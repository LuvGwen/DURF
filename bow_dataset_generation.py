"""Generate the R2 speech-level Bag-of-Words dataset."""

import csv
import hashlib
import json
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from bow_feature_extractor import extract_bow_features, score_definition_manifest
from bow_lexicon import CORE_LEXICON_BY_TOKEN, write_core_lexicon_csv
from bow_speech_generator import (
    SPEECH_GENERATOR_VERSION,
    generate_utterance_from_speech_event,
    template_registry_rows,
)
from bow_tokenizer import TOKENIZER_VERSION, build_vocabulary, tokenize
from config import (
    DEFAULT_MAX_ROUNDS,
    TEN_PLAYER_CREDIBILITY_COST_SCALE,
    TEN_PLAYER_HERDING_WEIGHT_SCALE,
    TEN_PLAYER_INITIAL_P_WOLF,
    TEN_PLAYER_ROLE_SETUP,
    TEN_PLAYER_SPEECH_SIGNAL_SCALE,
)
from game import Game, create_default_players
from ml_observation_builder import compute_score_state


R2_RESULTS_DIR = Path("results") / "bow_speech_stage_r2"
VOCABULARY_SETTINGS = {
    "min_document_frequency": 2,
    "max_document_frequency_ratio": 0.95,
    "max_vocabulary_size": 300,
    "include_bigrams": True,
    "unknown_token_handling": "ignored at vectorization time",
}

PRIMARY_REGIME_IDS = [
    "balanced_social",
    "deception_adaptive",
    "trust_weighted_memory",
    "random_vote_speech",
]
OOD_REGIME_IDS = [
    "risk_heterogeneous",
    "last_words_enabled",
]

R2_SPLIT_PLAN = [
    {
        "dataset_split": "train",
        "seeds": list(range(300, 310)),
        "games_per_seed": 20,
        "regime_ids": PRIMARY_REGIME_IDS,
    },
    {
        "dataset_split": "validation",
        "seeds": list(range(310, 315)),
        "games_per_seed": 10,
        "regime_ids": PRIMARY_REGIME_IDS,
    },
    {
        "dataset_split": "final_test",
        "seeds": list(range(315, 325)),
        "games_per_seed": 10,
        "regime_ids": PRIMARY_REGIME_IDS,
    },
    {
        "dataset_split": "ood_template",
        "seeds": list(range(325, 330)),
        "games_per_seed": 5,
        "regime_ids": PRIMARY_REGIME_IDS,
    },
    {
        "dataset_split": "ood_regime",
        "seeds": list(range(330, 335)),
        "games_per_seed": 10,
        "regime_ids": OOD_REGIME_IDS,
    },
]


def stable_seed(*parts):
    digest = hashlib.sha256(
        "|".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()
    return int(digest[:16], 16) % (2 ** 32)


def current_git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def get_r2_behavioral_regimes():
    base = {
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": True,
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "seer_first",
        "enable_wolf_deception": False,
        "wolf_deception_strategy": "adaptive",
        "enable_deception_credibility": True,
        "enable_speaker_memory": True,
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": True,
        "enable_risk_preference": False,
        "enable_last_words": False,
        "trust_vote_weight": 0.20,
        "speech_signal_scale": TEN_PLAYER_SPEECH_SIGNAL_SCALE,
        "credibility_cost_scale": TEN_PLAYER_CREDIBILITY_COST_SCALE,
        "herding_alpha": 0.5 * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "herding_beta": 0.3 * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "herding_gamma": 0.2 * TEN_PLAYER_HERDING_WEIGHT_SCALE,
        "seer_check_strategy": "information_gain_proxy",
        "seer_avoid_repeat_checks": True,
        "enable_position_model": True,
        "randomize_seat_roles": True,
        "role_setup": TEN_PLAYER_ROLE_SETUP,
        "initial_p_wolf": TEN_PLAYER_INITIAL_P_WOLF,
    }

    regimes = {
        "balanced_social": {
            "behavioral_regime_id": "balanced_social",
            "description": "Speech, role prior, herding, trust memory, and strategic wolf kills without daytime deception.",
            "config": dict(base),
        },
        "deception_adaptive": {
            "behavioral_regime_id": "deception_adaptive",
            "description": "Adaptive wolf deception with credibility costs and speaker memory.",
            "config": {
                **base,
                "enable_wolf_deception": True,
                "wolf_deception_strategy": "adaptive",
            },
        },
        "trust_weighted_memory": {
            "behavioral_regime_id": "trust_weighted_memory",
            "description": "Speaker memory receives stronger vote/speech influence.",
            "config": {
                **base,
                "trust_vote_weight": 0.40,
                "enable_wolf_deception": True,
                "wolf_deception_strategy": "deflect_suspicion",
            },
        },
        "random_vote_speech": {
            "behavioral_regime_id": "random_vote_speech",
            "description": "Speech is generated but day voting and wolf kills are random legal actions.",
            "config": {
                **base,
                "use_suspicion_voting": False,
                "enable_herding": False,
                "enable_role_prior": False,
                "enable_wolf_strategy": False,
                "wolf_kill_strategy": "random",
                "enable_wolf_deception": False,
            },
        },
        "risk_heterogeneous": {
            "behavioral_regime_id": "risk_heterogeneous",
            "description": "Out-of-regime role-based risk preferences with adaptive deception.",
            "config": {
                **base,
                "enable_wolf_deception": True,
                "enable_risk_preference": True,
                "risk_preference_mode": "role_based",
                "seer_check_strategy": "coverage_balanced",
                "wolf_kill_strategy": "low_suspicion",
            },
        },
        "last_words_enabled": {
            "behavioral_regime_id": "last_words_enabled",
            "description": "Out-of-regime last-words speeches added after deaths.",
            "config": {
                **base,
                "enable_wolf_deception": True,
                "enable_last_words": True,
                "wolf_deception_strategy": "mixed",
            },
        },
    }
    return regimes


def get_split_plan():
    return [dict(row) for row in R2_SPLIT_PLAN]


def get_later_day_vote(event_log, source_index, round_number, speaker_id):
    for event in event_log[source_index + 1:]:
        if event.get("event_type") != "day_vote":
            continue
        if event.get("round") != round_number:
            continue
        content = event.get("content", {})
        return {
            "later_vote_target": content.get("votes", {}).get(speaker_id, ""),
            "later_elimination_target": content.get("eliminated", ""),
            "p_wolf_scores": content.get("p_wolf_scores", {}),
            "suspicion_scores": content.get("suspicion_scores", {}),
        }
    return {
        "later_vote_target": "",
        "later_elimination_target": "",
        "p_wolf_scores": {},
        "suspicion_scores": {},
    }


def get_player_by_id(game_state, player_id):
    if player_id in ("", None):
        return None
    try:
        return game_state.get_player_by_id(int(player_id))
    except (TypeError, ValueError):
        return None


def event_flags(row):
    intent = row.get("speech_intent", "")
    deception_type = row.get("deception_type", "")
    return {
        "accusation_flag": str(intent in {
            "accusation",
            "strong_accusation",
            "false_accusation",
            "retaliation",
        }),
        "defense_flag": str(intent in {"defense", "self_defense"}),
        "role_claim_flag": str(intent in {
            "seer_claim",
            "witch_claim",
            "hunter_claim",
            "false_role_claim",
            "counter_claim",
        }),
        "trust_building_flag": str(intent in {
            "trust_building",
            "trust_support",
        }),
        "deflection_flag": str(
            intent == "deflection" or deception_type == "deflect_suspicion"
        ),
        "information_report_flag": str(intent == "information_report"),
    }


def build_utterance_rows_from_game(
    game,
    result,
    game_id,
    seed,
    base_game_index,
    behavioral_regime,
    dataset_split,
):
    rows = []
    event_log = game.event_log
    past_events = []

    for index, event in enumerate(event_log):
        if event.get("event_type") not in {"speech", "last_words"}:
            past_events.append(event)
            continue

        content = event.get("content", {})
        speaker = get_player_by_id(game.state, content.get("speaker"))
        if speaker is None:
            past_events.append(event)
            continue

        score_state = compute_score_state(
            game.state.players,
            past_events,
            initial_p_wolf=TEN_PLAYER_INITIAL_P_WOLF,
        )
        target = get_player_by_id(game.state, content.get("target"))
        generated = generate_utterance_from_speech_event(
            game.state,
            event,
            past_events,
            game_id=game_id,
            seed=seed,
            base_game_index=base_game_index,
            behavioral_regime=behavioral_regime,
            dataset_split=dataset_split,
            source_event_index=index,
        )
        token_list = tokenize(
            generated["utterance_text"],
            speaker_id=speaker.player_id,
            target_id=target.player_id if target is not None else None,
        )
        features = extract_bow_features(
            generated["utterance_text"],
            tokens=token_list,
            speaker_id=speaker.player_id,
            target_id=target.player_id if target is not None else None,
        )
        later_vote = get_later_day_vote(
            event_log,
            index,
            event.get("round"),
            speaker.player_id,
        )
        affected_id = (
            target.player_id if target is not None else speaker.player_id
        )
        before_suspicion = score_state["suspicion"].get(affected_id, 0.0)
        after_suspicion = later_vote["suspicion_scores"].get(
            affected_id,
            before_suspicion,
        )
        speaker_team_win = (
            result.get("winner") == "wolf"
            if speaker.is_wolf()
            else result.get("winner") == "village"
        )
        row = {
            **generated,
            **features,
            **event_flags(generated),
            "speaker_is_wolf": str(speaker.is_wolf()),
            "eventual_winner": result.get("winner"),
            "speaker_team_win": str(bool(speaker_team_win)),
            "later_vote_target": later_vote["later_vote_target"],
            "later_elimination_target": later_vote[
                "later_elimination_target"
            ],
            "later_suspicion_change": after_suspicion - before_suspicion,
            "speaker_suspicion_score": score_state["suspicion"].get(
                speaker.player_id,
                0.0,
            ),
            "speaker_p_wolf": score_state["p_wolf"].get(
                speaker.player_id,
                TEN_PLAYER_INITIAL_P_WOLF,
            ),
            "target_suspicion_score": (
                score_state["suspicion"].get(target.player_id, 0.0)
                if target is not None
                else ""
            ),
            "target_p_wolf": (
                score_state["p_wolf"].get(
                    target.player_id,
                    TEN_PLAYER_INITIAL_P_WOLF,
                )
                if target is not None
                else ""
            ),
            "tokens": " ".join(token_list),
        }
        rows.append(row)
        past_events.append(event)

    return rows


def run_r2_source_games(max_rounds=DEFAULT_MAX_ROUNDS):
    regimes = get_r2_behavioral_regimes()
    utterance_rows = []
    split_rows = []
    game_count = 0

    for split_config in R2_SPLIT_PLAN:
        dataset_split = split_config["dataset_split"]
        for seed in split_config["seeds"]:
            for regime_id in split_config["regime_ids"]:
                regime = regimes[regime_id]
                for game_index in range(1, split_config["games_per_seed"] + 1):
                    game_count += 1
                    base_game_index = game_index
                    game_id = (
                        f"r2_{dataset_split}_{regime_id}_"
                        f"seed_{seed}_game_{game_index}"
                    )
                    random.seed(stable_seed("r2_source_game", game_id))
                    players = create_default_players(
                        role_setup=TEN_PLAYER_ROLE_SETUP,
                        initial_p_wolf=TEN_PLAYER_INITIAL_P_WOLF,
                    )
                    game = Game(players, **regime["config"])
                    result = game.run_game(max_rounds=max_rounds)
                    rows = build_utterance_rows_from_game(
                        game,
                        result,
                        game_id=game_id,
                        seed=seed,
                        base_game_index=base_game_index,
                        behavioral_regime=regime_id,
                        dataset_split=dataset_split,
                    )
                    utterance_rows.extend(rows)
                    split_rows.append({
                        "game_id": game_id,
                        "game_family_id": (
                            f"{dataset_split}_{regime_id}_{seed}_{base_game_index}"
                        ),
                        "base_configuration_id": (
                            f"r2_{dataset_split}_{regime_id}"
                        ),
                        "dataset_split": dataset_split,
                        "seed": seed,
                        "behavioral_regime": regime_id,
                        "base_game_index": base_game_index,
                        "utterance_count": len(rows),
                        "winner": result.get("winner"),
                    })

    return utterance_rows, split_rows


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            restval="",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def stable_json_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_vocabulary_outputs(output_dir, utterance_rows):
    tokenized_rows = [
        {
            "utterance_id": row["utterance_id"],
            "game_id": row["game_id"],
            "dataset_split": row["dataset_split"],
            "template_family": row["template_family"],
            "tokens": row["tokens"],
        }
        for row in utterance_rows
    ]
    vocabulary_info = build_vocabulary(
        tokenized_rows,
        min_document_frequency=VOCABULARY_SETTINGS[
            "min_document_frequency"
        ],
        max_document_frequency_ratio=VOCABULARY_SETTINGS[
            "max_document_frequency_ratio"
        ],
        max_vocabulary_size=VOCABULARY_SETTINGS[
            "max_vocabulary_size"
        ],
    )
    vocabulary_tokens = vocabulary_info["tokens"]
    vocabulary_rows = []
    for rank, token in enumerate(vocabulary_tokens, start=1):
        vocabulary_rows.append({
            "vocabulary_rank": rank,
            "token": token,
            "document_frequency": vocabulary_info[
                "document_frequency"
            ].get(token, 0),
            "total_count": vocabulary_info["total_counts"].get(token, 0),
            "ngram_order": 2 if "__" in token else 1,
            "source_split": "train",
            "in_core_lexicon": str(token in CORE_LEXICON_BY_TOKEN),
        })
    write_csv(output_dir / "bow_vocabulary.csv", vocabulary_rows)

    vocabulary_hash = stable_json_hash(vocabulary_tokens)
    manifest = {
        **VOCABULARY_SETTINGS,
        "tokenizer_version": TOKENIZER_VERSION,
        "training_document_count": vocabulary_info[
            "training_document_count"
        ],
        "vocabulary_size": len(vocabulary_tokens),
        "vocabulary_hash": vocabulary_hash,
        "built_from_split": "train",
        "source_commit": current_git_commit(),
    }
    (output_dir / "bow_vocabulary_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    vocabulary_set = set(vocabulary_tokens)
    dtm_rows = []
    for row in utterance_rows:
        counts = Counter(
            token for token in row["tokens"].split()
            if token in vocabulary_set
        )
        for token, count in sorted(counts.items()):
            dtm_rows.append({
                "utterance_id": row["utterance_id"],
                "token": token,
                "count": count,
            })
    write_csv(output_dir / "bow_document_term_matrix.csv", dtm_rows)
    write_csv(output_dir / "bow_tokenized_utterances.csv", tokenized_rows)
    return vocabulary_rows, manifest, dtm_rows


def write_registries(output_dir, split_rows):
    template_rows = template_registry_rows()
    write_csv(output_dir / "bow_template_registry.csv", template_rows)

    regime_rows = []
    for regime in get_r2_behavioral_regimes().values():
        regime_rows.append({
            "behavioral_regime_id": regime["behavioral_regime_id"],
            "description": regime["description"],
            "config_json": json.dumps(
                regime["config"],
                sort_keys=True,
                default=str,
            ),
        })
    write_csv(output_dir / "bow_behavioral_regime_registry.csv", regime_rows)
    write_csv(output_dir / "bow_dataset_split_assignments.csv", split_rows)


def validate_dataset(utterance_rows, split_rows, vocabulary_manifest):
    summary = []

    def add(metric, value, status="PASS", notes=""):
        summary.append({
            "metric": metric,
            "value": value,
            "status": status,
            "notes": notes,
        })

    split_counts = Counter(row["dataset_split"] for row in utterance_rows)
    game_count = len({row["game_id"] for row in split_rows})
    add("source_game_count", game_count)
    add("utterance_count", len(utterance_rows))
    add("seed_count", len({row["seed"] for row in utterance_rows}))
    add("behavioral_regime_count", len({row["behavioral_regime"] for row in utterance_rows}))
    add("template_family_count", len({row["template_family"] for row in utterance_rows}))
    add("dataset_split_counts", json.dumps(dict(split_counts), sort_keys=True))
    add("vocabulary_size", vocabulary_manifest["vocabulary_size"])
    add(
        "hidden_information_leakage_flags",
        sum(
            1 for row in utterance_rows
            if row["hidden_information_leakage_flag"] == "True"
        ),
    )

    template_splits = defaultdict(set)
    game_splits = defaultdict(set)
    base_splits = defaultdict(set)
    for row in utterance_rows:
        template_splits[row["template_family"]].add(row["dataset_split"])
        game_splits[row["game_family_id"]].add(row["dataset_split"])
        base_splits[row["base_configuration_id"]].add(row["dataset_split"])

    train_templates = {
        family for family, splits in template_splits.items()
        if "train" in splits
    }
    ood_templates = {
        family for family, splits in template_splits.items()
        if "ood_template" in splits
    }
    add(
        "ood_template_overlap_with_train",
        len(train_templates & ood_templates),
        "PASS" if not (train_templates & ood_templates) else "FAIL",
    )
    add(
        "game_family_split_crossing_count",
        sum(1 for splits in game_splits.values() if len(splits) > 1),
        "PASS" if all(len(splits) == 1 for splits in game_splits.values()) else "FAIL",
    )
    add(
        "base_configuration_split_crossing_count",
        sum(1 for splits in base_splits.values() if len(splits) > 1),
        "PASS" if all(len(splits) == 1 for splits in base_splits.values()) else "FAIL",
    )
    add(
        "minimum_scale_check",
        "games>=1000 and utterances>=10000",
        "PASS" if game_count >= 1000 and len(utterance_rows) >= 10000 else "WARN",
    )
    return summary


def generate_bow_dataset_outputs(output_dir=R2_RESULTS_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_core_lexicon_csv(output_dir / "bow_core_lexicon.csv")
    utterance_rows, split_rows = run_r2_source_games()
    write_csv(output_dir / "bow_speech_utterance_dataset.csv", utterance_rows)
    vocabulary_rows, vocabulary_manifest, dtm_rows = write_vocabulary_outputs(
        output_dir,
        utterance_rows,
    )
    write_registries(output_dir, split_rows)
    (output_dir / "bow_score_definition_manifest.json").write_text(
        json.dumps(
            score_definition_manifest(),
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    validation_rows = validate_dataset(
        utterance_rows,
        split_rows,
        vocabulary_manifest,
    )
    write_csv(output_dir / "bow_dataset_validation_summary.csv", validation_rows)
    return {
        "utterance_rows": utterance_rows,
        "split_rows": split_rows,
        "vocabulary_rows": vocabulary_rows,
        "vocabulary_manifest": vocabulary_manifest,
        "dtm_rows": dtm_rows,
        "validation_rows": validation_rows,
    }


if __name__ == "__main__":
    result = generate_bow_dataset_outputs()
    print("R2 BoW dataset generated")
    print(f"Source games: {len(result['split_rows'])}")
    print(f"Utterances: {len(result['utterance_rows'])}")
    print(f"Vocabulary size: {len(result['vocabulary_rows'])}")
