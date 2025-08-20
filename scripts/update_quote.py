# Replaces the quote block between <!-- QUOTE:START --> and <!-- QUOTE:END -->.
# Uses a built-in list for reliability (no rate limits).


from __future__ import annotations
import hashlib
from datetime import datetime, timezone
import re


QUOTES = [
"“Programs must be written for people to read, and only incidentally for machines to execute.” — Harold Abelson",
"“Premature optimization is the root of all evil.” — Donald Knuth",
"“Simplicity is the soul of efficiency.” — Austin Freeman",
"“The only way to go fast, is to go well.” — Robert C. Martin",
"“Controlling complexity is the essence of computer programming.” — Brian Kernighan",
"“First, solve the problem. Then, write the code.” — John Johnson",
"“Talk is cheap. Show me the code.” — Linus Torvalds",
"“Code is like humor. When you have to explain it, it’s bad.” — Cory House",
"“Fix the cause, not the symptom.” — Steve Maguire",
"“Simple is better than complex.” — The Zen of Python",
]


READ_ME = "README.md"


now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
idx = int(hashlib.sha256(now.encode()).hexdigest(), 16) % len(QUOTES)
quote = QUOTES[idx]


with open(READ_ME, "r", encoding="utf-8") as f:
content = f.read()


pattern = r"(<!-- QUOTE:START -->)(.*?)(<!-- QUOTE:END -->)"
replacement = r"\1\n" + quote + r"\n\3"
updated = re.sub(pattern, replacement, content, flags=re.S)


if updated != content:
