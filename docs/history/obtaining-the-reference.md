---
type: procedure
status: current
authority: rationale
---

# Obtaining the reference

**This procedure is incomplete, and that is the honest state of it.** Everything needed to *check*
that you obtained the right prior art is recorded below and is checkable from this repository.
Everything needed to *fetch* it is not — the clone source is recorded nowhere here. The note is
marked `planned` for that reason, and [what closes it](#what-closes-this-note) says exactly what
supplying it takes.

The stake is not small. The change that created this note records **139 `file:line` citations across
61 distinct files pointing into `reference/`**
(`openspec/changes/restructure-docs-as-vault/proposal.md:5`), almost all of them in
[the reference audit](reference-audit.md) and [carry-forward](carry-forward.md). That figure is a
count taken when the change was proposed, not a live one; `python3 ci/gates/citations.py` reports
how many citations it checked on the tree in front of you. Until the fetch step exists, none of them
is checkable by anyone but the author.

## What is pinned

| Component | Expected path, relative to this repository's root | Pinned revision |
|---|---|---|
| Plugboard (Elixir/Phoenix) | `reference/Plugboard` | `6756a07` |
| Telephone (Go) | `reference/Telephone` | `9ccba86` |

Recorded in three places that agree: `docs/start-here.md:109`,
`docs/history/reference-audit.md:11`, and `docs/history/carry-forward.md:12`. The last of these also
fixes the form of a citation — `carry-forward.md:12` states that citations are relative to each
component root, so `endpoint.ex:118` (`docs/history/reference-audit.md:48`) names line 118 of that
file inside `reference/Plugboard` at `6756a07`. A line number resolved against any other revision is
not the line the vault cites.

The paths are not decorative. `reference/` is a one-line entry in this repository's `.gitignore`,
and [`ci/vault.json`](../../ci/vault.json) declares it an exempt root — read-only prior art, untracked
by design — while its `cited_artifacts` block declares *this note* as the one stating how to obtain
it. [`ci/gates/citations.py`](../../ci/gates/citations.py) fails while a declared artifact's
obtaining note is missing, or while that note omits either pinned revision.

## The gap

There is no repository URL, no archive location, and no fetch instruction anywhere in this
repository. Three checks establish it, and all three are cheap to repeat:

```
grep -rIn 'git@\|github\.com\|gitlab\|bitbucket' . | grep -v '^\./\.git'
cat .gitignore
git remote -v
```

As of this note, the second command prints `reference/` and nothing further about it, and the third
prints nothing at all — this repository has no configured remote. Neither records where the prior art
came from.

> **Unverified.** The two clone sources appear to be recorded in exactly one place — `.gitmodules`
> inside the `reference/` checkout itself, which is the circularity that makes this a gap: learning
> where to get the prior art requires already having it. In one working copy that file names
> `git@github.com:AdrianLSY/Vera-Plugboard` for `Plugboard` and
> `https://github.com/AdrianLSY/Vera-Telephone` for `Telephone`, as submodules at the paths
> `Plugboard` and `Telephone` of an outer repository whose own remote is
> `git@github.com:AdrianLSY/Vera-Reverse-Proxy.git` — which, if it is right, means cloning that outer
> repository into `reference/` with `--recurse-submodules` produces the expected layout directly.
> Nothing in this repository records any of the three, and none has been confirmed reachable by
> anyone other than the author: two are SSH remotes needing a key, and whether any of the three is
> publicly readable is unknown. — needs checking against the three hosts themselves, by a clone
> attempted from a machine holding no existing checkout and no author credential.

The requirement this note serves is
[*A cited artifact is obtainable*](../../openspec/changes/restructure-docs-as-vault/specs/docs/knowledge-base/spec.md#requirement-a-cited-artifact-is-obtainable).
Its first two scenarios are decidable by a gate and pass: the artifact is declared, and this note
pins the revisions. Its third — a reader who follows the instructions arriving at the revision the
citations name — is the half still unsatisfied, because there are no instructions to follow. That is
the gap, stated where the requirement can be read next to it rather than left for a reader to notice.

Treat the block above as a lead, not an instruction. A `git clone` line written from a guess would
look identical to one written from knowledge, and a plausible wrong URL is worse than an admitted
gap — that failure mode is the reason [the documentation rules](../method/documentation-rules.md)
make an uncheckable claim a defect rather than a rough edge.

## Verifying you got the right thing

Independent of how the trees arrive, this is the check that they are the trees the citations were
taken against. Run it from the repository root:

```
git -C reference/Plugboard rev-parse --short=7 HEAD     # expect 6756a07
git -C reference/Telephone rev-parse --short=7 HEAD     # expect 9ccba86
```

`--short=7` rather than `--short`, so the width of the output is fixed by the command and the
comparison against a seven-character pin is exact.

If either prints something else, check out the pin by name before reading a single citation —
`git -C reference/Plugboard checkout 6756a07`. Doing it by SHA rather than trusting a submodule
pointer or a branch tip is deliberate: a pointer can have moved since the audit, and the SHA is the
thing the citations name.

Then confirm a citation, not just a revision. Ten sampled from the audit and carry-forward is the
bar task 4.2 sets; `docs/history/reference-audit.md:48-51` gives four of them in one block, each a
`file:line` in `reference/Plugboard` with the text it is claimed to hold.

## What the prior art is not

**Never a behavioural source of truth.** `docs/start-here.md:9-12` states the standing rule, and
[the reference audit](reference-audit.md) records what it found. Obtaining these trees makes the
vault's claims *about* them checkable; it confers nothing on the code itself. Cite it with a
`file:line` or not at all.

## What closes this note

Two things, in this order:

1. **Record the fetch step in this repository** — the two clone sources, or an archive location, or
   a vendored bundle — verified reachable from a machine with no existing checkout. Then this note
   becomes `status: current` and stops being the weakest link in 139 citations.
2. **Sample and confirm**, per task 4.2 of
   [the change that created this note](../../openspec/changes/restructure-docs-as-vault/tasks.md):
   ten citations resolving to the cited lines at the pinned revisions, from a clean environment.

Task 4.3 in the same list builds the gate that refuses a citation into an artifact with no obtaining
note. That gate can check this note exists and pins the revisions. It cannot check that the fetch
step works, which is why step 1 is a person's job.

> Orientation, not behaviour. The specifications win.

## On the requirement titles named above

Where this note names a specification's own requirement, it does so because a reader checking the
claim should land on the obligation itself rather than on a paraphrase. Those summaries are
**non-normative**: the owning specification wins where it and this note disagree, and where this note
is narrower or wider than the requirement it names, the requirement is right.
