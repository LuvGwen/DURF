from r81_common import build_bootstrap_outputs


first = build_bootstrap_outputs(replicates=10)[1]
second = build_bootstrap_outputs(replicates=10)[1]
assert first == second
