"""Evaluation and statistical analysis for R2 BoW speech features."""

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from bow_lexicon import CORE_LEXICON_BY_TOKEN
from bow_train_models import (
    MultinomialNB,
    SparseLogisticRegression,
    as_float,
    binary_metrics,
    macro_weighted_f1,
)


SPLITS = ["train", "validation", "final_test", "ood_template", "ood_regime"]
DIRECT_ROLE_WORDS = {"wolf", "seer", "witch", "hunter"}
PLAYER_PLACEHOLDER_WORDS = {
    "player_self",
    "player_target",
    "player_other",
    "player_ref",
}
ACCUSATION_VERBS = {"accuse", "suspect", "pressure", "push", "vote", "eliminate"}
DECEPTION_TERMS = {"fake", "frame", "deflect", "divert", "claim", "mislead", "mask", "lie"}


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def mean(values):
    values = [as_float(value) for value in values]
    return sum(values) / len(values) if values else 0.0


def stdev(values):
    values = [as_float(value) for value in values]
    if len(values) < 2:
        return 0.0
    value_mean = mean(values)
    return math.sqrt(
        sum((value - value_mean) ** 2 for value in values)
        / (len(values) - 1)
    )


def quantile(values, probability):
    values = sorted(as_float(value) for value in values)
    if not values:
        return 0.0
    index = (len(values) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[int(index)]
    return values[lower] * (upper - index) + values[upper] * (index - lower)


def median(values):
    return quantile(values, 0.5)


def iqr(values):
    return quantile(values, 0.75) - quantile(values, 0.25)


def normal_p_value(z_value):
    return math.erfc(abs(z_value) / math.sqrt(2.0))


def holm_adjust(rows, p_key="raw_p_value"):
    ordered = sorted(
        enumerate(rows),
        key=lambda item: as_float(item[1].get(p_key), 1.0),
    )
    adjusted = [1.0 for _ in rows]
    running_max = 0.0
    total = len(rows)
    for rank, (index, row) in enumerate(ordered, start=1):
        adjusted_value = min(1.0, as_float(row.get(p_key), 1.0) * (total - rank + 1))
        running_max = max(running_max, adjusted_value)
        adjusted[index] = running_max
    for row, value in zip(rows, adjusted):
        row["holm_adjusted_p_value"] = value
    return rows


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def token_counts_for_row(row, allowed_tokens=None, remove_tokens=None, unigram_only=False):
    counts = Counter(row.get("tokens", "").split())
    if unigram_only:
        counts = Counter({token: count for token, count in counts.items() if "__" not in token})
    if allowed_tokens is not None:
        allowed_tokens = set(allowed_tokens)
        counts = Counter({token: count for token, count in counts.items() if token in allowed_tokens})
    if remove_tokens:
        remove_tokens = set(remove_tokens)
        counts = Counter({token: count for token, count in counts.items() if token not in remove_tokens})
    total = sum(counts.values())
    if total:
        return {f"tok:{token}": count / total for token, count in counts.items()}
    return {}


def numeric_feature_row(row, names):
    return {
        name: as_float(row.get(name), 0.0)
        for name in names
    }


def structured_feature_row(row):
    features = {}
    for name in [
        "speech_intent",
        "speech_subtype",
        "speech_type",
        "deception_type",
        "behavioral_regime",
    ]:
        value = row.get(name, "")
        if value:
            features[f"{name}={value}"] = 1.0
    for flag in [
        "accusation_flag",
        "defense_flag",
        "role_claim_flag",
        "trust_building_flag",
        "deflection_flag",
        "information_report_flag",
    ]:
        features[flag] = 1.0 if row.get(flag) == "True" else 0.0
    return features


def combine_features(*feature_dicts):
    output = {}
    for features in feature_dicts:
        output.update(features)
    return output


def split_rows(rows):
    return group_by(rows, "dataset_split")


def label_speaker_is_wolf(rows):
    return [1 if row.get("speaker_is_wolf") == "True" else 0 for row in rows]


def fit_logistic_model(train_rows, feature_builder):
    features = [feature_builder(row) for row in train_rows]
    labels = label_speaker_is_wolf(train_rows)
    model = SparseLogisticRegression()
    model.fit(features, labels)
    return model


def evaluate_binary_model(model_name, rows_by_split, score_builder):
    metrics_rows = []
    for split in SPLITS:
        rows = rows_by_split.get(split, [])
        if not rows:
            continue
        labels = label_speaker_is_wolf(rows)
        scores = score_builder(rows)
        metrics = binary_metrics(labels, scores)
        metrics_rows.append({
            "task": "speaker_is_wolf",
            "model_name": model_name,
            "dataset_split": split,
            "n_rows": len(rows),
            "positive_rate": mean(labels),
            **metrics,
            "top_1_wolf_rate": top_k_identification_rate(rows, scores, k=1),
            "top_3_wolf_rate": top_k_identification_rate(rows, scores, k=3),
        })
    return metrics_rows


def top_k_identification_rate(rows, scores, k=1):
    grouped = defaultdict(list)
    for row, score in zip(rows, scores):
        grouped[row["game_family_id"]].append((score, row))
    hits = []
    for values in grouped.values():
        values.sort(key=lambda item: item[0], reverse=True)
        top_rows = values[:k]
        hits.append(
            1 if any(item[1].get("speaker_is_wolf") == "True" for item in top_rows) else 0
        )
    return mean(hits)


def role_prediction_metrics(rows, vocabulary_tokens):
    rows_by_split = split_rows(rows)
    train_rows = rows_by_split["train"]
    metrics = []
    base_rate = mean(label_speaker_is_wolf(train_rows))
    metrics.extend(
        evaluate_binary_model(
            "base_rate",
            rows_by_split,
            lambda split_rows_value: [base_rate for _ in split_rows_value],
        )
    )

    model_specs = [
        (
            "p_wolf_only",
            lambda row: numeric_feature_row(row, ["speaker_p_wolf"]),
        ),
        (
            "suspicion_only",
            lambda row: numeric_feature_row(row, ["speaker_suspicion_score"]),
        ),
        (
            "p_wolf_plus_suspicion",
            lambda row: numeric_feature_row(row, ["speaker_p_wolf", "speaker_suspicion_score"]),
        ),
        (
            "bow_scores_only",
            lambda row: numeric_feature_row(row, [
                "bow_werewolf_leaning_score",
                "bow_emotional_intensity_score",
                "bow_information_density_score",
            ]),
        ),
        (
            "structured_speech_labels_only",
            structured_feature_row,
        ),
        (
            "structured_labels_plus_bow_scores",
            lambda row: combine_features(
                structured_feature_row(row),
                numeric_feature_row(row, [
                    "bow_werewolf_leaning_score",
                    "bow_emotional_intensity_score",
                    "bow_information_density_score",
                ]),
            ),
        ),
        (
            "p_wolf_suspicion_structured",
            lambda row: combine_features(
                structured_feature_row(row),
                numeric_feature_row(row, ["speaker_p_wolf", "speaker_suspicion_score"]),
            ),
        ),
        (
            "full_legal_combined",
            lambda row: combine_features(
                structured_feature_row(row),
                numeric_feature_row(row, [
                    "speaker_p_wolf",
                    "speaker_suspicion_score",
                    "bow_werewolf_leaning_score",
                    "bow_emotional_intensity_score",
                    "bow_information_density_score",
                    "accusation_lexicon_count",
                    "defense_lexicon_count",
                    "trust_lexicon_count",
                    "role_claim_count",
                    "certainty_count",
                    "uncertainty_count",
                    "emotional_term_count",
                    "evidence_term_count",
                    "manipulation_term_count",
                    "player_reference_count",
                    "negation_count",
                ]),
                token_counts_for_row(row, allowed_tokens=vocabulary_tokens),
            ),
        ),
    ]

    for model_name, builder in model_specs:
        model = fit_logistic_model(train_rows, builder)
        metrics.extend(
            evaluate_binary_model(
                model_name,
                rows_by_split,
                lambda split_rows_value, model=model, builder=builder: model.predict_proba(
                    [builder(row) for row in split_rows_value]
                ),
            )
        )

    nb = MultinomialNB()
    nb.fit(
        [
            Counter({
                token.replace("tok:", ""): value
                for token, value in token_counts_for_row(
                    row,
                    allowed_tokens=vocabulary_tokens,
                ).items()
            })
            for row in train_rows
        ],
        label_speaker_is_wolf(train_rows),
    )
    metrics.extend(
        evaluate_binary_model(
            "full_bow_vector_naive_bayes",
            rows_by_split,
            lambda split_rows_value: nb.predict_proba_label([
                Counter(row["tokens"].split())
                for row in split_rows_value
            ], positive_label=1),
        )
    )
    return metrics


def descriptive_statistics(rows):
    output = []
    for (split, intent), values in group_by_intent_split(rows).items():
        for score_name in [
            "bow_werewolf_leaning_score",
            "bow_emotional_intensity_score",
            "bow_information_density_score",
        ]:
            score_values = [as_float(row[score_name]) for row in values]
            output.append({
                "dataset_split": split,
                "speech_intent": intent,
                "score_name": score_name,
                "n_rows": len(score_values),
                "mean": mean(score_values),
                "stdev": stdev(score_values),
                "median": median(score_values),
                "iqr": iqr(score_values),
            })
    return output


def group_by_intent_split(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["dataset_split"], row["speech_intent"])].append(row)
    return grouped


