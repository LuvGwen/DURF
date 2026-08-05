# R8.3 Inference Interpretation Standard

## Primary CI

The primary effect interval is the candidate-minus-reference matched-set
bootstrap confidence interval over actor-payoff differences. The inference
block is `matched_set_id`.

## Multiplicity

The reported CI is not multiplicity-adjusted. The confirmatory decision is
controlled by the Holm-adjusted p-value across exactly three primary tests:
Villager, Seer, and Witch.

## Conflicting CI and P-Value Reporting

If an unadjusted CI excludes zero but the Holm-adjusted p-value is not
confirmatory, the result must be reported as positive-direction but not
confirmatorily replicated. An unadjusted CI must not be described as
overriding the preregistered adjusted test.

## Policy-Level CIs Versus Paired-Effect CIs

Policy-level CIs describe the mean outcome for one policy. Paired-effect CIs
describe the matched candidate-minus-reference contrast and are the relevant
interval for R8.3 primary inference.

## Bootstrap Versus Sign-Flip Inference

The matched bootstrap estimates uncertainty in the paired mean difference.
The sign-flip test estimates a two-sided null distribution under exchangeable
signs for all matched differences, including zero differences. Removing zero
differences while changing the denominator is not valid for the R8.3 primary
test.
