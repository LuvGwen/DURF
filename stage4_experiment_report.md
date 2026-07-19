# DURF Werewolf Simulation: Stage 4 Experiment Report

## 1. Overview

Stage 1 built the basic Werewolf simulation, including the game loop, role setup, win conditions, batch simulation, and payoff calculation.

Stage 2 added language-like and belief-based mechanisms, including Bag-of-Words speech signals, `p_wolf` belief updating, herding pressure, role prior, wolf night-kill strategy, and result export.

Stage 3 added wolf daytime deception and credibility costs. Wolves could use false accusations, false defenses, role claims, suspicion deflection, and trust-building speech. Credibility costs prevented deception from becoming a cost-free dominant strategy.

Stage 4 adds speaker-specific trust memory. The goal is to test whether agents can resist deception by remembering which speakers were reliable or misleading in previous discussion.

## 2. Motivation

In previous stages, agents had global `suspicion_score` and `p_wolf` values, but they did not strongly distinguish between reliable and unreliable speakers. A wolf who repeatedly misled the village could still influence votes unless the deception also raised global suspicion.

Stage 4 asks:

- Can players learn who is trustworthy?
- Can correct accusations increase speaker credibility?
- Can wrong accusations reduce speaker credibility?
- Does speaker trust memory help village agents resist wolf deception?

## 3. Stage 4 Mechanisms

### 3.1 Speaker-Specific Trust Memory

Stage 4 adds:

- `speaker_memory.py`

Each player stores a trust score for other speakers. Conceptually, this is:

```text
player.memory["speaker_trust"][speaker_id] = trust_score
```

In the current implementation, speaker trust is stored as structured memory records inside each `Player.memory` list. Each record tracks:

- speaker id
- trust score
- number of observations
- positive updates
- negative updates
- most recent update reason

Trust scores are clipped to the range:

```text
0.0 <= trust_score <= 1.0
```

The neutral starting value is:

```text
trust_score = 0.50
```

### 3.2 Trust-Aware Voting

Stage 4 connects trust memory to voting through `voting.py`.

The voting score now includes a trust-memory term:

```text
vote_score =
    alpha * suspicion_score
    + beta * p_wolf
    + gamma * herding_pressure
    + delta * role_prior_score
    + trust_vote_weight * speaker_memory_score
    + noise
```

The trust-memory component is:

```text
speaker_memory_score = 0.5 - trust_score
```

This means:

- If a voter trusts a candidate less than 0.50, that candidate becomes more likely to receive a vote.
- If a voter trusts a candidate more than 0.50, that candidate becomes less likely to receive a vote.
- If trust remains at 0.50, speaker memory has no direct voting effect.

### 3.3 Trust Updates from Speech Credibility

Speaker trust can be updated when existing credibility events occur.

Examples:

- Repeated accusations reduce trust in the speaker.
- Repeated self-defense or excessive trust-building can reduce trust.
- A speaker who made a wrong accusation can lose credibility when the target is later revealed.

These updates are tracked as speaker trust updates.

### 3.4 Trust Updates from Vote Outcomes

Stage 4 also adds:

- `trust_update.py`

This module updates speaker trust based on whether a speech act was validated by the later vote outcome.

The current vote-outcome rules are:

| Speech Type | Eliminated Target Is Wolf | Eliminated Target Is Village |
|---|---:|---:|
| accusation or question | `+0.08` trust | `-0.10` trust |
| defense or trust | `-0.08` trust | `+0.06` trust |

The supported speech formats include:

- ordinary accusations
- ordinary questions
- ordinary defenses
- ordinary trust statements
- wolf `false_accuse`
- wolf `false_defend`

Vote outcome trust updates are stored inside the `day_vote` event:

```text
day_vote.content["vote_outcome_trust_events"]
```

Each update event records:

- observer
- speaker
- target
- trust delta
- reason
- trust after update

## 4. Debug Fix: Vote Outcome Trust Updates

