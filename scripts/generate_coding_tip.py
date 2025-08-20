# Updates the README between <!-- CODING_TIP:START --> and <!-- CODING_TIP:END -->
# with a deterministic tip-of-the-day (no external APIs needed).


from __future__ import annotations
import hashlib
from datetime import datetime, timezone
import re


TIPS = [
"Keep a \"tiny repro\" habit: isolate the smallest failing case before debugging.",
"Name things well. Descriptive identifiers reduce comments and bugs.",
"Prefer pure functions. Side effects make code harder to test.",
"Write tests for bugs you find; they become guardrails for the future.",
"Automate repetitive tasks with scripts—your future self will thank you.",
"Fail fast: validate inputs and assert invariants early.",
"Keep functions short. If it needs scrolling, split it.",
"Log with context (ids, sizes, timings), not just messages.",
"Measure before optimizing; profiling beats guessing.",
"Document \"why\" in PRs; the code shows \"what\".",
"Use feature flags for safer rollouts and quick rollbacks.",
"Make linters part of CI; let robots catch style issues.",
"Prefer composition over inheritance for flexibility.",
"Choose immutability by default; mutate only when needed.",
"Guard your boundaries: validate at API edges.",
]


READ_ME = "README.md"


now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
idx = int(hashlib.sha256(now.encode()).hexdigest(), 16) % len(TIPS)
new_tip = TIPS[idx]


with open(READ_ME, "r", encoding="utf-8") as f:
content = f.read()


pattern = r"(<!-- CODING_TIP:START -->)(.*?)(<!-- CODING_TIP:END -->)"
replacement = r"\1\n" + new_tip + r"\n\3"
updated = re.sub(pattern, replacement, content, flags=re.S)


if updated != content:
with open(READ_ME, "w", encoding="utf-8") as f:
f.write(updated)
print("Updated coding tip.")
else:
print("Coding tip unchanged.")
