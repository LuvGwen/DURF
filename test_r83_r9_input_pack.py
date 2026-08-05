from r83_common import RESULTS_DIR, read_csv


pack = RESULTS_DIR / "corrected_r9_input_pack"
files = [
    "r9_methods_facts.csv",
    "r9_results_facts.csv",
    "r9_discussion_claims.csv",
    "r9_limitations.csv",
    "prohibited_overclaims.csv",
    "README.md",
]

for file_name in files:
    assert (pack / file_name).exists(), file_name

results = read_csv(pack / "r9_results_facts.csv")
assert any(row["row_id"] == "R_Seer" for row in results)
assert all(row["authoritative_stage"] == "R8.3" for row in results)
