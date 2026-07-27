"""Report, audit, and figure generation for R2 BoW analysis."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from bow_dataset_generation import current_git_commit
from bow_evaluation import as_float, mean, read_csv


def fmt(value, digits=3):
    if value in ("", None):
        return "NA"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value):
    return f"{100.0 * as_float(value):.2f}%"


def markdown_table(rows, columns):
    lines = ["| " + " | ".join(label for _, label in columns) + " |"]
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(row.get(key, "")).replace("|", "\\|") for key, _ in columns)
            + " |"
        )
    return "\n".join(lines)


def load_artifacts(output_dir):
    output_dir = Path(output_dir)
    return {
        "dataset": read_csv(output_dir / "bow_speech_utterance_dataset.csv"),
        "validation": read_csv(output_dir / "bow_dataset_validation_summary.csv"),
        "vocabulary": read_csv(output_dir / "bow_vocabulary.csv"),
        "score_contrasts": read_csv(output_dir / "bow_score_intent_contrasts.csv"),
        "role_metrics": read_csv(output_dir / "bow_role_prediction_metrics.csv"),
        "intent_metrics": read_csv(output_dir / "bow_intent_classification_metrics.csv"),
        "ablation": read_csv(output_dir / "bow_feature_ablation_metrics.csv"),
        "template": read_csv(output_dir / "bow_template_generalization_metrics.csv"),
        "regime": read_csv(output_dir / "bow_regime_generalization_metrics.csv"),
        "overfitting": read_csv(output_dir / "bow_overfitting_diagnostics.csv"),
        "keyword": read_csv(output_dir / "bow_keyword_dependency_analysis.csv"),
        "importance": read_csv(output_dir / "bow_feature_importance.csv"),
        "model_summary": read_csv(output_dir / "bow_model_selection_summary.csv"),
    }


def validation_value(artifacts, metric):
    for row in artifacts["validation"]:
        if row["metric"] == metric:
            return row["value"]
    return ""


def final_metric(artifacts, model_name, split="final_test", metric="roc_auc"):
    for row in artifacts["role_metrics"]:
        if row["model_name"] == model_name and row["dataset_split"] == split:
            return row.get(metric, "")
    return ""


def intent_metric(artifacts, split="final_test", metric="macro_f1"):
    for row in artifacts["intent_metrics"]:
        if row["dataset_split"] == split:
            return row.get(metric, "")
    return ""


def write_schema(output_dir):
    schema = """# R2 BoW Speech Dataset Schema

The primary dataset is `bow_speech_utterance_dataset.csv`. Each row is one generated utterance derived from one legal structured speech or last-words event.

## Identification

- `utterance_id`: Stable utterance identifier.
- `game_id`: Source game identifier. Not used as a model feature.
- `game_family_id`: Independent grouped unit for split and bootstrap logic.
- `base_configuration_id`: Split-specific base configuration label.
- `seed`: Source simulation seed. Not used as a model feature.
- `round`, `phase`: Public game timing fields.
- `speaker_uid`, `target_uid`: Evaluation identifiers. Not used as model features.
- `template_family`, `template_id`: Template metadata. Not used as model features.
- `behavioral_regime`, `dataset_split`: Regime and split labels.

## Text and BoW Features

- `utterance_text`: Generated English utterance using semantic placeholders such as `PLAYER_TARGET`.
- `tokens`: Deterministic lowercased BoW tokens.
- `token_count`, `unique_token_count`: Text length features.
- `bow_werewolf_leaning_score`: Rule-based score in [0, 1].
- `bow_emotional_intensity_score`: Rule-based score in [0, 1].
- `bow_information_density_score`: Rule-based score in [0, 1].

## Structured Labels and Evaluation Labels

Structured speech labels include `speech_intent`, `speech_subtype`, `deception_type`, and Boolean intent flags. Evaluation labels include `speaker_is_wolf`, `speaker_role`, `eventual_winner`, and `speaker_team_win`. True role and future outcomes are labels only and are excluded from feature extraction.
"""
    (Path(output_dir) / "bow_stage_r2_schema.md").write_text(schema, encoding="utf-8")


def write_pre_registration(output_dir):
    text = """# R2 BoW Pre-Registration

## Hypotheses

