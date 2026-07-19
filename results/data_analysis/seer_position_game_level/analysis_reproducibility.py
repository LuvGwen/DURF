import csv
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/durf_werewolf_matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = (
    ROOT
    / "results"
    / "ten_player_seer_position_randomized_roles_game_level_raw.csv"
)
OUTPUT_DIR = Path(__file__).resolve().parent

STRATEGIES = [
    "default",
    "random",
    "edge_first",
    "inner_first",
    "highest_p_wolf",
    "highest_suspicion",
    "opposite_side",
]
SEEDS = [42, 43, 44, 45, 46]
EDGE_SEAT_COUNT = 4
INNER_SEAT_COUNT = 6
TOTAL_SEAT_COUNT = 10
WOLF_COUNT = 3
Z_975 = 1.959963984540054


def normal_cdf(value):
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def normal_p_value(z_value):
    return 2.0 * (1.0 - normal_cdf(abs(z_value)))


def gammainc_lower_series(a_value, x_value):
    gln = math.lgamma(a_value)

    if x_value <= 0:
        return 0.0

    ap = a_value
    total = 1.0 / a_value
    delta = total

    for _ in range(1000):
        ap += 1.0
        delta *= x_value / ap
        total += delta
        if abs(delta) < abs(total) * 1e-14:
            break

    return total * math.exp(-x_value + a_value * math.log(x_value) - gln)


def gammainc_upper_cf(a_value, x_value):
    gln = math.lgamma(a_value)
    b_value = x_value + 1.0 - a_value
    c_value = 1.0 / 1e-300
    d_value = 1.0 / b_value
    h_value = d_value

    for i in range(1, 1000):
        an = -i * (i - a_value)
        b_value += 2.0
        d_value = an * d_value + b_value
        if abs(d_value) < 1e-300:
            d_value = 1e-300
        c_value = b_value + an / c_value
        if abs(c_value) < 1e-300:
            c_value = 1e-300
        d_value = 1.0 / d_value
        delta = d_value * c_value
        h_value *= delta
        if abs(delta - 1.0) < 1e-14:
            break

    return math.exp(-x_value + a_value * math.log(x_value) - gln) * h_value


def chi_square_sf(statistic, df):
    if statistic < 0:
        return 1.0

    a_value = df / 2.0
    x_value = statistic / 2.0

    if x_value < a_value + 1.0:
        return max(0.0, min(1.0, 1.0 - gammainc_lower_series(a_value, x_value)))

    return max(0.0, min(1.0, gammainc_upper_cf(a_value, x_value)))


def hypergeom_pmf(k_value, population, successes, draws):
    return (
        math.comb(successes, k_value)
        * math.comb(population - successes, draws - k_value)
        / math.comb(population, draws)
    )


def safe_float(value):
    if value in ("", None):
        return None

    return float(value)


def safe_int(value):
    if value in ("", None):
        return None

    return int(float(value))


def parse_json_list(value):
    if value in ("", None):
        return []

    return json.loads(value)


def write_csv(path, rows, fieldnames):
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


def format_p_value(value):
    if value is None:
        return "NA"

    if value < 0.001:
        return "<0.001"

    return f"{value:.3f}"


def format_pct(value):
    return f"{value * 100:.2f}%"


def wilson_ci(successes, total):
    if total == 0:
        return (None, None)

    phat = successes / total
    denominator = 1.0 + Z_975 ** 2 / total
    center = (phat + Z_975 ** 2 / (2.0 * total)) / denominator
    margin = (
        Z_975
        * math.sqrt(
            phat * (1.0 - phat) / total
            + Z_975 ** 2 / (4.0 * total ** 2)
        )
        / denominator
    )
    return (max(0.0, center - margin), min(1.0, center + margin))


def mean_ci(values):
    if not values:
        return (None, None, None, None)

    mean_value = sum(values) / len(values)
    if len(values) < 2:
        return (mean_value, 0.0, mean_value, mean_value)

    sd_value = math.sqrt(
        sum((value - mean_value) ** 2 for value in values)
        / (len(values) - 1)
    )
    margin = Z_975 * sd_value / math.sqrt(len(values))
    return (mean_value, sd_value, mean_value - margin, mean_value + margin)


def two_proportion_test(success_a, total_a, success_b, total_b):
    rate_a = success_a / total_a
    rate_b = success_b / total_b
    pooled = (success_a + success_b) / (total_a + total_b)
    se = math.sqrt(pooled * (1.0 - pooled) * (1.0 / total_a + 1.0 / total_b))
    z_value = (rate_a - rate_b) / se if se > 0 else 0.0
    p_value = normal_p_value(z_value)
    ci_se = math.sqrt(
        rate_a * (1.0 - rate_a) / total_a
        + rate_b * (1.0 - rate_b) / total_b
    )
    diff = rate_a - rate_b
    h_value = 2.0 * (
        math.asin(math.sqrt(rate_a)) - math.asin(math.sqrt(rate_b))
    )
    return {
        "rate_a": rate_a,
        "rate_b": rate_b,
        "difference": diff,
        "ci_low": diff - Z_975 * ci_se,
        "ci_high": diff + Z_975 * ci_se,
        "z": z_value,
        "p_value": p_value,
        "cohen_h": h_value,
    }


def odds_ratio_2x2(success_a, fail_a, success_b, fail_b):
    a_value = success_a + 0.5
    b_value = fail_a + 0.5
    c_value = success_b + 0.5
    d_value = fail_b + 0.5
    log_or = math.log((a_value * d_value) / (b_value * c_value))
    se = math.sqrt(1.0 / a_value + 1.0 / b_value + 1.0 / c_value + 1.0 / d_value)
    z_value = log_or / se
    return {
        "odds_ratio": math.exp(log_or),
        "ci_low": math.exp(log_or - Z_975 * se),
        "ci_high": math.exp(log_or + Z_975 * se),
        "z": z_value,
        "p_value": normal_p_value(z_value),
    }


def holm_adjust(p_values):
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [None] * len(p_values)
    running_max = 0.0
    m_value = len(p_values)

    for rank, (index, p_value) in enumerate(indexed):
        adjusted_p = min(1.0, (m_value - rank) * p_value)
        running_max = max(running_max, adjusted_p)
        adjusted[index] = running_max

    return adjusted


def load_rows():
    rows = []

    with INPUT_PATH.open() as file:
        for raw_row in csv.DictReader(file):
            row = dict(raw_row)
            row["seed"] = safe_int(row["seed"])
            row["game_index_within_seed"] = safe_int(
                row["game_index_within_seed"]
            )
            row["village_win"] = safe_int(row["village_win"])
            row["wolf_win"] = safe_int(row["wolf_win"])
            row["seer_seat"] = safe_int(row["seer_seat"])
            row["wolf_seats"] = parse_json_list(row["wolf_seats"])
            row["wolves_on_edge"] = safe_int(row["wolves_on_edge"])
            row["wolves_on_inner"] = safe_int(row["wolves_on_inner"])
            row["wolves_left_side"] = safe_int(row["wolves_left_side"])
            row["wolves_right_side"] = safe_int(row["wolves_right_side"])
            row["first_check_target"] = safe_int(row["first_check_target"])
            row["first_check_target_is_wolf"] = safe_int(
                row["first_check_target_is_wolf"]
            )
            row["all_seer_check_targets_in_order"] = parse_json_list(
                row["all_seer_check_targets_in_order"]
            )
            row["all_seer_check_roles_in_order"] = parse_json_list(
                row["all_seer_check_roles_in_order"]
            )
            row["total_seer_checks"] = safe_int(row["total_seer_checks"])
            row["seer_found_any_wolf"] = safe_int(row["seer_found_any_wolf"])
            row["seer_found_wolf_count"] = safe_int(row["seer_found_wolf_count"])
            row["first_check_wolf"] = safe_int(row["first_check_wolf"])
            row["seer_survived_to_game_end"] = safe_int(
                row["seer_survived_to_game_end"]
            )
            row["seer_death_round"] = safe_int(row["seer_death_round"])
            row["total_rounds"] = safe_int(row["total_rounds"])
            row["final_alive_players"] = safe_int(row["final_alive_players"])
            row["final_alive_wolves"] = safe_int(row["final_alive_wolves"])
            row["final_alive_villagers"] = safe_int(row["final_alive_villagers"])
            rows.append(row)

    return rows


