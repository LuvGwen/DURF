from financial_stage_r5_analysis import build_dataset_registry


def main():
    player_rows = [{"game_id": "g1", "role": "seer", "condition_name": "c", "calculation_specification": "core"}]
    game_rows = [{"game_id": "g1", "condition_name": "c", "calculation_specification": "core"}]
    event_rows = [{"game_id": "g1", "actor_role": "seer", "condition_name": "c", "calculation_specification": "core"}]
    strategy_rows = [{"game_id": "g1", "role": "seer", "condition_name": "c"}]
    registry = build_dataset_registry(player_rows, game_rows, event_rows, strategy_rows)
    event_entry = next(row for row in registry if row["dataset_id"] == "r4_event_level_payoff_ledger")
    assert event_entry["allowed_for_primary_analysis"] is False
    print("test_financial_no_leakage.py passed")


if __name__ == "__main__":
    main()
