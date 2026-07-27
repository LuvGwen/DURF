# Remaining Work Roadmap

## Stage R0: Documentation and cumulative evidence completion

- Objective: Reconstruct evidence chain and proposal alignment.
- Unanswered question: Which claims are supported, rejected, or unresolved?
- Implementation: Generate documentation artifacts and validation script.
- Experiment: No new simulation; validate documentation only.
- Data Analysis: No new simulation; validate documentation only.
- Required report: research_progress documentation set.
- Entry condition: Existing reports and result files present.
- Exit condition: Required files pass validation.
- Dependencies: All prior committed results.
- Risk of overfitting or invalid inference: Risk of transcription error; mitigated by source traceability.
- Expected outputs: Cumulative reports, registry, proposal audit, roadmap, validation summary.

## Stage R1: ML Stage 2B - offline-to-live failure diagnosis

- Status: Completed in `results/ml_optimization_stage2b/`.
- Objective: Diagnose why frozen wolf-kill ML failed live.
- Unanswered question: Was failure caused by distribution shift, repeated-decision compounding, or special-role targeting loss?
- Implementation: Add diagnostic logging, not a new deployed policy.
- Experiment: Matched analysis of existing Stage 2A decisions and targeted small diagnostics if needed.
- Data Analysis: Matched analysis of existing Stage 2A decisions and targeted small diagnostics if needed.
- Required report: ML Stage 2B research report.
- Entry condition: Stage 2A negative result documented.
- Exit condition: Failure modes ranked with evidence.
- Completed output: `results/ml_optimization_stage2b/ml_stage2b_research_report.md`.
- Dependencies: Stage 2A artifacts.
- Risk of overfitting or invalid inference: High overfitting risk if tuned on live final seeds.
- Expected outputs: Failure taxonomy, drift metrics, opportunity-cost diagnostics.

## Stage R2: Formal Bag-of-Words speech quantification

- Status: Completed in `results/bow_speech_stage_r2/`.
- Objective: Implement proposal-level BoW metrics.
- Unanswered question: Can werewolf-leaning, emotional-intensity, and information-density scores be defined without leakage?
- Implementation: Tokenizer and score calculators.
- Experiment: Validation on generated speech events.
- Data Analysis: Validation on generated speech events.
- Required report: BoW quantification report.
- Entry condition: Documentation stage complete.
- Exit condition: Scores reproducible and observation-safe.
- Completed output: `results/bow_speech_stage_r2/bow_stage_r2_research_report.md`.
- Dependencies: Speech modules.
- Risk of overfitting or invalid inference: Risk of post-hoc metric design.
- Expected outputs: BoW lexicon, tokenizer, schema, validation.

## Stage R3: BoW integration and comparative Data Analysis

- Status: Next exact experiment.
- Objective: Test whether BoW metrics improve decisions.
- Unanswered question: Do formal BoW scores improve village coordination or enable wolf manipulation?
- Implementation: Integrate BoW scores into belief/voting toggles.
- Experiment: Matched multi-seed ablation.
- Data Analysis: Matched multi-seed ablation.
- Required report: BoW integration research report.
- Entry condition: R2 scores validated.
- Exit condition: Formal contrasts with CIs and adjusted p-values.
- Dependencies: R2 outputs.
- Risk of overfitting or invalid inference: Risk of confounding speech generation and voting.
- Expected outputs: Raw data, formal analysis, plots.

## Stage R4: Unified role-specific payoff matrix

- Objective: Synthesize payoff by role and strategy.
- Unanswered question: Which roles gain or lose under each mechanism?
- Implementation: Role-level payoff extraction.
- Experiment: Multi-seed payoff summary and formal contrasts.
- Data Analysis: Multi-seed payoff summary and formal contrasts.
- Required report: Role payoff report.
- Entry condition: Core results stable.
- Exit condition: Role payoff matrix complete.
- Dependencies: payoff.py and experiment outputs.
- Risk of overfitting or invalid inference: Risk of mixing game sizes and incompatible conditions.
- Expected outputs: Payoff matrix, expected payoff by role.

## Stage R5: Financial-risk and Sharpe-like payoff analysis

- Objective: Translate payoff into financial risk metrics.
- Unanswered question: Do strategies improve risk-adjusted returns?
- Implementation: Variance, downside risk, opportunity cost, Sharpe-like metrics.
- Experiment: Role/strategy risk-return analysis.
- Data Analysis: Role/strategy risk-return analysis.
- Required report: Financial risk report.
- Entry condition: R4 payoff matrix complete.
- Exit condition: Risk metrics validated and documented.
- Dependencies: R4 outputs.
- Risk of overfitting or invalid inference: Risk of overextending analogy.
- Expected outputs: Risk cost, opportunity cost, Sharpe-like tables.

## Stage R6: Unified role strategy optimization synthesis

- Objective: Compare strategic choices across roles.
- Unanswered question: Which strategies optimize team and individual outcomes?
- Implementation: No new mechanics unless needed; synthesize existing policies.
- Experiment: Formal cross-role strategy comparison.
- Data Analysis: Formal cross-role strategy comparison.
- Required report: Strategy synthesis report.
- Entry condition: R4 and R5 complete.
- Exit condition: Strategy recommendations labeled by evidence level.
- Dependencies: All strategy experiments.
- Risk of overfitting or invalid inference: Risk of multiple comparisons and selective reporting.
- Expected outputs: Unified strategy matrix.

## Stage R7: Systematic literature comparison

- Objective: Connect findings to social deduction, deception, trust, and financial manipulation literature.
- Unanswered question: Which findings align with prior theory?
- Implementation: Literature search and citation map.
- Experiment: No simulation required.
- Data Analysis: No simulation required.
- Required report: Literature comparison report.
- Entry condition: Core results documented.
- Exit condition: Citations and claim mapping complete.
- Dependencies: Final outline and reports.
- Risk of overfitting or invalid inference: Risk of unsupported analogy.
- Expected outputs: Literature matrix and synthesis.

## Stage R8: Final integrated Data Analysis

- Objective: Finalize statistical evidence for report.
- Unanswered question: Which claims remain significant or practically meaningful after correction?
- Implementation: Consolidated analysis scripts.
- Experiment: Formal models, CIs, effect sizes, robustness summaries.
- Data Analysis: Formal models, CIs, effect sizes, robustness summaries.
- Required report: Final Data Analysis report.
- Entry condition: R1-R7 complete or intentionally deferred.
- Exit condition: All final claims trace to source files.
- Dependencies: All results.
- Risk of overfitting or invalid inference: Risk of treating pilots as final.
- Expected outputs: Final tables, plots, evidence registry.

## Stage R9: Final DURF report and presentation

- Objective: Produce final written report and presentation.
- Unanswered question: What did the project establish scientifically?
- Implementation: Write report and refresh presentation.
- Experiment: No new analysis except final checks.
- Data Analysis: No new analysis except final checks.
- Required report: Final DURF report and final presentation.
- Entry condition: R8 complete.
- Exit condition: Final deliverables ready to submit.
- Dependencies: All prior reports.
- Risk of overfitting or invalid inference: Risk of overclaiming incomplete proposal pieces.
- Expected outputs: Final report, slides, appendix.
