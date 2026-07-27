"""Run the complete R2 BoW speech quantification stage."""

from pathlib import Path

from bow_dataset_generation import R2_RESULTS_DIR, generate_bow_dataset_outputs
from bow_evaluation import evaluate_bow_outputs
from bow_stage_r2_analysis import write_all_reports


def run_bow_stage_r2(output_dir=R2_RESULTS_DIR):
    output_dir = Path(output_dir)
    dataset = generate_bow_dataset_outputs(output_dir)
    analysis = evaluate_bow_outputs(output_dir)
    reports = write_all_reports(output_dir)
    return {
        "output_dir": output_dir,
        "dataset": dataset,
        "analysis": analysis,
        "reports": reports,
    }


if __name__ == "__main__":
    result = run_bow_stage_r2()
    print("R2 BoW stage complete")
    print(f"Output directory: {result['output_dir']}")
    print(f"Source games: {len(result['dataset']['split_rows'])}")
    print(f"Utterances: {len(result['dataset']['utterance_rows'])}")
    print(f"Vocabulary size: {len(result['dataset']['vocabulary_rows'])}")
