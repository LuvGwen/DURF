from pathlib import Path

from r61_common_experiment import RESULTS_DIR, write_pre_registration, write_schema


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_schema(RESULTS_DIR)
    write_pre_registration(RESULTS_DIR)
    assert (Path(RESULTS_DIR) / "r61_schema.md").exists()
    assert (Path(RESULTS_DIR) / "r61_pre_registration.md").exists()
    print("test_r61_documentation_outputs.py passed")


if __name__ == "__main__":
    main()
