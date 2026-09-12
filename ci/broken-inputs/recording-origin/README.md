# Violating input: the recording origin, built wrong

- **Subject:** `conformance/recorder` — the instrument, and its assertion suite `AssertFaithful`.
- **Task:** `rebuild-plugboard` task 4.2 — *"a deliberately map-backed variant committed under
  `ci/broken-inputs/` fails the header and method assertions — the instrument is proven to
  discriminate before anything is measured with it."*

## What is wrong with it, and what deliberately is not

`MapBacked` makes exactly two of the prior attempt's type choices and no others:

1. a field section keyed by a canonicalised name (`proxy_controller.ex:496` was
   `Enum.into(conn.req_headers, %{})`; `telephone.go:85` was the same shape in Go);
2. a method token normalised to upper case (`router.ex:63-69` matched an enumerated list of
   upper-case verbs).

Body octets, the digest, and the raw request target are carried **faithfully**. That is the point of
the fixture rather than an economy: it shows the suite rejecting those two properties *specifically*,
not rejecting a generally broken implementation. A suite that failed everything on a partly-wrong
recorder would be no more useful than one that failed nothing, and `mapbacked_test.go` asserts both
directions.

## Why this is not a gate fixture

There is no `ci/gates/recording_origin.py`, so `ci/gates/meta.py` and
`ci/gates/fixture_declarations.py` both pass over this directory — it is keyed on gate modules, and
this is not a gate. What runs it is
`conformance/recorder/discriminates_test.go`, in the integration tier: `ci/broken-inputs` is a
declared scan exclusion, so nothing here is reachable from a component's build and the proof has to
be pulled in from the other side or it is never performed.

## Its own module, deliberately

A `go.mod` with a `replace` to `../../../conformance`. Without it this source would either be part of
the conformance module — where a deliberately wrong recorder sits one import away from the real one —
or be uncompilable, which is the same as absent.

```
cd ci/broken-inputs/recording-origin && go test -race ./...   # passes: the suite rejects MapBacked
make -C conformance test-integration                           # runs the above from the other side
```
