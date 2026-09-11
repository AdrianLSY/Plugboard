#!/usr/bin/env python3
"""Case 3: fails about three distinct subjects while reporting one."""
print("[FAIL] understated: 3 violation(s)")
print("  - docs/a.md:3: something")
print("  - docs/b.md:9: something")
print("  - docs/c.md:1: something")
print("  coverage: 1 note from a directory scan | covered: docs | excluded: -")
raise SystemExit(1)
