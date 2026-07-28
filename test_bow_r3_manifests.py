from bow_r3_analysis import write_manifests
from bow_r3_belief_integration import r2_manifest_hashes


if __name__ == "__main__":
    hashes = r2_manifest_hashes()
    assert hashes["r2_vocabulary_hash"]
    print("PASS: R2 vocabulary hash available")
    assert hashes["r2_score_definition_hash"]
    print("PASS: R2 score-definition hash available")
    manifest_hashes = write_manifests("results/bow_integration_stage_r3")
    assert manifest_hashes["r3_bow_policy_manifest_hash"]
    print("PASS: R3 policy manifest hash generated")
    assert manifest_hashes["r3_selective_override_manifest_hash"]
    print("PASS: R3 selective override manifest hash generated")
    print("test_bow_r3_manifests.py passed")
