import csv
import math
import os
from itertools import combinations
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path("results/data_analysis/structured_seer_search/mpl_cache")),
)

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path("results/structured_seer_search")
OUTPUT_DIR = Path("results/data_analysis/structured_seer_search")
RAW_PATH = BASE_DIR / "structured_seer_search_game_level_raw.csv"
STRATEGY_SUMMARY_PATH = BASE_DIR / "structured_seer_search_strategy_summary.csv"
SEED_SUMMARY_PATH = BASE_DIR / "structured_seer_search_seed_summary.csv"
SCHEMA_PATH = BASE_DIR / "structured_seer_search_schema.md"
EXPERIMENT_REPORT_PATH = (
    BASE_DIR / "structured_seer_search_experiment_report.md"
)

STRATEGIES = [
    "random",
    "default",
    "edge_first",
    "inner_first",
    "highest_p_wolf",
    "highest_suspicion",
    "left_to_right",
    "right_to_left",
    "alternate_sides",
    "nearest_first",
    "farthest_first",
    "coverage_balanced",
    "hybrid_suspicion_position",
    "information_gain_proxy",
]

KEY_CONTRASTS = [
    ("alternate_sides", "random"),
    ("alternate_sides", "right_to_left"),
    ("alternate_sides", "inner_first"),
    ("alternate_sides", "edge_first"),
    ("right_to_left", "random"),
    ("information_gain_proxy", "random"),
    ("highest_p_wolf", "random"),
    ("highest_suspicion", "random"),
]

EARLY_OUTCOMES = [
    "first_check_wolf",
    "found_wolf_by_check_2",
    "found_wolf_by_check_3",
]

METRIC_COLUMNS = [
    "village_win",
    "wolf_win",
    "first_check_wolf",
    "found_wolf_by_check_2",
    "found_wolf_by_check_3",
    "seer_found_any_wolf",
    "seer_found_wolf_count",
    "seer_survived_to_game_end",
    "total_seer_checks",
    "search_path_coverage_score",
    "unique_seat_types_checked",
    "unique_sides_checked",
    "mean_pairwise_distance_between_checked_targets",
]

EXPLOITATION_STRATEGIES = {
    "highest_p_wolf",
    "highest_suspicion",
    "hybrid_suspicion_position",
}

DIVERSIFICATION_STRATEGIES = {
    "alternate_sides",
    "right_to_left",
    "farthest_first",
    "coverage_balanced",
    "information_gain_proxy",
}


def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_sf(x):
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def norm_p_value(z):
    return 2.0 * normal_sf(abs(z))


def gammainc_lower_reg(a, x, eps=1e-14, max_iter=1000):
    if x <= 0:
        return 0.0

    ap = a
    summation = 1.0 / a
    delta = summation

    for _ in range(max_iter):
        ap += 1.0
        delta *= x / ap
        summation += delta

        if abs(delta) < abs(summation) * eps:
            break

    return summation * math.exp(-x + a * math.log(x) - math.lgamma(a))


