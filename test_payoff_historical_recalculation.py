from payoff_historical_recalculation import (
    build_historical_recalculated_payoffs,
    build_historical_recalculation_coverage,
)


if __name__ == "__main__":
    coverage = build_historical_recalculation_coverage()
    assert coverage
    assert any(row["stage"] == "BoW R3 live" for row in coverage)
    recalculated = build_historical_recalculated_payoffs(coverage)
    assert len(recalculated) == len(coverage)
    assert all("recalculation_status" in row for row in recalculated)
    print("test_payoff_historical_recalculation.py passed")
