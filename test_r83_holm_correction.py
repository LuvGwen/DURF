from r83_common import holm_adjust


rows = [
    {"raw_p_value": 0.04},
    {"raw_p_value": 0.01},
    {"raw_p_value": 0.03},
]

holm_adjust(rows)

adjusted = [row["Holm_adjusted_p_value"] for row in rows]
assert adjusted == [0.06, 0.03, 0.06]
