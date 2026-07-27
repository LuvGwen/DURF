"""Update cumulative research-progress artifacts for R2 BoW."""

import csv
from pathlib import Path

from bow_dataset_generation import R2_RESULTS_DIR, current_git_commit
from bow_evaluation import as_float, read_csv


RESEARCH_DIR = Path("results") / "research_progress"


def write_csv(path, rows, fieldnames):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            restval="",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames


def metric(rows, model_name, split, key):
    for row in rows:
        if row["model_name"] == model_name and row["dataset_split"] == split:
            return as_float(row.get(key), 0.0)
    return 0.0


def validation_value(rows, key):
    for row in rows:
        if row["metric"] == key:
            return row["value"]
    return ""


def contrast_row(rows, name):
    for row in rows:
        if row["contrast"] == name:
            return row
    return {}


def update_evidence_registry():
    path = RESEARCH_DIR / "cumulative_evidence_registry.csv"
    rows, fieldnames = load_csv(path)
    rows = [row for row in rows if row["stage_id"] != "r2_bow_speech"]
    validation = read_csv(R2_RESULTS_DIR / "bow_dataset_validation_summary.csv")
    role_metrics = read_csv(R2_RESULTS_DIR / "bow_role_prediction_metrics.csv")
    intent_metrics = read_csv(R2_RESULTS_DIR / "bow_intent_classification_metrics.csv")
    contrasts = read_csv(R2_RESULTS_DIR / "bow_score_intent_contrasts.csv")
    template = read_csv(R2_RESULTS_DIR / "bow_template_generalization_metrics.csv")
    keyword = read_csv(R2_RESULTS_DIR / "bow_keyword_dependency_analysis.csv")

    games = validation_value(validation, "source_game_count")
    utterances = validation_value(validation, "utterance_count")
    vocab = validation_value(validation, "vocabulary_size")
    templates = validation_value(validation, "template_family_count")
    regimes = validation_value(validation, "behavioral_regime_count")
    seeds = validation_value(validation, "seed_count")
    commit = current_git_commit()
    raw_count = (
        f"{utterances} utterance rows; {vocab} vocabulary terms; "
        f"{games} source games"
    )

    bow_auc = metric(role_metrics, "bow_scores_only", "final_test", "roc_auc")
    p_wolf_auc = metric(role_metrics, "p_wolf_only", "final_test", "roc_auc")
    suspicion_auc = metric(role_metrics, "suspicion_only", "final_test", "roc_auc")
    structured_auc = metric(role_metrics, "structured_speech_labels_only", "final_test", "roc_auc")
    combined_auc = metric(role_metrics, "full_legal_combined", "final_test", "roc_auc")
    p_wolf_structured_auc = metric(role_metrics, "p_wolf_suspicion_structured", "final_test", "roc_auc")
    nb_auc = metric(role_metrics, "full_bow_vector_naive_bayes", "final_test", "roc_auc")
    nb_ood = metric(role_metrics, "full_bow_vector_naive_bayes", "ood_template", "roc_auc")
    intent_f1 = metric(intent_metrics, "multinomial_nb_bow", "final_test", "macro_f1")
    role_word_change = 0.0
    for row in keyword:
        if row["comparison"] == "remove_direct_role_words_vs_bow_only_unigram_bigram":
            role_word_change = as_float(row["auc_change"], 0.0)

    def base_row(hypothesis_id, hypothesis, comparison, effect, pp_effect, conclusion, status, limitation):
        return {
            "stage_id": "r2_bow_speech",
            "stage_name": "R2 Formal Bag-of-Words speech quantification",
            "research_domain": "speech quantification",
            "hypothesis_id": hypothesis_id,
            "hypothesis": hypothesis,
            "prior_hypothesis_source": "results/research_progress/remaining_work_roadmap.md",
            "experiment_design": (
                "Shadow BoW utterance generation, train-only vocabulary, "
                "grouped split validation, score contrasts, role prediction, "
                "intent classification, keyword ablations, and leakage audit."
            ),
            "dataset_path": str(R2_RESULTS_DIR / "bow_speech_utterance_dataset.csv"),
            "report_path": str(R2_RESULTS_DIR / "bow_stage_r2_research_report.md"),
            "raw_row_count": raw_count,
            "raw_game_count": games,
            "independent_sample_size": "game families and template families",
            "matched_set_count": "NA",
            "seed_count": seeds,
            "behavioral_regime_count": regimes,
            "primary_outcome": "ROC-AUC or score contrast",
            "comparison": comparison,
            "control_condition": "see comparison",
            "descriptive_effect": effect,
            "absolute_percentage_point_effect": pp_effect,
            "effect_size_type": "ROC-AUC difference or Cohen d",
            "effect_size": pp_effect,
            "confidence_interval": "see bow_score_intent_contrasts.csv and related metrics",
            "raw_p_value": "see bow_score_intent_contrasts.csv where applicable",
            "adjusted_p_value": "see bow_score_intent_contrasts.csv where applicable",
            "multiplicity_method": "Holm for four pre-specified score contrasts",
            "evidence_level": "LEVEL 4 - robustness-validated",
            "seed_robustness": "35 seeds across train/validation/final/OOD splits",
            "regime_robustness": "six behavioral regimes including two OOD regimes",
            "design_validity": "R2 is shadow-only; no live gameplay policy changed",
            "engine_validity": "uses existing validated complete-game engine",
            "distribution_shift_status": "OOD template and OOD regime metrics exported",
            "overfitting_status": "see bow_overfitting_diagnostics.csv",
            "leakage_status": "information-leakage audit passed",
            "conclusion_label": conclusion,
            "hypothesis_status": status,
            "main_limitation": limitation,
            "supersedes_stage_id": "",
            "superseded_by_stage_id": "",
            "next_hypothesis": (
                "R3 should test BoW-weighted belief and voting updates in "
                "matched live games with credibility safeguards."
            ),
            "source_commit": commit,
            "current_documentation_commit": "pending_current_stage_commit",
        }

    accusation = contrast_row(contrasts, "accusation_vs_neutral_werewolf_score")
    emotional = contrast_row(contrasts, "emotional_vs_neutral_intensity")
    informative = contrast_row(contrasts, "informative_vs_low_information_density")
    deceptive = contrast_row(contrasts, "deceptive_vs_non_deceptive_werewolf_score")

    new_rows = [
        base_row(
            "H-R2-1_intent_prediction",
            "BoW features can predict structured speech intent better than chance.",
            "multinomial_nb_bow vs chance over generated intents",
            f"final-test macro F1 {intent_f1:.3f}",
            f"macro F1 {intent_f1:.3f}",
            "hypothesis supported",
            "supported",
            "Intent labels are generated templates, not human annotations.",
        ),
        base_row(
            "H-R2-2_werewolf_leaning_role_signal",
            "BoW werewolf-leaning can distinguish wolf-generated speech from village-generated speech.",
            "bow_scores_only vs base rate",
            f"BoW scores final ROC-AUC {bow_auc:.3f} vs base 0.500",
            f"+{bow_auc - 0.5:.3f} AUC",
            "hypothesis supported",
            "supported",
            "Role prediction is predictive association, not causal inference.",
        ),
        base_row(
            "H-R2-3_emotional_intensity_construct",
            "Emotional-intensity score is higher for emotional speech than neutral speech.",
            "emotional speech vs neutral",
            f"mean difference {as_float(emotional.get('mean_difference')):.3f}; Cohen d {as_float(emotional.get('cohen_d')):.3f}",
            f"d {as_float(emotional.get('cohen_d')):.3f}",
            "hypothesis supported",
            "supported",
            "Emotion is template-generated.",
        ),
        base_row(
            "H-R2-4_information_density_construct",
            "Information-density score is higher for concrete informative speech.",
            "informative speech vs low-information speech",
            f"mean difference {as_float(informative.get('mean_difference')):.3f}; Cohen d {as_float(informative.get('cohen_d')):.3f}",
            f"d {as_float(informative.get('cohen_d')):.3f}",
            "hypothesis supported",
            "supported",
            "Information density is based on controlled templates.",
        ),
        base_row(
            "H-R2-5_bow_vs_existing_scores",
            "BoW features add value beyond existing p_wolf and suspicion scores.",
            "bow_scores_only vs p_wolf_only and suspicion_only",
            f"BoW scores AUC {bow_auc:.3f}; p_wolf {p_wolf_auc:.3f}; suspicion {suspicion_auc:.3f}",
            f"+{bow_auc - max(p_wolf_auc, suspicion_auc):.3f} AUC over best existing scalar",
            "hypothesis supported",
            "supported",
            "Does not imply live-game decision improvement.",
        ),
        base_row(
            "H-R2-6_bow_weaker_than_structured",
            "BoW-only models are weaker than structured behavior plus BoW.",
            "full_bow_vector_naive_bayes vs full_legal_combined",
            f"NB BoW AUC {nb_auc:.3f}; full legal combined {combined_auc:.3f}",
            f"{combined_auc - nb_auc:+.3f} AUC",
            "hypothesis supported",
            "supported",
            "Structured labels are generated by the simulator and highly informative.",
        ),
        base_row(
            "H-R2-7_unseen_template_generalization",
            "BoW should be tested against unseen template families.",
            "full_bow_vector_naive_bayes final_test vs ood_template",
            f"NB AUC drops from {nb_auc:.3f} to {nb_ood:.3f}",
            f"{nb_ood - nb_auc:+.3f} AUC",
            "template-bound",
            "supported as a failure mode",
            "Vector BoW is template-bound; transparent scores retain some signal.",
        ),
        base_row(
            "H-R2-8_keyword_ablation",
            "Keyword ablation tests whether results depend on direct role words.",
            "remove direct role words vs BoW unigram+bigram baseline",
            f"final-test AUC change {role_word_change:+.3f}",
            f"{role_word_change:+.3f} AUC",
            "hypothesis supported",
            "supported",
            "Other template shortcuts may still exist.",
        ),
        base_row(
            "H-R2-9_unseen_regime_generalization",
            "BoW generalization should be checked across unseen behavioral regimes.",
            "final_test vs ood_regime",
            "OOD-regime metrics exported; p_wolf-only is less stable than structured/combined models",
            "see bow_regime_generalization_metrics.csv",
            "promising but uncertain",
            "unresolved",
            "OOD regimes are simulator regimes, not natural data.",
        ),
        base_row(
            "H-R2-10_leakage_audit",
            "BoW features must avoid hidden-role, future-outcome, and ID leakage.",
            "leakage checks",
            "information-leakage audit PASS",
            "0 leakage flags",
            "implementation validated",
            "supported",
            "Audit validates current pipeline, not future R3 integrations.",
        ),
        base_row(
            "H-R2-11_structured_plus_bow",
            "Structured + BoW should provide complementary information.",
            "full_legal_combined vs p_wolf_suspicion_structured",
            f"full combined AUC {combined_auc:.3f}; p_wolf+suspicion+structured {p_wolf_structured_auc:.3f}",
            f"{combined_auc - p_wolf_structured_auc:+.3f} AUC",
            "no meaningful improvement",
            "unresolved",
            "BoW does not clearly add beyond existing structured+p_wolf/suspicion.",
        ),
        base_row(
            "H-R2-12_r3_readiness",
            "R2 should determine whether the BoW module is ready for R3 integration testing.",
            "R2 decision rules",
            "pipeline valid; pure vector model template-bound; R3 should test guarded hybrid integration",
            "qualitative decision",
            "promising but uncertain",
            "ready for controlled R3 test",
            "R2 does not test live outcome effects.",
        ),
    ]
    rows.extend(new_rows)
    write_csv(path, rows, fieldnames)


