import csv
import json
import math
import os
import tempfile
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd


OUTPUT_DIR = Path("results") / "data_analysis" / "seat_order_neutral"
SOURCE_DIR = Path("results") / "seat_order_neutral"
RAW_PATH = SOURCE_DIR / "seat_order_neutral_game_level_raw.csv"
PAIR_SUMMARY_PATH = SOURCE_DIR / "seat_order_neutral_matched_pair_summary.csv"
STRATEGY_SUMMARY_PATH = SOURCE_DIR / "seat_order_neutral_strategy_summary.csv"
LABEL_SUMMARY_PATH = SOURCE_DIR / "seat_order_neutral_label_condition_summary.csv"
DIVERGENCE_SUMMARY_PATH = SOURCE_DIR / "seat_order_neutral_divergence_summary.csv"
SCHEMA_PATH = SOURCE_DIR / "seat_order_neutral_schema.md"
AUDIT_PATH = SOURCE_DIR / "seat_order_neutral_implementation_audit.md"
REPORT_SOURCE_PATH = SOURCE_DIR / "seat_order_neutral_experiment_report.md"

VALIDATION_SUMMARY_PATH = OUTPUT_DIR / "validation_summary.csv"
DESCRIPTIVE_PATH = OUTPUT_DIR / "descriptive_statistics.csv"
OMNIBUS_PATH = OUTPUT_DIR / "strategy_omnibus_tests.csv"
PRIMARY_CONTRASTS_PATH = OUTPUT_DIR / "primary_pairwise_contrasts.csv"
PAIRED_ANALYSIS_PATH = OUTPUT_DIR / "paired_strategy_analysis.csv"
LABEL_INVARIANCE_PATH = OUTPUT_DIR / "label_invariance_validation.csv"
EARLY_DISCOVERY_PATH = OUTPUT_DIR / "early_discovery_analysis.csv"
MECHANISM_MODELS_PATH = OUTPUT_DIR / "mechanism_models.csv"
PHYSICAL_LAYOUT_PATH = OUTPUT_DIR / "physical_layout_interactions.csv"
SEED_ROBUSTNESS_PATH = OUTPUT_DIR / "seed_robustness.csv"
EFFECT_SIZE_PATH = OUTPUT_DIR / "effect_size_precision.csv"
RESIDUAL_VALIDITY_PATH = OUTPUT_DIR / "residual_validity_assessment.md"
ANALYSIS_REPORT_PATH = OUTPUT_DIR / "analysis_report.md"

STRATEGIES = [
    "physical_clockwise",
    "physical_counterclockwise",
    "alternate_physical_sides",
    "random_neutral",
]
LABEL_CONDITIONS = ["normal", "mirrored", "rotated"]
SEEDS = [42, 43, 44, 45, 46]
PRIMARY_CONTRASTS = [
    ("physical_clockwise", "physical_counterclockwise"),
    ("physical_clockwise", "random_neutral"),
    ("physical_clockwise", "alternate_physical_sides"),
    ("alternate_physical_sides", "random_neutral"),
    ("physical_counterclockwise", "random_neutral"),
    ("alternate_physical_sides", "physical_counterclockwise"),
]
NORMAL = NormalDist()


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mpl_dir = Path(tempfile.gettempdir()) / "durf_werewolf_mpl_cache"
    mpl_dir.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))


def read_json_list(value):
    if value is None or value == "" or (isinstance(value, float) and math.isnan(value)):
        return []
    return json.loads(value)


def safe_float(value):
    if value is None or value == "" or (isinstance(value, float) and math.isnan(value)):
        return np.nan
    return float(value)


def safe_int(value):
    if value is None or value == "" or (isinstance(value, float) and math.isnan(value)):
        return np.nan
    return int(value)


def write_rows(path, rows, fieldnames=None):
    rows = list(rows)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            restval="",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def pct(value):
    if value == "" or pd.isna(value):
        return "NA"
    return f"{float(value) * 100:.2f}%"


def num(value, digits=3):
    if value == "" or pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def pp(value):
    if value == "" or pd.isna(value):
        return "NA"
    return f"{float(value) * 100:.2f} pp"


def odds_ratio_text(value):
    if value == "" or pd.isna(value):
        return "NA"
    return f"{float(value):.3f}"


def wilson_ci(successes, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) / n) + z * z / (4 * n * n)) / denom
    return center - half, center + half


def normal_ci(mean_value, se, z=1.96):
    return mean_value - z * se, mean_value + z * se


def normal_pvalue(z_value):
    return 2 * (1 - NORMAL.cdf(abs(z_value)))


def chi_square_sf(x, df):
    # Regularized upper incomplete gamma Q(df / 2, x / 2), implemented to
    # avoid adding scipy/statsmodels dependencies to the repository.
    if x < 0 or df <= 0:
        return np.nan
    a = df / 2.0
    xx = x / 2.0
    if xx == 0:
        return 1.0

    eps = 1e-12
    max_iter = 1000

    if xx < a + 1.0:
        ap = a
        term = 1.0 / a
        total = term
        for _ in range(max_iter):
            ap += 1.0
            term *= xx / ap
            total += term
            if abs(term) < abs(total) * eps:
                break
        lower = total * math.exp(-xx + a * math.log(xx) - math.lgamma(a))
        return max(0.0, min(1.0, 1.0 - lower))

    b = xx + 1.0 - a
    c = 1.0 / 1e-300
    d = 1.0 / b
    h = d
    for i in range(1, max_iter + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    upper = math.exp(-xx + a * math.log(xx) - math.lgamma(a)) * h
    return max(0.0, min(1.0, upper))


def holm_adjust(rows, p_key="p_value", out_key="holm_p_value"):
    valid = [
        (index, row[p_key])
        for index, row in enumerate(rows)
        if row.get(p_key) not in ("", None) and not pd.isna(row[p_key])
    ]
    valid.sort(key=lambda item: item[1])
    m = len(valid)
    adjusted = [None] * len(rows)
    running = 0.0
    for rank, (index, p_value) in enumerate(valid):
        adjusted_p = min(1.0, (m - rank) * p_value)
        running = max(running, adjusted_p)
        adjusted[index] = running
    for index, row in enumerate(rows):
        row[out_key] = "" if adjusted[index] is None else adjusted[index]
    return rows


def interpretation_label(p_value, holm_p_value, abs_diff):
    if holm_p_value != "" and holm_p_value < 0.05:
        return "statistically supported"
    if abs_diff >= 0.02:
        return "practically meaningful but statistically uncertain"
    if p_value != "" and p_value < 0.10:
        return "weak/inconclusive"
    return "unsupported"


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -35, 35)))


def fit_logit(X, y, colnames, max_iter=100, tol=1e-9):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    beta = np.zeros(X.shape[1])
    converged = False
    for _ in range(max_iter):
        eta = X @ beta
        p = sigmoid(eta)
        w = np.clip(p * (1 - p), 1e-8, None)
        hessian = X.T @ (w[:, None] * X)
        score = X.T @ (y - p)
        step = np.linalg.pinv(hessian) @ score
        beta_next = beta + step
        if np.max(np.abs(step)) < tol:
            beta = beta_next
            converged = True
            break
        beta = beta_next
    p = np.clip(sigmoid(X @ beta), 1e-12, 1 - 1e-12)
    w = np.clip(p * (1 - p), 1e-8, None)
    hessian = X.T @ (w[:, None] * X)
    cov = np.linalg.pinv(hessian)
    log_likelihood = float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))
    return {
        "beta": beta,
        "cov": cov,
        "columns": list(colnames),
        "log_likelihood": log_likelihood,
        "n": len(y),
        "k": X.shape[1],
        "converged": converged,
    }


def make_design(df, strategy_reference="random_neutral", extra_terms=None):
    if extra_terms is None:
        extra_terms = []
    columns = [np.ones(len(df))]
    names = ["intercept"]

    for strategy in STRATEGIES:
        if strategy == strategy_reference:
            continue
        columns.append((df["strategy"] == strategy).astype(float).to_numpy())
        names.append(f"strategy:{strategy}")

    for seed in SEEDS[1:]:
        columns.append((df["seed"] == seed).astype(float).to_numpy())
        names.append(f"seed:{seed}")

    for name, values in extra_terms:
        columns.append(np.asarray(values, dtype=float))
        names.append(name)

    return np.column_stack(columns), names


def fit_strategy_model(df, extra_terms=None):
    X, names = make_design(df, extra_terms=extra_terms)
    return fit_logit(X, df["village_win"].to_numpy(), names)


def make_seed_only_design(df):
    columns = [np.ones(len(df))]
    names = ["intercept"]
    for seed in SEEDS[1:]:
        columns.append((df["seed"] == seed).astype(float).to_numpy())
        names.append(f"seed:{seed}")
    return np.column_stack(columns), names


def coefficient_vector(model, name):
    vector = np.zeros(len(model["columns"]))
    if name in model["columns"]:
        vector[model["columns"].index(name)] = 1.0
    return vector


