# Final Research Report Outline: Deception, Credibility, and Risk Scoring in a Werewolf Social Deduction Simulation

## 1. Abstract Draft

This project uses Werewolf as a controlled social deduction environment for studying hidden information, belief updating, deception, credibility, and trust. The project builds an agent-based Python simulation in which players have roles, private team identities, public speech actions, suspicion scores, belief probabilities, and speaker-specific memory. Across four development stages, the model adds increasingly rich social mechanisms: baseline voting and role actions, Bag-of-Words speech signals, `p_wolf` belief updating, herding pressure, role priors, wolf night-kill strategy, daytime wolf deception, credibility costs, and trust-weighted communication. The project evaluates these mechanisms through ablation experiments, targeted diagnostic experiments, and a final multi-seed robustness test. The main results show that wolves dominate the low-information baseline, while village information mechanisms sharply reduce wolf advantage. Wolf deception can partially restore wolf performance, but credibility costs and trust-weighted mechanisms are needed to control deceptive influence. The risk management interpretation is central: `p_wolf` acts like a dynamic risk score, wolf deception resembles adversarial manipulation, and credibility memory functions like a reputation-based control system. The simulation therefore provides a compact experimental framework for studying how social signals, trust, and adversarial behavior affect collective decision-making under uncertainty.

## 2. Introduction

### 2.1 Research Motivation

- Social deduction games are useful simplified environments for studying decision-making under hidden information.
- Werewolf is especially relevant because it combines incomplete information, deception, group voting, social influence, trust, and reputation.
- Unlike fully deterministic games, Werewolf requires agents to reason from noisy behavioral signals rather than complete state information.
- These themes connect naturally to data science, business analytics, and risk management.
- In business and risk settings, decision-makers often infer hidden intent or hidden risk from incomplete public signals.
- Examples include fraud detection, misinformation analysis, insider threat monitoring, reputation systems, and collective decision failures caused by information cascades.

### 2.2 Research Question

```text
How do belief updating, speech signals, deception, credibility costs, and trust memory affect collective decision-making in a hidden-information social deduction environment?
```

### 2.3 Research Objectives

- Build a modular Python simulation of Werewolf that can run many games automatically.
- Create explicit mechanisms for belief updating, speech, deception, credibility, and trust.
- Compare major mechanisms through ablation experiments.
- Test whether findings are stable across multiple random seeds.
- Interpret the simulation as a risk-scoring and adversarial manipulation model.

### 2.4 Contributions

- A staged simulation framework for social deduction under hidden information.
- A dynamic `p_wolf` belief score that functions as an agent-level risk estimate.
- A Bag-of-Words speech system for controlled language-like signals.
- Wolf deception policies and credibility costs.
- Speaker-specific trust memory and trust-weighted social influence.
- Ablation, diagnostic, and multi-seed robustness experiments.
- A risk management interpretation linking game mechanisms to dynamic risk scoring, reputation systems, and adversarial manipulation.

## 3. Background and Conceptual Framing

### 3.1 Werewolf as a Hidden-Information Environment

- Players have asymmetric information: wolves know their identity, while villagers must infer hidden roles.
- The village must aggregate uncertain evidence through discussion and voting.
- Wolves can manipulate public beliefs through speech and strategic actions.
- The game therefore provides a small but expressive model of adversarial social inference.

### 3.2 Belief Updating and Risk Scoring

- `p_wolf` represents the estimated probability that a player is a wolf.
- This is analogous to a dynamic risk score in fraud detection or risk monitoring.
- New events such as speech, voting, role checks, and credibility outcomes update the score.
- The model allows investigation of how noisy signals affect collective risk estimates.

### 3.3 Deception, Credibility, and Reputation

- Deception is modeled as strategic wolf speech.
- Credibility costs penalize repeated or incorrect manipulative speech.
- Speaker memory tracks whether specific speakers have been reliable in previous rounds.
- These mechanisms approximate real-world reputation-based controls.

### 3.4 Herding and Information Cascades

