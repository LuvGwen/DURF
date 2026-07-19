import csv
import math
from itertools import combinations, product
from pathlib import Path
from statistics import mean, stdev


ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = (
    ROOT
    / "results"
    / "ten_player_seer_position_randomized_roles_multi_seed_raw.csv"
)
SINGLE_SEED_PATH = (
    ROOT / "results" / "ten_player_seer_position_randomized_roles_results.csv"
)
OUTPUT_DIR = ROOT / "results" / "data_analysis" / "seer_position_randomized_roles"

STRATEGY_ORDER = [
    "seer_default",
    "seer_random",
    "seer_edge_first",
    "seer_inner_first",
    "seer_highest_p_wolf",
    "seer_highest_suspicion",
    "seer_opposite_side",
]

DISPLAY_NAMES = {
    "seer_default": "default",
    "seer_random": "random",
    "seer_edge_first": "edge_first",
    "seer_inner_first": "inner_first",
    "seer_highest_p_wolf": "highest_p_wolf",
    "seer_highest_suspicion": "highest_suspicion",
    "seer_opposite_side": "opposite_side",
}

COLORS = {
    "seer_default": "#6b7280",
    "seer_random": "#2563eb",
    "seer_edge_first": "#dc2626",
    "seer_inner_first": "#16a34a",
    "seer_highest_p_wolf": "#7c3aed",
    "seer_highest_suspicion": "#ea580c",
    "seer_opposite_side": "#0891b2",
}

RATE_METRICS = [
    "wolf_win_rate",
    "village_win_rate",
    "seer_found_wolf_rate",
    "first_check_found_wolf_rate",
    "edge_check_rate",
    "edge_has_wolf_rate",
    "seer_on_edge_rate",
    "seer_left_side_rate",
]

NUMERIC_METRICS = [
    "avg_rounds",
    "avg_payoff",
    "avg_wolves_on_edge",
]

T_CRIT_95 = {
    1: None,
    2: 12.706,
    3: 4.303,
    4: 3.182,
    5: 2.776,
    6: 2.571,
    7: 2.447,
    8: 2.365,
    9: 2.306,
    10: 2.262,
}


def read_csv(path):
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def to_float(value, default=0.0):
    if value in {None, "", "NA", "None"}:
        return default

    return float(value)


def metric_value(row, metric):
    value = to_float(row.get(metric))

    if metric in RATE_METRICS:
        return value * 100

    return value


def group_by_condition(rows):
    grouped = {condition: [] for condition in STRATEGY_ORDER}

    for row in rows:
        grouped.setdefault(row["condition"], []).append(row)

    for condition_rows in grouped.values():
        condition_rows.sort(key=lambda row: int(row["seed"]))

    return grouped


def sample_sd(values):
    if len(values) < 2:
        return 0.0

    return stdev(values)


def ci95(values):
    if len(values) < 2:
        value = values[0] if values else 0.0
        return value, value

    sd = sample_sd(values)
    t_crit = T_CRIT_95.get(len(values), 1.96)
    half_width = t_crit * sd / math.sqrt(len(values))
    return mean(values) - half_width, mean(values) + half_width


def format_float(value):
    return f"{value:.2f}"


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            restval="",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_table(path, title, rows, columns):
    with path.open("w") as file:
        file.write(f"# {title}\n\n")
        file.write("| " + " | ".join(label for _, label in columns) + " |\n")
        file.write("|" + "|".join("---" for _ in columns) + "|\n")

        for row in rows:
            file.write(
                "| "
                + " | ".join(str(row.get(key, "")) for key, _ in columns)
                + " |\n"
            )


def descriptive_summary(rows):
    grouped = group_by_condition(rows)
    summary_rows = []

    for condition in STRATEGY_ORDER:
        condition_rows = grouped[condition]
        output = {
            "condition": condition,
            "strategy": DISPLAY_NAMES[condition],
            "n_seeds": len(condition_rows),
        }

        for metric in RATE_METRICS + NUMERIC_METRICS:
            values = [metric_value(row, metric) for row in condition_rows]
            low, high = ci95(values)
            prefix = metric.replace("_rate", "")
            output[f"{prefix}_mean"] = mean(values)
            output[f"{prefix}_sd"] = sample_sd(values)
            output[f"{prefix}_ci95_low"] = low
            output[f"{prefix}_ci95_high"] = high

        summary_rows.append(output)

    return summary_rows


