---
type: rule
status: current
authority: rationale
---

# A top-level directory carries a README, or a declared reason it does not

**Gate:** `ci/gates/top_level_readmes.py`

Every directory at the root of the repository that holds a tracked file has a `README.md` naming what
the directory is and linking the note that states its boundary. A directory that legitimately has no
README is named in `ci/vault.json` under `code_standards.top_level_readmes.exempt`, with the reason
beside it — and that declaration fails once its directory holds no tracked file, so an exemption
cannot outlive its subject.

The README routes. It does not restate the boundary: that half is
[a component's boundary is stated once](component-boundary-stated-once.md), and the two are separate
gates on purpose, so "there is no README" and "the README is a second copy of the boundary" fail
apart and hand over different remedies.

## Why

Five component directories were created empty, in one commit, before any of them held a line of
source. An empty directory with no README is indistinguishable from a mistake — and the failure mode
is not that somebody deletes it, but that the next person puts a file in the wrong one of the five
because nothing at the root told them which.

The prior art shows where that ends. `MountStore` and `HookStore` were the same GenServer twice, and
domain affinities were then bolted *inside* `MountStore` because there was no third slot and nothing
said where a third slot would go ([reference audit](../../history/reference-audit.md)). Placement has
to be answerable before a contributor picks a file, and the cheapest place to answer it is the
directory they are already standing in.

The exemptions are declared rather than inferred because each of the four is exempt for a different
reason: `docs/` is entered through a generated index, `openspec/` has its layout owned by an external
tool, `ci/` is described once in [the harness note](../../method/harness.md), and `.github/` and
`.obsidian/` are read by a service and an editor rather than by a person arriving at the tree. No
heuristic recovers those; a person knows them, so a person writes them down.
