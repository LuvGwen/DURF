# Risk Preference Experiment Report

## 1. Purpose

This experiment adds heterogeneous individual risk preferences to the Werewolf simulation. Previous stages treated all players as behaviorally neutral unless a role-specific or mechanism-specific rule applied. The new mechanism tests whether conservative, neutral, and aggressive agents behave differently under the same hidden-information environment.

The main research question is:

```text
How does heterogeneous risk preference affect deception, voting, witch poison use, wolf deception, payoff, and village resilience in a social deduction simulation?
```

Risk preference is disabled by default, so previous experiments remain comparable unless the new flag is explicitly enabled.

## 2. Mechanism Design

Each `Player` now has a `risk_preference` attribute. The default value is `"neutral"`, which preserves existing behavior.

The project defines three risk types:

- `conservative`: less willing to make high-risk claims, accusations, poison actions, and deception.
- `neutral`: baseline behavior.
- `aggressive`: more willing to accuse, poison, vote strongly, and deceive.

Risk preference can be assigned by experiment mode:

- `all_neutral`
- `mixed`
- `conservative_majority`
- `aggressive_majority`
- `role_based`

The mechanism affects these decision points:

- Speech: conservative players may downgrade accusations to questions, while aggressive players may upgrade some statements to accusations.
- Voting: vote scores are multiplied by the voter's risk multiplier when risk preference is enabled.
- Witch poison: conservative witches use a higher poison threshold, while aggressive witches use a lower poison threshold.
- Wolf deception: conservative wolves are less likely to perform risky deception, while aggressive wolves are more likely to do so.

## 3. Probability Design

Risk preference uses separate multipliers for ordinary actions and high-risk actions.

| Risk preference | Normal multiplier | High-risk action multiplier |
|---|---:|---:|
| conservative | 0.80 | 0.60 |
| neutral | 1.00 | 1.00 |
| aggressive | 1.20 | 1.40 |

The mixed assignment mode samples approximately:

- 30% conservative
- 40% neutral
- 30% aggressive

The conservative-majority and aggressive-majority modes shift this distribution while keeping the same role setup. This allows the experiment to test population-level risk composition without changing game rules.

## 4. Experiment Conditions

The ten-player experiment compares eight conditions:

| Condition | Description |
|---|---|
| `ten_player_trust_memory` | Speaker memory enabled, all players neutral. |
| `ten_player_trust_memory_risk_mixed` | Speaker memory plus mixed risk preferences. |
| `ten_player_trust_memory_risk_conservative_majority` | Speaker memory plus conservative-majority risk preferences. |
| `ten_player_trust_memory_risk_aggressive_majority` | Speaker memory plus aggressive-majority risk preferences. |
| `ten_player_credibility_cost` | Deception credibility costs enabled, all players neutral. |
| `ten_player_credibility_cost_risk_mixed` | Credibility costs plus mixed risk preferences. |
| `ten_player_deception` | Wolf deception enabled without credibility costs, all players neutral. |
| `ten_player_deception_risk_mixed` | Wolf deception plus mixed risk preferences. |

Each single-seed condition uses 500 games with seed 42.

## 5. Main Results

### 5.1 Single-Seed Results

