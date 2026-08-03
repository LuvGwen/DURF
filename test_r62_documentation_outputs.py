from pathlib import Path


REQUIRED = [
    "r62_research_report.md",
    "r62_seer_survival_audit_report.md",
    "r62_witch_potion_waste_audit_report.md",
    "recommended_research_configuration.json",
    "r62_next_stage_readiness.md",
]


def main():
    base = Path("results/metrics_integrity_stage_r62")
    for filename in REQUIRED:
        assert (base / filename).exists(), filename
    print("test_r62_documentation_outputs.py passed")


if __name__ == "__main__":
    main()