def cohen_d(values_a, values_b):
    values_a = [as_float(value) for value in values_a]
    values_b = [as_float(value) for value in values_b]
    if len(values_a) < 2 or len(values_b) < 2:
        return 0.0
    pooled = math.sqrt(
        (
            (len(values_a) - 1) * stdev(values_a) ** 2
            + (len(values_b) - 1) * stdev(values_b) ** 2
        )
        / (len(values_a) + len(values_b) - 2)
    )
    if pooled == 0:
        return 0.0
    return (mean(values_a) - mean(values_b)) / pooled


def grouped_bootstrap_diff(rows_a, rows_b, score_name, iterations=400, seed=90210):
    groups = defaultdict(list)
    for row in rows_a:
        groups[("a", row["game_family_id"])].append(row)
    for row in rows_b:
        groups[("b", row["game_family_id"])].append(row)
    a_keys = [key for key in groups if key[0] == "a"]
    b_keys = [key for key in groups if key[0] == "b"]
    if not a_keys or not b_keys:
        return 0.0, 0.0
    rng = random.Random(seed)
    diffs = []
    for _ in range(iterations):
        sample_a = []
        sample_b = []
        for key in (rng.choice(a_keys) for _ in a_keys):
            sample_a.extend(groups[key])
        for key in (rng.choice(b_keys) for _ in b_keys):
            sample_b.extend(groups[key])
        diffs.append(
            mean(row[score_name] for row in sample_a)
            - mean(row[score_name] for row in sample_b)
        )
    return quantile(diffs, 0.025), quantile(diffs, 0.975)


