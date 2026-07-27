import hashlib
import json
from pathlib import Path

from ml_train_baselines import as_float
from ml_wolf_kill_model_freeze import current_git_commit


DEFAULT_SELECTIVE_OVERRIDE_MANIFEST_PATH = (
    Path("results")
    / "ml_optimization_stage2b"
    / "selective_override_manifest.json"
)


def stable_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256_json(value):
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def percentile(values, quantile):
    numeric = sorted(float(value) for value in values)
    if not numeric:
        return 0.0
    if len(numeric) == 1:
        return numeric[0]
    position = (len(numeric) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(numeric) - 1)
    weight = position - lower
    return numeric[lower] * (1.0 - weight) + numeric[upper] * weight


def load_selective_override_manifest(path):
    if path is None:
        path = DEFAULT_SELECTIVE_OVERRIDE_MANIFEST_PATH
    with Path(path).open() as file:
        return json.load(file)


def write_selective_override_manifest(path, manifest):
    Path(path).parent.mkdir(exist_ok=True, parents=True)
    payload = dict(manifest)
    payload["manifest_hash"] = sha256_json({
        key: value
        for key, value in payload.items()
        if key != "manifest_hash"
    })
    with Path(path).open("w") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")
    return payload


def candidate_row_for_uid(candidate_rows, uid):
    for row in candidate_rows:
        if str(row.get("candidate_uid")) == str(uid):
            return row
    return None


def candidate_row_for_player_id(candidate_rows, player_id):
    for row in candidate_rows:
        if str(row.get("candidate_player_id")) == str(player_id):
            return row
    return None


def top_ml_row(candidate_rows):
    if not candidate_rows:
        return None
    return sorted(
        candidate_rows,
        key=lambda row: (
            -as_float(row.get("ml_predicted_wolf_value")),
            as_float(row.get("tie_break_value")),
            str(row.get("candidate_uid")),
        ),
    )[0]


def build_selective_metrics(candidate_rows, existing_row=None, ml_row=None):
    if ml_row is None:
        ml_row = top_ml_row(candidate_rows)
    if existing_row is None:
        existing_candidates = [
            row for row in candidate_rows
            if int(row.get("action_selected_by_existing_policy", 0)) == 1
        ]
        existing_row = existing_candidates[0] if existing_candidates else None

    if ml_row is None or existing_row is None:
        return {
            "selective_metric_complete": False,
            "ml_existing_disagree": False,
            "ml_advantage_over_existing": 0.0,
            "top_two_predicted_value_margin": 0.0,
            "selected_shift_category": "unknown",
            "selected_missing_feature_count": 0,
            "selected_maximum_absolute_z_score": 0.0,
            "selected_fraction_outside_training_minmax": 0.0,
            "selected_feature_vector_novelty_score": 0.0,
            "selected_prediction_extremity": 0.0,
        }

    margin = as_float(ml_row.get("candidate_ranking_margin"))
    advantage = (
        as_float(ml_row.get("ml_predicted_wolf_value"))
        - as_float(existing_row.get("ml_predicted_wolf_value"))
    )
    return {
        "selective_metric_complete": True,
        "ml_existing_disagree": (
            str(ml_row.get("candidate_uid"))
            != str(existing_row.get("candidate_uid"))
        ),
        "ml_advantage_over_existing": advantage,
        "top_two_predicted_value_margin": margin,
        "selected_shift_category": ml_row.get(
            "distribution_shift_category",
            ml_row.get("candidate_distribution_shift_category", "unknown"),
        ),
        "selected_missing_feature_count": int(as_float(
            ml_row.get("missing_feature_count")
        )),
        "selected_maximum_absolute_z_score": as_float(
            ml_row.get("maximum_absolute_z_score")
        ),
        "selected_fraction_outside_training_minmax": as_float(
            ml_row.get("fraction_features_outside_training_minmax")
        ),
        "selected_feature_vector_novelty_score": as_float(
            ml_row.get("feature_vector_novelty_score")
        ),
        "selected_prediction_extremity": as_float(
            ml_row.get("prediction_extremity")
        ),
    }


