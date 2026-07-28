from financial_r51_analysis import event_flag_sets


def test_conservative_information_label_does_not_require_terminal_outcome():
    events = [
        {"game_id": "g1", "payoff_component": "seer_investigation_used", "target_role": "werewolf"},
    ]
    information, _manipulation = event_flag_sets(events)
    assert "g1" in information["wolf_found_by_check"]
    assert "g1" not in information["primary_useful_information"]
