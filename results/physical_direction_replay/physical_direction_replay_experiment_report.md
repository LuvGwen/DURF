# Physical-Direction Replay Experiment Report

## Replay Framework Design

This stage adds a diagnostic supplied-action replay layer. Reference games are generated with the existing seat-order-neutral engine, then their event logs are converted into stable `SuppliedAction` records keyed by `actor_uid` and physical target identity. `ReplayController` consumes those records without calling strategy modules for new decisions.

## Physical Mirror Definition

The physical mirror maps seats 1<->10, 2<->9, 3<->8, 4<->7, and 5<->6. Actor identity and role identity are preserved, while physical seats and physical direction metadata are mirrored. Clockwise distances map to counterclockwise distances.

## Action Capture Design

Action capture parses the reference `event_log` into ordered external actions: seer checks, wolf kills, witch saves and poisons, hunter shots, speech acts, individual votes, abstentions, and day-vote resolution. Non-decision bookkeeping events such as `player_death` are not used as strategy choices; their effects are represented by the supplied action that caused the death.

## State Canonicalization Design

Canonical physical state serializes round, phase, game-over flag, winner, actor_uid, physical seat, role, alive/dead state, suspicion_score, p_wolf, potion state, check memory, and vote state with sorted JSON keys and sha256 hashing. For mirror comparisons, mirrored physical seats are transformed back into reference coordinates before comparison.

## Experiment Scale

- Experiment A supplied replay pairs: 1000
- Experiment B physical mirror replay pairs: 2500
- Experiment C strategy mirror pairs: 5000
- Experiment C completed games: 10000

## Summary Results

| component | pairs | exact replay | physical mirror | strategy action mirror | winner match | final alive match |
|---|---:|---:|---:|---:|---:|---:|
| supplied_action_replay | 1000 | 100.00% | NA | NA | 100.00% | 100.00% |
| physical_mirror_replay | 2500 | 100.00% | 100.00% | NA | 100.00% | 100.00% |
| strategy_mirror_counterfactual | 5000 | NA | NA | 100.00% | 100.00% | 100.00% |

## Divergence Summary

| component | phase | type | divergences |
|---|---|---|---:|
| all | none | none | 0 |

## Subsystem-Specific Diagnostics

Unit diagnostics passed for fixed-action speech-only, vote-only, wolf-kill-only, witch-save/poison, hunter-shot, chained-death, duplicate seer-check rejection, wrong-phase rejection, and illegal target rejection scenarios. No replay divergence was observed in the full generated experiment outputs.

## Required Questions

1. **Can a captured game be replayed exactly from supplied actions?** yes. Exact replay match rate is 100.00%.
2. **Does physical mirroring preserve engine behavior under fixed actions?** yes. Physical mirror replay match rate is 100.00%.
3. **Are all core subsystems physically symmetric under predetermined actions?** supported by unit diagnostics. The dedicated replay tests cover speech, vote, wolf kill, witch, hunter, and chained death fixed-action cases.
4. **Does clockwise map exactly to counterclockwise under physical mirroring?** yes. First-check mirror match rate is 100.00%.
5. **Do mirrored strategy pairs produce mirrored full check sequences?** yes. Full check sequence mirror match rate is 100.00%.
6. **Do mirrored strategy pairs produce mirrored first-check targets?** yes. First-check mirror match rate is 100.00%.
7. **At what point do strategy-mirror pairs first diverge?** none observed. First divergence details are stored in replay_divergence_events.csv.
8. **Is any divergence caused by speech, voting, wolf action, witch action, hunter action, death resolution, seer strategy, or state feedback?** none observed. The divergence summary contains zero observed divergence events across replay and strategy-mirror outputs.
9. **Can residual physical engine asymmetry explain the previous clockwise advantage?** unlikely in this diagnostic scope. Fixed-action replay and mirrored fixed-action replay are symmetric in the generated dataset.
10. **Is the previous clockwise advantage more likely engine artifact, path-layout interaction, random variation, or unresolved?** path-layout interaction or random variation. The replay harness did not detect non-strategy engine asymmetry; formal follow-up analysis should quantify remaining uncertainty.
11. **Is the simulator valid enough for final directional inference?** closer, but final inference still needs formal analysis. This task is implementation and descriptive validation only; no advanced hypothesis testing is performed here.
12. **Is the structured-search chapter ready to close?** not yet. The next Data Analytics stage should formally analyze these replay and strategy-mirror outputs.
13. **What should the next formal Data Analytics stage analyze?** replay outputs. Analyze match rates, divergence distributions, and whether strategy-mirror equivalence eliminates the earlier clockwise/counterclockwise concern.

## Decision Rule

ENGINE PHYSICAL SYMMETRY SUPPORTED and STRATEGY MIRROR SYMMETRY SUPPORTED.