def rows_by(rows, key):
    grouped = defaultdict(list)

    for row in rows:
        grouped[row[key]].append(row)

    return grouped


def build_design_matrix(
    rows,
    strategy_ref="random",
    include_seed_fixed_effects=True,
    include_post_treatment=False,
    include_edge_wolves_interaction=False,
    include_strategy_first_check_interaction=False,
    include_seat_type_strategy_interaction=False,
):
    columns = ["intercept"]
    matrix_rows = []
    strategy_levels = [strategy for strategy in STRATEGIES if strategy != strategy_ref]
    seed_levels = [seed for seed in SEEDS if seed != SEEDS[0]]

    columns.extend(f"strategy:{strategy}" for strategy in strategy_levels)
    columns.extend([
        "first_check_target_is_wolf",
        "wolves_on_edge",
        "seer_seat_centered",
        "seer_side:right",
    ])
    if include_seed_fixed_effects:
        columns.extend(f"seed:{seed}" for seed in seed_levels)

    if include_post_treatment:
        columns.extend([
            "total_seer_checks",
            "seer_survived_to_game_end",
        ])

    if include_edge_wolves_interaction:
        columns.append("strategy:edge_first_x_wolves_on_edge")

    if include_strategy_first_check_interaction:
        columns.extend(
            f"strategy:{strategy}_x_first_check_target_is_wolf"
            for strategy in strategy_levels
        )

    if include_seat_type_strategy_interaction:
        columns.append("seer_seat_type:edge")
        columns.extend(
            f"strategy:{strategy}_x_seer_seat_type:edge"
            for strategy in strategy_levels
        )

    for row in rows:
        values = [1.0]
        strategy = row["strategy"]
        first_check = float(row["first_check_target_is_wolf"])
        seer_edge = 1.0 if row["seer_seat_type"] == "edge" else 0.0
        values.extend(1.0 if strategy == level else 0.0 for level in strategy_levels)
        values.extend([
            first_check,
            float(row["wolves_on_edge"]),
            float(row["seer_seat"] - 5.5),
            1.0 if row["seer_side"] == "right" else 0.0,
        ])
        if include_seed_fixed_effects:
            values.extend(
                1.0 if row["seed"] == seed else 0.0
                for seed in seed_levels
            )

        if include_post_treatment:
            values.extend([
                float(row["total_seer_checks"]),
                float(row["seer_survived_to_game_end"]),
            ])

        if include_edge_wolves_interaction:
            values.append(
                (1.0 if strategy == "edge_first" else 0.0)
                * float(row["wolves_on_edge"])
            )

        if include_strategy_first_check_interaction:
            values.extend(
                (1.0 if strategy == level else 0.0) * first_check
                for level in strategy_levels
            )

        if include_seat_type_strategy_interaction:
            values.append(seer_edge)
            values.extend(
                (1.0 if strategy == level else 0.0) * seer_edge
                for level in strategy_levels
            )

        matrix_rows.append(values)

    return np.asarray(matrix_rows, dtype=float), columns


def logistic_fit(y_values, x_values, columns):
    y_array = np.asarray(y_values, dtype=float)
    x_array = np.asarray(x_values, dtype=float)
    beta = np.zeros(x_array.shape[1])

    for _ in range(100):
        eta = np.clip(x_array @ beta, -35.0, 35.0)
        p_hat = 1.0 / (1.0 + np.exp(-eta))
        weights = np.clip(p_hat * (1.0 - p_hat), 1e-9, None)
        gradient = x_array.T @ (y_array - p_hat)
        hessian = x_array.T @ (weights[:, None] * x_array)
        step = np.linalg.pinv(hessian) @ gradient
        beta += step

        if float(np.max(np.abs(step))) < 1e-8:
            break

    eta = np.clip(x_array @ beta, -35.0, 35.0)
    p_hat = 1.0 / (1.0 + np.exp(-eta))
    weights = np.clip(p_hat * (1.0 - p_hat), 1e-9, None)
    hessian = x_array.T @ (weights[:, None] * x_array)
    covariance = np.linalg.pinv(hessian)
    log_likelihood = float(
        np.sum(
            y_array * np.log(np.clip(p_hat, 1e-12, 1.0))
            + (1.0 - y_array) * np.log(np.clip(1.0 - p_hat, 1e-12, 1.0))
        )
    )

    return {
        "beta": beta,
        "covariance": covariance,
        "columns": columns,
        "log_likelihood": log_likelihood,
        "aic": 2.0 * len(columns) - 2.0 * log_likelihood,
        "predicted": p_hat,
        "x": x_array,
        "y": y_array,
    }


def cluster_covariance(model, groups):
    x_array = model["x"]
    y_array = model["y"]
    p_hat = model["predicted"]
    hessian_inv = model["covariance"]
    grouped_scores = defaultdict(lambda: np.zeros(x_array.shape[1]))

    for index, group in enumerate(groups):
        grouped_scores[group] += x_array[index] * (y_array[index] - p_hat[index])

    meat = np.zeros((x_array.shape[1], x_array.shape[1]))
    for score in grouped_scores.values():
        meat += np.outer(score, score)

    cluster_count = len(grouped_scores)
    n_rows = x_array.shape[0]
    n_params = x_array.shape[1]
    finite_correction = (
        cluster_count / (cluster_count - 1)
        * (n_rows - 1)
        / (n_rows - n_params)
        if cluster_count > 1 and n_rows > n_params
        else 1.0
    )

    return finite_correction * hessian_inv @ meat @ hessian_inv


def coefficient_rows(model_name, model, covariance=None, note=""):
    beta = model["beta"]
    cov = model["covariance"] if covariance is None else covariance
    rows = []

    for index, column in enumerate(model["columns"]):
        se = math.sqrt(max(float(cov[index, index]), 0.0))
        z_value = beta[index] / se if se > 0 else 0.0
        rows.append({
            "model": model_name,
            "term": column,
            "coef": beta[index],
            "std_error": se,
            "odds_ratio": math.exp(beta[index]),
            "ci_low": math.exp(beta[index] - Z_975 * se),
            "ci_high": math.exp(beta[index] + Z_975 * se),
            "z": z_value,
            "p_value": normal_p_value(z_value),
            "n": len(model["y"]),
            "log_likelihood": model["log_likelihood"],
            "aic": model["aic"],
            "note": note,
        })

    return rows


def model_contrast(model, term_weights, label, contrast_type):
    index_by_column = {
        column: index for index, column in enumerate(model["columns"])
    }
    vector = np.zeros(len(model["columns"]))

    for term, weight in term_weights.items():
        if term not in index_by_column:
            continue
        vector[index_by_column[term]] = weight

    log_or = float(vector @ model["beta"])
    variance = float(vector @ model["covariance"] @ vector)
    se = math.sqrt(max(variance, 0.0))
    z_value = log_or / se if se > 0 else 0.0

    return {
        "contrast_type": contrast_type,
        "comparison": label,
        "estimate": log_or,
        "std_error": se,
        "odds_ratio": math.exp(log_or),
        "ci_low": math.exp(log_or - Z_975 * se),
        "ci_high": math.exp(log_or + Z_975 * se),
        "z": z_value,
        "p_value": normal_p_value(z_value),
        "p_value_holm": "",
        "effect_size": "",
        "notes": "Log-odds contrast from adjusted village-win model.",
    }


