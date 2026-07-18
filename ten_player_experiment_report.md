# Ten-Player Werewolf Experiment Report

## 1. Purpose

This experiment extends the existing 7-player Werewolf simulation to a larger 10-player setup: 3 werewolves, 1 seer, 1 witch, 1 hunter, and 4 villagers. The goal is not to replace the original 7-player model, but to test whether the same mechanisms generalize to a larger and noisier setting.

The 10-player setup increases the number of hidden adversaries and creates more communication noise. This makes it a useful stress test for the model's speech, deception, credibility, and trust mechanisms.

## 2. Model Adjustment

The main model adjustment is the role setup. The original default setup remains the 7-player game, while the 10-player setup is added as a separate experimental condition.

The 10-player configuration uses:

- 3 werewolves
- 1 seer
- 1 witch
- 1 hunter
- 4 villagers

The initial `p_wolf` value is set near 0.30 because 3 out of 10 players are wolves. The speech signal impact is scaled down to reduce the effect of any single statement in a larger game. Herding impact is also scaled down to avoid excessive early group pressure. Credibility costs are scaled down so that three wolves do not lose credibility too quickly in the larger setup. Multi-seed testing is included because larger games introduce more randomness.

## 3. Experiment Conditions

- `ten_player_baseline`: 10-player setup with basic role actions and voting, without speech, deception, speaker memory, or trust weighting.
- `ten_player_speech`: adds Bag-of-Words speech and belief updates through speech signals.
- `ten_player_deception`: adds wolf daytime deception on top of speech.
- `ten_player_credibility_cost`: adds credibility costs for repeated or misleading deceptive behavior.
- `ten_player_trust_memory`: adds speaker-specific trust memory and trust updates.
- `ten_player_trust_weighted_herding`: adds trust-weighted herding pressure on top of trust memory.

## 4. Main Results

The single-seed experiment uses seed 42 and 500 games per condition. The results are generated in `results/ten_player_experiment_results.md`.

| condition | wolf_win_rate | village_win_rate | avg_rounds | avg_payoff | wolf_deceptions | credibility_cost_events | trust_updates |
|---|---:|---:|---:|---:|---:|---:|---:|
| ten_player_baseline | 52.40% | 47.60% | 3.35 | 0.16 | 0 | 0 | 0 |
| ten_player_speech | 39.60% | 60.40% | 3.23 | 0.29 | 0 | 0 | 0 |
| ten_player_deception | 78.20% | 21.80% | 3.22 | -0.07 | 2845 | 0 | 0 |
| ten_player_credibility_cost | 57.60% | 42.40% | 3.34 | 0.11 | 2912 | 4065 | 0 |
| ten_player_trust_memory | 40.00% | 60.00% | 3.34 | 0.26 | 2858 | 3853 | 12554 |
| ten_player_trust_weighted_herding | 53.00% | 47.00% | 3.32 | 0.14 | 2916 | 4153 | 13960 |

The single-seed results show that speech strongly helps the village, while wolf deception sharply increases wolf win rate. Credibility costs reduce this wolf advantage. Speaker memory performs strongly in this run, bringing village win rate back to 60.00%. Trust-weighted herding is less favorable for the village in this 10-player configuration than speaker memory alone, suggesting that herding parameters may require size-specific calibration.

## 5. Multi-Seed Robustness

The multi-seed experiment uses seeds 42, 43, 44, 45, and 46, with 500 games per condition per seed. The summary is generated in `results/ten_player_multi_seed_summary.md`.

| condition | wolf_mean | wolf_min | wolf_max | wolf_stdev_pp | village_mean |
|---|---:|---:|---:|---:|---:|
| ten_player_baseline | 56.32 | 52.40 | 59.40 | 2.95 | 43.68 |
| ten_player_speech | 34.84 | 32.00 | 39.60 | 3.02 | 65.16 |
| ten_player_deception | 78.40 | 76.60 | 79.80 | 1.22 | 21.60 |
| ten_player_credibility_cost | 58.32 | 56.60 | 60.80 | 1.74 | 41.68 |
| ten_player_trust_memory | 39.68 | 38.60 | 40.80 | 0.81 | 60.32 |
| ten_player_trust_weighted_herding | 51.44 | 49.80 | 53.00 | 1.34 | 48.56 |

The multi-seed results confirm that the major patterns are stable. Speech improves village outcomes, deception strongly improves wolf outcomes, credibility costs reduce the deception advantage, and speaker memory is the strongest village-favorable mechanism among these 10-player conditions. Trust-weighted herding has a more mixed effect in the 10-player setup and does not outperform speaker memory alone.

## 6. Comparison with 7-Player Model

The 10-player game has more players and more noisy communication than the original 7-player game. Individual speech signals should matter less, because each statement is one signal among more agents. Herding can become more dangerous if it is too strong, since public pressure can spread across a larger group. Wolves also have more coordination power because there are 3 wolves instead of 2. The village has more total players, but also more uncertainty.

If results differ from the 7-player model, this suggests that model parameters should be calibrated by game size. In particular, speech weights, herding pressure, credibility costs, and trust update rates may need separate tuning for larger games.

## 7. Financial / Risk Management Interpretation

The 10-player setup is closer to a larger market or organization than the 7-player setup. More agents produce more noise, more signals, and more opportunities for hidden adversaries to manipulate public interpretation.

In this analogy:

- Wolves represent hidden risk or dishonest actors.
- Villagers represent decision-makers.
- `p_wolf` represents a dynamic risk score.
- Bag-of-Words speech represents public signals.
- Deception represents signal manipulation.
- Credibility cost represents penalties for unreliable information.
- Trust memory represents reputation history.

The 10-player results show why larger systems need calibrated controls. More communication does not automatically produce better decisions if adversarial actors can manipulate signals. Reputation and credibility mechanisms can help, but they must be tuned carefully.

## 8. Limitations

- Speech is still symbolic and does not use real natural language.
- Parameters are heuristic and need further calibration.
- The 10-player setup may need different weights from the 7-player setup.
- There is no human data validation.
- More seeds may be needed for stronger robustness claims.
- The financial and risk management analogy is simplified.

## 9. Conclusion

The 10-player extension tests whether the model generalizes beyond the original 7-player setup. The results show that the main mechanisms remain meaningful in a larger game: speech helps the village, deception helps wolves, credibility costs reduce deception, and trust memory can improve village performance. At the same time, the trust-weighted herding result suggests that larger games require separate calibration. Overall, the 10-player experiment strengthens the connection between the Werewolf simulation and noisy, multi-agent risk environments.
