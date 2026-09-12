# Violating input: code-duplication

- **Gate:** `ci/gates/code_duplication.py` (`code_duplication`)
- **Rule note:** `docs/code/rules/duplication-threshold.md`
- **Task:** `rebuild-plugboard` task 3.6.
## Violations

1. `first.go` and `second.go` carry ten identical non-comment lines. The verbatim pass.
2. and 3. `third.go` is the same block with every identifier renamed — `in`→`src`, `out`→`dst`,
   `b`→`octet`. Invisible to a verbatim comparison, which is why the rule says "whether or not
   identifiers were renamed between them". `MountStore` and `HookStore` were the same GenServer
   twice.

## One finding per region, not one per window

A ten-line block copied once contains one window; a twenty-line block contains eleven. Reporting each
window is eleven lines about one defect, which is how a gate's output stops being read. Overlapping
windows over the same region are collapsed, and `expect.json` declares the collapsed count.

## The price of the second pass, stated

Blanking identifiers can match two blocks that share only a shape — ten lines of struct fields, a
decision table. It is reported as its own kind so a reviewer can tell the two apart without reading
both sites, and a window carrying fewer than three distinct lines is not evidence of anything: a run
of imports blanks to ten identical placeholders, and matching that is matching the language.

## Expected

Exit 1, three violations.
