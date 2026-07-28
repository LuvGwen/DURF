from bow_r3_voting_policy import choose_r3_vote_target
from game_state import GameState
from player import Player
from roles import SEER, VILLAGER, WEREWOLF


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected}, got {actual}")
    print(f"PASS: {label}")


def build_state():
    voter = Player(1, VILLAGER)
    wolf = Player(2, WEREWOLF)
    seer = Player(3, SEER)
    state = GameState([voter, wolf, seer])
    return state, voter, wolf, seer


def test_pure_bow_selects_highest_signal():
    state, voter, wolf, seer = build_state()
    target, _ = choose_r3_vote_target(
        voter,
        state.players,
        state,
        policy_name="pure_bow_vote_diagnostic",
        existing_target=seer,
        signal_by_player={
            2: {"bow_signal": 0.9},
            3: {"bow_signal": 0.1},
        },
    )
    assert_equal(target.player_id, 2, "pure BoW selects highest signal")


def test_illegal_self_target_excluded():
    state, voter, wolf, seer = build_state()
    target, _ = choose_r3_vote_target(
        voter,
        state.players,
        state,
        policy_name="pure_bow_vote_diagnostic",
        existing_target=seer,
        signal_by_player={
            1: {"bow_signal": 1.0},
            2: {"bow_signal": 0.2},
            3: {"bow_signal": 0.1},
        },
    )
    assert target.player_id != voter.player_id
    print("PASS: illegal self target excluded")


def test_selective_override_guard_blocks_unseen_template():
    state, voter, wolf, seer = build_state()
    target, event = choose_r3_vote_target(
        voter,
        state.players,
        state,
        policy_name="selective_bow_vote_override",
        existing_target=seer,
        template_condition="unseen_template_families",
        signal_by_player={
            2: {
                "bow_signal": 0.95,
                "bow_information_density_score": 0.9,
                "ood_category": "strong_template_shift",
            },
            3: {"bow_signal": 0.1},
        },
    )
    assert_equal(target.player_id, 3, "strong template shift keeps existing vote")
    assert_equal(event["selected_reason"], "strong_template_shift", "guardrail reason")


if __name__ == "__main__":
    test_pure_bow_selects_highest_signal()
    test_illegal_self_target_excluded()
    test_selective_override_guard_blocks_unseen_template()
    print("test_bow_r3_voting_policy.py passed")
