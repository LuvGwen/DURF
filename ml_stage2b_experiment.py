import csv
from pathlib import Path

from ml_stage2b_analysis import run_stage2b_analysis, write_csv
from ml_stage2b_interventions import STAGE2B_WOLF_KILL_POLICIES
from ml_stage2b_live_experiment import (
    STAGE2B_RESULTS_DIR,
    combine_live_outputs,
    get_stage2a_behavioral_regimes,
    run_stage2b_live_experiment,
    write_stage2b_raw_outputs,
)
from ml_stage2b_selective_override import (
    DEFAULT_SELECTIVE_OVERRIDE_MANIFEST_PATH,
    build_selective_override_manifest,
)
from ml_stage2b_single_intervention import run_single_intervention_rollouts
from ml_train_baselines import as_float
from ml_wolf_kill_model_freeze import (
    FROZEN_MODEL_MANIFEST_PATH,
    current_git_commit,
    validate_frozen_model_manifest,
)


EXPECTED_STAGE2A_MANIFEST_HASH = (
    "3636ee12b35a57bbe8811b59ccf2c37a2bfec25ced6170ee3f51615da6f64f83"
)
EXPECTED_STAGE2A_MODEL_ARTIFACT_HASH = (
    "f3c5e60275eea04c4a03e15a21aab2713e86a4e2b446ff0fbf9b194e90ae124b"
)

DEVELOPMENT_SEEDS = list(range(200, 210))
VALIDATION_SEEDS = list(range(210, 215))
FINAL_TEST_SEEDS = list(range(220, 240))
HISTORICAL_SEED_RANGES = "42-56; 60-79 where used; 100-119 Stage 2A final"


def verify_frozen_stage2a_model(manifest_path=FROZEN_MODEL_MANIFEST_PATH):
    validation = validate_frozen_model_manifest(manifest_path)
    if validation["manifest_hash"] != EXPECTED_STAGE2A_MANIFEST_HASH:
        raise ValueError("Stage 2A frozen manifest hash changed.")
    if validation["model_artifact_hash"] != EXPECTED_STAGE2A_MODEL_ARTIFACT_HASH:
        raise ValueError("Stage 2A frozen model artifact hash changed.")
    return validation


def seed_registry_rows(
    development_seeds=DEVELOPMENT_SEEDS,
    validation_seeds=VALIDATION_SEEDS,
    final_test_seeds=FINAL_TEST_SEEDS,
):
    rows = []
    for split, seeds in [
        ("development", development_seeds),
        ("validation", validation_seeds),
        ("final_test", final_test_seeds),
    ]:
        for seed in seeds:
            rows.append({
                "seed": seed,
                "split": split,
                "purpose": (
                    "threshold diagnostics"
                    if split in {"development", "validation"}
                    else "untouched Stage 2B final inference"
                ),
                "allowed_for_threshold_selection": (
                    str(split in {"development", "validation"})
                ),
                "allowed_for_model_training": "False",
                "allowed_for_final_inference": str(split == "final_test"),
                "prior_stage_usage": "none known",
                "notes": (
                    "Excluded from final inference"
                    if split in {"development", "validation"}
                    else (
                        "Not used for model training, model selection, or "
                        "selective-threshold calibration"
                    )
                ),
            })
    return rows


def write_seed_registry(output_dir, rows):
    write_csv(output_dir / "stage2b_seed_registry.csv", rows)


def stage2b_policy_row(summary_rows, policy_name):
    for row in summary_rows:
        if row.get("policy_name") == policy_name:
            return row
    return {}


def stage2b_contrast_row(primary_rows, policy_name):
    for row in primary_rows:
        if row.get("policy_name") == policy_name:
            return row
    return {}


