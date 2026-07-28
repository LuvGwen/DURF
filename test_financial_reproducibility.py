from financial_metric_manifest import build_metric_manifest


def main():
    first = build_metric_manifest()
    second = build_metric_manifest()
    assert first["metric_manifest_hash"] == second["metric_manifest_hash"]
    print("test_financial_reproducibility.py passed")


if __name__ == "__main__":
    main()