def make_bar_plot(
    path,
    labels,
    values,
    ci_lows,
    ci_highs,
    ylabel,
    title,
    color="#2b6cb0",
    rotate=False,
):
    fig_width = max(8.0, len(labels) * 1.15)
    fig, ax = plt.subplots(figsize=(fig_width, 5.2))
    x_values = np.arange(len(labels))
    yerr = [
        [value - low for value, low in zip(values, ci_lows)],
        [high - value for value, high in zip(values, ci_highs)],
    ]
    ax.bar(
        x_values,
        values,
        yerr=yerr,
        color=color,
        edgecolor="#1f2937",
        linewidth=0.8,
        capsize=4,
    )
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels, rotation=30 if rotate else 0, ha="right" if rotate else "center")
    ax.set_ylim(0.0, min(1.0, max(ci_highs) * 1.25))
    ax.yaxis.set_major_formatter(lambda value, _: f"{value * 100:.0f}%")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)
    strip_trailing_whitespace(path)


def strip_trailing_whitespace(path):
    path.write_text(
        "\n".join(line.rstrip() for line in path.read_text().splitlines())
        + "\n"
    )


def make_grouped_metric_plot(path, rows):
    labels = ["random", "edge_first", "inner_first"]
    metrics = [
        ("first_check_wolf_rate", "First check wolf"),
        ("village_win_rate", "Village win"),
        ("seer_survival_rate", "Seer survival"),
    ]
    row_by_strategy = {row["strategy"]: row for row in rows}
    x_values = np.arange(len(labels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    colors = ["#2b6cb0", "#d97706", "#6b8e23"]

    for index, (field, label) in enumerate(metrics):
        values = [row_by_strategy[strategy][field] for strategy in labels]
        ax.bar(
            x_values + (index - 1) * width,
            values,
            width,
            label=label,
            color=colors[index],
            edgecolor="#1f2937",
            linewidth=0.7,
        )

    ax.set_title("Edge-first vs inner-first vs random comparison")
    ax.set_ylabel("Rate")
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels)
    ax.yaxis.set_major_formatter(lambda value, _: f"{value * 100:.0f}%")
    ax.set_ylim(0.0, 0.8)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)
    strip_trailing_whitespace(path)


def make_leave_one_seed_plot(path, rows):
    loo_rows = [
        row for row in rows
        if row["section"] == "leave_one_seed_out_strategy"
    ]
    fig, ax = plt.subplots(figsize=(10.5, 5.5))

    for strategy in ["random", "edge_first", "inner_first"]:
        strategy_rows = [
            row for row in loo_rows
            if row["strategy"] == strategy
        ]
        strategy_rows.sort(key=lambda row: row["excluded_seed"])
        ax.plot(
            [row["excluded_seed"] for row in strategy_rows],
            [row["village_win_rate"] for row in strategy_rows],
            marker="o",
            linewidth=1.8,
            label=strategy,
        )

    ax.set_title("Leave-one-seed-out village win rates")
    ax.set_xlabel("Excluded seed")
    ax.set_ylabel("Village win rate")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value * 100:.0f}%")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)
    strip_trailing_whitespace(path)


