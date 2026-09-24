---
type: rule
status: current
authority: rationale
---

# A credential is absent from the tree, and absent from the range under review

**Gate:** `ci/gates/secret_scan.py`

Two subjects, one detector. Every tracked file that decodes as UTF-8 is scanned for a closed set of
credential shapes, and so is every blob added or modified by a commit in the range under review —
the merge-base of the base branch with `HEAD`, or whatever `--range` names.

The second subject is the one that is easy to leave out and is the reason the rule is worth a gate.
A value committed on Tuesday and deleted on Wednesday is gone from the tree and present in every
clone of the branch, so a scan of the tree alone reports green over a credential that is already
disclosed. **Deleting a committed secret is not rotating it**; the fix is at the issuer, and the gate
says so in the failure it prints.

**Merge commits are in that range too**, read through their combined diff — the version the merge
itself wrote where that version matches none of its parents, which is the conflict resolution and any
value typed during one. A resolution belongs to no parent, so skipping merges left such a value in no
subject set at all while the coverage line still claimed every blob the range added or modified
(`ci/gates/secret_scan.py:461`, and the case that holds it is `--self-test` case 5). What a parent
changed is reached through that parent's own commit, which is in the range whenever the parent is.

## Which way the errors run, decided on purpose

Toward false negatives. Every pattern is anchored either on a prefix an issuer assigns — `AKIA…`
for an AWS access key id, `ghp_…` for a GitHub token, `sk_live_…` for a Stripe secret key — or on a
structural delimiter that does not occur by accident, such as a PEM private-key header or the
`user:value@` userinfo of a URL. There is no entropy sweep over arbitrary strings, and no rule that
fires because a value sits next to a secret-sounding name.

This is the position [the banned patterns](../banned-patterns/headers-as-a-map.md) already take for
the same reason: a check that fires on every high-entropy token in a tree is switched off within a
week, and the rule then has no enforcement at all rather than partial enforcement. A credential of an
unrecognised shape passing is a gap. A gate nobody runs is a gap in every shape at once.

So the gate is also held to its negative controls, which live beside the planted values in
`ci/broken-inputs/secret-scan/tree`: a vendor's own published example key, a `${VARIABLE}`
reference, a forty-character commit SHA, and a value keyed on a secret-sounding name. A finding on
any of those is a defect in this gate.

## Two escapes, and what each has to carry

A matched value containing a placeholder token — `example`, `redacted`, `changeme` and their
neighbours — is not reported, because vendors publish example keys of exactly the issued shape and a
gate failing every repository that quotes one is a gate that gets removed.

The second escape is the weakest exclusion in this repository and therefore the one with the most
conditions on it. A line carrying `not-a-live-credential:` suppresses its own finding — for the
revoked value a conformance fixture legitimately holds — but only when the reason after the marker
**names the day the value stopped being live**, as a calendar date already behind us. Every other
exclusion here is one declaration in `ci/vault.json` carrying a reason and the work that ends it,
retrievable by anyone; this one is in-file, per-line and self-service, written by whoever wanted the
finding to stop. The date is what stops it outliving the fact that justified it.

Three markers therefore suppress nothing, and the failure says which condition refused it: a bare
marker, a reason of arbitrary prose with no day in it, and a day that has not arrived — which is a
plan to revoke rather than a revocation. Twelve characters of prose was once the whole condition, so
`aaaaaaaaaaaa` silenced a live token as permanently as a sentence did; the regression cases for all
three are `ci/broken-inputs/secret-scan/tree-marker/`.

Both escapes are counted on every run, passing runs included, and **each honoured suppression is
printed with its path, line, shape and reason** — never counted alone. A count tells a reader of a
green run that something is silenced and not which file, which is an exclusion nobody can retrieve,
which is an exemption. That printing is itself held by `--self-test` case 6, because nothing else
gates it: the fixture declaration reads the violation lines and the failure count, so the list could
be deleted and every other check stay green.

## The value is never printed

A failure names the path, the line, the shape and a fingerprint — never the matched value. A build
log is an artifact too, and a scanner that echoes what it found into one has moved the disclosure
rather than reported it. That is the same obligation the
[threat model](../../how/threat-model.md) puts on emitted signals, applied to the harness itself.

