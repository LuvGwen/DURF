from pathlib import Path

from r8_test_utils import R8_DIR


texts = []
for path in R8_DIR.glob("r8_*.md"):
    texts.append(path.read_text(encoding="utf-8").lower())
joined = "\n".join(texts)

assert "global optimum" in joined
assert "not causal" in joined or "do not label premiums as causal effects" in joined
assert "proves" not in joined
assert "guarantees" not in joined
print("test_r8_no_overclaiming passed")