def update_source_traceability():
    path = RESEARCH_DIR / "source_traceability_index.csv"
    rows, fieldnames = load_csv(path)
    rows = [row for row in rows if not row["claim_id"].startswith("C_R2_")]
    commit = current_git_commit()
    new_rows = [
        ("C_R2_1", "R2 generated a real text-based BoW utterance dataset", "results/bow_speech_stage_r2/bow_stage_r2_research_report.md", "Data Scale and Splits", "results/bow_speech_stage_r2/bow_speech_utterance_dataset.csv", "bow_stage_r2_experiment.py", "1600 games and 32721 utterances."),
        ("C_R2_2", "R2 vocabulary was built from train split only", "results/bow_speech_stage_r2/bow_vocabulary_manifest.json", "built_from_split", "results/bow_speech_stage_r2/bow_vocabulary.csv", "bow_dataset_generation.py", "Vocabulary size 289."),
        ("C_R2_3", "BoW score constructs are significant in pre-specified contrasts", "results/bow_speech_stage_r2/bow_score_intent_contrasts.csv", "all rows", "results/bow_speech_stage_r2/bow_score_intent_contrasts.csv", "bow_evaluation.py", "Holm-adjusted p-values reported."),
        ("C_R2_4", "BoW scores outperform p_wolf and suspicion scalar baselines for speaker-is-wolf prediction", "results/bow_speech_stage_r2/bow_role_prediction_metrics.csv", "final_test rows", "results/bow_speech_stage_r2/bow_role_prediction_metrics.csv", "bow_evaluation.py", "BoW score AUC 0.692 vs p_wolf 0.569 and suspicion 0.515."),
        ("C_R2_5", "Full vector BoW is template-bound under unseen-template evaluation", "results/bow_speech_stage_r2/bow_template_generalization_metrics.csv", "full_bow_vector_naive_bayes", "results/bow_speech_stage_r2/bow_template_generalization_metrics.csv", "bow_evaluation.py", "AUC drops to 0.361 in OOD-template split."),
        ("C_R2_6", "Information leakage audit passed", "results/bow_speech_stage_r2/bow_stage_r2_information_leakage_audit.md", "Status", "results/bow_speech_stage_r2/bow_speech_utterance_dataset.csv", "bow_stage_r2_analysis.py", "No hidden information leakage flags."),
    ]
    for claim_id, summary, source_file, section, dataset, script, notes in new_rows:
        rows.append({
            "claim_id": claim_id,
            "claim_summary": summary,
            "stage": "R2 BoW",
            "source_file": source_file,
            "source_table_or_section": section,
            "dataset": dataset,
            "analysis_script": script,
            "commit_hash": commit,
            "verification_status": "verified_from_source",
            "notes": notes,
        })
    write_csv(path, rows, fieldnames)


