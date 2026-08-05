from r81_test_utils import read_text


text = read_text("r81_overclaiming_audit.md")
assert "avoid global-optimum claims" in text
assert "requires targeted replication" in text
