from r83_common import verify_r82_raw_hashes
from r83_primary_contrast_recalculation import recompute_primary_contrasts


first = recompute_primary_contrasts()
second = recompute_primary_contrasts()

assert first == second
assert all(row["matches"] == "True" for row in verify_r82_raw_hashes())
