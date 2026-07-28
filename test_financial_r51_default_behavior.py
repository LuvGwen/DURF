from financial_metric_manifest import R4_MANIFEST_HASH
from financial_r51_analysis import R5_METRIC_MANIFEST_HASH


def test_r51_keeps_frozen_manifest_hashes():
    assert R4_MANIFEST_HASH == "eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd"
    assert R5_METRIC_MANIFEST_HASH == "4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf"
