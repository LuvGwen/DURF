from bow_r3_live_experiment import extract_event_rows, run_single_game


if __name__ == "__main__":
    matched_row = {
        "matched_set_id": "test_r3_1",
        "seed_split": "development",
        "seed": 400,
        "behavioral_regime": "baseline_speech",
        "template_condition": "in_distribution_templates",
        "base_game_index": 1,
    }
    game, game_row = run_single_game(
        matched_row,
        "guarded_bow_010_live",
        max_rounds=3,
    )
    assert game_row["num_r3_belief_updates"] > 0
    print("PASS: R3 live game records belief updates")
    assert game_row["num_r3_vote_decisions"] > 0
    print("PASS: R3 live game records vote decisions")
    extracted = extract_event_rows(game, game_row)
    assert len(extracted[1]) == game_row["num_r3_belief_updates"]
    print("PASS: belief update raw extraction matches event count")
    print("test_bow_r3_live_experiment.py passed")
