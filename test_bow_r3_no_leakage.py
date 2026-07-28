from game import Game


PROHIBITED_LIVE_KEYS = {
    "speaker_role",
    "speaker_is_wolf",
    "belief_target_is_wolf",
    "existing_target_is_wolf",
    "selected_target_is_wolf",
    "eventual_winner",
    "future_vote",
    "future_elimination",
}


if __name__ == "__main__":
    game = Game(
        enable_bow_r3=True,
        r3_belief_policy="guarded_bow_010",
        r3_vote_policy="guarded_bow_vote_010",
    )
    game.run_game(max_rounds=3)
    for event in game.event_log:
        if event["event_type"] not in {
            "r3_bow_belief_update",
            "r3_bow_vote_decision",
        }:
            continue
        content_keys = set(event.get("content", {}))
        leaked = content_keys & PROHIBITED_LIVE_KEYS
        assert not leaked, f"Live R3 event leaked evaluator labels: {leaked}"
    print("PASS: live R3 events exclude evaluator-only labels")
    print("test_bow_r3_no_leakage.py passed")
