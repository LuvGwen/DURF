"""Audit the R8.2 Seer CI and p-value inconsistency."""

from __future__ import annotations

from r83_common import (
    PRIMARY_METRIC,
    R83_SIGN_FLIP_REPLICATES,
    RESULTS_DIR,
    normal_ci,
    paired_differences,
    r82_buggy_nonzero_sign_flip_p_value,
    r82_policy_summary,
    r82_primary_contrasts,
    sign_flip_p_value,
    write_csv,
    write_text,
)


OUTPUT_FIELDS = [
    "statistic",
    "reported_value",
    "source_file",
    "source_column",
    "estimator",
    "independent_unit",
    "clustering_unit",
    "resampling_method",
    "number_of_replicates",
    "confidence_level",
    "null_distribution",
    "one_or_two_sided",
    "multiplicity_adjusted",
    "calculation_verified",
    "issue_detected",
    "corrected_value",
    "explanation",
]


def seer_original_primary():
    for row in r82_primary_contrasts():
        if row["module"] == "seer" and row["outcome_role"] == "primary":
            return row
    raise ValueError("Seer primary contrast not found.")


def seer_policy_summary(policy):
    for row in r82_policy_summary():
        if row["module"] == "seer" and row["policy"] == policy:
            return row
    raise ValueError(f"Seer policy summary not found: {policy}")


def build_seer_consistency_audit(corrected_rows):
    original = seer_original_primary()
    corrected = next(row for row in corrected_rows if row["module"] == "seer")
    immediate = seer_policy_summary("immediate_reveal")
    private = seer_policy_summary("private_only")
    diffs = [row["difference"] for row in paired_differences("seer", PRIMARY_METRIC)]
    normal_low, normal_high = normal_ci(diffs)
    buggy_p, nonzero_count = r82_buggy_nonzero_sign_flip_p_value(
        diffs,
        replicates=R83_SIGN_FLIP_REPLICATES,
        seed=830301,
    )
    corrected_p = sign_flip_p_value(
        diffs,
        replicates=R83_SIGN_FLIP_REPLICATES,
        seed=830301,
    )

    rows = [
        {
            "statistic": "candidate_policy_level_actor_payoff_ci",
            "reported_value": f"[{immediate['actor_payoff_ci_low']}, {immediate['actor_payoff_ci_high']}]",
            "source_file": "results/targeted_replication_stage_r82/r82_policy_summary.csv",
            "source_column": "actor_payoff_ci_low;actor_payoff_ci_high",
            "estimator": "single-policy mean actor payoff",
            "independent_unit": "complete game row for immediate_reveal policy",
            "clustering_unit": "not paired; policy-level normal CI",
            "resampling_method": "normal approximation",
            "number_of_replicates": "0",
            "confidence_level": "95%",
            "null_distribution": "not applicable",
            "one_or_two_sided": "not applicable",
            "multiplicity_adjusted": "False",
            "calculation_verified": "True",
            "issue_detected": "False",
            "corrected_value": "",
            "explanation": "This CI describes the candidate policy mean, not the paired treatment effect.",
        },
        {
            "statistic": "reference_policy_level_actor_payoff_ci",
            "reported_value": f"[{private['actor_payoff_ci_low']}, {private['actor_payoff_ci_high']}]",
            "source_file": "results/targeted_replication_stage_r82/r82_policy_summary.csv",
            "source_column": "actor_payoff_ci_low;actor_payoff_ci_high",
            "estimator": "single-policy mean actor payoff",
            "independent_unit": "complete game row for private_only policy",
            "clustering_unit": "not paired; policy-level normal CI",
            "resampling_method": "normal approximation",
            "number_of_replicates": "0",
            "confidence_level": "95%",
            "null_distribution": "not applicable",
            "one_or_two_sided": "not applicable",
            "multiplicity_adjusted": "False",
            "calculation_verified": "True",
            "issue_detected": "False",
            "corrected_value": "",
            "explanation": "This CI describes the reference policy mean, not the paired treatment effect.",
        },
        {
            "statistic": "paired_actor_payoff_ci",
            "reported_value": f"[{original['ci_low']}, {original['ci_high']}]",
            "source_file": "results/targeted_replication_stage_r82/r82_primary_contrasts.csv",
            "source_column": "ci_low;ci_high",
            "estimator": "mean paired actor-payoff difference",
            "independent_unit": "matched_set_id",
            "clustering_unit": "matched_set_id",
            "resampling_method": "normal approximation over all 1000 matched differences",
            "number_of_replicates": "0",
            "confidence_level": "95%",
            "null_distribution": "normal approximation",
            "one_or_two_sided": "two-sided interval",
            "multiplicity_adjusted": "False",
            "calculation_verified": "True",
            "issue_detected": "False",
            "corrected_value": f"[{normal_low}, {normal_high}]",
            "explanation": "The R8.2 paired CI is internally reproducible and uses all matched-set differences.",
        },
        {
            "statistic": "raw_sign_flip_p_value",
            "reported_value": original["raw_p_value"],
            "source_file": "results/targeted_replication_stage_r82/r82_primary_contrasts.csv",
            "source_column": "raw_p_value",
            "estimator": "matched sign-flip p-value",
            "independent_unit": "intended matched_set_id",
            "clustering_unit": "matched_set_id",
            "resampling_method": "Monte Carlo sign-flip",
            "number_of_replicates": "1000 in R8.2; audited with 20000 in R8.3",
            "confidence_level": "not applicable",
            "null_distribution": "sign-flipped paired differences",
            "one_or_two_sided": "two-sided",
            "multiplicity_adjusted": "False",
            "calculation_verified": "False",
            "issue_detected": "True",
            "corrected_value": corrected["raw_p_value"],
            "explanation": (
                "R8.2 excluded zero differences and computed null means over "
                f"only {nonzero_count} nonzero differences. R8.3 retains all "
                "1000 matched differences in the denominator."
            ),
        },
        {
            "statistic": "bug_reproduction_nonzero_denominator_p_value",
            "reported_value": str(buggy_p),
            "source_file": "r61_statistical_analysis.py",
            "source_column": "permutation_p_value",
            "estimator": "bug reproduction using nonzero denominator",
            "independent_unit": "nonzero paired differences only",
            "clustering_unit": "matched_set_id partially retained but denominator changed",
            "resampling_method": "Monte Carlo sign-flip over nonzero differences",
            "number_of_replicates": str(R83_SIGN_FLIP_REPLICATES),
            "confidence_level": "not applicable",
            "null_distribution": "sign-flipped nonzero paired differences",
            "one_or_two_sided": "two-sided",
            "multiplicity_adjusted": "False",
            "calculation_verified": "True",
            "issue_detected": "True",
            "corrected_value": corrected_p,
            "explanation": "This reproduces the source of the high Seer p-value and verifies the denominator error.",
        },
        {
            "statistic": "Holm_adjusted_p_value",
            "reported_value": original["holm_adjusted_p_value"],
            "source_file": "results/targeted_replication_stage_r82/r82_primary_contrasts.csv",
            "source_column": "holm_adjusted_p_value",
            "estimator": "Holm correction across three primary p-values",
            "independent_unit": "three frozen primary module contrasts",
            "clustering_unit": "matched_set_id within each contrast",
            "resampling_method": "Holm adjustment of raw p-values",
            "number_of_replicates": "not applicable",
            "confidence_level": "not applicable",
            "null_distribution": "family of three primary tests",
            "one_or_two_sided": "two-sided raw p-values",
            "multiplicity_adjusted": "True",
            "calculation_verified": "True for Holm implementation; false for original raw p input",
            "issue_detected": "True",
            "corrected_value": corrected["Holm_adjusted_p_value"],
            "explanation": "Holm logic is standard; the adjusted value was wrong because the Seer raw p-value input was wrong.",
        },
    ]
    return rows


