import math


def calculate_distribution_shift(manifest, feature_row, prediction=None, margin=None):
    feature_order = manifest["feature_order"]
    means = manifest["standardization_means"]
    scales = manifest["standardization_scales"]
    ranges = manifest.get("training_feature_ranges", {})

    squared_z_sum = 0.0
    max_abs_z = 0.0
    outside_count = 0
    missing_count = 0

    for feature, mean, scale in zip(feature_order, means, scales):
        raw_value = feature_row.get(feature)
        if raw_value in ("", None):
            missing_count += 1
            value = 0.0
        else:
            value = float(raw_value)
        scale = scale if scale else 1.0
        z_score = (value - mean) / scale
        abs_z = abs(z_score)
        squared_z_sum += z_score ** 2
        max_abs_z = max(max_abs_z, abs_z)

        training_range = ranges.get(feature, {})
        lower = training_range.get("min")
        upper = training_range.get("max")
        if lower is not None and upper is not None:
            if value < lower or value > upper:
                outside_count += 1

    feature_count = len(feature_order) if feature_order else 1
    fraction_outside = outside_count / feature_count
    standardized_distance = math.sqrt(squared_z_sum / feature_count)
    prediction_extremity = (
        abs(float(prediction) - 0.5)
        if prediction is not None
        else 0.0
    )
    candidate_margin = float(margin) if margin is not None else 0.0
    novelty_score = (
        standardized_distance
        + 0.50 * max_abs_z
        + 2.00 * fraction_outside
        + 0.10 * missing_count
    )

    if (
        max_abs_z >= 4.0
        or fraction_outside >= 0.25
        or missing_count > 0
        or novelty_score >= 5.0
    ):
        category = "strong_shift"
    elif (
        max_abs_z >= 2.5
        or fraction_outside >= 0.10
        or novelty_score >= 3.0
    ):
        category = "mild_shift"
    else:
        category = "in_distribution"

    return {
        "standardized_feature_distance": standardized_distance,
        "maximum_absolute_z_score": max_abs_z,
        "fraction_features_outside_training_minmax": fraction_outside,
        "missing_feature_count": missing_count,
        "feature_vector_novelty_score": novelty_score,
        "prediction_extremity": prediction_extremity,
        "candidate_ranking_margin": candidate_margin,
        "distribution_shift_category": category,
    }


def summarize_shift_rows(rows):
    grouped = {}
    for row in rows:
        key = row.get("distribution_shift_category", "unknown")
        grouped.setdefault(key, []).append(row)

    output = []
    for category, category_rows in sorted(grouped.items()):
        wolf_wins = sum(
            int(row.get("wolf_win", 0))
            for row in category_rows
            if row.get("wolf_win") not in ("", None)
        )
        total = len(category_rows)
        output.append({
            "distribution_shift_category": category,
            "rows": total,
            "wolf_win_rate": wolf_wins / total if total else 0.0,
            "avg_standardized_feature_distance": mean_float(
                row.get("standardized_feature_distance")
                for row in category_rows
            ),
            "avg_max_abs_z": mean_float(
                row.get("maximum_absolute_z_score")
                for row in category_rows
            ),
            "avg_fraction_outside_training_minmax": mean_float(
                row.get("fraction_features_outside_training_minmax")
                for row in category_rows
            ),
            "avg_prediction_extremity": mean_float(
                row.get("prediction_extremity")
                for row in category_rows
            ),
        })
    return output


def mean_float(values):
    numeric = []
    for value in values:
        if value in ("", None):
            continue
        numeric.append(float(value))
    return sum(numeric) / len(numeric) if numeric else 0.0