def strategy_logit_vector(model, strategy):
    if strategy == "random_neutral":
        return np.zeros(len(model["columns"]))
    return coefficient_vector(model, f"strategy:{strategy}")


def contrast_from_model(model, strategy_a, strategy_b):
    vector = strategy_logit_vector(model, strategy_a) - strategy_logit_vector(
        model,
        strategy_b,
    )
    estimate = float(vector @ model["beta"])
    se = float(math.sqrt(max(vector @ model["cov"] @ vector, 0.0)))
    z_value = estimate / se if se > 0 else np.nan
    p_value = normal_pvalue(z_value) if se > 0 else np.nan
    ci_low, ci_high = normal_ci(estimate, 1.96 * 0 + se)
    return {
        "log_odds_estimate": estimate,
        "log_odds_se": se,
        "z_value": z_value,
        "p_value": p_value,
        "odds_ratio": math.exp(estimate),
        "odds_ratio_ci_low": math.exp(ci_low),
        "odds_ratio_ci_high": math.exp(ci_high),
    }


def average_predicted_probability(df, model, strategy):
    adjusted_df = df.copy()
    adjusted_df["strategy"] = strategy

    columns = []
    for name in model["columns"]:
        if name == "intercept":
            columns.append(np.ones(len(adjusted_df)))
        elif name.startswith("strategy:"):
            strategy_name = name.split(":", 1)[1]
            columns.append((adjusted_df["strategy"] == strategy_name).astype(float))
        elif name.startswith("seed:"):
            seed = int(name.split(":", 1)[1])
            columns.append((adjusted_df["seed"] == seed).astype(float))
        elif name in adjusted_df.columns:
            columns.append(adjusted_df[name].astype(float))
        else:
            raise ValueError(f"Cannot rebuild prediction column: {name}")

    X = np.column_stack(columns)
    return float(np.mean(sigmoid(X @ model["beta"])))


def likelihood_ratio_test(full_model, reduced_model):
    statistic = 2 * (
        full_model["log_likelihood"] - reduced_model["log_likelihood"]
    )
    df = full_model["k"] - reduced_model["k"]
    return statistic, df, chi_square_sf(statistic, df)


def add_categorical_terms(df, column, prefix, include_interactions=True):
    terms = []
    categories = sorted(df[column].dropna().unique())
    if len(categories) <= 1:
        return terms
    reference = categories[0]
    main_terms = []
    for category in categories:
        if category == reference:
            continue
        values = (df[column] == category).astype(float).to_numpy()
        name = f"{prefix}:{category}"
        terms.append((name, values))
        main_terms.append((name, values))
    if include_interactions:
        for strategy in STRATEGIES:
            if strategy == "random_neutral":
                continue
            strategy_indicator = (df["strategy"] == strategy).astype(float).to_numpy()
            for main_name, values in main_terms:
                terms.append((
                    f"strategy:{strategy}*{main_name}",
                    strategy_indicator * values,
                ))
    return terms


def add_numeric_interaction_terms(df, column, prefix):
    values = df[column].astype(float).to_numpy()
    terms = [(prefix, values)]
    for strategy in STRATEGIES:
        if strategy == "random_neutral":
            continue
        strategy_indicator = (df["strategy"] == strategy).astype(float).to_numpy()
        terms.append((f"strategy:{strategy}*{prefix}", strategy_indicator * values))
    return terms


def load_and_prepare_data():
    raw = pd.read_csv(RAW_PATH)
    for column in [
        "village_win",
        "wolf_win",
        "seed",
        "base_game_index",
        "total_rounds",
        "total_seer_checks",
        "first_check_target_is_wolf",
        "found_wolf_by_check_1",
        "found_wolf_by_check_2",
        "found_wolf_by_check_3",
        "no_wolf_found",
        "seer_found_wolf_count",
        "seer_survived_to_game_end",
        "wolves_on_edge",
        "wolves_on_inner",
        "wolves_left_side",
        "wolves_right_side",
        "edge_has_wolf",
        "seer_on_edge",
        "seer_left_side",
        "neutral_mode_enabled",
    ]:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")

    normal = raw[raw["label_condition"] == "normal"].copy().reset_index(drop=True)
    normal["wolf_seats_list"] = normal["physical_wolf_seats"].apply(read_json_list)
    normal["check_targets_list"] = normal["all_check_physical_targets"].apply(
        read_json_list
    )
    normal["checks_until_first_wolf_num"] = pd.to_numeric(
        normal["checks_until_first_wolf"],
        errors="coerce",
    )
    normal["checks_until_first_wolf_filled"] = (
        normal["checks_until_first_wolf_num"].fillna(0)
    )
    normal["first_check_target_is_wolf"] = (
        normal["first_check_target_is_wolf"].fillna(0)
    )
    normal["seer_survived_to_game_end"] = (
        normal["seer_survived_to_game_end"].fillna(0)
    )
    normal["config_id"] = (
        normal["seed"].astype(str)
        + "_"
        + normal["base_game_index"].astype(str)
    )

    derived_rows = normal.apply(derive_layout_features, axis=1)
    derived = pd.DataFrame(list(derived_rows))
    normal = pd.concat([normal, derived], axis=1)
    return raw, normal


def clockwise_distance(start, target):
    distance = (target - start) % 10
    return distance if distance != 0 else 10


def counterclockwise_distance(start, target):
    distance = (start - target) % 10
    return distance if distance != 0 else 10


def circular_distance(start, target):
    return min(clockwise_distance(start, target), counterclockwise_distance(start, target))


def derive_layout_features(row):
    seer_seat = int(row["physical_seer_seat"])
    wolf_seats = [int(value) for value in row["wolf_seats_list"]]
    check_targets = [int(value) for value in row["check_targets_list"]]
    clockwise_distances = [clockwise_distance(seer_seat, wolf) for wolf in wolf_seats]
    counterclockwise_distances = [
        counterclockwise_distance(seer_seat, wolf) for wolf in wolf_seats
    ]
    nearest_clockwise = min(clockwise_distances)
    nearest_counterclockwise = min(counterclockwise_distances)
    clockwise_side_count = sum(1 for distance in clockwise_distances if distance < 5)
    counterclockwise_side_count = sum(
        1 for distance in counterclockwise_distances if distance < 5
    )
    opposite_wolf_count = sum(1 for distance in clockwise_distances if distance == 5)
    local_wolf_density = sum(
        1 for wolf in wolf_seats
        if circular_distance(seer_seat, wolf) <= 2
    )

    if nearest_clockwise < nearest_counterclockwise:
        layout_condition = "clockwise_wolf_earlier"
    elif nearest_counterclockwise < nearest_clockwise:
        layout_condition = "counterclockwise_wolf_earlier"
    else:
        layout_condition = "equal_nearest_wolf_distance"

    first_target = safe_int(row["first_check_physical_target"])
    first_target_clockwise_distance = (
        clockwise_distance(seer_seat, first_target)
        if not pd.isna(first_target)
        else np.nan
    )
    first_target_counterclockwise_distance = (
        counterclockwise_distance(seer_seat, first_target)
        if not pd.isna(first_target)
        else np.nan
    )
    first_target_side = "none"
    if not pd.isna(first_target):
        if first_target_clockwise_distance < first_target_counterclockwise_distance:
            first_target_side = "clockwise"
        elif first_target_counterclockwise_distance < first_target_clockwise_distance:
            first_target_side = "counterclockwise"
        else:
            first_target_side = "opposite"

    discovered_wolves = [target for target in check_targets if target in wolf_seats]
    first_discovered_wolf = discovered_wolves[0] if discovered_wolves else np.nan
    first_discovered_wolf_cw_distance = (
        clockwise_distance(seer_seat, first_discovered_wolf)
        if not pd.isna(first_discovered_wolf)
        else np.nan
    )

    return {
        "clockwise_wolf_count": clockwise_side_count,
        "counterclockwise_wolf_count": counterclockwise_side_count,
        "opposite_wolf_count": opposite_wolf_count,
        "nearest_clockwise_wolf_distance": nearest_clockwise,
        "nearest_counterclockwise_wolf_distance": nearest_counterclockwise,
        "clockwise_minus_counterclockwise_nearest_distance": (
            nearest_clockwise - nearest_counterclockwise
        ),
        "first_wolf_encountered_clockwise_before_counter": (
            1 if nearest_clockwise < nearest_counterclockwise else 0
        ),
        "local_wolf_density_near_seer": local_wolf_density,
        "layout_condition": layout_condition,
        "first_target_clockwise_distance": first_target_clockwise_distance,
        "first_target_counterclockwise_distance": (
            first_target_counterclockwise_distance
        ),
        "first_target_side": first_target_side,
        "first_discovered_wolf_physical_seat": first_discovered_wolf,
        "first_discovered_wolf_clockwise_distance": (
            first_discovered_wolf_cw_distance
        ),
    }


