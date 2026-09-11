#!/usr/bin/env python3
"""A generator that states nothing about what its violating input misses."""
import sys
from pathlib import Path
root = Path(sys.argv[sys.argv.index("--root") + 1])
(root / "docs").mkdir(parents=True, exist_ok=True)
(root / "docs" / "rule-index.md").write_text("# pinned\n", encoding="utf-8")