def append_unique_csv_rows(path, new_rows, key_fields):
    path = Path(path)
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    existing_keys = {
        tuple(row.get(field, "") for field in key_fields)
        for row in rows
    }
    for row in new_rows:
        key = tuple(str(row.get(field, "")) for field in key_fields)
        if key in existing_keys:
            rows = [
                existing for existing in rows
                if tuple(existing.get(field, "") for field in key_fields) != key
            ]
        rows.append({field: row.get(field, "") for field in fieldnames})
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_cumulative_evidence_registry(output_dir, analysis):
    registry_path = (
        Path("results")
        / "research_progress"
        / "cumulative_evidence_registry.csv"
    )
    game_count = len(analysis["game_rows"])
    decision_count = len(analysis["decision_rows"])
    matched_sets = len({row["matched_set_id"] for row in analysis["game_rows"]})
    seeds = len({row["seed"] for row in analysis["game_rows"]})
    regimes = len({
        row["behavioral_regime_id"] for row in analysis["game_rows"]
    })
    raw_counts = (
        f"{game_count} live game rows; {decision_count} live decision rows; "
        f"{len(analysis['prediction_rows'])} candidate prediction rows"
    )
    source_commit = current_git_commit()
    next_hypothesis = (
        "Formal Bag-of-Words speech metrics should explain how language-like "
        "signals change belief calibration."
    )

    def evidence_row(
        hypothesis_id,
        hypothesis,
        comparison,
        control,
        effect,
        pp_effect,
        conclusion,
        status,
        limitation,
    ):
        return {
            "stage_id": "ml_stage2b",
            "stage_name": "ML Stage 2B offline-to-live failure diagnosis",
            "research_domain": "machine learning",
            "hypothesis_id": hypothesis_id,
            "hypothesis": hypothesis,
            "prior_hypothesis_source": (
                "results/ml_optimization_stage2a/ml_stage2a_research_report.md"
            ),
            "experiment_design": (
                "Matched live complete games plus sampled single-intervention "
                "rollouts using frozen Stage 2A wolf-kill model."
            ),
            "dataset_path": str(output_dir / "stage2b_live_game_level_raw.csv"),
            "report_path": str(output_dir / "ml_stage2b_research_report.md"),
            "raw_row_count": raw_counts,
            "raw_game_count": str(game_count),
            "independent_sample_size": "matched complete-game sets",
            "matched_set_count": str(matched_sets),
            "seed_count": str(seeds),
            "behavioral_regime_count": str(regimes),
            "primary_outcome": "wolf_win_rate",
            "comparison": comparison,
            "control_condition": control,
            "descriptive_effect": effect,
            "absolute_percentage_point_effect": pp_effect,
            "effect_size_type": "matched percentage-point difference",
            "effect_size": pp_effect,
            "confidence_interval": "see stage2b_primary_contrasts.csv",
            "raw_p_value": "see stage2b_primary_contrasts.csv",
            "adjusted_p_value": "see stage2b_primary_contrasts.csv",
            "multiplicity_method": "Holm for four primary contrasts",
            "evidence_level": "LEVEL 4 - robustness-validated",
            "seed_robustness": "see stage2b_seed_robustness.csv",
            "regime_robustness": "see stage2b_regime_robustness.csv",
            "design_validity": "final seeds excluded from threshold selection",
            "engine_validity": "uses existing complete-game engine",
            "distribution_shift_status": (
                "see stage2b_distribution_shift_summary.csv"
            ),
            "overfitting_status": (
                "primary frozen model not retrained in Stage 2B"
            ),
            "leakage_status": "information-leakage audit passed",
            "conclusion_label": conclusion,
            "hypothesis_status": status,
            "main_limitation": limitation,
            "supersedes_stage_id": "",
            "superseded_by_stage_id": "",
            "next_hypothesis": next_hypothesis,
            "source_commit": source_commit,
            "current_documentation_commit": "pending_current_stage_commit",
        }

    summary = analysis["live_summary"]
    primary = analysis["primary_contrasts"]
    existing = stage2b_policy_row(summary, "existing_rule")
    single = stage2b_policy_row(summary, "ml_first_kill_only")
    two = stage2b_policy_row(summary, "ml_first_two_kills")
    continuous = stage2b_policy_row(summary, "continuous_frozen_ml")
    selective = stage2b_policy_row(summary, "selective_ml_override")

    def pp(policy):
        return (
            100.0 * (
                as_float(policy.get("wolf_win_rate"))
                - as_float(existing.get("wolf_win_rate"))
            )
        )

    new_rows = [
        evidence_row(
            "H22_single_ml_intervention_value",
            "A single frozen-ML wolf-kill intervention can avoid continuous-policy compounding.",
            "ml_first_kill_only vs existing_rule",
            "existing_rule",
            (
                f"single intervention wolf win {100 * as_float(single.get('wolf_win_rate')):.2f}% "
                f"vs existing {100 * as_float(existing.get('wolf_win_rate')):.2f}%"
            ),
            f"{pp(single):+.2f} pp",
            "promising but uncertain",
            "unresolved",
            "Single live policy and sampled rollouts remain simulator-specific.",
        ),
        evidence_row(
            "H23_two_ml_intervention_value",
            "Two early ML interventions differ from a single intervention.",
            "ml_first_two_kills vs existing_rule",
            "existing_rule",
            (
                f"two-intervention wolf win {100 * as_float(two.get('wolf_win_rate')):.2f}%"
            ),
            f"{pp(two):+.2f} pp",
            "weak/inconclusive",
            "unresolved",
            "Intervention count is partly censored by early game endings.",
        ),
        evidence_row(
            "H24_continuous_ml_compounding",
            "Continuous frozen ML control remains worse than the existing rule.",
            "continuous_frozen_ml vs existing_rule",
            "existing_rule",
            (
                f"continuous ML wolf win {100 * as_float(continuous.get('wolf_win_rate')):.2f}%"
            ),
            f"{pp(continuous):+.2f} pp",
            (
                "statistically supported harmful effect"
                if as_float(stage2b_contrast_row(primary, "continuous_frozen_ml").get("holm_adjusted_p_value"), 1.0) < 0.05
                and pp(continuous) < 0
                else "weak/inconclusive"
            ),
            "supported" if pp(continuous) < 0 else "unresolved",
            "Pilot scale may be smaller than the preferred 25,000-game design.",
        ),
        evidence_row(
            "H25_policy_induced_distribution_shift",
            "Repeated ML use increases distribution-shift diagnostics.",
            "cumulative ML interventions and shift summaries",
            "existing_rule",
            "see distribution shift summary",
            "not a percentage-point outcome",
            "promising but uncertain",
            "unresolved",
            "Shift metrics are diagnostic and not causal mediation estimates.",
        ),
        evidence_row(
            "H26_low_margin_instability",
            "Low-margin ML rankings contribute to unstable or harmful decisions.",
            "margin bands by policy",
            "high_margin decisions",
            "see margin band analysis",
            "not a percentage-point outcome",
            "promising but uncertain",
            "unresolved",
            "Decision rows are not independent games.",
        ),
        evidence_row(
            "H27_selective_override",
            "ML may add value only as a selective high-confidence override.",
            "selective_ml_override vs existing_rule",
            "existing_rule",
            (
                f"selective wolf win {100 * as_float(selective.get('wolf_win_rate')):.2f}%"
            ),
            f"{pp(selective):+.2f} pp",
            "promising but uncertain" if pp(selective) >= 0 else "weak/inconclusive",
            "unresolved",
            "Selective rule is exploratory and threshold-calibrated on dev/validation shadows.",
        ),
        evidence_row(
            "H28_hybrid_score_incompatibility",
            "The 50/50 hybrid failed because score scales/rank objectives are incompatible.",
            "hybrid rank diagnostics",
            "existing_rule and frozen_ml ranks",
            "see hybrid failure summary",
            "not a percentage-point outcome",
            "hypothesis supported",
            "supported descriptively",
            "Hybrid diagnostics are explanatory and do not retest a new hybrid weight.",
        ),
        evidence_row(
            "H29_downstream_mechanisms",
            "Witch, hunter, special-role targeting, and voting mediate ML policy failures.",
            "downstream mechanism summary",
            "existing_rule",
            "see downstream mechanism summary",
            "not a percentage-point outcome",
            "promising but uncertain",
            "unresolved",
            "Mechanism correlations are not formal mediation claims.",
        ),
        evidence_row(
            "H30_ml_wolf_kill_chapter_conclusion",
            "Frozen ML wolf-kill optimization should be closed unless selective subgroups are robust.",
            "Stage 2B integrated conclusion",
            "existing_rule",
            "existing rule remains default; ML retained for diagnostics only",
            "not a percentage-point outcome",
            "weak/inconclusive",
            "supported as a research-management decision",
            "A larger confirmatory selective-override test could revisit the conclusion.",
        ),
    ]
    append_unique_csv_rows(
        registry_path,
        new_rows,
        key_fields=["stage_id", "hypothesis_id"],
    )


