# Third-party notices — `.claude/`

**Nothing in this directory is covered by the repository's [`LICENSE`](../LICENSE).** The files here
are a vendored agent harness: skills and slash commands authored elsewhere and copied in. `D28` scopes
the Apache-2.0 grant to the work this repository authors, and this file records what is known about
the rest.

`ci/vault.json` already declares `.claude` an exempt root for the note gates, on the ground that its
"frontmatter keys and file layout are owned by the Claude Code loader and by vendored upstream
skills". That exemption is about *classification*. This file is about *copyright*, which no gate
checks and no exemption settles.

## What is declared

Six skills carry a licence in their own frontmatter, at `SKILL.md:5` and `SKILL.md:8` of each:

| path | declared licence | declared author |
|---|---|---|
| `skills/openspec-apply-change/` | MIT | `openspec` |
| `skills/openspec-archive-change/` | MIT | `openspec` |
| `skills/openspec-explore/` | MIT | `openspec` |
| `skills/openspec-propose/` | MIT | `openspec` |
| `skills/openspec-sync-specs/` | MIT | `openspec` |
| `skills/openspec-update-change/` | MIT | `openspec` |

MIT requires that its permission notice travel with all copies. These six declare the licence and the
author but carry no copyright line and no notice text, so the obligation is recorded here and is not
yet dischargeable from this tree — see the gap below.

## What is not declared

> **Unverified.** The remaining twenty-five skill directories under `skills/` and the six
> slash commands under `commands/opsx/` declare **no licence, no copyright holder, and no source URL**
> anywhere in this repository. `setup-matt-pocock-skills/` names a family by convention and records no
> upstream either. Their origin is not establishable from the tracked tree — reproduce with
> `git ls-files .claude` and read the frontmatter of each. — needs the installing party to name where
> each set was obtained.

This is the defect [the supply-chain rule](../docs/method/supply-chain.md) logs against the prior art,
turned on this repository: *"85 JPEGs of unestablished origin under a blanket MIT claim with no
attribution."* The response is the same one the vault requires everywhere else — state the gap, do not
issue a licence claim over files whose provenance is unknown, and give it an ending condition. It has
one, in [follow-ups](../docs/method/follow-ups.md).

## What this means for a reader

Clone, read and run the harness as the upstream terms allow — this repository does not extend a grant
it does not hold. If you are redistributing this tree, the MIT directories need their notices and the
undeclared ones need their provenance established first.

Removing `.claude/` entirely leaves the vault and the specifications in place: it is a declared exempt
root, so no gate takes a *subject* from it. That is not the same as removing it cleanly. Three tracked
notes link *into* this file — the README, [`d28-licensing`](../docs/decisions/d28-licensing.md) and
[`follow-ups`](../docs/method/follow-ups.md) — and `ci/gates/links.py` resolves link targets whatever
root they point at, so those three links have to go with the directory or `make check` fails with
three `missing-file` violations. Exemption governs what a gate takes as its subject, never what a
tracked note may point at.
