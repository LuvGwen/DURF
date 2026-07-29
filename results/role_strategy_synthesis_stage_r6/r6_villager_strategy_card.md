# R6 Villager Strategy Card

        ## Current Evidence Status

        Current default: structured speech plus belief/trust-aware voting reference

        Evidence grade: B

        Confidence: moderate

        ## Recommendation

        random voting has no supported improvement and live BoW overrides are harmful.

        ## Supported or Candidate Strategies

        | Strategy | Grade | Label | Recommendation |
| --- | --- | --- | --- |
| structured_speech_reference | B | retain reference/default | Retain structured speech and belief voting as the current Villager-facing default. |

        ## Rejected or No-Improvement Strategies

        | Strategy | Grade | Label | Main Risk |
| --- | --- | --- | --- |
| villager_random_vote | D | no supported improvement | does not improve payoff and discards available belief structure. |
| guarded_bow_010_live | E | statistically supported harmful | large harmful live effect. |
| structured_bow_guarded_live | E | statistically supported harmful | largest harmful R3 live effect. |
| selective_bow_vote_override_live | D | no supported improvement | no reliable improvement. |

        ## Remaining Gaps

        | Gap | Question | Priority | Required Experiment |
| --- | --- | --- | --- |
| R6-G05 | Which structured voting rule should villagers use after speech and trust updates? | high | suspicion-only, p_wolf-only, trust-weighted, herding-guarded, conservative vote policies |

        ## Source Boundaries

        This card synthesizes existing results only. It does not rerun simulation,
        change game mechanics, or claim a global optimum. Actor-specific evidence
        is separated from cross-role externalities.
