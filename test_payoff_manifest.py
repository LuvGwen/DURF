from payoff_manifest import build_manifest, manifest_hash


if __name__ == "__main__":
    manifest = build_manifest(source_commit="test")
    assert manifest["manifest_version"] == "r4_payoff_manifest_v1"
    assert manifest["manifest_hash"] == manifest_hash(manifest)
    assert len(manifest["proposal_reference"]) >= 15
    assert any(
        component["component_id"] == "witch_correct_poison"
        and component["base_value"] == 0.4
        for component in manifest["payoff_components"]
    )
    print("test_payoff_manifest.py passed")
