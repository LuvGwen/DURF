# Permanent Stage Reporting Standard

Every future DURF Werewolf stage must produce the following before it can be marked complete:

1. Implementation or experiment outputs.
2. Formal Data Analysis, or an explicit statement that only implementation validation was possible.
3. Stage research report.
4. Cumulative evidence registry update.
5. Cumulative research report update.
6. Proposal-alignment audit update where relevant.
7. Next hypothesis.
8. Exact next experiment.
9. Reproducibility information.
10. Git commit and push status.

## Required Stage Report Sections

Each stage report must include background, prior-stage connection, hypothesis, pre-specified outcomes, experimental design, data scale, independent sample definition, implementation, validation, Data Analysis, descriptive findings, formal inference, robustness, leakage/overfitting/design audit, scientific interpretation, conclusion label, limitations, next hypothesis, source files, reproducibility information, and commit information.

## Required Evidence Discipline

- Distinguish descriptive results from formal statistical results.
- State the independent unit.
- Separate raw rows from games, decision states, matched sets, and deterministic duplicates.
- Report confidence intervals and effect sizes when formal inference is performed.
- Report raw and adjusted p-values when multiple comparisons are tested.
- Preserve superseded findings rather than deleting them.
- Never treat shadow policy values as live win rates.
- Never treat candidate rows as independent games.
- Never claim BoW completion unless tokenized text features and proposed speech scores exist.
- Never claim financial-risk completion unless risk cost, opportunity cost, payoff variance, and Sharpe-like metrics are formally computed.

## Required Conclusion Labels

Allowed labels are:

- statistically supported improvement
- statistically supported harmful effect
- promising but uncertain
- weak/inconclusive
- no meaningful improvement
- overfit
- unstable across regimes
- surrogate-only improvement
- invalid due to leakage
- invalid due to design limitation
- hypothesis supported
- hypothesis rejected
- hypothesis unresolved
- implementation validated
- engine symmetry validated

No future stage may be marked complete unless all applicable reporting outputs exist.
