from financial_r51_analysis import holm_adjust, sign_test_p_value


def test_sign_test_detects_consistent_direction():
    assert sign_test_p_value([1, 1, 1, 1]) < 0.2
    assert sign_test_p_value([1, -1, 1, -1]) == 1.0


def test_holm_adjustment_is_monotone_within_family():
    rows = [
        {"payoff_specification": "core", "affected_role": "seer", "raw_p_value": 0.01},
        {"payoff_specification": "core", "affected_role": "seer", "raw_p_value": 0.04},
    ]
    holm_adjust(rows)
    assert rows[0]["holm_adjusted_p_value"] <= rows[1]["holm_adjusted_p_value"]
