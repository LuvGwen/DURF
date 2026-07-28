from financial_information_premium import premium_difference, useful_information_game_ids


def main():
    events = [
        {"game_id": "g1", "payoff_component": "seer_information_leads_to_wolf_elimination"},
        {"game_id": "g2", "payoff_component": "seer_investigation_used"},
    ]
    players = [
        {"game_id": "g1", "role": "seer", "total_payoff": "2.0"},
        {"game_id": "g2", "role": "seer", "total_payoff": "0.0"},
    ]
    flagged = useful_information_game_ids(events)
    metrics = premium_difference(players, flagged)
    assert flagged == {"g1"}
    assert metrics["premium"] == 2.0
    print("test_financial_information_premium.py passed")


if __name__ == "__main__":
    main()
