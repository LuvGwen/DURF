# R8 Limitations Registry

| ID | Domain | Limitation | Reporting Rule |
| --- | --- | --- | --- |
| L_R8_01 | simulation environment | The Werewolf environment is synthetic and self-built. | Report findings as simulation evidence, not direct human-subject evidence. |
| L_R8_02 | speech | Generated BoW utterances are template-bound and not a natural conversation corpus. | Use BoW as controlled signal engineering; do not claim natural-language generality. |
| L_R8_03 | sample units | Games, matched sets, player rows, events, utterances, and rollouts are incompatible units. | Never sum these units into a single independent sample size. |
| L_R8_04 | strategy search | The strongest tested policy is not proof of a global optimum. | Use the phrase strongest tested policy and preserve strategy-space bounds. |
| L_R8_05 | ML | Offline predictive or rollout quality did not reliably transfer to live policy control. | Treat ML outputs as diagnostic unless matched live policy evidence supports deployment. |
| L_R8_06 | financial analogy | Payoffs are not externally priced financial returns. | Use risk metrics as formal analogues within the game ledger only. |
| L_R8_07 | causal inference | Premium analyses are descriptive associations because exposure groups are behaviorally selected. | Do not label premiums as causal effects. |
| L_R8_08 | historical coverage | Some historical outputs are summary-only and cannot be recalculated at event level. | Use later raw game-level stages for formal inference and list historical datasets separately. |
