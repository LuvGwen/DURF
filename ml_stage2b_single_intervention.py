import random
from collections import defaultdict

from config import DEFAULT_MAX_ROUNDS
from ml_full_counterfactual_rollout import run_single_full_rollout
from ml_train_baselines import as_float
from seat_order_neutral import stable_seed


EXISTING_CONTINUATION_POLICY = {
    "continuation_policy_id": "stage2b_existing_rule_after_forced_action",
    "description": (
        "After the forced one-step wolf kill, all later wolf kills use the "
        "existing rule."
    ),
    "config_updates": {
        "enable_ml_wolf_kill_policy": False,
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "threat_based",
        "wolf_kill_noise_level": 0.0,
    },
}


def eligible_disagreement_decisions(decision_rows, snapshots_by_decision_id):
    rows = []
    for row in decision_rows:
        if row.get("policy_name") != "existing_with_ml_shadow":
            continue
        if int(row.get("ml_existing_agree", 1)) == 1:
            continue
        if not row.get("pre_decision_snapshot_id"):
            continue
        if row["pre_decision_snapshot_id"] not in snapshots_by_decision_id:
            continue
        if not row.get("existing_rule_target_actor_uid"):
            continue
        if not row.get("frozen_ml_target_actor_uid"):
            continue
        rows.append(row)
    return rows


def deterministic_sample(rows, max_decisions, seed=42):
    ordered = sorted(rows, key=lambda row: row["decision_id"])
    if len(ordered) <= max_decisions:
        return ordered
    rng = random.Random(stable_seed("stage2b_single_intervention_sample", seed))
    keyed = [(rng.random(), row["decision_id"], row) for row in ordered]
    return [item[2] for item in sorted(keyed)[:max_decisions]]


def run_single_intervention_rollouts(
    decision_rows,
    snapshots_by_decision_id,
    max_decisions=25,
    rollouts_per_branch=2,
    rollout_seed=222,
    max_rounds=DEFAULT_MAX_ROUNDS,
):
    sampled_decisions = deterministic_sample(
        eligible_disagreement_decisions(decision_rows, snapshots_by_decision_id),
        max_decisions=max_decisions,
        seed=rollout_seed,
    )
    output = []
    for decision in sampled_decisions:
        snapshot = snapshots_by_decision_id[decision["pre_decision_snapshot_id"]]
        branches = [
            ("existing_rule_forced_once", decision["existing_rule_target_actor_uid"]),
            ("frozen_ml_forced_once", decision["frozen_ml_target_actor_uid"]),
        ]
        for branch_name, candidate_uid in branches:
            for rollout_index in range(rollouts_per_branch):
                seed = stable_seed(
                    "stage2b_single_intervention_rollout",
                    rollout_seed,
                    decision["decision_id"],
                    branch_name,
                    rollout_index,
                )
                result = run_single_full_rollout(
                    snapshot,
                    {
                        "decision_id": decision["decision_id"],
                        "decision_type": "wolf_kill",
                        "actor_uid": decision["actor_uid"],
                    },
                    candidate_uid,
                    EXISTING_CONTINUATION_POLICY,
                    seed,
                    max_rounds=max_rounds,
                )
                output.append({
                    "source_decision_id": decision["decision_id"],
                    "source_game_id": decision["game_id"],
                    "seed": decision["seed"],
                    "behavioral_regime_id": decision[
                        "behavioral_regime_id"
                    ],
                    "round": decision["round"],
                    "branch_policy": branch_name,
                    "forced_candidate_uid": candidate_uid,
                    "forced_candidate_player_id": (
                        decision["existing_rule_target"]
                        if branch_name == "existing_rule_forced_once"
                        else decision["frozen_ml_target"]
                    ),
                    "forced_candidate_role": (
                        decision.get("existing_rule_target_role", "")
                        if branch_name == "existing_rule_forced_once"
                        else decision.get("frozen_ml_target_role", "")
                    ),
                    "rollout_index": rollout_index,
                    "rollout_seed": seed,
                    "continuation_policy_id": (
                        EXISTING_CONTINUATION_POLICY[
                            "continuation_policy_id"
                        ]
                    ),
                    "wolf_team_win": result["full_rollout_team_win"],
                    "wolf_win": result["full_rollout_wolf_win"],
                    "village_win": result["full_rollout_village_win"],
                    "winner": result["full_rollout_winner"],
                    "total_rounds": result["full_rollout_total_rounds"],
                    "target_role": result["full_rollout_target_role"],
                    "target_is_special": result[
                        "full_rollout_target_is_special"
                    ],
                    "witch_save_occurred": result[
                        "full_rollout_witch_save_occurred"
                    ],
                    "hunter_retaliation_occurred": result[
                        "full_rollout_hunter_retaliation_occurred"
                    ],
                    "alive_wolves": result["full_rollout_alive_wolves"],
                    "alive_villagers": result[
                        "full_rollout_alive_villagers"
                    ],
                    "ml_advantage_over_existing": decision.get(
                        "ml_advantage_over_existing",
                        0.0,
                    ),
                    "top_two_predicted_value_margin": decision.get(
                        "top_two_predicted_value_margin",
                        0.0,
                    ),
                    "distribution_shift_category": decision.get(
                        "distribution_shift_category",
                        "",
                    ),
                })
    return output