def score_intent_contrasts(rows):
    final_like_rows = [
        row for row in rows
        if row["dataset_split"] in {"validation", "final_test", "ood_template", "ood_regime"}
    ]
    contrast_specs = [
        (
            "accusation_vs_neutral_werewolf_score",
            "bow_werewolf_leaning_score",
            {"accusation", "strong_accusation", "false_accusation"},
            {"neutral_statement"},
        ),
        (
            "emotional_vs_neutral_intensity",
            "bow_emotional_intensity_score",
            {"strong_accusation", "panic", "retaliation", "self_defense", "deflection"},
            {"neutral_statement"},
        ),
        (
            "informative_vs_low_information_density",
            "bow_information_density_score",
            {"information_report", "vote_explanation", "seer_claim", "witch_claim", "hunter_claim"},
            {"neutral_statement", "uncertainty"},
        ),
        (
            "deceptive_vs_non_deceptive_werewolf_score",
            "bow_werewolf_leaning_score",
            {"false_accusation", "false_role_claim", "deflection", "trust_building"},
            {"defense", "trust_support", "neutral_statement"},
        ),
    ]
    output = []
    for contrast_name, score_name, intents_a, intents_b in contrast_specs:
        rows_a = [row for row in final_like_rows if row["speech_intent"] in intents_a]
        rows_b = [row for row in final_like_rows if row["speech_intent"] in intents_b]
        values_a = [as_float(row[score_name]) for row in rows_a]
        values_b = [as_float(row[score_name]) for row in rows_b]
        diff = mean(values_a) - mean(values_b)
        se = math.sqrt(
            (stdev(values_a) ** 2 / max(1, len(values_a)))
            + (stdev(values_b) ** 2 / max(1, len(values_b)))
        )
        z_value = diff / se if se else 0.0
        ci_low, ci_high = grouped_bootstrap_diff(rows_a, rows_b, score_name)
        output.append({
            "contrast": contrast_name,
            "score_name": score_name,
            "n_group_a": len(rows_a),
            "n_group_b": len(rows_b),
            "mean_group_a": mean(values_a),
            "mean_group_b": mean(values_b),
            "mean_difference": diff,
            "bootstrap_ci_low": ci_low,
            "bootstrap_ci_high": ci_high,
            "cohen_d": cohen_d(values_a, values_b),
            "z_value": z_value,
            "raw_p_value": normal_p_value(z_value),
            "multiplicity_method": "Holm over four pre-specified score contrasts",
        })
    return holm_adjust(output)


