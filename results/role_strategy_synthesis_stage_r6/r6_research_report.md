# R6 Unified Role Strategy Evidence Synthesis

        ## 1. Executive Summary

        R6 synthesizes the tested strategy space across Villager, Seer, Witch,
        Hunter, and Werewolf roles. It is a synthesis of existing evidence, not a
        new gameplay experiment. The analysis reviews 25 source files,
        classifies 23 strategy or mechanism rows across 5
        roles, separates actor-specific evidence from cross-role externalities,
        and preserves negative findings from BoW integration, ML deployment, and
        strategy attribution audits.

        The current conclusion is role synthesis complete with sparse-strategy
        caveat. Current defaults can be documented, but targeted experiments are
        required before final role-specific strategy recommendations are complete.
        The exact next stage is R6.1 - Targeted Missing Strategy Experiments.

        ## 2. Scope and Non-Intervention Boundary

        R6 does not change the simulator, payoff rules, role setup, BoW weights, ML
        models, or decision policies. It reads frozen historical artifacts and
        writes analysis registries, recommendation cards, gap lists, and reports.

        ## 3. Evidence Sources Reviewed

        | Source | Rows/Lines | Metrics Used | Status |
| --- | --- | --- | --- |
| results/payoff_matrix_stage_r4/r4_payoff_manifest.json | 654 | context, validation, or report narrative | verified_from_source |
| results/financial_risk_stage_r5/r5_metric_definition_manifest.json | 127 | context, validation, or report narrative | verified_from_source |
| results/financial_risk_stage_r5/r5_role_expected_payoff_summary.csv | 10 | context, validation, or report narrative | verified_from_source |
| results/financial_risk_stage_r5/r5_role_var_cvar_summary.csv | 10 | context, validation, or report narrative | verified_from_source |
| results/financial_risk_stage_r51/r51_mapping_validation_summary.csv | 1 | context, validation, or report narrative | verified_from_source |
| results/financial_risk_stage_r51/r51_actor_specific_strategy_summary.csv | 8 | mean payoff, volatility, downside, Sharpe-like, Sortino-like metrics | verified_from_source |
| results/financial_risk_stage_r51/r51_actor_specific_primary_contrasts.csv | 8 | actor-specific payoff differences, CIs, raw and Holm-adjusted p-values | verified_from_source |
| results/financial_risk_stage_r51/r51_cross_role_externality_summary.csv | 32 | cross-role externality payoff differences | verified_from_source |
| results/financial_risk_stage_r51/r51_information_premium_summary.csv | 6 | information premium estimates and CIs | verified_from_source |
| results/financial_risk_stage_r51/r51_manipulation_premium_summary.csv | 8 | manipulation premium estimates and imbalance warnings | verified_from_source |
| results/financial_risk_stage_r51/r51_r5_result_validity_registry.csv | 10 | context, validation, or report narrative | verified_from_source |
| results/bow_speech_stage_r2/bow_stage_r2_research_report.md | 56 | context, validation, or report narrative | verified_from_source |
| results/bow_integration_stage_r3/r3_policy_game_outcome_summary.csv | 7 | context, validation, or report narrative | verified_from_source |
| results/bow_integration_stage_r3/r3_primary_game_contrasts.csv | 3 | matched BoW live game contrasts | verified_from_source |
| results/structured_seer_search/structured_seer_search_strategy_summary.csv | 14 | seer search strategy outcome rates | verified_from_source |
| results/data_analysis/structured_seer_search/pairwise_strategy_contrasts.csv | 8 | structured seer pairwise tests | verified_from_source |
| results/data_analysis/structured_seer_search/strategy_omnibus_tests.csv | 4 | context, validation, or report narrative | verified_from_source |
| results/data_analysis/seer_position_randomized_roles/statistical_summary.csv | 7 | context, validation, or report narrative | verified_from_source |
| results/data_analysis/seer_position_randomized_roles/pairwise_strategy_comparisons.csv | 42 | context, validation, or report narrative | verified_from_source |
| results/data_analysis/seat_order_neutral/validation_summary.csv | 21 | context, validation, or report narrative | verified_from_source |
| results/ml_optimization_stage2a/wolf_kill_live_policy_summary.csv | 4 | context, validation, or report narrative | verified_from_source |
| results/ml_optimization_stage2a/wolf_kill_primary_contrasts.csv | 3 | ML Stage 2A live policy contrasts | verified_from_source |
| results/ml_optimization_stage2b/stage2b_policy_win_summary.csv | 8 | context, validation, or report narrative | verified_from_source |
| results/ml_optimization_stage2b/stage2b_primary_contrasts.csv | 4 | ML Stage 2B live policy contrasts | verified_from_source |
| stage3_experiment_report.md | 237 | context, validation, or report narrative | verified_from_source |

        ## 4. Evidence Grading System

        | Grade | Definition |