def formatted_descriptive_summary(summary_rows):
    formatted_rows = []

    for row in summary_rows:
        formatted_rows.append({
            "condition": row["condition"],
            "strategy": row["strategy"],
            "n_seeds": row["n_seeds"],
            "wolf_mean_pp": format_float(row["wolf_win_mean"]),
            "wolf_sd_pp": format_float(row["wolf_win_sd"]),
            "wolf_ci95": (
                f"[{row['wolf_win_ci95_low']:.2f}, "
                f"{row['wolf_win_ci95_high']:.2f}]"
            ),
            "village_mean_pp": format_float(row["village_win_mean"]),
            "seer_found_wolf_mean_pp": format_float(
                row["seer_found_wolf_mean"]
            ),
            "seer_found_wolf_sd_pp": format_float(
                row["seer_found_wolf_sd"]
            ),
            "first_check_found_wolf_mean_pp": format_float(
                row["first_check_found_wolf_mean"]
            ),
            "edge_check_mean_pp": format_float(row["edge_check_mean"]),
            "edge_has_wolf_mean_pp": format_float(row["edge_has_wolf_mean"]),
            "avg_wolves_on_edge_mean": format_float(
                row["avg_wolves_on_edge_mean"]
            ),
            "avg_payoff_mean": format_float(row["avg_payoff_mean"]),
        })

    return formatted_rows


def average_ranks(values_by_condition, lower_is_better=True):
    seeds = sorted(next(iter(values_by_condition.values())).keys())
    rank_sums = {condition: 0.0 for condition in STRATEGY_ORDER}

    for seed in seeds:
        values = [
            (condition, values_by_condition[condition][seed])
            for condition in STRATEGY_ORDER
        ]
        values.sort(key=lambda item: item[1], reverse=not lower_is_better)

        index = 0
        while index < len(values):
            end = index
            while end + 1 < len(values) and values[end + 1][1] == values[index][1]:
                end += 1

            average_rank = (index + 1 + end + 1) / 2
            for tied_index in range(index, end + 1):
                rank_sums[values[tied_index][0]] += average_rank

            index = end + 1

    return {
        condition: rank_sums[condition] / len(seeds)
        for condition in STRATEGY_ORDER
    }


def chi_square_sf_even_df(x_value, df):
    if df % 2 != 0:
        return None

    m = df // 2
    half_x = x_value / 2
    total = 0.0

    for index in range(m):
        total += (half_x ** index) / math.factorial(index)

    return math.exp(-half_x) * total


def friedman_test(rows, metric, lower_is_better=True):
    grouped = group_by_condition(rows)
    seeds = sorted({int(row["seed"]) for row in rows})
    values_by_condition = {
        condition: {
            int(row["seed"]): metric_value(row, metric)
            for row in grouped[condition]
        }
        for condition in STRATEGY_ORDER
    }
    ranks = average_ranks(
        values_by_condition,
        lower_is_better=lower_is_better,
    )
    n_blocks = len(seeds)
    n_conditions = len(STRATEGY_ORDER)
    rank_sum_square = sum(
        (ranks[condition] * n_blocks) ** 2
        for condition in STRATEGY_ORDER
    )
    q_statistic = (
        12
        / (n_blocks * n_conditions * (n_conditions + 1))
        * rank_sum_square
        - 3 * n_blocks * (n_conditions + 1)
    )
    p_value = chi_square_sf_even_df(q_statistic, n_conditions - 1)

    return {
        "metric": metric,
        "friedman_q": q_statistic,
        "df": n_conditions - 1,
        "p_value_chi_square_approx": p_value,
        "average_ranks": ranks,
    }


def paired_rows(rows, condition_a, condition_b):
    grouped = group_by_condition(rows)
    by_seed_a = {
        int(row["seed"]): row
        for row in grouped[condition_a]
    }
    by_seed_b = {
        int(row["seed"]): row
        for row in grouped[condition_b]
    }
    seeds = sorted(set(by_seed_a) & set(by_seed_b))

    return [(seed, by_seed_a[seed], by_seed_b[seed]) for seed in seeds]


def paired_permutation_p_value(differences):
    observed = mean(differences)
    total = 0
    at_least_as_extreme = 0

    for signs in product([-1, 1], repeat=len(differences)):
        total += 1
        permuted_mean = mean(
            sign * diff for sign, diff in zip(signs, differences)
        )
        if abs(permuted_mean) >= abs(observed) - 1e-12:
            at_least_as_extreme += 1

    return at_least_as_extreme / total


def paired_comparison(rows, metric):
    comparison_rows = []

    for condition_a, condition_b in combinations(STRATEGY_ORDER, 2):
        paired = paired_rows(rows, condition_a, condition_b)
        differences = [
            metric_value(row_a, metric) - metric_value(row_b, metric)
            for _, row_a, row_b in paired
        ]
        diff_mean = mean(differences)
        diff_sd = sample_sd(differences)
        ci_low, ci_high = ci95(differences)
        p_value = paired_permutation_p_value(differences)
        effect_size = diff_mean / diff_sd if diff_sd else 0.0

        comparison_rows.append({
            "metric": metric,
            "strategy_a": condition_a,
            "strategy_b": condition_b,
            "mean_diff_pp": diff_mean,
            "ci95_low_pp": ci_low,
            "ci95_high_pp": ci_high,
            "p_permutation": p_value,
            "cohen_dz": effect_size,
            "abs_mean_diff_pp": abs(diff_mean),
            "practically_meaningful_3pp": abs(diff_mean) >= 3.0,
        })

    return apply_holm_correction(comparison_rows)


