from collections import defaultdict

from ml_train_baselines import as_float


def rows_by_decision(prediction_rows):
    grouped = defaultdict(list)
    for row in prediction_rows:
        grouped[row["decision_id"]].append(row)
    return grouped


def top_by_rank(rows, rank_field):
    ordered = [
        row for row in rows
        if row.get(rank_field) not in ("", None)
    ]
    if not ordered:
        return None
    return sorted(
        ordered,
        key=lambda row: (
            int(as_float(row[rank_field])),
            str(row.get("candidate_uid")),
        ),
    )[0]


def build_hybrid_ranking_diagnostics(prediction_rows):
    output = []
    for decision_id, rows in sorted(rows_by_decision(prediction_rows).items()):
        if not rows:
            continue
        base = rows[0]
        ml_top = top_by_rank(rows, "ml_rank")
        rule_top = top_by_rank(rows, "existing_rule_rank")
        hybrid_top = top_by_rank(rows, "hybrid_rank")
        if ml_top is None or rule_top is None or hybrid_top is None:
            continue
        ml_values = [as_float(row["ml_predicted_wolf_value"]) for row in rows]
        rule_values = [
            as_float(row["observation_safe_rule_proxy_score"])
            for row in rows
        ]
        hybrid_values = [as_float(row["hybrid_score"]) for row in rows]
        output.append({
            "decision_id": decision_id,
            "policy_name": base.get("policy_name"),
            "seed": base.get("seed"),
            "behavioral_regime_id": base.get("behavioral_regime_id"),
            "round": base.get("round"),
            "ml_top_candidate": ml_top.get("candidate_player_id"),
            "rule_top_candidate": rule_top.get("candidate_player_id"),
            "hybrid_top_candidate": hybrid_top.get("candidate_player_id"),
            "ml_rule_disagree": int(
                str(ml_top.get("candidate_uid"))
                != str(rule_top.get("candidate_uid"))
            ),
            "hybrid_matches_ml": int(
                str(hybrid_top.get("candidate_uid"))
                == str(ml_top.get("candidate_uid"))
            ),
            "hybrid_matches_rule": int(
                str(hybrid_top.get("candidate_uid"))
                == str(rule_top.get("candidate_uid"))
            ),
            "hybrid_matches_neither": int(
                str(hybrid_top.get("candidate_uid"))
                not in {
                    str(ml_top.get("candidate_uid")),
                    str(rule_top.get("candidate_uid")),
                }
            ),
            "ml_score_range": max(ml_values) - min(ml_values),
            "rule_score_range": max(rule_values) - min(rule_values),
            "hybrid_score_range": max(hybrid_values) - min(hybrid_values),
            "ml_top_role": ml_top.get("candidate_role_for_posthoc_analysis"),
            "rule_top_role": rule_top.get("candidate_role_for_posthoc_analysis"),
            "hybrid_top_role": hybrid_top.get(
                "candidate_role_for_posthoc_analysis"
            ),
            "ml_top_is_special": int(
                ml_top.get("candidate_role_for_posthoc_analysis")
                in {"seer", "witch", "hunter"}
            ),
            "rule_top_is_special": int(
                rule_top.get("candidate_role_for_posthoc_analysis")
                in {"seer", "witch", "hunter"}
            ),
            "hybrid_top_is_special": int(
                hybrid_top.get("candidate_role_for_posthoc_analysis")
                in {"seer", "witch", "hunter"}
            ),
        })
    return output


def mean(values):
    numeric = [as_float(value) for value in values]
    return sum(numeric) / len(numeric) if numeric else 0.0


def summarize_hybrid_diagnostics(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get("policy_name", "")].append(row)
    output = []
    for policy_name, group_rows in sorted(grouped.items()):
        output.append({
            "policy_name": policy_name,
            "decision_rows": len(group_rows),
            "ml_rule_disagreement_rate": mean(
                row["ml_rule_disagree"] for row in group_rows
            ),
            "hybrid_matches_ml_rate": mean(
                row["hybrid_matches_ml"] for row in group_rows
            ),
            "hybrid_matches_rule_rate": mean(
                row["hybrid_matches_rule"] for row in group_rows
            ),
            "hybrid_matches_neither_rate": mean(
                row["hybrid_matches_neither"] for row in group_rows
            ),
            "avg_ml_score_range": mean(
                row["ml_score_range"] for row in group_rows
            ),
            "avg_rule_score_range": mean(
                row["rule_score_range"] for row in group_rows
            ),
            "avg_hybrid_score_range": mean(
                row["hybrid_score_range"] for row in group_rows
            ),
            "ml_top_special_rate": mean(
                row["ml_top_is_special"] for row in group_rows
            ),
            "rule_top_special_rate": mean(
                row["rule_top_is_special"] for row in group_rows
            ),
            "hybrid_top_special_rate": mean(
                row["hybrid_top_is_special"] for row in group_rows
            ),
            "diagnosis": (
                "multiple mechanisms"
                if mean(row["hybrid_matches_neither"] for row in group_rows)
                > 0.05
                else "incompatible score scales"
                if mean(row["ml_score_range"] for row in group_rows)
                != mean(row["rule_score_range"] for row in group_rows)
                else "insufficient evidence"
            ),
        })
    return output