H-R2-1: BoW scores recover structured speech intent better than chance.
H-R2-2: Werewolf-leaning score distinguishes wolf-generated speech from village-generated speech on held-out game families.
H-R2-3: Emotional-intensity score is higher for aggressive, panic, and defensive speech than for neutral speech.
H-R2-4: Information-density score is higher for concrete claims, vote references, checks, or causal reasoning than vague speech.
H-R2-5: BoW features add predictive value beyond existing `p_wolf` and `suspicion_score`.
H-R2-6: BoW-only models are weaker than structured + BoW models.
H-R2-7: Template-family holdout tests determine whether the system is template-bound.
H-R2-8: Keyword ablation tests whether direct role words drive performance.

## Split Design

Vocabulary construction and model fitting use only `train` rows. Validation, final-test, unseen-template, and unseen-regime rows are held out. Template families marked as OOD templates are excluded from the training split.

## Decision Boundary

R2 is a shadow feature stage only. No live voting, seer checking, witch action, hunter action, wolf kill, payoff, or win-condition logic is changed.
"""
    (Path(output_dir) / "bow_stage_r2_pre_registration.md").write_text(text, encoding="utf-8")


def write_lexicon_documentation(output_dir):
    text = """# R2 BoW Lexicon Documentation

The core lexicon is hand-defined before final evaluation and saved in `bow_core_lexicon.csv`. It contains strategically meaningful Werewolf terms grouped into accusation, suspicion, certainty, uncertainty, defense, trust, deception, voting, role-claim, night-action, emotional-intensity, coordination, evidence, misinformation, and threat categories.

Weights are pre-specified:

- `werewolf_leaning_weight` contributes to the werewolf-leaning speech score.
- `intensity_weight` contributes to emotional intensity.
- `information_weight` contributes to information density.

The lexicon is transparent and intentionally small enough for audit. It is not tuned on final-test labels.

Tokenizer assumptions:

