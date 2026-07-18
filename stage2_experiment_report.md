# DURF Werewolf Simulation: Stage 2 Experiment Report

## 1. Overview

Stage 1 built a modular Werewolf simulation with a complete game loop, core roles, win-condition checking, repeated simulation, ablation experiments, and payoff calculation. The Stage 1 model established a measurable baseline for comparing how different game mechanisms affect wolf and village outcomes.

Stage 2 adds language-like and belief-based mechanisms. The goal is to move from purely action-based agents toward social deduction agents that use speech, belief, group pressure, and role priors. Instead of relying only on random voting or direct role actions, agents now produce simplified speech signals, update beliefs about who may be a wolf, and use those signals during voting.

This stage also adds strategic wolf night-kill variants and automatic result export. The exported experiment results are stored in:

- `results/ablation_results.md`
- `results/wolf_strategy_results.md`
- `results/experiment_results.md`

All reported experiments use 100 games per condition with random seed 42.

## 2. Stage 2 Mechanisms

### 2.1 Bag-of-Words Speech Signals

Stage 2 adds:

- `bow_lexicon.py`
- `speech_action.py`

Each alive player produces one simplified speech act during the day phase. Speech types include:

- `accuse`
- `defend`
- `claim_role`
- `deny`
- `agree`
- `question`
- `trust`
- `neutral`

Speech affects suspicion and belief before voting. This is not full natural language processing yet; it is a controlled Bag-of-Words style signal system. The purpose is to create a structured communication layer that can be measured and connected to voting behavior.

### 2.2 Belief Updating with `p_wolf`

Stage 2 adds:

- `belief_update.py`

Each player has a `p_wolf` value representing the model's belief that the player may be a wolf. Speech, voting behavior, and role events can update this value. Voting now uses both an external suspicion score and an internal belief probability.

The first belief-aware voting model can be summarized as:

```text
vote_score = 0.6 * suspicion_score + 0.4 * p_wolf + noise
```

Later Stage 2 mechanisms extend this score with herding pressure and role prior terms.

### 2.3 Herding Pressure

Stage 2 adds:

- `herding.py`

Herding pressure measures whether recent speech creates group pressure against a target. Accusations, agreement, and questions increase pressure. Defense and trust reduce pressure.

The voting score is extended as:

```text
vote_score =
    alpha * suspicion_score
    + beta * p_wolf
    + gamma * herding_pressure
    + noise
```

This mechanism is intended to capture a simple version of social momentum: if several players verbally pressure the same target, that target becomes more likely to receive votes.

### 2.4 Role Prior

Stage 2 adds:

- `role_prior.py`

Role prior estimates how wolf-like a player appears based on role-related information. It uses role claims, denial, seer checks, witch poison, and hunter shots.

The voting score is extended again:

```text
vote_score =
    alpha * suspicion_score
    + beta * p_wolf
    + gamma * herding_pressure
    + delta * role_prior_score
    + noise
```

The current role prior is intentionally simple. In some cases it uses true role information as a diagnostic shortcut. A future version should replace this with strictly observable public information.

### 2.5 Wolf Strategy Diagnostics

Stage 2 adds:

- `wolf_strategy.py`
- `wolf_strategy_experiment.py`

The wolf night kill is no longer limited to random target selection. The project now supports multiple night-kill strategies:

- `random`
- `threat_based`
- `seer_first`
- `witch_first`
- `avoid_hunter`
- `low_suspicion`

These strategies allow a controlled comparison of different assumptions about wolf behavior. For example, `seer_first` prioritizes the seer, while `avoid_hunter` tries to reduce the risk of triggering a hunter shot.

### 2.6 Experiment Result Export

Stage 2 adds:

- `export_results.py`

This module exports experiment outputs to Markdown and CSV without using pandas. The exported files are intended for use in the DURF progress report.

Generated files include:

- `results/ablation_results.csv`
- `results/ablation_results.md`
- `results/wolf_strategy_results.csv`
- `results/wolf_strategy_results.md`
- `results/experiment_results.md`

## 3. Experimental Setup

The default game setup contains 7 players:

- 2 werewolves
- 2 villagers
- 1 seer
- 1 witch
- 1 hunter

Each condition was evaluated for 100 games. The main metrics are:

