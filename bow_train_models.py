"""Small standard-library models and metrics for R2 BoW evaluation."""

import math
import random
from collections import Counter, defaultdict


def as_float(value, default=0.0):
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def sigmoid(value):
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


class SparseLogisticRegression:
    def __init__(self, learning_rate=0.08, l2=0.001, epochs=35, seed=1234):
        self.learning_rate = learning_rate
        self.l2 = l2
        self.epochs = epochs
        self.seed = seed
        self.weights = defaultdict(float)
        self.bias = 0.0

    def fit(self, feature_rows, labels):
        rows = list(zip(feature_rows, labels))
        rng = random.Random(self.seed)
        for _ in range(self.epochs):
            rng.shuffle(rows)
            for features, label in rows:
                prediction = sigmoid(
                    self.bias
                    + sum(self.weights[key] * value for key, value in features.items())
                )
                error = prediction - label
                self.bias -= self.learning_rate * error
                for key, value in features.items():
                    gradient = error * value + self.l2 * self.weights[key]
                    self.weights[key] -= self.learning_rate * gradient
        return self

    def predict_proba(self, feature_rows):
        return [
            sigmoid(
                self.bias
                + sum(self.weights[key] * value for key, value in features.items())
            )
            for features in feature_rows
        ]


class MultinomialNB:
    def __init__(self, alpha=1.0):
        self.alpha = alpha
        self.class_log_prior = {}
        self.feature_log_prob = {}
        self.default_log_prob = {}
        self.classes = []
        self.vocabulary = set()

    def fit(self, token_count_rows, labels):
        class_counts = Counter(labels)
        feature_counts = defaultdict(Counter)
        total_feature_counts = Counter()
        for counts, label in zip(token_count_rows, labels):
            self.vocabulary.update(counts.keys())
            feature_counts[label].update(counts)
            total_feature_counts[label] += sum(counts.values())
        total_rows = len(labels)
        self.classes = sorted(class_counts)
        vocab_size = max(1, len(self.vocabulary))
        for label in self.classes:
            self.class_log_prior[label] = math.log(class_counts[label] / total_rows)
            denominator = total_feature_counts[label] + self.alpha * vocab_size
            self.default_log_prob[label] = math.log(self.alpha / denominator)
            self.feature_log_prob[label] = {}
            for token in self.vocabulary:
                self.feature_log_prob[label][token] = math.log(
                    (feature_counts[label][token] + self.alpha) / denominator
                )
        return self

    def predict_proba_label(self, token_count_rows, positive_label=1):
        output = []
        for counts in token_count_rows:
            scores = {}
            for label in self.classes:
                score = self.class_log_prior[label]
                for token, count in counts.items():
                    score += count * self.feature_log_prob[label].get(
                        token,
                        self.default_log_prob[label],
                    )
                scores[label] = score
            max_score = max(scores.values())
            exp_scores = {
                label: math.exp(score - max_score)
                for label, score in scores.items()
            }
            denominator = sum(exp_scores.values())
            output.append(exp_scores.get(positive_label, 0.0) / denominator)
        return output

    def predict(self, token_count_rows):
        predictions = []
        for counts in token_count_rows:
            scores = {}
            for label in self.classes:
                score = self.class_log_prior[label]
                for token, count in counts.items():
                    score += count * self.feature_log_prob[label].get(
                        token,
                        self.default_log_prob[label],
                    )
                scores[label] = score
            predictions.append(max(scores, key=scores.get))
        return predictions


def roc_auc(labels, scores):
    pairs = sorted(zip(scores, labels), key=lambda item: item[0])
    positive = sum(1 for label in labels if label == 1)
    negative = len(labels) - positive
    if positive == 0 or negative == 0:
        return 0.5
    rank_sum = 0.0
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and pairs[end][0] == pairs[index][0]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        positives_in_tie = sum(label for _, label in pairs[index:end])
        rank_sum += positives_in_tie * average_rank
        index = end
    return (rank_sum - positive * (positive + 1) / 2.0) / (positive * negative)


def pr_auc(labels, scores):
    pairs = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    positives = sum(labels)
    if positives == 0:
        return 0.0
    tp = 0
    fp = 0
    area = 0.0
    previous_recall = 0.0
    for score, label in pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / max(1, tp + fp)
        area += precision * (recall - previous_recall)
        previous_recall = recall
    return area


def brier_score(labels, scores):
    return sum((score - label) ** 2 for label, score in zip(labels, scores)) / len(labels)


def log_loss(labels, scores):
    epsilon = 1e-12
    total = 0.0
    for label, score in zip(labels, scores):
        score = min(1.0 - epsilon, max(epsilon, score))
        total += label * math.log(score) + (1 - label) * math.log(1 - score)
    return -total / len(labels)


def calibration_slope_intercept(labels, scores):
    logits = [
        math.log(min(1.0 - 1e-6, max(1e-6, score)) / (1.0 - min(1.0 - 1e-6, max(1e-6, score))))
        for score in scores
    ]
    mean_x = sum(logits) / len(logits)
    mean_y = sum(labels) / len(labels)
    variance_x = sum((value - mean_x) ** 2 for value in logits)
    if variance_x == 0:
        return 0.0, mean_y
    slope = sum(
        (x_value - mean_x) * (y_value - mean_y)
        for x_value, y_value in zip(logits, labels)
    ) / variance_x
    intercept = mean_y - slope * mean_x
    return slope, intercept


def binary_metrics(labels, scores):
    if not labels:
        return {
            "roc_auc": 0.5,
            "pr_auc": 0.0,
            "brier_score": 0.0,
            "log_loss": 0.0,
            "calibration_slope": 0.0,
            "calibration_intercept": 0.0,
        }
    slope, intercept = calibration_slope_intercept(labels, scores)
    return {
        "roc_auc": roc_auc(labels, scores),
        "pr_auc": pr_auc(labels, scores),
        "brier_score": brier_score(labels, scores),
        "log_loss": log_loss(labels, scores),
        "calibration_slope": slope,
        "calibration_intercept": intercept,
    }


def macro_weighted_f1(labels, predictions):
    classes = sorted(set(labels) | set(predictions))
    rows = []
    total = len(labels)
    for label in classes:
        tp = sum(1 for y, pred in zip(labels, predictions) if y == label and pred == label)
        fp = sum(1 for y, pred in zip(labels, predictions) if y != label and pred == label)
        fn = sum(1 for y, pred in zip(labels, predictions) if y == label and pred != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        support = sum(1 for y in labels if y == label)
        rows.append({
            "class": label,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        })
    macro_f1 = sum(row["f1"] for row in rows) / len(rows) if rows else 0.0
    weighted_f1 = (
        sum(row["f1"] * row["support"] for row in rows) / total
        if total
        else 0.0
    )
    accuracy = sum(1 for y, pred in zip(labels, predictions) if y == pred) / total
    return accuracy, macro_f1, weighted_f1, rows


if __name__ == "__main__":
    y = [0, 0, 1, 1]
    p = [0.1, 0.4, 0.6, 0.9]
    print(binary_metrics(y, p))
