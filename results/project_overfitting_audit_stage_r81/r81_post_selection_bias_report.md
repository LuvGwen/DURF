# Post-Selection Bias and Winner's Curse

Bootstrap selection frequencies are used to separate stable defaults from descriptive winners.

| Role | Bootstrap Top | Frequency | Stability |
| --- | --- | --- | --- |
| Hunter | reference | 0.849200 | stable |
| Seer | immediate_reveal | 0.997200 | stable |
| Villager | trust_weighted | 1.000000 | stable |
| Werewolf | reference | 0.992600 | stable |
| Witch | aggressive_full | 0.999200 | stable |

| Role | Policy | Selection Freq | Winner's Curse |
| --- | --- | --- | --- |
| Hunter | reference | 0.849200 | 0.00284187 |
| Hunter | random_shot | 0.000000 |  |
| Hunter | no_shot | 0.000000 |  |
| Hunter | highest_suspicion | 0.849200 | 0.00284187 |
| Hunter | highest_p_wolf | 0.152200 | 0.01807181 |
| Hunter | conservative_threshold | 0.000000 |  |
| Seer | private_only | 0.000000 |  |
| Seer | immediate_reveal | 0.997200 | -0.00011466 |
| Seer | reveal_first_wolf | 0.000200 | 0.03575000 |
| Seer | delayed_round_2 | 0.002600 | 0.03886923 |
| Seer | under_threat | 0.000000 |  |
| Seer | selective_useful_info | 0.000000 |  |
