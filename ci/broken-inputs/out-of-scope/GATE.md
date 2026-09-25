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

## The declaration that named its own declarant, in `tree-self-declared`

`tree-self-declared/ci/vault.json` carries, field for field, the declaration the repository held until
`rebuild-plugboard` task 3.16: `openspec/changes/rebuild-plugboard/specs` declared out of scope by
`rebuild-plugboard`, the change that owns those specifications. [D31](../../../docs/decisions/d31-out-of-scope-containment.md)
refuses it — the byte-unchanged assertion cannot see which change is editing, so the owner is refused
every revision to its own files. Two failures: the containment case, naming the path and
`rebuild-plugboard`, and the `1/16` coverage shortfall that any fixture carrying one placeholder
specification rather than sixteen also trips. The second is `tree`'s case and is declared here only
because the gate emits it.

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

# 2. Against the real tree -- which, since rebuild-plugboard task 3.16, declares
#    nothing out of scope, so this run reports the emptiness and the vacuity
#    declaration in ci/vault.json gate_policy that explains it.
python3 ci/gates/out_of_scope.py        # exit 0, 0 declared paths, reason and ending printed
```

The self-test also carries D31's negative half — its declarant is not `rebuild-plugboard`, so
containment must stay silent — and the three states of an empty declaration: declared with a reason
(passes, saying so), undeclared (fails), and a vacuity still declared over a set that has gained a
path (fails, so the exemption cannot outlive the emptiness it explains).

And three declarations, each committed in a repository of its own so the gate takes the history
route the real run takes:

- a change other than `rebuild-plugboard` declaring `openspec/specs/docs`, an existing path outside
  its own tree and outside `rebuild-plugboard`'s specifications. This is the declaration D31 permits
  and the vacuity in `ci/vault.json` names as its ending, so it must pass with containment silent. The
  sixteen-spec assertion binds only a set that overlaps `rebuild-plugboard`'s specification tree;
  applied to every set, it failed this one with a message about a change it never named.
- `./openspec/changes/rebuild-plugboard/specs` declared by `rebuild-plugboard`, and `.` declared by
  another change. Git resolves both to the declarant's own files, so containment must fire. Declared
  paths are normalised once where they are read; compared as raw strings, both got past containment.

The meta-check of task 1.3 should treat `--self-test` as this gate's second violating
input: `--root tree` proves the declaration half, `--self-test` proves the history half,
and neutering either code path makes one of the two stop failing.

## Runs

| command | expected |
| --- | --- |
| `python3 ci/gates/out_of_scope.py --root ci/broken-inputs/out-of-scope/tree` | exit 1, 2 violations |
| `python3 ci/gates/out_of_scope.py --root ci/broken-inputs/out-of-scope/tree --report-only` | exit 0, same 2 reported as `[warn]` |
| `python3 ci/gates/out_of_scope.py --root ci/broken-inputs/out-of-scope/tree-self-declared` | exit 1, 2 violations |
| `python3 ci/gates/out_of_scope.py` | exit 0 on the current tree — nothing declared, the declared vacuity's reason and ending printed |
| `python3 ci/gates/out_of_scope.py --self-test` | exit 0, having asserted a planted modification fails, containment stays silent, the three empty-declaration states behave, a declaration D31 permits passes, and the `./` and `.` respellings fire containment |