def gammainc_upper_reg(a, x, eps=1e-14, max_iter=1000):
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d

    for i in range(1, max_iter + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b

        if abs(d) < tiny:
            d = tiny

        c = b + an / c

        if abs(c) < tiny:
            c = tiny

        d = 1.0 / d
        delta = d * c
        h *= delta

        if abs(delta - 1.0) < eps:
            break

    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_sf(value, df):
    if value <= 0:
        return 1.0

    a = df / 2.0
    x = value / 2.0

    if x < a + 1.0:
        return max(0.0, min(1.0, 1.0 - gammainc_lower_reg(a, x)))

    return max(0.0, min(1.0, gammainc_upper_reg(a, x)))


def holm_adjust(p_values):
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [None] * len(p_values)
    running_max = 0.0
    total = len(p_values)

    for rank, (index, p_value) in enumerate(indexed, start=1):
        value = min(1.0, (total - rank + 1) * p_value)
        running_max = max(running_max, value)
        adjusted[index] = running_max

    return adjusted


def wilson_ci(successes, n, z=1.96):
    if n == 0:
        return None, None

    proportion = successes / n
    denominator = 1.0 + z * z / n
    center = (proportion + z * z / (2.0 * n)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / n
            + z * z / (4.0 * n * n)
        )
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def mean_ci(values, z=1.96):
    clean_values = [value for value in values if not pd.isna(value)]
    n = len(clean_values)

    if n == 0:
        return None, None, None

    mean_value = float(np.mean(clean_values))

    if n == 1:
        return mean_value, mean_value, mean_value

    se = float(np.std(clean_values, ddof=1) / math.sqrt(n))
    return mean_value, mean_value - z * se, mean_value + z * se


def sigmoid(values):
    values = np.clip(values, -35, 35)
    return 1.0 / (1.0 + np.exp(-values))


def build_design(df, predictors):
    columns = []
    matrices = []
    intercept = np.ones((len(df), 1))
    matrices.append(intercept)
    columns.append("Intercept")

    for predictor in predictors:
        kind = predictor["kind"]

        if kind == "num":
            name = predictor["name"]
            matrices.append(df[[name]].to_numpy(dtype=float))
            columns.append(name)
        elif kind == "cat":
            name = predictor["name"]
            ref = str(predictor["ref"])
            categories = [str(category) for category in predictor["levels"]]

            for category in categories:
                if category == ref:
                    continue

                column_name = f"{name}[{category}]"
                column_values = (
                    df[name].astype(str).to_numpy() == category
                ).astype(float)
                matrices.append(column_values.reshape(-1, 1))
                columns.append(column_name)
        elif kind == "interaction":
            left = predictor["left"]
            right = predictor["right"]
            right_kind = predictor.get("right_kind", "num")
            left_ref = str(predictor["left_ref"])
            left_levels = [str(level) for level in predictor["left_levels"]]

            for left_level in left_levels:
                if left_level == left_ref:
                    continue

                left_values = (
                    df[left].astype(str).to_numpy() == left_level
                ).astype(float)

                if right_kind == "num":
                    values = left_values * df[right].to_numpy(dtype=float)
                    matrices.append(values.reshape(-1, 1))
                    columns.append(f"{left}[{left_level}]:{right}")
                else:
                    right_ref = str(predictor["right_ref"])
                    right_levels = [
                        str(level) for level in predictor["right_levels"]
                    ]

                    for right_level in right_levels:
                        if right_level == right_ref:
                            continue

                        right_values = (
                            df[right].astype(str).to_numpy() == right_level
                        ).astype(float)
                        values = left_values * right_values
                        matrices.append(values.reshape(-1, 1))
                        columns.append(
                            f"{left}[{left_level}]:{right}[{right_level}]"
                        )
        else:
            raise ValueError(f"Unknown predictor kind: {kind}")

    return np.hstack(matrices), columns


def fit_logit(df, outcome, predictors, max_iter=80, tolerance=1e-8):
    y = df[outcome].to_numpy(dtype=float)
    x, columns = build_design(df, predictors)
    beta = np.zeros(x.shape[1])

    for _ in range(max_iter):
        eta = x @ beta
        p = sigmoid(eta)
        weights = np.clip(p * (1.0 - p), 1e-8, None)
        gradient = x.T @ (y - p)
        hessian = x.T @ (weights[:, None] * x)

        try:
            delta = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            delta = np.linalg.pinv(hessian) @ gradient

        beta = beta + delta

        if float(np.max(np.abs(delta))) < tolerance:
            break

    eta = x @ beta
    p = sigmoid(eta)
    weights = np.clip(p * (1.0 - p), 1e-8, None)
    hessian = x.T @ (weights[:, None] * x)
    covariance = np.linalg.pinv(hessian)
    log_likelihood = float(
        np.sum(y * np.log(np.clip(p, 1e-12, 1.0))
               + (1.0 - y) * np.log(np.clip(1.0 - p, 1e-12, 1.0)))
    )

    return {
        "outcome": outcome,
        "predictors": predictors,
        "columns": columns,
        "beta": beta,
        "covariance": covariance,
        "log_likelihood": log_likelihood,
        "n": len(df),
        "k": len(beta),
    }


def coefficient_index(model, name):
    try:
        return model["columns"].index(name)
    except ValueError:
        return None


def strategy_contrast_vector(model, numerator, denominator):
    vector = np.zeros(len(model["columns"]))

    for sign, strategy in [(1.0, numerator), (-1.0, denominator)]:
        if strategy == "random":
            continue

        index = coefficient_index(model, f"strategy[{strategy}]")
        if index is not None:
            vector[index] += sign

    return vector


def contrast_row(model, numerator, denominator, outcome, family):
    vector = strategy_contrast_vector(model, numerator, denominator)
    log_or = float(vector @ model["beta"])
    variance = float(vector @ model["covariance"] @ vector)
    se = math.sqrt(max(variance, 0.0))
    z_value = log_or / se if se > 0 else 0.0
    p_value = norm_p_value(z_value) if se > 0 else 1.0
    lower = log_or - 1.96 * se
    upper = log_or + 1.96 * se

    return {
        "analysis_family": family,
        "outcome": outcome,
        "contrast": f"{numerator} vs {denominator}",
        "numerator": numerator,
        "denominator": denominator,
        "log_odds_ratio": log_or,
        "odds_ratio": math.exp(log_or),
        "or_ci_low": math.exp(lower),
        "or_ci_high": math.exp(upper),
        "z_value": z_value,
        "p_value": p_value,
    }


def model_lr_test(full_model, reduced_model, label):
    lr_stat = 2.0 * (
        full_model["log_likelihood"] - reduced_model["log_likelihood"]
    )
    df = full_model["k"] - reduced_model["k"]

    return {
        "test": label,
        "outcome": full_model["outcome"],
        "lr_statistic": lr_stat,
        "df": df,
        "p_value": chi2_sf(lr_stat, df),
        "full_log_likelihood": full_model["log_likelihood"],
        "reduced_log_likelihood": reduced_model["log_likelihood"],
        "n": full_model["n"],
    }


def predictors_strategy_seed():
    return [
        {
            "kind": "cat",
            "name": "strategy",
            "levels": STRATEGIES,
            "ref": "random",
        },
        {
            "kind": "cat",
            "name": "seed",
            "levels": ["42", "43", "44", "45", "46"],
            "ref": "42",
        },
    ]


def predictors_seed_only():
    return [
        {
            "kind": "cat",
            "name": "seed",
            "levels": ["42", "43", "44", "45", "46"],
            "ref": "42",
        },
    ]


def prediction_row(strategy, seed, predictors, columns):
    row = {"strategy": strategy, "seed": str(seed)}

    for predictor in predictors:
        if predictor["kind"] == "num":
            row[predictor["name"]] = 0.0

    row_df = pd.DataFrame([row])
    design, _ = build_design(row_df, predictors)
    aligned = np.zeros(len(columns))

    _, row_columns = build_design(row_df, predictors)
    row_lookup = dict(zip(row_columns, design[0]))

    for index, column in enumerate(columns):
        aligned[index] = row_lookup.get(column, 0.0)

    return aligned


def adjusted_probability_rows(model, predictors):
    rows = []
    seeds = ["42", "43", "44", "45", "46"]

    for strategy in STRATEGIES:
        vectors = np.vstack([
            prediction_row(strategy, seed, predictors, model["columns"])
            for seed in seeds
        ])
        probabilities = sigmoid(vectors @ model["beta"])
        probability = float(np.mean(probabilities))
        gradient = np.mean(
            probabilities[:, None] * (1.0 - probabilities[:, None])
            * vectors,
            axis=0,
        )
        se = math.sqrt(
            max(float(gradient @ model["covariance"] @ gradient), 0.0)
        )
        rows.append({
            "analysis_family": "adjusted_probability",
            "outcome": model["outcome"],
            "strategy": strategy,
            "adjusted_probability": probability,
            "ci_low": max(0.0, probability - 1.96 * se),
            "ci_high": min(1.0, probability + 1.96 * se),
        })

    return rows


def prepare_data():
    df = pd.read_csv(RAW_PATH)

    for column in [
        "seed",
        "strategy",
        "seer_side",
        "seer_seat_type",
        "winner",
    ]:
        df[column] = df[column].astype(str)

    numeric_columns = [
        "village_win",
        "wolf_win",
        "total_rounds",
        "seer_seat",
        "wolves_on_edge",
        "wolves_on_inner",
        "wolves_left_side",
        "wolves_right_side",
        "first_check_target",
        "first_check_target_is_wolf",
        "first_check_target_distance_from_seer",
        "total_seer_checks",
        "first_check_wolf",
        "found_wolf_by_check_1",
        "found_wolf_by_check_2",
        "found_wolf_by_check_3",
        "checks_until_first_wolf",
        "seer_found_any_wolf",
        "seer_found_wolf_count",
        "unique_seat_types_checked",
        "unique_sides_checked",
        "mean_pairwise_distance_between_checked_targets",
        "search_path_coverage_score",
        "seer_survived_to_game_end",
        "seer_death_round",
        "final_alive_players",
        "final_alive_wolves",
        "final_alive_villagers",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["seer_seat"] = df["seer_seat"].astype("Int64").astype(str)
    df["seed"] = df["seed"].astype(str)
    return df


def descriptive_statistics(df):
    rows = []

    for strategy in STRATEGIES:
        subset = df[df["strategy"] == strategy]
        n = len(subset)
        row = {"strategy": strategy, "num_games": n}

        for column in METRIC_COLUMNS:
            values = subset[column].dropna()

            if column in {
                "village_win",
                "wolf_win",
                "first_check_wolf",
                "found_wolf_by_check_2",
                "found_wolf_by_check_3",
                "seer_found_any_wolf",
                "seer_survived_to_game_end",
            }:
                successes = int(values.sum())
                lower, upper = wilson_ci(successes, len(values))
                row[f"{column}_mean"] = successes / len(values)
                row[f"{column}_ci_low"] = lower
                row[f"{column}_ci_high"] = upper
            else:
                mean_value, lower, upper = mean_ci(values)
                row[f"{column}_mean"] = mean_value
                row[f"{column}_ci_low"] = lower
                row[f"{column}_ci_high"] = upper

        checks_until = subset["checks_until_first_wolf"].dropna()
        mean_value, lower, upper = mean_ci(checks_until)
        row["checks_until_first_wolf_mean"] = mean_value
        row["checks_until_first_wolf_ci_low"] = lower
        row["checks_until_first_wolf_ci_high"] = upper
        row["no_wolf_found_rate_mean"] = (
            1.0 - subset["seer_found_any_wolf"].mean()
        )
        no_wolf_lower, no_wolf_upper = wilson_ci(
            int((subset["seer_found_any_wolf"] == 0).sum()),
            n,
        )
        row["no_wolf_found_rate_ci_low"] = no_wolf_lower
        row["no_wolf_found_rate_ci_high"] = no_wolf_upper
        rows.append(row)

    return pd.DataFrame(rows)


def strategy_models(df):
    predictors = predictors_strategy_seed()
    seed_predictors = predictors_seed_only()
    full = fit_logit(df, "village_win", predictors)
    reduced = fit_logit(df, "village_win", seed_predictors)
    omnibus = pd.DataFrame([
        model_lr_test(full, reduced, "strategy_omnibus_seed_adjusted")
    ])

    contrasts = [
        contrast_row(
            full,
            numerator,
            denominator,
            "village_win",
            "village_win_pairwise",
        )
        for numerator, denominator in KEY_CONTRASTS
    ]
    adjusted = holm_adjust([row["p_value"] for row in contrasts])

    for row, adjusted_p in zip(contrasts, adjusted):
        row["p_value_holm"] = adjusted_p

    adjusted_probabilities = pd.DataFrame(
        adjusted_probability_rows(full, predictors)
    )
    return full, omnibus, pd.DataFrame(contrasts), adjusted_probabilities


def early_discovery_models(df):
    rows = []
    omnibus_rows = []

    for outcome in EARLY_OUTCOMES:
        predictors = predictors_strategy_seed()
        full = fit_logit(df, outcome, predictors)
        reduced = fit_logit(df, outcome, predictors_seed_only())
        omnibus_rows.append(
            model_lr_test(full, reduced, "strategy_omnibus_seed_adjusted")
        )

        outcome_rows = [
            contrast_row(
                full,
                numerator,
                denominator,
                outcome,
                "early_discovery_pairwise",
            )
            for numerator, denominator in KEY_CONTRASTS
        ]
        adjusted = holm_adjust([row["p_value"] for row in outcome_rows])

        for row, adjusted_p in zip(outcome_rows, adjusted):
            row["p_value_holm"] = adjusted_p

        rows.extend(outcome_rows)

    return pd.DataFrame(omnibus_rows), pd.DataFrame(rows)


def mechanism_models(df):
    model_specs = [
        (
            "model_1_strategy_seed",
            predictors_strategy_seed(),
            "Pre-treatment strategy and seed fixed effects.",
        ),
        (
            "model_2_add_first_check_wolf",
            predictors_strategy_seed()
            + [{"kind": "num", "name": "first_check_wolf"}],
            "Adds early discovery indicator; intermediate variable.",
        ),
        (
            "model_3_add_found_wolf_by_check_2",
            predictors_strategy_seed()
            + [{"kind": "num", "name": "found_wolf_by_check_2"}],
            "Adds discovery by check 2; intermediate variable.",
        ),
        (
            "model_4_add_seer_survival",
            predictors_strategy_seed()
            + [{"kind": "num", "name": "seer_survived_to_game_end"}],
            "Adds seer survival; post-treatment lifecycle variable.",
        ),
        (
            "model_5_add_coverage_diversity",
            predictors_strategy_seed()
            + [
                {"kind": "num", "name": "search_path_coverage_score"},
                {"kind": "num", "name": "unique_seat_types_checked"},
                {"kind": "num", "name": "unique_sides_checked"},
                {
                    "kind": "num",
                    "name": "mean_pairwise_distance_between_checked_targets",
                },
            ],
            "Adds search coverage/diversity; post-treatment search path.",
        ),
        (
            "model_6_full_mechanism",
            predictors_strategy_seed()
            + [
                {"kind": "num", "name": "first_check_wolf"},
                {"kind": "num", "name": "found_wolf_by_check_2"},
                {"kind": "num", "name": "found_wolf_by_check_3"},
                {"kind": "num", "name": "seer_survived_to_game_end"},
                {"kind": "num", "name": "search_path_coverage_score"},
                {"kind": "num", "name": "unique_seat_types_checked"},
                {"kind": "num", "name": "unique_sides_checked"},
                {
                    "kind": "num",
                    "name": "mean_pairwise_distance_between_checked_targets",
                },
            ],
            "Adds early discovery, survival, coverage, and diversity.",
        ),
    ]
    fit_rows = []
    coef_rows = []
    models = {}

    for model_name, predictors, note in model_specs:
        model = fit_logit(df, "village_win", predictors)
        models[model_name] = model
        fit_rows.append({
            "model": model_name,
            "n": model["n"],
            "parameters": model["k"],
            "log_likelihood": model["log_likelihood"],
            "aic": 2 * model["k"] - 2 * model["log_likelihood"],
            "note": note,
        })

        for column, beta, se in zip(
            model["columns"],
            model["beta"],
            np.sqrt(np.diag(model["covariance"])),
        ):
            if column == "Intercept":
                continue

            z_value = beta / se if se > 0 else 0.0
            coef_rows.append({
                "model": model_name,
                "term": column,
                "coefficient": beta,
                "odds_ratio": math.exp(beta),
                "or_ci_low": math.exp(beta - 1.96 * se),
                "or_ci_high": math.exp(beta + 1.96 * se),
                "z_value": z_value,
                "p_value": norm_p_value(z_value) if se > 0 else 1.0,
                "term_type": (
                    "strategy"
                    if column.startswith("strategy[")
                    else "covariate"
                ),
                "reference": "random" if column.startswith("strategy[") else "",
            })

    base_lookup = {
        row["term"]: row["coefficient"]
        for row in coef_rows
        if row["model"] == "model_1_strategy_seed"
    }

    for row in coef_rows:
        if row["term_type"] != "strategy":
            row["attenuation_vs_model_1_pct"] = ""
            continue

        base = base_lookup.get(row["term"])

        if base in (None, 0):
            row["attenuation_vs_model_1_pct"] = ""
        else:
            row["attenuation_vs_model_1_pct"] = (
                100.0 * (base - row["coefficient"]) / base
            )

    return pd.DataFrame(fit_rows), pd.DataFrame(coef_rows), models


def exploitation_vs_diversification(df, descriptive):
    rows = []

    groups = {
        "behavioral_exploitation": EXPLOITATION_STRATEGIES,
        "structured_diversification": DIVERSIFICATION_STRATEGIES,
        "random_reference": {"random"},
    }

    for group_name, strategies in groups.items():
        subset = df[df["strategy"].isin(strategies)]
        rows.append({
            "row_type": "group",
            "group": group_name,
            "strategy": "",
            "num_games": len(subset),
            "village_win_rate": subset["village_win"].mean(),
            "first_check_wolf_rate": subset["first_check_wolf"].mean(),
            "found_wolf_by_check_2_rate": (
                subset["found_wolf_by_check_2"].mean()
            ),
            "found_wolf_by_check_3_rate": (
                subset["found_wolf_by_check_3"].mean()
            ),
            "no_wolf_found_rate": (
                1.0 - subset["seer_found_any_wolf"].mean()
            ),
            "mean_wolves_found_per_game": (
                subset["seer_found_wolf_count"].mean()
            ),
            "seer_survival_rate": (
                subset["seer_survived_to_game_end"].mean()
            ),
            "mean_total_checks": subset["total_seer_checks"].mean(),
            "coverage": subset["search_path_coverage_score"].mean(),
            "unique_seat_types": subset["unique_seat_types_checked"].mean(),
            "unique_sides": subset["unique_sides_checked"].mean(),
            "mean_pairwise_distance": (
                subset[
                    "mean_pairwise_distance_between_checked_targets"
                ].mean()
            ),
        })

    for strategy in sorted(EXPLOITATION_STRATEGIES | DIVERSIFICATION_STRATEGIES):
        subset = df[df["strategy"] == strategy]
        group = (
            "behavioral_exploitation"
            if strategy in EXPLOITATION_STRATEGIES
            else "structured_diversification"
        )
        rows.append({
            "row_type": "strategy",
            "group": group,
            "strategy": strategy,
            "num_games": len(subset),
            "village_win_rate": subset["village_win"].mean(),
            "first_check_wolf_rate": subset["first_check_wolf"].mean(),
            "found_wolf_by_check_2_rate": (
                subset["found_wolf_by_check_2"].mean()
            ),
            "found_wolf_by_check_3_rate": (
                subset["found_wolf_by_check_3"].mean()
            ),
            "no_wolf_found_rate": (
                1.0 - subset["seer_found_any_wolf"].mean()
            ),
            "mean_wolves_found_per_game": (
                subset["seer_found_wolf_count"].mean()
            ),
            "seer_survival_rate": (
                subset["seer_survived_to_game_end"].mean()
            ),
            "mean_total_checks": subset["total_seer_checks"].mean(),
            "coverage": subset["search_path_coverage_score"].mean(),
            "unique_seat_types": subset["unique_seat_types_checked"].mean(),
            "unique_sides": subset["unique_sides_checked"].mean(),
            "mean_pairwise_distance": (
                subset[
                    "mean_pairwise_distance_between_checked_targets"
                ].mean()
            ),
        })

    return pd.DataFrame(rows)


def fit_direction_interaction(df, modifier, modifier_kind):
    subset = df[df["strategy"].isin(["left_to_right", "right_to_left"])].copy()
    subset["strategy"] = subset["strategy"].astype(str)
    strategy_predictor = {
        "kind": "cat",
        "name": "strategy",
        "levels": ["left_to_right", "right_to_left"],
        "ref": "left_to_right",
    }
    seed_predictor = {
        "kind": "cat",
        "name": "seed",
        "levels": ["42", "43", "44", "45", "46"],
        "ref": "42",
    }

    if modifier_kind == "num":
        base_predictors = [
            strategy_predictor,
            seed_predictor,
            {"kind": "num", "name": modifier},
        ]
        interaction = {
            "kind": "interaction",
            "left": "strategy",
            "left_levels": ["left_to_right", "right_to_left"],
            "left_ref": "left_to_right",
            "right": modifier,
            "right_kind": "num",
        }
    else:
        levels = sorted(subset[modifier].astype(str).unique())
        base_predictors = [
            strategy_predictor,
            seed_predictor,
            {
                "kind": "cat",
                "name": modifier,
                "levels": levels,
                "ref": levels[0],
            },
        ]
        interaction = {
            "kind": "interaction",
            "left": "strategy",
            "left_levels": ["left_to_right", "right_to_left"],
            "left_ref": "left_to_right",
            "right": modifier,
            "right_kind": "cat",
            "right_levels": levels,
            "right_ref": levels[0],
        }

    reduced = fit_logit(subset, "village_win", base_predictors)
    full = fit_logit(subset, "village_win", base_predictors + [interaction])
    test = model_lr_test(full, reduced, f"strategy_x_{modifier}")
    test["modifier"] = modifier
    test["modifier_kind"] = modifier_kind
    return test


def direction_asymmetry(df):
    rows = []
    subset = df[df["strategy"].isin(["left_to_right", "right_to_left"])]

    for seed in sorted(subset["seed"].unique()):
        seed_subset = subset[subset["seed"] == seed]
        pivot = seed_subset.groupby("strategy")["village_win"].mean()
        rows.append({
            "analysis_type": "seed_difference",
            "modifier": "seed",
            "level": seed,
            "left_to_right_village_win_rate": pivot.get("left_to_right"),
            "right_to_left_village_win_rate": pivot.get("right_to_left"),
            "right_minus_left_pp": (
                100.0 * (
                    pivot.get("right_to_left")
                    - pivot.get("left_to_right")
                )
            ),
        })

    for modifier in ["seer_side", "seer_seat"]:
        for level in sorted(subset[modifier].astype(str).unique()):
            level_subset = subset[subset[modifier].astype(str) == level]
            pivot = level_subset.groupby("strategy")["village_win"].mean()
            rows.append({
                "analysis_type": "stratified_difference",
                "modifier": modifier,
                "level": level,
                "left_to_right_village_win_rate": pivot.get("left_to_right"),
                "right_to_left_village_win_rate": pivot.get("right_to_left"),
                "right_minus_left_pp": (
                    100.0 * (
                        pivot.get("right_to_left")
                        - pivot.get("left_to_right")
                    )
                ),
            })

    interaction_specs = [
        ("seer_seat", "cat"),
        ("seer_side", "cat"),
        ("wolves_on_edge", "num"),
        ("wolves_left_side", "num"),
        ("wolves_right_side", "num"),
    ]

    for modifier, modifier_kind in interaction_specs:
        row = fit_direction_interaction(df, modifier, modifier_kind)
        row["analysis_type"] = "interaction_lr_test"
        row["level"] = ""
        row["left_to_right_village_win_rate"] = ""
        row["right_to_left_village_win_rate"] = ""
        row["right_minus_left_pp"] = ""
        rows.append(row)

    return pd.DataFrame(rows)


def robustness_analysis(df):
    rows = []

    for seed in sorted(df["seed"].unique()):
        for strategy in STRATEGIES:
            subset = df[(df["seed"] == seed) & (df["strategy"] == strategy)]
            rows.append({
                "analysis_type": "seed_stratified",
                "held_out_seed": "",
                "seed": seed,
                "strategy": strategy,
                "num_games": len(subset),
                "village_win_rate": subset["village_win"].mean(),
                "wolf_win_rate": subset["wolf_win"].mean(),
                "first_check_wolf_rate": subset["first_check_wolf"].mean(),
            })

    for held_out_seed in sorted(df["seed"].unique()):
        kept = df[df["seed"] != held_out_seed]

        for strategy in STRATEGIES:
            subset = kept[kept["strategy"] == strategy]
            rows.append({
                "analysis_type": "leave_one_seed_out",
                "held_out_seed": held_out_seed,
                "seed": "",
                "strategy": strategy,
                "num_games": len(subset),
                "village_win_rate": subset["village_win"].mean(),
                "wolf_win_rate": subset["wolf_win"].mean(),
                "first_check_wolf_rate": subset["first_check_wolf"].mean(),
            })

    for strategy, baseline in KEY_CONTRASTS:
        seed_diffs = []

        for seed in sorted(df["seed"].unique()):
            seed_df = df[df["seed"] == seed]
            strategy_rate = seed_df[
                seed_df["strategy"] == strategy
            ]["village_win"].mean()
            baseline_rate = seed_df[
                seed_df["strategy"] == baseline
            ]["village_win"].mean()
            seed_diffs.append((strategy_rate - baseline_rate) * 100.0)

        rows.append({
            "analysis_type": "seed_diff_summary",
            "held_out_seed": "",
            "seed": "all",
            "strategy": f"{strategy} vs {baseline}",
            "num_games": "",
            "village_win_rate": np.mean(seed_diffs),
            "wolf_win_rate": "",
            "first_check_wolf_rate": "",
            "seed_diff_min_pp": min(seed_diffs),
            "seed_diff_max_pp": max(seed_diffs),
            "seed_diff_stdev_pp": (
                float(np.std(seed_diffs, ddof=1))
                if len(seed_diffs) > 1
                else 0.0
            ),
            "seed_diff_positive_count": sum(diff > 0 for diff in seed_diffs),
        })

    return pd.DataFrame(rows)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(path, index=False)


def setup_plot():
    plt.rcParams.update({
        "figure.figsize": (10, 6),
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": "#4b5563",
        "axes.labelcolor": "#111827",
        "xtick.color": "#111827",
        "ytick.color": "#111827",
        "text.color": "#111827",
        "font.size": 10,
    })


def save_bar_with_ci(path, df, value, lower, upper, title, ylabel):
    ordered = df.sort_values(value, ascending=True)
    y = np.arange(len(ordered))
    values = ordered[value].to_numpy(dtype=float) * 100.0
    low = ordered[lower].to_numpy(dtype=float) * 100.0
    high = ordered[upper].to_numpy(dtype=float) * 100.0
    xerr = np.vstack([values - low, high - values])
    plt.figure(figsize=(10, 7))
    plt.barh(y, values, color="#2f6f9f")
    plt.errorbar(values, y, xerr=xerr, fmt="none", ecolor="#111827", capsize=3)
    plt.yticks(y, ordered["strategy"])
    plt.xlabel(ylabel)
    plt.title(title)
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    plt.savefig(path, format="svg")
    plt.close()


def create_plots(df, descriptive, exploitation):
    setup_plot()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    save_bar_with_ci(
        OUTPUT_DIR / "village_win_rate_by_strategy.svg",
        descriptive,
        "village_win_mean",
        "village_win_ci_low",
        "village_win_ci_high",
        "Village Win Rate by Seer Search Strategy",
        "Village win rate (%)",
    )
    save_bar_with_ci(
        OUTPUT_DIR / "first_check_wolf_rate_by_strategy.svg",
        descriptive,
        "first_check_wolf_mean",
        "first_check_wolf_ci_low",
        "first_check_wolf_ci_high",
        "First-Check Wolf Discovery by Strategy",
        "First-check wolf rate (%)",
    )
    save_bar_with_ci(
        OUTPUT_DIR / "seer_survival_by_strategy.svg",
        descriptive,
        "seer_survived_to_game_end_mean",
        "seer_survived_to_game_end_ci_low",
        "seer_survived_to_game_end_ci_high",
        "Seer Survival by Strategy",
        "Seer survival rate (%)",
    )

    ordered = descriptive.set_index("strategy").loc[STRATEGIES].reset_index()
    x = np.arange(len(ordered))
    width = 0.38
    plt.figure(figsize=(12, 6))
    plt.bar(
        x - width / 2,
        ordered["found_wolf_by_check_2_mean"] * 100,
        width,
        label="By check 2",
        color="#2f6f9f",
    )
    plt.bar(
        x + width / 2,
        ordered["found_wolf_by_check_3_mean"] * 100,
        width,
        label="By check 3",
        color="#d97706",
    )
    plt.xticks(x, ordered["strategy"], rotation=45, ha="right")
    plt.ylabel("Discovery rate (%)")
    plt.title("Wolf Discovery by Check 2 and Check 3")
    plt.legend()
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "found_wolf_by_check_2_and_3.svg", format="svg")
    plt.close()

    plt.figure(figsize=(8, 6))
    plt.scatter(
        descriptive["search_path_coverage_score_mean"],
        descriptive["village_win_mean"] * 100,
        color="#2f6f9f",
    )

    for _, row in descriptive.iterrows():
        plt.annotate(
            row["strategy"],
            (
                row["search_path_coverage_score_mean"],
                row["village_win_mean"] * 100,
            ),
            fontsize=8,
            xytext=(4, 3),
            textcoords="offset points",
        )

    plt.xlabel("Mean search-path coverage score")
    plt.ylabel("Village win rate (%)")
    plt.title("Coverage vs Village Win Rate")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "coverage_vs_village_win.svg", format="svg")
    plt.close()

    group_rows = exploitation[exploitation["row_type"] == "group"]
    plt.figure(figsize=(8, 5))
    plt.bar(
        group_rows["group"],
        group_rows["village_win_rate"] * 100,
        color=["#9a3412", "#2f6f9f", "#6b7280"],
    )
    plt.ylabel("Village win rate (%)")
    plt.title("Structured Diversification vs Behavioral Exploitation")
    plt.xticks(rotation=20, ha="right")
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "structured_vs_behavioral_comparison.svg",
        format="svg",
    )
    plt.close()

    seed_rates = (
        df.groupby(["seed", "strategy"], as_index=False)["village_win"]
        .mean()
    )
    plt.figure(figsize=(12, 7))

    for strategy in STRATEGIES:
        subset = seed_rates[seed_rates["strategy"] == strategy]
        plt.plot(
            subset["seed"],
            subset["village_win"] * 100,
            marker="o",
            linewidth=1,
            label=strategy,
        )

    plt.ylabel("Village win rate (%)")
    plt.xlabel("Seed")
    plt.title("Seed-Level Strategy Performance")
    plt.legend(ncol=2, fontsize=7)
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "seed_level_strategy_performance.svg", format="svg")
    plt.close()

    side_rates = (
        df[df["strategy"].isin(["left_to_right", "right_to_left"])]
        .groupby(["seer_side", "strategy"], as_index=False)["village_win"]
        .mean()
    )
    sides = sorted(side_rates["seer_side"].unique())
    x = np.arange(len(sides))
    width = 0.35
    left_values = [
        side_rates[
            (side_rates["seer_side"] == side)
            & (side_rates["strategy"] == "left_to_right")
        ]["village_win"].iloc[0] * 100
        for side in sides
    ]
    right_values = [
        side_rates[
            (side_rates["seer_side"] == side)
            & (side_rates["strategy"] == "right_to_left")
        ]["village_win"].iloc[0] * 100
        for side in sides
    ]
    plt.figure(figsize=(7, 5))
    plt.bar(x - width / 2, left_values, width, label="left_to_right")
    plt.bar(x + width / 2, right_values, width, label="right_to_left")
    plt.xticks(x, sides)
    plt.ylabel("Village win rate (%)")
    plt.xlabel("Seer side")
    plt.title("Left-to-Right vs Right-to-Left by Seer Side")
    plt.legend()
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "left_vs_right_by_seer_side.svg",
        format="svg",
    )
    plt.close()


