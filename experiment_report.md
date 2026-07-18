# DURF Werewolf Simulation: Stage 1 Experiment Report

## Background

This project aims to build an agent-based Werewolf simulation for studying how information, suspicion, and role abilities affect social deduction outcomes. The current framework starts from a minimal random baseline and gradually adds modular mechanisms, including suspicion-based voting, vote-driven suspicion updates, seer checks, witch actions, hunter shots, and payoff calculation.

The long-term goal is to use this simulation as a controlled environment for studying social deduction dynamics. Stage 1 focuses on making the game loop complete and experimentally measurable. Later stages will introduce Bag-of-Words language signals, belief updating, and more strategic decision models.

## Current Code Structure

- `roles.py`: role constants and team mapping
- `player.py`: player state, suspicion score, p_wolf, memory, potion states
- `game_state.py`: round, phase, alive/dead players, win condition
- `game.py`: main game loop and phase logic
- `voting.py`: suspicion-based voting
- `suspicion_update.py`: vote-based suspicion updates
- `seer_action.py`: seer information action
- `witch_action.py`: witch save and poison actions
- `hunter_action.py`: hunter death-shot action
- `payoff.py`: role-level payoff calculation
- `simulation.py`: repeated simulation and summary statistics
- `ablation_experiment.py`: mechanism comparison experiments
- `config.py`: default parameters

## Experimental Setup

Each ablation condition was evaluated with 500 games using a fixed random seed. The simulation uses simplified Werewolf rules. The village team wins if all wolves are eliminated. The wolf team wins if the number of alive wolves is greater than or equal to the number of alive village-team players.

After the hunter implementation, the default role setup is a 7-player game:

- 2 werewolves
- 2 villagers
- 1 seer
- 1 witch
- 1 hunter

## Ablation Conditions

1. `random_baseline`
   - Random day voting
   - No suspicion update
   - No seer
   - No witch
   - No hunter

2. `suspicion_voting`
   - Suspicion-based voting enabled
   - No suspicion update

3. `suspicion_update`
   - Suspicion-based voting
   - Vote-based suspicion update

4. `seer_action`
   - Suspicion update
   - Seer checks at night

5. `witch_action`
   - Seer enabled
   - Witch save and poison enabled

6. `hunter_action`
   - Full model with hunter death-shot enabled

## Results Table

| Condition | Wolf Win % | Village Win % | Draw % | Avg Rounds | Witch Saves | Witch Poison | Seer Checks | Hunter Shots | Avg Payoff | Wolf Payoff | Village Payoff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_baseline | 93.00 | 7.00 | 0.00 | 2.25 | 0 | 0 | 0 | 0 | -0.22 | 1.21 | -0.80 |
| suspicion_voting | 91.00 | 9.00 | 0.00 | 2.25 | 0 | 0 | 0 | 0 | -0.21 | 1.16 | -0.76 |
| suspicion_update | 85.00 | 15.00 | 0.00 | 2.20 | 0 | 0 | 0 | 0 | -0.16 | 1.03 | -0.63 |
| seer_action | 77.00 | 23.00 | 0.00 | 2.39 | 0 | 0 | 182 | 0 | -0.06 | 0.86 | -0.42 |
| witch_action | 51.00 | 49.00 | 0.00 | 2.44 | 87 | 58 | 208 | 0 | 0.17 | 0.19 | 0.16 |
| hunter_action | 54.00 | 46.00 | 0.00 | 2.23 | 83 | 45 | 186 | 41 | 0.13 | 0.25 | 0.07 |

## Key Findings

### Finding 1: Random play heavily favors wolves

The random baseline strongly favors the wolf team, with a 93% wolf win rate and only a 7% village win rate. Wolves benefit from guaranteed night kills and from the village team's lack of reliable information. Without discussion, inference, or informative voting patterns, the village team has little ability to identify wolves before the wolf win condition is reached.

### Finding 2: Suspicion voting alone has limited effect

Suspicion-based voting without suspicion updates only slightly improves village performance, raising the village win rate from 7% to 9%. This small change is expected because suspicion scores are not informative unless they are updated by game events. In this condition, voting is structurally different from random voting, but the underlying scores still contain almost no signal.

### Finding 3: Vote-based suspicion update improves village performance

Adding vote-based suspicion updates increases the village win rate from 9% to 15%. This suggests that accumulated voting history creates weak but useful information. The mechanism is still hand-coded and simple, but it allows later votes to respond to earlier behavior rather than remaining purely random.

### Finding 4: Seer information produces a stronger improvement

Adding seer checks increases the village win rate from 15% to 23%. The seer mechanism injects direct information into suspicion scores, which gives the village team a stronger basis for identifying wolves. This confirms that even simple private information can substantially alter social deduction outcomes.

### Finding 5: Witch action is the largest improvement so far

The witch action produces the largest village improvement in the current model, increasing the village win rate from 23% to 49%. Witch saves extend game duration and can prevent immediate loss of village-team players. Witch poison also creates a direct removal mechanism, allowing high-suspicion targets to be eliminated outside of the day vote.

### Finding 6: Hunter action adds complexity but does not strictly improve village win rate in this configuration

The hunter condition gives the village team a 46% win rate, compared with 49% in the witch-only condition. This does not mean the hunter is ineffective in general. Instead, it suggests that the current hunter implementation adds both benefits and risks. The hunter can shoot incorrectly, and the 7-player role composition changes the balance of the game. In this configuration, the hunter increases interaction complexity but does not strictly improve village win rate.

## Payoff Interpretation

The payoff results show how role mechanisms change not only win rates but also player-level incentives. In the random baseline, wolves have a very large payoff advantage: wolf payoff is 1.21 while village payoff is -0.80. This reflects the structural advantage wolves have when the village lacks information.

As information and village abilities are added, the payoff gap narrows. In the `witch_action` condition, payoffs become nearly balanced, with wolf payoff at 0.19 and village payoff at 0.16. This aligns with the near-balanced win rate in that condition.

In the `hunter_action` condition, wolves regain a slight payoff advantage, with wolf payoff at 0.25 and village payoff at 0.07. This is consistent with the win-rate result, where hunter action adds complexity but does not strictly improve village outcomes in the current configuration.

## Current Limitations

- No natural language or Bag-of-Words signal has been implemented yet.
- Suspicion updates are still hand-coded.
- Seer and witch knowledge is directly translated into suspicion score instead of being communicated through discussion.
- Wolves do not strategically coordinate beyond random night kills.
- Voting does not yet include herding pressure or role prior.
- The payoff matrix is simplified.
- Mesa integration has not been added yet.

## Next Steps

1. Implement Bag-of-Words speech signals.
2. Add `p_wolf` belief update based on speech and actions.
3. Add herding pressure to voting.
4. Add role prior to voting.
5. Add wolf strategy instead of random killing.
6. Run larger simulations with 1000+ games.
7. Export experiment results to CSV later.
8. Compare model behavior to social deduction theory and related papers.

## Conclusion

The Stage 1 framework successfully runs complete Werewolf games with modular role mechanisms and payoff calculation. The ablation experiment shows that information mechanisms systematically reduce wolf dominance, with witch and seer abilities producing the strongest improvements for the village team. The framework is now ready for the next stage: introducing language-based signals and belief updating.
