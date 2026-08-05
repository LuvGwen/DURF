from r83_common import RESULTS_DIR, read_csv


prohibited = ["optimal", "proven", "universally best", "causes"]
tables = [
    read_csv(RESULTS_DIR / "r83_final_five_role_recommendations.csv"),
    read_csv(RESULTS_DIR / "r83_final_claim_registry.csv"),
]

for rows in tables:
    for row in rows:
        safe_text = " ".join(
            value
            for key, value in row.items()
            if key not in {"prohibited_wording", "claim"}
        ).lower()
        for word in prohibited:
            assert word not in safe_text
