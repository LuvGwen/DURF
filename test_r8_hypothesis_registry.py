from r8_test_utils import read_rows


rq_rows = read_rows("r8_research_question_registry.csv")
h_rows = read_rows("r8_final_hypothesis_registry.csv")
rq_ids = {row["research_question_id"] for row in rq_rows}

assert len(rq_rows) >= 6
assert len(h_rows) >= 14
assert all(row["research_question_id"] in rq_ids for row in h_rows)
assert all(row["final_safe_wording"] for row in h_rows)
print("test_r8_hypothesis_registry passed")
