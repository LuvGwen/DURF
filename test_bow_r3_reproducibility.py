from bow_r3_live_experiment import run_single_game


def run_once():
    matched_row = {
        "matched_set_id": "test_r3_repro",
        "seed_split": "development",
        "seed": 400,
        "behavioral_regime": "baseline_speech",
        "template_condition": "in_distribution_templates",
        "base_game_index": 1,
    }
    game, game_row = run_single_game(
        matched_row,
        "structured_bow_guarded_live",
        max_rounds=3,
    )
    votes = [
        event.get("content", {}).get("votes", {})
        for event in game.event_log
        if event["event_type"] == "day_vote"
    ]
    return game_row["winner"], votes


if __name__ == "__main__":
    first = run_once()
    second = run_once()
    assert first == second
    print("PASS: R3 live single game is reproducible")
    print("test_bow_r3_reproducibility.py passed")