def evaluate_selective_override(candidate_rows, existing_row, ml_row, manifest):
    metrics = build_selective_metrics(
        candidate_rows,
        existing_row=existing_row,
        ml_row=ml_row,
    )
    rule = manifest.get("rule", manifest)
    allowed_shift_categories = set(rule.get(
        "allowed_shift_categories",
        ["in_distribution"],
    ))
    checks = {
        "metric_complete": bool(metrics["selective_metric_complete"]),
        "ml_existing_disagree": bool(metrics["ml_existing_disagree"]),
        "shift_allowed": (
            metrics["selected_shift_category"] in allowed_shift_categories
        ),
        "margin_threshold_met": (
            metrics["top_two_predicted_value_margin"]
            >= as_float(rule.get("min_top_two_margin"), 0.0)
        ),
        "advantage_threshold_met": (
            metrics["ml_advantage_over_existing"]
            >= as_float(rule.get("min_ml_advantage_over_existing"), 0.0)
        ),
        "missingness_allowed": (
            metrics["selected_missing_feature_count"]
            <= int(as_float(rule.get("max_missing_feature_count"), 0))
        ),
        "extrapolation_allowed": (
            metrics["selected_maximum_absolute_z_score"]
            <= as_float(rule.get("max_absolute_z_score"), 2.5)
            and metrics["selected_fraction_outside_training_minmax"]
            <= as_float(rule.get("max_fraction_outside_training_minmax"), 0.0)
            and metrics["selected_feature_vector_novelty_score"]
            <= as_float(rule.get("max_feature_vector_novelty_score"), 3.0)
        ),
    }
    qualified = all(checks.values())
    return {
        **metrics,
        "selective_override_qualified": qualified,
        "selective_override_checks": checks,
        "selective_override_manifest_hash": manifest.get(
            "manifest_hash",
            "",
        ),
    }


def rows_by_decision(prediction_rows):
    grouped = {}
    for row in prediction_rows:
        grouped.setdefault(row.get("decision_id"), []).append(row)
    return grouped


def calibration_metrics_from_rows(decision_rows, prediction_rows):
    predictions = rows_by_decision(prediction_rows)
    metrics = []
    for decision in decision_rows:
        candidate_rows = predictions.get(decision.get("decision_id"), [])
        existing_row = candidate_row_for_player_id(
            candidate_rows,
            decision.get("existing_rule_target"),
        )
        ml_row = candidate_row_for_player_id(
            candidate_rows,
            decision.get("frozen_ml_target"),
        )
        metric = build_selective_metrics(candidate_rows, existing_row, ml_row)
        metric.update({
            "decision_id": decision.get("decision_id"),
            "seed": decision.get("seed"),
            "split": decision.get("split", ""),
            "behavioral_regime_id": decision.get("behavioral_regime_id"),
        })
        if metric["selective_metric_complete"]:
            metrics.append(metric)
    return metrics


def build_selective_override_manifest(
    decision_rows,
    prediction_rows,
    development_seeds,
    validation_seeds,
    final_test_seeds,
    output_path=DEFAULT_SELECTIVE_OVERRIDE_MANIFEST_PATH,
):
    calibration_seed_set = {
        str(seed)
        for seed in list(development_seeds) + list(validation_seeds)
    }
    calibration_decisions = [
        row for row in decision_rows
        if str(row.get("seed")) in calibration_seed_set
    ]
    metrics = calibration_metrics_from_rows(
        calibration_decisions,
        prediction_rows,
    )
    disagreement_metrics = [
        metric for metric in metrics
        if metric["ml_existing_disagree"]
        and metric["selected_shift_category"] == "in_distribution"
        and metric["selected_missing_feature_count"] == 0
    ]
    positive_advantages = [
        metric["ml_advantage_over_existing"]
        for metric in disagreement_metrics
        if metric["ml_advantage_over_existing"] > 0
    ]
    margins = [
        metric["top_two_predicted_value_margin"]
        for metric in disagreement_metrics
    ]
    novelty_scores = [
        metric["selected_feature_vector_novelty_score"]
        for metric in disagreement_metrics
    ]
    max_z_scores = [
        metric["selected_maximum_absolute_z_score"]
        for metric in disagreement_metrics
    ]

    rule = {
        "allowed_shift_categories": ["in_distribution"],
        "min_top_two_margin": max(0.01, percentile(margins, 0.50)),
        "min_ml_advantage_over_existing": max(
            0.005,
            percentile(positive_advantages, 0.50),
        ),
        "max_missing_feature_count": 0,
        "max_absolute_z_score": min(2.5, percentile(max_z_scores, 0.90) or 2.5),
        "max_fraction_outside_training_minmax": 0.0,
        "max_feature_vector_novelty_score": min(
            3.0,
            percentile(novelty_scores, 0.90) or 3.0,
        ),
        "threshold_selection_note": (
            "Thresholds were calibrated only from development and validation "
            "shadow decisions. Final-test outcomes were excluded."
        ),
    }
    manifest = {
        "stage": "ml_optimization_stage2b",
        "policy": "selective_ml_override",
        "rule": rule,
        "margin_bands": {
            "very_low_margin_max": 0.01,
            "low_margin_max": 0.03,
            "medium_margin_max": 0.06,
        },
        "development_seeds": list(development_seeds),
        "validation_seeds": list(validation_seeds),
        "excluded_final_test_seeds": list(final_test_seeds),
        "calibration_decision_count": len(metrics),
        "calibration_disagreement_in_distribution_count": (
            len(disagreement_metrics)
        ),
        "allowed_for_model_training": False,
        "primary_model_retrained": False,
        "source_commit_hash": current_git_commit(),
    }
    return write_selective_override_manifest(output_path, manifest)
