---
type: guide
status: current
authority: rationale
---

# Go conventions

Go holds three modules: [`sidecar/`](../../../sidecar/README.md), the program a tenant runs;
[`terminator/`](../../../terminator/README.md), the client-facing edge
[D16](../../decisions/d16-http2-to-clients.md) puts in v1; and
[`conformance/`](../../../conformance/README.md), the suite that is the authority on the contract.
Which languages appear here is [keyed on tracked source](../rules/language-conventions-keyed-on-source.md),
so this note arrived with the modules and not before.

Why Go at all is [D4](../../decisions/d04-runtime.md), and the reason is not only the static binary:
it is the language a customer's platform team will read before allowing the process into their pods.

## One linter configuration, and the recipes in one copy

`.golangci.yml` at the root is the only one, and `ci/make/go.mk` holds the only copy of `fmt`, `lint`,
`test`, `gen` and `dev`. Both are enforced — [one linter configuration](../rules/one-linter-config.md)
— because the prior art's asymmetry, thirty linters on one side and none on the component facing the
internet, is what two configurations become.

## `-race` is the invocation, not a flag

`ci/make/go.mk`'s `test` target is `go test -race ./...`, and no target here runs `go test` without
it. A data race in a proxy is a corrupted response body, and it is the defect class least likely to
reproduce under a rerun — so it is not something a contributor is asked to remember on the run that
matters.

## Module paths are internal

`plugboard/sidecar`, `plugboard/terminator`, `plugboard/conformance`. Nothing here is published and no
`go get` resolves them, so a host-shaped path would be a claim about a repository that has no remote
today. When one exists the paths change in one edit per module; until then, a path implying an owner
nobody has stated is the kind of confident unsourced detail this repository removes elsewhere.

## The constructs that are refused

Not restated here — each is [its own banned pattern](../banned-patterns/) with the defect it prevents
and its citation. The three that bite Go specifically:
[headers as a map](../banned-patterns/headers-as-a-map.md) — `map[string]string` over header fields,
with `Set-Cookie` as the case that proves it;
[a proxied body accumulated before it is emitted](../banned-patterns/read-all-on-a-proxied-body.md) —
`io.ReadAll` on a body in transit; and
[an unbounded accumulator](../banned-patterns/unbounded-accumulator.md).

`gorilla/websocket` is not used: it is archived, and message-level where the contract needs frame-level
fidelity ([topology](../../how/topology.md)).

## What is deliberately absent

No dependency is added to a module before the code that needs it. The three modules declare none today
and build with the standard library alone, which is why `go build` needs no network on a clean clone.
The contract's generated codecs arrive with [section 11](../../../openspec/changes/rebuild-plugboard/tasks.md)
and bring the first of them.
