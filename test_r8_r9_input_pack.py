from r8_test_utils import R8_DIR, read_rows


manifest = read_rows("r9_input_pack_manifest.csv")

assert len(manifest) >= 10
assert all(row["status"] == "included" for row in manifest)
assert (R8_DIR / "r9_input_pack" / "README.md").exists()
print("test_r8_r9_input_pack passed")