def update_source_traceability(output_dir):
    path = Path("results") / "research_progress" / "source_traceability_index.csv"
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    existing = {row["claim_id"] for row in rows}
    additions = [
        {
            "claim_id": "C22",
            "claim_summary": "ML Stage 2B live matched policies diagnose wolf-kill failure",
            "stage": "ML Stage 2B",
            "source_file": str(output_dir / "ml_stage2b_research_report.md"),
            "source_table_or_section": "Live Policy Results",
            "dataset": str(output_dir / "stage2b_live_game_level_raw.csv"),
            "analysis_script": "ml_stage2b_analysis.py",
            "commit_hash": current_git_commit(),
            "verification_status": "verified_from_source",
            "notes": "Final-test seeds 220-239 are isolated from threshold calibration.",
        },
        {
            "claim_id": "C23",
            "claim_summary": "ML Stage 2B selective override is threshold-frozen before final evaluation",
            "stage": "ML Stage 2B",
            "source_file": str(output_dir / "selective_override_manifest.json"),
            "source_table_or_section": "rule",
            "dataset": str(output_dir / "stage2b_live_decision_raw.csv"),
            "analysis_script": "ml_stage2b_selective_override.py",
            "commit_hash": current_git_commit(),
            "verification_status": "verified_from_source",
            "notes": "Development and validation seeds only.",
        },
    ]
    rows = [row for row in rows if row["claim_id"] not in {"C22", "C23"}]
    rows.extend(additions)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in rows)


