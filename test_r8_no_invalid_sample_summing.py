from r8_test_utils import read_rows


rows = read_rows("r8_sample_unit_registry.csv")
not_summable = {
    "independent_complete_game",
    "matched_configuration_set",
    "player_game_row",
    "action_event",
    "speech_utterance",
    "vote_event",
    "belief_update",
    "rollout_branch",
}
for row in rows:
    if row["unit_type"] in not_summable:
        assert row["can_be_summed_across_stages"] == "no"
print("test_r8_no_invalid_sample_summing passed")
