"""One-command runner for R3 guarded BoW integration."""

from bow_r3_analysis import analyze_r3_outputs
from bow_r3_live_experiment import run_r3_live_experiment


def run_bow_stage_r3_experiment(matched_games_per_cell=1):
    live_artifacts = run_r3_live_experiment(
        matched_games_per_cell=matched_games_per_cell,
    )
    analysis_artifacts = analyze_r3_outputs()
    return {
        "live": live_artifacts,
        "analysis": analysis_artifacts,
    }


if __name__ == "__main__":
    artifacts = run_bow_stage_r3_experiment()
    scale = artifacts["analysis"]["scale"]
    print("R3 BoW integration stage complete")
    print("Output directory: results/bow_integration_stage_r3")
    print(f"Matched sets: {scale['matched_set_count']}")
    print(f"Live games: {scale['live_game_count']}")
    print(f"Speech events: {scale['speech_event_count']}")
    print(f"Belief updates: {scale['belief_update_count']}")
    print(f"Vote decisions: {scale['vote_decision_count']}")
