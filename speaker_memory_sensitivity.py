from config import DEFAULT_MAX_ROUNDS, DEFAULT_RANDOM_SEED
from simulation import run_simulation, summarize_results


TRUST_VOTE_WEIGHTS = [0.0, 0.05, 0.10, 0.20, 0.30, 0.40]


def format_optional_float(value):
    if value is None:
        return "None"

    return f"{value:.2f}"


def run_speaker_memory_sensitivity(
    num_games=500,
    seed=DEFAULT_RANDOM_SEED,
):
    sensitivity_results = []

    for weight in TRUST_VOTE_WEIGHTS:
        results = run_simulation(
            num_games=num_games,
            max_rounds=DEFAULT_MAX_ROUNDS,
            seed=seed,
            use_suspicion_voting=True,
            enable_suspicion_update=True,
            enable_seer=True,
            enable_witch=True,
            enable_hunter=True,
            enable_speech=True,
            enable_herding=True,
            enable_role_prior=True,
            enable_wolf_strategy=True,
            wolf_kill_strategy="seer_first",
            enable_wolf_deception=True,
            wolf_deception_policy="adaptive",
            enable_deception_credibility=True,
            enable_speaker_memory=True,
            trust_vote_weight=weight,
        )
        summary = summarize_results(results)
        summary["trust_vote_weight"] = weight
        sensitivity_results.append(summary)

    return sensitivity_results


def print_speaker_memory_sensitivity(results):
    print("Speaker memory sensitivity")
    print("--------------------------")

    for summary in results:
        print(
            f"Trust vote weight: {summary['trust_vote_weight']:.2f} | "
            f"Wolf: {summary['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {summary['village_win_rate'] * 100:.2f}% | "
            f"Draw: {summary['draw_rate'] * 100:.2f}% | "
            f"Avg rounds: {summary['average_rounds']:.2f} | "
            f"Total speaker trust updates: "
            f"{summary['total_speaker_trust_updates']} | "
            f"Total vote outcome trust updates: "
            f"{summary['total_vote_outcome_trust_updates']} | "
            f"Avg trust received: "
            f"{summary['average_trust_received']:.2f} | "
            f"Avg wolf trust received: "
            f"{summary['average_wolf_trust_received']:.2f} | "
            f"Avg village trust received: "
            f"{summary['average_village_trust_received']:.2f} | "
            f"Total wolf deceptions: "
            f"{summary['total_wolf_deceptions']} | "
            f"Accusation pressure costs: "
            f"{summary['total_accusation_pressure_costs']} | "
            f"Self-defense costs: "
            f"{summary['total_self_defense_credibility_costs']} | "
            f"Wrong accusation penalties: "
            f"{summary['total_wrong_accusation_penalties']} | "
            f"Average payoff: "
            f"{format_optional_float(summary['average_payoff'])} | "
            f"Wolf payoff: "
            f"{format_optional_float(summary['average_wolf_payoff'])} | "
            f"Village payoff: "
            f"{format_optional_float(summary['average_village_payoff'])}"
        )


if __name__ == "__main__":
    results = run_speaker_memory_sensitivity(
        num_games=500,
        seed=DEFAULT_RANDOM_SEED,
    )
    print_speaker_memory_sensitivity(results)
