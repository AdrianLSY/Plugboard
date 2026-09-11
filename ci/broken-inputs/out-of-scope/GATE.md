# Violating input: out-of-scope

- **Gate:** `ci/gates/out_of_scope.py`
- **Rule note:** `docs/method/rules/out-of-scope-byte-unchanged.md`
- **Violation:** `tree/ci/vault.json` declares an out-of-scope set that asserts nothing.
  One of its two declared paths — `openspec/changes/rebuild-plugboard/specs/never-existed`
  — matches no file at all, and the set covers **one** `spec.md` file where
  `rebuild-plugboard` has **sixteen**: `specs/proxy/http-fidelity/spec.md` exists in the
  tree and sits outside the declaration entirely, so a coherence pass could revise it
  unnoticed.
- **Expected:** two failures in one run — the prefix that matches nothing, and the
  `1/16` coverage shortfall — each naming `restructure-docs-as-vault` as the change
  that declared the set.

## Why this fixture does not carry the byte-modification case

A violation of "an artifact declared out of scope stays byte-unchanged" is a property of
the **declaration plus version-control history**, never of a file's bytes. A fixture tree
cannot hold history: a nested `.git` under `ci/broken-inputs/` would be committed as a
gitlink, and this repository forbids submodules (`CLAUDE.md` — "One repo, no submodules —
a CI guard enforces that"). So the fixture carries the half of the requirement a tree
without history can carry — set coverage — and the byte-modification case is proven two
other ways, both of which exit non-zero on a real modification:

```sh
# 1. Self-contained. Builds a throwaway git repository in a temp dir with sixteen
#    committed spec.md files, then plants a one-byte change, a deletion and an
#    untracked addition, and asserts this gate fails naming each path, the line,
#    and the declaring change. Exit 0 = the gate detected them; exit 1 = it did not.
python3 ci/gates/out_of_scope.py --self-test

# 2. Against the real tree, which a human or CI can run directly.
F=openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md
printf 'x' >> "$F"
python3 ci/gates/out_of_scope.py        # exit 1, names $F and restructure-docs-as-vault
git checkout -- "$F"
python3 ci/gates/out_of_scope.py        # exit 0, 16/16 covered
```

The meta-check of task 1.3 should treat `--self-test` as this gate's second violating
input: `--root tree` proves the declaration half, `--self-test` proves the history half,
and neutering either code path makes one of the two stop failing.

## Runs

| command | expected |
| --- | --- |
| `python3 ci/gates/out_of_scope.py --root ci/broken-inputs/out-of-scope/tree` | exit 1, 2 violations |
| `python3 ci/gates/out_of_scope.py --root ci/broken-inputs/out-of-scope/tree --report-only` | exit 0, same 2 reported as `[warn]` |
| `python3 ci/gates/out_of_scope.py` | exit 0 on the current tree — `16/16` covered, unchanged since `HEAD` |
| `python3 ci/gates/out_of_scope.py --self-test` | exit 0, having asserted a planted modification fails |