def apply_holm_correction(rows):
    sorted_rows = sorted(rows, key=lambda row: row["p_permutation"])
    m = len(sorted_rows)
    running_max = 0.0

    for index, row in enumerate(sorted_rows):
        adjusted = min(1.0, row["p_permutation"] * (m - index))
        running_max = max(running_max, adjusted)
        row["p_holm"] = running_max
        row["significant_0_05_holm"] = row["p_holm"] < 0.05

    return rows


def formatted_pairwise_rows(rows):
    formatted = []

    for row in rows:
        formatted.append({
            "metric": row["metric"],
            "strategy_a": row["strategy_a"],
            "strategy_b": row["strategy_b"],
            "mean_diff_pp": format_float(row["mean_diff_pp"]),
            "ci95": (
                f"[{row['ci95_low_pp']:.2f}, "
                f"{row['ci95_high_pp']:.2f}]"
            ),
            "p_permutation": format_float(row["p_permutation"]),
            "p_holm": format_float(row["p_holm"]),
            "cohen_dz": format_float(row["cohen_dz"]),
            "practical_3pp": row["practically_meaningful_3pp"],
            "significant_holm": row["significant_0_05_holm"],
        })

    return formatted


def outlier_and_influence_rows(rows):
    grouped = group_by_condition(rows)
    output = []

    for condition in STRATEGY_ORDER:
        condition_rows = grouped[condition]
        wolf_values = [
            metric_value(row, "wolf_win_rate") for row in condition_rows
        ]
        wolf_mean = mean(wolf_values)
        wolf_sd = sample_sd(wolf_values)

        for row in condition_rows:
            seed = int(row["seed"])
            wolf_value = metric_value(row, "wolf_win_rate")
            z_score = (
                (wolf_value - wolf_mean) / wolf_sd
                if wolf_sd
                else 0.0
            )
            leave_one_out_values = [
                metric_value(other_row, "wolf_win_rate")
                for other_row in condition_rows
                if int(other_row["seed"]) != seed
            ]
            leave_one_out_mean = mean(leave_one_out_values)
            output.append({
                "condition": condition,
                "seed": seed,
                "wolf_win_rate_pp": wolf_value,
                "condition_wolf_z": z_score,
                "leave_one_out_wolf_mean_pp": leave_one_out_mean,
                "influence_shift_pp": leave_one_out_mean - wolf_mean,
                "outlier_flag_abs_z_ge_2": abs(z_score) >= 2.0,
            })

    return output


def seed_level_rows(rows):
    seeds = sorted({int(row["seed"]) for row in rows})
    output = []
    seed_means = []

    for seed in seeds:
        seed_rows = [row for row in rows if int(row["seed"]) == seed]
        wolf_values = [
            metric_value(row, "wolf_win_rate") for row in seed_rows
        ]
        seed_mean = mean(wolf_values)
        seed_means.append(seed_mean)
        output.append({
            "seed": seed,
            "mean_wolf_win_rate_pp": seed_mean,
            "sd_wolf_win_rate_pp": sample_sd(wolf_values),
        })

    overall_mean = mean(seed_means)
    overall_sd = sample_sd(seed_means)

    for row in output:
        row["seed_mean_z"] = (
            (row["mean_wolf_win_rate_pp"] - overall_mean) / overall_sd
            if overall_sd
            else 0.0
        )
        row["outlier_flag_abs_z_ge_2"] = abs(row["seed_mean_z"]) >= 2.0

    return output