- Herding pressure captures the way public accusations and voting patterns can amplify each other.
- In risk management terms, herding resembles information cascades or systemic amplification of weak signals.
- Trust-weighted herding tests whether credibility filtering can reduce manipulation risk.

## 4. Simulation Design

### 4.1 Core Game Framework

- Main files:
  - `roles.py`
  - `player.py`
  - `game_state.py`
  - `game.py`
  - `simulation.py`
  - `config.py`
- The model represents players, roles, alive/dead status, phase transitions, game rounds, and win conditions.
- The game loop alternates between night and day phases.
- Night actions include wolf kills and special role actions.
- Day actions include speech, belief updates, herding, voting, and elimination.

### 4.2 Role Setup

- Default role setup:
  - Werewolf
  - Werewolf
  - Villager
  - Villager
  - Seer
  - Witch
  - Hunter
- Wolves win when they reach parity or eliminate the village advantage.
- Village wins when all wolves are eliminated.

### 4.3 State Variables

- `suspicion_score`: public suspicion level.
- `p_wolf`: belief-based probability that a player is a wolf.
- `memory`: player-specific memory structure.
- `speaker_trust`: trust score assigned by one player to another speaker.
- `event_log`: structured record of game events.
- Payoff values: final utility summaries for players and teams.

### 4.4 Reproducibility and Configuration

- Central configuration is stored in `config.py`.
- Main experiments use 500 games per condition unless otherwise stated.
- Fixed random seeds support reproducibility.
- Multi-seed experiments use seeds 42, 43, 44, 45, and 46.

## 5. Mechanism Development by Stage

### 5.1 Stage 1: Basic Simulation and Payoff

- Implemented a minimum playable Werewolf game loop.
- Added role setup, night kills, day voting, phase transitions, and win conditions.
- Added batch simulation and result summaries.
- Added payoff calculation for outcome evaluation.
- Established the low-information baseline.

### 5.2 Stage 2: Speech, Belief Updating, Herding, Role Prior, and Wolf Strategy

- Added Bag-of-Words speech signals:
  - accuse
  - defend
  - claim_role
  - deny
  - agree
  - question
  - trust
  - neutral
- Added `p_wolf` belief updating.
- Added suspicion update after votes.
- Added herding pressure from public signals.
- Added role prior scores.
- Added strategic wolf night-kill policies.
- Created ablation experiments to compare each mechanism.

### 5.3 Stage 3: Wolf Deception and Credibility Costs

- Added wolf daytime deception:
  - false accusation
  - false defense
  - false role claim
  - suspicion deflection
  - trust building
- Tested deception policies such as mixed, false-accuse-only, deflect-suspicion-only, and adaptive.
- Added credibility costs:
  - accusation pressure cost
  - wrong accusation penalty
  - self-defense credibility cost
- Found that deception can improve wolf performance, but unchecked deception can become too strong.

### 5.4 Stage 4: Speaker Memory and Trust-Weighted Influence

- Added speaker-specific trust memory.
- Added trust updates from correct and incorrect speech outcomes.
- Connected speaker trust to voting.
- Added trust-weighted speech influence.
- Added trust-weighted herding pressure.
- Tested whether trust memory helps agents resist deception.
- Found that speaker memory alone is not automatically protective and can create new manipulation channels.

### 5.5 Final Robustness Testing

- Added multi-seed robustness experiment.
- Tested major conditions across five seeds.
- Reported mean, range, and standard deviation of win rates.
- Used robustness testing to distinguish stable findings from seed-specific noise.

## 6. Experimental Design

### 6.1 Ablation Experiment

- Purpose: identify how each mechanism changes wolf and village win rates.
- Conditions include:
  - random baseline
  - suspicion voting
  - suspicion update
  - seer action
  - witch action
  - hunter action
  - speech
  - herding
  - role prior
  - wolf strategy
  - wolf deception
  - speaker memory
  - trust-weighted speech
  - trust-weighted herding
  - trust-weighted speech and herding

