"""R6.2 Witch potion payoff reconciliation."""

from __future__ import annotations


def reconciliation_rows(lifecycle_rows):
    rows = []
    for row in lifecycle_rows:
        rows.extend(reconcile_lifecycle_row(row))
    return rows


def reconcile_lifecycle_row(row):
    output = []
    game_id = row["game_id"]
    witch_uid = row["witch_uid"]
    policy = row["policy"]

    save_category = row.get("save_event_category", "")
    if row.get("save_used"):
        if save_category in {"save_regular_villager", "save_special_role"}:
            output.append(_row(
                game_id,
                witch_uid,
                policy,
                "save",
                "correct_save_village",
                False,
                False,
                "correct_save",
                0.3,
                False,
                "reconciled",
                "Correct save receives the R4 +0.3 anchor once.",
            ))
        elif save_category in {"save_wolf", "unnecessary_save", "invalid_save_attempt"}:
            output.append(_row(
                game_id,
                witch_uid,
                policy,
                "save",
                save_category,
                True,
                True,
                "wasted_potion",
                -0.2,
                False,
                "reconciled",
                "Primary save waste receives only the generic waste anchor.",
            ))

    poison_category = row.get("poison_event_category", "")
    if row.get("poison_used"):
        if poison_category == "correct_poison_wolf":
            output.append(_row(
                game_id,
                witch_uid,
                policy,
                "poison",
                "correct_poison_wolf",
                False,
                False,
                "correct_poison",
                0.4,
                False,
                "reconciled",
                "Correct poison receives the R4 +0.4 anchor once.",
            ))
        elif poison_category in {"poison_regular_villager", "poison_special_role"}:
            output.append(_row(
                game_id,
                witch_uid,
                policy,
                "poison",
                poison_category,
                True,
                True,
                "poison_villager",
                -0.5,
                False,
                "reconciled",
                "Wrong poison uses the poison-villager penalty and is not double-counted as generic waste.",
            ))
        elif poison_category == "invalid_poison_attempt":
            output.append(_row(
                game_id,
                witch_uid,
                policy,
                "poison",
                poison_category,
                True,
                True,
                "wasted_potion",
                -0.2,
                False,
                "reconciled",
                "Invalid consumed poison uses generic waste only.",
            ))

    for potion_type, field in [
        ("save", "save_available_at_death"),
        ("save", "save_available_at_game_end"),
        ("poison", "poison_available_at_death"),
        ("poison", "poison_available_at_game_end"),
    ]:
        if row.get(field):
            output.append(_row(
                game_id,
                witch_uid,
                policy,
                potion_type,
                field,
                False,
                True,
                "unused_potion_record",
                0.0,
                False,
                "reconciled",
                "Unused potion is recorded separately and is not primary used-potion waste.",
            ))

    return output


def _row(
    game_id,
    actor_uid,
    policy,
    potion_type,
    event_category,
    primary_waste_flag,
    extended_waste_flag,
    payoff_component,
    payoff_value,
    duplicate_penalty_flag,
    reconciliation_status,
    notes,
):
    return {
        "game_id": game_id,
        "actor_uid": actor_uid,
        "policy": policy,
        "potion_type": potion_type,
        "event_category": event_category,
        "primary_waste_flag": int(primary_waste_flag),
        "extended_waste_flag": int(extended_waste_flag),
        "payoff_component": payoff_component,
        "payoff_value": payoff_value,
        "duplicate_penalty_flag": int(duplicate_penalty_flag),
        "reconciliation_status": reconciliation_status,
        "notes": notes,
    }


WITCH_RECONCILIATION_FIELDS = [
    "game_id",
    "actor_uid",
    "policy",
    "potion_type",
    "event_category",
    "primary_waste_flag",
    "extended_waste_flag",
    "payoff_component",
    "payoff_value",
    "duplicate_penalty_flag",
    "reconciliation_status",
    "notes",
]
