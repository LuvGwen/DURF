from pathlib import Path


report = Path("results/project_overfitting_audit_stage_r81/r81_manifest_hash_forensic_report.md").read_text()
cumulative = Path("results/research_progress/cumulative_research_report.md").read_text()
trace = Path("results/research_progress/source_traceability_index.csv").read_text()

assert "A. Historical hashes verified" in report
assert "R8.1 Manifest Hash Forensic Correction" in cumulative
assert "C_R81_03" in trace
