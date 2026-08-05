# Payoff Sensitivity

R8.1 performs a summary-level perturbation audit only; R4 and R5 manifests are unchanged.

| Scenario | Description |
| --- | --- |
| baseline_r61_payoff | Original R6.1 actor_payoff summaries. |
| core_like_terminal_075 | Summary-level perturbation lowering terminal payoff weight. |
| core_like_terminal_125 | Summary-level perturbation raising terminal payoff weight. |
| action_bonus_075 | Lower action-specific reward/penalty weight. |
| action_bonus_125 | Higher action-specific reward/penalty weight. |
| credibility_cost_075 | Lower credibility/manipulation costs. |
| credibility_cost_125 | Higher credibility/manipulation costs. |
| witch_wrong_poison_harsher | Extra penalty for risky Witch poison policies. |
| witch_wrong_poison_lighter | Lower penalty for risky Witch poison policies. |
| seer_exposure_penalty | Penalize public reveal policies for survival exposure. |
| wolf_deception_penalty | Penalize deception-heavy wolf policies. |
| villager_false_positive_penalty | Penalize riskier vote policies by action cost. |
| downside_risk_averse | Subtract 0.10 times downside deviation. |
| risk_seeking | Add 0.05 times payoff volatility. |

| Scenario | Role | Winner | Adjusted Mean |
| --- | --- | --- | --- |
| baseline_r61_payoff | Hunter | highest_suspicion | -0.41380000 |
| baseline_r61_payoff | Seer | immediate_reveal | -0.15905000 |
| baseline_r61_payoff | Witch | aggressive_full | -0.03725000 |
| baseline_r61_payoff | Werewolf | reference | 0.69691667 |
| baseline_r61_payoff | Villager | trust_weighted | -0.09395000 |
| core_like_terminal_075 | Hunter | highest_suspicion | -0.45518000 |
| core_like_terminal_075 | Seer | immediate_reveal | -0.17495500 |
| core_like_terminal_075 | Witch | aggressive_full | -0.04097500 |
| core_like_terminal_075 | Werewolf | reference | 0.62722500 |
| core_like_terminal_075 | Villager | trust_weighted | -0.10334500 |
| core_like_terminal_125 | Hunter | highest_suspicion | -0.37242000 |
| core_like_terminal_125 | Seer | immediate_reveal | -0.14314500 |
| core_like_terminal_125 | Witch | aggressive_full | -0.03352500 |
| core_like_terminal_125 | Werewolf | reference | 0.76660833 |
| core_like_terminal_125 | Villager | trust_weighted | -0.08455500 |
| action_bonus_075 | Hunter | reference | -0.41380000 |
| action_bonus_075 | Seer | immediate_reveal | -0.18905000 |
| action_bonus_075 | Witch | aggressive_full | -0.06725000 |
| action_bonus_075 | Werewolf | reference | 0.69691667 |
| action_bonus_075 | Villager | trust_weighted | -0.12395000 |
| action_bonus_125 | Hunter | highest_suspicion | -0.41380000 |
| action_bonus_125 | Seer | immediate_reveal | -0.12905000 |
| action_bonus_125 | Witch | aggressive_full | -0.00725000 |
| action_bonus_125 | Werewolf | reference | 0.69691667 |
| action_bonus_125 | Villager | trust_weighted | -0.06395000 |
| credibility_cost_075 | Hunter | highest_suspicion | -0.41380000 |
| credibility_cost_075 | Seer | immediate_reveal | -0.15905000 |
| credibility_cost_075 | Witch | aggressive_full | -0.03725000 |
| credibility_cost_075 | Werewolf | threat_adaptive | 0.73691667 |
| credibility_cost_075 | Villager | trust_weighted | -0.09395000 |
| credibility_cost_125 | Hunter | highest_suspicion | -0.41380000 |
| credibility_cost_125 | Seer | immediate_reveal | -0.15905000 |
| credibility_cost_125 | Witch | aggressive_full | -0.03725000 |
| credibility_cost_125 | Werewolf | reference | 0.69691667 |
| credibility_cost_125 | Villager | trust_weighted | -0.09395000 |