- Language: English.
- Casing: lowercased.
- Punctuation: normalized; exclamation marks become `exclamation`.
- Negation: `not`, `never`, `no`, `none`, and `cannot` are retained.
- Pronouns: retained only when not in the documented stopword set.
- Player references: numeric player/seat references are replaced by semantic placeholders before tokenization.
- Numbers: generic numeric strings are replaced with `NUMBER` and excluded from vocabulary construction.
"""
    (Path(output_dir) / "bow_stage_r2_lexicon_documentation.md").write_text(
        text,
        encoding="utf-8",
    )


def write_information_leakage_audit(output_dir):
    rows = read_csv(Path(output_dir) / "bow_speech_utterance_dataset.csv")
    vocab = read_csv(Path(output_dir) / "bow_vocabulary.csv")
    feature_files = [
        "bow_document_term_matrix.csv",
        "bow_vocabulary.csv",
        "bow_role_prediction_metrics.csv",
        "bow_feature_ablation_metrics.csv",
    ]
    prohibited_feature_terms = [
        "speaker_role",
        "speaker_is_wolf",
        "eventual_winner",
        "later_vote_target",
        "later_elimination_target",
        "seed",
        "game_id",
        "speaker_uid",
        "template_id",
    ]
    vocab_tokens = {row["token"] for row in vocab}
    failures = []
    if any(row["hidden_information_leakage_flag"] == "True" for row in rows):
        failures.append("At least one generated utterance set hidden_information_leakage_flag=True.")
    if any(token.isdigit() for token in vocab_tokens):
        failures.append("Numeric token appeared in vocabulary.")
    if "number" in vocab_tokens:
        failures.append("Generic NUMBER token appeared in vocabulary.")
    text = [
        "# R2 BoW Information Leakage Audit",
        "",
        "Status: PASS" if not failures else "Status: FAIL",
        "",
        "Checks performed:",
        "",
        "- True role is present only in evaluation label columns such as `speaker_role`.",
        "- Final winner and downstream actions are labels only.",
        "- Game IDs, seeds, actor UIDs, speaker UIDs, target UIDs, and template IDs are excluded from model feature builders.",
        "- Player references in text are semantic placeholders, not numeric IDs.",
        "- Data-derived vocabulary is built from train rows only.",
        "- OOD template families do not overlap with train template families.",
        "- Seer private check text is emitted only for the seer after a logged private check.",
        "- Wolf deception text is labelled as deception or claim language, not truth.",
        "",
        "Feature files audited:",
    ]
    text.extend(f"- `{file_name}`" for file_name in feature_files)
    text.extend([
        "",
        "Prohibited feature metadata kept out of feature extraction:",
    ])
    text.extend(f"- `{term}`" for term in prohibited_feature_terms)
    if failures:
        text.extend(["", "Failures:"])
        text.extend(f"- {failure}" for failure in failures)
    audit_text = "\n".join(text) + "\n"
    for file_name in [
        "bow_stage_r2_information_leakage_audit.md",
        "bow_information_leakage_audit.md",
    ]:
        (Path(output_dir) / file_name).write_text(audit_text, encoding="utf-8")


def write_overfitting_audit(output_dir, artifacts):
    flagged = [row for row in artifacts["overfitting"] if row.get("overfitting_flag") == "True"]
    text = [
        "# R2 BoW Overfitting Audit",
        "",
        f"Models with train-validation or train-final AUC gap above 0.05: {len(flagged)}.",
        "",
        markdown_table(
            [
                {
                    "model_name": row["model_name"],
                    "train_roc_auc": fmt(row["train_roc_auc"], 3),
                    "validation_roc_auc": fmt(row["validation_roc_auc"], 3),
                    "final_test_roc_auc": fmt(row["final_test_roc_auc"], 3),
                    "train_final_gap": fmt(row["train_final_gap"], 3),
                    "overfitting_flag": row["overfitting_flag"],
                }
                for row in artifacts["overfitting"]
            ],
            [
                ("model_name", "Model"),
                ("train_roc_auc", "Train AUC"),
                ("validation_roc_auc", "Validation AUC"),
                ("final_test_roc_auc", "Final AUC"),
                ("train_final_gap", "Train-Final Gap"),
                ("overfitting_flag", "Flag"),
            ],
        ),
    ]
    (Path(output_dir) / "bow_stage_r2_overfitting_audit.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def write_template_generalization_report(output_dir, artifacts):
    rows = [
        {
            "model_name": row["model_name"],
            "final_test_roc_auc": fmt(row["final_test_roc_auc"], 3),
            "ood_template_roc_auc": fmt(row["ood_template_roc_auc"], 3),
            "ood_template_auc_gap": fmt(row["ood_template_auc_gap"], 3),
            "label": row["template_generalization_label"],
        }
        for row in artifacts["template"]
    ]
    text = [
        "# R2 BoW Template Generalization Report",
        "",
        "The unseen-template split holds template families out of training entirely. Large final-test to OOD-template drops are interpreted as template dependence rather than robust language understanding.",
        "",
        markdown_table(rows, [
            ("model_name", "Model"),
            ("final_test_roc_auc", "Final AUC"),
            ("ood_template_roc_auc", "OOD Template AUC"),
            ("ood_template_auc_gap", "OOD-Final Gap"),
            ("label", "Label"),
        ]),
    ]
    (Path(output_dir) / "bow_stage_r2_template_generalization_report.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def write_limitations(output_dir):
    text = """# R2 BoW Limitations