| --- | --- |
| A | Strong formal support: valid actor-specific comparison, adequate sample, adjusted inference, and no major design concern. |
| B | Moderate support: valid repeated evidence with stable direction, but formal inference or strategy coverage is incomplete. |
| C | Promising but uncertain: positive or useful signal with unresolved inference, sparse coverage, or confidence intervals crossing no effect. |
| D | No supported improvement: no reliable advantage over the relevant reference condition. |
| E | Supported harmful or not recommended: formal harm, repeated live-policy failure, or clear negative mechanism result. |
| F | Invalid or superseded: leakage, mapping error, surrogate-only result contradicted by live validation, or superseded attribution. |
| U | Unresolved or insufficient data: no compatible actor-specific comparison or missing event-level coverage. |

        ## 5. Evidence Priority Rules

        R6 prioritizes complete live-game outcomes above matched actor-specific
        payoff analysis, then grouped formal analysis, multi-seed summaries,
        full-rollout counterfactuals, shadow diagnostics, surrogate prediction,
        and single-seed descriptive findings. This resolves the main conflicts:
        R3 live BoW outcomes outrank R2 predictive AUC, Stage 2A/2B live ML
        outcomes outrank shadow ML diagnostics, and R5.1 actor attribution
        supersedes ambiguous R5 strategy-frontier labels.

        ## 6. Role Strategy Decision Matrix

        | Role | Strategy | Evidence Type | Grade | Label | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Villager | structured_speech_reference | global_configuration | B | retain reference/default | Retain structured speech and belief voting as the current Villager-facing default. |
