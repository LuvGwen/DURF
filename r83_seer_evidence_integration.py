"""Separate R8.2 Seer replication evidence from R6.2 safety lifecycle evidence."""

from __future__ import annotations

from r83_common import (
    RESULTS_DIR,
    rows_by_key,
    r82_policy_summary,
    r82_special_metrics,
    read_csv,
    write_csv,
    write_text,
    R62_DIR,
)


OUTPUT_FIELDS = [
    "evidence_source",
    "dataset",
    "seed_status",
    "metric",
    "estimate",
    "inference_status",
    "can_be_combined_numerically",
    "final_use",
    "limitation",
]


def build_seer_evidence_integration(corrected_rows):
    summary = rows_by_key(r82_policy_summary(), "module", "policy")
    special = rows_by_key(r82_special_metrics(), "module", "policy")
    corrected = next(row for row in corrected_rows if row["module"] == "seer")
    hazard_rows = {
        row["policy"]: row
        for row in read_csv(R62_DIR / "r62_seer_post_reveal_hazard_summary.csv")
    }
    immediate_hazard = hazard_rows["immediate_reveal"]

    rows = [
        {
            "evidence_source": "A_R8.2_independent_replication",
            "dataset": "results/targeted_replication_stage_r82/r82_game_level_raw.csv",
            "seed_status": "fresh R8.2 seeds 820-839",
            "metric": "actor_payoff_direction",
            "estimate": corrected["paired_difference"],
            "inference_status": f"corrected Holm p={corrected['Holm_adjusted_p_value']}",
            "can_be_combined_numerically": "not_applicable",
            "final_use": "primary payoff replication evidence",
            "limitation": "Does not include next-night reveal hazard.",
        },
        {
            "evidence_source": "A_R8.2_independent_replication",
            "dataset": "results/targeted_replication_stage_r82/r82_policy_summary.csv",
            "seed_status": "fresh R8.2 seeds 820-839",
            "metric": "village_win_direction",
            "estimate": (
                float(summary[("seer", "immediate_reveal")]["village_win_rate"])
                - float(summary[("seer", "private_only")]["village_win_rate"])
            ),
            "inference_status": "secondary, not primary-decision controlling",
            "can_be_combined_numerically": "not_applicable",
            "final_use": "secondary direction evidence",
            "limitation": "Secondary result does not override safety caveats.",
        },
        {
            "evidence_source": "A_R8.2_independent_replication",
            "dataset": "results/targeted_replication_stage_r82/r82_special_module_metrics.csv",
            "seed_status": "fresh R8.2 seeds 820-839",
            "metric": "terminal_survival",
            "estimate": (
                "private_only="
                + special[("seer", "private_only")]["seer_survival_rate"]
                + "; immediate_reveal="
                + special[("seer", "immediate_reveal")]["seer_survival_rate"]
            ),
            "inference_status": "terminal-only descriptive metric",
            "can_be_combined_numerically": "False",
            "final_use": "disclose narrow metric only",
            "limitation": "Terminal survival is not next-night or two-round survival.",
        },
        {
            "evidence_source": "B_R6.2_historical_lifecycle_audit",
            "dataset": "results/metrics_integrity_stage_r62/r62_seer_post_reveal_hazard_summary.csv",
            "seed_status": "historical supplementary audit, not R8.2 fresh-seed replication",
            "metric": "next_night_hazard",
            "estimate": immediate_hazard["night_kill_hazard_after_reveal"],
            "inference_status": "historical lifecycle safety evidence",
            "can_be_combined_numerically": "False",
            "final_use": "safety caveat for immediate_reveal",
            "limitation": "Different audit dataset and metric definition; do not pool with R8.2.",
        },
        {
            "evidence_source": "B_R6.2_historical_lifecycle_audit",
            "dataset": "results/metrics_integrity_stage_r62/r62_seer_post_reveal_hazard_summary.csv",
            "seed_status": "historical supplementary audit, not R8.2 fresh-seed replication",
            "metric": "one_round_death_probability_after_reveal",
            "estimate": immediate_hazard["hazard_within_one_night"],
            "inference_status": "historical lifecycle safety evidence",
            "can_be_combined_numerically": "False",
            "final_use": "safety caveat for immediate_reveal",
            "limitation": "R8.2 did not export this metric.",
        },
        {
            "evidence_source": "B_R6.2_historical_lifecycle_audit",
            "dataset": "results/metrics_integrity_stage_r62/r62_seer_post_reveal_hazard_summary.csv",
            "seed_status": "historical supplementary audit, not R8.2 fresh-seed replication",
            "metric": "two_round_death_probability_after_reveal",
            "estimate": immediate_hazard["hazard_within_two_nights"],
            "inference_status": "historical lifecycle safety evidence",
            "can_be_combined_numerically": "False",
            "final_use": "safety caveat for immediate_reveal",
            "limitation": "R8.2 did not export this metric.",
        },
        {
            "evidence_source": "B_R6.2_historical_lifecycle_audit",
            "dataset": "results/metrics_integrity_stage_r62/r62_seer_survival_audit_report.md",
            "seed_status": "historical supplementary audit, not R8.2 fresh-seed replication",
            "metric": "post_reveal_exposure",
            "estimate": "public reveal creates strategic targeting exposure",
            "inference_status": "historical safety interpretation",
            "can_be_combined_numerically": "False",
            "final_use": "qualify default recommendation",
            "limitation": "Qualitative integration only; no numeric pooling.",
        },
    ]
    return rows


def write_seer_evidence_outputs(corrected_rows):
    rows = build_seer_evidence_integration(corrected_rows)
    write_csv(
        RESULTS_DIR / "r83_seer_evidence_integration.csv",
        rows,
        OUTPUT_FIELDS,
    )
    write_text(
        RESULTS_DIR / "r83_seer_evidence_integration_report.md",
        seer_evidence_report(rows),
    )
    return rows


def seer_evidence_report(rows):
    return """# R8.3 Seer Evidence Integration Report

R8.3 separates R8.2 independent payoff replication from R6.2 historical safety
evidence. The corrected R8.2 actor-payoff contrast supports a positive
`immediate_reveal` payoff effect, but R8.2 does not export next-night hazard or
short-horizon survival fields. R6.2 remains the source for post-reveal exposure
evidence and must not be numerically pooled with R8.2.

Final wording may say that `immediate_reveal` has replicated payoff evidence
with unresolved/high exposure risk. It must not say that R8.2 proved the policy
safe.
"""


if __name__ == "__main__":
    from r83_primary_contrast_recalculation import recompute_primary_contrasts

    for row in write_seer_evidence_outputs(recompute_primary_contrasts()):
        print(row)