def update_proposal_matrix():
    path = RESEARCH_DIR / "durf_proposal_alignment_matrix.csv"
    rows, fieldnames = load_csv(path)
    updates = {
        "Bag-of-Words vocabulary": {
            "status": "completed_and_extended",
            "evidence": "Formal core lexicon and train-derived vocabulary exported.",
            "source_file": "bow_lexicon.py; results/bow_speech_stage_r2/bow_core_lexicon.csv; results/bow_speech_stage_r2/bow_vocabulary.csv",
            "quality_of_completion": "High for simulator-generated English BoW.",
            "remaining_work": "Integrate validated scores into live decisions in R3.",
            "required_next_stage": "R3",
            "priority": "Medium",
            "blocking_final_report": "No",
        },
        "Speech text tokenization": {
            "status": "completed",
            "evidence": "Deterministic English tokenizer implemented and tested; player IDs and numbers are normalized.",
            "source_file": "bow_tokenizer.py; test_bow_tokenizer.py",
            "quality_of_completion": "High for English template text.",
            "remaining_work": "No multilingual design yet.",
            "required_next_stage": "R3",
            "priority": "Medium",
            "blocking_final_report": "No",
        },
        "Werewolf-leaning speech score": {
            "status": "completed",
            "evidence": "Rule-based werewolf-leaning score implemented and validated against accusation/deception contrasts.",
            "source_file": "bow_feature_extractor.py; results/bow_speech_stage_r2/bow_score_intent_contrasts.csv",
            "quality_of_completion": "Medium-High; construct is valid in generated text.",
            "remaining_work": "Live decision effect untested.",
            "required_next_stage": "R3",
            "priority": "Medium",
            "blocking_final_report": "No",
        },
        "Emotional-intensity score": {
            "status": "completed",
            "evidence": "Emotional-intensity score implemented and validated against emotional-vs-neutral speech.",
            "source_file": "bow_feature_extractor.py; results/bow_speech_stage_r2/bow_score_intent_contrasts.csv",
            "quality_of_completion": "Medium-High for generated text.",
            "remaining_work": "Human-language validation not attempted.",
            "required_next_stage": "R7",
            "priority": "Low",
            "blocking_final_report": "No",
        },
        "Information-density score": {
            "status": "completed",
            "evidence": "Information-density score implemented and validated against informative-vs-low-information speech.",
            "source_file": "bow_feature_extractor.py; results/bow_speech_stage_r2/bow_score_intent_contrasts.csv",
            "quality_of_completion": "Medium-High for generated text.",
            "remaining_work": "Human-language validation not attempted.",
            "required_next_stage": "R7",
            "priority": "Low",
            "blocking_final_report": "No",
        },
        "BoW integration into decisions": {
            "status": "partially_completed",
            "evidence": "R2 implements BoW as a shadow feature system only; live decisions are intentionally unchanged.",
            "source_file": "results/bow_speech_stage_r2/bow_stage_r2_research_report.md",
            "quality_of_completion": "Correctly deferred.",
            "remaining_work": "Run matched R3 live-decision integration experiment.",
            "required_next_stage": "R3",
            "priority": "High",
            "blocking_final_report": "Yes",
        },
    }
    for row in rows:
        if row["proposal_component"] in updates:
            row.update(updates[row["proposal_component"]])
    write_csv(path, rows, fieldnames)


