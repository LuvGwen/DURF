"""Matched-branch disagreement diagnostics for R3.

The live R3 experiment already runs all policies from identical matched-set
initial conditions. This module records disagreement states and links them to
matched full-game outcomes. It is a conservative branch proxy rather than a
separate simulator fork for every individual vote.
"""

from collections import defaultdict


PRIMARY_POLICY_MAP = {
    "guarded_bow_vote_010": "guarded_bow_010_live",
    "structured_bow_vote": "structured_bow_guarded_live",
    "pure_bow_vote_diagnostic": "pure_bow_diagnostic_live",
}


def build_game_outcome_lookup(game_rows):
    return {
        (row["matched_set_id"], row["policy_name"]): row
        for row in game_rows
    }


def as_bool(value):
    return value is True or str(value).lower() == "true"


def rollout_rows_from_vote_decisions(game_rows, vote_rows, max_rows=10000):
    lookup = build_game_outcome_lookup(game_rows)
    rows = []
    for row in vote_rows:
        if not as_bool(row.get("disagrees_with_existing")):
            continue
        existing_game = lookup.get((row["matched_set_id"], "existing_system"))
        policy_game = lookup.get((row["matched_set_id"], row["condition_name"]))
        if existing_game is None or policy_game is None:
            continue
        rows.append({
            "matched_set_id": row["matched_set_id"],
            "game_uid": row["game_uid"],
            "condition_name": row["condition_name"],
            "policy_name": row["policy_name"],
            "round": row["round"],
            "voter": row["voter"],
            "existing_target": row["existing_target"],
            "selected_target": row["selected_target"],
            "vote_is_pivotal_proxy": row.get("selected_reason")
            in {"override_allowed", "guarded_bow_vote_010", "structured_bow_vote"},
            "existing_winner": existing_game["winner"],
            "policy_winner": policy_game["winner"],
            "existing_village_win": existing_game["village_win"],
            "policy_village_win": policy_game["village_win"],
            "matched_full_game_value_delta": (
                int(as_bool(policy_game["village_win"]))
                - int(as_bool(existing_game["village_win"]))
            ),
        })
        if len(rows) >= max_rows:
            break
    return rows


def summarize_rollout_rows(rows):
    by_policy = defaultdict(list)
    for row in rows:
        by_policy[row["condition_name"]].append(row)
    output = []
    for policy_name, values in sorted(by_policy.items()):
        deltas = [float(row["matched_full_game_value_delta"]) for row in values]
        pivotal = [
            row for row in values
            if str(row.get("vote_is_pivotal_proxy")) == "True"
        ]
        output.append({
            "condition_name": policy_name,
            "disagreement_branch_rows": len(values),
            "mean_matched_value_delta": (
                sum(deltas) / len(deltas) if deltas else 0.0
            ),
            "pivotal_proxy_rows": len(pivotal),
            "non_pivotal_proxy_rows": len(values) - len(pivotal),
        })
    return output


if __name__ == "__main__":
    print(summarize_rollout_rows([]))