def pct(value):
    return f"{value * 100:.2f}%"


def pp(value):
    return f"{value:.2f} pp"


def get_strategy_value(descriptive, strategy, column):
    row = descriptive[descriptive["strategy"] == strategy].iloc[0]
    return row[column]


def write_report(
    df,
    descriptive,
    omnibus,
    pairwise,
    early_omnibus,
    early_pairwise,
    model_fits,
    mechanism,
    exploitation,
    direction,
    robustness,
):
    random_village = get_strategy_value(descriptive, "random", "village_win_mean")
    alternate_village = get_strategy_value(
        descriptive,
        "alternate_sides",
        "village_win_mean",
    )
    right_village = get_strategy_value(
        descriptive,
        "right_to_left",
        "village_win_mean",
    )
    behavioral_group = exploitation[
        exploitation["group"] == "behavioral_exploitation"
    ].iloc[0]
    structured_group = exploitation[
        exploitation["group"] == "structured_diversification"
    ].iloc[0]

    alt_random = pairwise[
        pairwise["contrast"] == "alternate_sides vs random"
    ].iloc[0]
    right_random = pairwise[
        pairwise["contrast"] == "right_to_left vs random"
    ].iloc[0]
    hpw_random = pairwise[
        pairwise["contrast"] == "highest_p_wolf vs random"
    ].iloc[0]
    hs_random = pairwise[
        pairwise["contrast"] == "highest_suspicion vs random"
    ].iloc[0]
    alt_right = pairwise[
        pairwise["contrast"] == "alternate_sides vs right_to_left"
    ].iloc[0]
    strategy_omnibus = omnibus.iloc[0]

    with (OUTPUT_DIR / "analysis_report.md").open("w") as file:
        file.write(
            "# Structured Seer Search Statistical Analysis Report\n\n"
        )
        file.write("## Technical Summary\n\n")
        file.write(
            f"The structured seer search experiment analyzed {len(df):,} "
            "game-level rows from 14 strategies, 5 seeds, and 500 games per "
            "strategy-seed cell. A seed-adjusted logistic model found an "
            f"overall strategy effect on village victory "
            f"(LR={strategy_omnibus['lr_statistic']:.2f}, "
            f"df={int(strategy_omnibus['df'])}, "
            f"p={strategy_omnibus['p_value']:.4g}). "
            f"Descriptively, `alternate_sides` had the highest village win "
            f"rate ({pct(alternate_village)}) and `right_to_left` was close "
            f"behind ({pct(right_village)}), compared with random "
            f"({pct(random_village)}). However, the specific "
            "`alternate_sides` vs `right_to_left` contrast was not "
            "statistically supported after correction, so `alternate_sides` "
            "should be treated as descriptively highest rather than proven "
            "best.\n\n"
        )
        file.write(
            "The clearest negative result is that behavioral exploitation "
            "strategies underperformed: `highest_p_wolf` and "
            "`highest_suspicion` had lower village win rates than random, "
            "with corrected pairwise evidence against both. Their early wolf "
            "discovery rates were not better than random, and their seer "
            "survival rates were lower, suggesting that aggressive behavioral "
            "targeting narrows the search without improving information "
            "quality in this simulation.\n\n"
        )

        file.write("## Scope, Data, and Metrics\n\n")
        file.write(
            "- Primary dataset: "
            "`results/structured_seer_search/"
            "structured_seer_search_game_level_raw.csv`.\n"
            "- Unit of analysis: one completed game.\n"
            "- Outcome: `village_win`, a binary indicator for village victory.\n"
            "- Main baseline: `random` seer checking.\n"
            "- Seed handling: seed fixed effects in primary logistic models.\n"
            "- Search-path coverage: `unique_checked_targets / 9`.\n"
            "- Inference note: strategy is pre-treatment; early discovery, "
            "seer survival, coverage, and diversity are intermediate or "
            "post-treatment variables. Mechanism models are diagnostic, not "
            "formal causal mediation.\n\n"
        )

        file.write("## Descriptive Results\n\n")
        file.write(
            "The top descriptive strategy was `alternate_sides`, followed by "
            "`right_to_left` and `farthest_first`. `random` and `default` "
            "matched because the structured experiment enables the repeat "
            "guard for both.\n\n"
        )
        file.write(
            "| strategy | village win | 95% CI | first check wolf | "
            "found by check 3 | no wolf found | seer survival | coverage |\n"
        )
        file.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")

        for _, row in descriptive.iterrows():
            file.write(
                f"| {row['strategy']} | "
                f"{pct(row['village_win_mean'])} | "
                f"{pct(row['village_win_ci_low'])}-"
                f"{pct(row['village_win_ci_high'])} | "
                f"{pct(row['first_check_wolf_mean'])} | "
                f"{pct(row['found_wolf_by_check_3_mean'])} | "
                f"{pct(row['no_wolf_found_rate_mean'])} | "
                f"{pct(row['seer_survived_to_game_end_mean'])} | "
                f"{row['search_path_coverage_score_mean']:.2f} |\n"
            )

        file.write("\n## Strategy Comparison Model\n\n")
        file.write(
            "The primary model was a game-level logistic regression: "
            "`village_win ~ strategy + seed`, with `random` and seed 42 as "
            "references. Pairwise tests below use Holm correction across the "
            "requested comparisons.\n\n"
        )
        file.write(
            "| contrast | odds ratio | 95% CI | p | Holm p | interpretation |\n"
        )
        file.write("|---|---:|---:|---:|---:|---|\n")

        for _, row in pairwise.iterrows():
            interpretation = "statistically supported"
            if row["p_value_holm"] >= 0.05:
                interpretation = "weak/inconclusive"
            file.write(
                f"| {row['contrast']} | {row['odds_ratio']:.3f} | "
                f"{row['or_ci_low']:.3f}-{row['or_ci_high']:.3f} | "
                f"{row['p_value']:.4g} | {row['p_value_holm']:.4g} | "
                f"{interpretation} |\n"
            )

        file.write("\n## Early Discovery and Mechanisms\n\n")
        file.write(
            "Structured strategies did not consistently improve first-check "
            "wolf discovery relative to random. The stronger village outcomes "
            "for `alternate_sides` and `right_to_left` are therefore not "
            "fully explained by a first-check advantage. Discovery by check 2 "
            "or check 3 is somewhat better for some structured strategies, "
            "but the effect sizes are modest.\n\n"
        )
        file.write(
            "Staged models show that adding early discovery and seer survival "
            "changes some strategy coefficients, but because these variables "
            "occur after strategy assignment they should be interpreted as "
            "mechanism diagnostics rather than causal mediation estimates.\n\n"
        )

        file.write("## Exploitation vs Diversification\n\n")
        file.write(
            f"Behavioral exploitation strategies had a combined village win "
            f"rate of {pct(behavioral_group['village_win_rate'])}, while the "
            f"structured diversification group had {pct(structured_group['village_win_rate'])}. "
            "The behavioral group also had lower seer survival. This supports "
            "the interpretation that aggressive behavioral targeting can "
            "narrow search without increasing useful information.\n\n"
        )

        file.write("## Direction Asymmetry\n\n")
        file.write(
            f"`right_to_left` beat `random` descriptively, but the requested "
            f"pairwise model did not survive Holm correction "
            f"(OR={right_random['odds_ratio']:.3f}, "
            f"raw p={right_random['p_value']:.4g}, "
            f"Holm p={right_random['p_value_holm']:.4g}). "
            f"The direct `alternate_sides` vs `right_to_left` contrast was "
            f"inconclusive (OR={alt_right['odds_ratio']:.3f}, "
            f"Holm p={alt_right['p_value_holm']:.4g}). "
            "Direction-asymmetry interaction tests are reported separately in "
            "`direction_asymmetry_analysis.csv`; because left/right ordering "
            "could reflect seat indexing artifacts, this should be isolated "
            "in a follow-up experiment.\n\n"
        )

        file.write("## Robustness\n\n")
        file.write(
            "Seed-stratified and leave-one-seed-out summaries are saved in "
            "`robustness_analysis.csv`. The strongest caution is that only "
            "five seeds are available, so seed fixed effects and "
            "leave-one-seed-out checks are more reliable than cluster-robust "
            "standard errors with five clusters. Conclusions that depend on "
            "one strategy's exact rank should be treated cautiously.\n\n"
        )

        file.write("## Answers to Required Questions\n\n")
        file.write(
            "1. **Which strategies are statistically better than random?** "
            "No positive strategy-vs-random contrast is statistically "
            "significant after Holm correction. `alternate_sides` and "
            "`right_to_left` are practically meaningful but statistically "
            "uncertain improvements over random. `highest_p_wolf` and "
            "`highest_suspicion` are statistically worse than random.\n"
        )
        file.write(
            "2. **Is `alternate_sides` truly best?** It is descriptively "
            "highest, but not statistically distinguishable from "
            "`right_to_left` in the requested contrast.\n"
        )
        file.write(
            "3. **Is `right_to_left` robust?** It is stronger than random in "
            "descriptive results and the unadjusted primary contrast, but it "
            "does not survive Holm correction. The direction asymmetry should "
            "therefore be treated as potentially structural or artifact-prone "
            "until a follow-up isolates seat-order effects.\n"
        )
        file.write(
            "4. **Do structured strategies outperform behavioral suspicion "
            "strategies?** Yes, in this dataset structured diversification "
            "outperforms behavioral exploitation descriptively and aligns "
            "with the poor model results for `highest_p_wolf` and "
            "`highest_suspicion`.\n"
        )
        file.write(
            "5. **Does early wolf discovery explain performance?** Only "
            "partially. Early discovery improves village outcomes, but "
            "strategy differences are not simply first-check discovery "
            "differences.\n"
        )
        file.write(
            "6. **Does diversification matter independently?** Evidence is "
            "suggestive but not causal. Coverage/diversity metrics are "
            "post-treatment, and their independent role should be tested in a "
            "targeted design.\n"
        )
        file.write(
            "7. **Why do behavioral strategies perform poorly?** They do not "
            "improve early discovery enough to compensate for lower seer "
            "survival and narrower search behavior.\n"
        )
        file.write(
            "8. **Is there evidence of simulation asymmetry?** Yes, the "
            "`left_to_right` vs `right_to_left` gap is large enough to merit "
            "a follow-up that randomizes or mirrors seat numbering.\n"
        )
        file.write(
            "9. **Next experiment:** isolate seat-order asymmetry by running "
            "mirrored seat labels or randomized clockwise/counter-clockwise "
            "orientation while holding role randomization and strategy logic "
            "constant.\n\n"
        )

        file.write("## Output Files\n\n")
        for filename in [
            "descriptive_statistics.csv",
            "strategy_omnibus_tests.csv",
            "pairwise_strategy_contrasts.csv",
            "early_discovery_analysis.csv",
            "village_win_models.csv",
            "mechanism_models.csv",
            "exploitation_vs_diversification.csv",
            "direction_asymmetry_analysis.csv",
            "robustness_analysis.csv",
        ]:
            file.write(f"- `{filename}`\n")


