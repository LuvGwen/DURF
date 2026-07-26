from ml_stage15_experiment import build_overfitting_diagnostics


def diagnose_overfitting(identity_metrics, action_metrics):
    return build_overfitting_diagnostics(identity_metrics, action_metrics)
