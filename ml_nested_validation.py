from ml_stage15_experiment import (
    evaluate_action_value_generalization,
    evaluate_feature_ablation,
    evaluate_identity_generalization,
)


def run_grouped_nested_validation(rows):
    return {
        "identity_metrics": evaluate_identity_generalization(rows),
        "action_value_metrics": evaluate_action_value_generalization(rows),
        "feature_ablation_metrics": evaluate_feature_ablation(rows),
        "selection_note": (
            "Stage 1.5 uses train and validation splits for model selection; "
            "final_test rows are evaluated after selections are frozen."
        ),
    }
