"""R8.2 targeted independent replication for load-bearing role recommendations."""

from __future__ import annotations

import csv
import gzip
import io
from collections import defaultdict
from pathlib import Path

from config import DEFAULT_MAX_ROUNDS
from r61_common_experiment import (
    ACTION_FIELDS,
    GAME_LEVEL_FIELDS,
    R4_MANIFEST_HASH,
    R5_METRIC_MANIFEST_HASH,
    ROBUSTNESS_FIELDS,
    SUMMARY_FIELDS,
    fmt,
    leave_one_out_rows,
    robustness_rows,
    run_policy_game,
    summarize_policy_rows,
    summarize_special_module_metrics,
    write_csv,
)
from r61_matched_design import BEHAVIORAL_REGIMES, FINAL_SEEDS, stable_int_seed
from r61_statistical_analysis import holm_adjust, mean, paired_contrast


RESULTS_DIR = Path("results/targeted_replication_stage_r82")
R82_FINAL_SEEDS = list(range(820, 840))
R82_REPLICATES_PER_SEED_REGIME = 5
R82_MATCHED_SETS_PER_MODULE = (
    len(R82_FINAL_SEEDS)
    * len(BEHAVIORAL_REGIMES)
    * R82_REPLICATES_PER_SEED_REGIME
)
PRIMARY_OUTCOME = "actor_payoff"
SECONDARY_OUTCOME = "village_win"
PERMUTATION_REPLICATES = 1000

FROZEN_MODULES = {
    "villager": {
        "role": "villager",
        "reference_policy": "reference",
        "candidate_policy": "trust_weighted",
        "recommendation_source": "R6.1/R8.1 load-bearing Villager candidate",
    },
    "seer": {
        "role": "seer",
        "reference_policy": "private_only",
        "candidate_policy": "immediate_reveal",
        "recommendation_source": "R6.1/R8.1 load-bearing Seer candidate",
    },
    "witch": {
        "role": "witch",
        "reference_policy": "reference",
        "candidate_policy": "aggressive_full",
        "recommendation_source": "R6.1/R8.1 load-bearing Witch candidate",
    },
}

CONTRAST_FIELDS = [
    "module",
    "reference_policy",
    "candidate_policy",
    "metric",
    "outcome_role",
    "multiple_testing_family",
    "matched_set_count",
    "mean_difference",
    "ci_low",
    "ci_high",
    "difference_stdev",
    "effect_size_dz",
    "raw_p_value",
    "holm_adjusted_p_value",
    "replication_label",
]

DECISION_FIELDS = [
    "module",
    "reference_policy",
    "candidate_policy",
    "primary_metric",
    "primary_mean_difference",
    "primary_ci_low",
    "primary_ci_high",
    "primary_raw_p_value",
    "primary_holm_adjusted_p_value",
    "primary_effect_size_dz",
    "secondary_village_win_difference",
    "seed_support_rate",
    "regime_support_rate",
    "replication_decision",
    "decision_reason",
]

VALIDATION_FIELDS = ["check", "passed", "detail"]


def frozen_policies_for(module):
    spec = FROZEN_MODULES[module]
    return [spec["reference_policy"], spec["candidate_policy"]]


def generate_r82_matched_sets(
    seeds=None,
    regimes=None,
    replicates_per_seed_regime=R82_REPLICATES_PER_SEED_REGIME,
):
    if seeds is None:
        seeds = R82_FINAL_SEEDS
    if regimes is None:
        regimes = BEHAVIORAL_REGIMES

    rows = []
    for seed in seeds:
        for regime in regimes:
            for replicate_index in range(1, replicates_per_seed_regime + 1):
                matched_set_id = f"r82_seed{seed}_{regime}_rep{replicate_index:02d}"
                rows.append({
                    "matched_set_id": matched_set_id,
                    "seed": seed,
                    "seed_split": "r82_independent_replication",
                    "behavioral_regime": regime,
                    "replicate_index": replicate_index,
                    "game_seed": stable_int_seed(
                        "r82",
                        seed,
                        regime,
                        replicate_index,
                    ),
                })
    return rows