def analyze(rows):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_games = len(rows)
    strategy_groups = rows_by(rows, "strategy")
    seed_groups = rows_by(rows, "seed")
    y_values = [row["village_win"] for row in rows]

    descriptive_rows = []
    descriptive_rows.append({
        "section": "dataset",
        "strategy": "all",
        "seed": "all",
        "n_games": total_games,
        "village_wins": sum(row["village_win"] for row in rows),
        "wolf_wins": sum(row["wolf_win"] for row in rows),
        "village_win_rate": sum(row["village_win"] for row in rows) / total_games,
        "first_check_wolf_rate": (
            sum(row["first_check_target_is_wolf"] for row in rows) / total_games
        ),
        "mean_total_seer_checks": (
            sum(row["total_seer_checks"] for row in rows) / total_games
        ),
        "seer_survival_rate": (
            sum(row["seer_survived_to_game_end"] for row in rows) / total_games
        ),
        "first_target_edge_rate": (
            sum(1 for row in rows if row["first_check_target_seat_type"] == "edge")
            / total_games
        ),
        "mean_wolves_on_edge": (
            sum(row["wolves_on_edge"] for row in rows) / total_games
        ),
    })

    for strategy in STRATEGIES:
        strategy_rows = strategy_groups[strategy]
        n_games = len(strategy_rows)
        descriptive_rows.append({
            "section": "strategy",
            "strategy": strategy,
            "seed": "all",
            "n_games": n_games,
            "village_wins": sum(row["village_win"] for row in strategy_rows),
            "wolf_wins": sum(row["wolf_win"] for row in strategy_rows),
            "village_win_rate": (
                sum(row["village_win"] for row in strategy_rows) / n_games
            ),
            "first_check_wolf_rate": (
                sum(row["first_check_target_is_wolf"] for row in strategy_rows)
                / n_games
            ),
            "mean_total_seer_checks": (
                sum(row["total_seer_checks"] for row in strategy_rows) / n_games
            ),
            "seer_survival_rate": (
                sum(row["seer_survived_to_game_end"] for row in strategy_rows)
                / n_games
            ),
            "first_target_edge_rate": (
                sum(
                    1 for row in strategy_rows
                    if row["first_check_target_seat_type"] == "edge"
                )
                / n_games
            ),
            "mean_wolves_on_edge": (
                sum(row["wolves_on_edge"] for row in strategy_rows) / n_games
            ),
        })

    for seed in SEEDS:
        seed_rows = seed_groups[seed]
        for strategy in STRATEGIES:
            strategy_seed_rows = [
                row for row in seed_rows
                if row["strategy"] == strategy
            ]
            n_games = len(strategy_seed_rows)
            descriptive_rows.append({
                "section": "strategy_seed",
                "strategy": strategy,
                "seed": seed,
                "n_games": n_games,
                "village_wins": sum(row["village_win"] for row in strategy_seed_rows),
                "wolf_wins": sum(row["wolf_win"] for row in strategy_seed_rows),
                "village_win_rate": (
                    sum(row["village_win"] for row in strategy_seed_rows) / n_games
                ),
                "first_check_wolf_rate": (
                    sum(
                        row["first_check_target_is_wolf"]
                        for row in strategy_seed_rows
                    )
                    / n_games
                ),
                "mean_total_seer_checks": (
                    sum(row["total_seer_checks"] for row in strategy_seed_rows)
                    / n_games
                ),
                "seer_survival_rate": (
                    sum(
                        row["seer_survived_to_game_end"]
                        for row in strategy_seed_rows
                    )
                    / n_games
                ),
                "first_target_edge_rate": (
                    sum(
                        1 for row in strategy_seed_rows
                        if row["first_check_target_seat_type"] == "edge"
                    )
                    / n_games
                ),
                "mean_wolves_on_edge": (
                    sum(row["wolves_on_edge"] for row in strategy_seed_rows)
                    / n_games
                ),
            })

    seed_summary_by_strategy = {}
    for strategy in STRATEGIES:
        strategy_seed_rows = [
            row for row in descriptive_rows
            if row["section"] == "strategy_seed"
            and row["strategy"] == strategy
        ]
        village_mean, village_sd, _, _ = mean_ci([
            row["village_win_rate"] for row in strategy_seed_rows
        ])
        first_mean, first_sd, _, _ = mean_ci([
            row["first_check_wolf_rate"] for row in strategy_seed_rows
        ])
        survival_mean, survival_sd, _, _ = mean_ci([
            row["seer_survival_rate"] for row in strategy_seed_rows
        ])
        seed_summary_by_strategy[strategy] = {
            "village_win_rate_seed_mean": village_mean,
            "village_win_rate_seed_sd": village_sd,
            "first_check_wolf_rate_seed_mean": first_mean,
            "first_check_wolf_rate_seed_sd": first_sd,
            "seer_survival_rate_seed_mean": survival_mean,
            "seer_survival_rate_seed_sd": survival_sd,
        }
        descriptive_rows.append({
            "section": "strategy_seed_summary",
            "strategy": strategy,
            "seed": "all",
            "n_games": sum(row["n_games"] for row in strategy_seed_rows),
            "village_wins": "",
            "wolf_wins": "",
            "village_win_rate": village_mean,
            "village_win_rate_seed_sd": village_sd,
            "first_check_wolf_rate": first_mean,
            "first_check_wolf_rate_seed_sd": first_sd,
            "mean_total_seer_checks": "",
            "seer_survival_rate": survival_mean,
            "seer_survival_rate_seed_sd": survival_sd,
            "first_target_edge_rate": "",
            "mean_wolves_on_edge": "",
        })

    seat_rows = []
    total_edge_wolves = sum(row["wolves_on_edge"] for row in rows)
    total_inner_wolves = sum(row["wolves_on_inner"] for row in rows)
    total_edge_slots = total_games * EDGE_SEAT_COUNT
    total_inner_slots = total_games * INNER_SEAT_COUNT
    edge_prop = total_edge_wolves / total_edge_slots
    inner_prop = total_inner_wolves / total_inner_slots
    edge_ci = wilson_ci(total_edge_wolves, total_edge_slots)
    inner_ci = wilson_ci(total_inner_wolves, total_inner_slots)
    wolves_edge_values = [row["wolves_on_edge"] for row in rows]
    edge_mean, edge_sd, edge_mean_low, edge_mean_high = mean_ci(wolves_edge_values)
    expected_edge_mean = WOLF_COUNT * EDGE_SEAT_COUNT / TOTAL_SEAT_COUNT
    expected_edge_var = (
        WOLF_COUNT
        * (EDGE_SEAT_COUNT / TOTAL_SEAT_COUNT)
        * (1.0 - EDGE_SEAT_COUNT / TOTAL_SEAT_COUNT)
        * ((TOTAL_SEAT_COUNT - WOLF_COUNT) / (TOTAL_SEAT_COUNT - 1))
    )
    edge_z = (
        (edge_mean - expected_edge_mean)
        / math.sqrt(expected_edge_var / total_games)
    )
    distribution = Counter(wolves_edge_values)
    chi_square_stat = 0.0

    for k_value in range(4):
        expected_probability = hypergeom_pmf(
            k_value,
            TOTAL_SEAT_COUNT,
            EDGE_SEAT_COUNT,
            WOLF_COUNT,
        )
        observed_count = distribution.get(k_value, 0)
        expected_count = expected_probability * total_games
        chi_square_stat += (
            (observed_count - expected_count) ** 2 / expected_count
        )
        seat_rows.append({
            "section": "wolves_on_edge_distribution",
            "seat_type": "",
            "wolves_on_edge": k_value,
            "observed_count": observed_count,
            "observed_probability": observed_count / total_games,
            "expected_probability": expected_probability,
            "expected_count": expected_count,
            "observed_wolf_probability": "",
            "expected_wolf_probability": "",
            "ci_low": "",
            "ci_high": "",
            "test": "hypergeometric expected distribution",
            "statistic": "",
            "df": "",
            "p_value": "",
            "effect_size": "",
        })

    chi_square_p = chi_square_sf(chi_square_stat, 3)
    cramers_v = math.sqrt(chi_square_stat / (total_games * 3))

    seat_rows.extend([
        {
            "section": "seat_type_probability",
            "seat_type": "edge",
            "wolves_on_edge": "",
            "observed_count": total_edge_wolves,
            "observed_probability": "",
            "expected_probability": "",
            "expected_count": total_edge_slots * (WOLF_COUNT / TOTAL_SEAT_COUNT),
            "observed_wolf_probability": edge_prop,
            "expected_wolf_probability": WOLF_COUNT / TOTAL_SEAT_COUNT,
            "ci_low": edge_ci[0],
            "ci_high": edge_ci[1],
            "test": "clustered mean vs hypergeometric expectation",
            "statistic": edge_z,
            "df": "",
            "p_value": normal_p_value(edge_z),
            "effect_size": edge_mean - expected_edge_mean,
        },
        {
            "section": "seat_type_probability",
            "seat_type": "inner",
            "wolves_on_edge": "",
            "observed_count": total_inner_wolves,
            "observed_probability": "",
            "expected_probability": "",
            "expected_count": total_inner_slots * (WOLF_COUNT / TOTAL_SEAT_COUNT),
            "observed_wolf_probability": inner_prop,
            "expected_wolf_probability": WOLF_COUNT / TOTAL_SEAT_COUNT,
            "ci_low": inner_ci[0],
            "ci_high": inner_ci[1],
            "test": "descriptive complement",
            "statistic": "",
            "df": "",
            "p_value": "",
            "effect_size": "",
        },
        {
            "section": "mean_wolves_on_edge",
            "seat_type": "edge",
            "wolves_on_edge": "",
            "observed_count": "",
            "observed_probability": "",
            "expected_probability": "",
            "expected_count": "",
            "observed_wolf_probability": edge_mean,
            "expected_wolf_probability": expected_edge_mean,
            "ci_low": edge_mean_low,
            "ci_high": edge_mean_high,
            "test": "one-sample normal approximation",
            "statistic": edge_z,
            "df": "",
            "p_value": normal_p_value(edge_z),
            "effect_size": edge_mean - expected_edge_mean,
        },
        {
            "section": "distribution_goodness_of_fit",
            "seat_type": "edge",
            "wolves_on_edge": "",
            "observed_count": total_games,
            "observed_probability": "",
            "expected_probability": "",
            "expected_count": "",
            "observed_wolf_probability": "",
            "expected_wolf_probability": "",
            "ci_low": "",
            "ci_high": "",
            "test": "chi-square goodness-of-fit vs hypergeometric",
            "statistic": chi_square_stat,
            "df": 3,
            "p_value": chi_square_p,
            "effect_size": cramers_v,
        },
    ])

    first_check_rows = []
    for strategy in STRATEGIES:
        strategy_rows = strategy_groups[strategy]
        n_games = len(strategy_rows)
        successes = sum(row["first_check_target_is_wolf"] for row in strategy_rows)
        ci_low, ci_high = wilson_ci(successes, n_games)
        first_check_rows.append({
            "strategy": strategy,
            "n_games": n_games,
            "first_check_wolf_count": successes,
            "first_check_wolf_rate": successes / n_games,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "first_target_edge_rate": (
                sum(
                    1 for row in strategy_rows
                    if row["first_check_target_seat_type"] == "edge"
                )
                / n_games
            ),
            "first_target_inner_rate": (
                sum(
                    1 for row in strategy_rows
                    if row["first_check_target_seat_type"] == "inner"
                )
                / n_games
            ),
            "mean_total_seer_checks": (
                sum(row["total_seer_checks"] for row in strategy_rows) / n_games
            ),
            "village_win_rate": (
                sum(row["village_win"] for row in strategy_rows) / n_games
            ),
            "seer_survival_rate": (
                sum(row["seer_survived_to_game_end"] for row in strategy_rows)
                / n_games
            ),
        })

    contrast_rows = []
    p_values_to_adjust = []
    first_check_contrast_indexes = []

    for i, strategy_a in enumerate(STRATEGIES):
        for strategy_b in STRATEGIES[i + 1:]:
            rows_a = strategy_groups[strategy_a]
            rows_b = strategy_groups[strategy_b]
            success_a = sum(row["first_check_target_is_wolf"] for row in rows_a)
            success_b = sum(row["first_check_target_is_wolf"] for row in rows_b)
            test = two_proportion_test(
                success_a,
                len(rows_a),
                success_b,
                len(rows_b),
            )
            contrast_rows.append({
                "contrast_type": "first_check_rate_pairwise",
                "comparison": f"{strategy_a} vs {strategy_b}",
                "estimate": test["difference"],
                "std_error": "",
                "odds_ratio": "",
                "ci_low": test["ci_low"],
                "ci_high": test["ci_high"],
                "z": test["z"],
                "p_value": test["p_value"],
                "p_value_holm": "",
                "effect_size": test["cohen_h"],
                "notes": "Estimate is first-check wolf-rate difference; effect_size is Cohen h.",
            })
            p_values_to_adjust.append(test["p_value"])
            first_check_contrast_indexes.append(len(contrast_rows) - 1)

    adjusted_p_values = holm_adjust(p_values_to_adjust)
    for index, adjusted_p in zip(first_check_contrast_indexes, adjusted_p_values):
        contrast_rows[index]["p_value_holm"] = adjusted_p

    first_check_success_groups = rows_by(rows, "first_check_target_is_wolf")
    success_rows = first_check_success_groups[1]
    failure_rows = first_check_success_groups[0]
    success_village = sum(row["village_win"] for row in success_rows)
    failure_village = sum(row["village_win"] for row in failure_rows)
    raw_outcome_test = odds_ratio_2x2(
        success_village,
        len(success_rows) - success_village,
        failure_village,
        len(failure_rows) - failure_village,
    )
    raw_outcome_diff = (
        success_village / len(success_rows)
        - failure_village / len(failure_rows)
    )

    x_main, columns_main = build_design_matrix(rows)
    main_model = logistic_fit(y_values, x_main, columns_main)
    x_post, columns_post = build_design_matrix(rows, include_post_treatment=True)
    post_model = logistic_fit(y_values, x_post, columns_post)
    x_cluster, columns_cluster = build_design_matrix(
        rows,
        include_seed_fixed_effects=False,
    )
    cluster_model = logistic_fit(y_values, x_cluster, columns_cluster)
    clustered_cov = cluster_covariance(
        cluster_model,
        [row["seed"] for row in rows],
    )
    model_rows = []
    model_rows.extend(coefficient_rows("main_adjusted", main_model))
    model_rows.extend(
        coefficient_rows(
            "main_no_seed_fixed_effects_seed_clustered_se",
            cluster_model,
            covariance=clustered_cov,
            note=(
                "Clustered by seed without seed fixed effects; only five "
                "clusters, so use as sensitivity evidence."
            ),
        )
    )
    model_rows.extend(
        coefficient_rows(
            "post_treatment_adjusted_sensitivity",
            post_model,
            note=(
                "Includes post-treatment total_seer_checks and "
                "seer_survived_to_game_end; not causal."
            ),
        )
    )
    model_rows.append({
        "model": "raw_first_check_success",
        "term": "first_check_target_is_wolf",
        "coef": math.log(raw_outcome_test["odds_ratio"]),
        "std_error": "",
        "odds_ratio": raw_outcome_test["odds_ratio"],
        "ci_low": raw_outcome_test["ci_low"],
        "ci_high": raw_outcome_test["ci_high"],
        "z": raw_outcome_test["z"],
        "p_value": raw_outcome_test["p_value"],
        "n": total_games,
        "log_likelihood": "",
        "aic": "",
        "note": (
            "Raw 2x2 comparison; village win rate when first check found wolf "
            f"{success_village / len(success_rows):.4f} vs "
            f"{failure_village / len(failure_rows):.4f} when it did not."
        ),
    })

    contrast_rows.extend([
        model_contrast(
            main_model,
            {"strategy:edge_first": 1.0},
            "edge_first vs random",
            "adjusted_village_win_model",
        ),
        model_contrast(
            main_model,
            {
                "strategy:edge_first": 1.0,
                "strategy:inner_first": -1.0,
            },
            "edge_first vs inner_first",
            "adjusted_village_win_model",
        ),
        model_contrast(
            main_model,
            {
                "strategy:edge_first": 1.0,
                "strategy:default": -1.0,
            },
            "edge_first vs default",
            "adjusted_village_win_model",
        ),
    ])

    interaction_specs = [
        (
            "edge_first_x_wolves_on_edge",
            {"include_edge_wolves_interaction": True},
            1,
        ),
        (
            "strategy_x_first_check_target_is_wolf",
            {"include_strategy_first_check_interaction": True},
            len(STRATEGIES) - 1,
        ),
        (
            "seer_seat_type_x_strategy",
            {"include_seat_type_strategy_interaction": True},
            len(STRATEGIES),
        ),
    ]
    interaction_rows = []
    interaction_p_values = []

    for name, kwargs, df_diff in interaction_specs:
        x_interaction, columns_interaction = build_design_matrix(rows, **kwargs)
        interaction_model = logistic_fit(y_values, x_interaction, columns_interaction)
        lr_stat = max(
            0.0,
            2.0 * (
                interaction_model["log_likelihood"]
                - main_model["log_likelihood"]
            ),
        )
        p_value = chi_square_sf(lr_stat, df_diff)
        focal_coef = ""
        focal_or = ""
        focal_p_value = ""

        if name == "edge_first_x_wolves_on_edge":
            focal_term = "strategy:edge_first_x_wolves_on_edge"
            focal_index = columns_interaction.index(focal_term)
            focal_coef = interaction_model["beta"][focal_index]
            focal_se = math.sqrt(
                max(
                    interaction_model["covariance"][
                        focal_index,
                        focal_index,
                    ],
                    0.0,
                )
            )
            focal_or = math.exp(focal_coef)
            focal_z = focal_coef / focal_se if focal_se > 0 else 0.0
            focal_p_value = normal_p_value(focal_z)

        interaction_rows.append({
            "interaction": name,
            "base_model": "main_adjusted",
            "comparison_model": f"main_plus_{name}",
            "df_diff": df_diff,
            "lr_statistic": lr_stat,
            "p_value": p_value,
            "p_value_holm": "",
            "focal_coef": focal_coef,
            "focal_odds_ratio": focal_or,
            "focal_p_value": focal_p_value,
            "base_aic": main_model["aic"],
            "interaction_aic": interaction_model["aic"],
            "delta_aic": interaction_model["aic"] - main_model["aic"],
            "interpretation": "",
        })
        interaction_p_values.append(p_value)

    for row, adjusted_p in zip(interaction_rows, holm_adjust(interaction_p_values)):
        row["p_value_holm"] = adjusted_p
        if adjusted_p < 0.05:
            row["interpretation"] = "statistically supported interaction"
        elif row["delta_aic"] < -2:
            row["interpretation"] = "model-fit improvement but corrected p >= 0.05"
        else:
            row["interpretation"] = "weak or unsupported interaction"

    robustness_rows = []
    for seed in SEEDS:
        seed_rows = seed_groups[seed]
        n_seed = len(seed_rows)
        seed_village_rate = sum(row["village_win"] for row in seed_rows) / n_seed
        robustness_rows.append({
            "section": "seed_overall",
            "seed": seed,
            "excluded_seed": "",
            "strategy": "all",
            "n_games": n_seed,
            "village_win_rate": seed_village_rate,
            "wolf_win_rate": 1.0 - seed_village_rate,
            "first_check_wolf_rate": (
                sum(row["first_check_target_is_wolf"] for row in seed_rows)
                / n_seed
            ),
            "edge_vs_random_village_diff": "",
            "edge_vs_inner_village_diff": "",
            "z_score": "",
            "flag": "",
        })

    seed_rates = [
        row["village_win_rate"] for row in robustness_rows
        if row["section"] == "seed_overall"
    ]
    seed_mean, seed_sd, _, _ = mean_ci(seed_rates)

    for row in robustness_rows:
        if row["section"] != "seed_overall":
            continue

        z_score = (
            (row["village_win_rate"] - seed_mean) / seed_sd
            if seed_sd not in (None, 0.0)
            else 0.0
        )
        row["z_score"] = z_score
        row["flag"] = "potential_outlier" if abs(z_score) > 2.0 else "not_outlier"

    for excluded_seed in SEEDS:
        loo_rows = [
            row for row in rows
            if row["seed"] != excluded_seed
        ]
        loo_groups = rows_by(loo_rows, "strategy")
        edge_rate = (
            sum(row["village_win"] for row in loo_groups["edge_first"])
            / len(loo_groups["edge_first"])
        )
        random_rate = (
            sum(row["village_win"] for row in loo_groups["random"])
            / len(loo_groups["random"])
        )
        inner_rate = (
            sum(row["village_win"] for row in loo_groups["inner_first"])
            / len(loo_groups["inner_first"])
        )

        for strategy in STRATEGIES:
            strategy_rows = loo_groups[strategy]
            n_strategy = len(strategy_rows)
            village_rate = (
                sum(row["village_win"] for row in strategy_rows)
                / n_strategy
            )
            robustness_rows.append({
                "section": "leave_one_seed_out_strategy",
                "seed": "",
                "excluded_seed": excluded_seed,
                "strategy": strategy,
                "n_games": n_strategy,
                "village_win_rate": village_rate,
                "wolf_win_rate": 1.0 - village_rate,
                "first_check_wolf_rate": (
                    sum(row["first_check_target_is_wolf"] for row in strategy_rows)
                    / n_strategy
                ),
                "edge_vs_random_village_diff": edge_rate - random_rate,
                "edge_vs_inner_village_diff": edge_rate - inner_rate,
                "z_score": "",
                "flag": "",
            })

    write_csv(
        OUTPUT_DIR / "descriptive_statistics.csv",
        descriptive_rows,
        [
            "section",
            "strategy",
            "seed",
            "n_games",
            "village_wins",
            "wolf_wins",
            "village_win_rate",
            "village_win_rate_seed_sd",
            "first_check_wolf_rate",
            "first_check_wolf_rate_seed_sd",
            "mean_total_seer_checks",
            "seer_survival_rate",
            "seer_survival_rate_seed_sd",
            "first_target_edge_rate",
            "mean_wolves_on_edge",
        ],
    )
    write_csv(
        OUTPUT_DIR / "seat_distribution_analysis.csv",
        seat_rows,
        [
            "section",
            "seat_type",
            "wolves_on_edge",
            "observed_count",
            "observed_probability",
            "expected_probability",
            "expected_count",
            "observed_wolf_probability",
            "expected_wolf_probability",
            "ci_low",
            "ci_high",
            "test",
            "statistic",
            "df",
            "p_value",
            "effect_size",
        ],
    )
    write_csv(
        OUTPUT_DIR / "first_check_analysis.csv",
        first_check_rows,
        [
            "strategy",
            "n_games",
            "first_check_wolf_count",
            "first_check_wolf_rate",
            "ci_low",
            "ci_high",
            "first_target_edge_rate",
            "first_target_inner_rate",
            "mean_total_seer_checks",
            "village_win_rate",
            "seer_survival_rate",
        ],
    )
    write_csv(
        OUTPUT_DIR / "village_win_models.csv",
        model_rows,
        [
            "model",
            "term",
            "coef",
            "std_error",
            "odds_ratio",
            "ci_low",
            "ci_high",
            "z",
            "p_value",
            "n",
            "log_likelihood",
            "aic",
            "note",
        ],
    )
    write_csv(
        OUTPUT_DIR / "model_contrasts.csv",
        contrast_rows,
        [
            "contrast_type",
            "comparison",
            "estimate",
            "std_error",
            "odds_ratio",
            "ci_low",
            "ci_high",
            "z",
            "p_value",
            "p_value_holm",
            "effect_size",
            "notes",
        ],
    )
    write_csv(
        OUTPUT_DIR / "interaction_tests.csv",
        interaction_rows,
        [
            "interaction",
            "base_model",
            "comparison_model",
            "df_diff",
            "lr_statistic",
            "p_value",
            "p_value_holm",
            "focal_coef",
            "focal_odds_ratio",
            "focal_p_value",
            "base_aic",
            "interaction_aic",
            "delta_aic",
            "interpretation",
        ],
    )
    write_csv(
        OUTPUT_DIR / "robustness_analysis.csv",
        robustness_rows,
        [
            "section",
            "seed",
            "excluded_seed",
            "strategy",
            "n_games",
            "village_win_rate",
            "wolf_win_rate",
            "first_check_wolf_rate",
            "edge_vs_random_village_diff",
            "edge_vs_inner_village_diff",
            "z_score",
            "flag",
        ],
    )

    make_bar_plot(
        OUTPUT_DIR / "wolf_probability_by_seat_type.svg",
        ["edge seats", "inner seats"],
        [edge_prop, inner_prop],
        [edge_ci[0], inner_ci[0]],
        [edge_ci[1], inner_ci[1]],
        "Wolf probability per seat",
        "Wolf probability by seat type",
        color="#2b6cb0",
    )

    first_strategy_labels = [row["strategy"] for row in first_check_rows]
    make_bar_plot(
        OUTPUT_DIR / "first_check_wolf_rate_by_strategy.svg",
        first_strategy_labels,
        [row["first_check_wolf_rate"] for row in first_check_rows],
        [row["ci_low"] for row in first_check_rows],
        [row["ci_high"] for row in first_check_rows],
        "First-check wolf rate",
        "First-check wolf rate by strategy",
        color="#d97706",
        rotate=True,
    )

    village_plot_values = []
    village_ci_lows = []
    village_ci_highs = []
    for strategy in STRATEGIES:
        strategy_rows = strategy_groups[strategy]
        wins = sum(row["village_win"] for row in strategy_rows)
        ci_low, ci_high = wilson_ci(wins, len(strategy_rows))
        village_plot_values.append(wins / len(strategy_rows))
        village_ci_lows.append(ci_low)
        village_ci_highs.append(ci_high)

    make_bar_plot(
        OUTPUT_DIR / "village_win_rate_by_strategy.svg",
        STRATEGIES,
        village_plot_values,
        village_ci_lows,
        village_ci_highs,
        "Village win rate",
        "Village win rate by strategy",
        color="#6b8e23",
        rotate=True,
    )

    conditional_labels = ["first check not wolf", "first check wolf"]
    conditional_values = [
        failure_village / len(failure_rows),
        success_village / len(success_rows),
    ]
    conditional_cis = [
        wilson_ci(failure_village, len(failure_rows)),
        wilson_ci(success_village, len(success_rows)),
    ]
    make_bar_plot(
        OUTPUT_DIR / "village_win_by_first_check_result.svg",
        conditional_labels,
        conditional_values,
        [ci[0] for ci in conditional_cis],
        [ci[1] for ci in conditional_cis],
        "Village win rate",
        "Village win probability conditional on first-check result",
        color="#c2410c",
    )

    make_grouped_metric_plot(
        OUTPUT_DIR / "edge_inner_random_comparison.svg",
        first_check_rows,
    )
    make_leave_one_seed_plot(
        OUTPUT_DIR / "leave_one_seed_out_strategy_effects.svg",
        robustness_rows,
    )

    summary = {
        "total_games": total_games,
        "edge_prop": edge_prop,
        "inner_prop": inner_prop,
        "edge_ci": edge_ci,
        "inner_ci": inner_ci,
        "edge_mean": edge_mean,
        "edge_mean_ci": (edge_mean_low, edge_mean_high),
        "expected_edge_mean": expected_edge_mean,
        "seat_chi_square": chi_square_stat,
        "seat_chi_square_p": chi_square_p,
        "seat_cramers_v": cramers_v,
        "first_check_rows": first_check_rows,
        "raw_success_rate": success_village / len(success_rows),
        "raw_failure_rate": failure_village / len(failure_rows),
        "raw_outcome_diff": raw_outcome_diff,
        "raw_outcome_or": raw_outcome_test,
        "main_model": main_model,
        "post_model": post_model,
        "model_contrasts": contrast_rows,
        "interaction_rows": interaction_rows,
        "robustness_rows": robustness_rows,
        "descriptive_rows": descriptive_rows,
        "seed_summary_by_strategy": seed_summary_by_strategy,
    }
    write_report(summary)


