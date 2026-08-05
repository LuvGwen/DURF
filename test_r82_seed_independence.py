"""Seed-isolation tests for R8.2 targeted independent replication."""

from r61_matched_design import BEHAVIORAL_REGIMES, FINAL_SEEDS
from r82_targeted_replication import (
    R82_FINAL_SEEDS,
    R82_MATCHED_SETS_PER_MODULE,
    R82_REPLICATES_PER_SEED_REGIME,
    generate_r82_matched_sets,
)


def test_r82_seeds_do_not_overlap_r61_final_seeds():
    assert not (set(R82_FINAL_SEEDS) & set(FINAL_SEEDS))


def test_r82_matched_set_count_is_fixed():
    matched_sets = generate_r82_matched_sets()
    expected = (
        len(R82_FINAL_SEEDS)
        * len(BEHAVIORAL_REGIMES)
        * R82_REPLICATES_PER_SEED_REGIME
    )
    assert expected == R82_MATCHED_SETS_PER_MODULE
    assert len(matched_sets) == expected


def test_r82_matched_set_ids_use_r82_namespace():
    matched_sets = generate_r82_matched_sets()
    assert all(row["matched_set_id"].startswith("r82_") for row in matched_sets)
    assert all(row["seed_split"] == "r82_independent_replication" for row in matched_sets)


if __name__ == "__main__":
    test_r82_seeds_do_not_overlap_r61_final_seeds()
    test_r82_matched_set_count_is_fixed()
    test_r82_matched_set_ids_use_r82_namespace()
    print("R8.2 seed independence tests passed.")
