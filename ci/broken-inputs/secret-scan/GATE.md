# Violating input: secret-scan

- **Gate:** `ci/gates/secret_scan.py` (`secret_scan`)
- **Rule note:** `docs/code/rules/no-credential-in-tree-or-history.md`
- **Task:** `rebuild-plugboard` task 3.15 — planted credential-shaped values.

## `tree/` — four violations, one per shape the gate anchors on

1. `config/service.conf:3` an AWS access key id, matched on the issuer's prefix.
2. `config/service.conf:4` an AWS secret access key. Unprefixed, forty characters of the base64
   alphabet, and admitted only because the same line names the field AWS itself names — the
   co-occurrence rule `ci/gates/banned_patterns.py` uses to make "a map over header fields"
   decidable. Without that condition this pattern matches a commit SHA.
3. `deploy/tunnel.key:1` a private-key block, matched on its delimiter rather than on its contents.
4. `ops/restore.sh:6` a password in a URL's userinfo.

## The negative controls, in the same tree

Five of them, and they are half the point of this fixture. A secret scanner is easy to write and
hard to keep switched on, so what this tree holds beside the planted values is every shape that a
scanner built out of entropy reports and this one does not:

- `config/service.conf.example` carries the two values **AWS itself publishes** in its
  documentation. Both match a pattern and both are dropped for containing a placeholder token, which
  the run reports as `placeholders skipped: 2`.
- `ops/restore.sh:10` is the same command taking its password from `${PGPASSWORD}`. A reference is
  not a disclosure.
- `ops/restore.sh:13` is the same command again with the word a runbook writes for a reader to fill
  in.
- `ops/notes.txt` holds a forty-character commit SHA on a line that does not name the AWS field, and
  a base64 digest longer than forty characters.
- `ops/notes.txt` also holds two values keyed on a secret-sounding **name**. Nothing here decides by
  name: that rule needs the configuration schema to say which items are secret, and the schema is
  task 5.2's.

A finding on any of those five is a defect in the gate, not a stricter gate.

## `tree-marker/` — three violations: the escape has to end, and cannot be silent

The `not-a-live-credential:` marker is the weakest exclusion in this repository: in-file,
self-service, per-line, and written by whoever wanted the finding to stop. Every other exclusion is
one declaration in `ci/vault.json` carrying a reason **and the work that ends it**, so what this one
has to carry is the day the value stopped being live. Three of the five files here are refusals, and
each failure says which condition refused it:

1. `fixtures/current.token:5` — a **bare** marker. An off switch with no stated reason.
2. `fixtures/undated.token:8` — a real sentence with **no day in it**. Twelve characters of arbitrary
   prose was once the whole condition, so `aaaaaaaaaaaa` silenced a live token exactly as well as a
   sentence does — which is to say permanently. This file is the regression case for that.
3. `fixtures/promised.token:6` — a day that has **not arrived** (`2099-01-01`). A revocation somebody
   intends is not a revocation; it is an exemption that switches itself on today and ends on a day
   nobody has to reach.

The other two are honoured, and the run **names both**:

```
suppressed by marker: 2
    fixtures/revoked.token:4 github-token, fingerprint …: revoked at the issuer on 2026-02-01, …
    fixtures/rotated-tls.pem:5 private-key-block, fingerprint …: key pair retired … on 2026-03-14, …
```

A count alone tells a reader of a green run that something is silenced and not which file, which is
an exemption nobody can retrieve. The count and the lines are printed on every run, passing runs
included.

`fixtures/rotated-tls.pem` is also the fixture that pins **which half of the key-file case works**.
The marker is read on the finding's line and the line above, so a file whose first line *is* the
delimiter has nowhere to put one. A PEM file does: RFC 7468 §5.2 allows explanatory text before the
encapsulation boundary, so the marker sits above `-----BEGIN …-----` and the file still parses. An
OpenSSH-format private key does not tolerate that text, so a tracked OpenSSH key fixture needs a
declared path scope in `ci/vault.json` on the precedent `ci/gates/binary_assets.py` sets. This gate
does not invent that key for itself; the change that lands the first one declares it.

## The history half, which no static tree can carry

The second subject is the commit range under review, and a tree with no `.git` cannot demonstrate
it — a nested repository would be a gitlink, which this repository forbids. So the range cases are
built in temporary repositories by `--self-test`, which asserts six things:

```
python3 ci/gates/secret_scan.py --self-test
```

1. a credential introduced by a commit in the range and **deleted by a later commit** fails, naming
   the path, the line and the introducing commit;
2. the same repository passes for a range that excludes that commit, so the range bounds the half
   rather than decorating it;
3. the same repository passes with no range resolvable, and says so — which records why the history
   half exists rather than trusting a sentence about it;
4. a credential in a tracked file fails on its own, with its line;
5. a credential written by a **merge commit's own conflict resolution** fails, naming that merge. It
   belongs to no parent, so it is in no single-parent commit's diff, and a later commit removes it
   from the tree: a range walk passing `--no-merges` put it in no subject set at all while the
   coverage line claimed every blob the range added. The case also asserts the built merge really has
   two parents, so it cannot pass by testing something else;
6. a **refused** marker still fails and an **honoured** one is printed with its path, line, shape and
   reason. Nothing else gates that printing — the declaration below reads the violation lines and the
   failure count — so without this case the suppression list could be deleted and every check stay
   green.

It also asserts that the matched value never appears in the output. A scanner that echoes what it
found into a build log has moved the disclosure rather than reported it.

## What this gate's runner needs

This is the only gate that requires a runner able to **create a commit**: `git` on `PATH`, at least
2.28 for `init -b`, and a writable temporary directory. Nothing is written to the repository under
review — the read-only paths set `GIT_OPTIONAL_LOCKS=0`, and the built repositories live in a
`TemporaryDirectory`. No global or system git config is read or required: `GIT_CONFIG_GLOBAL` and
`GIT_CONFIG_SYSTEM` are pinned to `os.devnull` and the identity and `commit.gpgsign=false` are passed
per command. When the build fails anyway, `--self-test` prints that dependency rather than a bare
error.

## Expected

`tree/`: exit 1, four violations, `placeholders skipped: 2`. `tree-marker/`: exit 1, three
violations, `suppressed by marker: 2` with both locations named. `--self-test`: exit 0.