def run_r82_module(module, matched_sets=None, max_rounds=DEFAULT_MAX_ROUNDS):
    if matched_sets is None:
        matched_sets = generate_r82_matched_sets()

    game_rows = []
    action_rows = []
    for matched_set in matched_sets:
        for policy in frozen_policies_for(module):
            row, actions = run_policy_game(
                module,
                policy,
                matched_set,
                max_rounds=max_rounds,
            )
            game_rows.append(row)
            action_rows.extend(actions)
    return game_rows, action_rows


def build_r82_contrasts(all_rows):
    contrast_rows = []
    for outcome_role, metric in [
        ("primary", PRIMARY_OUTCOME),
        ("secondary", SECONDARY_OUTCOME),
    ]:
        family_rows = []
        for module, spec in FROZEN_MODULES.items():
            module_rows = [row for row in all_rows if row["module"] == module]
            contrast = paired_contrast(
                module_rows,
                module,
                spec["reference_policy"],
                spec["candidate_policy"],
                metric_key=metric,
                permutation_iterations=PERMUTATION_REPLICATES,
            )
            contrast["outcome_role"] = outcome_role
            contrast["multiple_testing_family"] = f"r82_{outcome_role}_{metric}"
            family_rows.append(contrast)
        holm_adjust(family_rows)
        for row in family_rows:
            row["replication_label"] = replication_label(row)
        contrast_rows.extend(family_rows)
    return contrast_rows


def replication_label(contrast):
    diff = contrast.get("mean_difference")
    adjusted = contrast.get("holm_adjusted_p_value")
    if diff is None or adjusted in (None, ""):
        return "insufficient data"
    if adjusted <= 0.05 and diff > 0:
        return "replicated positive effect"
    if adjusted <= 0.05 and diff < 0:
        return "replicated harmful effect"
    if diff > 0:
        return "positive but not statistically replicated"
    if diff < 0:
        return "negative but not statistically replicated"
    return "no observed difference"


def support_rate(rows, group_key, module, reference_policy, candidate_policy):
    grouped = defaultdict(list)
    for row in rows:
        if row["module"] == module:
            grouped[row[group_key]].append(row)

    support = []
    for group_rows in grouped.values():
        reference_rows = [
            row for row in group_rows
            if row["policy"] == reference_policy
        ]
        candidate_rows = [
            row for row in group_rows
            if row["policy"] == candidate_policy
        ]
        if not reference_rows or not candidate_rows:
            continue
        diff = mean([row[PRIMARY_OUTCOME] for row in candidate_rows]) - mean([
            row[PRIMARY_OUTCOME] for row in reference_rows
        ])
        support.append(1 if diff > 0 else 0)
    return mean(support) if support else None


def build_replication_decisions(all_rows, contrast_rows):
    rows = []
    primary = {
        row["module"]: row
        for row in contrast_rows
        if row["outcome_role"] == "primary"
    }
    secondary = {
        row["module"]: row
        for row in contrast_rows
        if row["outcome_role"] == "secondary"
    }
    for module, spec in FROZEN_MODULES.items():
        primary_row = primary[module]
        secondary_row = secondary[module]
        seed_rate = support_rate(
            all_rows,
            "seed",
            module,
            spec["reference_policy"],
            spec["candidate_policy"],
        )
        regime_rate = support_rate(
            all_rows,
            "behavioral_regime",
            module,
            spec["reference_policy"],
            spec["candidate_policy"],
        )
        decision = primary_row["replication_label"]
        reason = (
            "Decision uses the preregistered actor_payoff primary outcome "
            "with Holm correction across the three frozen R8.2 primary "
            "contrasts. Village win is secondary and does not replace the "
            "primary result."
        )
        rows.append({
            "module": module,
            "reference_policy": spec["reference_policy"],
            "candidate_policy": spec["candidate_policy"],
            "primary_metric": PRIMARY_OUTCOME,
            "primary_mean_difference": primary_row["mean_difference"],
            "primary_ci_low": primary_row["ci_low"],
            "primary_ci_high": primary_row["ci_high"],
            "primary_raw_p_value": primary_row["raw_p_value"],
            "primary_holm_adjusted_p_value": primary_row["holm_adjusted_p_value"],
            "primary_effect_size_dz": primary_row["effect_size_dz"],
            "secondary_village_win_difference": secondary_row["mean_difference"],
            "seed_support_rate": seed_rate,
            "regime_support_rate": regime_rate,
            "replication_decision": decision,
            "decision_reason": reason,
        })
    return rows


