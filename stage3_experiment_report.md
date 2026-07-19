# DURF Werewolf Simulation: Stage 3 Experiment Report

## 1. Overview

Stage 1 built the basic Werewolf simulation framework, including the core game loop, role setup, win conditions, and batch simulation tools. Stage 2 added social deduction mechanisms such as speech signals, `p_wolf` belief updating, herding pressure, role prior, wolf night strategy, and result export.

Stage 3 focuses on wolf daytime deception. The goal is to test whether wolves can recover strategic advantage through deceptive communication during the day phase, and whether that advantage remains plausible once speech credibility costs are introduced.

## 2. Stage 3 Mechanisms

### 2.1 Wolf Daytime Deception

Stage 3 adds `wolf_deception.py`, which allows wolves to produce deceptive speech during the day phase.

Deception types include:

- `false_accuse`
- `false_defend`
- `false_role_claim`
- `deflect_suspicion`
- `trust_building`

Wolves can generate deception speech during the existing speech round. These deceptive speech acts are recorded in the event log and can affect `p_wolf`, suspicion, herding pressure, and voting indirectly.

### 2.2 Deception Policy Diagnostics

Stage 3 adds `wolf_deception_experiment.py` to compare different wolf deception policies.

The diagnostic experiment is designed to:

- Compare different deception policies.
- Identify which type of deception helps wolves most.
- Test whether mixed deception performs better than single-strategy deception.

Policies tested:

- `mixed`
- `adaptive`
- `false_accuse`
- `false_defend`
- `false_role_claim`
- `deflect_suspicion`
- `trust_building`

### 2.3 Adaptive Wolf Deception Policy

The first adaptive policy selected `false_accuse` too often. This made wolves too strong because false accusation initially had no cost.

The policy was later made cost-aware. Cost-aware adaptive deception uses:

- `deflect_suspicion` when the wolf is under suspicion.
- `false_accuse` only selectively.
- `trust_building` when accusation risk is high.
- Never `false_role_claim`.

### 2.4 Deception Credibility Costs

Stage 3 adds `deception_credibility.py`, which introduces credibility costs for repeated or misleading deceptive speech.

Mechanisms:

1. Accusation pressure cost
   - Repeated accusations increase the speaker's suspicion and `p_wolf`.

2. Wrong accusation penalty
   - If a player accuses a village-team player who is later eliminated, the accuser is penalized.

3. Self-defense credibility cost
   - Repeated `deflect_suspicion` or `trust_building` increases the speaker's suspicion and `p_wolf`.

The purpose is to prevent `false_accuse` and `deflect_suspicion` from becoming cost-free dominant strategies. The credibility model represents the idea that repeated manipulative speech reduces a speaker's trustworthiness.

## 3. Experimental Setup

The Stage 3 experiments use 500 games per condition with a fixed random seed. The default setup is a 7-player game:

- 2 werewolves
- 2 villagers
- 1 seer
- 1 witch
- 1 hunter

Stage 2 mechanisms remain enabled:

- Speech
- `p_wolf` belief update
- Herding pressure
- Role prior
- Wolf night strategy

Wolf night strategy uses seer-first or strategic kill settings depending on the experiment.

Main metrics:

- Wolf win rate
- Village win rate
- Deception type counts
- Accusation pressure costs
- Wrong accusation penalties
- Self-defense costs

## 4. Initial Wolf Deception Results

| Policy | Wolf Win % | Village Win % | Main Result |
|---|---:|---:|---|
| mixed | 35.00 | 65.00 | Mixed deception performed poorly because it included too many false role claims. |
| false_accuse | 78.00 | 22.00 | Extremely strong before credibility costs. |
| false_defend | 42.00 | 58.00 | Mildly useful but not dominant. |
| false_role_claim | 23.00 | 77.00 | Strongly harmful to wolves. |
| deflect_suspicion | 60.00 | 40.00 | Strong self-protection strategy before self-defense cost. |
| trust_building | 33.00 | 67.00 | Weak strategy. |

Interpretation:

- `false_accuse` was initially the strongest strategy.
- `false_role_claim` was the worst strategy.
- Mixed deception underperformed because it selected `false_role_claim` too often.
- `deflect_suspicion` was effective because it had no credibility cost yet.

## 5. Adaptive Policy Before Credibility Costs

The initial adaptive policy mostly selected `false_accuse`.

| Policy | Wolf Win % | Village Win % | Deception Types |
|---|---:|---:|---|
| adaptive | 78.00 | 22.00 | `{'false_accuse': 278}` |

Interpretation:

