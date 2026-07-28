from payoff_events import PayoffEvent


if __name__ == "__main__":
    event = PayoffEvent(
        payoff_event_id="e1",
        game_id="g1",
        matched_set_id="m1",
        seed=1,
        round=1,
        phase="day",
        actor_uid=1,
        actor_role="villager",
        actor_team="village",
        target_uid=2,
        target_role="werewolf",
        event_type="day_vote",
        event_subtype="vote_target_quality",
        payoff_component="correct_vote_for_wolf",
        calculation_specification="core",
        specification="core",
        component_category="individual_action_payoff",
        team_or_individual="individual",
        immediate_or_terminal="immediate",
        base_value=0.05,
        multiplier=1.0,
        final_value=0.05,
        manifest_version="test",
        manifest_hash="hash",
        source_action_id="source",
        explanation="test",
        order_index=0,
        evaluator_only_fields="target_role",
    )
    row = event.to_dict()
    assert row["final_value"] == "0.0500000000"
    assert row["validation_status"] == "PASS"
    print("test_payoff_events.py passed")