### 6.2 Diagnostic Experiments

- Witch poison threshold sweep.
- Wolf strategy comparison.
- Wolf deception policy comparison.
- Speaker memory sensitivity experiment.
- Trust-weighted speech and herding comparison.
- Experiment configuration audit.

### 6.3 Multi-Seed Robustness Experiment

- Seeds: 42, 43, 44, 45, 46.
- 500 games per condition per seed.
- Conditions:
  - `random_baseline`
  - `wolf_strategy`
  - `wolf_deception`
  - `speaker_memory_vote_only`
  - `trust_weighted_speech`
  - `trust_weighted_herding`
  - `trust_weighted_speech_and_herding`
- Metrics:
  - wolf win rate mean
  - wolf win rate range
  - wolf win rate standard deviation
  - village win rate mean
  - average rounds
  - payoff summaries

## 7. Main Results

### 7.1 Low-Information Baseline

- Wolves dominate the low-information baseline.
- Multi-seed result:
  - wolf mean win rate: 91.68%
  - wolf range: 90.00%-93.00%
  - wolf standard deviation: 1.25 percentage points
  - village mean win rate: 8.32%
- Interpretation:
  - Without useful information channels, village agents cannot coordinate effectively.
  - The baseline validates Werewolf as an asymmetric hidden-information environment.

### 7.2 Village Information Mechanisms

- Information-rich mechanisms sharply reduce wolf advantage.
- Multi-seed `wolf_strategy` result:
  - wolf mean win rate: 38.40%
  - village mean win rate: 61.60%
- Interpretation:
  - Speech, belief updating, role prior, herding, and special roles give the village enough information to outperform wolves.
  - This result is robust across seeds, although some seed-level variation remains.

### 7.3 Wolf Deception

- Wolf deception partially restores wolf performance.
- Multi-seed comparison:
  - `wolf_strategy`: 38.40% wolf mean
  - `wolf_deception`: 42.28% wolf mean
- Interpretation:
  - Daytime deception matters because it lets wolves manipulate public inference.
  - Deception improves wolf outcomes but does not fully restore low-information dominance.

### 7.4 Speaker Memory and Trust

- Speaker memory is not automatically beneficial for the village.
- Multi-seed comparison:
  - `wolf_deception`: 42.28% wolf mean
  - `speaker_memory_vote_only`: 57.88% wolf mean
- Interpretation:
  - Reputation systems can be manipulated.
  - Trust memory may amplify early misleading signals if not calibrated carefully.

### 7.5 Trust-Weighted Speech and Herding

- Trust-weighted mechanisms improve over speaker memory alone.
- Multi-seed results:
  - `speaker_memory_vote_only`: 57.88% wolf mean
  - `trust_weighted_speech`: 56.76% wolf mean
  - `trust_weighted_herding`: 54.72% wolf mean
  - `trust_weighted_speech_and_herding`: 55.80% wolf mean
- Interpretation:
  - Trust-weighted herding is the most promising trust-based correction among the tested variants.
  - Public pressure appears to be a key channel for deception spread.
  - Filtering herding by speaker credibility reduces, but does not eliminate, wolf advantage.

## 8. Risk Management Interpretation

### 8.1 `p_wolf` as Dynamic Risk Score

- `p_wolf` estimates hidden wolf identity from observable behavior.
- This parallels fraud scores, credit risk indicators, or insider threat scores.
- The simulation shows how risk scores can improve when updated from multiple evidence channels.

### 8.2 Deception as Adversarial Manipulation

- Wolf deception represents adversarial attempts to manipulate risk perception.
- False accusations resemble false reports or misinformation.
- Suspicion deflection resembles strategic blame shifting.
- Trust building resembles reputation manipulation.

### 8.3 Credibility Costs as Controls

- Credibility costs penalize repeated or inaccurate manipulative behavior.
- These mechanisms resemble control systems that reduce the influence of unreliable actors.
- The experiments suggest that controls must be calibrated to avoid either under-penalizing or over-penalizing speech behavior.

