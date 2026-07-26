import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ml_feature_registry import FEATURE_COLUMNS, PROHIBITED_FEATURES


STAGE15_WOLF_DATASET = (
    Path("results")
    / "ml_optimization_stage15"
    / "ml_full_rollout_wolf_kill_dataset.csv"
)
STAGE2A_RESULTS_DIR = Path("results") / "ml_optimization_stage2a"
FROZEN_MODEL_MANIFEST_PATH = (
    STAGE2A_RESULTS_DIR / "wolf_kill_frozen_model_manifest.json"
)
TARGET_COLUMN = "full_rollout_mean_team_win_rate"
MODEL_TYPE = "ridge_regression_stdlib_l2"
TRAINING_SEEDS = list(range(42, 50))
VALIDATION_SEEDS = [50, 51]
EXCLUDED_STAGE15_FINAL_TEST_SEEDS = list(range(52, 57))
LIVE_FINAL_TEST_SEEDS = list(range(100, 120))

PROHIBITED_LIVE_FEATURE_TOKENS = [
    "true_candidate_role",
    "candidate_is_wolf_label",
    "candidate_is_special_label",
    "eventual_winner",
    "actor_team_win",
    "full_rollout",
    "rollout_value",
    "final_survival",
    "future",
]


def as_float(value, default=0.0):
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def stable_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_hash(value):
    return sha256_text(stable_json(value))


def current_git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return ""


def read_csv_rows(path):
    with Path(path).open(newline="") as file:
        return list(csv.DictReader(file))


def write_json(path, value):
    path.parent.mkdir(exist_ok=True, parents=True)
    with Path(path).open("w") as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write("\n")


def load_json(path):
    with Path(path).open() as file:
        return json.load(file)


def live_feature_columns():
    features = list(FEATURE_COLUMNS)
    validate_live_feature_safety(features)
    return features


def validate_live_feature_safety(feature_columns):
    prohibited = set(feature_columns) & set(PROHIBITED_FEATURES)
    token_hits = [
        feature for feature in feature_columns
        if any(token in feature for token in PROHIBITED_LIVE_FEATURE_TOKENS)
    ]
    if prohibited or token_hits:
        raise ValueError({
            "prohibited_features": sorted(prohibited),
            "token_hits": sorted(token_hits),
        })
    return True


def train_rows_from_stage15(path=STAGE15_WOLF_DATASET):
    rows = read_csv_rows(path)
    return [
        row for row in rows
        if row.get("decision_type") == "wolf_kill"
        and row.get("split_name") == "train"
    ]


def feature_training_ranges(rows, feature_columns):
    ranges = {}
    for feature in feature_columns:
        values = [as_float(row.get(feature), 0.0) for row in rows]
        ranges[feature] = {
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0,
            "missing_count": sum(
                1 for row in rows
                if row.get(feature) in ("", None)
            ),
        }
    return ranges


def build_model_payload(model, rows, feature_columns):
    return {
        "model_type": MODEL_TYPE,
        "target_column": TARGET_COLUMN,
        "feature_order": list(feature_columns),
        "intercept": model["intercept"],
        "coefficients": list(model["weights"]),
        "standardization_means": list(model["standardizer_means"]),
        "standardization_scales": list(model["standardizer_scales"]),
        "training_feature_ranges": feature_training_ranges(
            rows,
            feature_columns,
        ),
        "missing_value_handling": "missing numeric features are filled with 0.0 before training-set standardization",
        "regularization": {
            "kind": "L2 ridge",
            "l2": 0.01,
            "epochs": 220,
            "learning_rate": 0.01,
        },
    }


def model_artifact_hash(payload):
    return stable_hash({
        "model_type": payload["model_type"],
        "target_column": payload["target_column"],
        "feature_order": payload["feature_order"],
        "intercept": payload["intercept"],
        "coefficients": payload["coefficients"],
        "standardization_means": payload["standardization_means"],
        "standardization_scales": payload["standardization_scales"],
        "missing_value_handling": payload["missing_value_handling"],
        "regularization": payload["regularization"],
    })


def manifest_hash(manifest):
    canonical = {
        key: value for key, value in manifest.items()
        if key != "manifest_hash"
    }
    return stable_hash(canonical)