- wolf win rate
- village win rate
- average number of rounds
- number of seer checks
- number of witch saves and poison actions
- number of hunter shots
- number of wolf night kills
- average payoff
- average wolf payoff
- average village payoff

The ablation experiment incrementally enables mechanisms to measure their effect. The wolf strategy experiment holds the broader Stage 2 model fixed while changing the wolf night-kill policy.

## 4. Ablation Experiment Results

| Experiment | Wolf Win % | Village Win % | Avg Rounds | Witch Saves | Witch Poison | Seer Checks | Hunter Shots | Wolf Kills | Avg Herding | Avg Role Prior | Avg Payoff | Wolf Payoff | Village Payoff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| random_baseline | 93.00 | 7.00 | 2.25 | 0 | 0 | 0 | 0 | 225 | 0.00 | 0.00 | -0.22 | 1.21 | -0.80 |
| suspicion_voting | 92.00 | 8.00 | 2.26 | 0 | 0 | 0 | 0 | 226 | 0.00 | 0.00 | -0.22 | 1.18 | -0.78 |
| suspicion_update | 84.00 | 16.00 | 2.21 | 0 | 0 | 0 | 0 | 221 | 0.00 | 0.00 | -0.15 | 1.01 | -0.61 |
| seer_action | 80.00 | 20.00 | 2.34 | 0 | 0 | 186 | 0 | 234 | 0.00 | 0.00 | -0.08 | 0.93 | -0.49 |
| witch_action | 58.00 | 42.00 | 2.52 | 87 | 63 | 205 | 0 | 252 | 0.00 | 0.00 | 0.10 | 0.34 | 0.01 |
| hunter_action | 58.00 | 42.00 | 2.32 | 80 | 45 | 192 | 44 | 232 | 0.00 | 0.00 | 0.09 | 0.34 | -0.01 |
| speech_enabled | 42.00 | 58.00 | 2.17 | 81 | 40 | 189 | 50 | 217 | 0.02 | 0.00 | 0.24 | -0.01 | 0.34 |
| speech_plus_herding | 38.00 | 62.00 | 1.99 | 78 | 48 | 174 | 50 | 199 | 0.02 | 0.00 | 0.29 | -0.11 | 0.44 |
| speech_herding_role_prior | 36.00 | 64.00 | 1.98 | 80 | 46 | 176 | 49 | 198 | 0.02 | 0.03 | 0.30 | -0.15 | 0.48 |
| wolf_strategy | 36.00 | 64.00 | 2.06 | 85 | 48 | 162 | 45 | 206 | 0.02 | 0.03 | 0.30 | -0.15 | 0.47 |

## 5. Wolf Strategy Experiment Results

| Strategy | Wolf Win % | Village Win % | Avg Rounds | Wolf Kills | Witch Saves | Witch Poison | Seer Checks | Hunter Shots | Avg Payoff | Wolf Payoff | Village Payoff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| random | 36.00 | 64.00 | 1.98 | 198 | 80 | 46 | 176 | 49 | 0.30 | -0.15 | 0.48 |
| threat_based | 36.00 | 64.00 | 2.06 | 206 | 85 | 48 | 162 | 45 | 0.30 | -0.15 | 0.47 |
| seer_first | 39.00 | 61.00 | 2.09 | 209 | 84 | 45 | 162 | 48 | 0.27 | -0.08 | 0.41 |
| witch_first | 33.00 | 67.00 | 2.11 | 211 | 65 | 25 | 191 | 49 | 0.32 | -0.19 | 0.52 |
| avoid_hunter | 38.00 | 62.00 | 2.09 | 209 | 83 | 48 | 161 | 33 | 0.28 | -0.10 | 0.43 |
| low_suspicion | 34.00 | 66.00 | 2.03 | 203 | 84 | 46 | 191 | 53 | 0.32 | -0.18 | 0.52 |

## 6. Main Findings

### 6.1 The baseline strongly favors wolves

The random baseline produces a 93% wolf win rate and a 7% village win rate. This confirms that without information, belief updates, or coordinated voting, the village team has little ability to identify wolves before the wolf win condition is reached.

### 6.2 Suspicion and role mechanics gradually reduce wolf dominance

Suspicion voting alone has little effect, moving village win rate from 7% to 8%. Adding suspicion updates improves village win rate to 16%. Adding seer action raises it to 20%, while witch action raises it to 42%.