### 8.4 Speaker Memory as Reputation History

- Speaker-specific trust memory resembles reputation scoring.
- The experiments show that reputation history can be useful but also risky.
- If reputation updates are too weak, trust has little effect.
- If updates are too naive, wolves can exploit the reputation system.

### 8.5 Herding as Systemic Risk

- Herding pressure models how public opinion can amplify signals.
- In risk management, this resembles information cascades, market panic, or systemic amplification.
- Trust-weighted herding suggests that filtering public pressure by credibility can reduce manipulation risk.

## 9. Discussion

### 9.1 What the Simulation Shows

- Hidden-information environments are highly sensitive to information quality.
- Village agents need structured evidence to overcome the wolves' private-information advantage.
- Deception is powerful when it can shape collective interpretation.
- Credibility and trust mechanisms must be outcome-aware.
- Reputation systems can help but can also introduce new vulnerabilities.

### 9.2 Why Speaker Memory Alone Can Hurt the Village

- Speaker memory may lock in early misleading impressions.
- Wolves may gain trust before village agents have enough evidence.
- Voting influence based on trust can amplify reputation errors.
- This suggests that trust systems need safeguards, validation, and decay.

### 9.3 Why Trust-Weighted Herding Helps

- Herding is a public amplification channel.
- If unreliable speakers contribute equally to public pressure, deception spreads more easily.
- Weighting herding by trust reduces the influence of low-credibility speakers.
- This makes trust-weighted herding more effective than trust-weighted speech alone in the current model.

## 10. Limitations

- The simulation uses simplified agents rather than learning agents.
- Speech is represented through controlled Bag-of-Words categories, not real natural language.
- Trust and credibility parameters are hand-coded.
- Only a small default role setup is tested.
- Only five seeds are used in the robustness experiment.
- No confidence intervals are computed beyond standard deviation.
- No visualization is included in the final experiments.
- Agents do not yet have rich private strategies or personalized reasoning models.
- Results may depend on the current payoff and update parameter choices.

## 11. Future Work

### 11.1 Model Calibration

- Calibrate trust update strength.
- Test trust decay over time.
- Tune credibility penalties.
- Compare different `p_wolf` update weights.

### 11.2 Expanded Robustness Testing

- Run more seeds.
- Run more games per condition.
- Add confidence intervals.
- Test sensitivity to role composition.

### 11.3 Improved Agent Reasoning

- Add more personalized agent memory.
- Allow agents to interpret the same speech differently.
- Add strategic village voting.
- Test adaptive village defenses against deception.

### 11.4 Language Extensions

- Expand the Bag-of-Words speech system.
- Add more structured speech content.
- Eventually connect controlled speech acts to natural language generation or parsing.

### 11.5 Reporting and Visualization

- Export final result tables.
- Add simple plots in a later analysis stage if allowed.
- Prepare final DURF presentation materials.

## 12. Proposed Final Report Structure

1. Abstract
2. Introduction
3. Background: Werewolf, Hidden Information, and Risk Scoring
4. Simulation Framework
5. Mechanism Design
6. Experimental Design
7. Results
8. Risk Management Interpretation
9. Discussion
10. Limitations
11. Future Work
12. Conclusion

## 13. Conclusion Draft

This project demonstrates that Werewolf can serve as a compact experimental environment for studying deception, credibility, and dynamic risk scoring under hidden information. The simulation shows that wolves strongly dominate in low-information settings, but village information mechanisms can robustly reduce this advantage. Wolf daytime deception partially restores wolf performance by manipulating public inference. However, deception must be understood together with credibility and trust: unchecked deception can distort collective decision-making, while poorly calibrated trust systems can unintentionally create new manipulation channels. The multi-seed robustness test confirms that the central results are not artifacts of a single random seed. Overall, the project supports a broader risk management lesson: dynamic risk scores and reputation systems are useful only when paired with carefully calibrated credibility controls and outcome-based validation.
