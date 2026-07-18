# Limited Last Words Mechanism Experiment Report

## 1. Purpose

Last words are a common but rule-dependent Werewolf mechanism. This project uses a limited version rather than allowing every dead player to speak. In this implementation, voted-out players can give last words, Night 1 wolf-kill victims can give last words, later night-kill victims cannot, and witch poison or hunter shot victims cannot.

The purpose of this experiment is to test whether limited post-elimination speech adds useful information or extra noise in the 10-player Werewolf model.

## 2. Mechanism Design

Last words are processed as Bag-of-Words speech signals. They can affect suspicion, `p_wolf`, trust, and later voting through the same event-log and belief-update pathway used by other speech signals.

The mechanism uses the following rules:

- Voted-out players can give last words.
- Night 1 wolf-kill victims can give last words.
- Night 2 and later wolf-kill victims cannot give last words.
- Witch poison victims cannot give last words.
- Hunter shot victims cannot give last words.
- Hunter shooting is treated as a role skill, not as last words.
- Each player can give last words at most once.
- Dead players remain dead and cannot continue normal actions.

Last words have slightly higher weight than ordinary speech, using a `LAST_WORDS_WEIGHT` of 1.20. This makes last words informative, but not overwhelmingly strong.

## 3. Experiment Conditions

The experiment compares eight 10-player conditions:

- `ten_player_speech`
- `ten_player_speech_limited_last_words`
- `ten_player_deception`
- `ten_player_deception_limited_last_words`
- `ten_player_credibility_cost`
- `ten_player_credibility_cost_limited_last_words`
- `ten_player_trust_memory`
- `ten_player_trust_memory_limited_last_words`

Each single-seed condition uses 500 games with seed 42. The multi-seed experiment uses seeds 42, 43, 44, 45, and 46, with 500 games per condition per seed.

## 4. Main Results

The single-seed results are generated in `results/ten_player_limited_last_words_results.md`.

| condition | wolf_win_rate | village_win_rate | avg_rounds | avg_payoff | total_last_words | voted_out_last_words | night1_kill_last_words | wolf_last_words | village_team_last_words | correct_last_words_accusations | wrong_last_words_accusations | total_wolf_deceptions | credibility_cost_events | trust_updates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ten_player_speech | 37.40% | 62.60% | 3.36 | 0.32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ten_player_speech_limited_last_words | 34.40% | 65.60% | 3.23 | 0.34 | 1588 | 1442 | 146 | 848 | 740 | 408 | 1180 | 0 | 0 | 0 |
| ten_player_deception | 79.20% | 20.80% | 3.23 | -0.07 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3032 | 0 | 0 |
| ten_player_deception_limited_last_words | 77.40% | 22.60% | 3.47 | -0.05 | 1628 | 1478 | 150 | 535 | 1093 | 564 | 1064 | 3163 | 0 | 0 |
| ten_player_credibility_cost | 58.40% | 41.60% | 3.34 | 0.11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3096 | 4280 | 0 |
| ten_player_credibility_cost_limited_last_words | 54.40% | 45.60% | 3.55 | 0.14 | 1692 | 1549 | 143 | 683 | 1009 | 639 | 1053 | 3174 | 4572 | 0 |
| ten_player_trust_memory | 45.60% | 54.40% | 3.37 | 0.22 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3103 | 4240 | 13600 |
| ten_player_trust_memory_limited_last_words | 35.80% | 64.20% | 3.49 | 0.31 | 1705 | 1559 | 146 | 835 | 870 | 569 | 1136 | 3133 | 4331 | 13706 |

In the single-seed experiment, limited last words improve village win rate in all four paired comparisons. The largest improvement appears in the trust memory condition, where village win rate increases from 54.40% to 64.20%.

## 5. Multi-Seed Robustness

The multi-seed summary is generated in `results/ten_player_limited_last_words_multi_seed_summary.md`.

| condition | wolf_mean | wolf_min | wolf_max | wolf_stdev_pp | village_mean | avg_last_words |
|---|---:|---:|---:|---:|---:|---:|
| ten_player_speech | 38.08 | 37.40 | 38.80 | 0.70 | 61.92 | 0.00 |
| ten_player_speech_limited_last_words | 35.24 | 34.20 | 37.00 | 1.16 | 64.76 | 3.23 |
| ten_player_deception | 79.32 | 77.00 | 81.80 | 1.77 | 20.68 | 0.00 |
| ten_player_deception_limited_last_words | 78.00 | 77.00 | 81.40 | 1.91 | 22.00 | 3.24 |
| ten_player_credibility_cost | 60.64 | 57.60 | 66.60 | 3.55 | 39.36 | 0.00 |
| ten_player_credibility_cost_limited_last_words | 56.00 | 53.40 | 58.60 | 2.25 | 44.00 | 3.37 |
| ten_player_trust_memory | 42.96 | 40.00 | 45.60 | 2.11 | 57.04 | 0.00 |
| ten_player_trust_memory_limited_last_words | 35.64 | 33.60 | 37.20 | 1.36 | 64.36 | 3.42 |

The multi-seed results confirm the single-seed pattern. Limited last words reduce wolf mean win rate in every paired comparison. The mechanism has the largest effect when combined with trust memory, reducing wolf mean win rate from 42.96% to 35.64%.

## 6. Interpretation

Limited last words appear to help the village more than the wolves in this version of the 10-player model. When last words are enabled, eliminated players add a final risk signal to the public information environment. Because voted-out players and Night 1 victims often include village-team players, this signal can improve later belief updates and voting.

The mechanism does not eliminate deception. In the deception-only setting, wolves still win most games. However, limited last words slightly reduce wolf performance, suggesting that post-elimination information can partially counteract deceptive speech.

In the financial analogy, last words resemble late disclosures, final warnings, or public statements after removal from a decision process. These statements can help identify hidden risk, but they can also introduce noise if the speaker is unreliable.

## 7. Limitations

- Speech is symbolic and does not use real natural language.
- The last-words weight is heuristic.
- The rule variant may differ from other Werewolf rule sets.
- Last words currently use simple target selection logic.
- The mechanism needs calibration for different role setups.
- More seeds may be needed for stronger robustness claims.

## 8. Conclusion

The limited last words mechanism improves village outcomes in the tested 10-player conditions. It adds an additional information channel without allowing all dead players to continue participating. The results suggest that limited post-elimination speech can improve collective decision-making when it is restricted by clear eligibility rules. At the same time, the mechanism adds both information and noise, so its strength should remain calibrated rather than unlimited.
