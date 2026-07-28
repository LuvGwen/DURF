# R5 Strategy Frontier Report

| Role | Strategy | Risk metric | Mean | Risk | Efficient | Dominated |
| --- | --- | --- | --- | --- | --- | --- |
| hunter | reference_strategy_mix | standard_deviation | -0.8576 | 1.3051 | True | False |
| hunter | seer_highest_suspicion | standard_deviation | -0.8966 | 1.2358 | True | False |
| hunter | villager_random_vote | standard_deviation | -0.8681 | 1.2854 | True | False |
| hunter | witch_conservative_poison | standard_deviation | -0.7420 | 1.3346 | True | False |
| hunter | wolf_random_kill | standard_deviation | -0.3916 | 1.4310 | True | False |
| seer | reference_strategy_mix | standard_deviation | -0.1688 | 1.1666 | True | False |
| seer | seer_highest_suspicion | standard_deviation | -0.2104 | 1.1658 | True | False |
| seer | villager_random_vote | standard_deviation | -0.3206 | 1.0752 | True | False |
| seer | witch_conservative_poison | standard_deviation | -0.0375 | 1.2294 | True | False |
| seer | wolf_random_kill | standard_deviation | 0.3384 | 1.4977 | True | False |
| villager | reference_strategy_mix | standard_deviation | -0.6304 | 0.9909 | True | False |
| villager | seer_highest_suspicion | standard_deviation | -0.6722 | 0.9758 | True | False |
| villager | villager_random_vote | standard_deviation | -0.7014 | 0.9362 | True | False |
| villager | witch_conservative_poison | standard_deviation | -0.5686 | 1.0233 | True | False |
| villager | wolf_random_kill | standard_deviation | -0.2861 | 1.0677 | True | False |
| werewolf | reference_strategy_mix | standard_deviation | 1.3184 | 1.3742 | False | True |
| werewolf | seer_highest_suspicion | standard_deviation | 1.3743 | 1.3512 | False | True |
| werewolf | villager_random_vote | standard_deviation | 1.3998 | 1.3280 | True | False |
| werewolf | witch_conservative_poison | standard_deviation | 1.2463 | 1.4150 | False | True |
| werewolf | wolf_random_kill | standard_deviation | 0.7085 | 1.5753 | False | True |
| witch | reference_strategy_mix | standard_deviation | -0.3471 | 1.1984 | True | False |
| witch | seer_highest_suspicion | standard_deviation | -0.3835 | 1.1652 | True | False |
| witch | villager_random_vote | standard_deviation | -0.3781 | 1.1725 | True | False |
| witch | witch_conservative_poison | standard_deviation | -0.3134 | 1.2070 | True | False |
| witch | wolf_random_kill | standard_deviation | -0.0231 | 1.3739 | True | False |

R5 constructs role-specific frontiers separately for standard deviation,
downside deviation, and CVaR-like loss. Cross-role frontiers are not pooled
because role payoff distributions are not normalized to a common baseline.
