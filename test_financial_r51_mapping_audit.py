from financial_r51_analysis import build_mapping_audit


def test_mapping_audit_classifies_reference_actor_and_externality():
    rows = [
        {"condition_name": "reference_strategy_mix", "role": "seer"},
        {"condition_name": "seer_highest_suspicion", "role": "seer"},
        {"condition_name": "wolf_random_kill", "role": "seer"},
    ]
    audit = build_mapping_audit(rows)
    assert audit[0]["audit_status"] == "valid_global_configuration"
    assert audit[1]["audit_status"] == "valid_actor_specific"
    assert audit[2]["audit_status"] == "valid_cross_role_externality"