def validate_data(raw, normal):
    rows = []
    append_validation = lambda check, observed, expected, passed: rows.append({
        "check": check,
        "observed": observed,
        "expected": expected,
        "passed": bool(passed),
    })
    append_validation("row_count", len(raw), 30000, len(raw) == 30000)
    append_validation(
        "unique_matched_sets",
        raw["matched_set_id"].nunique(),
        10000,
        raw["matched_set_id"].nunique() == 10000,
    )
    label_counts = raw.groupby("matched_set_id")["label_condition"].nunique()
    append_validation(
        "three_label_rows_per_matched_set",
        int((label_counts == 3).sum()),
        10000,
        bool((label_counts == 3).all()),
    )
    append_validation(
        "four_strategies",
        ",".join(sorted(raw["strategy"].unique())),
        ",".join(sorted(STRATEGIES)),
        set(raw["strategy"].unique()) == set(STRATEGIES),
    )
    append_validation(
        "seeds_42_to_46",
        ",".join(str(int(seed)) for seed in sorted(raw["seed"].unique())),
        "42,43,44,45,46",
        set(raw["seed"].unique()) == set(SEEDS),
    )
    seed_strategy_counts = normal.groupby(["strategy", "seed"]).size()
    append_validation(
        "500_base_configs_per_strategy_seed",
        int((seed_strategy_counts == 500).sum()),
        len(STRATEGIES) * len(SEEDS),
        bool((seed_strategy_counts == 500).all()),
    )
    append_validation(
        "valid_winners",
        ",".join(sorted(raw["winner"].unique())),
        "draw,village,wolf subset",
        set(raw["winner"].unique()).issubset({"wolf", "village", "draw"}),
    )
    append_validation(
        "unique_game_ids",
        raw["game_id"].nunique(),
        len(raw),
        raw["game_id"].nunique() == len(raw),
    )
    duplicate_check_rows = raw[
        raw["all_check_physical_targets"].apply(
            lambda value: len(read_json_list(value)) != len(set(read_json_list(value)))
        )
    ]
    append_validation(
        "no_duplicate_seer_checks",
        len(duplicate_check_rows),
        0,
        len(duplicate_check_rows) == 0,
    )
    for column in [
        "physical_seer_seat",
        "physical_wolf_seats",
        "all_check_physical_targets",
        "winner",
        "total_rounds",
        "seer_survived_to_game_end",
    ]:
        unique_counts = raw.groupby("matched_set_id")[column].nunique(dropna=False)
        append_validation(
            f"{column}_identical_across_label_conditions",
            int((unique_counts == 1).sum()),
            10000,
            bool((unique_counts == 1).all()),
        )
    append_validation(
        "physical_check_sequence_flag_matches_reference",
        int(
            raw[raw["label_condition"] != "normal"][
                "physical_check_sequence_matches_reference_until_divergence"
            ].sum()
        ),
        20000,
        bool(
            (
                raw[raw["label_condition"] != "normal"][
                    "physical_check_sequence_matches_reference_until_divergence"
                ] == 1
            ).all()
        ),
    )
    append_validation(
        "winner_flag_matches_reference",
        int(raw[raw["label_condition"] != "normal"]["paired_outcome_agreement"].sum()),
        20000,
        bool(
            (
                raw[raw["label_condition"] != "normal"][
                    "paired_outcome_agreement"
                ] == 1
            ).all()
        ),
    )
    append_validation(
        "final_physical_alive_set_matches_reference",
        int(
            raw[raw["label_condition"] != "normal"][
                "physical_final_alive_set_matches"
            ].sum()
        ),
        20000,
        bool(
            (
                raw[raw["label_condition"] != "normal"][
                    "physical_final_alive_set_matches"
                ] == 1
            ).all()
        ),
    )
    append_validation(
        "no_recorded_divergence",
        ",".join(sorted(raw["first_divergence_event_type"].fillna("none").unique())),
        "none",
        set(raw["first_divergence_event_type"].fillna("none").unique()) == {"none"},
    )
    append_validation(
        "neutral_mode_enabled_all_rows",
        int(raw["neutral_mode_enabled"].sum()),
        len(raw),
        bool((raw["neutral_mode_enabled"] == 1).all()),
    )

    physical_cols = [
        "physical_seer_seat",
        "physical_wolf_seats",
        "neutral_actor_iteration_order",
        "all_check_physical_targets",
        "winner",
        "village_win",
        "wolf_win",
        "total_rounds",
        "total_seer_checks",
        "first_check_target_is_wolf",
        "found_wolf_by_check_2",
        "found_wolf_by_check_3",
        "seer_survived_to_game_end",
        "seer_found_wolf_count",
        "search_path_coverage_score",
    ]
    mismatch_counts = {}
    for column in physical_cols:
        mismatch_counts[column] = int(
            (raw.groupby("matched_set_id")[column].nunique(dropna=False) > 1).sum()
        )
    append_validation(
        "physical_outcome_mechanism_duplicates_identical",
        sum(mismatch_counts.values()),
        0,
        sum(mismatch_counts.values()) == 0,
    )
    write_rows(VALIDATION_SUMMARY_PATH, rows)
    return rows, mismatch_counts


def make_descriptive_statistics(df):
    rows = []
    for strategy in STRATEGIES:
        group = df[df["strategy"] == strategy]
        n = len(group)
        village_wins = int(group["village_win"].sum())
        wolf_wins = int(group["wolf_win"].sum())
        ci_low, ci_high = wilson_ci(village_wins, n)
        rows.append({
            "strategy": strategy,
            "n_independent_base_games": n,
            "village_wins": village_wins,
            "wolf_wins": wolf_wins,
            "village_win_rate": village_wins / n,
            "village_win_ci_low": ci_low,
            "village_win_ci_high": ci_high,
            "wolf_win_rate": wolf_wins / n,
            "first_check_wolf_rate": group["first_check_target_is_wolf"].mean(),
            "found_wolf_by_check_2_rate": group["found_wolf_by_check_2"].mean(),
            "found_wolf_by_check_3_rate": group["found_wolf_by_check_3"].mean(),
            "no_wolf_found_rate": group["no_wolf_found"].mean(),
            "mean_checks_until_first_wolf": group[
                "checks_until_first_wolf_num"
            ].mean(),
            "mean_total_seer_checks": group["total_seer_checks"].mean(),
            "mean_wolves_found_per_game": group["seer_found_wolf_count"].mean(),
            "seer_survival_rate": group["seer_survived_to_game_end"].mean(),
            "mean_total_rounds": group["total_rounds"].mean(),
            "mean_search_path_coverage_score": group[
                "search_path_coverage_score"
            ].mean(),
        })
    write_rows(DESCRIPTIVE_PATH, rows)
    return rows


def raw_strategy_differences(descriptive_rows):
    by_strategy = {row["strategy"]: row for row in descriptive_rows}
    rows = []
    for strategy_a, strategy_b in [
        ("physical_clockwise", "physical_counterclockwise"),
        ("physical_clockwise", "random_neutral"),
        ("physical_clockwise", "alternate_physical_sides"),
        ("alternate_physical_sides", "random_neutral"),
    ]:
        rows.append({
            "contrast": f"{strategy_a} - {strategy_b}",
            "village_win_rate_difference": (
                by_strategy[strategy_a]["village_win_rate"]
                - by_strategy[strategy_b]["village_win_rate"]
            ),
            "first_check_wolf_rate_difference": (
                by_strategy[strategy_a]["first_check_wolf_rate"]
                - by_strategy[strategy_b]["first_check_wolf_rate"]
            ),
            "found_wolf_by_check_3_rate_difference": (
                by_strategy[strategy_a]["found_wolf_by_check_3_rate"]
                - by_strategy[strategy_b]["found_wolf_by_check_3_rate"]
            ),
            "seer_survival_rate_difference": (
                by_strategy[strategy_a]["seer_survival_rate"]
                - by_strategy[strategy_b]["seer_survival_rate"]
            ),
        })
    return rows


