from statistics import mean, stdev

from config import DEFAULT_MAX_ROUNDS
from simulation import run_simulation, summarize_results


DEFAULT_SEEDS = [42, 43, 44, 45, 46]
DEFAULT_NUM_GAMES_PER_SEED = 500


RANDOM_BASELINE_CONFIG = {
    "name": "random_baseline",
    "use_suspicion_voting": False,
    "enable_suspicion_update": False,
    "enable_seer": False,
    "enable_witch": False,
    "enable_hunter": False,
    "enable_speech": False,
    "enable_herding": False,
    "enable_role_prior": False,
    "enable_wolf_strategy": False,
    "enable_wolf_deception": False,
    "enable_deception_credibility": False,
    "enable_speaker_memory": False,
    "enable_trust_weighted_speech": False,
    "enable_trust_weighted_herding": False,
}

STAGE2_FULL_CONFIG = {
    "use_suspicion_voting": True,
    "enable_suspicion_update": True,
    "enable_seer": True,
    "enable_witch": True,
    "enable_hunter": True,
    "enable_speech": True,
    "enable_herding": True,
    "enable_role_prior": True,
    "enable_wolf_strategy": True,
    "enable_wolf_deception": False,
    "enable_deception_credibility": False,
    "enable_speaker_memory": False,
    "enable_trust_weighted_speech": False,
    "enable_trust_weighted_herding": False,
}

STAGE4_BASE_CONFIG = {
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
    "wolf_deception_strategy": "adaptive",
    "enable_deception_credibility": True,
    "enable_speaker_memory": True,
    "trust_vote_weight": 0.20,
}


def get_multi_seed_experiment_configs():
    wolf_strategy_config = dict(STAGE2_FULL_CONFIG)
    wolf_strategy_config.update({
        "name": "wolf_strategy",
        "wolf_kill_strategy": "threat_based",
    })

    wolf_deception_config = dict(STAGE2_FULL_CONFIG)
    wolf_deception_config.update({
        "name": "wolf_deception",
        "wolf_kill_strategy": "seer_first",
        "enable_wolf_deception": True,
        "wolf_deception_strategy": "mixed",
    })

    speaker_memory_config = dict(STAGE4_BASE_CONFIG)
    speaker_memory_config.update({
        "name": "speaker_memory_vote_only",
        "enable_trust_weighted_speech": False,
        "enable_trust_weighted_herding": False,
    })

    trust_weighted_speech_config = dict(STAGE4_BASE_CONFIG)
    trust_weighted_speech_config.update({
        "name": "trust_weighted_speech",
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": False,
    })

    trust_weighted_herding_config = dict(STAGE4_BASE_CONFIG)
    trust_weighted_herding_config.update({
        "name": "trust_weighted_herding",
        "enable_trust_weighted_speech": False,
        "enable_trust_weighted_herding": True,
    })

    trust_weighted_speech_and_herding_config = dict(STAGE4_BASE_CONFIG)
    trust_weighted_speech_and_herding_config.update({
        "name": "trust_weighted_speech_and_herding",
        "enable_trust_weighted_speech": True,
        "enable_trust_weighted_herding": True,
    })

    return [
        dict(RANDOM_BASELINE_CONFIG),
        wolf_strategy_config,
        wolf_deception_config,
        speaker_memory_config,
        trust_weighted_speech_config,
        trust_weighted_herding_config,
        trust_weighted_speech_and_herding_config,
    ]


def average_numeric(values):
    numeric_values = [value for value in values if value is not None]

    if not numeric_values:
        return None

    return mean(numeric_values)


def stdev_numeric(values):
    numeric_values = [value for value in values if value is not None]

    if len(numeric_values) < 2:
        return 0.0

    return stdev(numeric_values)


