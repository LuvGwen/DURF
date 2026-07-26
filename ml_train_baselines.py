import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path

from ml_dataset_generation import ACTION_VALUE_FIELDNAMES, DATASET_PATHS, MODELS_DIR, RESULTS_DIR
from ml_feature_registry import FEATURE_COLUMNS, LABEL_COLUMNS, validate_no_prohibited_features


IDENTITY_METRICS_PATH = RESULTS_DIR / "ml_identity_model_metrics.csv"
ACTION_VALUE_METRICS_PATH = RESULTS_DIR / "ml_action_value_model_metrics.csv"
FEATURE_IMPORTANCE_PATH = RESULTS_DIR / "ml_feature_importance.csv"


def read_csv_rows(path):
    with Path(path).open(newline="") as file:
        return list(csv.DictReader(file))


def write_csv_rows(path, rows, fieldnames):
    Path(path).parent.mkdir(exist_ok=True, parents=True)
    with Path(path).open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            restval="",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def as_float(value, default=0.0):
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def feature_matrix(rows, feature_columns=None):
    if feature_columns is None:
        feature_columns = FEATURE_COLUMNS
    validate_no_prohibited_features(feature_columns)
    return [
        [as_float(row.get(column), 0.0) for column in feature_columns]
        for row in rows
    ]


def labels(rows, target_column):
    return [as_float(row.get(target_column), 0.0) for row in rows]


def sigmoid(value):
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def fit_logistic_regression(rows, target_column, feature_columns=None, epochs=180, learning_rate=0.03, l2=0.001):
    if feature_columns is None:
        feature_columns = FEATURE_COLUMNS
    x = feature_matrix(rows, feature_columns)
    y = labels(rows, target_column)
    if not x:
        return {"intercept": 0.0, "weights": [0.0 for _ in feature_columns], "features": feature_columns}
    weights = [0.0 for _ in feature_columns]
    intercept = 0.0
    n = len(x)
    for epoch in range(epochs):
        step = learning_rate / (1.0 + 0.01 * epoch)
        grad_w = [0.0 for _ in feature_columns]
        grad_b = 0.0
        for row_x, row_y in zip(x, y):
            pred = sigmoid(intercept + sum(w * v for w, v in zip(weights, row_x)))
            error = pred - row_y
            grad_b += error
            for index, value in enumerate(row_x):
                grad_w[index] += error * value
        intercept -= step * grad_b / n
        for index in range(len(weights)):
            penalty = l2 * weights[index]
            weights[index] -= step * ((grad_w[index] / n) + penalty)
    return {
        "intercept": intercept,
        "weights": weights,
        "features": feature_columns,
    }


def predict_logistic(model, rows):
    x = feature_matrix(rows, model["features"])
    return [
        sigmoid(model["intercept"] + sum(w * v for w, v in zip(model["weights"], row_x)))
        for row_x in x
    ]


def fit_ridge_regression(rows, target_column, feature_columns=None, epochs=220, learning_rate=0.01, l2=0.01):
    if feature_columns is None:
        feature_columns = FEATURE_COLUMNS
    x = feature_matrix(rows, feature_columns)
    y = labels(rows, target_column)
    if not x:
        return {"intercept": 0.0, "weights": [0.0 for _ in feature_columns], "features": feature_columns}
    weights = [0.0 for _ in feature_columns]
    intercept = sum(y) / len(y)
    n = len(x)
    for epoch in range(epochs):
        step = learning_rate / (1.0 + 0.01 * epoch)
        grad_w = [0.0 for _ in feature_columns]
        grad_b = 0.0
        for row_x, row_y in zip(x, y):
            pred = intercept + sum(w * v for w, v in zip(weights, row_x))
            error = pred - row_y
            grad_b += error
            for index, value in enumerate(row_x):
                grad_w[index] += error * value
        intercept -= step * grad_b / n
        for index in range(len(weights)):
            weights[index] -= step * ((grad_w[index] / n) + l2 * weights[index])
    return {
        "intercept": intercept,
        "weights": weights,
        "features": feature_columns,
    }


def predict_ridge(model, rows):
    x = feature_matrix(rows, model["features"])
    return [
        max(0.0, min(1.0, model["intercept"] + sum(w * v for w, v in zip(model["weights"], row_x))))
        for row_x in x
    ]


def roc_auc(y_true, y_score):
    positives = [(score, index) for index, (label, score) in enumerate(zip(y_true, y_score)) if label == 1]
    negatives = [(score, index) for index, (label, score) in enumerate(zip(y_true, y_score)) if label == 0]
    if not positives or not negatives:
        return ""
    wins = 0.0
    total = len(positives) * len(negatives)
    for pos_score, _ in positives:
        for neg_score, _ in negatives:
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
    return wins / total


