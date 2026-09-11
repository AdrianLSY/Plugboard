# Violating input: precedence

- **Gate:** `ci/gates/precedence.py` (`precedence`)
- **Rule note:** `docs/method/authority-precedence.md`
- **Requirement:** `docs/knowledge-base` — "Authority precedence is stated and enforced".

## Violation

`docs/restates-precedence.md` carries the authority-precedence marker, so the order is stated in
two locations.

## Control that must NOT fail

`docs/defers-correctly.md` says the owning specification wins where it and the note disagree, and
names three layers in prose. That is a *deferral*, which every spine note describing behaviour is
required to make — not a restatement. An earlier version of this gate counted ordered layer names
and reported almost every capability note; the marker-based check has no such false positive.

## Expected

Exit 1, exactly one violation, naming only `docs/restates-precedence.md`.
