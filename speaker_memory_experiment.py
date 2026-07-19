from config import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_NUM_GAMES,
    DEFAULT_RANDOM_SEED,
    DEFAULT_TRUST_VOTE_WEIGHT,
    DEFAULT_WITCH_POISON_THRESHOLD,
)
from simulation import run_simulation, summarize_results, format_optional_float


SPEAKER_MEMORY_EXPERIMENTS = [
    {
        "name": "adaptive_deception_without_speaker_memory",
        "enable_speaker_memory": False,
    },
    {
        "name": "adaptive_deception_with_speaker_memory",
        "enable_speaker_memory": True,
    },
]


def run_speaker_memory_experiment(
    experiments=None,
    num_games=DEFAULT_NUM_GAMES,
    max_rounds=DEFAULT_MAX_ROUNDS,
    seed=DEFAULT_RANDOM_SEED,
):
    if experiments is None:
        experiments = SPEAKER_MEMORY_EXPERIMENTS

    experiment_results = []

    for experiment in experiments:
        results = run_simulation(
            num_games=num_games,
            max_rounds=max_rounds,
            seed=seed,
            enable_wolf_strategy=True,
            wolf_kill_strategy="seer_first",
            enable_wolf_deception=True,
            wolf_deception_strategy="adaptive",
            enable_deception_credibility=True,
            enable_speaker_memory=experiment["enable_speaker_memory"],
            trust_vote_weight=DEFAULT_TRUST_VOTE_WEIGHT,
            witch_poison_threshold=DEFAULT_WITCH_POISON_THRESHOLD,
        )
        summary = summarize_results(results)
        summary["name"] = experiment["name"]
        summary["enable_speaker_memory"] = experiment["enable_speaker_memory"]
        summary["trust_vote_weight"] = DEFAULT_TRUST_VOTE_WEIGHT
        experiment_results.append(summary)

    return experiment_results


def print_speaker_memory_results(experiment_results):
    print("Speaker memory experiment")
    print("-------------------------")

    for summary in experiment_results:
        print(
            f"{summary['name']} | "
            f"Speaker memory: {summary['enable_speaker_memory']} | "
            f"Trust vote weight: {summary['trust_vote_weight']:.2f} | "
            f"Wolf: {summary['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {summary['village_win_rate'] * 100:.2f}% | "
            f"Draw: {summary['draw_rate'] * 100:.2f}% | "
            f"Avg rounds: {summary['average_rounds']:.2f} | "
            f"Wolf deceptions: {summary['total_wolf_deceptions']} | "
            f"Deception types: {summary['total_deception_type_counts']} | "
            f"Total trust updates: "
            f"{summary['total_speaker_trust_updates']} | "
            f"Total vote outcome trust updates: "
            f"{summary['total_vote_outcome_trust_updates']} | "
            f"Avg trust received: "
            f"{summary['average_trust_received']:.2f} | "
            f"Wolf avg trust received: "
            f"{summary['average_wolf_trust_received']:.2f} | "
            f"Village avg trust received: "
            f"{summary['average_village_trust_received']:.2f} | "
            f"Accusation costs: "
            f"{summary['total_accusation_pressure_costs']} | "
            f"Wrong accusation penalties: "
            f"{summary['total_wrong_accusation_penalties']} | "
            f"Self-defense costs: "
            f"{summary['total_self_defense_credibility_costs']} | "
            f"Avg payoff: {format_optional_float(summary['average_payoff'])} | "
            f"Wolf payoff: "
            f"{format_optional_float(summary['average_wolf_payoff'])} | "
            f"Village payoff: "
            f"{format_optional_float(summary['average_village_payoff'])}"
        )


if __name__ == "__main__":
    results = run_speaker_memory_experiment()
    print_speaker_memory_results(results)