def intent_classification_metrics(rows, vocabulary_tokens):
    rows_by_split = split_rows(rows)
    train_rows = rows_by_split["train"]
    nb = MultinomialNB()
    nb.fit(
        [Counter(row["tokens"].split()) for row in train_rows],
        [row["speech_intent"] for row in train_rows],
    )
    output = []
    confusion_rows = []
    for split in SPLITS:
        split_data = rows_by_split.get(split, [])
        if not split_data:
            continue
        labels = [row["speech_intent"] for row in split_data]
        predictions = nb.predict([Counter(row["tokens"].split()) for row in split_data])
        accuracy, macro_f1, weighted_f1, class_rows = macro_weighted_f1(labels, predictions)
        output.append({
            "model_name": "multinomial_nb_bow",
            "dataset_split": split,
            "n_rows": len(split_data),
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "per_class_recall_json": json.dumps(
                {row["class"]: row["recall"] for row in class_rows},
                sort_keys=True,
            ),
        })
        counts = Counter(zip(labels, predictions))
        for (actual, predicted), count in counts.items():
            confusion_rows.append({
                "dataset_split": split,
                "actual_intent": actual,
                "predicted_intent": predicted,
                "count": count,
            })
    return output, confusion_rows


def downstream_associations(rows):
    output = []
    score_names = [
        "bow_werewolf_leaning_score",
        "bow_emotional_intensity_score",
        "bow_information_density_score",
    ]
    for split in SPLITS:
        split_rows_value = [row for row in rows if row["dataset_split"] == split]
        for score_name in score_names:
            scores = [as_float(row[score_name]) for row in split_rows_value]
            suspicion_change = [
                as_float(row.get("later_suspicion_change"), 0.0)
                for row in split_rows_value
            ]
            eliminated = [
                1 if str(row.get("later_elimination_target")) == str(row.get("target_uid")) and row.get("target_uid") != "" else 0
                for row in split_rows_value
            ]
            output.append({
                "dataset_split": split,
                "score_name": score_name,
                "n_rows": len(split_rows_value),
                "correlation_with_later_suspicion_change": pearson(scores, suspicion_change),
                "mean_score_when_target_eliminated": mean(
                    score for score, flag in zip(scores, eliminated) if flag
                ),
                "mean_score_when_target_not_eliminated": mean(
                    score for score, flag in zip(scores, eliminated) if not flag
                ),
                "target_elimination_rate": mean(eliminated),
            })
    return output


def pearson(values_x, values_y):
    if len(values_x) != len(values_y) or len(values_x) < 2:
        return 0.0
    mean_x = mean(values_x)
    mean_y = mean(values_y)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(values_x, values_y))
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in values_x))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in values_y))
    if denominator_x == 0 or denominator_y == 0:
        return 0.0
    return numerator / (denominator_x * denominator_y)