| Villager | villager_random_vote | actor_specific | D | no supported improvement | Do not replace the structured-voting reference with random voting. |
| Villager | guarded_bow_010_live | global_configuration | E | statistically supported harmful | Keep formal BoW as diagnostic unless a later guarded design passes live validation. |
| Villager | structured_bow_guarded_live | global_configuration | E | statistically supported harmful | Do not activate structured plus BoW live voting under current evidence. |
| Villager | selective_bow_vote_override_live | global_configuration | D | no supported improvement | Diagnostic only; do not treat as current default. |
| Seer | random_or_diversified_checking_reference | strategy_level_game_outcome | B | retain reference/default | Use random or diversified checking as the current seer-search reference. |
| Seer | edge_first | strategy_level_game_outcome | D | no supported improvement | Do not revive edge-seat checking folklore after role randomization. |
| Seer | alternate_sides | strategy_level_game_outcome | C | promising but uncertain | Treat side alternation as a candidate for future validation, not a default. |
| Seer | right_to_left | strategy_level_game_outcome | C | promising but uncertain | Treat directional search as exploratory until a targeted matched test confirms it. |
| Seer | highest_p_wolf | strategy_level_game_outcome | E | not recommended | Do not use highest p_wolf as the current seer check rule. |
| Seer | highest_suspicion | actor_specific | E | not recommended | Do not use highest suspicion as the current seer check rule. |
| Seer | early_wolf_discovery_signal | post_outcome_association | B | conditionally recommended | Prioritize earlier wolf discovery as a search objective, but report the premium as associative. |
| Witch | witch_conservative_poison | actor_specific | C | promising but uncertain | Conditionally prefer conservative poison over indiscriminate poison; keep as uncertain. |
| Witch | joint_save_poison_policy | insufficient_data | U | requires targeted experiment | Do not claim a full Witch policy recommendation beyond conservative poison uncertainty. |
| Hunter | hunter_actor_specific_shot_policy | insufficient_data | U | insufficient data | No Hunter shot policy is recommended under current evidence. |
| Werewolf | existing_rule_night_kill_reference | reference_policy | B | retain reference/default | Retain existing night-kill rule as the current Werewolf reference. |
| Werewolf | wolf_random_kill | actor_specific | E | statistically supported harmful | Do not use random night kills as the Werewolf default. |
| Werewolf | continuous_frozen_ml | live_policy | E | not recommended | Retain ML for diagnostics only; do not deploy continuous frozen ML. |
| Werewolf | frozen_hybrid_50_50 | live_policy | E | statistically supported harmful | Do not recommend frozen hybrid ML policy. |
| Werewolf | ml_first_kill_only | live_policy | C | promising but uncertain | Treat as a future candidate only. |
| Werewolf | selective_ml_override | live_policy | D | no supported improvement | Diagnostic only under current evidence. |
| Werewolf | adaptive_deception_with_credibility_costs | strategy_level_game_outcome | C | conditionally recommended | Use as a controlled deception model, not as a final Werewolf optimization claim. |
| Werewolf | false_role_claim | strategy_level_game_outcome | E | not recommended | Do not recommend false role claim as a Werewolf deception subtype. |

        ## 7. Villager Synthesis

        Villager evidence supports retaining structured speech and belief/trust
        voting as the current reference. R5.1 found that `villager_random_vote`
        had no supported payoff improvement against the reference mix. R3 showed
        live guarded BoW overrides were harmful, while selective BoW override was
        near neutral and unsupported. Villager strategy comparison remains sparse
        because most speech and trust mechanisms are global discussion settings,
        not isolated Villager-owned voting policies.

        ## 8. Seer Synthesis

        Seer evidence rejects strong edge-seat folklore after role randomization
        and seat-order-neutral validation. Random or diversified search remains
        the current reference. Structured search found descriptive promise for
        side alternation and right-to-left search, but they are not final
        recommendations. Highest `p_wolf` and highest-suspicion search rules are
        not recommended because they performed poorly in structured search, and
        R5.1 found no actor-specific payoff improvement for highest suspicion.
        Useful information and wolf-found premiums are strong descriptive
        associations, but reveal timing remains unresolved.

        ## 9. Witch Synthesis

        Witch evidence gives only a cautious signal for conservative poison.
        R5.1 reports a small positive mean payoff difference for
        `witch_conservative_poison`, but the confidence interval crosses no
        effect. The full joint antidote/poison timing policy remains unresolved.

        ## 10. Hunter Synthesis

        Hunter has insufficient compatible actor-specific strategy data. R5
        role-level metrics show high downside and tail risk, but R5.1 does not
        support a Hunter-owned policy recommendation. No Hunter shot policy is
        recommended under current evidence.

        ## 11. Werewolf Synthesis

        Werewolf evidence supports retaining the existing night-kill reference.
        R5.1 shows `wolf_random_kill` is statistically harmful relative to the
        reference mix. Stage 2A/2B show frozen continuous ML and hybrid ML do not
        beat existing rule in live complete games; ML remains diagnostic only.
        Stage 3 deception diagnostics show deception is behaviorally important,
        but subtype value is not yet formally settled after credibility costs.

        ## 12. Multi-Criteria Decision Matrix

        R6 evaluates expected payoff, risk-adjusted payoff, downside risk, win
        probability, information value, exposure risk, seed robustness, regime
        robustness, current default status, and data sufficiency. The matrix is
        exported as `r6_role_strategy_decision_matrix.csv`.

        ## 13. Actor-Specific versus Externality Evidence

        Actor-specific recommendations are limited to strategy rows where the
        strategy owner is the affected role. Cross-role externalities are retained
        separately and must not be reported as role-owned strategy value.

        | Owner | Strategy | Affected Role | Mean Diff | Holm p |
