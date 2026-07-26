import math
import random

from ml_observation_builder import stable_hash
from roles import HUNTER, SEER, WITCH, WOLF_TEAM


SPECIAL_ROLES = {SEER, WITCH, HUNTER}


class RolloutError(ValueError):
    pass


def clamp(value, lower=0.02, upper=0.98):
    return max(lower, min(upper, float(value)))


def standard_error(rate, count):
    if count <= 0:
        return 0.0
    return math.sqrt(rate * (1.0 - rate) / count)


def seeded_rng(*parts):
    return random.Random(stable_hash(parts))


def estimate_action_success_probability(decision_snapshot, candidate_action):
    if int(decision_snapshot.get("action_legal", 0)) != 1:
        raise RolloutError("Cannot evaluate an illegal candidate action.")

    decision_type = decision_snapshot.get("decision_type")
    actor_team = decision_snapshot.get("actor_team")
    candidate_is_wolf = int(decision_snapshot.get("candidate_is_wolf_label", 0))
    candidate_is_special = int(
        decision_snapshot.get("candidate_is_special_label", 0)
    )
    p_wolf = float(decision_snapshot.get("candidate_p_wolf", 0.3))
    suspicion = float(decision_snapshot.get("candidate_suspicion_score", 0.0))
    uncertainty = float(
        decision_snapshot.get("candidate_uncertainty_proxy", 0.5)
    )
    coverage = float(
        decision_snapshot.get("candidate_search_coverage_bonus", 0.0)
    )
    current_vote_count = float(
        decision_snapshot.get("candidate_current_vote_count", 0.0)
    )
    trust_from_actor = float(
        decision_snapshot.get("candidate_trust_from_actor", 0.5)
    )

    if decision_type == "seer_check":
        probability = (
            0.48
            + 0.24 * candidate_is_wolf
            - 0.05 * (1 - candidate_is_wolf)
            + 0.06 * uncertainty
            + 0.05 * coverage
            + 0.04 * p_wolf
            + 0.03 * suspicion
        )
    elif decision_type == "wolf_kill":
        hunter_risk = 1 if decision_snapshot.get(
            "true_candidate_role_label"
        ) == HUNTER else 0
        probability = (
            0.50
            + 0.13 * candidate_is_special
            - 0.04 * hunter_risk
            + 0.05 * (1.0 - suspicion)
            + 0.04 * (1.0 - p_wolf)
            + 0.03 * trust_from_actor
        )
    elif decision_type == "day_vote":
        if actor_team == WOLF_TEAM:
            probability = (
                0.50
                + 0.18 * (1 - candidate_is_wolf)
                - 0.18 * candidate_is_wolf
                + 0.04 * current_vote_count
                - 0.03 * suspicion
            )
        else:
            probability = (
                0.48
                + 0.22 * candidate_is_wolf
                - 0.15 * (1 - candidate_is_wolf)
                + 0.05 * p_wolf
                + 0.05 * suspicion
                + 0.03 * current_vote_count
            )
    else:
        raise RolloutError(f"Unsupported decision_type: {decision_type}")

    return clamp(probability)


def evaluate_candidate_action(
    decision_snapshot,
    candidate_action,
    rollout_count=20,
    rollout_seed=42,
    continuation_policy_config=None,
):
    if continuation_policy_config is None:
        continuation_policy_config = {}
    if int(decision_snapshot.get("action_legal", 0)) != 1:
        raise RolloutError("Illegal candidate action rejected.")
    if str(decision_snapshot.get("candidate_uid")) != str(candidate_action):
        raise RolloutError("Candidate action does not match snapshot row.")
    if rollout_count <= 0:
        raise RolloutError("rollout_count must be positive.")

    base_probability = estimate_action_success_probability(
        decision_snapshot,
        candidate_action,
    )
    rewards = []
    immediate = []
    secondary = []

    for rollout_index in range(rollout_count):
        rng = seeded_rng(
            "ml_stage1_rollout",
            rollout_seed,
            decision_snapshot.get("decision_id"),
            candidate_action,
            rollout_index,
            continuation_policy_config.get("policy", "fixed_baseline"),
        )
        perturbation = rng.uniform(-0.06, 0.06)
        probability = clamp(base_probability + perturbation)
        rewards.append(1 if rng.random() < probability else 0)
        immediate.append(
            int(decision_snapshot.get("candidate_is_wolf_label", 0))
            if decision_snapshot.get("decision_type") != "wolf_kill"
            else int(decision_snapshot.get("candidate_is_special_label", 0))
        )
        secondary.append(
            float(decision_snapshot.get("candidate_uncertainty_proxy", 0.0))
            + float(
                decision_snapshot.get(
                    "candidate_search_coverage_bonus",
                    0.0,
                )
            )
        )

    win_rate = sum(rewards) / rollout_count
    immediate_success_rate = sum(immediate) / len(immediate)
    secondary_mean = sum(secondary) / len(secondary)
    return {
        "rollout_count": rollout_count,
        "rollout_team_win_rate": win_rate,
        "rollout_team_win_standard_error": standard_error(
            win_rate,
            rollout_count,
        ),
        "rollout_immediate_success_rate": immediate_success_rate,
        "rollout_secondary_reward_mean": secondary_mean,
        "rollout_mode": continuation_policy_config.get(
            "rollout_mode",
            "observation_safe_surrogate",
        ),
    }


def add_rollout_values_to_rows(
    rows,
    rollout_count_by_type=None,
    rollout_seed=42,
    continuation_policy_config=None,
):
    if rollout_count_by_type is None:
        rollout_count_by_type = {
            "seer_check": 5,
            "wolf_kill": 5,
            "day_vote": 3,
        }
    valued_rows = []
    rows_by_decision = {}

    for row in rows:
        decision_type = row["decision_type"]
        rollout_count = rollout_count_by_type.get(decision_type, 3)
        value = evaluate_candidate_action(
            row,
            row["candidate_uid"],
            rollout_count=rollout_count,
            rollout_seed=rollout_seed,
            continuation_policy_config=continuation_policy_config,
        )
        valued_row = dict(row)
        valued_row.update(value)
        rows_by_decision.setdefault(row["decision_id"], []).append(valued_row)

    for decision_rows in rows_by_decision.values():
        best_value = max(
            row["rollout_team_win_rate"]
            for row in decision_rows
        )
        best_rows = [
            row for row in decision_rows
            if row["rollout_team_win_rate"] == best_value
        ]
        best_action = sorted(
            best_rows,
            key=lambda row: str(row["candidate_uid"]),
        )[0]["candidate_uid"]
        existing_values = [
            row["rollout_team_win_rate"]
            for row in decision_rows
            if int(row["action_selected_by_existing_policy"]) == 1
        ]
        existing_value = existing_values[0] if existing_values else best_value
        for row in decision_rows:
            higher_values = sum(
                1 for other in decision_rows
                if other["rollout_team_win_rate"] > row["rollout_team_win_rate"]
            )
            row["rollout_value_rank_within_decision"] = higher_values + 1
            row["rollout_best_action"] = best_action
            row["rollout_existing_policy_regret"] = (
                best_value - existing_value
            )
            valued_rows.append(row)

    return valued_rows


ROLLOUT_FIELD_COLUMNS = [
    "rollout_count",
    "rollout_team_win_rate",
    "rollout_team_win_standard_error",
    "rollout_immediate_success_rate",
    "rollout_secondary_reward_mean",
    "rollout_value_rank_within_decision",
    "rollout_best_action",
    "rollout_existing_policy_regret",
    "rollout_mode",
]
