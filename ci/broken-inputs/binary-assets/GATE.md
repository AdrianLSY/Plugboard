# Violating input: binary-assets

- **Gate:** `ci/gates/binary_assets.py` (`binary_assets`)
- **Rule note:** `docs/code/rules/binary-assets-carry-provenance.md`
- **Task:** `rebuild-plugboard` task 3.14 — a planted unattributed image.

## Violation

1. `assets/unattributed.png` is a real PNG — an eight-byte signature, an `IHDR`, a compressed `IDAT`
   and an `IEND` — committed with no entry in `ci/vault.json`'s `binary_assets`. Nothing in the
   repository says where it came from or on what terms, which is exactly the state the prior attempt's
   85 JPEGs were in.

## The negative control, in the same directory

`assets/README.txt` sits beside it and is not reported. The classifier decides binary-or-not by git's
own heuristic — a NUL byte in the leading block, or a UTF-8 decode that fails — and a check that
reported every file in a directory holding one image would emit two violations here. `expect.json`
says one.

## The other two cases, and why they are not here

The gate also fails a manifest entry whose file is gone, and an entry stating no origin or no terms.
Both are about the DECLARATION in the real `ci/vault.json`, which every run reads regardless of the
tree it was pointed at — so against a deliberately partial tree they would fire about files that tree
was never going to contain. They are scoped to the repository by `on_tracked_tree`, the same guard
`component_boundaries`, `index_drift` and `out_of_scope` each arrived at.

## Expected

Exit 1, one violation.
