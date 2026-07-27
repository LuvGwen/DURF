from collections import defaultdict

from ml_train_baselines import as_float


DEFAULT_MARGIN_BANDS = {
    "very_low_margin_max": 0.01,
    "low_margin_max": 0.03,
    "medium_margin_max": 0.06,
}


def intervention_count_band(count):
    count = int(as_float(count))
    if count <= 0:
        return "0_interventions"
    if count == 1:
        return "1_intervention"
    if count == 2:
        return "2_interventions"
    return "3_plus_interventions"


def classify_margin_band(margin, bands=None):
    if bands is None:
        bands = DEFAULT_MARGIN_BANDS
    value = as_float(margin)
    if value < as_float(bands.get("very_low_margin_max"), 0.01):
        return "very_low_margin"
    if value < as_float(bands.get("low_margin_max"), 0.03):
        return "low_margin"
    if value < as_float(bands.get("medium_margin_max"), 0.06):
        return "medium_margin"
    return "high_margin"


def mean(values):
    numeric = [as_float(value) for value in values]
    return sum(numeric) / len(numeric) if numeric else 0.0


def summarize_by_group(rows, fields, metric_fields):
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(field, "") for field in fields)].append(row)
    output = []
    for key, group_rows in sorted(grouped.items()):
        result = {
            field: key[index]
            for index, field in enumerate(fields)
        }
        result["rows"] = len(group_rows)
        for metric in metric_fields:
            result[f"avg_{metric}"] = mean(
                row.get(metric, 0.0) for row in group_rows
            )
        result["wolf_win_rate"] = mean(
            row.get("wolf_win", 0.0) for row in group_rows
        )
        output.append(result)
    return output


def add_shift_derived_fields(decision_rows, margin_bands=None):
    rows = []
    for row in decision_rows:
        derived = dict(row)
        derived["margin_band"] = classify_margin_band(
            row.get("top_two_predicted_value_margin", 0.0),
            bands=margin_bands,
        )
        derived["prior_intervention_band"] = intervention_count_band(
            row.get("prior_ml_interventions", 0)
        )
        derived["cumulative_intervention_band"] = intervention_count_band(
            row.get("cumulative_ml_interventions", 0)
        )
        derived["strong_shift_flag"] = int(
            row.get("distribution_shift_category") == "strong_shift"
        )
        derived["in_distribution_flag"] = int(
            row.get("distribution_shift_category") == "in_distribution"
        )
        rows.append(derived)
    return rows


def summarize_distribution_shift(decision_rows, margin_bands=None):
    rows = add_shift_derived_fields(decision_rows, margin_bands=margin_bands)
    return summarize_by_group(
        rows,
        ["policy_name", "distribution_shift_category"],
        [
            "top_two_predicted_value_margin",
            "ml_advantage_over_existing",
            "prior_ml_interventions",
            "cumulative_ml_interventions",
            "strong_shift_flag",
        ],
    )


def summarize_margin_bands(decision_rows, margin_bands=None):
    rows = add_shift_derived_fields(decision_rows, margin_bands=margin_bands)
    return summarize_by_group(
        rows,
        ["policy_name", "margin_band"],
        [
            "top_two_predicted_value_margin",
            "ml_advantage_over_existing",
            "stage2b_executed_ml_intervention",
            "strong_shift_flag",
        ],
    )


def summarize_intervention_counts(game_rows):
    rows = []
    for row in game_rows:
        derived = dict(row)
        derived["intervention_count_band"] = intervention_count_band(
            row.get("total_ml_interventions", 0)
        )
        rows.append(derived)
    return summarize_by_group(
        rows,
        ["policy_name", "intervention_count_band"],
        [
            "total_ml_interventions",
            "strong_shift_decision_rate",
            "avg_top_two_margin",
            "successful_night_kills",
            "special_role_kills",
            "witch_saves",
            "hunter_retaliations",
            "round_number",
        ],
    )
