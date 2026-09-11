#!/usr/bin/env python3
"""A conforming generator.

## What the violating input does not reach

Anything: this module exists so the fixture holds a passing case alongside the failing ones.
"""
import sys
from pathlib import Path
root = Path(sys.argv[sys.argv.index("--root") + 1])
(root / "docs" / "method").mkdir(parents=True, exist_ok=True)
(root / "docs" / "method" / "conventions.md").write_text("# pinned\n", encoding="utf-8")
