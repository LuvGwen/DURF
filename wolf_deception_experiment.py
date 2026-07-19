from config import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_NUM_GAMES,
    DEFAULT_RANDOM_SEED,
    DEFAULT_WITCH_POISON_THRESHOLD,
)
from simulation import run_simulation, summarize_results, format_optional_float
from wolf_deception import EXPERIMENT_WOLF_DECEPTION_STRATEGIES


def run_wolf_deception_experiment(
    strategies=None,
    num_games=DEFAULT_NUM_GAMES,
    max_rounds=DEFAULT_MAX_ROUNDS,
    seed=DEFAULT_RANDOM_SEED,
):
    if strategies is None:
        strategies = EXPERIMENT_WOLF_DECEPTION_STRATEGIES

    experiment_results = []

    for strategy in strategies:
        results = run_simulation(
            num_games=num_games,
            max_rounds=max_rounds,
            seed=seed,
            enable_wolf_strategy=True,
            wolf_kill_strategy="seer_first",
            enable_wolf_deception=True,
            wolf_deception_strategy=strategy,
            witch_poison_threshold=DEFAULT_WITCH_POISON_THRESHOLD,
        )
        summary = summarize_results(results)
        summary["wolf_deception_strategy"] = strategy
        experiment_results.append(summary)

    return experiment_results


def print_wolf_deception_results(experiment_results):
    print("Wolf deception experiment")
    print("-------------------------")

    for summary in experiment_results:
        print(
            f"Strategy: {summary['wolf_deception_strategy']} | "
            f"Wolf: {summary['wolf_win_rate'] * 100:.2f}% | "
            f"Village: {summary['village_win_rate'] * 100:.2f}% | "
            f"Draw: {summary['draw_rate'] * 100:.2f}% | "
            f"Avg rounds: {summary['average_rounds']:.2f} | "
            f"Wolf deceptions: {summary['total_wolf_deceptions']} | "
            f"Accusation costs: "
            f"{summary['total_accusation_pressure_costs']} | "
            f"Wrong accusation penalties: "
            f"{summary['total_wrong_accusation_penalties']} | "
            f"Self-defense costs: "
            f"{summary['total_self_defense_credibility_costs']} | "
            f"Deception types: "
            f"{summary['total_deception_type_counts']} | "
            f"Strategic wolf kills: "
            f"{summary['total_strategic_wolf_kills']} | "
            f"Witch saves: {summary['total_witch_saves']} | "
            f"Witch poison: {summary['total_witch_poison']} | "
            f"Seer checks: {summary['total_seer_checks']} | "
            f"Hunter shots: {summary['total_hunter_shots']} | "
            f"Avg payoff: {format_optional_float(summary['average_payoff'])} | "
            f"Wolf payoff: "
            f"{format_optional_float(summary['average_wolf_payoff'])} | "
            f"Village payoff: "
            f"{format_optional_float(summary['average_village_payoff'])}"
        )


if __name__ == "__main__":
    results = run_wolf_deception_experiment()
    print_wolf_deception_results(results)
