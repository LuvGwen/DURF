TRAIN_SEEDS = set(range(42, 50))
VALIDATION_SEEDS = {50, 51}
FINAL_TEST_SEEDS = set(range(52, 57))


def split_for_seed_and_regime(seed, behavioral_regime_id):
    if behavioral_regime_id in {
        "deception_enabled_policy",
        "risk_heterogeneous_policy",
    }:
        return "ood_test", "C_out_of_distribution"
    if seed in TRAIN_SEEDS:
        return "train", "A_in_distribution"
    if seed in VALIDATION_SEEDS:
        return "validation", "A_in_distribution"
    if seed in FINAL_TEST_SEEDS:
        return "final_test", "B_unseen_seed"
    return "train", "A_in_distribution"


def make_base_configuration_id(behavioral_regime_id, seed, base_game_index):
    return (
        f"regime_{behavioral_regime_id}_"
        f"seed_{seed}_base_{base_game_index}"
    )


def make_game_family_id(behavioral_regime_id, seed, base_game_index):
    return (
        f"regime_{behavioral_regime_id}_"
        f"seed_{seed}_base_{base_game_index}"
    )


def make_split_group_id(behavioral_regime_id, seed, base_game_index):
    return make_game_family_id(behavioral_regime_id, seed, base_game_index)


def assign_grouped_split(row):
    split_name, split_level = split_for_seed_and_regime(
        int(row["seed"]),
        row["behavioral_regime_id"],
    )
    row["split_name"] = split_name
    row["split_level"] = split_level
    row["base_configuration_id"] = make_base_configuration_id(
        row["behavioral_regime_id"],
        row["seed"],
        row["base_game_index"],
    )
    row["game_family_id"] = make_game_family_id(
        row["behavioral_regime_id"],
        row["seed"],
        row["base_game_index"],
    )
    row["split_group_id"] = make_split_group_id(
        row["behavioral_regime_id"],
        row["seed"],
        row["base_game_index"],
    )
    return row


def validate_grouped_splits(rows):
    errors = []
    for group_field in [
        "split_group_id",
        "game_family_id",
        "base_configuration_id",
    ]:
        groups = {}
        for row in rows:
            key = row[group_field]
            split = row["split_name"]
            if key in groups and groups[key] != split:
                errors.append(
                    f"{group_field} {key} crosses splits "
                    f"{groups[key]} and {split}."
                )
            groups[key] = split
    final_test_rows = [
        row for row in rows
        if row["split_name"] == "final_test"
    ]
    if not final_test_rows:
        errors.append("No final_test rows were generated.")
    return {
        "valid": not errors,
        "errors": errors,
        "split_counts": {
            split: sum(1 for row in rows if row["split_name"] == split)
            for split in ["train", "validation", "final_test", "ood_test"]
        },
    }
