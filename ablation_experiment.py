from config import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_NUM_GAMES,
    DEFAULT_RANDOM_SEED,
    DEFAULT_WITCH_POISON_THRESHOLD,
)
from simulation import run_simulation, summarize_results, format_optional_float
from trust_weighted_herding_experiment import (
    get_trust_weighted_herding_experiment_configs,
)


ABLATION_DEFAULT_OVERRIDES = {
    "enable_deception_credibility": False,
    "enable_speaker_memory": False,
    "enable_trust_weighted_speech": False,
    "enable_trust_weighted_herding": False,
}


def get_stage4_ablation_configs():
    configs = []

    for config in get_trust_weighted_herding_experiment_configs():
        ablation_config = dict(config)

        if ablation_config["name"] == "speaker_memory_vote_only":
            ablation_config["name"] = "speaker_memory"

        configs.append(ablation_config)

    return configs


ABLATION_CONFIGS = [
    {
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
    },
    {
        "name": "suspicion_voting",
        "use_suspicion_voting": True,
        "enable_suspicion_update": False,
        "enable_seer": False,
        "enable_witch": False,
        "enable_hunter": False,
        "enable_speech": False,
        "enable_herding": False,
        "enable_role_prior": False,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
    },
    {
        "name": "suspicion_update",
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": False,
        "enable_witch": False,
        "enable_hunter": False,
        "enable_speech": False,
        "enable_herding": False,
        "enable_role_prior": False,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
    },
    {
        "name": "seer_action",
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": False,
        "enable_hunter": False,
        "enable_speech": False,
        "enable_herding": False,
        "enable_role_prior": False,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
    },
    {
        "name": "witch_action",
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": False,
        "enable_speech": False,
        "enable_herding": False,
        "enable_role_prior": False,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
    },
    {
        "name": "hunter_action",
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": False,
        "enable_herding": False,
        "enable_role_prior": False,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
    },
    {
        "name": "speech_enabled",
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": False,
        "enable_role_prior": False,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
    },
    {
        "name": "speech_plus_herding",
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": False,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
    },
    {
        "name": "speech_herding_role_prior",
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": True,
        "enable_wolf_strategy": False,
        "enable_wolf_deception": False,
    },
    {
        "name": "wolf_strategy",
        "use_suspicion_voting": True,
        "enable_suspicion_update": True,
        "enable_seer": True,
        "enable_witch": True,
        "enable_hunter": True,
        "enable_speech": True,
        "enable_herding": True,
        "enable_role_prior": True,
        "enable_wolf_strategy": True,
        "wolf_kill_strategy": "threat_based",
        "enable_wolf_deception": False,
    },
    {
        "name": "wolf_deception",
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
        "wolf_deception_strategy": "mixed",
    },
] + get_stage4_ablation_configs()


def run_ablation_experiment(
    num_games=DEFAULT_NUM_GAMES,
    max_rounds=DEFAULT_MAX_ROUNDS,
    seed=DEFAULT_RANDOM_SEED,
    configs=None,
):
    if configs is None:
        configs = ABLATION_CONFIGS

    experiment_results = []

    for experiment in configs:
        effective_experiment = dict(ABLATION_DEFAULT_OVERRIDES)
        effective_experiment.update(experiment)
        simulation_kwargs = {
            key: value
            for key, value in effective_experiment.items()
            if key not in {"name", "enable_wolf_deception"}
        }
        results = run_simulation(
            num_games=num_games,
            max_rounds=max_rounds,
            seed=seed,
            witch_poison_threshold=DEFAULT_WITCH_POISON_THRESHOLD,
            enable_wolf_deception=effective_experiment.get(
                "enable_wolf_deception",
                None,
            ),
            **simulation_kwargs,
        )
        summary = summarize_results(results)
        summary["name"] = effective_experiment["name"]
        experiment_results.append(summary)

    return experiment_results


def print_ablation_results(experiment_results):
    print("Ablation experiment")
    print("-------------------")

    for summary in experiment_results:
        print(
            f"{summary['name']} | "
            f"Wolf: {summary['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {summary['village_win_rate'] * 100:.2f}% | "
            f"Draw: {summary['draw_rate'] * 100:.2f}% | "
            f"Avg rounds: {summary['average_rounds']:.2f} | "
            f"Witch saves: {summary['total_witch_saves']} | "
            f"Witch poison: {summary['total_witch_poison']} | "
            f"Seer checks: {summary['total_seer_checks']} | "
            f"Hunter shots: {summary['total_hunter_shots']} | "
            f"Wolf deceptions: {summary['total_wolf_deceptions']} | "
            f"Avg wolf deceptions: "
            f"{summary['average_wolf_deceptions_per_game']:.2f} | "
            f"Accusation costs: "
            f"{summary['total_accusation_pressure_costs']} | "
            f"Wrong accusation penalties: "
            f"{summary['total_wrong_accusation_penalties']} | "
            f"Self-defense costs: "
            f"{summary['total_self_defense_credibility_costs']} | "
            f"Deception types: "
            f"{summary['total_deception_type_counts']} | "
            f"Wolf kills: {summary['total_wolf_kill_attempts']} | "
            f"Strategic wolf kills: "
            f"{summary['total_strategic_wolf_kills']} | "
            f"Avg herding: {summary['average_herding_pressure']:.2f} | "
            f"Avg trust weighted herding: "
            f"{summary['average_trust_weighted_herding_pressure']:.2f} | "
            f"Avg role prior: "
            f"{summary['average_role_prior_score']:.2f} | "
            f"Avg speech multiplier: "
            f"{summary['average_trust_speech_multiplier']:.2f} | "
            f"Avg payoff: {format_optional_float(summary['average_payoff'])} | "
            f"Wolf payoff: "
            f"{format_optional_float(summary['average_wolf_payoff'])} | "
            f"Village payoff: "
            f"{format_optional_float(summary['average_village_payoff'])}"
        )


if __name__ == "__main__":
    results = run_ablation_experiment(
        num_games=DEFAULT_NUM_GAMES,
        max_rounds=DEFAULT_MAX_ROUNDS,
        seed=DEFAULT_RANDOM_SEED,
    )
    print_ablation_results(results)