def pr_auc(y_true, y_score):
    if sum(y_true) == 0:
        return ""
    ordered = sorted(zip(y_score, y_true), reverse=True)
    tp = 0
    fp = 0
    precision_sum = 0.0
    for _, label in ordered:
        if label == 1:
            tp += 1
            precision_sum += tp / (tp + fp)
        else:
            fp += 1
    return precision_sum / sum(y_true)


def brier_score(y_true, y_score):
    if not y_true:
        return ""
    return sum((score - label) ** 2 for label, score in zip(y_true, y_score)) / len(y_true)


def log_loss(y_true, y_score):
    if not y_true:
        return ""
    eps = 1e-6
    total = 0.0
    for label, score in zip(y_true, y_score):
        score = min(1.0 - eps, max(eps, score))
        total += -(label * math.log(score) + (1 - label) * math.log(1 - score))
    return total / len(y_true)


def calibration_error(y_true, y_score, bins=5):
    if not y_true:
        return ""
    total_error = 0.0
    total_count = 0
    for bin_index in range(bins):
        low = bin_index / bins
        high = (bin_index + 1) / bins
        indices = [
            index for index, score in enumerate(y_score)
            if (score >= low and (score < high or bin_index == bins - 1))
        ]
        if not indices:
            continue
        pred_mean = sum(y_score[index] for index in indices) / len(indices)
        actual_mean = sum(y_true[index] for index in indices) / len(indices)
        total_error += abs(pred_mean - actual_mean) * len(indices)
        total_count += len(indices)
    return total_error / total_count if total_count else ""


def top_k_metrics(rows, scores, k=3):
    grouped = defaultdict(list)
    for row, score in zip(rows, scores):
        grouped[row["decision_id"]].append((row, score))
    top1_hits = []
    top3_recalls = []
    for decision_rows in grouped.values():
        ordered = sorted(decision_rows, key=lambda item: item[1], reverse=True)
        top1_hits.append(int(ordered[0][0]["candidate_is_wolf_label"]))
        wolf_total = sum(int(row["candidate_is_wolf_label"]) for row, _ in decision_rows)
        if wolf_total:
            top_k = ordered[:k]
            top3_recalls.append(
                sum(int(row["candidate_is_wolf_label"]) for row, _ in top_k)
                / wolf_total
            )
    return {
        "top1_wolf_hit_rate": sum(top1_hits) / len(top1_hits) if top1_hits else "",
        "top3_wolf_recall": sum(top3_recalls) / len(top3_recalls) if top3_recalls else "",
    }


def identity_contexts(rows):
    return {
        "seer_candidate_states": [
            row for row in rows if row["decision_type"] == "seer_check"
        ],
        "village_vote_candidate_states": [
            row for row in rows
            if row["decision_type"] == "day_vote"
            and row["actor_team"] != "wolf"
        ],
        "wolf_kill_candidate_states": [
            row for row in rows if row["decision_type"] == "wolf_kill"
        ],
    }


def evaluate_identity_model(context_name, model_name, test_rows, scores, status="trained"):
    y_true = [int(row["candidate_is_wolf_label"]) for row in test_rows]
    base = {
        "context": context_name,
        "model": model_name,
        "status": status,
        "test_rows": len(test_rows),
        "roc_auc": roc_auc(y_true, scores) if scores else "",
        "pr_auc": pr_auc(y_true, scores) if scores else "",
        "brier_score": brier_score(y_true, scores) if scores else "",
        "log_loss": log_loss(y_true, scores) if scores else "",
        "calibration_error": calibration_error(y_true, scores) if scores else "",
    }
    base.update(top_k_metrics(test_rows, scores) if scores else {
        "top1_wolf_hit_rate": "",
        "top3_wolf_recall": "",
    })
    return base


