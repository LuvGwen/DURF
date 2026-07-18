from pprint import pprint

from ablation_experiment import ABLATION_CONFIGS, ABLATION_DEFAULT_OVERRIDES
from config import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_NUM_GAMES,
    DEFAULT_RANDOM_SEED,
    DEFAULT_WITCH_POISON_THRESHOLD,
)
from trust_weighted_herding_experiment import (
    get_trust_weighted_herding_experiment_configs,
)


TRUST_WEIGHTED_CONDITIONS = {
    "speaker_memory_vote_only",
    "trust_weighted_speech",
    "trust_weighted_herding",
    "trust_weighted_speech_and_herding",
}

ABLATION_CONDITIONS = {
    "speaker_memory",
    "trust_weighted_speech",
    "trust_weighted_herding",
    "trust_weighted_speech_and_herding",
    "wolf_deception",
}

COMPARISON_PAIRS = [
    ("speaker_memory_vote_only", "speaker_memory"),
    ("trust_weighted_speech", "trust_weighted_speech"),
    ("trust_weighted_herding", "trust_weighted_herding"),
    ("trust_weighted_speech_and_herding", "trust_weighted_speech_and_herding"),
]


def without_name(config):
    return {
        key: value
        for key, value in config.items()
        if key != "name"
    }


def get_ablation_effective_configs():
    configs = []

    for config in ABLATION_CONFIGS:
        effective_config = dict(ABLATION_DEFAULT_OVERRIDES)
        effective_config.update(config)
        configs.append(effective_config)

    return configs


def index_by_name(configs):
    return {
        config["name"]: config
        for config in configs
    }


def with_run_settings(config, num_games):
    full_config = {
        "num_games": num_games,
        "max_rounds": DEFAULT_MAX_ROUNDS,
        "seed": DEFAULT_RANDOM_SEED,
        "witch_poison_threshold": DEFAULT_WITCH_POISON_THRESHOLD,
    }
    full_config.update(config)
    return full_config


def print_selected_configs(title, configs_by_name, selected_names, num_games):
    print(title)
    print("-" * len(title))

    for name in selected_names:
        config = configs_by_name.get(name)

        if config is None:
            print(f"{name}: MISSING")
            continue

        print(f"{name}:")
        pprint(with_run_settings(config, num_games), sort_dicts=True)
        print()


def print_comparison(trust_configs_by_name, ablation_configs_by_name):
    print("Config parity check")
    print("-------------------")

    for trust_name, ablation_name in COMPARISON_PAIRS:
        trust_config = trust_configs_by_name.get(trust_name)
        ablation_config = ablation_configs_by_name.get(ablation_name)

        if trust_config is None or ablation_config is None:
            print(f"{trust_name} vs {ablation_name}: MISSING")
            continue

        trust_kwargs = without_name(trust_config)
        ablation_kwargs = without_name(ablation_config)

        if trust_kwargs == ablation_kwargs:
            print(f"{trust_name} vs {ablation_name}: MATCH")
            continue

        print(f"{trust_name} vs {ablation_name}: MISMATCH")
        keys = sorted(set(trust_kwargs) | set(ablation_kwargs))

        for key in keys:
            trust_value = trust_kwargs.get(key)
            ablation_value = ablation_kwargs.get(key)

            if trust_value != ablation_value:
                print(
                    f"  {key}: trust_experiment={trust_value!r}, "
                    f"ablation={ablation_value!r}"
                )


if __name__ == "__main__":
    trust_configs = get_trust_weighted_herding_experiment_configs()
    ablation_configs = get_ablation_effective_configs()
    trust_configs_by_name = index_by_name(trust_configs)
    ablation_configs_by_name = index_by_name(ablation_configs)

    print_selected_configs(
        "trust_weighted_herding_experiment.py configs",
        trust_configs_by_name,
        [
            "speaker_memory_vote_only",
            "trust_weighted_speech",
            "trust_weighted_herding",
            "trust_weighted_speech_and_herding",
        ],
        num_games=500,
    )
    print_selected_configs(
        "ablation_experiment.py configs",
        ablation_configs_by_name,
        [
            "speaker_memory",
            "trust_weighted_speech",
            "trust_weighted_herding",
            "trust_weighted_speech_and_herding",
            "wolf_deception",
        ],
        num_games=DEFAULT_NUM_GAMES,
    )
    print_comparison(trust_configs_by_name, ablation_configs_by_name)
