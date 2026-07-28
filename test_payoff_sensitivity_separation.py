from payoff_manifest import build_manifest
from payoff_stage_r4_analysis import sensitivity_analysis


if __name__ == "__main__":
    manifest = build_manifest(source_commit="test")
    before_hash = manifest["manifest_hash"]
    rows = [{
        "calculation_specification": "core",
        "role": "villager",
        "condition_name": "reference",
        "terminal_team_payoff": "1.0",
        "individual_action_payoff": "0.1",
        "shared_wolf_team_bonus": "0.0",
        "survival_or_exposure_payoff": "0.0",
        "opportunity_cost": "0.0",
        "total_payoff": "1.1",
    }]
    sensitivity = sensitivity_analysis(rows)
    after_hash = build_manifest(source_commit="test")["manifest_hash"]
    assert sensitivity
    assert before_hash == after_hash
    print("test_payoff_sensitivity_separation.py passed")
