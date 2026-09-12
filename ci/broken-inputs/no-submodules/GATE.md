# Violating input: no-submodules

- **Gate:** `ci/gates/no_submodules.py` (`no_submodules`)
- **Rule note:** `docs/code/rules/no-submodules.md`
- **Decision:** [D22 — one repository](../../../docs/decisions/d22-one-repository.md).

## Violations

1. `.gitmodules` sits at the root of the tree, declaring a `sidecar` submodule — the exact shape D22
   replaced, down to the component name.

## The second case, and why it is not here

The gate also fails any tracked path recorded with mode `160000`, the gitlink entry a submodule leaves
in the version-control index. That entry is what actually pins a foreign revision: it survives
`.gitmodules` being deleted, so a fixture that demonstrated only the declaration would leave the
load-bearing half unproven.

It cannot be demonstrated here. A violating input is a directory, not a repository, so it has no index
to record a mode in — and committing a real gitlink into this repository to serve as a fixture is the
one thing the gate exists to prevent. It is demonstrated in a throwaway repository instead, which is
what `rebuild-plugboard` task 1.2 asks for and carries no risk to this one's index:

```
mkdir -p /tmp/sm/inner /tmp/sm/outer
git -C /tmp/sm/inner init -q . && (cd /tmp/sm/inner && echo hi > a.txt && git add -A && git commit -qm init)
git -C /tmp/sm/outer init -q . && (cd /tmp/sm/outer && echo hi > b.txt && git add -A && git commit -qm init)
git -C /tmp/sm/outer -c protocol.file.allow=always submodule add -q ../inner vendor/inner
python3 ci/gates/no_submodules.py --root /tmp/sm/outer     # 2 violations, exit 1
git -C /tmp/sm/outer rm -q --cached .gitmodules && rm /tmp/sm/outer/.gitmodules
python3 ci/gates/no_submodules.py --root /tmp/sm/outer     # 1 violation, exit 1 -- the gitlink alone
```

The second run is the one that matters: with the declaration deleted the entry is still there, still
pinning `inner`'s commit, and the gate still names it. A check that read `.gitmodules` alone would
have gone green on that tree.

Stated rather than omitted: a fixture that does not say which case it leaves uncovered turns an
unexamined case into an apparently examined one.

## Expected

Exit 1, one violation.
