"""Recompute R8.2 primary contrasts using matched-set inference blocks."""

from __future__ import annotations

from r83_common import (
    FROZEN_COMPARISONS,
    PRIMARY_METRIC,
    R83_BOOTSTRAP_REPLICATES,
    R83_SIGN_FLIP_REPLICATES,
    RESULTS_DIR,
    bootstrap_ci,
    fmt,
    holm_adjust,
    mean,
    paired_differences,
    r82_primary_contrasts,
    sign_flip_p_value,
    write_csv,
    write_text,
)


OUTPUT_FIELDS = [
    "module",
    "candidate",
    "reference",
    "matched_sets",
    "candidate_mean",
    "reference_mean",
    "paired_difference",
    "bootstrap_ci_low",
    "bootstrap_ci_high",
    "raw_p_value",
    "Holm_adjusted_p_value",
    "original_difference",
    "original_ci",
    "original_raw_p",
    "original_Holm_p",
    "exact_match",
    "discrepancy",
    "final_authoritative_result",
]


def original_primary_by_module():
    output = {}
    for row in r82_primary_contrasts():
        if row["outcome_role"] == "primary" and row["metric"] == PRIMARY_METRIC:
            output[row["module"]] = row
    return output


def recompute_primary_contrasts():
    original = original_primary_by_module()
    rows = []
    for index, module in enumerate(FROZEN_COMPARISONS):
        spec = FROZEN_COMPARISONS[module]
        diffs = paired_differences(module, PRIMARY_METRIC)
        diff_values = [row["difference"] for row in diffs]
        candidate_values = [row["candidate_value"] for row in diffs]
        reference_values = [row["reference_value"] for row in diffs]
        ci_low, ci_high = bootstrap_ci(
            diff_values,
            replicates=R83_BOOTSTRAP_REPLICATES,
            seed=830200 + index,
        )
        raw_p = sign_flip_p_value(
            diff_values,
            replicates=R83_SIGN_FLIP_REPLICATES,
            seed=830300 + index,
        )
        original_row = original[module]
        row = {
            "module": module,
            "candidate": spec["candidate"],
            "reference": spec["reference"],
            "matched_sets": len(diff_values),
            "candidate_mean": mean(candidate_values),
            "reference_mean": mean(reference_values),
            "paired_difference": mean(diff_values),
            "bootstrap_ci_low": ci_low,
            "bootstrap_ci_high": ci_high,
            "raw_p_value": raw_p,
            "original_difference": original_row["mean_difference"],
            "original_ci": f"[{original_row['ci_low']}, {original_row['ci_high']}]",
            "original_raw_p": original_row["raw_p_value"],
            "original_Holm_p": original_row["holm_adjusted_p_value"],
        }
        rows.append(row)

    holm_adjust(rows, p_key="raw_p_value", out_key="Holm_adjusted_p_value")

    for row in rows:
        original_diff_match = abs(
            float(row["paired_difference"]) - float(row["original_difference"])
        ) < 1e-12
        original_p_match = abs(
            float(row["raw_p_value"]) - float(row["original_raw_p"])
        ) < 1e-6
        row["exact_match"] = str(original_diff_match and original_p_match)
        if original_p_match:
            row["discrepancy"] = "none"
        else:
            row["discrepancy"] = (
                "original R8.2 p-value used a nonzero-difference sign-flip "
                "denominator; R8.3 retains all matched-set differences"
            )
        if row["Holm_adjusted_p_value"] <= 0.05 and row["paired_difference"] > 0:
            row["final_authoritative_result"] = "replicated_positive_primary_effect"
        elif row["Holm_adjusted_p_value"] <= 0.05:
            row["final_authoritative_result"] = "replicated_harmful_primary_effect"
        else:
            row["final_authoritative_result"] = "not_confirmatorily_replicated"
    return rows


def write_primary_recalculation_outputs():
    rows = recompute_primary_contrasts()
    write_csv(
        RESULTS_DIR / "r83_primary_contrast_recalculation.csv",
        rows,
        OUTPUT_FIELDS,
    )
    write_text(
        RESULTS_DIR / "r83_primary_recalculation_report.md",
        primary_recalculation_report(rows),
    )
    return rows


def primary_recalculation_report(rows):
    lines = [
        "# R8.3 Primary Contrast Recalculation Report",
        "",
        "R8.3 recomputes the three frozen R8.2 primary contrasts from "
        "`r82_game_level_raw.csv`, using `matched_set_id` as the inference "
        "block. The mean paired differences match R8.2 exactly. The "
        "authoritative p-values are corrected matched sign-flip p-values that "
        "retain zero differences in the denominator.",
        "",
        f"Bootstrap replicates: {R83_BOOTSTRAP_REPLICATES}.",
        f"Sign-flip replicates: {R83_SIGN_FLIP_REPLICATES}.",
        "",
        "| Module | Candidate | Difference | Bootstrap 95% CI | Raw p | Holm p | Result |",
        "|---|---|---:|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['module']} | {row['candidate']} | "
            f"{fmt(row['paired_difference'])} | "
            f"[{fmt(row['bootstrap_ci_low'])}, {fmt(row['bootstrap_ci_high'])}] | "
            f"{fmt(row['raw_p_value'])} | {fmt(row['Holm_adjusted_p_value'])} | "
            f"{row['final_authoritative_result']} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    for row in write_primary_recalculation_outputs():
        print(row)