- The adaptive policy technically worked, but it became equivalent to `false_accuse`.
- Because false accusation had no cost, this made wolves unrealistically strong.

## 6. Accusation Credibility Cost Results

| Policy | Wolf Win % | Village Win % | Accusation Costs | Wrong Accusation Penalties |
|---|---:|---:|---:|---:|
| mixed | 39.00 | 61.00 | 62 | 44 |
| adaptive | 50.00 | 50.00 | 301 | 215 |
| false_accuse | 50.00 | 50.00 | 301 | 215 |
| deflect_suspicion | 60.00 | 40.00 | 0 | 5 |
| false_role_claim | 23.00 | 77.00 | 0 | 0 |

Interpretation:

- Accusation costs reduced `false_accuse` from a 78% wolf win rate to 50%.
- This made false accusation strong but risky.
- `deflect_suspicion` became the strongest remaining strategy because it avoided accusation costs.

## 7. Cost-Aware Adaptive Policy

| Policy | Wolf Win % | Village Win % | Accusation Costs | Wrong Accusation Penalties | Deception Types |
|---|---:|---:|---:|---:|---|
| adaptive | 56.00 | 44.00 | 18 | 18 | `{'deflect_suspicion': 249, 'false_accuse': 18, 'trust_building': 24}` |

Interpretation:

- Cost-aware adaptive policy reduced overuse of `false_accuse`.
- Wolves mostly used `deflect_suspicion`, with selective false accusations and some trust building.
- This produced a plausible wolf advantage without returning to the unrealistic 78% win rate.

## 8. Self-Defense Credibility Cost Results

| Policy | Wolf Win % | Village Win % | Accusation Costs | Wrong Accusation Penalties | Self-Defense Costs |
|---|---:|---:|---:|---:|---:|
| adaptive | 46.00 | 54.00 | 15 | 16 | 69 |
| deflect_suspicion | 46.00 | 54.00 | 0 | 0 | 102 |
| false_accuse | 50.00 | 50.00 | 301 | 215 | 0 |
| mixed | 41.00 | 59.00 | 62 | 44 | 2 |

Interpretation:

- Self-defense cost reduced `deflect_suspicion` from 60% to 46%.
- Adaptive policy also decreased from 56% to 46%.
- Repeated self-defense is no longer free.
- `false_accuse` remains balanced at 50%, but with very high credibility cost.
- The final credibility model creates a more balanced deception environment.

## 9. Key Findings

### Finding 1: Deception can strongly shift game balance

Before credibility costs, `false_accuse` gave wolves a 78% win rate.

### Finding 2: Not all deception is useful

`false_role_claim` gave wolves only a 23% win rate, making it actively harmful.

### Finding 3: Credibility costs are necessary

Without costs, `false_accuse` and `deflect_suspicion` become dominant strategies.

### Finding 4: Accusation cost balances false accusation

`false_accuse` drops from 78% to 50% after accusation pressure and wrong accusation penalties.

### Finding 5: Self-defense cost balances deflection

`deflect_suspicion` drops from 60% to 46% after repeated self-defense penalties.

### Finding 6: Final adaptive deception is more realistic

Final adaptive policy has:

- Wolf win rate: 46%
- Village win rate: 54%
- Accusation costs: 15
- Wrong accusation penalties: 16
- Self-defense costs: 69

It no longer produces unrealistic wolf dominance.

## 10. Current Limitations

- Deception is still template-based and symbolic.
- There is no real natural language understanding yet.
- Credibility costs are hand-coded.
- Players do not track speaker-specific trust histories in detail.
- Wolves do not coordinate deception with each other.
- False role claims are too weak and need a better credibility system.
- The model still uses simplified access to true outcomes for penalties.
- There are no confidence intervals or multi-seed statistical tests yet.
- There is no visualization yet.

## 11. Next Steps

1. Add speaker credibility memory for each player.
2. Track trust toward individual speakers rather than global suspicion only.
3. Improve false role claim mechanics.
4. Add wolf coordination during daytime discussion.
5. Add multi-seed statistical testing.
6. Export Stage 3 results to CSV / Markdown.
7. Add visual plots later.
8. Eventually compare simulated deception patterns to social deduction theory.

## 12. Conclusion

Stage 3 demonstrates that wolf daytime deception can substantially affect Werewolf game outcomes. However, deception only produces plausible behavior when credibility costs are included. False accusation and self-defense both become powerful if cost-free, but the credibility system balances these strategies and creates a more realistic social deduction environment. The next stage should focus on speaker-specific trust memory and more nuanced deception credibility.
