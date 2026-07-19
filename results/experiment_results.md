# DURF Werewolf Experiment Results

Random seed: 42

## Ablation Experiment Results

| Experiment | Total Games | Wolf Wins | Village Wins | Draws | Wolf Win % | Village Win % | Draw % | Avg Rounds | Avg Alive | Witch Saves | Witch Poison | Seer Checks | Hunter Shots | Wolf Deceptions | Accusation Costs | Wrong Accusation Penalties | Self-Defense Costs | Deception Types | Wolf Kills | Strategic Wolf Kills | Avg Herding | Avg Trust Weighted Herding | Avg Role Prior | Avg Payoff | Wolf Payoff | Village Payoff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_baseline | 100 | 93 | 7 | 0 | 93.00 | 7.00 | 0.00 | 2.25 | 3.43 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | {} | 225 | 0 | 0.00 | 0.00 | 0.00 | -0.22 | 1.21 | -0.80 |
| suspicion_voting | 100 | 92 | 8 | 0 | 92.00 | 8.00 | 0.00 | 2.26 | 3.40 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | {} | 226 | 0 | 0.00 | 0.00 | 0.00 | -0.22 | 1.18 | -0.78 |
| suspicion_update | 100 | 84 | 16 | 0 | 84.00 | 16.00 | 0.00 | 2.21 | 3.42 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | {} | 221 | 0 | 0.00 | 0.00 | 0.00 | -0.15 | 1.01 | -0.61 |
| seer_action | 100 | 80 | 20 | 0 | 80.00 | 20.00 | 0.00 | 2.34 | 3.12 | 0 | 0 | 186 | 0 | 0 | 0 | 0 | 0 | {} | 234 | 0 | 0.00 | 0.00 | 0.00 | -0.08 | 0.93 | -0.49 |
| witch_action | 100 | 58 | 42 | 0 | 58.00 | 42.00 | 0.00 | 2.52 | 2.60 | 87 | 63 | 205 | 0 | 0 | 0 | 0 | 0 | {} | 252 | 0 | 0.00 | 0.00 | 0.00 | 0.10 | 0.34 | 0.01 |
| hunter_action | 100 | 58 | 42 | 0 | 58.00 | 42.00 | 0.00 | 2.32 | 2.79 | 80 | 45 | 192 | 44 | 0 | 0 | 0 | 0 | {} | 232 | 0 | 0.00 | 0.00 | 0.00 | 0.09 | 0.34 | -0.01 |
| speech_enabled | 100 | 41 | 59 | 0 | 41.00 | 59.00 | 0.00 | 2.05 | 3.24 | 77 | 37 | 184 | 48 | 0 | 0 | 0 | 0 | {} | 205 | 0 | 0.02 | 0.02 | 0.00 | 0.25 | -0.03 | 0.37 |
| speech_plus_herding | 100 | 45 | 55 | 0 | 45.00 | 55.00 | 0.00 | 2.01 | 3.06 | 74 | 54 | 166 | 50 | 0 | 0 | 0 | 0 | {} | 201 | 0 | 0.02 | 0.02 | 0.00 | 0.21 | 0.06 | 0.27 |
| speech_herding_role_prior | 100 | 41 | 59 | 0 | 41.00 | 59.00 | 0.00 | 2.03 | 3.24 | 77 | 45 | 171 | 45 | 0 | 0 | 0 | 0 | {} | 203 | 0 | 0.02 | 0.02 | 0.03 | 0.26 | -0.01 | 0.38 |
| wolf_strategy | 100 | 29 | 71 | 0 | 29.00 | 71.00 | 0.00 | 2.03 | 3.38 | 88 | 58 | 161 | 22 | 0 | 0 | 0 | 0 | {} | 203 | 203 | 0.02 | 0.02 | 0.03 | 0.38 | -0.28 | 0.64 |
| wolf_deception | 100 | 46 | 54 | 0 | 46.00 | 54.00 | 0.00 | 2.00 | 3.14 | 78 | 46 | 171 | 47 | 239 | 0 | 0 | 0 | {'false_accuse': 78, 'deflect_suspicion': 16, 'false_role_claim': 97, 'trust_building': 48} | 200 | 200 | 0.03 | 0.03 | 0.03 | 0.20 | 0.09 | 0.24 |
| speaker_memory | 100 | 60 | 40 | 0 | 60.00 | 40.00 | 0.00 | 2.32 | 2.50 | 89 | 52 | 163 | 68 | 281 | 16 | 15 | 63 | {'deflect_suspicion': 221, 'trust_building': 44, 'false_accuse': 16} | 232 | 232 | 0.03 | 0.03 | 0.03 | 0.05 | 0.38 | -0.08 |
| trust_weighted_speech | 100 | 52 | 48 | 0 | 52.00 | 48.00 | 0.00 | 2.35 | 2.58 | 89 | 43 | 168 | 69 | 295 | 16 | 12 | 51 | {'deflect_suspicion': 217, 'trust_building': 62, 'false_accuse': 16} | 235 | 235 | 0.03 | 0.03 | 0.03 | 0.12 | 0.22 | 0.09 |
| trust_weighted_herding | 100 | 48 | 52 | 0 | 48.00 | 52.00 | 0.00 | 2.30 | 2.58 | 89 | 44 | 168 | 69 | 293 | 13 | 16 | 62 | {'deflect_suspicion': 225, 'trust_building': 55, 'false_accuse': 13} | 230 | 230 | 0.02 | 0.02 | 0.03 | 0.16 | 0.13 | 0.18 |
| trust_weighted_speech_and_herding | 100 | 60 | 40 | 0 | 60.00 | 40.00 | 0.00 | 2.32 | 2.59 | 87 | 48 | 164 | 69 | 282 | 14 | 12 | 60 | {'deflect_suspicion': 223, 'trust_building': 45, 'false_accuse': 14} | 232 | 232 | 0.02 | 0.02 | 0.03 | 0.05 | 0.38 | -0.08 |

## Wolf Strategy Experiment Results

| Strategy | Total Games | Wolf Wins | Village Wins | Draws | Wolf Win % | Village Win % | Draw % | Avg Rounds | Avg Alive | Wolf Kills | Witch Saves | Witch Poison | Seer Checks | Hunter Shots | Avg Payoff | Wolf Payoff | Village Payoff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random | 100 | 29 | 71 | 0 | 29.00 | 71.00 | 0.00 | 2.08 | 3.05 | 208 | 87 | 53 | 191 | 47 | 0.37 | -0.28 | 0.63 |
| threat_based | 100 | 31 | 69 | 0 | 31.00 | 69.00 | 0.00 | 2.02 | 3.16 | 202 | 81 | 48 | 170 | 37 | 0.34 | -0.23 | 0.57 |
| seer_first | 100 | 39 | 61 | 0 | 39.00 | 61.00 | 0.00 | 1.95 | 3.14 | 195 | 79 | 51 | 168 | 49 | 0.26 | -0.07 | 0.39 |
| witch_first | 100 | 35 | 65 | 0 | 35.00 | 65.00 | 0.00 | 2.04 | 3.05 | 204 | 68 | 26 | 191 | 43 | 0.31 | -0.14 | 0.49 |
| avoid_hunter | 100 | 29 | 71 | 0 | 29.00 | 71.00 | 0.00 | 2.02 | 3.26 | 202 | 84 | 46 | 172 | 29 | 0.37 | -0.28 | 0.63 |
| low_suspicion | 100 | 35 | 65 | 0 | 35.00 | 65.00 | 0.00 | 2.06 | 3.16 | 206 | 84 | 42 | 191 | 47 | 0.32 | -0.15 | 0.50 |
