from r8_test_utils import read_rows


bow_rows = read_rows("r8_speech_bow_final_table.csv")
ml_rows = read_rows("r8_ml_final_table.csv")
bow_text = " ".join(row["conclusion"] for row in bow_rows)
ml_text = " ".join(row["conclusion"] for row in ml_rows)

assert len(bow_rows) >= 8
assert len(ml_rows) >= 8
assert "harmful" in bow_text
assert "not recommended" in ml_text or "diagnostic" in ml_text
print("test_r8_bow_ml_summary passed")