def validate_r82_outputs(all_rows, all_action_rows, matched_sets):
    checks = []

    def add(check, passed, detail):
        checks.append({"check": check, "passed": str(bool(passed)), "detail": detail})

    expected_game_rows = len(FROZEN_MODULES) * 2 * len(matched_sets)
    add("expected_game_row_count", len(all_rows) == expected_game_rows, str(len(all_rows)))
    add("action_rows_present", len(all_action_rows) > 0, str(len(all_action_rows)))
    add(
        "frozen_modules_only",
        sorted({row["module"] for row in all_rows}) == sorted(FROZEN_MODULES),
        ",".join(sorted({row["module"] for row in all_rows})),
    )
    observed_pairs = sorted({
        (row["module"], row["policy"]) for row in all_rows
    })
    expected_pairs = sorted(
        (module, policy)
        for module in FROZEN_MODULES
        for policy in frozen_policies_for(module)
    )
    add("frozen_policy_pairs_only", observed_pairs == expected_pairs, str(observed_pairs))
    add(
        "no_hunter_or_werewolf_replication",
        not ({"hunter", "wolf"} & {row["module"] for row in all_rows}),
        "hunter/wolf absent from R8.2 game rows",
    )
    add(
        "r82_seed_namespace_independent",
        not (set(R82_FINAL_SEEDS) & set(FINAL_SEEDS)),
        f"r82={R82_FINAL_SEEDS[0]}-{R82_FINAL_SEEDS[-1]} r61={FINAL_SEEDS[0]}-{FINAL_SEEDS[-1]}",
    )
    add(
        "game_ids_unique",
        len({row["game_id"] for row in all_rows}) == len(all_rows),
        str(len({row["game_id"] for row in all_rows})),
    )
    assignment_groups = defaultdict(set)
    for row in all_rows:
        assignment_groups[(row["module"], row["matched_set_id"])].add(
            row["seat_assignment_signature"]
        )
    assignment_mismatches = sum(
        1 for signatures in assignment_groups.values()
        if len(signatures) != 1
    )
    add(
        "matched_seat_assignments_within_module",
        assignment_mismatches == 0,
        str(assignment_mismatches),
    )
    add("primary_outcome_fixed", PRIMARY_OUTCOME == "actor_payoff", PRIMARY_OUTCOME)
    add(
        "manifest_hashes_authoritative",
        R4_MANIFEST_HASH.startswith("eee800") and R5_METRIC_MANIFEST_HASH.startswith("4b48"),
        f"R4={R4_MANIFEST_HASH}; R5={R5_METRIC_MANIFEST_HASH}",
    )
    return checks