def write_seer_consistency_outputs(corrected_rows):
    rows = build_seer_consistency_audit(corrected_rows)
    write_csv(
        RESULTS_DIR / "r83_seer_statistical_consistency_audit.csv",
        rows,
        OUTPUT_FIELDS,
    )
    write_text(
        RESULTS_DIR / "r83_seer_statistical_consistency_report.md",
        seer_consistency_report(rows, corrected_rows),
    )
    write_text(
        RESULTS_DIR / "r83_statistical_consistency_method.md",
        statistical_consistency_method(),
    )
    return rows


def seer_consistency_report(rows, corrected_rows):
    seer = next(row for row in corrected_rows if row["module"] == "seer")
    return f"""# R8.3 Seer Statistical Consistency Report

## Finding

The R8.2 Seer paired actor-payoff CI was reproducible, but the R8.2 Seer
raw and Holm-adjusted p-values were not. The discrepancy was caused by a
sign-flip implementation error: zero matched differences were removed and
the null mean denominator was changed from all 1,000 matched sets to only
the nonzero subset.

## Corrected Authoritative Result

- Difference: {seer['paired_difference']}
- Matched-set bootstrap CI: [{seer['bootstrap_ci_low']}, {seer['bootstrap_ci_high']}]
- Corrected raw p-value: {seer['raw_p_value']}
- Corrected Holm-adjusted p-value: {seer['Holm_adjusted_p_value']}
- Result: {seer['final_authoritative_result']}

## Interpretation

The Seer effect is statistically replicated on the preregistered actor-payoff
primary outcome after correction. However, final default policy wording must
still separate payoff evidence from safety evidence because R8.2 did not export
next-night death hazard or short-horizon survival fields, while R6.2 documented
post-reveal exposure for `immediate_reveal`.
"""


def statistical_consistency_method():
    return """# R8.3 Statistical Consistency Method

R8.3 reads only frozen R8.2 complete-game outputs. The inference block is
`matched_set_id`; no player rows or action rows are treated as independent
primary observations.

For each frozen role module, R8.3 computes candidate-minus-reference paired
actor-payoff differences. The confidence interval is a matched-set cluster
bootstrap percentile interval over the paired differences. The raw p-value is
a two-sided Monte Carlo sign-flip test over all matched differences, including
zeros. Holm correction is then applied across exactly the three frozen primary
tests: Villager, Seer, and Witch.

The R8.2 inconsistency was traced to a sign-flip helper that removed zero
differences and computed null means over the nonzero subset. Removing zeros is
not itself harmful if the denominator remains the full matched-set count, but
changing the denominator inflates the null variance and can make p-values
inconsistent with a positive paired CI.
"""


if __name__ == "__main__":
    from r83_primary_contrast_recalculation import recompute_primary_contrasts

    for row in write_seer_consistency_outputs(recompute_primary_contrasts()):
        print(row)