| --- | --- | --- | --- | --- |
| seer | seer_highest_suspicion | hunter | -0.03900000000000001 | 1.0 |
| villager | villager_random_vote | hunter | -0.01050000000000001 | 1.0 |
| werewolf | wolf_random_kill | hunter | 0.466 | 3.066648565835738e-06 |
| witch | witch_conservative_poison | hunter | 0.115625 | 0.6537994238095228 |
| villager | villager_random_vote | seer | -0.151875 | 0.12413091978459705 |
| werewolf | wolf_random_kill | seer | 0.5071249999999999 | 9.701682772759487e-08 |
| witch | witch_conservative_poison | seer | 0.13125 | 0.12413091978459705 |
| seer | seer_highest_suspicion | villager | -0.04178125 | 0.22255820381407831 |
| werewolf | wolf_random_kill | villager | 0.34431249999999997 | 2.154728687833197e-22 |
| witch | witch_conservative_poison | villager | 0.061875000000000006 | 0.1675870561331836 |
| seer | seer_highest_suspicion | werewolf | 0.05591666666666666 | 0.44786662862101895 |
| villager | villager_random_vote | werewolf | 0.08141666666666666 | 0.44786662862101895 |

        ## 14. Cross-Stage Contradiction Audit

        | ID | Topic | Priority Source | Resolution |
| --- | --- | --- | --- |
| R6-X01 | BoW prediction versus live policy value | R3 matched live policy outcomes | BoW remains diagnostic; live integration is not recommended under current evidence. |
| R6-X02 | Frozen ML shadow value versus live wolf-kill value | Stage 2A/2B complete live policy contrasts | Frozen ML is diagnostic only; current night-kill rule remains reference. |
| R6-X03 | R5 strategy frontier versus actor-specific strategy ownership | R5.1 actor-specific attribution audit | Use R5 role metrics and R5.1 actor-specific/frontier outputs for recommendations. |
| R6-X04 | Edge-seat folklore versus randomized-role position tests | randomized-role and seat-order-neutral analyses | Do not recommend edge-first checking as a role-position rule. |
| R6-X05 | Wolf manipulation premium versus causal strategy value | R5.1 relabelled descriptive premium with imbalance warning | Treat manipulation premium as descriptive motivation for targeted deception experiments. |
| R6-X06 | Useful-information premium versus seer policy recommendation | R5.1 premium labels plus structured search policy tests | Prioritize information discovery as a goal but do not infer a final reveal/check policy. |

        ## 15. Strategy Rejection Registry

        | Role | Strategy | Reason | Grade | Label |
| --- | --- | --- | --- | --- |
| Werewolf | wolf_random_kill | statistically supported harm | E | statistically supported harmful |
| Werewolf | continuous_frozen_ml | live-policy failure | E | not recommended |
| Werewolf | frozen_hybrid_50_50 | statistically supported harm | E | statistically supported harmful |
| Villager | guarded_bow_010_live | live guarded BoW integration harmful | E | statistically supported harmful |
| Villager | structured_bow_guarded_live | structured plus BoW live integration harmful | E | statistically supported harmful |
| Seer | highest_suspicion | no supported improvement and structured-search harm | E | not recommended |
| Seer | highest_p_wolf | structured-search harm | E | not recommended |
| Seer | edge_first | engine artifact / position folklore not supported after randomization | D | no supported improvement |
| Werewolf | false_role_claim | deception subtype harmful in diagnostics | E | not recommended |

        ## 16. Current Default Registry

        | Role | Current Default | Grade | Confidence | Known Limitations |
| --- | --- | --- | --- | --- |
| Villager | structured speech plus belief/trust-aware voting reference | B | moderate | Villager-owned structured voting policies remain sparse. |
| Seer | random or diversified checking reference | B | moderate | reveal timing remains unresolved. |
| Witch | conservative poison as uncertain candidate; retain current potion safeguards | C | low | joint save and poison timing not isolated. |
| Hunter | no new recommendation | U | insufficient | role-level tail risk is high, but strategy attribution is missing. |
| Werewolf | existing night-kill rule plus credibility-constrained deception diagnostics | B | moderate | aggression versus deep-cover deception is unresolved. |

        ## 17. Remaining Evidence Gaps

        | Gap | Role | Question | Priority | Blocks Final Report |
