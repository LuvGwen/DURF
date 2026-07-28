from financial_stage_r5_analysis import enrich_player_rows


def main():
    rows = [{
        "total_payoff": "0.75",
        "opportunity_cost": "-0.25",
    }]
    enriched = enrich_player_rows(rows)[0]
    assert enriched["payoff_excluding_opportunity_cost"] == 1.0
    assert enriched["opportunity_cost_adjusted_payoff"] == 0.75
    print("test_financial_opportunity_cost.py passed")


if __name__ == "__main__":
    main()
