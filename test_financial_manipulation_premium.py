from financial_manipulation_premium import manipulation_game_ids, premium_difference


def main():
    events = [
        {"game_id": "g1", "payoff_component": "wolf_villager_voted_out_shared"},
        {"game_id": "g2", "payoff_component": "seer_investigation_used"},
    ]
    players = [
        {"game_id": "g1", "role": "werewolf", "total_payoff": "3.0"},
        {"game_id": "g2", "role": "werewolf", "total_payoff": "1.0"},
    ]
    flagged = manipulation_game_ids(events)
    metrics = premium_difference(players, flagged)
    assert flagged == {"g1"}
    assert metrics["premium"] == 2.0
    print("test_financial_manipulation_premium.py passed")


if __name__ == "__main__":
    main()