| Condition | Wolf win rate | Village win rate | Avg rounds | Avg payoff | Conservative count | Neutral count | Aggressive count | Wolf deceptions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ten_player_trust_memory` | 45.60% | 54.40% | 3.37 | 0.22 | 0 | 5000 | 0 | 3103 |
| `ten_player_trust_memory_risk_mixed` | 47.60% | 52.40% | 3.44 | 0.21 | 1538 | 2009 | 1453 | 2831 |
| `ten_player_trust_memory_risk_conservative_majority` | 35.60% | 64.40% | 3.49 | 0.32 | 3040 | 1477 | 483 | 2481 |
| `ten_player_trust_memory_risk_aggressive_majority` | 50.60% | 49.40% | 3.33 | 0.18 | 547 | 1454 | 2999 | 3047 |
| `ten_player_credibility_cost` | 58.40% | 41.60% | 3.34 | 0.11 | 0 | 5000 | 0 | 3096 |
| `ten_player_credibility_cost_risk_mixed` | 62.60% | 37.40% | 3.38 | 0.08 | 1466 | 2040 | 1494 | 2802 |
| `ten_player_deception` | 79.20% | 20.80% | 3.23 | -0.07 | 0 | 5000 | 0 | 3032 |
| `ten_player_deception_risk_mixed` | 80.40% | 19.60% | 3.30 | -0.08 | 1449 | 2013 | 1538 | 2856 |

### 5.2 Risk-Specific Payoff

In the speaker-memory setting, conservative-majority populations produced the strongest village result and the highest average payoff. In the mixed-risk trust-memory condition, neutral players had the highest average payoff.

In the deception-only setting, mixed risk preferences reduced wolf deception count but did not protect the village. This suggests that without credibility controls or speaker memory, risk heterogeneity alone is not enough to resist deception.

## Multi-Seed Robustness

The multi-seed experiment uses five seeds, with 500 games per condition per seed. The results below are read from `results/ten_player_risk_preference_multi_seed_summary.md`.

| Condition | Wolf mean | Wolf min | Wolf max | Wolf stdev | Village mean | Avg payoff |
|---|---:|---:|---:|---:|---:|---:|
| `ten_player_trust_memory` | 42.96% | 40.00% | 45.60% | 2.11 pp | 57.04% | 0.25 |
| `ten_player_trust_memory_risk_mixed` | 47.28% | 43.40% | 49.60% | 2.32 pp | 52.72% | 0.21 |
| `ten_player_trust_memory_risk_conservative_majority` | 38.56% | 35.60% | 41.20% | 2.15 pp | 61.44% | 0.30 |
| `ten_player_trust_memory_risk_aggressive_majority` | 50.96% | 48.80% | 53.40% | 1.65 pp | 49.04% | 0.17 |
| `ten_player_credibility_cost` | 60.64% | 57.60% | 66.60% | 3.55 pp | 39.36% | 0.09 |
| `ten_player_credibility_cost_risk_mixed` | 62.36% | 60.60% | 64.00% | 1.31 pp | 37.64% | 0.08 |
| `ten_player_deception` | 79.32% | 77.00% | 81.80% | 1.77 pp | 20.68% | -0.07 |
| `ten_player_deception_risk_mixed` | 76.16% | 73.20% | 80.40% | 2.70 pp | 23.84% | -0.04 |

The multi-seed results support the main single-seed findings. In the trust-memory setting, the conservative-majority condition has a lower wolf mean of 38.56%, compared with 42.96% for all-neutral trust memory. Its wolf win-rate range is 35.60%-41.20%, which remains below or near the lower part of the all-neutral range. This suggests that conservative-majority populations consistently reduce wolf advantage.

The aggressive-majority condition moves in the opposite direction. Its wolf mean is 50.96%, with a range of 48.80%-53.40%, which is clearly higher than the all-neutral trust-memory baseline. This supports the finding that aggressive risk composition makes the village more vulnerable.

The mixed-risk trust-memory condition has a wolf mean of 47.28% and a 2.32 percentage-point standard deviation. This is higher than the all-neutral trust-memory baseline and indicates that adding heterogeneous risk preference can introduce additional behavioral noise rather than automatically improving collective judgment.

Risk preference also affects payoff distribution. Conservative-majority trust memory produces the highest average payoff among the trust-memory conditions at 0.30, while aggressive-majority trust memory has a lower average payoff of 0.17. In deception-only settings, mixed risk preference slightly improves average payoff from -0.07 to -0.04, but wolves still dominate. Overall, the payoff results suggest that risk preference changes both win rates and the distribution of individual outcomes.

## 7. Interpretation

The strongest result is that population-level risk composition changes collective outcomes. Conservative-majority groups are slower to overcommit to aggressive accusations or risky claims, which improves village survival in the trust-memory condition. Aggressive-majority groups create more volatile voting and speech dynamics, which tends to help wolves.

Risk preference also interacts with deception. Mixed risk preferences slightly reduce wolf deception counts in some conditions, but the win-rate effect depends on whether credibility and trust mechanisms are present. This supports the broader project theme: deception is not controlled by one feature alone. It requires a combination of belief updating, credibility penalties, and memory.

## 8. Financial and Risk Management Analogy

This mechanism maps naturally to risk management concepts:

- `p_wolf` resembles a dynamic counterparty or fraud risk score.
- Speech and deception resemble noisy signals or adversarial disclosures.
- Speaker memory resembles reputation tracking.
- Risk preference resembles individual or institutional risk appetite.

In a financial setting, conservative agents resemble risk-averse decision makers who require stronger evidence before taking punitive action. Aggressive agents resemble risk-seeking or overconfident decision makers who respond faster but may amplify false positives. The experiment shows that risk appetite can change system-level resilience even when the underlying information environment is unchanged.

## 9. Limitations

This version remains intentionally simple:

- Risk preference is discrete rather than continuous.
- Risk effects are implemented through lightweight multipliers and thresholds.
- The model does not use natural language generation or parsing.
- The model does not include learning of individual risk preference over time.
- The same role setup is used across conditions.
- No payoff rules or role abilities were changed for this experiment.

These limits keep the experiment interpretable but leave room for richer behavioral modeling.

## 10. Conclusion

The risk preference extension adds heterogeneous decision tendencies while preserving all previous experiments by default. The results suggest that risk composition matters: conservative-majority groups perform better for the village under trust memory, while aggressive-majority groups increase wolf advantage. However, risk preference alone does not solve deception. The broader pattern remains that social deduction resilience depends on combining belief updates, speaker memory, credibility costs, and controlled risk-taking.