def validate_outputs(df, descriptive, pairwise):
    issues = []

    if len(df) != 35000:
        issues.append(f"Expected 35,000 raw rows, found {len(df):,}.")

    if df["game_id"].nunique() != len(df):
        issues.append("game_id values are not unique.")

    if set(df["winner"].unique()) - {"wolf", "village", "draw"}:
        issues.append("Invalid winner values found.")

    if len(descriptive) != len(STRATEGIES):
        issues.append("Descriptive row count does not match strategy count.")

    if pairwise["p_value_holm"].isna().any():
        issues.append("Missing Holm-adjusted p-values.")

    return issues


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = prepare_data()
    descriptive = descriptive_statistics(df)
    primary_model, omnibus, pairwise, adjusted_probabilities = (
        strategy_models(df)
    )
    early_omnibus, early_pairwise = early_discovery_models(df)
    all_omnibus = pd.concat([omnibus, early_omnibus], ignore_index=True)
    early_analysis = pd.concat(
        [
            early_omnibus.assign(row_type="omnibus"),
            early_pairwise.assign(row_type="pairwise"),
        ],
        ignore_index=True,
        sort=False,
    )
    model_fits, mechanism, _ = mechanism_models(df)
    exploitation = exploitation_vs_diversification(df, descriptive)
    direction = direction_asymmetry(df)
    robustness = robustness_analysis(df)

    write_csv(OUTPUT_DIR / "descriptive_statistics.csv", descriptive)
    write_csv(OUTPUT_DIR / "strategy_omnibus_tests.csv", all_omnibus)
    write_csv(OUTPUT_DIR / "pairwise_strategy_contrasts.csv", pairwise)
    write_csv(OUTPUT_DIR / "early_discovery_analysis.csv", early_analysis)
    write_csv(
        OUTPUT_DIR / "adjusted_village_win_probabilities.csv",
        adjusted_probabilities,
    )
    write_csv(OUTPUT_DIR / "village_win_models.csv", model_fits)
    write_csv(OUTPUT_DIR / "mechanism_models.csv", mechanism)
    write_csv(
        OUTPUT_DIR / "exploitation_vs_diversification.csv",
        exploitation,
    )
    write_csv(OUTPUT_DIR / "direction_asymmetry_analysis.csv", direction)
    write_csv(OUTPUT_DIR / "robustness_analysis.csv", robustness)
    create_plots(df, descriptive, exploitation)
    write_report(
        df,
        descriptive,
        omnibus,
        pairwise,
        early_omnibus,
        early_pairwise,
        model_fits,
        mechanism,
        exploitation,
        direction,
        robustness,
    )

    validation_issues = validate_outputs(df, descriptive, pairwise)
    validation_path = OUTPUT_DIR / "validation_summary.txt"

    with validation_path.open("w") as file:
        if validation_issues:
            file.write("Validation issues:\n")
            for issue in validation_issues:
                file.write(f"- {issue}\n")
        else:
            file.write("Validation passed: generated analysis outputs are internally consistent.\n")

    print("Structured seer search statistical analysis complete.")
    print(f"Rows analyzed: {len(df):,}")
    print(f"Output directory: {OUTPUT_DIR}")
    if validation_issues:
        print("Validation issues:")
        for issue in validation_issues:
            print(f"- {issue}")
    else:
        print("Validation passed.")


if __name__ == "__main__":
    main()