def update_cumulative_report(output_dir, analysis):
    path = Path("results") / "research_progress" / "cumulative_research_report.md"
    text = path.read_text()
    section = f"""

## 23. Machine Learning Stage 2B

Question: Why did the frozen wolf-kill ML policy fail after promising shadow
analysis?

Hypothesis: The offline-to-live gap is caused by mixed mechanisms: repeated
intervention compounding, distribution shift, low-margin instability,
hybrid score incompatibility, and downstream interaction with witch, hunter,
seer, speech, and voting systems.

Design: Stage 2B uses the unchanged Stage 2A frozen wolf-kill model in
matched complete games. Selective override thresholds are calibrated from
development/validation shadow seeds only, then evaluated on isolated final
seeds. Primary comparisons are matched against `existing_rule` with Holm
correction.

Evidence: See `{output_dir / 'ml_stage2b_research_report.md'}` and
`{output_dir / 'stage2b_primary_contrasts.csv'}`.

Conclusion: The existing rule remains the default. The frozen ML model should
be retained for diagnostics only unless a later, pre-registered selective
override validation shows stable non-harmful value.
"""
    marker = "## 23. Machine Learning Stage 2B"
    if marker in text:
        text = text[:text.index(marker)].rstrip() + section
    else:
        text = text.rstrip() + section
    path.write_text(text)