def create_frozen_wolf_kill_model(
    output_path=FROZEN_MODEL_MANIFEST_PATH,
    source_dataset=STAGE15_WOLF_DATASET,
    created_at_utc=None,
):
    feature_columns = live_feature_columns()
    rows = train_rows_from_stage15(source_dataset)
    if not rows:
        raise ValueError("No Stage 1.5 wolf-kill train rows found.")
    from ml_train_baselines import fit_ridge_regression

    model = fit_ridge_regression(
        rows,
        TARGET_COLUMN,
        feature_columns=feature_columns,
    )
    payload = build_model_payload(model, rows, feature_columns)
    manifest = {
        **payload,
        "stage": "ml_optimization_stage2a",
        "serialization_format": "json_manifest_v1",
        "created_at_utc": (
            created_at_utc
            if created_at_utc is not None
            else datetime.now(timezone.utc).isoformat()
        ),
        "source_commit_hash": current_git_commit(),
        "source_dataset": str(source_dataset),
        "source_dataset_sha256": sha256_text(
            Path(source_dataset).read_text()
        ),
        "training_rows": len(rows),
        "training_seeds": TRAINING_SEEDS,
        "validation_seeds": VALIDATION_SEEDS,
        "excluded_stage15_final_test_seeds": (
            EXCLUDED_STAGE15_FINAL_TEST_SEEDS
        ),
        "live_final_test_seeds": LIVE_FINAL_TEST_SEEDS,
        "final_test_seed_isolation": (
            "Seeds 100-119 are reserved for Stage 2A live testing and are "
            "not used for model training, feature selection, hybrid weight "
            "selection, epsilon selection, or model selection."
        ),
        "model_artifact_hash": model_artifact_hash(payload),
    }
    manifest["manifest_hash"] = manifest_hash(manifest)
    write_json(output_path, manifest)
    return manifest


def validate_frozen_model_manifest(
    manifest_or_path=FROZEN_MODEL_MANIFEST_PATH,
):
    if isinstance(manifest_or_path, (str, Path)):
        manifest = load_json(manifest_or_path)
    else:
        manifest = dict(manifest_or_path)

    validate_live_feature_safety(manifest["feature_order"])
    if manifest["feature_order"] != live_feature_columns():
        raise ValueError("Frozen model feature order changed.")
    if len(manifest["coefficients"]) != len(manifest["feature_order"]):
        raise ValueError("Coefficient count does not match feature order.")
    if len(manifest["standardization_means"]) != len(
        manifest["feature_order"]
    ):
        raise ValueError("Preprocessing mean count changed.")
    if len(manifest["standardization_scales"]) != len(
        manifest["feature_order"]
    ):
        raise ValueError("Preprocessing scale count changed.")
    expected_model_hash = model_artifact_hash(manifest)
    if expected_model_hash != manifest.get("model_artifact_hash"):
        raise ValueError("Frozen model artifact hash changed.")
    expected_manifest_hash = manifest_hash(manifest)
    if expected_manifest_hash != manifest.get("manifest_hash"):
        raise ValueError("Frozen model manifest hash changed.")
    if any(seed in TRAINING_SEEDS + VALIDATION_SEEDS for seed in LIVE_FINAL_TEST_SEEDS):
        raise ValueError("Live final-test seeds overlap development seeds.")
    return {
        "valid": True,
        "model_artifact_hash": manifest["model_artifact_hash"],
        "manifest_hash": manifest["manifest_hash"],
        "feature_count": len(manifest["feature_order"]),
    }


def predict_from_manifest(manifest, feature_row):
    values = []
    missing_count = 0
    for feature in manifest["feature_order"]:
        raw_value = feature_row.get(feature)
        if raw_value in ("", None):
            missing_count += 1
        values.append(as_float(raw_value, 0.0))

    standardized = []
    for value, mean, scale in zip(
        values,
        manifest["standardization_means"],
        manifest["standardization_scales"],
    ):
        scale = scale if scale else 1.0
        standardized.append((value - mean) / scale)

    prediction = manifest["intercept"] + sum(
        weight * value
        for weight, value in zip(manifest["coefficients"], standardized)
    )
    prediction = max(0.0, min(1.0, prediction))
    return prediction, {
        "raw_values": values,
        "standardized_values": standardized,
        "missing_feature_count": missing_count,
    }


if __name__ == "__main__":
    manifest = create_frozen_wolf_kill_model()
    validation = validate_frozen_model_manifest(manifest)
    print("Frozen wolf-kill model manifest created")
    print("Manifest:", FROZEN_MODEL_MANIFEST_PATH)
    print("Manifest hash:", validation["manifest_hash"])
    print("Model artifact hash:", validation["model_artifact_hash"])
