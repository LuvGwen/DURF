from config import DEFAULT_MAX_ROUNDS, DEFAULT_RANDOM_SEED
from simulation import run_simulation, summarize_results


TRUST_WEIGHTED_HERDING_EXPERIMENTS = [
    {
        "name": "speaker_memory_vote_only",
        "enable_trust_weighted_speech": False,
        "enable_trust_weighted_herding": False,
    },
    {
        "name": "trust_weighted_speech",
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": False,
    },
    {
        "name": "trust_weighted_herding",
        "enable_trust_weighted_speech": False,
        "enable_trust_weighted_herding": True,
    },
    {
        "name": "trust_weighted_speech_and_herding",
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": True,
    },
]

TRUST_WEIGHTED_HERDING_BASE_CONFIG = {
    "use_suspicion_voting": True,
    "enable_suspicion_update": True,
    "enable_seer": True,
    "enable_witch": True,
    "enable_hunter": True,
    "enable_speech": True,
    "enable_herding": True,
    "enable_role_prior": True,
    "enable_wolf_strategy": True,
    "wolf_kill_strategy": "seer_first",
    "enable_wolf_deception": True,
    "wolf_deception_policy": "adaptive",
    "enable_deception_credibility": True,
    "enable_speaker_memory": True,
    "trust_vote_weight": 0.20,
}


def get_trust_weighted_herding_experiment_configs():
    configs = []

    for experiment in TRUST_WEIGHTED_HERDING_EXPERIMENTS:
        config = dict(TRUST_WEIGHTED_HERDING_BASE_CONFIG)
        config.update(experiment)
        configs.append(config)

    return configs


def format_optional_float(value):
    if value is None:
        return "None"

    return f"{value:.2f}"


def run_trust_weighted_herding_experiment(
    num_games=500,
    seed=DEFAULT_RANDOM_SEED,
):
    experiment_results = []

    for experiment in get_trust_weighted_herding_experiment_configs():
        simulation_kwargs = {
            key: value for key, value in experiment.items()
            if key != "name"
        }
        results = run_simulation(
            num_games=num_games,
            max_rounds=DEFAULT_MAX_ROUNDS,
            seed=seed,
            **simulation_kwargs,
        )
        summary = summarize_results(results)
        summary["experiment"] = experiment["name"]
        experiment_results.append(summary)

    return experiment_results


def print_trust_weighted_herding_results(results):
    print("Trust-weighted herding experiment")
    print("---------------------------------")

    for summary in results:
        print(
            f"{summary['experiment']} | "
            f"Wolf: {summary['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {summary['village_win_rate'] * 100:.2f}% | "
            f"Draw: {summary['draw_rate'] * 100:.2f}% | "
            f"Avg rounds: {summary['average_rounds']:.2f} | "
            f"Avg herding: {summary['average_herding_pressure']:.2f} | "
            f"Avg trust weighted herding: "
            f"{summary['average_trust_weighted_herding_pressure']:.2f} | "
            f"Avg trust: {summary['average_trust_received']:.2f} | "
            f"Wolf trust: {summary['average_wolf_trust_received']:.2f} | "
            f"Village trust: "
            f"{summary['average_village_trust_received']:.2f} | "
            f"Avg speech multiplier: "
            f"{summary['average_trust_speech_multiplier']:.2f} | "
            f"Vote outcome trust updates: "
            f"{summary['total_vote_outcome_trust_updates']} | "
            f"Wolf deceptions: {summary['total_wolf_deceptions']} | "
            f"Accusation costs: "
            f"{summary['total_accusation_pressure_costs']} | "
            f"Self-defense costs: "
            f"{summary['total_self_defense_credibility_costs']} | "
            f"Wrong accusation penalties: "
            f"{summary['total_wrong_accusation_penalties']} | "
            f"Avg payoff: "
            f"{format_optional_float(summary['average_payoff'])} | "
            f"Wolf payoff: "
            f"{format_optional_float(summary['average_wolf_payoff'])} | "
            f"Village payoff: "
            f"{format_optional_float(summary['average_village_payoff'])}"
        )


if __name__ == "__main__":
    results = run_trust_weighted_herding_experiment(
        num_games=500,
        seed=DEFAULT_RANDOM_SEED,
    )
    print_trust_weighted_herding_results(results)