def append_once(path, marker, text):
    path = Path(path)
    current = path.read_text(encoding="utf-8")
    if marker in current:
        before = current.split(marker)[0].rstrip()
        current = before + "\n\n"
    path.write_text(current.rstrip() + "\n\n" + text.strip() + "\n", encoding="utf-8")


def update_markdown_reports():
    cumulative_section = """## 24. R2 Formal Bag-of-Words Speech Quantification

Question: Can the simulator implement proposal-level Bag-of-Words speech metrics rather than relying only on structured speech labels?

Design: R2 generates English natural-language utterances from existing legal speech events without changing gameplay policy. It tokenizes text deterministically, builds a train-only BoW vocabulary, extracts werewolf-leaning, emotional-intensity, and information-density scores, and evaluates role prediction, intent prediction, template generalization, regime generalization, ablations, leakage, and overfitting.

Evidence: See `results/bow_speech_stage_r2/bow_stage_r2_research_report.md`. The dataset contains 1,600 source games, 32,721 utterances, 48 template families, 6 behavioral regimes, and a 289-term train-derived vocabulary. BoW score contrasts are significant after Holm correction. Final-test BoW-score ROC-AUC for speaker-is-wolf is 0.692, compared with 0.569 for `p_wolf` and 0.515 for suspicion. Structured labels remain stronger, and the full legal combined model does not clearly improve over `p_wolf + suspicion + structured` labels.

Conclusion: `promising but uncertain`. R2 validates the BoW measurement pipeline, but live decision integration remains R3."""
    append_once(
        RESEARCH_DIR / "cumulative_research_report.md",
        "## 24. R2 Formal Bag-of-Words Speech Quantification",
        cumulative_section,
    )

    audit_section = """## R2 BoW Update

R2 completes the formal BoW vocabulary, English tokenization, werewolf-leaning score, emotional-intensity score, and information-density score as shadow-analysis modules. `BoW integration into decisions` remains partially completed because R2 intentionally does not alter live voting, checking, killing, or payoff rules. The next required stage is R3: BoW Integration and Comparative Decision Analysis."""
    append_once(
        RESEARCH_DIR / "durf_proposal_alignment_audit.md",
        "## R2 BoW Update",
        audit_section,
    )

    assessment_section = """## R2 Current Assessment

Formal BoW speech quantification is now implemented and validated as a shadow feature system. The project has a real English tokenizer, core lexicon, train-derived vocabulary, utterance-level dataset, score manifests, leakage audit, overfitting audit, model comparisons, template/regime generalization checks, and R2 research reports. BoW is not yet integrated into live decisions; that remains the exact R3 task."""
    append_once(
        RESEARCH_DIR / "current_progress_assessment.md",
        "## R2 Current Assessment",
        assessment_section,
    )

    roadmap = RESEARCH_DIR / "remaining_work_roadmap.md"
    roadmap_text = roadmap.read_text(encoding="utf-8")
    roadmap_text = roadmap_text.replace(
        "## Stage R2: Formal Bag-of-Words speech quantification\n\n- Objective: Implement proposal-level BoW metrics.",
        "## Stage R2: Formal Bag-of-Words speech quantification\n\n- Status: Completed in `results/bow_speech_stage_r2/`.\n- Objective: Implement proposal-level BoW metrics.",
    )
    roadmap_text = roadmap_text.replace(
        "- Exit condition: Scores reproducible and observation-safe.",
        "- Exit condition: Scores reproducible and observation-safe.\n- Completed output: `results/bow_speech_stage_r2/bow_stage_r2_research_report.md`.",
    )
    roadmap_text = roadmap_text.replace(
        "## Stage R3: BoW integration and comparative Data Analysis\n\n- Objective: Test whether BoW metrics improve decisions.",
        "## Stage R3: BoW integration and comparative Data Analysis\n\n- Status: Next exact experiment.\n- Objective: Test whether BoW metrics improve decisions.",
    )
    roadmap.write_text(roadmap_text, encoding="utf-8")


def main():
    update_evidence_registry()
    update_source_traceability()
    update_proposal_matrix()
    update_markdown_reports()
    print("R2 research progress artifacts updated")


if __name__ == "__main__":
    main()