This progression shows that direct information and role abilities matter more than voting structure alone.

### 6.3 Bag-of-Words speech produces the largest Stage 2 improvement

The `speech_enabled` condition raises village win rate from 42% in `hunter_action` to 58%. This is the largest jump in the Stage 2 ablation sequence.

The result suggests that even simplified speech acts can create useful social signals when connected to belief updates and voting.

### 6.4 Herding and role prior add smaller but consistent gains

Adding herding pressure increases village win rate from 58% to 62%. Adding role prior increases it to 64%.

These gains are smaller than the speech mechanism, but they are directionally consistent. They make voting more sensitive to recent social pressure and role-based evidence.

### 6.5 Current wolf strategy does not recover wolf advantage

The full `wolf_strategy` condition has the same wolf win rate as `speech_herding_role_prior`: 36%.

This means the current threat-based wolf strategy changes the distribution of night kills but does not substantially improve wolf outcomes. The village-side information mechanisms remain strong enough to preserve a village advantage.

### 6.6 Among wolf strategies, `seer_first` performs best for wolves

In the wolf strategy experiment, `seer_first` has the highest wolf win rate at 39%. This is consistent with the importance of seer information: killing the seer first weakens the village team's direct information channel.

`avoid_hunter` follows with a 38% wolf win rate and substantially fewer hunter shots than several other strategies. This suggests that avoiding hunter risk can matter, though it is not enough to restore wolf dominance.

### 6.7 `witch_first` and `low_suspicion` are less effective for wolves

`witch_first` produces a 33% wolf win rate, and `low_suspicion` produces a 34% wolf win rate. In this model, directly targeting the witch or low-suspicion players is less effective than prioritizing the seer.

One possible explanation is that seer information has an immediate and repeated effect on suspicion and belief, while the witch's effect depends on potion availability, threshold conditions, and target suspicion.

### 6.8 Payoff results align with win-rate results

The random baseline gives wolves a strong payoff advantage: wolf payoff is 1.21 and village payoff is -0.80. In the later Stage 2 conditions, wolf payoff becomes negative and village payoff becomes positive.

For example, in `speech_herding_role_prior`, wolf payoff is -0.15 and village payoff is 0.48. This confirms that the added information mechanisms affect both team outcomes and role-level incentives.

## 7. Interpretation

Stage 2 demonstrates that social information can strongly reshape the game. The baseline game is structurally wolf-favored because wolves kill every night while the village lacks reliable information. As soon as speech signals and belief updates are introduced, voting becomes more informative and village performance improves sharply.

The wolf strategy diagnostics also show that strategic killing is not automatically enough to counterbalance village information. The best wolf strategy in this experiment, `seer_first`, only reaches a 39% wolf win rate. This suggests that future wolf models may need more sophisticated coordination, deception, or speech manipulation rather than only better night-kill targeting.

## 8. Limitations

- The Bag-of-Words speech system is symbolic and simplified.
- Role prior currently uses simplified role information and should later be replaced with strictly observable evidence.
- Agents do not yet have rich individual memory or private communication histories.
- Wolves do not coordinate during the day or manipulate speech strategically.
- Each condition uses 100 games, so small differences should be interpreted cautiously.
- The model does not yet use Mesa, pandas, matplotlib, or external visualization tools.

## 9. Next Steps

1. Run larger experiments with 500 or 1000 games per condition.
2. Replace true-role role prior with public evidence based on claims and observed events.
3. Add richer player memory and individual decision policies.
4. Add wolf-side speech or deception strategies.
5. Compare results across different role setups and player counts.
6. Add optional visualization only after the core mechanisms stabilize.

## 10. Conclusion

Stage 2 successfully extends the Werewolf simulation from a role-action model into a social deduction model. The major additions are Bag-of-Words speech, `p_wolf` belief updates, herding pressure, role prior, wolf strategy diagnostics, and result export.

The experiments show that village performance improves substantially as social information is added. The random baseline has only a 7% village win rate, while the strongest Stage 2 conditions reach 64% village win rate. Wolf strategy diagnostics show that `seer_first` is currently the strongest wolf night-kill policy, but even this strategy does not recover wolf dominance.

These results provide a useful foundation for the next stage: more realistic information constraints, richer agent memory, and strategic speech behavior.