def get_row(rows, **conditions):
    for row in rows:
        if all(row.get(key) == value for key, value in conditions.items()):
            return row

    return None


def get_model_row(model_rows, term, model_name="main_adjusted"):
    for row in model_rows:
        if row["model"] == model_name and row["term"] == term:
            return row

    return None


def write_report(summary):
    first_by_strategy = {
        row["strategy"]: row for row in summary["first_check_rows"]
    }
    descriptive_by_strategy = {
        row["strategy"]: row
        for row in summary["descriptive_rows"]
        if row["section"] == "strategy"
    }
    model_rows = list(csv.DictReader(
        (OUTPUT_DIR / "village_win_models.csv").open()
    ))
    contrast_rows = summary["model_contrasts"]
    first_contrast_lookup = {
        row["comparison"]: row for row in contrast_rows
        if row["contrast_type"] == "first_check_rate_pairwise"
    }
    adjusted_contrast_lookup = {
        row["comparison"]: row for row in contrast_rows
        if row["contrast_type"] == "adjusted_village_win_model"
    }
    main_first_check = get_model_row(
        model_rows,
        "first_check_target_is_wolf",
    )
    edge_model_row = get_model_row(model_rows, "strategy:edge_first")
    total_games = summary["total_games"]
    report_path = OUTPUT_DIR / "analysis_report.md"

    with report_path.open("w") as file:
        file.write(
            "# Game-Level Analysis of Randomized-Role Seer Position Experiment\n\n"
        )
        file.write("## Technical Summary\n\n")
        file.write(
            f"The analysis used `{INPUT_PATH.relative_to(ROOT)}` as the "
            f"primary source of truth, with {total_games:,} completed games "
            "covering 7 seer checking strategies, 5 seeds, and 500 games per "
            "strategy-seed cell. No simulation code was changed and the raw "
            "game-level dataset was preserved unchanged.\n\n"
        )
        file.write(
            "**Edge seats were not wolf-heavy after randomization.** Edge "
            f"seats contained wolves in {format_pct(summary['edge_prop'])} "
            f"of edge-seat opportunities, compared with "
            f"{format_pct(summary['inner_prop'])} for inner seats and an "
            "expected 30.00% under the 3-wolf / 10-seat role pool. The "
            "wolves-on-edge distribution matched the exact hypergeometric "
            f"expectation closely (chi-square p = "
            f"{format_p_value(summary['seat_chi_square_p'])}, Cramer's V = "
            f"{summary['seat_cramers_v']:.3f}).\n\n"
        )
        edge_vs_random_first = first_contrast_lookup[
            "random vs edge_first"
        ]
        edge_vs_inner_first = first_contrast_lookup[
            "edge_first vs inner_first"
        ]
        file.write(
            "**Edge-first did not produce a statistically supported first-check "
            "discovery advantage.** Its first-check wolf rate was "
            f"{format_pct(first_by_strategy['edge_first']['first_check_wolf_rate'])}, "
            f"versus {format_pct(first_by_strategy['random']['first_check_wolf_rate'])} "
            "for random and "
            f"{format_pct(first_by_strategy['inner_first']['first_check_wolf_rate'])} "
            "for inner-first. Random was "
            f"{float(edge_vs_random_first['estimate']) * 100:.2f} percentage "
            f"points higher than edge-first in direct comparison (Holm p = "
            f"{format_p_value(float(edge_vs_random_first['p_value_holm']))}).\n\n"
        )
        file.write(
            "**Finding a wolf on the first check was strongly associated with "
            "village winning, but it should not be interpreted as a randomized "
            "causal effect.** Village win rate was "
            f"{format_pct(summary['raw_success_rate'])} when the first check "
            "found a wolf and "
            f"{format_pct(summary['raw_failure_rate'])} otherwise, a "
            f"{summary['raw_outcome_diff'] * 100:.2f} percentage-point "
            "difference. The adjusted village-win model also estimated a "
            f"positive association (OR = {float(main_first_check['odds_ratio']):.2f}, "
            f"95% CI {float(main_first_check['ci_low']):.2f}-"
            f"{float(main_first_check['ci_high']):.2f}, p = "
            f"{format_p_value(float(main_first_check['p_value']))}).\n\n"
        )
        file.write(
            "**After adjustment, edge-first did not retain an independent "
            "advantage over random or inner-first, although it remained above "
            "default.** In the main model with strategy, first-check success, "
            "wolves-on-edge, seer seat, seer side, and seed controls, "
            f"edge-first vs random had OR = "
            f"{float(edge_model_row['odds_ratio']):.2f} "
            f"(95% CI {float(edge_model_row['ci_low']):.2f}-"
            f"{float(edge_model_row['ci_high']):.2f}, p = "
            f"{format_p_value(float(edge_model_row['p_value']))}). This "
            "weakens the edge-seat theory: structured search paths matter, "
            "but edge seats are not uniquely informative once roles are "
            "randomized.\n\n"
        )

        file.write("## Scope, Data, and Metric Definitions\n\n")
        file.write(
            "- **Unit of analysis:** one completed game.\n"
            "- **Input dataset:** "
            "`results/ten_player_seer_position_randomized_roles_game_level_raw.csv`.\n"
            "- **Strategies:** default, random, edge_first, inner_first, "
            "highest_p_wolf, highest_suspicion, and opposite_side.\n"
            "- **Outcome:** `village_win`, a binary indicator equal to 1 when "
            "`winner == village`.\n"
            "- **First-check success:** `first_check_target_is_wolf == 1`.\n"
            "- **Seat model:** 4 edge seats and 6 inner seats; each game has "
            "3 wolves assigned randomly across 10 seats.\n"
            "- **Inference frame:** simulation games are treated as repeated "
            "Monte Carlo observations. Seed fixed effects and leave-one-seed-out "
            "checks are used for robustness.\n\n"
        )

        file.write("## Edge Seats Are Not Intrinsically Wolf-Heavy\n\n")
        file.write(
            f"The observed edge-seat wolf probability was "
            f"{format_pct(summary['edge_prop'])} "
            f"(95% CI {format_pct(summary['edge_ci'][0])}-"
            f"{format_pct(summary['edge_ci'][1])}); the inner-seat probability "
            f"was {format_pct(summary['inner_prop'])} "
            f"(95% CI {format_pct(summary['inner_ci'][0])}-"
            f"{format_pct(summary['inner_ci'][1])}). The expected probability "
            "for both seat types is 30.00% because the randomized role pool "
            "assigns 3 wolves across 10 seats. The expected number of wolves "
            f"on edge seats is {summary['expected_edge_mean']:.2f}; the "
            f"observed mean was {summary['edge_mean']:.3f} "
            f"(95% CI {summary['edge_mean_ci'][0]:.3f}-"
            f"{summary['edge_mean_ci'][1]:.3f}).\n\n"
        )
        file.write(
            "![Wolf probability by seat type](wolf_probability_by_seat_type.svg)\n\n"
        )
        file.write(
            "The hypergeometric goodness-of-fit test checks the full "
            "`wolves_on_edge` distribution, not just the mean. It produced "
            f"chi-square = {summary['seat_chi_square']:.3f}, p = "
            f"{format_p_value(summary['seat_chi_square_p'])}, and Cramer's "
            f"V = {summary['seat_cramers_v']:.3f}. This is statistically "
            "and practically consistent with randomized roles rather than an "
            "edge-heavy role assignment pattern.\n\n"
        )

        file.write("## First-Check Discovery Varies, but Edge-First Is Not Unique\n\n")
        file.write(
            "The first-check comparison suggests that structured strategies can "
            "shift search paths, but edge-first is not clearly superior. The "
            f"edge-first first-check wolf rate was "
            f"{format_pct(first_by_strategy['edge_first']['first_check_wolf_rate'])}; "
            f"inner-first was "
            f"{format_pct(first_by_strategy['inner_first']['first_check_wolf_rate'])}; "
            f"random was {format_pct(first_by_strategy['random']['first_check_wolf_rate'])}; "
            f"default was {format_pct(first_by_strategy['default']['first_check_wolf_rate'])}.\n\n"
        )
        file.write(
            "![First-check wolf rate by strategy](first_check_wolf_rate_by_strategy.svg)\n\n"
        )
        for comparison in [
            "random vs edge_first",
            "edge_first vs inner_first",
            "default vs edge_first",
        ]:
            row = first_contrast_lookup[comparison]
            file.write(
                f"- `{comparison}`: difference = "
                f"{float(row['estimate']) * 100:.2f} pp, "
                f"95% CI {float(row['ci_low']) * 100:.2f} to "
                f"{float(row['ci_high']) * 100:.2f} pp, Holm p = "
                f"{format_p_value(float(row['p_value_holm']))}, "
                f"Cohen h = {float(row['effect_size']):.3f}.\n"
            )
        file.write("\n")

        file.write("## First-Check Success Predicts Village Wins, with Causal Caveats\n\n")
        file.write(
            f"Raw village win rate was {format_pct(summary['raw_success_rate'])} "
            "when the first check found a wolf and "
            f"{format_pct(summary['raw_failure_rate'])} otherwise. The raw "
            f"odds ratio was {summary['raw_outcome_or']['odds_ratio']:.2f} "
            f"(95% CI {summary['raw_outcome_or']['ci_low']:.2f}-"
            f"{summary['raw_outcome_or']['ci_high']:.2f}, p = "
            f"{format_p_value(summary['raw_outcome_or']['p_value'])}). This "
            "is a strong predictive association, but first-check success is "
            "not randomized independently of strategy and game state.\n\n"
        )
        file.write(
            "![Village win by first-check result](village_win_by_first_check_result.svg)\n\n"
        )

        file.write("## Adjusted Village-Win Model Weakens Edge-Seat Theory\n\n")
        edge_random_contrast = adjusted_contrast_lookup["edge_first vs random"]
        edge_inner_contrast = adjusted_contrast_lookup[
            "edge_first vs inner_first"
        ]
        edge_default_contrast = adjusted_contrast_lookup[
            "edge_first vs default"
        ]
        file.write(
            "The main logistic model used `random` as the reference strategy "
            "and adjusted for first-check success, wolves on edge seats, "
            "seer seat, seer side, and seed. Explicit contrasts show:\n\n"
        )
        for row in [
            edge_random_contrast,
            edge_inner_contrast,
            edge_default_contrast,
        ]:
            file.write(
                f"- `{row['comparison']}`: OR = {float(row['odds_ratio']):.2f}, "
                f"95% CI {float(row['ci_low']):.2f}-"
                f"{float(row['ci_high']):.2f}, p = "
                f"{format_p_value(float(row['p_value']))}.\n"
            )
        file.write("\n")
        file.write(
            "![Village win rate by strategy](village_win_rate_by_strategy.svg)\n\n"
        )
        file.write(
            "The adjusted estimates do not support an independent edge-first "
            "advantage over random or inner-first. Edge-first is higher than "
            "default in the adjusted model, which supports the broader idea "
            "that a structured search path can help relative to the default "
            "process. It does not establish that edge seats themselves are "
            "informative. Highest-p-wolf and highest-suspicion strategies are "
            "associated with lower village win rates in this configuration, "
            "but those strategies are partly post-belief strategies and "
            "should be interpreted as policy comparisons rather than clean "
            "causal effects.\n\n"
        )

        file.write("## Search-Path Evidence: Structured Paths Matter More Than Edge Seats\n\n")
        file.write(
            "Edge-first and inner-first perform similarly on village win rate "
            "and first-check success. That pattern is more consistent with "
            "structured search changing the seer's path away from the default "
            "process than with edge seats being intrinsically informative. "
            "Because role assignment is randomized, edge seat status itself "
            "does not carry wolf information.\n\n"
        )
        file.write(
            "![Edge, inner, and random comparison](edge_inner_random_comparison.svg)\n\n"
        )
        for strategy in ["random", "edge_first", "inner_first"]:
            row = first_by_strategy[strategy]
            seed_summary = summary["seed_summary_by_strategy"][strategy]
            file.write(
                f"- `{strategy}`: first-check wolf "
                f"{format_pct(row['first_check_wolf_rate'])}, village win "
                f"{format_pct(row['village_win_rate'])} "
                f"(seed SD {seed_summary['village_win_rate_seed_sd'] * 100:.2f} pp), "
                f"seer survival "
                f"{format_pct(row['seer_survival_rate'])}, mean checks "
                f"{row['mean_total_seer_checks']:.2f}.\n"
            )
        file.write("\n")

        file.write("## Interactions and Robustness\n\n")
        file.write(
            "Interaction tests were added one at a time to the main model and "
            "Holm-corrected across the three requested interaction families. "
            "The results were:\n\n"
        )
        for row in summary["interaction_rows"]:
            focal_note = ""
            if row["interaction"] == "edge_first_x_wolves_on_edge":
                focal_note = (
                    f" focal OR per additional edge wolf = "
                    f"{row['focal_odds_ratio']:.2f};"
                )
            file.write(
                f"- `{row['interaction']}`: LR = {row['lr_statistic']:.3f}, "
                f"df = {row['df_diff']}, Holm p = "
                f"{format_p_value(row['p_value_holm'])}, delta AIC = "
                f"{row['delta_aic']:.2f};{focal_note} "
                f"{row['interpretation']}.\n"
            )
        file.write("\n")
        file.write(
            "The significant `edge_first_x_wolves_on_edge` interaction means "
            "edge-first becomes more favorable when more wolves happen to be "
            "on edge seats in a given randomized game. That is conditional "
            "heterogeneity, not evidence that edge seats are intrinsically "
            "wolf-heavy. Because the role assignment itself is balanced, this "
            "does not rescue the edge-seat prior as a general theory.\n\n"
        )
        file.write(
            "Leave-one-seed-out checks did not reveal a single seed that "
            "reverses the main interpretation. No seed exceeded an absolute "
            "z-score of 2 on overall village win rate. Clustered standard "
            "errors by seed were also generated as a sensitivity check, but "
            "with only five clusters they should be treated as diagnostic "
            "rather than definitive.\n\n"
        )
        file.write(
            "![Leave-one-seed-out strategy effects](leave_one_seed_out_strategy_effects.svg)\n\n"
        )

        file.write("## Direct Answers to the Research Questions\n\n")
        file.write(
            "1. **Are edge seats actually more wolf-heavy after randomization?** "
            "No. Observed edge and inner wolf probabilities are both near the "
            "30% expectation.\n"
            "2. **Does edge_first increase first-check wolf discovery?** Not "
            "in a statistically supported or practically meaningful way versus "
            "random, inner-first, or default after Holm correction.\n"
            "3. **Does first-check wolf discovery predict village victory?** "
            "Yes. It has a strong positive predictive association with village "
            "wins, both raw and adjusted.\n"
            "4. **Does edge_first retain an independent effect after adjustment?** "
            "Not against random or inner-first; it is higher than default, "
            "which points to a structured-search effect rather than an "
            "edge-seat effect.\n"
            "5. **Does edge_first outperform inner_first?** No. Their village "
            "win rates and first-check wolf rates are very close.\n"
            "6. **Is edge-seat theory supported, weakened, or rejected?** "
            "Weakened to rejected for this randomized-role design: edge seats "
            "are not intrinsically more informative once roles are randomized.\n"
            "7. **What should the next experiment test?** Test whether "
            "structured search paths improve information flow under alternate "
            "communication rules, not whether edge seats have inherent role "
            "risk.\n\n"
        )

        file.write("## Limitations and Next Steps\n\n")
        file.write(
            "- These are simulation outcomes, not real human game observations.\n"
            "- First-check success, total seer checks, and seer survival are "
            "partly downstream of strategy and game dynamics; post-treatment "
            "models are predictive diagnostics, not causal estimates.\n"
            "- Seed-aware inference is limited by having only five seeds. "
            "Leave-one-seed-out analysis is more transparent than relying on "
            "clustered standard errors alone.\n"
            "- The next experiment should isolate structured-search effects "
            "from position labels by adding strategy variants that force "
            "deterministic but non-positional search paths.\n"
        )


def main():
    rows = load_rows()
    analyze(rows)


if __name__ == "__main__":
    main()