def summarize_across_seeds(experiment_name, seed_summaries):
    if not seed_summaries:
        raise ValueError("No seed summaries to aggregate.")

    wolf_rates = [summary["wolf_win_rate"] for summary in seed_summaries]
    village_rates = [
        summary["village_win_rate"] for summary in seed_summaries
    ]
    draw_rates = [summary["draw_rate"] for summary in seed_summaries]
    average_rounds = [
        summary["average_rounds"] for summary in seed_summaries
    ]
    average_payoffs = [
        summary["average_payoff"] for summary in seed_summaries
    ]
    average_wolf_payoffs = [
        summary["average_wolf_payoff"] for summary in seed_summaries
    ]
    average_village_payoffs = [
        summary["average_village_payoff"] for summary in seed_summaries
    ]

    return {
        "name": experiment_name,
        "num_seeds": len(seed_summaries),
        "num_games_per_seed": seed_summaries[0]["total_games"],
        "total_games": sum(
            summary["total_games"] for summary in seed_summaries
        ),
        "wolf_win_rate_mean": mean(wolf_rates),
        "wolf_win_rate_min": min(wolf_rates),
        "wolf_win_rate_max": max(wolf_rates),
        "wolf_win_rate_stdev": stdev_numeric(wolf_rates),
        "village_win_rate_mean": mean(village_rates),
        "village_win_rate_min": min(village_rates),
        "village_win_rate_max": max(village_rates),
        "village_win_rate_stdev": stdev_numeric(village_rates),
        "draw_rate_mean": mean(draw_rates),
        "average_rounds_mean": mean(average_rounds),
        "average_rounds_stdev": stdev_numeric(average_rounds),
        "average_payoff_mean": average_numeric(average_payoffs),
        "average_wolf_payoff_mean": average_numeric(average_wolf_payoffs),
        "average_village_payoff_mean": average_numeric(
            average_village_payoffs
        ),
        "seed_summaries": seed_summaries,
    }


def run_multi_seed_experiment(
    num_games=DEFAULT_NUM_GAMES_PER_SEED,
    seeds=None,
    max_rounds=DEFAULT_MAX_ROUNDS,
    configs=None,
):
    if seeds is None:
        seeds = DEFAULT_SEEDS

    if configs is None:
        configs = get_multi_seed_experiment_configs()

    experiment_results = []

    for config in configs:
        experiment_name = config["name"]
        simulation_kwargs = {
            key: value for key, value in config.items()
            if key != "name"
        }
        seed_summaries = []

        for seed in seeds:
            results = run_simulation(
                num_games=num_games,
                max_rounds=max_rounds,
                seed=seed,
                **simulation_kwargs,
            )
            summary = summarize_results(results)
            summary["seed"] = seed
            seed_summaries.append(summary)

        experiment_results.append(
            summarize_across_seeds(experiment_name, seed_summaries)
        )

    return experiment_results


def format_optional_float(value):
    if value is None:
        return "None"

    return f"{value:.2f}"


def print_multi_seed_results(experiment_results):
    print("Multi-seed robustness experiment")
    print("--------------------------------")

    for result in experiment_results:
        print(
            f"{result['name']} | "
            f"Wolf mean: {result['wolf_win_rate_mean'] * 100:.2f}% | "
            f"Wolf range: "
            f"{result['wolf_win_rate_min'] * 100:.2f}%"
            f"-{result['wolf_win_rate_max'] * 100:.2f}% | "
            f"Wolf stdev: "
            f"{result['wolf_win_rate_stdev'] * 100:.2f}pp | "
            f"Village mean: "
            f"{result['village_win_rate_mean'] * 100:.2f}% | "
            f"Village range: "
            f"{result['village_win_rate_min'] * 100:.2f}%"
            f"-{result['village_win_rate_max'] * 100:.2f}% | "
            f"Draw mean: {result['draw_rate_mean'] * 100:.2f}% | "
            f"Avg rounds: {result['average_rounds_mean']:.2f} | "
            f"Avg payoff: "
            f"{format_optional_float(result['average_payoff_mean'])} | "
            f"Wolf payoff: "
            f"{format_optional_float(result['average_wolf_payoff_mean'])} | "
            f"Village payoff: "
            f"{format_optional_float(result['average_village_payoff_mean'])}"
        )

    print("\nPer-seed win rates")
    print("------------------")

    for result in experiment_results:
        seed_parts = []

        for summary in result["seed_summaries"]:
            seed_parts.append(
                f"seed {summary['seed']}: "
                f"Wolf {summary['wolf_win_rate'] * 100:.2f}% / "
                f"Village {summary['village_win_rate'] * 100:.2f}%"
            )

        print(f"{result['name']} | " + " | ".join(seed_parts))


if __name__ == "__main__":
    results = run_multi_seed_experiment()
    print_multi_seed_results(results)