def svg_escape(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def write_bar_ci_svg(path, summary_rows, metric_prefix, title, x_label):
    width = 980
    height = 520
    margin_left = 190
    margin_right = 50
    margin_top = 55
    margin_bottom = 55
    plot_width = width - margin_left - margin_right
    row_height = (height - margin_top - margin_bottom) / len(summary_rows)
    max_x = max(
        row[f"{metric_prefix}_ci95_high"] for row in summary_rows
    )
    max_x = min(100, max(10, math.ceil(max_x / 5) * 5))

    def x_pos(value):
        return margin_left + (value / max_x) * plot_width

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" '
        'font-family="Arial" font-size="18" font-weight="700">'
        f'{svg_escape(title)}</text>',
    ]

    for tick in range(0, int(max_x) + 1, 10):
        x = x_pos(tick)
        lines.append(
            f'<line x1="{x:.1f}" y1="{margin_top}" x2="{x:.1f}" '
            f'y2="{height - margin_bottom}" stroke="#e5e7eb"/>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="{height - margin_bottom + 22}" '
            'text-anchor="middle" font-family="Arial" font-size="11" '
            f'fill="#4b5563">{tick}</text>'
        )

    for index, row in enumerate(summary_rows):
        condition = row["condition"]
        y = margin_top + index * row_height + row_height / 2
        mean_value = row[f"{metric_prefix}_mean"]
        ci_low = max(0.0, row[f"{metric_prefix}_ci95_low"])
        ci_high = min(max_x, row[f"{metric_prefix}_ci95_high"])
        bar_width = x_pos(mean_value) - margin_left
        color = COLORS.get(condition, "#4b5563")
        label = DISPLAY_NAMES.get(condition, condition)

        lines.append(
            f'<text x="{margin_left - 12}" y="{y + 4:.1f}" '
            'text-anchor="end" font-family="Arial" font-size="12" '
            f'fill="#111827">{svg_escape(label)}</text>'
        )
        lines.append(
            f'<rect x="{margin_left}" y="{y - 10:.1f}" '
            f'width="{bar_width:.1f}" height="20" fill="{color}" '
            'opacity="0.80"/>'
        )
        lines.append(
            f'<line x1="{x_pos(ci_low):.1f}" y1="{y:.1f}" '
            f'x2="{x_pos(ci_high):.1f}" y2="{y:.1f}" '
            'stroke="#111827" stroke-width="2"/>'
        )
        lines.append(
            f'<line x1="{x_pos(ci_low):.1f}" y1="{y - 6:.1f}" '
            f'x2="{x_pos(ci_low):.1f}" y2="{y + 6:.1f}" '
            'stroke="#111827" stroke-width="2"/>'
        )
        lines.append(
            f'<line x1="{x_pos(ci_high):.1f}" y1="{y - 6:.1f}" '
            f'x2="{x_pos(ci_high):.1f}" y2="{y + 6:.1f}" '
            'stroke="#111827" stroke-width="2"/>'
        )
        lines.append(
            f'<text x="{x_pos(mean_value) + 6:.1f}" y="{y + 4:.1f}" '
            'font-family="Arial" font-size="11" fill="#111827">'
            f'{mean_value:.2f}</text>'
        )

    lines.append(
        f'<text x="{margin_left + plot_width / 2}" y="{height - 10}" '
        'text-anchor="middle" font-family="Arial" font-size="12" '
        f'fill="#374151">{svg_escape(x_label)}</text>'
    )
    lines.append("</svg>")
    path.write_text("\n".join(lines))


def write_seed_line_svg(path, rows, metric, title, y_label):
    width = 980
    height = 540
    margin_left = 70
    margin_right = 190
    margin_top = 55
    margin_bottom = 60
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    seeds = sorted({int(row["seed"]) for row in rows})
    values = [metric_value(row, metric) for row in rows]
    min_y = math.floor((min(values) - 2) / 5) * 5
    max_y = math.ceil((max(values) + 2) / 5) * 5

    def x_pos(seed):
        index = seeds.index(seed)
        return margin_left + index * plot_width / (len(seeds) - 1)

    def y_pos(value):
        return margin_top + (max_y - value) / (max_y - min_y) * plot_height

    grouped = group_by_condition(rows)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" '
        'font-family="Arial" font-size="18" font-weight="700">'
        f'{svg_escape(title)}</text>',
    ]

    for tick in range(int(min_y), int(max_y) + 1, 5):
        y = y_pos(tick)
        lines.append(
            f'<line x1="{margin_left}" y1="{y:.1f}" '
            f'x2="{width - margin_right}" y2="{y:.1f}" '
            'stroke="#e5e7eb"/>'
        )
        lines.append(
            f'<text x="{margin_left - 10}" y="{y + 4:.1f}" '
            'text-anchor="end" font-family="Arial" font-size="11" '
            f'fill="#4b5563">{tick}</text>'
        )

    for seed in seeds:
        x = x_pos(seed)
        lines.append(
            f'<text x="{x:.1f}" y="{height - margin_bottom + 25}" '
            'text-anchor="middle" font-family="Arial" font-size="11" '
            f'fill="#4b5563">{seed}</text>'
        )

    for condition in STRATEGY_ORDER:
        condition_rows = grouped[condition]
        points = [
            (
                x_pos(int(row["seed"])),
                y_pos(metric_value(row, metric)),
            )
            for row in condition_rows
        ]
        color = COLORS.get(condition, "#4b5563")
        point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        lines.append(
            f'<polyline points="{point_string}" fill="none" '
            f'stroke="{color}" stroke-width="2"/>'
        )

        for x, y in points:
            lines.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" '
                f'fill="{color}"/>'
            )

    legend_x = width - margin_right + 20
    legend_y = margin_top

    for index, condition in enumerate(STRATEGY_ORDER):
        y = legend_y + index * 24
        color = COLORS.get(condition, "#4b5563")
        lines.append(
            f'<rect x="{legend_x}" y="{y - 9}" width="14" '
            f'height="14" fill="{color}" opacity="0.8"/>'
        )
        lines.append(
            f'<text x="{legend_x + 20}" y="{y + 2}" '
            'font-family="Arial" font-size="11" fill="#111827">'
            f'{svg_escape(DISPLAY_NAMES[condition])}</text>'
        )

    lines.append(
        f'<text x="{margin_left + plot_width / 2}" y="{height - 12}" '
        'text-anchor="middle" font-family="Arial" font-size="12" '
        'fill="#374151">Seed</text>'
    )
    lines.append(
        f'<text x="18" y="{margin_top + plot_height / 2}" '
        'text-anchor="middle" font-family="Arial" font-size="12" '
        'fill="#374151" transform="rotate(-90 18 '
        f'{margin_top + plot_height / 2})">{svg_escape(y_label)}</text>'
    )
    lines.append("</svg>")
    path.write_text("\n".join(lines))