def make_primary_models(df):
    full_model = fit_strategy_model(df)
    seed_only_X, seed_only_names = make_seed_only_design(df)
    reduced_model = fit_logit(
        seed_only_X,
        df["village_win"].to_numpy(),
        seed_only_names,
    )
    lr_stat, lr_df, lr_p = likelihood_ratio_test(full_model, reduced_model)
    omnibus_rows = [{
        "test": "strategy_omnibus_seed_adjusted",
        "model": "village_win ~ strategy + seed",
        "reference_strategy": "random_neutral",
        "n_independent_base_games": len(df),
        "lr_statistic": lr_stat,
        "df": lr_df,
        "p_value": lr_p,
        "full_log_likelihood": full_model["log_likelihood"],
        "reduced_log_likelihood": reduced_model["log_likelihood"],
        "converged": full_model["converged"],
    }]
    write_rows(OMNIBUS_PATH, omnibus_rows)

    predicted = {
        strategy: average_predicted_probability(df, full_model, strategy)
        for strategy in STRATEGIES
    }
    contrast_rows = []
    for strategy_a, strategy_b in PRIMARY_CONTRASTS:
        contrast = contrast_from_model(full_model, strategy_a, strategy_b)
        diff = predicted[strategy_a] - predicted[strategy_b]
        contrast_rows.append({
            "contrast": f"{strategy_a} vs {strategy_b}",
            "strategy_a": strategy_a,
            "strategy_b": strategy_b,
            **contrast,
            "adjusted_probability_a": predicted[strategy_a],
            "adjusted_probability_b": predicted[strategy_b],
            "adjusted_probability_difference": diff,
            "absolute_probability_difference_pp": diff * 100,
            "interpretation": "",
        })
    holm_adjust(contrast_rows)
    for row in contrast_rows:
        row["interpretation"] = interpretation_label(
            row["p_value"],
            row["holm_p_value"],
            abs(row["adjusted_probability_difference"]),
        )
    write_rows(PRIMARY_CONTRASTS_PATH, contrast_rows)
    return full_model, omnibus_rows, contrast_rows, predicted


def binom_exact_two_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    logs = [
        math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
        - n * math.log(2)
        for i in range(k + 1)
    ]
    max_log = max(logs)
    cdf = math.exp(max_log) * sum(math.exp(value - max_log) for value in logs)
    return min(1.0, 2 * cdf)


def paired_bootstrap_diff(config_df, strategy_a, strategy_b, iterations=2000):
    pivot = config_df.pivot(
        index="config_id",
        columns="strategy",
        values="village_win",
    )
    diffs = (pivot[strategy_a] - pivot[strategy_b]).to_numpy()
    rng = np.random.default_rng(20260724)
    bootstrap = []
    for _ in range(iterations):
        sample = rng.choice(diffs, size=len(diffs), replace=True)
        bootstrap.append(float(np.mean(sample)))
    low, high = np.quantile(bootstrap, [0.025, 0.975])
    return float(low), float(high)


def make_paired_strategy_analysis(df):
    pairing_checks = []
    group = df.groupby("config_id")
    complete_configs = group.filter(
        lambda rows: set(rows["strategy"]) == set(STRATEGIES) and len(rows) == 4
    )
    for column in ["physical_seer_seat", "physical_wolf_seats"]:
        unique_counts = complete_configs.groupby("config_id")[column].nunique(
            dropna=False
        )
        pairing_checks.append({
            "check_type": "pairing_validation",
            "metric": f"{column}_identical_across_strategies",
            "observed": int((unique_counts == 1).sum()),
            "expected": 2500,
            "passed": bool((unique_counts == 1).all()),
        })

    pivot = complete_configs.pivot(
        index="config_id",
        columns="strategy",
        values="village_win",
    )
    rows = []
    for strategy_a, strategy_b in PRIMARY_CONTRASTS:
        a = pivot[strategy_a].astype(int)
        b = pivot[strategy_b].astype(int)
        diff_values = a - b
        b_count = int(((a == 1) & (b == 0)).sum())
        c_count = int(((a == 0) & (b == 1)).sum())
        discordant = b_count + c_count
        paired_diff = float(diff_values.mean())
        se = float(diff_values.std(ddof=1) / math.sqrt(len(diff_values)))
        ci_low, ci_high = normal_ci(paired_diff, se)
        correction = 0.5 if b_count == 0 or c_count == 0 else 0.0
        paired_or = (b_count + correction) / (c_count + correction)
        log_or = math.log(paired_or)
        log_or_se = math.sqrt(
            1.0 / (b_count + correction)
            + 1.0 / (c_count + correction)
        ) if discordant else np.nan
        or_ci_low = math.exp(log_or - 1.96 * log_or_se) if discordant else np.nan
        or_ci_high = math.exp(log_or + 1.96 * log_or_se) if discordant else np.nan
        p_value = binom_exact_two_sided(b_count, c_count)
        boot_low, boot_high = paired_bootstrap_diff(
            complete_configs,
            strategy_a,
            strategy_b,
        )
        rows.append({
            "check_type": "paired_contrast",
            "metric": f"{strategy_a} vs {strategy_b}",
            "strategy_a": strategy_a,
            "strategy_b": strategy_b,
            "matched_configurations": len(pivot),
            "a_win_b_loss": b_count,
            "a_loss_b_win": c_count,
            "discordant_pairs": discordant,
            "paired_village_win_difference": paired_diff,
            "paired_difference_ci_low": ci_low,
            "paired_difference_ci_high": ci_high,
            "paired_bootstrap_ci_low": boot_low,
            "paired_bootstrap_ci_high": boot_high,
            "paired_odds_ratio": paired_or,
            "paired_odds_ratio_ci_low": or_ci_low,
            "paired_odds_ratio_ci_high": or_ci_high,
            "p_value": p_value,
            "holm_p_value": "",
            "interpretation": "",
            "observed": "",
            "expected": "",
            "passed": "",
        })
    contrast_rows = [row for row in rows if row["check_type"] == "paired_contrast"]
    holm_adjust(contrast_rows)
    for row in contrast_rows:
        row["interpretation"] = interpretation_label(
            row["p_value"],
            row["holm_p_value"],
            abs(row["paired_village_win_difference"]),
        )
    all_rows = pairing_checks + rows
    write_rows(PAIRED_ANALYSIS_PATH, all_rows)
    return all_rows, complete_configs


def make_label_invariance_validation(raw):
    rows = []
    non_normal = raw[raw["label_condition"] != "normal"]
    metrics = {
        "identical_winners": "paired_outcome_agreement",
        "identical_first_physical_targets": (
            "physical_first_target_matches_reference"
        ),
        "identical_physical_check_sequences": (
            "physical_check_sequence_matches_reference_until_divergence"
        ),
        "identical_final_physical_alive_sets": "physical_final_alive_set_matches",
    }
    for label_condition in ["mirrored", "rotated"]:
        subset = non_normal[non_normal["label_condition"] == label_condition]
        for metric, column in metrics.items():
            successes = int(pd.to_numeric(subset[column], errors="coerce").sum())
            rows.append({
                "label_condition": label_condition,
                "metric": metric,
                "matched_sets": len(subset),
                "identical_count": successes,
                "identical_rate": successes / len(subset),
            })

        for column, metric in [
            ("total_rounds", "identical_total_rounds"),
            ("seer_survived_to_game_end", "identical_seer_survival"),
            ("first_check_target_is_wolf", "identical_first_check_wolf"),
            ("found_wolf_by_check_2", "identical_found_by_check_2"),
            ("found_wolf_by_check_3", "identical_found_by_check_3"),
            ("total_seer_checks", "identical_total_seer_checks"),
        ]:
            unique_counts = raw[
                raw["label_condition"].isin(["normal", label_condition])
            ].groupby("matched_set_id")[column].nunique(dropna=False)
            identical = int((unique_counts == 1).sum())
            rows.append({
                "label_condition": label_condition,
                "metric": metric,
                "matched_sets": len(unique_counts),
                "identical_count": identical,
                "identical_rate": identical / len(unique_counts),
            })
    write_rows(LABEL_INVARIANCE_PATH, rows)
    return rows


def make_early_discovery_analysis(df):
    rows = []
    for strategy in STRATEGIES:
        group = df[df["strategy"] == strategy]
        for metric in [
            "first_check_target_is_wolf",
            "found_wolf_by_check_2",
            "found_wolf_by_check_3",
            "no_wolf_found",
            "seer_survived_to_game_end",
        ]:
            successes = int(group[metric].sum())
            low, high = wilson_ci(successes, len(group))
            rows.append({
                "row_type": "strategy_metric",
                "strategy": strategy,
                "metric": metric,
                "n": len(group),
                "value": successes / len(group),
                "ci_low": low,
                "ci_high": high,
            })
        rows.append({
            "row_type": "strategy_metric",
            "strategy": strategy,
            "metric": "mean_checks_until_first_wolf",
            "n": int(group["checks_until_first_wolf_num"].notna().sum()),
            "value": group["checks_until_first_wolf_num"].mean(),
            "ci_low": "",
            "ci_high": "",
        })
        rows.append({
            "row_type": "strategy_metric",
            "strategy": strategy,
            "metric": "mean_total_seer_checks",
            "n": len(group),
            "value": group["total_seer_checks"].mean(),
            "ci_low": "",
            "ci_high": "",
        })

    for strategy_a, strategy_b in [
        ("physical_clockwise", "random_neutral"),
        ("physical_clockwise", "physical_counterclockwise"),
    ]:
        group_a = df[df["strategy"] == strategy_a]
        group_b = df[df["strategy"] == strategy_b]
        for metric in [
            "first_check_target_is_wolf",
            "found_wolf_by_check_2",
            "found_wolf_by_check_3",
            "no_wolf_found",
            "seer_survived_to_game_end",
            "total_seer_checks",
            "total_rounds",
        ]:
            rows.append({
                "row_type": "contrast_difference",
                "strategy": f"{strategy_a} - {strategy_b}",
                "metric": metric,
                "n": min(len(group_a), len(group_b)),
                "value": group_a[metric].mean() - group_b[metric].mean(),
                "ci_low": "",
                "ci_high": "",
            })
    write_rows(EARLY_DISCOVERY_PATH, rows)
    return rows