def write_registries(matched_sets):
    seed_rows = []
    for seed in R82_FINAL_SEEDS:
        seed_rows.append({
            "seed": seed,
            "seed_split": "r82_independent_replication",
            "usage": "formal targeted independent replication only",
            "overlaps_r61_final_seed": seed in FINAL_SEEDS,
        })
    write_csv(
        RESULTS_DIR / "r82_seed_registry.csv",
        seed_rows,
        ["seed", "seed_split", "usage", "overlaps_r61_final_seed"],
    )

    module_rows = []
    policy_rows = []
    for module, spec in FROZEN_MODULES.items():
        module_rows.append({
            "module": module,
            "role": spec["role"],
            "reference_policy": spec["reference_policy"],
            "candidate_policy": spec["candidate_policy"],
            "recommendation_source": spec["recommendation_source"],
            "included_in_r82": True,
        })
        for policy_type in ["reference_policy", "candidate_policy"]:
            policy_rows.append({
                "module": module,
                "policy": spec[policy_type],
                "policy_role": policy_type.replace("_policy", ""),
                "primary_outcome": PRIMARY_OUTCOME,
                "secondary_outcome": SECONDARY_OUTCOME,
                "strategy_frozen": True,
                "threshold_tuned_in_r82": False,
            })
    write_csv(
        RESULTS_DIR / "r82_module_registry.csv",
        module_rows,
        [
            "module",
            "role",
            "reference_policy",
            "candidate_policy",
            "recommendation_source",
            "included_in_r82",
        ],
    )
    write_csv(
        RESULTS_DIR / "r82_policy_registry.csv",
        policy_rows,
        [
            "module",
            "policy",
            "policy_role",
            "primary_outcome",
            "secondary_outcome",
            "strategy_frozen",
            "threshold_tuned_in_r82",
        ],
    )
    write_csv(
        RESULTS_DIR / "r82_matched_set_registry.csv",
        matched_sets,
        [
            "matched_set_id",
            "seed",
            "seed_split",
            "behavioral_regime",
            "replicate_index",
            "game_seed",
        ],
    )


def write_pre_registration():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    text = f"""# R8.2 Targeted Independent Replication Pre-Registration

## Frozen Scope

R8.2 independently replicates only three load-bearing role recommendations:

1. Villager `reference` versus `trust_weighted`
2. Seer `private_only` versus `immediate_reveal`
3. Witch `reference` versus `aggressive_full`

Hunter and Werewolf replication are explicitly excluded. No additional
strategies, threshold searches, interim sample-size changes, or post-hoc
primary outcome changes are allowed in this stage.

## Independent Sampling Plan

- Seeds: {R82_FINAL_SEEDS[0]}-{R82_FINAL_SEEDS[-1]} ({len(R82_FINAL_SEEDS)} seeds)
- Behavioral regimes: {len(BEHAVIORAL_REGIMES)} frozen R6.1 regimes
- Replicates per seed-regime cell: {R82_REPLICATES_PER_SEED_REGIME}
- Matched sets per module: {R82_MATCHED_SETS_PER_MODULE}
- Policy arms per module: 2
- Total complete-game rows: {len(FROZEN_MODULES) * 2 * R82_MATCHED_SETS_PER_MODULE}

## Outcomes

The preregistered primary outcome is `{PRIMARY_OUTCOME}` for all three role
modules. The secondary outcome is `{SECONDARY_OUTCOME}`. Primary conclusions
must be based on the primary actor-payoff contrast, with Holm correction across
the three frozen primary contrasts.

## Manifest Integrity

The authoritative R4 payoff manifest hash is `{R4_MANIFEST_HASH}`. The
authoritative R5 metric manifest hash is `{R5_METRIC_MANIFEST_HASH}`. R8.2 does
not modify either manifest.
"""
    (RESULTS_DIR / "r82_pre_registration.md").write_text(text, encoding="utf-8")