def train_identity_models(rows):
    metrics = []
    importance = []
    contexts = identity_contexts(rows)
    for context_name, context_rows in contexts.items():
        train_rows = [row for row in context_rows if row["dataset_split"] == "train"]
        test_rows = [row for row in context_rows if row["dataset_split"] == "test"]
        if not train_rows or not test_rows:
            continue
        train_labels = {
            int(row["candidate_is_wolf_label"]) for row in train_rows
        }
        test_labels = {
            int(row["candidate_is_wolf_label"]) for row in test_rows
        }
        if len(train_labels) < 2 or len(test_labels) < 2:
            metrics.append(evaluate_identity_model(
                context_name,
                "identity_task_not_meaningful",
                test_rows,
                [],
                status="not_meaningful_no_label_variance",
            ))
            continue

        p_scores = [as_float(row["candidate_p_wolf"], 0.3) for row in test_rows]
        s_scores = [
            as_float(row["candidate_suspicion_score"], 0.0)
            for row in test_rows
        ]
        metrics.append(evaluate_identity_model(
            context_name,
            "existing_p_wolf",
            test_rows,
            p_scores,
            status="baseline",
        ))
        metrics.append(evaluate_identity_model(
            context_name,
            "existing_suspicion_score",
            test_rows,
            s_scores,
            status="baseline",
        ))

        model = fit_logistic_regression(
            train_rows,
            "candidate_is_wolf_label",
            feature_columns=FEATURE_COLUMNS,
        )
        scores = predict_logistic(model, test_rows)
        metrics.append(evaluate_identity_model(
            context_name,
            "logistic_regression_stdlib",
            test_rows,
            scores,
        ))
        save_model(
            MODELS_DIR / f"identity_{context_name}_logistic_stdlib.json",
            model,
        )
        for feature, weight in zip(model["features"], model["weights"]):
            importance.append({
                "task": "identity_prediction",
                "context": context_name,
                "model": "logistic_regression_stdlib",
                "feature": feature,
                "importance": abs(weight),
                "signed_weight": weight,
            })
        metrics.append(evaluate_identity_model(
            context_name,
            "random_forest_sklearn",
            test_rows,
            [],
            status="skipped_sklearn_unavailable",
        ))
        metrics.append(evaluate_identity_model(
            context_name,
            "hist_gradient_boosting_sklearn",
            test_rows,
            [],
            status="skipped_sklearn_unavailable",
        ))
    return metrics, importance


def rmse(y_true, y_pred):
    if not y_true:
        return ""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / len(y_true))


def mae(y_true, y_pred):
    if not y_true:
        return ""
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / len(y_true)


def rank(values):
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    for rank_index, (_, original_index) in enumerate(ordered, start=1):
        ranks[original_index] = rank_index
    return ranks


def pearson(xs, ys):
    if len(xs) < 2:
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_denom = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_denom = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if x_denom == 0 or y_denom == 0:
        return None
    return numerator / (x_denom * y_denom)


def rank_correlation_by_decision(rows, predictions):
    grouped = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        grouped[row["decision_id"]].append((row, prediction))
    values = []
    for decision_rows in grouped.values():
        if len(decision_rows) < 2:
            continue
        actual = [as_float(row["rollout_team_win_rate"]) for row, _ in decision_rows]
        pred = [prediction for _, prediction in decision_rows]
        corr = pearson(rank(actual), rank(pred))
        if corr is not None:
            values.append(corr)
    return sum(values) / len(values) if values else ""


def top_action_metrics(rows, predictions):
    grouped = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        grouped[row["decision_id"]].append((row, prediction))
    agreements = []
    values = []
    regrets = []
    for decision_rows in grouped.values():
        pred_best_row = sorted(
            decision_rows,
            key=lambda item: (item[1], str(item[0]["candidate_uid"])),
            reverse=True,
        )[0][0]
        actual_best = str(pred_best_row.get("rollout_best_action"))
        agreements.append(1 if str(pred_best_row["candidate_uid"]) == actual_best else 0)
        predicted_value = as_float(pred_best_row["rollout_team_win_rate"])
        best_value = max(as_float(row["rollout_team_win_rate"]) for row, _ in decision_rows)
        values.append(predicted_value)
        regrets.append(best_value - predicted_value)
    return {
        "top_action_selection_accuracy": (
            sum(agreements) / len(agreements) if agreements else ""
        ),
        "estimated_policy_value": sum(values) / len(values) if values else "",
        "average_regret": sum(regrets) / len(regrets) if regrets else "",
        "top1_action_agreement": (
            sum(agreements) / len(agreements) if agreements else ""
        ),
    }