def feature_ablation_metrics(rows, vocabulary_tokens):
    rows_by_split = split_rows(rows)
    train_rows = rows_by_split["train"]
    core_tokens = set(CORE_LEXICON_BY_TOKEN)
    ablations = [
        ("bow_only_unigram_bigram", None, None, False, False),
        ("remove_direct_role_words", None, DIRECT_ROLE_WORDS, False, False),
        ("remove_player_placeholders", None, PLAYER_PLACEHOLDER_WORDS, False, False),
        ("remove_emotional_punctuation", None, {"exclamation"}, False, False),
        ("remove_explicit_accusation_verbs", None, ACCUSATION_VERBS, False, False),
        ("remove_deception_specific_terms", None, DECEPTION_TERMS, False, False),
        ("unigram_only", None, None, True, False),
        ("core_lexicon_only", core_tokens, None, False, False),
        ("data_derived_vocabulary_only", set(vocabulary_tokens), None, False, False),
        ("structured_speech_labels_only", None, None, False, True),
        ("structured_plus_bow", None, None, False, "structured_plus_bow"),
    ]
    output = []
    for name, allowed, removed, unigram_only, structured_mode in ablations:
        if structured_mode is True:
            builder = structured_feature_row
        elif structured_mode == "structured_plus_bow":
            builder = lambda row, allowed=allowed, removed=removed: combine_features(
                structured_feature_row(row),
                token_counts_for_row(row, allowed_tokens=allowed or vocabulary_tokens, remove_tokens=removed),
            )
        else:
            builder = lambda row, allowed=allowed, removed=removed, unigram_only=unigram_only: token_counts_for_row(
                row,
                allowed_tokens=allowed or vocabulary_tokens,
                remove_tokens=removed,
                unigram_only=unigram_only,
            )
        model = fit_logistic_model(train_rows, builder)
        for split in ["validation", "final_test", "ood_template", "ood_regime"]:
            split_data = rows_by_split.get(split, [])
            if not split_data:
                continue
            labels = label_speaker_is_wolf(split_data)
            scores = model.predict_proba([builder(row) for row in split_data])
            metrics = binary_metrics(labels, scores)
            output.append({
                "ablation_name": name,
                "dataset_split": split,
                "n_rows": len(split_data),
                **metrics,
            })
    return output


def template_generalization_metrics(role_metrics):
    output = []
    by_model = defaultdict(dict)
    for row in role_metrics:
        by_model[row["model_name"]][row["dataset_split"]] = row
    for model_name, split_map in sorted(by_model.items()):
        final_auc = as_float(split_map.get("final_test", {}).get("roc_auc"), 0.5)
        ood_auc = as_float(split_map.get("ood_template", {}).get("roc_auc"), 0.5)
        output.append({
            "model_name": model_name,
            "final_test_roc_auc": final_auc,
            "ood_template_roc_auc": ood_auc,
            "ood_template_auc_gap": ood_auc - final_auc,
            "template_generalization_label": (
                "template_bound" if final_auc - ood_auc > 0.05 else "stable_or_uncertain"
            ),
        })
    return output


def regime_generalization_metrics(role_metrics):
    output = []
    by_model = defaultdict(dict)
    for row in role_metrics:
        by_model[row["model_name"]][row["dataset_split"]] = row
    for model_name, split_map in sorted(by_model.items()):
        final_auc = as_float(split_map.get("final_test", {}).get("roc_auc"), 0.5)
        ood_auc = as_float(split_map.get("ood_regime", {}).get("roc_auc"), 0.5)
        output.append({
            "model_name": model_name,
            "final_test_roc_auc": final_auc,
            "ood_regime_roc_auc": ood_auc,
            "ood_regime_auc_gap": ood_auc - final_auc,
            "regime_generalization_label": (
                "unstable_across_regimes" if final_auc - ood_auc > 0.05 else "stable_or_uncertain"
            ),
        })
    return output


def overfitting_diagnostics(role_metrics):
    output = []
    by_model = defaultdict(dict)
    for row in role_metrics:
        by_model[row["model_name"]][row["dataset_split"]] = row
    for model_name, split_map in sorted(by_model.items()):
        train_auc = as_float(split_map.get("train", {}).get("roc_auc"), 0.5)
        validation_auc = as_float(split_map.get("validation", {}).get("roc_auc"), 0.5)
        final_auc = as_float(split_map.get("final_test", {}).get("roc_auc"), 0.5)
        output.append({
            "model_name": model_name,
            "train_roc_auc": train_auc,
            "validation_roc_auc": validation_auc,
            "final_test_roc_auc": final_auc,
            "train_validation_gap": train_auc - validation_auc,
            "train_final_gap": train_auc - final_auc,
            "overfitting_flag": str((train_auc - validation_auc) > 0.05 or (train_auc - final_auc) > 0.05),
        })
    return output