The first Stage 4 implementation successfully produced speaker trust updates, but vote outcome trust updates remained at zero:

```text
Total speaker trust updates > 0
Total vote outcome trust updates = 0
```

This indicated that trust memory existed, but the vote-outcome validation path was not being triggered correctly.

The fix involved three changes:

1. `trust_update.py` was updated to provide `update_trust_from_vote_outcome(game_state, speech_events, eliminated_id)`.
2. `game.py` was updated so `day_phase()` calls this function while the current day's `speech_events` are still available.
3. `simulation.py` was updated to count trust updates from:

```text
day_vote.content["vote_outcome_trust_events"]
```

After the fix, vote outcome trust updates became nonzero.

## 5. Unit-Level Trust Update Tests

The `trust_update.py` test checks two cases.

### 5.1 Correct Accusation

Speaker 2 accused wolf player 1.

Result:

```text
Other players increased trust in speaker 2 from 0.50 to 0.58.
```

Output:

```text
[{'observer': 1, 'speaker': 2, 'target': 1, 'delta': 0.08, 'reason': 'correct_accusation', 'trust_after': 0.58}, {'observer': 3, 'speaker': 2, 'target': 1, 'delta': 0.08, 'reason': 'correct_accusation', 'trust_after': 0.58}, {'observer': 4, 'speaker': 2, 'target': 1, 'delta': 0.08, 'reason': 'correct_accusation', 'trust_after': 0.58}]
```

### 5.2 Wrong Accusation and Correct Defense

Speaker 1 falsely accused village player 3.

Result:

```text
Other players decreased trust in speaker 1 from 0.50 to 0.40.
```

Speaker 4 defended village player 3.

Result:

```text
Other players increased trust in speaker 4 from 0.50 to 0.56.
```

Output:

```text
[{'observer': 2, 'speaker': 1, 'target': 3, 'delta': -0.1, 'reason': 'wrong_accusation', 'trust_after': 0.4}, {'observer': 3, 'speaker': 1, 'target': 3, 'delta': -0.1, 'reason': 'wrong_accusation', 'trust_after': 0.4}, {'observer': 4, 'speaker': 1, 'target': 3, 'delta': -0.1, 'reason': 'wrong_accusation', 'trust_after': 0.4}, {'observer': 1, 'speaker': 4, 'target': 3, 'delta': 0.06, 'reason': 'correct_defense', 'trust_after': 0.56}, {'observer': 2, 'speaker': 4, 'target': 3, 'delta': 0.06, 'reason': 'correct_defense', 'trust_after': 0.56}, {'observer': 3, 'speaker': 4, 'target': 3, 'delta': 0.06, 'reason': 'correct_defense', 'trust_after': 0.56}]
```

## 6. Sensitivity Experiment

Stage 4 adds:

- `speaker_memory_experiment.py`
- `speaker_memory_sensitivity.py`

The sensitivity experiment tests whether speaker memory has no effect, or whether the original trust voting weight was too weak.

The experiment varies:

```text
trust_vote_weight
```

while keeping the rest of the Stage 4 setup fixed.

Tested values:

```text
0.00, 0.05, 0.10, 0.20, 0.30, 0.40
```

Each condition used 500 games with the fixed random seed.

## 7. Sensitivity Results

| Trust Vote Weight | Wolf Win % | Village Win % | Vote Outcome Trust Updates |
|---:|---:|---:|---:|
| 0.00 | 47.80 | 52.20 | 4717 |
| 0.05 | 44.40 | 55.60 | 4695 |
| 0.10 | 42.20 | 57.80 | 4689 |
| 0.20 | 41.20 | 58.80 | 4604 |
| 0.30 | 42.60 | 57.40 | 4606 |
| 0.40 | 36.40 | 63.60 | 4678 |

## 8. Main Findings

### Finding 1: Vote outcome trust updates are now active

