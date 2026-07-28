# R4 Event Attribution Rules

## Seer Information Attribution

The core ledger awards `seer_information_leads_to_wolf_elimination` only when
the same seer checked a wolf and that checked wolf was eliminated by day vote
within two rounds. The basic check reward remains separate from this later
attribution event.

## Witch Correct Save

The core ledger treats an antidote as correct when it is legally used on a
village-team night-kill target who would otherwise die. Saving a wolf or using a
potion without the legal target condition is treated as wasted potion.

## Hunter Correct Shot

The core ledger treats a hunter shot as correct only when the legal death shot
targets a werewolf. Shots into village-team players receive the proposal
wrong-shot penalty.

## Wolf Shared Rewards

Wolf special-kill and village-vote-elimination bonuses are team-shared and split
equally across all wolves. This prevents multiplying one team event by the wolf
count while preserving player-level totals.

## Opportunity Costs

Primary R4 opportunity costs use only observable rule-based states. Speculative
counterfactual full-rollout costs are excluded from the core ledger and deferred
to R5 risk-adjusted analysis.
