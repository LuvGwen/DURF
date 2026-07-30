from r61_common_experiment import run_policy_game
from r61_matched_design import generate_r61_matched_sets


def main():
    matched_set = generate_r61_matched_sets()[:1][0]
    row1, _ = run_policy_game("seer", "private_only", matched_set)
    row2, _ = run_policy_game("seer", "private_only", matched_set)
    assert row1["winner"] == row2["winner"]
    assert row1["seat_assignment_signature"] == row2["seat_assignment_signature"]
    print("test_r61_reproducibility.py passed")


if __name__ == "__main__":
    main()