Before the debug fix, vote outcome trust updates were always zero. After the fix, the sensitivity experiment produced thousands of vote outcome trust updates per condition.

This confirms that speech acts are now being evaluated against later voting outcomes.

### Finding 2: Trust memory can reduce wolf win rate

With `trust_vote_weight = 0.00`, wolves won 47.80% of games.

With `trust_vote_weight = 0.40`, wolves won 36.40% of games.

This suggests that speaker-specific trust memory helps the village resist wolf deception when trust is given enough weight in voting.

### Finding 3: The effect is not perfectly linear

Village win rate generally improves as trust weight increases, but the trend is not strictly monotonic:

- `trust_vote_weight = 0.20` produced 58.80% village wins.
- `trust_vote_weight = 0.30` produced 57.40% village wins.
- `trust_vote_weight = 0.40` produced 63.60% village wins.

This is expected in a stochastic simulation with interacting mechanisms such as wolf deception, witch saves, hunter shots, and seer checks.

### Finding 4: Trust memory separates wolf credibility from village credibility

After vote outcome trust updates were fixed, average wolf trust received fell below neutral more clearly than village trust received.

This supports the intended Stage 4 mechanism: deceptive wolves can lose credibility over time when their speech is contradicted by outcomes.

### Finding 5: Speaker memory changes the deception environment

In Stage 3, wolves could use adaptive deception while mainly facing global credibility costs. In Stage 4, misleading speech can also affect how individual observers evaluate the speaker.

This makes deception more socially risky. A wolf does not only become more globally suspicious; specific listeners may also become less willing to follow that wolf's future speech.

## 9. Interpretation

Stage 4 provides evidence that speaker-specific trust memory is useful for modeling social deduction.

The most important shift is that reliability becomes agent-specific. A player's speech is no longer treated only as a global signal. Instead, each observer can maintain a separate judgment about that speaker's credibility.

This is closer to real Werewolf-style reasoning:

- A player who correctly identifies a wolf becomes more credible.
- A player who repeatedly misleads the village becomes less credible.
- A defense of an innocent player can improve credibility.
- A defense of a wolf can damage credibility.

The sensitivity results show that trust memory has a measurable effect when connected strongly enough to voting.

## 10. Current Limitations

- Trust memory is still symbolic and rule-based.
- There is no natural language understanding.
- Trust updates depend on simplified speech categories.
- Vote outcome feedback is based on eliminated players, not richer public discussion.
- Observers update trust uniformly rather than based on their private beliefs or role.
- The model does not yet distinguish between public truth, private knowledge, and inferred truth.
- Trust scores remain fairly close to 0.50 in many games.
- Wolves do not yet strategically model which players trust them.

## 11. Next Steps

Possible next steps include:

1. Add observer-specific trust weighting.
   - Different players could care more or less about trust memory.

2. Let wolves reason about trust memory.
   - Wolves could choose deception targets based on which villagers still trust them.

3. Add memory decay.
   - Older speech outcomes could matter less than recent evidence.

4. Distinguish public and private evidence.
   - Seer information, wolf knowledge, and public elimination outcomes should have different epistemic status.

5. Improve false defense and trust-building modeling.
   - Supportive speech should become more meaningful when role claims and alliances become richer.

6. Export Stage 4 results.
   - Add Markdown and CSV export for speaker memory experiments.

7. Write a Stage 4 ablation table.
   - Compare Stage 3 adaptive deception against Stage 4 speaker memory under the same random seed and game count.

## 12. Conclusion

Stage 4 extends the simulation from global suspicion to speaker-specific social memory. The model now allows agents to remember which speakers were reliable or misleading, and vote outcome trust updates are correctly triggered.

The sensitivity experiment shows that stronger trust-aware voting can reduce wolf win rate from 47.80% to 36.40%. This suggests that speaker memory is a meaningful defense against wolf deception, especially when voters give enough weight to credibility history.

This completes the first working version of speaker-specific trust memory for the DURF Werewolf simulation.