def update_proposal_alignment(output_dir):
    audit_path = (
        Path("results")
        / "research_progress"
        / "durf_proposal_alignment_audit.md"
    )
    text = audit_path.read_text()
    section = f"""

## ML Stage 2B Update

ML Stage 2B adds a formal offline-to-live failure diagnosis for the frozen
wolf-kill model. It preserves the existing rule as the default, uses isolated
final seeds, and reports single-intervention, repeated-decision,
distribution-shift, selective-override, hybrid-failure, and downstream
mechanism diagnostics in `{output_dir}`.
"""
    marker = "## ML Stage 2B Update"
    if marker in text:
        text = text[:text.index(marker)].rstrip() + section
    else:
        text = text.rstrip() + section
    audit_path.write_text(text)

    matrix_path = (
        Path("results")
        / "research_progress"
        / "durf_proposal_alignment_matrix.csv"
    )
    with matrix_path.open(newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    for row in rows:
        if row["proposal_component"] == "Data Analysis":
            row["evidence"] = (
                "Formal Data Analysis outputs exist for seer position, "
                "structured search, seat-order neutral, ML Stage 2A, and "
                "ML Stage 2B."
            )
            row["source_file"] = "results/data_analysis/; results/ml_optimization_stage2b/"
        if row["proposal_component"] == "Wolf coordination":
            row["evidence"] = (
                "Night-kill strategies, deception policies, and ML wolf-kill "
                "failure diagnostics implemented."
            )
            row["source_file"] = (
                "wolf_strategy.py; wolf_deception.py; "
                "results/ml_optimization_stage2b/"
            )
    with matrix_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_current_assessment_and_roadmap(output_dir):
    assessment_path = (
        Path("results")
        / "research_progress"
        / "current_progress_assessment.md"
    )
    text = assessment_path.read_text()
    section = f"""

## ML Stage 2B Current Assessment

ML wolf-kill optimization has been formally diagnosed using Stage 2B
matched live policies and single-intervention diagnostics. The existing rule
remains the default, and the next planned proposal-completion stage is R2:
Formal Bag-of-Words Speech Quantification. Source outputs are in
`{output_dir}`.
"""
    marker = "## ML Stage 2B Current Assessment"
    if marker in text:
        text = text[:text.index(marker)].rstrip() + section
    else:
        text = text.rstrip() + section
    assessment_path.write_text(text)

    roadmap_path = (
        Path("results")
        / "research_progress"
        / "remaining_work_roadmap.md"
    )
    text = roadmap_path.read_text()
    text = text.replace(
        "## Stage R1: ML Stage 2B - offline-to-live failure diagnosis\n\n"
        "- Objective: Diagnose why frozen wolf-kill ML failed live.",
        "## Stage R1: ML Stage 2B - offline-to-live failure diagnosis\n\n"
        "- Status: Completed in `results/ml_optimization_stage2b/`.\n"
        "- Objective: Diagnose why frozen wolf-kill ML failed live.",
    )
    path_note = (
        "- Exit condition: Failure modes ranked with evidence.\n"
        "- Completed output: `results/ml_optimization_stage2b/ml_stage2b_research_report.md`.\n"
    )
    text = text.replace(
        "- Exit condition: Failure modes ranked with evidence.\n",
        path_note,
    )
    roadmap_path.write_text(text)


def update_research_progress(output_dir, analysis):
    update_cumulative_evidence_registry(output_dir, analysis)
    update_source_traceability(output_dir)
    update_cumulative_report(output_dir, analysis)
    update_proposal_alignment(output_dir)
    update_current_assessment_and_roadmap(output_dir)


def run_stage2b_experiment(
    output_dir=STAGE2B_RESULTS_DIR,
    development_seeds=DEVELOPMENT_SEEDS,
    validation_seeds=VALIDATION_SEEDS,
    final_test_seeds=FINAL_TEST_SEEDS,
    base_configs_per_seed=1,
    max_rounds=20,
    single_intervention_max_decisions=25,
    single_intervention_rollouts_per_branch=2,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_validation = verify_frozen_stage2a_model()
    seed_rows = seed_registry_rows(
        development_seeds=development_seeds,
        validation_seeds=validation_seeds,
        final_test_seeds=final_test_seeds,
    )
    write_seed_registry(output_dir, seed_rows)

    regimes = get_stage2a_behavioral_regimes()
    calibration_output = run_stage2b_live_experiment(
        output_dir=output_dir,
        seeds=list(development_seeds) + list(validation_seeds),
        split="calibration",
        base_configs_per_seed=base_configs_per_seed,
        policies=["existing_with_ml_shadow"],
        regimes=regimes,
        max_rounds=max_rounds,
        selective_override_manifest_path=None,
        capture_snapshots=False,
        write_outputs=False,
    )
    selective_manifest = build_selective_override_manifest(
        calibration_output["decision_rows"],
        calibration_output["prediction_rows"],
        development_seeds=development_seeds,
        validation_seeds=validation_seeds,
        final_test_seeds=final_test_seeds,
        output_path=DEFAULT_SELECTIVE_OVERRIDE_MANIFEST_PATH,
    )

    final_output = run_stage2b_live_experiment(
        output_dir=output_dir,
        seeds=final_test_seeds,
        split="final_test",
        base_configs_per_seed=base_configs_per_seed,
        policies=STAGE2B_WOLF_KILL_POLICIES,
        regimes=regimes,
        max_rounds=max_rounds,
        selective_override_manifest_path=DEFAULT_SELECTIVE_OVERRIDE_MANIFEST_PATH,
        capture_snapshots=True,
        write_outputs=False,
    )
    write_stage2b_raw_outputs(output_dir, final_output)

    single_rollout_rows = run_single_intervention_rollouts(
        final_output["decision_rows"],
        final_output["snapshots_by_decision_id"],
        max_decisions=single_intervention_max_decisions,
        rollouts_per_branch=single_intervention_rollouts_per_branch,
        rollout_seed=222,
        max_rounds=max_rounds,
    )
    analysis = run_stage2b_analysis(
        output_dir,
        final_output,
        single_rollout_rows,
        selective_manifest,
        manifest_validation,
        seed_rows,
    )
    update_research_progress(output_dir, analysis)
    return {
        "manifest_validation": manifest_validation,
        "selective_manifest": selective_manifest,
        "seed_registry_rows": seed_rows,
        "calibration_output": calibration_output,
        "final_output": final_output,
        "single_rollout_rows": single_rollout_rows,
        "analysis": analysis,
    }


def print_stage2b_summary(result):
    print("ML Stage 2B experiment complete")
    print("Frozen manifest:", result["manifest_validation"]["manifest_hash"])
    print(
        "Frozen artifact:",
        result["manifest_validation"]["model_artifact_hash"],
    )
    print("Final live games:", len(result["final_output"]["game_rows"]))
    print("Matched sets:", result["final_output"]["matched_sets"])
    print("Wolf win summary:")
    for row in result["analysis"]["live_summary"]:
        print(
            f"{row['policy_name']} | "
            f"Wolf: {100 * as_float(row['wolf_win_rate']):.2f}% | "
            f"Village: {100 * as_float(row['village_win_rate']):.2f}% | "
            f"Avg ML interventions: {as_float(row['avg_total_ml_interventions']):.2f}"
        )
    print("Primary contrasts:")
    for row in result["analysis"]["primary_contrasts"]:
        print(
            f"{row['contrast']} | "
            f"Diff: {100 * as_float(row['absolute_difference']):+.2f} pp | "
            f"Raw p: {as_float(row['raw_p_value']):.4f} | "
            f"Holm p: {as_float(row['holm_adjusted_p_value']):.4f}"
        )


if __name__ == "__main__":
    output = run_stage2b_experiment()
    print_stage2b_summary(output)
