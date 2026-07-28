import random

from game import Game


def day_votes(game):
    return [
        event.get("content", {}).get("votes", {})
        for event in game.event_log
        if event["event_type"] == "day_vote"
    ]


def run_game(enable_bow_r3):
    random.seed(123)
    game = Game(
        enable_bow_r3=enable_bow_r3,
        r3_belief_policy="bow_shadow_belief",
        r3_vote_policy="bow_shadow_vote",
    )
    result = game.run_game(max_rounds=4)
    return result, game


if __name__ == "__main__":
    baseline_result, baseline_game = run_game(False)
    shadow_result, shadow_game = run_game(True)
    assert baseline_result["winner"] == shadow_result["winner"]
    print("PASS: shadow mode keeps winner unchanged")
    assert day_votes(baseline_game) == day_votes(shadow_game)
    print("PASS: shadow mode keeps executed votes unchanged")
    assert any(
        event["event_type"] == "r3_bow_vote_decision"
        for event in shadow_game.event_log
    )
    print("PASS: shadow mode logs R3 vote decisions")
    print("test_bow_r3_shadow_mode.py passed")
