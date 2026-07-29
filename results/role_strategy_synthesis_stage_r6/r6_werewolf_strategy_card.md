# R6 Werewolf Strategy Card

        ## Current Evidence Status

        Current default: existing night-kill rule plus credibility-constrained deception diagnostics

        Evidence grade: B

        Confidence: moderate

        ## Recommendation

        random kill is formally harmful and live frozen ML policies do not beat the existing rule.

        ## Supported or Candidate Strategies

        | Strategy | Grade | Label | Recommendation |
| --- | --- | --- | --- |
| existing_rule_night_kill_reference | B | retain reference/default | Retain existing night-kill rule as the current Werewolf reference. |
| ml_first_kill_only | C | promising but uncertain | Treat as a future candidate only. |
| adaptive_deception_with_credibility_costs | C | conditionally recommended | Use as a controlled deception model, not as a final Werewolf optimization claim. |

        ## Rejected or No-Improvement Strategies

        | Strategy | Grade | Label | Main Risk |
| --- | --- | --- | --- |
| wolf_random_kill | E | statistically supported harmful | large supported payoff loss for wolves. |
| continuous_frozen_ml | E | not recommended | practically harmful live rollout. |
| frozen_hybrid_50_50 | E | statistically supported harmful | statistically supported harm. |
| selective_ml_override | D | no supported improvement | no reliable improvement. |
| false_role_claim | E | not recommended | severe wolf performance loss. |

        ## Remaining Gaps

        | Gap | Question | Priority | Required Experiment |
| --- | --- | --- | --- |
| R6-G04 | Should wolves prefer aggression or deep-cover deception under credibility costs? | high | adaptive, false-accuse, deflection, trust-building, low-profile controls |

        ## Source Boundaries

        This card synthesizes existing results only. It does not rerun simulation,
        change game mechanics, or claim a global optimum. Actor-specific evidence
        is separated from cross-role externalities.
