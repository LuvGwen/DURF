from ml_stage2b_hybrid_diagnostics import (
    build_hybrid_ranking_diagnostics,
    summarize_hybrid_diagnostics,
)


def main():
    rows = [
        {
            "decision_id": "d1",
            "policy_name": "frozen_hybrid_50_50",
            "seed": 1,
            "behavioral_regime_id": "unit",
            "round": 1,
            "candidate_uid": "a",
            "candidate_player_id": 1,
            "candidate_role_for_posthoc_analysis": "seer",
            "ml_rank": 1,
            "existing_rule_rank": 2,
            "hybrid_rank": 1,
            "ml_predicted_wolf_value": 0.8,
            "observation_safe_rule_proxy_score": 0.2,
            "hybrid_score": 0.5,
        },
        {
            "decision_id": "d1",
            "policy_name": "frozen_hybrid_50_50",
            "seed": 1,
            "behavioral_regime_id": "unit",
            "round": 1,
            "candidate_uid": "b",
            "candidate_player_id": 2,
            "candidate_role_for_posthoc_analysis": "villager",
            "ml_rank": 2,
            "existing_rule_rank": 1,
            "hybrid_rank": 2,
            "ml_predicted_wolf_value": 0.4,
            "observation_safe_rule_proxy_score": 0.6,
            "hybrid_score": 0.4,
        },
    ]
    diagnostic = build_hybrid_ranking_diagnostics(rows)
    summary = summarize_hybrid_diagnostics(diagnostic)
    assert len(diagnostic) == 1
    assert diagnostic[0]["ml_rule_disagree"] == 1
    assert summary[0]["decision_rows"] == 1
    print("hybrid_ranking_diagnostics: PASS")
    print("hybrid_summary: PASS")


if __name__ == "__main__":
    main()