## Why

The prior attempt had no secret scanning of any kind, on the side that held every credential: the
proxy terminating untrusted traffic carried no static analysis, no format gate and no vulnerability
scanning, while the sidecar carried thirty linters ([the audit](../../history/reference-audit.md)).
And material of exactly this class was in its tracked files — a signing salt whose only occurrence in
the repository was an example environment file, and two session salts set in a `Dockerfile` stage
that ended before the runtime image began. Neither is a shape this gate recognises, which is the
honest reading of what a prefix-anchored scanner buys and what it does not.

Dependency and vulnerability scanning is the neighbouring concern and is owned elsewhere —
[supply chain](../../method/supply-chain.md).

## What it does not reach

- **A credential of an unlisted shape.** A signing salt, a database password of no fixed form, a
  bearer value an in-house service issues. None carries an issuer prefix, and the name-anchored rule
  that would catch them is deferred rather than guessed at — see below.
- **A URL userinfo password holding no digit.** `postgres://u:SuperSecretPass@h/db` is not reported.
  The digit is a separate and stricter condition than the entropy floor beside it
  (`ci/gates/secret_scan.py:289`), not a subtlety of it, and it is the condition that decides most of
  the misses in this shape: dropping it fires on `postgres://user:ReplaceThisValue@host`, which a
  runbook writes for a reader to fill in. It is named in the run's own coverage line as its own
  exclusion rather than described as entropy.
- **A tracked key file whose first line is the delimiter.** The marker is read on the finding's line
  and the line above, so a PEM file can carry one — RFC 7468 §5.2 allows explanatory text before the
  encapsulation boundary, and `ci/broken-inputs/secret-scan/tree-marker/fixtures/rotated-tls.pem` is
  the case that shows the marker being suppressed — while an OpenSSH-format private key cannot carry
  one at all. The fixture demonstrating it holds placeholder base64 rather than a key, so the
  parse half of the claim is verified against a generated key and not against the fixture.
  A tracked OpenSSH key fixture therefore needs a declared path scope in `ci/vault.json`, on the
  precedent [binary-asset provenance](binary-assets-carry-provenance.md) sets. The gate does not
  invent that manifest key ahead of the first fixture that needs it.
- **A file that is not valid UTF-8.** It is not read at all. What a committed binary has to declare is
  [binary-asset provenance](binary-assets-carry-provenance.md)'s subject.
- **History before the merge-base.** The range under review is scanned on every run; the rest of
  history is not, and a full-history sweep is a separate piece of work with a different remedy —
  rewriting published history rather than failing a build.
- **Anything under a declared scan exclusion**, including this gate's own violating input. The
  planted values there are committed on purpose, so a secret hidden in that tree is invisible to both
  halves.
- **Whether a matched value is live, and whether it was rotated.** No check over a tree observes
  either; both are the operator's.
- **A value for a configuration item a schema marks secret.** `rebuild-plugboard` task 3.15 asks for
  that half too, and the single configuration schema it would read is task 5.2's and does not exist
  yet ([tasks.md](../../../openspec/changes/rebuild-plugboard/tasks.md)). Keying on the schema is the
  principled form of the name-anchored rule this gate deliberately does not guess at, so it belongs
  in the change that creates the schema rather than in a heuristic written ahead of it.

## What this gate asks of the runner

It is the only one that needs a runner able to **create a commit**: the range half's cases cannot be
carried by a static tree, because a nested repository would be a gitlink. So `--self-test` builds
throwaway repositories, which needs `git` on `PATH`, at least 2.28 for `init -b`, and a writable
temporary directory. Nothing is written to the repository under review — the read-only paths set
`GIT_OPTIONAL_LOCKS=0`, no global or system git config is read (`GIT_CONFIG_GLOBAL` and
`GIT_CONFIG_SYSTEM` are pinned to `os.devnull`), and identity and `commit.gpgsign=false` are passed
per command. When the build fails anyway the self-test prints that dependency rather than a bare
error (`ci/gates/secret_scan.py:926`).
