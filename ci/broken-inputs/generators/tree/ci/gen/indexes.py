#!/usr/bin/env python3
"""A generator whose output no longer matches its pinned expectation.

## What the violating input does not reach

Stated so this module exercises case 1 and not case 4 as well.
"""
import sys
from pathlib import Path
root = Path(sys.argv[sys.argv.index("--root") + 1])
(root / "docs").mkdir(parents=True, exist_ok=True)
(root / "docs" / "index.md").write_text("# drifted\n", encoding="utf-8")