def make_mechanism_models(df):
    models = [
        ("A_strategy_seed", []),
        ("B_plus_first_check_wolf", [
            ("first_check_target_is_wolf", df["first_check_target_is_wolf"])
        ]),
        ("C_plus_check2_check3", [
            ("found_wolf_by_check_2", df["found_wolf_by_check_2"]),
            ("found_wolf_by_check_3", df["found_wolf_by_check_3"]),
        ]),
        ("D_plus_timing_no_wolf", [
            (
                "checks_until_first_wolf_filled",
                df["checks_until_first_wolf_filled"],
            ),
            ("no_wolf_found", df["no_wolf_found"]),
        ]),
        ("E_plus_seer_survival", [
            ("seer_survived_to_game_end", df["seer_survived_to_game_end"])
        ]),
        ("F_plus_checks_rounds", [
            ("total_seer_checks", df["total_seer_checks"]),
            ("total_rounds", df["total_rounds"]),
        ]),
        ("G_full_diagnostic", [
            ("first_check_target_is_wolf", df["first_check_target_is_wolf"]),
            ("found_wolf_by_check_2", df["found_wolf_by_check_2"]),
            ("found_wolf_by_check_3", df["found_wolf_by_check_3"]),
            (
                "checks_until_first_wolf_filled",
                df["checks_until_first_wolf_filled"],
            ),
            ("no_wolf_found", df["no_wolf_found"]),
            ("seer_survived_to_game_end", df["seer_survived_to_game_end"]),
            ("total_seer_checks", df["total_seer_checks"]),
            ("total_rounds", df["total_rounds"]),
        ]),
    ]
    rows = []
    for model_name, extra_terms in models:
        model = fit_strategy_model(df, extra_terms=extra_terms)
        cw_random = contrast_from_model(model, "physical_clockwise", "random_neutral")
        cw_counter = contrast_from_model(
            model,
            "physical_clockwise",
            "physical_counterclockwise",
        )
        pred_cw = average_predicted_probability(df, model, "physical_clockwise")
        pred_random = average_predicted_probability(df, model, "random_neutral")
        pred_counter = average_predicted_probability(
            df,
            model,
            "physical_counterclockwise",
        )
        rows.append({
            "model": model_name,
            "formula": "village_win ~ strategy + seed"
            + (" + " + " + ".join(name for name, _ in extra_terms) if extra_terms else ""),
            "n": len(df),
            "log_likelihood": model["log_likelihood"],
            "converged": model["converged"],
            "clockwise_vs_random_or": cw_random["odds_ratio"],
            "clockwise_vs_random_ci_low": cw_random["odds_ratio_ci_low"],
            "clockwise_vs_random_ci_high": cw_random["odds_ratio_ci_high"],
            "clockwise_vs_random_p": cw_random["p_value"],
            "clockwise_vs_counterclockwise_or": cw_counter["odds_ratio"],
            "clockwise_vs_counterclockwise_ci_low": (
                cw_counter["odds_ratio_ci_low"]
            ),
            "clockwise_vs_counterclockwise_ci_high": (
                cw_counter["odds_ratio_ci_high"]
            ),
            "clockwise_vs_counterclockwise_p": cw_counter["p_value"],
            "adjusted_prob_clockwise": pred_cw,
            "adjusted_prob_random": pred_random,
            "adjusted_prob_counterclockwise": pred_counter,
            "clockwise_minus_random_adjusted_pp": (pred_cw - pred_random) * 100,
            "clockwise_minus_counter_adjusted_pp": (pred_cw - pred_counter) * 100,
            "note": "diagnostic only; added terms may be intermediate/post-treatment",
        })
    write_rows(MECHANISM_MODELS_PATH, rows)
    return rows


def make_physical_layout_interactions(df):
    base_terms = []
    interaction_specs = [
        ("physical_seer_seat", "categorical"),
        ("clockwise_wolf_count", "numeric"),
        ("counterclockwise_wolf_count", "numeric"),
        ("nearest_clockwise_wolf_distance", "numeric"),
        ("nearest_counterclockwise_wolf_distance", "numeric"),
        ("first_check_target_is_wolf", "numeric"),
        ("wolves_on_edge", "numeric"),
        ("local_wolf_density_near_seer", "numeric"),
        ("layout_condition", "categorical"),
    ]
    rows = []
    base_model = fit_strategy_model(df)
    for variable, kind in interaction_specs:
        if kind == "categorical":
            main_terms = add_categorical_terms(
                df,
                variable,
                variable,
                include_interactions=False,
            )
            full_terms = add_categorical_terms(
                df,
                variable,
                variable,
                include_interactions=True,
            )
            interaction_df = len(full_terms) - len(main_terms)
        else:
            main_terms = [(variable, df[variable])]
            full_terms = add_numeric_interaction_terms(df, variable, variable)
            interaction_df = len(full_terms) - len(main_terms)
        reduced_model = fit_strategy_model(df, extra_terms=main_terms)
        full_model = fit_strategy_model(df, extra_terms=full_terms)
        lr_stat, lr_df, p_value = likelihood_ratio_test(full_model, reduced_model)
        rows.append({
            "row_type": "interaction_lr_test",
            "variable": variable,
            "kind": kind,
            "lr_statistic": lr_stat,
            "df": lr_df,
            "p_value": p_value,
            "base_log_likelihood": base_model["log_likelihood"],
            "reduced_log_likelihood": reduced_model["log_likelihood"],
            "full_log_likelihood": full_model["log_likelihood"],
            "interpretation": (
                "layout-dependent strategy performance"
                if p_value < 0.05
                else "no strong interaction evidence"
            ),
        })

    for layout_condition in sorted(df["layout_condition"].unique()):
        for strategy in ["physical_clockwise", "physical_counterclockwise"]:
            group = df[
                (df["layout_condition"] == layout_condition)
                & (df["strategy"] == strategy)
            ]
            rows.append({
                "row_type": "clockwise_counterclockwise_by_layout",
                "variable": layout_condition,
                "kind": "descriptive",
                "strategy": strategy,
                "n": len(group),
                "village_win_rate": group["village_win"].mean(),
                "first_check_wolf_rate": group[
                    "first_check_target_is_wolf"
                ].mean(),
                "found_wolf_by_check_3_rate": group[
                    "found_wolf_by_check_3"
                ].mean(),
            })
    write_rows(PHYSICAL_LAYOUT_PATH, rows)
    return rows


def make_seed_robustness(df):
    rows = []
    for seed in SEEDS:
        seed_rows = df[df["seed"] == seed]
        for strategy in STRATEGIES:
            group = seed_rows[seed_rows["strategy"] == strategy]
            rows.append({
                "row_type": "seed_strategy_rate",
                "seed": seed,
                "strategy": strategy,
                "n": len(group),
                "village_win_rate": group["village_win"].mean(),
                "wolf_win_rate": group["wolf_win"].mean(),
            })
        pivot = seed_rows.pivot(
            index="config_id",
            columns="strategy",
            values="village_win",
        )
        for strategy_a, strategy_b in PRIMARY_CONTRASTS:
            rows.append({
                "row_type": "seed_paired_difference",
                "seed": seed,
                "strategy": f"{strategy_a} - {strategy_b}",
                "n": len(pivot),
                "village_win_rate": (
                    pivot[strategy_a].mean() - pivot[strategy_b].mean()
                ),
                "wolf_win_rate": "",
            })

    for excluded_seed in SEEDS:
        subset = df[df["seed"] != excluded_seed]
        model = fit_strategy_model(subset)
        cw_counter = contrast_from_model(
            model,
            "physical_clockwise",
            "physical_counterclockwise",
        )
        cw_random = contrast_from_model(model, "physical_clockwise", "random_neutral")
        rows.append({
            "row_type": "leave_one_seed_out_model",
            "seed": f"exclude_{excluded_seed}",
            "strategy": "physical_clockwise_vs_physical_counterclockwise",
            "n": len(subset),
            "odds_ratio": cw_counter["odds_ratio"],
            "p_value": cw_counter["p_value"],
            "village_win_rate": "",
            "wolf_win_rate": "",
        })
        rows.append({
            "row_type": "leave_one_seed_out_model",
            "seed": f"exclude_{excluded_seed}",
            "strategy": "physical_clockwise_vs_random_neutral",
            "n": len(subset),
            "odds_ratio": cw_random["odds_ratio"],
            "p_value": cw_random["p_value"],
            "village_win_rate": "",
            "wolf_win_rate": "",
        })

    seed_terms = []
    for seed in SEEDS[1:]:
        seed_values = (df["seed"] == seed).astype(float).to_numpy()
        for strategy in STRATEGIES:
            if strategy == "random_neutral":
                continue
            strategy_values = (df["strategy"] == strategy).astype(float).to_numpy()
            seed_terms.append((
                f"strategy:{strategy}*seed:{seed}",
                strategy_values * seed_values,
            ))
    full_interaction = fit_strategy_model(df, extra_terms=seed_terms)
    base = fit_strategy_model(df)
    lr_stat, lr_df, p_value = likelihood_ratio_test(full_interaction, base)
    rows.append({
        "row_type": "strategy_seed_interaction_lr_test",
        "seed": "all",
        "strategy": "all",
        "n": len(df),
        "lr_statistic": lr_stat,
        "df": lr_df,
        "p_value": p_value,
        "village_win_rate": "",
        "wolf_win_rate": "",
    })
    write_rows(SEED_ROBUSTNESS_PATH, rows)
    return rows