def evaluate_action_value_model(decision_type, model_name, test_rows, predictions, status="trained"):
    y_true = [as_float(row["rollout_team_win_rate"]) for row in test_rows]
    metrics = {
        "decision_type": decision_type,
        "model": model_name,
        "status": status,
        "test_rows": len(test_rows),
        "rmse": rmse(y_true, predictions) if predictions else "",
        "mae": mae(y_true, predictions) if predictions else "",
        "rank_correlation_within_decision": (
            rank_correlation_by_decision(test_rows, predictions)
            if predictions else ""
        ),
        "calibration_abs_error": (
            sum(abs(a - b) for a, b in zip(y_true, predictions)) / len(y_true)
            if predictions and y_true else ""
        ),
    }
    metrics.update(top_action_metrics(test_rows, predictions) if predictions else {
        "top_action_selection_accuracy": "",
        "estimated_policy_value": "",
        "average_regret": "",
        "top1_action_agreement": "",
    })
    return metrics


def train_action_value_models(rows):
    metrics = []
    importance = []
    for decision_type in ["seer_check", "wolf_kill", "day_vote"]:
        context_rows = [row for row in rows if row["decision_type"] == decision_type]
        train_rows = [row for row in context_rows if row["dataset_split"] == "train"]
        test_rows = [row for row in context_rows if row["dataset_split"] == "test"]
        if not train_rows or not test_rows:
            continue
        mean_value = sum(as_float(row["rollout_team_win_rate"]) for row in train_rows) / len(train_rows)
        mean_predictions = [mean_value for _ in test_rows]
        metrics.append(evaluate_action_value_model(
            decision_type,
            "mean_value_baseline",
            test_rows,
            mean_predictions,
            status="baseline",
        ))
        ridge = fit_ridge_regression(
            train_rows,
            "rollout_team_win_rate",
            feature_columns=FEATURE_COLUMNS,
        )
        predictions = predict_ridge(ridge, test_rows)
        metrics.append(evaluate_action_value_model(
            decision_type,
            "ridge_regression_stdlib",
            test_rows,
            predictions,
        ))
        save_model(
            MODELS_DIR / f"action_value_{decision_type}_ridge_stdlib.json",
            ridge,
        )
        for feature, weight in zip(ridge["features"], ridge["weights"]):
            importance.append({
                "task": "action_value",
                "context": decision_type,
                "model": "ridge_regression_stdlib",
                "feature": feature,
                "importance": abs(weight),
                "signed_weight": weight,
            })
        metrics.append(evaluate_action_value_model(
            decision_type,
            "random_forest_regressor_sklearn",
            test_rows,
            [],
            status="skipped_sklearn_unavailable",
        ))
        metrics.append(evaluate_action_value_model(
            decision_type,
            "hist_gradient_boosting_regressor_sklearn",
            test_rows,
            [],
            status="skipped_sklearn_unavailable",
        ))
    return metrics, importance


def save_model(path, model):
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w") as file:
        json.dump(model, file, sort_keys=True, indent=2)


def load_model(path):
    with Path(path).open() as file:
        return json.load(file)


def train_and_write_baselines(rows=None):
    if rows is None:
        rows = read_csv_rows(DATASET_PATHS["identity"])
    start = time.time()
    identity_metrics, identity_importance = train_identity_models(rows)
    action_metrics, action_importance = train_action_value_models(rows)
    write_csv_rows(
        IDENTITY_METRICS_PATH,
        identity_metrics,
        [
            "context",
            "model",
            "status",
            "test_rows",
            "roc_auc",
            "pr_auc",
            "brier_score",
            "log_loss",
            "calibration_error",
            "top1_wolf_hit_rate",
            "top3_wolf_recall",
        ],
    )
    write_csv_rows(
        ACTION_VALUE_METRICS_PATH,
        action_metrics,
        [
            "decision_type",
            "model",
            "status",
            "test_rows",
            "rmse",
            "mae",
            "rank_correlation_within_decision",
            "top_action_selection_accuracy",
            "estimated_policy_value",
            "average_regret",
            "top1_action_agreement",
            "calibration_abs_error",
        ],
    )
    write_csv_rows(
        FEATURE_IMPORTANCE_PATH,
        sorted(
            identity_importance + action_importance,
            key=lambda row: (row["task"], row["context"], -row["importance"]),
        ),
        [
            "task",
            "context",
            "model",
            "feature",
            "importance",
            "signed_weight",
        ],
    )
    return {
        "identity_metrics": identity_metrics,
        "action_value_metrics": action_metrics,
        "feature_importance": identity_importance + action_importance,
        "training_runtime_seconds": time.time() - start,
    }


if __name__ == "__main__":
    summary = train_and_write_baselines()
    print("ML Stage 1 baseline models trained")
    print(f"Identity metric rows: {len(summary['identity_metrics'])}")
    print(f"Action-value metric rows: {len(summary['action_value_metrics'])}")
    print(f"Training runtime seconds: {summary['training_runtime_seconds']:.2f}")