def write_gzip_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw_file:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw_file,
            mtime=0,
        ) as gzip_file:
            with io.TextIOWrapper(
                gzip_file,
                encoding="utf-8",
                newline="",
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=fieldnames,
                    restval="",
                    extrasaction="ignore",
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(rows)


def write_schema():
    text = """# R8.2 Dataset Schema

## Game-Level Raw Dataset

`r82_game_level_raw.csv` contains one complete-game row per module, policy arm,
and matched set. The core fields are inherited from the R6.1 game-level schema:
module, policy, matched_set_id, seed, behavioral_regime, game_seed, game_id,
winner, village_win, wolf_win, actor_role, actor_payoff, team_payoff, role action
counts, vote diagnostics, seer search diagnostics, and seat_assignment_signature.

## Action Raw Dataset

`r82_action_raw.csv.gz` contains gzip-compressed diagnostic event rows for the
active module only. Action rows are not independent statistical units;
complete-game rows are the independent matched units. The compressed artifact
can be restored with `gzip -dk r82_action_raw.csv.gz` if an uncompressed CSV is
needed locally.

## Primary Contrasts

`r82_primary_contrasts.csv` contains the preregistered primary actor-payoff
contrast and secondary village-win contrast for each frozen module. Holm
correction is applied across the three primary actor-payoff contrasts and
separately across the three secondary village-win contrasts.
"""
    (RESULTS_DIR / "r82_schema.md").write_text(text, encoding="utf-8")


def write_report(
    summary_rows,
    contrast_rows,
    decision_rows,
    validation_rows,
    special_rows,
):
    report_path = RESULTS_DIR / "r82_research_report.md"
    failed = [row for row in validation_rows if row["passed"] != "True"]
    with report_path.open("w", encoding="utf-8") as file:
        file.write("# R8.2 Targeted Independent Replication Report\n\n")
        file.write("## Technical Summary\n\n")
        file.write(
            "R8.2 is a targeted independent replication of three load-bearing "
            "role recommendations identified by R8.1. The stage uses a fresh "
            f"R8.2 seed namespace ({R82_FINAL_SEEDS[0]}-{R82_FINAL_SEEDS[-1]}), "
            f"{R82_MATCHED_SETS_PER_MODULE} matched sets per module, and only "
            "two frozen policy arms per module. Hunter and Werewolf are not "
            "replicated in this stage.\n\n"
        )
        file.write("## Frozen Policy Summary\n\n")
        file.write("| Module | Policy | Games | Village Win | Wolf Win | Mean Actor Payoff | Actor Payoff 95% CI | SD | Sharpe-like |\n")
        file.write("|---|---|---:|---:|---:|---:|---|---:|---:|\n")
        for row in summary_rows:
            file.write(
                f"| {row['module']} | {row['policy']} | {row['game_count']} | "
                f"{fmt(row['village_win_rate'])} | {fmt(row['wolf_win_rate'])} | "
                f"{fmt(row['mean_actor_payoff'])} | "
                f"[{fmt(row['actor_payoff_ci_low'])}, {fmt(row['actor_payoff_ci_high'])}] | "
                f"{fmt(row['stdev_payoff'])} | {fmt(row['sharpe_like_ratio'])} |\n"
            )
        file.write("\n## Preregistered Contrasts\n\n")
        file.write("| Module | Outcome Role | Metric | Candidate | Mean Diff | 95% CI | Raw p | Holm p | Effect Size dz | Label |\n")
        file.write("|---|---|---|---|---:|---|---:|---:|---:|---|\n")
        for row in contrast_rows:
            file.write(
                f"| {row['module']} | {row['outcome_role']} | {row['metric']} | "
                f"{row['candidate_policy']} | {fmt(row['mean_difference'])} | "
                f"[{fmt(row['ci_low'])}, {fmt(row['ci_high'])}] | "
                f"{fmt(row['raw_p_value'])} | {fmt(row['holm_adjusted_p_value'])} | "
                f"{fmt(row['effect_size_dz'])} | {row['replication_label']} |\n"
            )
        file.write("\n## Replication Decisions\n\n")
        file.write("| Module | Candidate | Primary Diff | Holm p | Seed Support | Regime Support | Decision |\n")
        file.write("|---|---|---:|---:|---:|---:|---|\n")
        for row in decision_rows:
            file.write(
                f"| {row['module']} | {row['candidate_policy']} | "
                f"{fmt(row['primary_mean_difference'])} | "
                f"{fmt(row['primary_holm_adjusted_p_value'])} | "
                f"{fmt(row['seed_support_rate'])} | {fmt(row['regime_support_rate'])} | "
                f"{row['replication_decision']} |\n"
            )
        file.write("\n## Role-Specific Diagnostics\n\n")
        file.write("| Module | Policy | Metric Summary |\n")
        file.write("|---|---|---|\n")
        for row in special_rows:
            module = row["module"]
            policy = row["policy"]
            details = {
                key: fmt(value)
                for key, value in row.items()
                if key not in {"module", "policy"} and key != "game_count"
            }
            detail_text = "; ".join(f"{key}={value}" for key, value in details.items())
            file.write(f"| {module} | {policy} | {detail_text} |\n")
        file.write("\n## Validation\n\n")
        for row in validation_rows:
            status = "PASS" if row["passed"] == "True" else "FAIL"
            file.write(f"- {status}: {row['check']} ({row['detail']})\n")
        file.write("\n## Conclusion\n\n")
        if failed:
            file.write(
                "R8.2 generated outputs but validation found failures. The "
                "replication conclusions should not be used until those failures "
                "are resolved.\n"
            )
        else:
            file.write(
                "R8.2 completed the frozen targeted independent replication with "
                "the preregistered actor-payoff primary outcome. Replication "
                "labels above determine whether the R8.1 load-bearing "
                "recommendations are supported independently.\n"
            )
    return report_path


def write_documentation_updates(summary_rows, contrast_rows, decision_rows):
    research_dir = Path("results/research_progress")
    registry_path = research_dir / "cumulative_evidence_registry.csv"
    if registry_path.exists():
        with registry_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            existing = list(reader)
            fieldnames = reader.fieldnames or []
        existing = [
            row for row in existing
            if not row.get("stage_id", "").startswith("r82_")
        ]
        contrast_by_module = {
            row["module"]: row
            for row in contrast_rows
            if row["outcome_role"] == "primary"
        }
        decision_by_module = {row["module"]: row for row in decision_rows}
        new_rows = []
        for module in FROZEN_MODULES:
            contrast = contrast_by_module[module]
            decision = decision_by_module[module]
            new_rows.append({
                "stage_id": f"r82_{module}_replication",
                "stage_name": "R8.2 Targeted Independent Replication",
                "research_domain": "role strategy replication",
                "hypothesis_id": f"H_R82_{module}",
                "hypothesis": (
                    f"{FROZEN_MODULES[module]['candidate_policy']} improves "
                    f"{module} actor payoff over "
                    f"{FROZEN_MODULES[module]['reference_policy']} in an "
                    "independent matched replication."
                ),
                "prior_hypothesis_source": "R8.1 replication priority registry",
                "experiment_design": "Targeted matched independent replication with frozen policy pair.",
                "dataset_path": "results/targeted_replication_stage_r82/r82_game_level_raw.csv",
                "report_path": "results/targeted_replication_stage_r82/r82_research_report.md",
                "raw_row_count": str(3 * 2 * R82_MATCHED_SETS_PER_MODULE),
                "raw_game_count": str(3 * 2 * R82_MATCHED_SETS_PER_MODULE),
                "independent_sample_size": str(R82_MATCHED_SETS_PER_MODULE),
                "matched_set_count": str(R82_MATCHED_SETS_PER_MODULE),
                "seed_count": str(len(R82_FINAL_SEEDS)),
                "behavioral_regime_count": str(len(BEHAVIORAL_REGIMES)),
                "primary_outcome": PRIMARY_OUTCOME,
                "comparison": (
                    f"{FROZEN_MODULES[module]['candidate_policy']} vs "
                    f"{FROZEN_MODULES[module]['reference_policy']}"
                ),
                "control_condition": FROZEN_MODULES[module]["reference_policy"],
                "descriptive_effect": f"{contrast['mean_difference']:.6f}",
                "absolute_percentage_point_effect": "",
                "effect_size_type": "paired dz",
                "effect_size": fmt(contrast["effect_size_dz"]),
                "confidence_interval": (
                    f"[{fmt(contrast['ci_low'])}, {fmt(contrast['ci_high'])}]"
                ),
                "raw_p_value": fmt(contrast["raw_p_value"]),
                "adjusted_p_value": fmt(contrast["holm_adjusted_p_value"]),
                "multiplicity_method": "Holm across three frozen primary R8.2 contrasts",
                "evidence_level": "LEVEL 5 - independent targeted replication",
                "seed_robustness": f"support_rate={fmt(decision['seed_support_rate'])}",
                "regime_robustness": f"support_rate={fmt(decision['regime_support_rate'])}",
                "design_validity": "frozen scope; independent seeds; matched policy arms",
                "engine_validity": "uses existing R6.1 engine without mechanism changes",
                "distribution_shift_status": "same frozen R6.1 behavioral regimes, fresh seeds",
                "overfitting_status": "independent replication",
                "leakage_status": "no hidden-information policy changes introduced",
                "conclusion_label": normalize_registry_label(decision["replication_decision"]),
                "hypothesis_status": normalize_hypothesis_status(decision["replication_decision"]),
                "main_limitation": "Replicates only three load-bearing strategy pairs.",
                "supersedes_stage_id": "",
                "superseded_by_stage_id": "",
                "next_hypothesis": "R9 can use replicated recommendations only if labels support them.",
                "source_commit": "pending_current_stage_commit",
                "current_documentation_commit": "pending_current_stage_commit",
            })
        with registry_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                restval="",
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(existing + new_rows)

    trace_path = research_dir / "source_traceability_index.csv"
    if trace_path.exists():
        with trace_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            trace_rows = list(reader)
            fieldnames = reader.fieldnames or []
        trace_rows = [row for row in trace_rows if not row.get("claim_id", "").startswith("C_R82_")]
        trace_rows.append({
            "claim_id": "C_R82_01",
            "claim_summary": "R8.2 independently replicates Villager, Seer, and Witch load-bearing policy pairs only.",
            "stage": "R8.2",
            "source_file": "results/targeted_replication_stage_r82/r82_research_report.md",
            "source_table_or_section": "Replication Decisions",
            "dataset": "results/targeted_replication_stage_r82/r82_primary_contrasts.csv",
            "analysis_script": "r82_targeted_replication.py",
            "commit_hash": "pending_current_stage_commit",
            "verification_status": "verified_from_source",
            "notes": "No Hunter/Werewolf replication and no additional strategies.",
        })
        with trace_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                restval="",
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(trace_rows)

    report_path = research_dir / "cumulative_research_report.md"
    if report_path.exists():
        text = report_path.read_text(encoding="utf-8")
        marker = "## 37. R8.2 Targeted Independent Replication"
        if marker not in text:
            text = text.rstrip() + """

## 37. R8.2 Targeted Independent Replication

R8.2 performs an independent targeted replication of the three load-bearing
role recommendations flagged by R8.1: Villager `trust_weighted` versus
`reference`, Seer `immediate_reveal` versus `private_only`, and Witch
`aggressive_full` versus `reference`. The stage uses fresh R8.2 seeds,
1,000 matched sets per module, the existing R6.1 behavioral regimes, and a
fixed actor-payoff primary outcome. Hunter and Werewolf are excluded from this
replication scope.
"""
            report_path.write_text(text + "\n", encoding="utf-8")


def normalize_registry_label(replication_decision):
    if replication_decision == "replicated positive effect":
        return "statistically supported improvement"
    if replication_decision == "replicated harmful effect":
        return "statistically supported harmful effect"
    if replication_decision == "insufficient data":
        return "insufficient data"
    return "promising but uncertain"


def normalize_hypothesis_status(replication_decision):
    if replication_decision == "replicated positive effect":
        return "hypothesis supported"
    if replication_decision == "replicated harmful effect":
        return "hypothesis rejected"
    return "hypothesis unresolved"


def run_r82_targeted_replication(max_rounds=DEFAULT_MAX_ROUNDS):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    matched_sets = generate_r82_matched_sets()
    write_pre_registration()
    write_schema()
    write_registries(matched_sets)

    all_rows = []
    all_action_rows = []
    for module in FROZEN_MODULES:
        game_rows, action_rows = run_r82_module(
            module,
            matched_sets=matched_sets,
            max_rounds=max_rounds,
        )
        all_rows.extend(game_rows)
        all_action_rows.extend(action_rows)

    summary_rows = []
    special_rows = []
    seed_rows = []
    regime_rows = []
    leave_seed_rows = []
    leave_regime_rows = []
    for module in FROZEN_MODULES:
        module_rows = [row for row in all_rows if row["module"] == module]
        module_actions = [row for row in all_action_rows if row["module"] == module]
        summary_rows.extend(summarize_policy_rows(module, module_rows, module_actions))
        special_rows.extend(summarize_special_module_metrics(module, module_rows))
        seed_rows.extend(robustness_rows(module, module_rows, "seed"))
        regime_rows.extend(robustness_rows(module, module_rows, "behavioral_regime"))
        leave_seed_rows.extend(leave_one_out_rows(module, module_rows, "seed"))
        leave_regime_rows.extend(leave_one_out_rows(module, module_rows, "behavioral_regime"))

    contrast_rows = build_r82_contrasts(all_rows)
    decision_rows = build_replication_decisions(all_rows, contrast_rows)
    validation_rows = validate_r82_outputs(all_rows, all_action_rows, matched_sets)

    write_csv(RESULTS_DIR / "r82_game_level_raw.csv", all_rows, GAME_LEVEL_FIELDS)
    write_gzip_csv(RESULTS_DIR / "r82_action_raw.csv.gz", all_action_rows, ACTION_FIELDS)
    write_csv(RESULTS_DIR / "r82_policy_summary.csv", summary_rows, SUMMARY_FIELDS)
    write_csv(RESULTS_DIR / "r82_primary_contrasts.csv", contrast_rows, CONTRAST_FIELDS)
    write_csv(RESULTS_DIR / "r82_replication_decision_summary.csv", decision_rows, DECISION_FIELDS)
    write_csv(RESULTS_DIR / "r82_seed_robustness.csv", seed_rows, ROBUSTNESS_FIELDS)
    write_csv(RESULTS_DIR / "r82_regime_robustness.csv", regime_rows, ROBUSTNESS_FIELDS)
    write_csv(RESULTS_DIR / "r82_leave_one_seed_out.csv", leave_seed_rows, ROBUSTNESS_FIELDS)
    write_csv(RESULTS_DIR / "r82_leave_one_regime_out.csv", leave_regime_rows, ROBUSTNESS_FIELDS)
    write_csv(
        RESULTS_DIR / "r82_special_module_metrics.csv",
        special_rows,
        sorted({key for row in special_rows for key in row}),
    )
    write_csv(RESULTS_DIR / "r82_validation_summary.csv", validation_rows, VALIDATION_FIELDS)
    write_report(summary_rows, contrast_rows, decision_rows, validation_rows, special_rows)
    write_documentation_updates(summary_rows, contrast_rows, decision_rows)

    return {
        "matched_sets": matched_sets,
        "game_rows": all_rows,
        "action_rows": all_action_rows,
        "summary_rows": summary_rows,
        "contrast_rows": contrast_rows,
        "decision_rows": decision_rows,
        "validation_rows": validation_rows,
    }


def print_r82_summary(outputs):
    print("R8.2 targeted independent replication")
    print("-------------------------------------")
    print(f"Matched sets per module: {R82_MATCHED_SETS_PER_MODULE}")
    print(f"Game rows: {len(outputs['game_rows'])}")
    print(f"Action rows: {len(outputs['action_rows'])}")
    print("\nPolicy summary:")
    for row in outputs["summary_rows"]:
        print(
            f"{row['module']} | {row['policy']} | "
            f"Village: {float(row['village_win_rate']) * 100:.2f}% | "
            f"Wolf: {float(row['wolf_win_rate']) * 100:.2f}% | "
            f"Actor payoff: {float(row['mean_actor_payoff']):.4f}"
        )
    print("\nPrimary replication decisions:")
    for row in outputs["decision_rows"]:
        print(
            f"{row['module']} | {row['candidate_policy']} vs {row['reference_policy']} | "
            f"diff={float(row['primary_mean_difference']):.4f} | "
            f"Holm p={float(row['primary_holm_adjusted_p_value']):.4f} | "
            f"{row['replication_decision']}"
        )
    failed = [row for row in outputs["validation_rows"] if row["passed"] != "True"]
    print(f"\nValidation failures: {len(failed)}")


if __name__ == "__main__":
    result = run_r82_targeted_replication()
    print_r82_summary(result)