def make_effect_size_precision(primary_rows, paired_rows):
    rows = []
    primary_by_contrast = {
        row["contrast"]: row
        for row in primary_rows
    }
    paired_by_metric = {
        row["metric"]: row
        for row in paired_rows
        if row.get("check_type") == "paired_contrast"
    }
    contrast_key = "physical_clockwise vs physical_counterclockwise"
    unpaired = primary_by_contrast[contrast_key]
    paired = paired_by_metric[contrast_key]
    rows.append({
        "contrast": contrast_key,
        "analysis_type": "seed_adjusted_logistic",
        "absolute_difference": unpaired["adjusted_probability_difference"],
        "odds_ratio": unpaired["odds_ratio"],
        "ci_low": unpaired["odds_ratio_ci_low"],
        "ci_high": unpaired["odds_ratio_ci_high"],
        "ci_width": unpaired["odds_ratio_ci_high"] - unpaired["odds_ratio_ci_low"],
        "holm_p_value": unpaired["holm_p_value"],
        "precision_note": (
            "CI is wide enough that effects near zero and modest positive "
            "clockwise effects remain compatible with the data."
        ),
    })
    rows.append({
        "contrast": contrast_key,
        "analysis_type": "paired_configuration",
        "absolute_difference": paired["paired_village_win_difference"],
        "odds_ratio": paired["paired_odds_ratio"],
        "ci_low": paired["paired_difference_ci_low"],
        "ci_high": paired["paired_difference_ci_high"],
        "ci_width": (
            paired["paired_difference_ci_high"] - paired["paired_difference_ci_low"]
        ),
        "holm_p_value": paired["holm_p_value"],
        "precision_note": (
            "Paired difference CI gives the directly interpretable range of "
            "percentage-point effects across shared base configurations."
        ),
    })
    write_rows(EFFECT_SIZE_PATH, rows)
    return rows


def make_figures(descriptive_rows, primary_rows, seed_rows, early_rows, layout_rows, paired_rows):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    strategy_labels = {
        "physical_clockwise": "Physical clockwise",
        "physical_counterclockwise": "Physical counterclockwise",
        "alternate_physical_sides": "Alternate physical sides",
        "random_neutral": "Random neutral",
    }
    colors = {
        "physical_clockwise": "#2f6fbb",
        "physical_counterclockwise": "#d28c2d",
        "alternate_physical_sides": "#7a9a45",
        "random_neutral": "#8c6bb1",
    }

    desc_df = pd.DataFrame(descriptive_rows)
    order = STRATEGIES
    fig, ax = plt.subplots(figsize=(9, 5))
    y = [desc_df[desc_df.strategy == strategy]["village_win_rate"].iloc[0] for strategy in order]
    low = [desc_df[desc_df.strategy == strategy]["village_win_ci_low"].iloc[0] for strategy in order]
    high = [desc_df[desc_df.strategy == strategy]["village_win_ci_high"].iloc[0] for strategy in order]
    err = [[y[i] - low[i] for i in range(len(y))], [high[i] - y[i] for i in range(len(y))]]
    ax.bar([strategy_labels[s] for s in order], y, yerr=err, color=[colors[s] for s in order], capsize=4)
    ax.set_ylim(0.34, 0.46)
    ax.set_ylabel("Village win rate")
    ax.set_title("Village win rate by neutral seer strategy")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "village_win_rate_by_strategy.svg")
    plt.close(fig)

    primary_df = pd.DataFrame(primary_rows)
    fig, ax = plt.subplots(figsize=(9, 5))
    values = primary_df["adjusted_probability_difference"].to_numpy()
    labels = primary_df["contrast"].str.replace("_", " ", regex=False).to_list()
    ax.barh(labels, values, color="#2f6fbb")
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_xlabel("Adjusted village-win difference")
    ax.set_title("Primary strategy contrasts")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "primary_strategy_contrasts.svg")
    plt.close(fig)

    seed_df = pd.DataFrame([
        row for row in seed_rows
        if row["row_type"] == "seed_strategy_rate"
    ])
    fig, ax = plt.subplots(figsize=(9, 5))
    for strategy in order:
        group = seed_df[seed_df["strategy"] == strategy].sort_values("seed")
        ax.plot(
            group["seed"],
            group["village_win_rate"],
            marker="o",
            label=strategy_labels[strategy],
            color=colors[strategy],
        )
    ax.set_ylim(0.30, 0.52)
    ax.set_xlabel("Seed")
    ax.set_ylabel("Village win rate")
    ax.set_title("Strategy performance by seed")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "strategy_performance_by_seed.svg")
    plt.close(fig)

    early_df = pd.DataFrame([
        row for row in early_rows
        if row["row_type"] == "strategy_metric"
        and row["metric"] in {
            "first_check_target_is_wolf",
            "found_wolf_by_check_2",
            "found_wolf_by_check_3",
        }
    ])
    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.22
    x = np.arange(len(order))
    metrics = [
        ("first_check_target_is_wolf", "First check"),
        ("found_wolf_by_check_2", "By check 2"),
        ("found_wolf_by_check_3", "By check 3"),
    ]
    for idx, (metric, label) in enumerate(metrics):
        values = [
            early_df[
                (early_df["strategy"] == strategy)
                & (early_df["metric"] == metric)
            ]["value"].iloc[0]
            for strategy in order
        ]
        ax.bar(x + (idx - 1) * width, values, width=width, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels([strategy_labels[s] for s in order], rotation=20)
    ax.set_ylabel("Discovery rate")
    ax.set_title("Early wolf discovery by strategy")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "early_discovery_by_strategy.svg")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    survival = [
        desc_df[desc_df.strategy == strategy]["seer_survival_rate"].iloc[0]
        for strategy in order
    ]
    ax.bar([strategy_labels[s] for s in order], survival, color=[colors[s] for s in order])
    ax.set_ylim(0.24, 0.34)
    ax.set_ylabel("Seer survival rate")
    ax.set_title("Seer survival by strategy")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "seer_survival_by_strategy.svg")
    plt.close(fig)

    layout_df = pd.DataFrame([
        row for row in layout_rows
        if row["row_type"] == "clockwise_counterclockwise_by_layout"
    ])
    layout_order = sorted(layout_df["variable"].unique())
    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.35
    x = np.arange(len(layout_order))
    for idx, strategy in enumerate(["physical_clockwise", "physical_counterclockwise"]):
        values = [
            layout_df[
                (layout_df["variable"] == layout)
                & (layout_df["strategy"] == strategy)
            ]["village_win_rate"].iloc[0]
            for layout in layout_order
        ]
        ax.bar(
            x + (idx - 0.5) * width,
            values,
            width=width,
            label=strategy_labels[strategy],
            color=colors[strategy],
        )
    ax.set_xticks(x)
    ax.set_xticklabels([label.replace("_", " ") for label in layout_order], rotation=15)
    ax.set_ylabel("Village win rate")
    ax.set_title("Clockwise vs counterclockwise by wolf-layout condition")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "clockwise_vs_counterclockwise_by_wolf_layout.svg")
    plt.close(fig)

    paired_df = pd.DataFrame([
        row for row in paired_rows
        if row["check_type"] == "paired_contrast"
    ])
    selected = paired_df[
        paired_df["metric"].isin([
            "physical_clockwise vs physical_counterclockwise",
            "physical_clockwise vs random_neutral",
            "physical_clockwise vs alternate_physical_sides",
            "alternate_physical_sides vs random_neutral",
        ])
    ]
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = selected["metric"].str.replace("_", " ", regex=False)
    ax.barh(labels, selected["paired_village_win_difference"], color="#7a9a45")
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_xlabel("Paired village-win difference")
    ax.set_title("Paired configuration outcome comparison")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "paired_configuration_outcome_comparison.svg")
    plt.close(fig)