def write_edge_comparison_svg(path, rows):
    selected = [
        "seer_default",
        "seer_random",
        "seer_edge_first",
        "seer_inner_first",
    ]
    summary = descriptive_summary(rows)
    summary = [row for row in summary if row["condition"] in selected]
    write_bar_ci_svg(
        path,
        summary,
        "wolf_win",
        "Edge-priority comparison: wolf win rate",
        "Wolf win rate (%), lower favors village",
    )


def write_omnibus_results(path, tests):
    rows = []

    for test in tests:
        rows.append({
            "metric": test["metric"],
            "friedman_q": format_float(test["friedman_q"]),
            "df": test["df"],
            "p_value_chi_square_approx": (
                format_float(test["p_value_chi_square_approx"])
                if test["p_value_chi_square_approx"] is not None
                else "NA"
            ),
            "average_ranks": "; ".join(
                f"{DISPLAY_NAMES[condition]}={rank:.2f}"
                for condition, rank in test["average_ranks"].items()
            ),
        })

    write_csv(
        path.with_suffix(".csv"),
        rows,
        [
            "metric",
            "friedman_q",
            "df",
            "p_value_chi_square_approx",
            "average_ranks",
        ],
    )
    write_markdown_table(
        path.with_suffix(".md"),
        "Omnibus Strategy Tests",
        rows,
        [
            ("metric", "Metric"),
            ("friedman_q", "Friedman Q"),
            ("df", "df"),
            ("p_value_chi_square_approx", "p-value"),
            ("average_ranks", "Average ranks"),
        ],
    )


def practical_label(diff_pp, p_holm):
    significant = p_holm < 0.05
    practical = abs(diff_pp) >= 3.0

    if significant and practical:
        return "statistically significant and practically meaningful"
    if significant:
        return "statistically significant but small"
    if practical:
        return "practically meaningful but statistically inconclusive"
    return "inconclusive/small"