| --- | --- | --- | --- | --- |
| R6-G01 | Hunter | Which Hunter shooting policy improves payoff without worsening tail risk? | critical | Yes, if final report requires role-specific Hunter recommendation |
| R6-G02 | Seer | When should the Seer reveal useful check information? | critical | Yes, if final report requires final Seer communication recommendation |
| R6-G03 | Witch | How should the Witch jointly manage antidote and poison timing? | critical | Yes, if final report requires full Witch policy recommendation |
| R6-G04 | Werewolf | Should wolves prefer aggression or deep-cover deception under credibility costs? | high | No, if reported as an explicit limitation |
| R6-G05 | Villager | Which structured voting rule should villagers use after speech and trust updates? | high | No, if current reference is retained with limitations |

        ## 18. Targeted Experiment Priorities

        | Priority | Role | Conditions | Minimum Scale | Required Before Final Report |
| --- | --- | --- | --- | --- |
| R6-P01 | Hunter | Hunter random shot vs no-shot vs suspicion-shot vs conservative-shot | 500 games per condition across at least 5 seeds | Yes, if final report requires role-specific Hunter recommendation |
| R6-P02 | Seer | private-only vs immediate reveal vs threshold reveal vs delayed reveal | 500 games per condition across at least 5 seeds | Yes, if final report requires final Seer communication recommendation |
| R6-P03 | Witch | factorial save probability x poison threshold policy test | 500 games per condition across at least 5 seeds | Yes, if final report requires full Witch policy recommendation |
| R6-P04 | Werewolf | adaptive, false-accuse, deflection, trust-building, low-profile controls | 500 games per condition across at least 5 seeds | No, if reported as an explicit limitation |
| R6-P05 | Villager | suspicion-only, p_wolf-only, trust-weighted, herding-guarded, conservative vote policies | 500 games per condition across at least 5 seeds | No, if current reference is retained with limitations |

        ## 19. Validation Summary

        | Check | Passed | Detail |
| --- | --- | --- |
| r4_payoff_manifest_unchanged | True | eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd |
| r5_metric_manifest_unchanged | True | 4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf |
| r51_attribution_preserved | True | valid actor-specific pairs=4 |
| r6_synthesis_only | True | R6 code reads historical outputs and does not import gameplay policy modules. |
| every_recommendation_has_source | True | 23 |
| every_recommendation_has_evidence_grade | True | 23 |
| every_recommendation_has_valid_label | True | 23 |
| every_role_has_default | True | 5 |
| hunter_not_recommended_without_data | True | Hunter rows checked |
| wolf_random_kill_not_labelled_optimal | True | wolf_random_kill rows checked |
| continuous_frozen_ml_not_recommended | True | continuous_frozen_ml rows checked |
| harmful_bow_live_not_recommended | True | R3 BoW live rows checked |
| highest_suspicion_not_supported | True | highest_suspicion checked |
| edge_folklore_not_revived | True | edge_first checked |
| actor_specific_externality_separated | True | decision matrix uses externality matrix separately |
| sources_exist | True | 25 |
| remaining_gaps_identify_required_experiment | True | 5 |
| confidence_levels_valid | True | 5 |

        ## 20. R6 Conclusion and Next Stage

        R6 documents evidence status for every role and removes unsupported
        strategy ownership claims. Negative findings are preserved: live BoW
        overrides are not recommended, continuous frozen ML is not recommended,
        wolf random kill is statistically harmful, highest-suspicion Seer checking
        is not supported, and Hunter remains data-insufficient. Final reporting can
        proceed only with explicit sparse-strategy limitations. Because several
        proposal-relevant role strategy gaps remain, the exact next stage is
        R6.1 - Targeted Missing Strategy Experiments.
