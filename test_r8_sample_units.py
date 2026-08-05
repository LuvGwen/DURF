from r8_test_utils import read_rows


rows = read_rows("r8_sample_unit_registry.csv")
unit_types = {row["unit_type"] for row in rows}

assert "independent_complete_game" in unit_types
assert "matched_configuration_set" in unit_types
assert "speech_utterance" in unit_types
assert "player_game_row" in unit_types
assert all(row["final_reporting_rule"] for row in rows)
print("test_r8_sample_units passed")
