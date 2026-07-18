# DURF Werewolf Simulation: Multi-Seed Robustness Report

## 1. Overview

Previous experiments in the DURF Werewolf simulation mostly used one fixed random seed. The purpose of this robustness test is to check whether the main findings remain stable across multiple seeds rather than depending on one particular random draw.

This experiment uses five seeds: 42, 43, 44, 45, and 46. For each seed, each condition is run for 500 games. The report summarizes wolf win rate mean, range, and standard deviation across seeds, along with village win rate mean.

## 2. Experimental Conditions

1. `random_baseline`

   This is the low-information baseline. It disables advanced speech, trust, deception, and belief mechanisms, so village agents have little reliable information to coordinate around.

2. `wolf_strategy`

   This condition uses an information-rich village model while wolves use a strategic night-kill policy. It includes core village information mechanisms such as speech, belief updating, role prior, herding, and special role actions.

3. `wolf_deception`

   This condition adds daytime deception for wolves. Wolves can influence daytime discussion rather than only acting through night kills.

4. `speaker_memory_vote_only`

   This condition enables speaker-specific trust memory and lets speaker trust affect voting. Trust memory changes how much voters rely on different speakers.

5. `trust_weighted_speech`

   This condition lets speaker trust affect the influence of speech on belief and suspicion updates. High-trust speakers have stronger speech effects, while low-trust speakers have weaker effects.

6. `trust_weighted_herding`

   This condition lets speaker trust affect herding pressure. Public pressure is filtered by speaker credibility.

7. `trust_weighted_speech_and_herding`

   This condition enables both trust-weighted speech and trust-weighted herding.

## 3. Results Table

| Condition | Wolf Mean % | Wolf Range | Wolf Stdev | Village Mean % |
|---|---:|---|---:|---:|
| random_baseline | 91.68 | 90.00-93.00 | 1.25 | 8.32 |
| wolf_strategy | 38.40 | 32.80-43.40 | 3.77 | 61.60 |
| wolf_deception | 42.28 | 38.80-44.00 | 2.09 | 57.72 |
| speaker_memory_vote_only | 57.88 | 54.80-60.40 | 2.04 | 42.12 |
| trust_weighted_speech | 56.76 | 54.80-58.60 | 1.34 | 43.24 |
| trust_weighted_herding | 54.72 | 52.40-57.60 | 2.08 | 45.28 |
| trust_weighted_speech_and_herding | 55.80 | 52.40-58.60 | 2.23 | 44.20 |

## 4. Key Findings

### Finding 1: The low-information baseline consistently favors wolves

The `random_baseline` condition has a wolf mean win rate of 91.68% and a low standard deviation of 1.25 percentage points. This confirms the baseline assumption that wolves dominate when village agents lack reliable information.

### Finding 2: Information-rich village mechanisms robustly reduce wolf advantage

The `wolf_strategy` condition has a wolf mean win rate of 38.40% and a village mean win rate of 61.60%. This shows that speech, belief updating, role prior, herding, and village role mechanisms create a strong information advantage for the village.

### Finding 3: Wolf daytime deception partially restores wolf performance

Wolf win rate increases from 38.40% in `wolf_strategy` to 42.28% in `wolf_deception`. This is an increase of about 3.88 percentage points. The result shows that deceptive communication matters, but it does not fully restore the strong wolf dominance seen in the low-information baseline.

### Finding 4: Speaker memory is not automatically beneficial for the village

Wolf win rate increases from 42.28% in `wolf_deception` to 57.88% in `speaker_memory_vote_only`. This suggests that reputation systems can be manipulated or may create unintended effects if they are not carefully calibrated.

### Finding 5: Trust-weighted herding is the most useful trust-based correction among the tested variants

Compared with `speaker_memory_vote_only`, which has a wolf mean win rate of 57.88%, `trust_weighted_herding` reduces wolf win rate to 54.72%. This reduction is larger than the reduction from `trust_weighted_speech` alone, which has a wolf mean win rate of 56.76%. The combined `trust_weighted_speech_and_herding` condition has a wolf mean win rate of 55.80%.

This suggests that public pressure is a key channel through which deception spreads. Filtering herding pressure by speaker credibility appears more useful than only weighting speech influence.

### Finding 6: The trust-based extensions show moderate but not decisive robustness

The trust-weighted mechanisms improve over `speaker_memory_vote_only`, but wolves still retain a majority win rate in those conditions. This means that the current trust mechanisms are promising but not sufficient. More calibration is needed before trust memory can be treated as a reliable village defense against deception.

## 5. Interpretation

The larger pattern is clear. Information mechanisms help the village by giving agents more structure for interpreting votes, speech, roles, and public pressure. Deception helps wolves by giving them a way to manipulate daytime discussion. Credibility costs and trust mechanisms can reduce deception, but they must be carefully designed. Trust memory is not automatically protective; it can create new manipulation channels if wolves learn how to exploit reputation dynamics. The strongest risk-management lesson is that reputation systems need calibration and outcome-based validation.

## 6. Risk Management Connection

The simulation has a direct connection to risk management. The `p_wolf` variable is analogous to a dynamic risk score that changes as new signals arrive. Wolf deception is analogous to adversarial manipulation, fraud, or misinformation. Credibility costs function as risk-control mechanisms that penalize repeated misleading behavior. Speaker memory is analogous to reputation history. Herding pressure is analogous to an information cascade or systemic risk, where public opinion can amplify misleading signals. Trust-weighted herding shows that filtering public pressure by speaker credibility can reduce manipulation risk.

## 7. Current Limitations

- Only five seeds were tested.
- No confidence intervals beyond standard deviation were computed.
- Trust mechanisms are still hand-coded.
- Agents do not yet have personalized interpretations of trust.
- Trust memory may be overly sensitive to early-game outcomes.
- No visualization has been added yet.
- No real natural language input is used yet.

## 8. Next Steps

1. Run larger multi-seed tests if time allows.
2. Calibrate speaker memory parameters.
3. Test trust memory with stronger outcome validation.
4. Add confidence intervals.
5. Export final result tables.
6. Prepare the final DURF report and presentation.
7. Avoid adding major new mechanisms until results are consolidated.

## 9. Conclusion

The multi-seed robustness test confirms several major findings: wolves dominate in low-information settings, village information mechanisms robustly reduce wolf advantage, and wolf deception partially restores wolf performance. However, trust and reputation mechanisms require careful calibration. Speaker memory alone can unintentionally improve wolf outcomes, while trust-weighted herding appears to be the most promising correction by reducing the influence of low-credibility speakers on public pressure.