def feature_importance(rows, vocabulary_tokens):
    train_rows = [row for row in rows if row["dataset_split"] == "train"]
    builder = lambda row: combine_features(
        structured_feature_row(row),
        numeric_feature_row(row, [
            "speaker_p_wolf",
            "speaker_suspicion_score",
            "bow_werewolf_leaning_score",
            "bow_emotional_intensity_score",
            "bow_information_density_score",
        ]),
        token_counts_for_row(row, allowed_tokens=vocabulary_tokens),
    )
    model = fit_logistic_model(train_rows, builder)
    rows_out = []
    for feature, coefficient in sorted(
        model.weights.items(),
        key=lambda item: abs(item[1]),
        reverse=True,
    )[:100]:
        rows_out.append({
            "model_name": "full_legal_combined",
            "feature": feature,
            "coefficient": coefficient,
            "absolute_coefficient": abs(coefficient),
            "direction": "wolf_positive" if coefficient > 0 else "village_positive",
        })
    return rows_out


def keyword_dependency_analysis(ablation_rows):
    lookup = {
        (row["ablation_name"], row["dataset_split"]): row
        for row in ablation_rows
    }
    baseline = lookup.get(("bow_only_unigram_bigram", "final_test"), {})
    output = []
    for name in [
        "remove_direct_role_words",
        "remove_player_placeholders",
        "remove_explicit_accusation_verbs",
        "remove_deception_specific_terms",
        "unigram_only",
        "core_lexicon_only",
    ]:
        row = lookup.get((name, "final_test"), {})
        output.append({
            "comparison": f"{name}_vs_bow_only_unigram_bigram",
            "baseline_final_test_roc_auc": baseline.get("roc_auc", ""),
            "ablation_final_test_roc_auc": row.get("roc_auc", ""),
            "auc_change": as_float(row.get("roc_auc"), 0.5)
            - as_float(baseline.get("roc_auc"), 0.5),
            "dependency_flag": str(
                as_float(baseline.get("roc_auc"), 0.5)
                - as_float(row.get("roc_auc"), 0.5)
                > 0.05
            ),
        })
    return output


def bootstrap_metric_ci(rows, model_name, score_builder, iterations=300, seed=4242):
    rng = random.Random(seed)
    groups = group_by(rows, "game_family_id")
    group_keys = list(groups)
    if not group_keys:
        return 0.0, 0.0
    values = []
    for _ in range(iterations):
        sample = []
        for key in (rng.choice(group_keys) for _ in group_keys):
            sample.extend(groups[key])
        labels = label_speaker_is_wolf(sample)
        scores = score_builder(sample)
        values.append(binary_metrics(labels, scores)["roc_auc"])
    return quantile(values, 0.025), quantile(values, 0.975)


def bootstrap_confidence_intervals(rows, role_metrics):
    final_rows = [row for row in rows if row["dataset_split"] == "final_test"]
    by_model = {
        row["model_name"]: row
        for row in role_metrics
        if row["dataset_split"] == "final_test"
    }
    output = []
    for model_name in [
        "p_wolf_only",
        "suspicion_only",
        "bow_scores_only",
        "structured_speech_labels_only",
        "full_legal_combined",
    ]:
        if model_name not in by_model:
            continue
        metric_value = as_float(by_model[model_name].get("roc_auc"), 0.5)
        output.append({
            "metric_name": "final_test_roc_auc",
            "model_name": model_name,
            "point_estimate": metric_value,
            "bootstrap_ci_low": "",
            "bootstrap_ci_high": "",
            "bootstrap_method": "Reported model metric; CIs reserved for score contrasts in this R2 implementation.",
        })
    return output