def write_residual_validity_assessment():
    audit_text = AUDIT_PATH.read_text()
    with RESIDUAL_VALIDITY_PATH.open("w") as file:
        file.write("# Residual Validity Assessment\n\n")
        file.write("## Source Reviewed\n\n")
        file.write(
            "- `results/seat_order_neutral/seat_order_neutral_implementation_audit.md`\n"
        )
        file.write(
            "- Prior symmetry audit and structured-search analysis reports were "
            "used as background context.\n\n"
        )
        file.write("## Assessment\n\n")
        file.write(
            "The neutral engine successfully removes the displayed-label paths "
            "identified in the prior audit for this experiment: lower displayed "
            "IDs no longer decide exact ties, speech/vote iteration follows a "
            "neutral actor order, speech RNG uses actor_uid-based substreams, "
            "and role assignment is fixed in physical-seat terms before labels "
            "are mapped.\n\n"
        )
        file.write(
            "The strongest validation evidence is deterministic equivalence: "
            "normal, mirrored, and rotated label conditions produce identical "
            "physical check sequences, winners, total rounds, seer survival, "
            "and final physical alive sets in all matched sets. This is stronger "
            "than a non-significant label effect because no physical divergence "
            "is observed.\n\n"
        )
        file.write(
            "Residual limitations remain. The narrow no-strategy control checks "
            "engine equivalence under simplified conditions, but there is not "
            "yet a full externally supplied-action replay harness. Therefore, "
            "the analysis can rule out displayed-label artifacts in the neutral "
            "experiment, but it cannot fully rule out a deeper physical "
            "clockwise/counterclockwise asymmetry embedded in action resolution, "
            "strategy implementation, or circular-seat representation.\n\n"
        )
        file.write(
            "The physical direction strategies themselves appear symmetric in "
            "implementation: clockwise and counterclockwise use matching "
            "distance functions and differ only in direction. However, the game "
            "state and strategy path can still interact with physical wolf "
            "placement. Any clockwise advantage should therefore be interpreted "
            "as a possible physical path-layout effect until a supplied-action "
            "replay or randomized physical-orientation experiment closes this "
            "remaining validity gap.\n\n"
        )
        file.write("## Audit Excerpt\n\n")
        file.write("```text\n")
        file.write(audit_text[:2500])
        file.write("\n```\n")


