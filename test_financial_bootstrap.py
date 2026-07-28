from financial_r5_bootstrap import grouped_bootstrap_ci, group_rows


def main():
    rows = [
        {"game_id": "g1", "value": 1.0, "player": 1},
        {"game_id": "g1", "value": 3.0, "player": 2},
        {"game_id": "g2", "value": 5.0, "player": 1},
        {"game_id": "g2", "value": 7.0, "player": 2},
    ]
    grouped = group_rows(rows, "game_id")
    assert len(grouped["g1"]) == 2
    ci = grouped_bootstrap_ci(
        rows,
        "game_id",
        lambda sample: sum(row["value"] for row in sample) / len(sample),
        iterations=50,
        seed=1,
    )
    assert ci["bootstrap_unit"] == "game_id"
    assert ci["estimate"] == 4.0
    print("test_financial_bootstrap.py passed")


if __name__ == "__main__":
    main()