def summarize_single_intervention_rollouts(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["source_decision_id"], row["branch_policy"])].append(row)

    by_decision = defaultdict(dict)
    for (decision_id, branch), branch_rows in grouped.items():
        by_decision[decision_id][branch] = (
            sum(as_float(row["wolf_team_win"]) for row in branch_rows)
            / len(branch_rows)
        )

    paired_diffs = []
    for decision_id, values in by_decision.items():
        if (
            "existing_rule_forced_once" in values
            and "frozen_ml_forced_once" in values
        ):
            paired_diffs.append(
                values["frozen_ml_forced_once"]
                - values["existing_rule_forced_once"]
            )

    branch_summaries = []
    branch_names = sorted({row["branch_policy"] for row in rows})
    for branch in branch_names:
        branch_rows = [row for row in rows if row["branch_policy"] == branch]
        branch_summaries.append({
            "analysis": "single_intervention_rollout",
            "branch_policy": branch,
            "rollouts": len(branch_rows),
            "source_decisions": len({
                row["source_decision_id"] for row in branch_rows
            }),
            "wolf_win_rate": (
                sum(as_float(row["wolf_team_win"]) for row in branch_rows)
                / len(branch_rows)
            ) if branch_rows else 0.0,
            "wolf_win_rate_or_value": (
                sum(as_float(row["wolf_team_win"]) for row in branch_rows)
                / len(branch_rows)
            ) if branch_rows else 0.0,
            "avg_rounds": (
                sum(as_float(row["total_rounds"]) for row in branch_rows)
                / len(branch_rows)
            ) if branch_rows else 0.0,
            "witch_save_rate": (
                sum(as_float(row["witch_save_occurred"]) for row in branch_rows)
                / len(branch_rows)
            ) if branch_rows else 0.0,
            "hunter_retaliation_rate": (
                sum(as_float(row["hunter_retaliation_occurred"]) for row in branch_rows)
                / len(branch_rows)
            ) if branch_rows else 0.0,
        })

    diff = sum(paired_diffs) / len(paired_diffs) if paired_diffs else 0.0
    branch_summaries.append({
        "analysis": "paired_single_intervention_difference",
        "branch_policy": "frozen_ml_minus_existing_rule",
        "rollouts": len(rows),
        "source_decisions": len(paired_diffs),
        "wolf_win_rate": diff,
        "wolf_win_rate_or_value": diff,
        "avg_rounds": "",
        "witch_save_rate": "",
        "hunter_retaliation_rate": "",
    })
    return branch_summaries
