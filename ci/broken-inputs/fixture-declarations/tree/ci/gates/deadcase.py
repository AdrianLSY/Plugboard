#!/usr/bin/env python3
"""A gate emitting two violations, so a declaration can be checked against it."""
import sys
if "--probe" in sys.argv:
    raise SystemExit(3)
print("[FAIL] deadcase: 2 violation(s)")
print("  - docs/first.md: the first case -- with a reason")
print("  - docs/second.md: the second case -- with a reason")
print("  coverage: 2 notes from a directory scan | covered: docs | excluded: -")
raise SystemExit(1)