def write_analysis_report(
    validation_rows,
    descriptive_rows,
    raw_diffs,
    omnibus_rows,
    primary_rows,
    paired_rows,
    label_rows,
    early_rows,
    mechanism_rows,
    layout_rows,
    seed_rows,
    effect_rows,
):
    desc = {row["strategy"]: row for row in descriptive_rows}
    primary = {row["contrast"]: row for row in primary_rows}
    paired = {
        row["metric"]: row
        for row in paired_rows
        if row.get("check_type") == "paired_contrast"
    }
    validation_ok = all(row["passed"] for row in validation_rows)
    label_identical = all(row["identical_rate"] == 1.0 for row in label_rows)

    with ANALYSIS_REPORT_PATH.open("w") as file:
        file.write("# Seat-Order-Neutral Directional Effects Analysis\n\n")
        file.write("## Technical Summary\n\n")
        file.write(
            "This analysis uses the seat-order-neutral game-level dataset and "
            "collapses the normal, mirrored, and rotated label rows to one "
            "independent row per strategy/base configuration before estimating "
            "strategy effects. The source file has 30,000 completed games, but "
            "the effective independent sample for strategy inference is 10,000 "
            "strategy/base rows, with 2,500 shared physical configurations "
            "available for paired cross-strategy comparisons.\n\n"
        )
        file.write(
            f"Validation status: {'passed' if validation_ok else 'failed'}. "
            f"Displayed-label invariance is "
            f"{'exactly observed' if label_identical else 'not exact'} across "
            "normal, mirrored, and rotated labels.\n\n"
        )
        file.write(
            "Descriptively, `physical_clockwise` has a village win rate of "
            f"{pct(desc['physical_clockwise']['village_win_rate'])}, above "
            f"`physical_counterclockwise` at "
            f"{pct(desc['physical_counterclockwise']['village_win_rate'])} "
            "and `random_neutral` at "
            f"{pct(desc['random_neutral']['village_win_rate'])}. "
            "The seed-adjusted model and paired analysis show positive "
            "clockwise differences over counterclockwise and random, but "
            "these differences remain statistically uncertain after multiple "
            "comparison correction and do not support clockwise as better "
            "than alternate physical sides.\n\n"
        )

        file.write("## Data Validation and Label Invariance\n\n")
        file.write(
            "| validation check | observed | expected | passed |\n"
            "|---|---:|---:|---|\n"
        )
        for row in validation_rows:
            file.write(
                f"| {row['check']} | {row['observed']} | "
                f"{row['expected']} | {row['passed']} |\n"
            )
        file.write("\n")
        file.write(
            "The three label conditions are deterministic physical duplicates "
            "for the outcome and mechanism fields tested. This should be read "
            "as computational equivalence, not merely failure to reject a label "
            "effect.\n\n"
        )

        file.write("## Descriptive Statistics\n\n")
        file.write(
            "| strategy | independent games | village win | 95% CI | wolf win | first check wolf | found by check 2 | found by check 3 | no wolf found | mean checks to first wolf | seer survival | mean rounds |\n"
        )
        file.write(
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )
        for row in descriptive_rows:
            file.write(
                f"| {row['strategy']} | "
                f"{row['n_independent_base_games']} | "
                f"{pct(row['village_win_rate'])} | "
                f"{pct(row['village_win_ci_low'])}-"
                f"{pct(row['village_win_ci_high'])} | "
                f"{pct(row['wolf_win_rate'])} | "
                f"{pct(row['first_check_wolf_rate'])} | "
                f"{pct(row['found_wolf_by_check_2_rate'])} | "
                f"{pct(row['found_wolf_by_check_3_rate'])} | "
                f"{pct(row['no_wolf_found_rate'])} | "
                f"{num(row['mean_checks_until_first_wolf'], 2)} | "
                f"{pct(row['seer_survival_rate'])} | "
                f"{num(row['mean_total_rounds'], 2)} |\n"
            )
        file.write("\n")

        file.write("## Primary Strategy Model\n\n")
        omni = omnibus_rows[0]
        file.write(
            "The seed-adjusted logistic model `village_win ~ strategy + seed` "
            f"finds an overall strategy effect "
            f"(LR={num(omni['lr_statistic'], 2)}, df={omni['df']}, "
            f"p={num(omni['p_value'], 4)}).\n\n"
        )
        file.write(
            "| contrast | adjusted OR | 95% CI | adjusted probability difference | raw p | Holm p | interpretation |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|---|\n")
        for row in primary_rows:
            file.write(
                f"| {row['contrast']} | "
                f"{odds_ratio_text(row['odds_ratio'])} | "
                f"{odds_ratio_text(row['odds_ratio_ci_low'])}-"
                f"{odds_ratio_text(row['odds_ratio_ci_high'])} | "
                f"{pp(row['adjusted_probability_difference'])} | "
                f"{num(row['p_value'], 4)} | "
                f"{num(row['holm_p_value'], 4)} | "
                f"{row['interpretation']} |\n"
            )
        file.write("\n")

        file.write("## Paired Configuration Analysis\n\n")
        file.write(
            "Cross-strategy pairing is valid: the same `seed` and "
            "`base_game_index` reuse the same physical seer seat and physical "
            "wolf seats across all four strategies. The paired analysis uses "
            "2,500 shared physical configurations and is preferred for "
            "strategy comparisons because it removes role-layout noise.\n\n"
        )
        file.write(
            "| contrast | paired diff | 95% CI | discordant A win/B win | paired OR | raw p | Holm p | interpretation |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|---:|---|\n")
        for row in paired.values():
            file.write(
                f"| {row['metric']} | "
                f"{pp(row['paired_village_win_difference'])} | "
                f"{pp(row['paired_difference_ci_low'])}-"
                f"{pp(row['paired_difference_ci_high'])} | "
                f"{row['a_win_b_loss']}/{row['a_loss_b_win']} | "
                f"{odds_ratio_text(row['paired_odds_ratio'])} | "
                f"{num(row['p_value'], 4)} | "
                f"{num(row['holm_p_value'], 4)} | "
                f"{row['interpretation']} |\n"
            )
        file.write("\n")

        file.write("## Early Discovery and Mechanisms\n\n")
        file.write(
            "`physical_clockwise` wins more often than `random_neutral` even "
            "though its first-check wolf rate is lower "
            f"({pct(desc['physical_clockwise']['first_check_wolf_rate'])} vs "
            f"{pct(desc['random_neutral']['first_check_wolf_rate'])}). "
            "The gap is not explained by first-check success alone. Clockwise "
            "has slightly better discovery by check 3 and a slightly lower "
            "no-wolf-found rate than random, but the mechanism models show the "
            "clockwise coefficient remains materially positive after adding "
            "early-discovery, timing, survival, and game-length diagnostics. "
            "These variables are intermediate/post-treatment, so the models "
            "are diagnostic rather than causal mediation.\n\n"
        )
        file.write(
            "| model | converged | cw vs random OR | cw vs random p | cw vs counter OR | cw vs counter p | cw-random adjusted pp | note |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|---:|---|\n")
        for row in mechanism_rows:
            file.write(
                f"| {row['model']} | {row['converged']} | "
                f"{odds_ratio_text(row['clockwise_vs_random_or'])} | "
                f"{num(row['clockwise_vs_random_p'], 4)} | "
                f"{odds_ratio_text(row['clockwise_vs_counterclockwise_or'])} | "
                f"{num(row['clockwise_vs_counterclockwise_p'], 4)} | "
                f"{num(row['clockwise_minus_random_adjusted_pp'], 2)} | "
                f"{row['note']} |\n"
            )
        file.write("\n")

        file.write("## Physical Layout Interactions\n\n")
        interaction_rows = [
            row for row in layout_rows
            if row["row_type"] == "interaction_lr_test"
        ]
        file.write(
            "| variable | LR statistic | df | p-value | interpretation |\n"
            "|---|---:|---:|---:|---|\n"
        )
        for row in interaction_rows:
            file.write(
                f"| {row['variable']} | {num(row['lr_statistic'], 2)} | "
                f"{row['df']} | {num(row['p_value'], 4)} | "
                f"{row['interpretation']} |\n"
            )
        file.write(
            "\nThe interaction checks suggest that strategy performance is "
            "partly conditional on physical wolf layout and local wolf "
            "density. The seer-seat interaction itself is not strong in this "
            "diagnostic model. Overall, this supports a path-layout "
            "interpretation over a pure displayed-label artifact.\n\n"
        )

        file.write("## Seed Robustness\n\n")
        seed_rate_rows = [
            row for row in seed_rows
            if row["row_type"] == "seed_strategy_rate"
        ]
        file.write(
            "| seed | physical_clockwise | physical_counterclockwise | alternate_physical_sides | random_neutral |\n"
            "|---:|---:|---:|---:|---:|\n"
        )
        for seed in SEEDS:
            seed_map = {
                row["strategy"]: row
                for row in seed_rate_rows
                if row["seed"] == seed
            }
            file.write(
                f"| {seed} | "
                f"{pct(seed_map['physical_clockwise']['village_win_rate'])} | "
                f"{pct(seed_map['physical_counterclockwise']['village_win_rate'])} | "
                f"{pct(seed_map['alternate_physical_sides']['village_win_rate'])} | "
                f"{pct(seed_map['random_neutral']['village_win_rate'])} |\n"
            )
        file.write(
            "\nOnly five seeds are available, so the robustness section relies "
            "on seed fixed effects, seed-stratified rates, leave-one-seed-out "
            "models, and paired configuration tests rather than cluster-robust "
            "standard errors.\n\n"
        )

        file.write("## Answers to Required Questions\n\n")
        answers = [
            (
                "Is physical_clockwise statistically better than physical_counterclockwise?",
                primary[
                    "physical_clockwise vs physical_counterclockwise"
                ]["interpretation"],
                (
                    f"Seed-adjusted Holm p="
                    f"{num(primary['physical_clockwise vs physical_counterclockwise']['holm_p_value'], 4)}; "
                    f"paired Holm p="
                    f"{num(paired['physical_clockwise vs physical_counterclockwise']['holm_p_value'], 4)}."
                ),
            ),
            (
                "Is physical_clockwise statistically better than random_neutral?",
                primary["physical_clockwise vs random_neutral"]["interpretation"],
                (
                    f"Seed-adjusted Holm p="
                    f"{num(primary['physical_clockwise vs random_neutral']['holm_p_value'], 4)}; "
                    f"paired Holm p="
                    f"{num(paired['physical_clockwise vs random_neutral']['holm_p_value'], 4)}."
                ),
            ),
            (
                "Is alternate_physical_sides statistically better than random_neutral?",
                primary[
                    "alternate_physical_sides vs random_neutral"
                ]["interpretation"],
                (
                    f"Seed-adjusted Holm p="
                    f"{num(primary['alternate_physical_sides vs random_neutral']['holm_p_value'], 4)}; "
                    f"paired Holm p="
                    f"{num(paired['alternate_physical_sides vs random_neutral']['holm_p_value'], 4)}."
                ),
            ),
            (
                "Did displayed-label condition have exactly zero physical effect?",
                "statistically supported as deterministic equivalence",
                "All tested physical trajectories and outcomes match exactly across label conditions.",
            ),
            (
                "Is the clockwise advantage stable across seeds?",
                "practically meaningful but statistically uncertain",
                "Clockwise beats counterclockwise in most seed-level cuts, but five seeds are too few for a final robustness claim by seed alone.",
            ),
            (
                "Does the clockwise advantage survive paired configuration analysis?",
                paired[
                    "physical_clockwise vs physical_counterclockwise"
                ]["interpretation"],
                (
                    f"Paired difference="
                    f"{pp(paired['physical_clockwise vs physical_counterclockwise']['paired_village_win_difference'])}."
                ),
            ),
            (
                "Why does clockwise win more despite a lower first-check wolf rate than random?",
                "weak/inconclusive mechanism",
                "The gain is not a first-check story; later discovery and path composition appear more relevant, but the staged models are diagnostic only.",
            ),
            (
                "Is the advantage explained by later discovery or seer survival?",
                "weak/inconclusive",
                "Adjustment does not eliminate the clockwise coefficient, so no single measured downstream mechanism fully explains it.",
            ),
            (
                "Does the advantage depend on where wolves are physically located?",
                "practically meaningful but statistically uncertain",
                "Layout interaction checks show dependence on wolf placement and local wolf density, consistent with path-layout alignment.",
            ),
            (
                "Is this a real directional search effect or favorable path alignment?",
                "weak/inconclusive",
                "The result is label-invariant, but path-layout alignment and residual physical-engine asymmetry remain possible explanations.",
            ),
            (
                "Are residual engine asymmetries still possible?",
                "yes",
                "A full supplied-action replay harness was not implemented, so the final physical-direction claim remains limited.",
            ),
            (
                "Is the structured-search chapter ready to close?",
                "not fully",
                "Displayed-label artifacts are controlled, but physical direction needs a stronger engine-symmetry validation.",
            ),
            (
                "What exact experiment should come next?",
                "next step",
                "Build a full supplied-action replay or randomized physical-orientation experiment that swaps clockwise/counterclockwise geometry while preserving action traces.",
            ),
        ]
        for index, (question, label, evidence) in enumerate(answers, start=1):
            file.write(
                f"{index}. **{question}** {label}. {evidence}\n"
            )

        file.write("\n## Output Files\n\n")
        for path in [
            VALIDATION_SUMMARY_PATH,
            DESCRIPTIVE_PATH,
            OMNIBUS_PATH,
            PRIMARY_CONTRASTS_PATH,
            PAIRED_ANALYSIS_PATH,
            LABEL_INVARIANCE_PATH,
            EARLY_DISCOVERY_PATH,
            MECHANISM_MODELS_PATH,
            PHYSICAL_LAYOUT_PATH,
            SEED_ROBUSTNESS_PATH,
            EFFECT_SIZE_PATH,
            RESIDUAL_VALIDITY_PATH,
        ]:
            file.write(f"- `{path}`\n")


def main():
    ensure_output_dir()
    raw, normal = load_and_prepare_data()
    validation_rows, _ = validate_data(raw, normal)
    descriptive_rows = make_descriptive_statistics(normal)
    raw_diffs = raw_strategy_differences(descriptive_rows)
    primary_model, omnibus_rows, primary_rows, _ = make_primary_models(normal)
    paired_rows, paired_configs = make_paired_strategy_analysis(normal)
    label_rows = make_label_invariance_validation(raw)
    early_rows = make_early_discovery_analysis(normal)
    mechanism_rows = make_mechanism_models(normal)
    layout_rows = make_physical_layout_interactions(normal)
    seed_rows = make_seed_robustness(normal)
    effect_rows = make_effect_size_precision(primary_rows, paired_rows)
    make_figures(
        descriptive_rows,
        primary_rows,
        seed_rows,
        early_rows,
        layout_rows,
        paired_rows,
    )
    write_residual_validity_assessment()
    write_analysis_report(
        validation_rows,
        descriptive_rows,
        raw_diffs,
        omnibus_rows,
        primary_rows,
        paired_rows,
        label_rows,
        early_rows,
        mechanism_rows,
        layout_rows,
        seed_rows,
        effect_rows,
    )
    print("Seat-order-neutral analysis complete.")
    print(f"Raw rows: {len(raw)}")
    print(f"Collapsed independent rows: {len(normal)}")
    print(f"Paired physical configurations: {paired_configs['config_id'].nunique()}")
    print(f"Wrote {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