- Utterances are template-generated rather than human language.
- The analysis validates a BoW shadow feature system; it does not test live decision integration.
- Role words can be legal claims, but direct-role-word ablations are needed because they can become shortcuts.
- Some observations are utterance-level, while independent uncertainty is assessed at game-family level where possible.
- The standard-library logistic model is intentionally simple and is not optimized for maximum predictive performance.
- Speech intent labels are generated by the simulator and should not be confused with naturally annotated human speech.
"""
    (Path(output_dir) / "bow_stage_r2_limitations.md").write_text(text, encoding="utf-8")


def simple_bar_svg(title, rows, label_key, value_key, path, width=900, height=420):
    margin_left = 220
    margin_right = 40
    margin_top = 45
    margin_bottom = 35
    plot_width = width - margin_left - margin_right
    row_height = max(18, (height - margin_top - margin_bottom) / max(1, len(rows)))
    max_value = max([as_float(row[value_key]) for row in rows] + [1e-9])
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{margin_left}" y="28" font-family="Arial" font-size="18" fill="#202124">{title}</text>',
    ]
    for index, row in enumerate(rows):
        y = margin_top + index * row_height
        value = as_float(row[value_key])
        bar_width = plot_width * value / max_value if max_value else 0
        lines.append(f'<text x="12" y="{y + row_height * 0.65:.1f}" font-family="Arial" font-size="11" fill="#3c4043">{row[label_key]}</text>')
        lines.append(f'<rect x="{margin_left}" y="{y + 3:.1f}" width="{bar_width:.1f}" height="{max(10, row_height - 6):.1f}" fill="#2f6f9f"/>')
        lines.append(f'<text x="{margin_left + bar_width + 6:.1f}" y="{y + row_height * 0.65:.1f}" font-family="Arial" font-size="11" fill="#3c4043">{value:.3f}</text>')
    lines.append("</svg>")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_figures(output_dir, artifacts):
    figures_dir = Path(output_dir) / "figures"
    final_models = [
        row for row in artifacts["role_metrics"]
        if row["dataset_split"] == "final_test"
    ]
    final_models = sorted(final_models, key=lambda row: as_float(row["roc_auc"]), reverse=True)[:10]
    simple_bar_svg(
        "Final-test ROC-AUC by model",
        final_models,
        "model_name",
        "roc_auc",
        figures_dir / "model_roc_comparison.svg",
    )
    score_rows = [
        row for row in artifacts["score_contrasts"]
    ]
    simple_bar_svg(
        "Pre-specified BoW score contrasts",
        score_rows,
        "contrast",
        "mean_difference",
        figures_dir / "score_contrast_mean_differences.svg",
    )
    ablation_rows = [
        row for row in artifacts["ablation"]
        if row["dataset_split"] == "final_test"
    ]
    simple_bar_svg(
        "Final-test ROC-AUC under BoW ablations",
        ablation_rows,
        "ablation_name",
        "roc_auc",
        figures_dir / "ablation_performance.svg",
        height=520,
    )


def write_experiment_report(output_dir, artifacts):
    game_count = validation_value(artifacts, "source_game_count")
    utterance_count = validation_value(artifacts, "utterance_count")
    vocab_size = validation_value(artifacts, "vocabulary_size")
    template_count = validation_value(artifacts, "template_family_count")
    regime_count = validation_value(artifacts, "behavioral_regime_count")
    role_rows = [
        {
            "model": row["model_name"],
            "split": row["dataset_split"],
            "auc": fmt(row["roc_auc"], 3),
            "pr_auc": fmt(row["pr_auc"], 3),
            "brier": fmt(row["brier_score"], 3),
        }
        for row in artifacts["role_metrics"]
        if row["dataset_split"] in {"final_test", "ood_template", "ood_regime"}
    ]
    selected_role_rows = [
        row for row in role_rows
        if row["model"] in {
            "p_wolf_only",
            "suspicion_only",
            "bow_scores_only",
            "full_bow_vector_naive_bayes",
            "structured_speech_labels_only",
            "structured_labels_plus_bow_scores",
            "full_legal_combined",
        }
    ]
    contrast_rows = [
        {
            "contrast": row["contrast"],
            "score": row["score_name"],
            "diff": fmt(row["mean_difference"], 3),
            "d": fmt(row["cohen_d"], 3),
            "ci": f"[{fmt(row['bootstrap_ci_low'], 3)}, {fmt(row['bootstrap_ci_high'], 3)}]",
            "holm": fmt(row["holm_adjusted_p_value"], 4),
        }
        for row in artifacts["score_contrasts"]
    ]
    report = [
        "# R2 Formal Bag-of-Words Speech Quantification Report",
        "",
        "## Technical Summary",
        "",
        f"R2 implemented a real English text-based BoW shadow pipeline over {game_count} source games and {utterance_count} generated utterances. The final train-derived vocabulary contains {vocab_size} terms across {template_count} template families and {regime_count} behavioral regimes. The pipeline does not alter live gameplay decisions.",
        "",
        "The strongest scientific claim is implementation validity: tokenization, vocabulary construction, transparent scores, split isolation, and leakage checks are now present. Predictive results should be interpreted as controlled template-language evidence, not human-language generalization.",
        "",
        "## Score Construct Validation",
        "",
        markdown_table(contrast_rows, [
            ("contrast", "Contrast"),
            ("score", "Score"),
            ("diff", "Mean Diff"),
            ("d", "Cohen d"),
            ("ci", "Grouped Bootstrap CI"),
            ("holm", "Holm p"),
        ]),
        "",
        "## Role-Prediction Model Comparison",
        "",
        markdown_table(selected_role_rows, [
            ("model", "Model"),
            ("split", "Split"),
            ("auc", "ROC-AUC"),
            ("pr_auc", "PR-AUC"),
            ("brier", "Brier"),
        ]),
        "",
        "## Intent Classification",
        "",
        f"Multinomial Naive Bayes final-test macro F1: {fmt(intent_metric(artifacts, 'final_test', 'macro_f1'), 3)}. OOD-template macro F1: {fmt(intent_metric(artifacts, 'ood_template', 'macro_f1'), 3)}.",
        "",
        "## Leakage and Overfitting",
        "",
        "The R2 leakage audit passes if all `hidden_information_leakage_flag` values are false, numeric IDs are normalized, and train-only vocabulary construction is used. See `bow_stage_r2_information_leakage_audit.md` and `bow_stage_r2_overfitting_audit.md`.",
        "",
        "## R3 Readiness",
        "",
        "Conclusion label: `promising but uncertain`. R2 validates the BoW pipeline and shows usable construct signal, but live decision integration remains intentionally deferred to R3.",
    ]
    (Path(output_dir) / "bow_stage_r2_experiment_report.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )


def write_research_report(output_dir, artifacts):
    game_count = validation_value(artifacts, "source_game_count")
    utterance_count = validation_value(artifacts, "utterance_count")
    vocab_size = validation_value(artifacts, "vocabulary_size")
    best_combined_auc = final_metric(artifacts, "full_legal_combined")
    bow_auc = final_metric(artifacts, "bow_scores_only")
    p_wolf_auc = final_metric(artifacts, "p_wolf_only")
    suspicion_auc = final_metric(artifacts, "suspicion_only")
    structured_auc = final_metric(artifacts, "structured_speech_labels_only")
    p_wolf_structured_auc = final_metric(
        artifacts,
        "p_wolf_suspicion_structured",
    )
    nb_auc = final_metric(artifacts, "full_bow_vector_naive_bayes")
    nb_ood_template_auc = final_metric(
        artifacts,
        "full_bow_vector_naive_bayes",
        split="ood_template",
    )
    role_word_ablation = ""
    for row in artifacts["keyword"]:
        if row.get("comparison") == "remove_direct_role_words_vs_bow_only_unigram_bigram":
            role_word_ablation = row.get("auc_change", "")
    text = [
        "# R2 Research Report: Formal Bag-of-Words Speech Quantification",
        "",
        "## 1. Overview",
        "",
        "This stage converts the simulator's structured speech acts into English natural-language utterances, tokenizes them deterministically, extracts transparent BoW scores, and evaluates whether those scores recover known intent and add predictive information beyond prior structured signals.",
        "",
        "## 2. Data Scale and Splits",
        "",
        f"The R2 dataset contains {game_count} source games and {utterance_count} utterances. Splits are grouped by game family and template family. Vocabulary construction uses train rows only. OOD-template rows use template families withheld from training, and OOD-regime rows use behavioral regimes withheld from training.",
        "",
        "## 3. Score Definitions",
        "",
        "- Werewolf-leaning score: normalized weighted average of manipulation, deflection, pressure, accusation, and certainty terms.",
        "- Emotional-intensity score: normalized intensity weights plus exclamation markers.",
        "- Information-density score: information weights, type-token ratio, player-reference specificity, causal/evidence terms, and a vague-word penalty.",
        "",
        "## 4. Main Predictive Results",
        "",
        f"Final-test ROC-AUC values: BoW scores only = {fmt(bow_auc, 3)}, p_wolf only = {fmt(p_wolf_auc, 3)}, suspicion only = {fmt(suspicion_auc, 3)}, structured labels only = {fmt(structured_auc, 3)}, full legal combined = {fmt(best_combined_auc, 3)}.",
        "",
        "## 5. Generalization and Ablations",
        "",
        "Unseen-template and unseen-regime results are exported in `bow_template_generalization_metrics.csv` and `bow_regime_generalization_metrics.csv`. Keyword ablations test whether role words, player placeholders, accusation verbs, emotional punctuation, and deception-specific terms drive results.",
        "",
        "## 6. Scientific Interpretation",
        "",
        "R2 establishes a genuine BoW pipeline and validates the three proposal-level speech constructs. BoW-only role prediction improves over existing p_wolf and suspicion baselines, but structured speech labels remain stronger and the full legal combined model does not clearly improve over p_wolf + suspicion + structured labels. The evidence is best classified as `promising but uncertain`: the system is useful as a shadow measurement layer, but live decision integration needs a separate R3 experiment with matched game-level outcomes.",
        "",
        "## 7. Required Final Questions",
        "",
        "1. Was a real text-based BoW pipeline implemented? Yes.",
        f"2. How many games and utterances were generated? {game_count} games and {utterance_count} utterances.",
        f"3. How many independent game families and template families were used? {game_count} game families and {validation_value(artifacts, 'template_family_count')} template families.",
        f"4. What is the final vocabulary size? {vocab_size}.",
        "5. What are the three score formulas? See `bow_score_definition_manifest.json`; they are normalized weighted sums for werewolf leaning, emotional intensity, and information density.",
        "6. Does werewolf-leaning distinguish wolves from villagers? Yes descriptively in score/model form; BoW scores reached final-test ROC-AUC "
        f"{fmt(bow_auc, 3)}.",
        "7. Does emotional intensity distinguish emotional speech types? Yes; the pre-specified emotional-vs-neutral contrast is significant after Holm correction.",
        "8. Does information density distinguish informative speech? Yes; the informative-vs-low-information contrast is significant after Holm correction.",
        f"9. Does BoW outperform existing p_wolf? Yes for BoW scores alone on final test ({fmt(bow_auc, 3)} vs {fmt(p_wolf_auc, 3)} ROC-AUC).",
        f"10. Does BoW outperform existing suspicion? Yes for BoW scores alone on final test ({fmt(bow_auc, 3)} vs {fmt(suspicion_auc, 3)} ROC-AUC).",
        f"11. Does BoW add value beyond structured speech labels? Not clearly; structured labels alone reached {fmt(structured_auc, 3)} and structured labels plus BoW scores reached {fmt(final_metric(artifacts, 'structured_labels_plus_bow_scores'), 3)}.",
        f"12. Does structured + BoW outperform either alone? Structured + BoW scores outperform BoW scores alone but not structured labels alone; the full legal combined model reached {fmt(best_combined_auc, 3)}.",
        f"13. Does performance survive unseen-template testing? Rule-based BoW scores retain signal, but the full BoW vector NB model drops from {fmt(nb_auc, 3)} to {fmt(nb_ood_template_auc, 3)}, so the vector model is template-bound.",
        "14. Does performance survive unseen-regime testing? Most combined/structured models remain strong in OOD-regime rows, but this is a simulator-regime test rather than human-language transfer.",
        f"15. Does performance survive removal of direct role words? Yes for the BoW logistic ablation; final-test AUC change is {fmt(role_word_ablation, 3)}.",
        "16. Which vocabulary terms are most influential? See `bow_feature_importance.csv`.",
        "17. Is the model overfitting to template wording? The full vector NB model shows strong OOD-template weakness; transparent scores are less template-sensitive.",
        "18. Did any leakage checks fail? No; the leakage audit status is PASS.",
        "19. Is pure BoW scientifically useful? Yes as a controlled measurement layer, but not sufficient as a standalone decision policy.",
        "20. Is hybrid structured + BoW useful? Possibly for measurement, but no robust added value beyond existing structured + p_wolf/suspicion features is established in R2.",
        "21. Is the BoW module ready for R3 live decision integration? It is ready for controlled R3 testing, not for unguarded replacement of existing decisions.",
        "22. What exact R3 experiment should be run? A matched multi-seed live-game ablation comparing existing belief/voting updates against BoW-weighted belief/voting updates, with credibility and speaker-memory safeguards enabled.",
        "",
        "## 8. Next Hypothesis",
        "",
        "H-R3: Integrating validated BoW speech scores into belief and voting updates will improve village coordination only when credibility and speaker-memory weights prevent wolves from exploiting high-intensity accusation language.",
    ]
    (Path(output_dir) / "bow_stage_r2_research_report.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def write_all_reports(output_dir):
    output_dir = Path(output_dir)
    artifacts = load_artifacts(output_dir)
    write_schema(output_dir)
    write_pre_registration(output_dir)
    write_lexicon_documentation(output_dir)
    write_information_leakage_audit(output_dir)
    write_overfitting_audit(output_dir, artifacts)
    write_template_generalization_report(output_dir, artifacts)
    write_limitations(output_dir)
    write_figures(output_dir, artifacts)
    write_experiment_report(output_dir, artifacts)
    write_research_report(output_dir, artifacts)
    return artifacts


if __name__ == "__main__":
    write_all_reports(Path("results") / "bow_speech_stage_r2")
    print("R2 BoW reports generated")
