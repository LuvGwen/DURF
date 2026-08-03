# R7 Theoretical Synthesis

Generated on 2026-08-04. This R7 artifact is literature synthesis only; no gameplay experiment was run.

## Core Model

The DURF simulator can be interpreted as a hidden-information decision system. Players observe public events, generate speech signals, update suspicion and `p_wolf`, and act under role-specific incentives. R7 maps that design to four linked theory families: incomplete-information games, reputation-weighted social learning, deception/misinformation, and risk-adjusted decision metrics.

## Trust-Weighted Voting

Trust-weighted voting is best interpreted as reliability-sensitive aggregation. Reputation literature supports the idea that prior speaker reliability should affect later decisions, while cascade literature warns that uncalibrated public influence can amplify errors.

## BoW and Live Policy Failure

The BoW results fit domain-shift theory: lexical features can predict labels in a familiar template distribution but fail under unseen templates. Offline policy literature explains why even a useful predictor may reduce live outcomes when inserted into a feedback system.

## Seer Reveal and Information Premium

The Seer resembles an informed signaler. The positive information premium is consistent with information-economics theory, but reveal timing also creates exposure risk. R7 therefore keeps immediate reveal as promising but uncertain.

## Witch and Hunter Risk

Witch and Hunter mechanisms show why mean payoff alone is insufficient. Wrong poison and death shot outcomes concentrate downside risk; unused potions create opportunity cost.

## Werewolf Manipulation

Werewolf deception and night strategy instantiate strategic misinformation by an informed minority. Credibility costs and speaker memory are the model's safeguards against cost-free manipulation.

## Contribution Beyond Existing Work

The project contributes by combining social-deduction simulation, controlled speech signals, speaker-specific trust memory, role-specific payoff accounting, risk metrics, and live-policy validation in one reproducible Python environment.