def model_selection_summary(role_metrics, template_metrics, regime_metrics):
    final_rows = [
        row for row in role_metrics
        if row["dataset_split"] == "final_test"
    ]
    final_rows.sort(key=lambda row: as_float(row.get("roc_auc"), 0.0), reverse=True)
    best = final_rows[0] if final_rows else {}
    bow_scores = next(
        (row for row in final_rows if row["model_name"] == "bow_scores_only"),
        {},
    )
    structured = next(
        (row for row in final_rows if row["model_name"] == "structured_speech_labels_only"),
        {},
    )
    combined = next(
        (row for row in final_rows if row["model_name"] == "full_legal_combined"),
        {},
    )
    return [
        {
            "criterion": "best_final_test_roc_auc",
            "selected_model": best.get("model_name", ""),
            "value": best.get("roc_auc", ""),
            "notes": "Selection is descriptive; no final-test tuning was performed.",
        },
        {
            "criterion": "bow_score_added_value_over_structured",
            "selected_model": "full_legal_combined",
            "value": as_float(combined.get("roc_auc"), 0.0) - as_float(structured.get("roc_auc"), 0.0),
            "notes": "Positive values indicate complementary BoW value beyond structured labels.",
        },
        {
            "criterion": "bow_scores_vs_existing_p_wolf",
            "selected_model": "bow_scores_only",
            "value": as_float(bow_scores.get("roc_auc"), 0.0),
            "notes": "Compare against p_wolf_only row in role prediction metrics.",
        },
    ]


def evaluate_bow_outputs(output_dir):
    output_dir = Path(output_dir)
    rows = read_csv(output_dir / "bow_speech_utterance_dataset.csv")
    vocabulary = read_csv(output_dir / "bow_vocabulary.csv")
    vocabulary_tokens = [row["token"] for row in vocabulary]

    score_stats = descriptive_statistics(rows)
    score_contrasts = score_intent_contrasts(rows)
    role_metrics = role_prediction_metrics(rows, vocabulary_tokens)
    intent_metrics, confusion_rows = intent_classification_metrics(
        rows,
        vocabulary_tokens,
    )
    downstream_rows = downstream_associations(rows)
    ablation_rows = feature_ablation_metrics(rows, vocabulary_tokens)
    template_rows = template_generalization_metrics(role_metrics)
    regime_rows = regime_generalization_metrics(role_metrics)
    overfitting_rows = overfitting_diagnostics(role_metrics)
    importance_rows = feature_importance(rows, vocabulary_tokens)
    keyword_rows = keyword_dependency_analysis(ablation_rows)
    bootstrap_rows = bootstrap_confidence_intervals(rows, role_metrics)
    model_summary_rows = model_selection_summary(
        role_metrics,
        template_rows,
        regime_rows,
    )

    write_csv(output_dir / "bow_score_descriptive_statistics.csv", score_stats)
    write_csv(output_dir / "bow_score_intent_contrasts.csv", score_contrasts)
    write_csv(output_dir / "bow_role_prediction_metrics.csv", role_metrics)
    write_csv(output_dir / "bow_intent_classification_metrics.csv", intent_metrics)
    write_csv(output_dir / "bow_intent_confusion_matrix.csv", confusion_rows)
    write_csv(output_dir / "bow_downstream_association_metrics.csv", downstream_rows)
    write_csv(output_dir / "bow_feature_ablation_metrics.csv", ablation_rows)
    write_csv(output_dir / "bow_template_generalization_metrics.csv", template_rows)
    write_csv(output_dir / "bow_regime_generalization_metrics.csv", regime_rows)
    write_csv(output_dir / "bow_overfitting_diagnostics.csv", overfitting_rows)
    write_csv(output_dir / "bow_feature_importance.csv", importance_rows)
    write_csv(output_dir / "bow_keyword_dependency_analysis.csv", keyword_rows)
    write_csv(output_dir / "bow_model_selection_summary.csv", model_summary_rows)
    write_csv(output_dir / "bow_bootstrap_confidence_intervals.csv", bootstrap_rows)

    return {
        "rows": rows,
        "vocabulary_tokens": vocabulary_tokens,
        "score_stats": score_stats,
        "score_contrasts": score_contrasts,
        "role_metrics": role_metrics,
        "intent_metrics": intent_metrics,
        "confusion_rows": confusion_rows,
        "downstream_rows": downstream_rows,
        "ablation_rows": ablation_rows,
        "template_rows": template_rows,
        "regime_rows": regime_rows,
        "overfitting_rows": overfitting_rows,
        "importance_rows": importance_rows,
        "keyword_rows": keyword_rows,
        "model_summary_rows": model_summary_rows,
    }


if __name__ == "__main__":
    analysis = evaluate_bow_outputs(Path("results") / "bow_speech_stage_r2")
    print("R2 BoW evaluation complete")
    print(f"Utterances analyzed: {len(analysis['rows'])}")
    print(f"Vocabulary size: {len(analysis['vocabulary_tokens'])}")