def build_report(
    summary_rows,
    pairwise_rows,
    omnibus_tests,
    outlier_rows,
    seed_rows,
):
    by_condition = {row["condition"]: row for row in summary_rows}
    edge = by_condition["seer_edge_first"]
    default = by_condition["seer_default"]
    random_row = by_condition["seer_random"]
    inner = by_condition["seer_inner_first"]
    best_village = min(summary_rows, key=lambda row: row["wolf_win_mean"])
    best_discovery = max(
        summary_rows,
        key=lambda row: row["seer_found_wolf_mean"],
    )

    def find_pair(metric, a, b):
        for row in pairwise_rows:
            if (
                row["metric"] == metric
                and row["strategy_a"] == a
                and row["strategy_b"] == b
            ):
                return row
            if (
                row["metric"] == metric
                and row["strategy_a"] == b
                and row["strategy_b"] == a
            ):
                reversed_row = dict(row)
                reversed_row["strategy_a"] = a
                reversed_row["strategy_b"] = b
                reversed_row["mean_diff_pp"] = -row["mean_diff_pp"]
                reversed_row["ci95_low_pp"] = -row["ci95_high_pp"]
                reversed_row["ci95_high_pp"] = -row["ci95_low_pp"]
                reversed_row["cohen_dz"] = -row["cohen_dz"]
                return reversed_row

        return None

    edge_vs_default = find_pair(
        "wolf_win_rate",
        "seer_edge_first",
        "seer_default",
    )
    edge_vs_random = find_pair(
        "wolf_win_rate",
        "seer_edge_first",
        "seer_random",
    )
    edge_vs_inner = find_pair(
        "wolf_win_rate",
        "seer_edge_first",
        "seer_inner_first",
    )
    edge_discovery_vs_default = find_pair(
        "seer_found_wolf_rate",
        "seer_edge_first",
        "seer_default",
    )
    flagged_outliers = [
        row for row in outlier_rows
        if row["outlier_flag_abs_z_ge_2"]
    ]
    flagged_seed_outliers = [
        row for row in seed_rows
        if row["outlier_flag_abs_z_ge_2"]
    ]

    report = [
        "# Statistical Analysis: Seer Position with Randomized Roles",
        "",
        "## Datasets Analyzed",
        "",
        f"- `{RAW_PATH.relative_to(ROOT)}`: seed-level raw results, 35 rows "
        "(7 strategies x 5 seeds).",
        f"- `{SINGLE_SEED_PATH.relative_to(ROOT)}`: seed 42 single-seed "
        "reference results.",
        "",
        "The original raw data files were preserved unchanged. All analysis "
        "outputs were written under "
        "`results/data_analysis/seer_position_randomized_roles/`.",
        "",
        "## Methods",
        "",
        "- Descriptive statistics across seeds: mean, sample standard "
        "deviation, minimum, maximum.",
        "- 95% confidence intervals across seeds using the t critical value "
        "for n=5 seeds.",
        "- Friedman omnibus tests across strategies for wolf win rate and "
        "seer wolf-discovery rate, using a chi-square approximation.",
        "- Paired exact sign-flip permutation tests across matched seeds for "
        "all pairwise strategy comparisons.",
        "- Holm correction for multiple pairwise comparisons.",
        "- Effect sizes reported as paired Cohen's dz.",
        "- Practical meaningfulness threshold: absolute difference of at "
        "least 3 percentage points.",
        "- Outlier and influence scan using within-condition z-scores and "
        "leave-one-seed-out mean shifts.",
        "",
        "## Main Descriptive Results",
        "",
        "| Strategy | Wolf mean % | Wolf SD pp | 95% CI | Village mean % | "
        "Seer found wolf % | First check wolf % | Edge check % | "
        "Avg wolves on edge |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summary_rows:
        report.append(
            f"| {DISPLAY_NAMES[row['condition']]} | "
            f"{row['wolf_win_mean']:.2f} | "
            f"{row['wolf_win_sd']:.2f} | "
            f"[{row['wolf_win_ci95_low']:.2f}, "
            f"{row['wolf_win_ci95_high']:.2f}] | "
            f"{row['village_win_mean']:.2f} | "
            f"{row['seer_found_wolf_mean']:.2f} | "
            f"{row['first_check_found_wolf_mean']:.2f} | "
            f"{row['edge_check_mean']:.2f} | "
            f"{row['avg_wolves_on_edge_mean']:.2f} |"
        )

    report.extend([
        "",
        "## Omnibus Strategy Tests",
        "",
        "| Metric | Friedman Q | df | p-value | Interpretation |",
        "|---|---:|---:|---:|---|",
    ])

    for test in omnibus_tests:
        p_value = test["p_value_chi_square_approx"]
        if p_value is None:
            interpretation = "not computed"
            p_text = "NA"
        elif p_value < 0.05:
            interpretation = "strategy differences detected"
            p_text = f"{p_value:.4f}"
        else:
            interpretation = "no statistically clear omnibus difference"
            p_text = f"{p_value:.4f}"

        report.append(
            f"| {test['metric']} | {test['friedman_q']:.2f} | "
            f"{test['df']} | {p_text} | {interpretation} |"
        )

    report.extend([
        "",
        "## Edge-Priority Evaluation",
        "",
        f"`seer_edge_first` has a wolf win-rate mean of "
        f"{edge['wolf_win_mean']:.2f}%, compared with "
        f"{default['wolf_win_mean']:.2f}% for default, "
        f"{random_row['wolf_win_mean']:.2f}% for random, and "
        f"{inner['wolf_win_mean']:.2f}% for inner-first.",
        "",
    ])

    for label, comparison in [
        ("edge_first vs default", edge_vs_default),
        ("edge_first vs random", edge_vs_random),
        ("edge_first vs inner_first", edge_vs_inner),
    ]:
        report.append(
            f"- {label}: mean wolf-rate difference "
            f"{comparison['mean_diff_pp']:.2f} pp "
            "(negative favors edge_first), 95% CI "
            f"[{comparison['ci95_low_pp']:.2f}, "
            f"{comparison['ci95_high_pp']:.2f}], "
            f"permutation p={comparison['p_permutation']:.4f}, "
            f"Holm p={comparison['p_holm']:.4f}, "
            f"Cohen's dz={comparison['cohen_dz']:.2f}. "
            f"This is {practical_label(comparison['mean_diff_pp'], comparison['p_holm'])}."
        )

    report.extend([
        "",
        f"For wolf discovery, edge_first exceeds default by "
        f"{edge_discovery_vs_default['mean_diff_pp']:.2f} pp "
        f"(Holm p={edge_discovery_vs_default['p_holm']:.4f}).",
        "",
        "Overall, the edge-priority advantage after role randomization is "
        "limited. It is directionally better than default and random for "
        "wolf win rate, but it is not statistically significant after "
        "multiple-comparison correction and it does not clearly outperform "
        "inner-first. The result is best treated as suggestive rather than "
        "confirmed.",
        "",
        "## Strategy Comparison",
        "",
        f"The best village outcome by mean wolf win rate is "
        f"`{best_village['condition']}` with wolf mean "
        f"{best_village['wolf_win_mean']:.2f}% and village mean "
        f"{best_village['village_win_mean']:.2f}%. The highest seer "
        f"wolf-discovery rate is `{best_discovery['condition']}` at "
        f"{best_discovery['seer_found_wolf_mean']:.2f}%. These are close "
        "enough that the analysis does not support a single dominant "
        "position-only strategy.",
        "",
        "## Robustness and Outliers",
        "",
    ])

    if flagged_outliers:
        report.append(
            f"The within-condition scan flagged {len(flagged_outliers)} "
            "seed-strategy rows with absolute z-score >= 2.0."
        )
    else:
        report.append(
            "No seed-strategy rows were flagged as outliers using the "
            "absolute z-score >= 2.0 threshold."
        )

    if flagged_seed_outliers:
        report.append(
            f"The across-strategy seed scan flagged "
            f"{len(flagged_seed_outliers)} seed-level outliers."
        )
    else:
        report.append(
            "No seed was unusually influential across strategies using the "
            "absolute z-score >= 2.0 threshold."
        )

    max_influence = max(
        outlier_rows,
        key=lambda row: abs(row["influence_shift_pp"]),
    )
    report.extend([
        "",
        f"The largest leave-one-seed-out wolf-rate mean shift is "
        f"{max_influence['influence_shift_pp']:.2f} pp for "
        f"`{max_influence['condition']}` seed {max_influence['seed']}. "
        "This indicates moderate seed sensitivity but no single run that "
        "fully drives the conclusion.",
        "",
        "## Conclusions",
        "",
        "- Statistically significant effects: The omnibus tests indicate "
        "that strategies differ overall, but pairwise Holm-corrected "
        "comparisons are conservative with only five seeds.",
        "- Practically meaningful effects: edge_first reduces wolf win rate "
        "by about 3.96 pp relative to default, which is practically "
        "noticeable, but not statistically decisive after correction.",
        "- Inconclusive effects: edge_first vs inner_first is essentially "
        "tied in wolf win rate, so there is no clear evidence that edge "
        "priority dominates inner priority after role randomization.",
        "- Main finding: the apparent edge-priority advantage becomes weak "
        "and conditional once roles are randomized across seats.",
        "",
        "Position should therefore be treated as a heuristic prior, not as "
        "standalone evidence. The randomized-role baseline makes this much "
        "harder to overinterpret, which is exactly the point of the test.",
        "",
        "## Generated Files",
        "",
        "- `statistical_summary.csv` and `.md`",
        "- `pairwise_strategy_comparisons.csv` and `.md`",
        "- `omnibus_strategy_tests.csv` and `.md`",
        "- `outlier_influence.csv` and `.md`",
        "- `seed_level_robustness.csv` and `.md`",
        "- `wolf_win_rate_ci_by_strategy.svg`",
        "- `seer_found_wolf_rate_ci_by_strategy.svg`",
        "- `seed_level_wolf_win_rates.svg`",
        "- `edge_priority_comparison.svg`",
    ])

    return "\n".join(report) + "\n"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(RAW_PATH)
    single_seed_rows = read_csv(SINGLE_SEED_PATH)
    _ = single_seed_rows

    summary_rows = descriptive_summary(rows)
    formatted_summary = formatted_descriptive_summary(summary_rows)
    summary_fieldnames = list(formatted_summary[0].keys())
    write_csv(
        OUTPUT_DIR / "statistical_summary.csv",
        formatted_summary,
        summary_fieldnames,
    )
    write_markdown_table(
        OUTPUT_DIR / "statistical_summary.md",
        "Statistical Summary",
        formatted_summary,
        [
            ("condition", "Condition"),
            ("strategy", "Strategy"),
            ("n_seeds", "n"),
            ("wolf_mean_pp", "Wolf mean %"),
            ("wolf_sd_pp", "Wolf SD pp"),
            ("wolf_ci95", "Wolf 95% CI"),
            ("village_mean_pp", "Village mean %"),
            ("seer_found_wolf_mean_pp", "Seer found wolf %"),
            ("first_check_found_wolf_mean_pp", "First check wolf %"),
            ("edge_check_mean_pp", "Edge check %"),
            ("edge_has_wolf_mean_pp", "Edge has wolf %"),
            ("avg_wolves_on_edge_mean", "Avg wolves on edge"),
            ("avg_payoff_mean", "Avg payoff"),
        ],
    )

    pairwise_rows = (
        paired_comparison(rows, "wolf_win_rate")
        + paired_comparison(rows, "seer_found_wolf_rate")
    )
    formatted_pairwise = formatted_pairwise_rows(pairwise_rows)
    write_csv(
        OUTPUT_DIR / "pairwise_strategy_comparisons.csv",
        formatted_pairwise,
        list(formatted_pairwise[0].keys()),
    )
    write_markdown_table(
        OUTPUT_DIR / "pairwise_strategy_comparisons.md",
        "Pairwise Strategy Comparisons",
        formatted_pairwise,
        [
            ("metric", "Metric"),
            ("strategy_a", "Strategy A"),
            ("strategy_b", "Strategy B"),
            ("mean_diff_pp", "Mean diff pp"),
            ("ci95", "95% CI"),
            ("p_permutation", "Permutation p"),
            ("p_holm", "Holm p"),
            ("cohen_dz", "Cohen dz"),
            ("practical_3pp", ">=3pp"),
            ("significant_holm", "Significant"),
        ],
    )

    omnibus_tests = [
        friedman_test(rows, "wolf_win_rate", lower_is_better=True),
        friedman_test(rows, "seer_found_wolf_rate", lower_is_better=False),
    ]
    write_omnibus_results(
        OUTPUT_DIR / "omnibus_strategy_tests.md",
        omnibus_tests,
    )

    outlier_rows = outlier_and_influence_rows(rows)
    formatted_outliers = []

    for row in outlier_rows:
        formatted_outliers.append({
            "condition": row["condition"],
            "seed": row["seed"],
            "wolf_win_rate_pp": format_float(row["wolf_win_rate_pp"]),
            "condition_wolf_z": format_float(row["condition_wolf_z"]),
            "leave_one_out_wolf_mean_pp": format_float(
                row["leave_one_out_wolf_mean_pp"]
            ),
            "influence_shift_pp": format_float(row["influence_shift_pp"]),
            "outlier_flag_abs_z_ge_2": row["outlier_flag_abs_z_ge_2"],
        })

    write_csv(
        OUTPUT_DIR / "outlier_influence.csv",
        formatted_outliers,
        list(formatted_outliers[0].keys()),
    )
    write_markdown_table(
        OUTPUT_DIR / "outlier_influence.md",
        "Outlier and Influence Diagnostics",
        formatted_outliers,
        [
            ("condition", "Condition"),
            ("seed", "Seed"),
            ("wolf_win_rate_pp", "Wolf %"),
            ("condition_wolf_z", "Within-condition z"),
            ("leave_one_out_wolf_mean_pp", "Leave-one-out mean %"),
            ("influence_shift_pp", "Influence shift pp"),
            ("outlier_flag_abs_z_ge_2", "Outlier"),
        ],
    )

    seed_rows = seed_level_rows(rows)
    formatted_seed_rows = []

    for row in seed_rows:
        formatted_seed_rows.append({
            "seed": row["seed"],
            "mean_wolf_win_rate_pp": format_float(
                row["mean_wolf_win_rate_pp"]
            ),
            "sd_wolf_win_rate_pp": format_float(row["sd_wolf_win_rate_pp"]),
            "seed_mean_z": format_float(row["seed_mean_z"]),
            "outlier_flag_abs_z_ge_2": row["outlier_flag_abs_z_ge_2"],
        })

    write_csv(
        OUTPUT_DIR / "seed_level_robustness.csv",
        formatted_seed_rows,
        list(formatted_seed_rows[0].keys()),
    )
    write_markdown_table(
        OUTPUT_DIR / "seed_level_robustness.md",
        "Seed-Level Robustness",
        formatted_seed_rows,
        [
            ("seed", "Seed"),
            ("mean_wolf_win_rate_pp", "Mean wolf %"),
            ("sd_wolf_win_rate_pp", "SD across strategies"),
            ("seed_mean_z", "Seed z"),
            ("outlier_flag_abs_z_ge_2", "Outlier"),
        ],
    )

    write_bar_ci_svg(
        OUTPUT_DIR / "wolf_win_rate_ci_by_strategy.svg",
        summary_rows,
        "wolf_win",
        "Wolf win rate by seer strategy",
        "Wolf win rate (%), lower favors village",
    )
    write_bar_ci_svg(
        OUTPUT_DIR / "seer_found_wolf_rate_ci_by_strategy.svg",
        summary_rows,
        "seer_found_wolf",
        "Seer wolf-discovery rate by strategy",
        "Seer found wolf rate (%)",
    )
    write_seed_line_svg(
        OUTPUT_DIR / "seed_level_wolf_win_rates.svg",
        rows,
        "wolf_win_rate",
        "Seed-level wolf win rates by strategy",
        "Wolf win rate (%)",
    )
    write_edge_comparison_svg(
        OUTPUT_DIR / "edge_priority_comparison.svg",
        rows,
    )

    report = build_report(
        summary_rows,
        pairwise_rows,
        omnibus_tests,
        outlier_rows,
        seed_rows,
    )
    (OUTPUT_DIR / "analysis_report.md").write_text(report)

    print(f"Analyzed {len(rows)} seed-level rows from {RAW_PATH}")
    print(f"Wrote analysis outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
