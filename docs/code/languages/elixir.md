---
type: guide
status: current
authority: rationale
---

# Elixir conventions

Elixir holds one component: [`proxy/`](../../../proxy/README.md), the application the operator runs.
Which languages appear here is [keyed on tracked source](../rules/language-conventions-keyed-on-source.md),
so this note arrived with the mix project and not before.

Why Elixir is [D4](../../decisions/d04-runtime.md), and the reversal recorded there is worth reading
before re-litigating it: the premise that originally forced a different runtime turned out to be
fabricated.

## Five tools, and the reference invoked none of them

`mix compile --warnings-as-errors`, `mix format --check-formatted`, `mix credo --strict`,
`mix dialyzer`, `mix sobelow --exit` and `mix deps.audit` — all reachable from `make -C proxy lint`,
which holds them in [one copy](../../../ci/make/elixir.mk).

The prior art declared `credo` as a dependency and never ran it, and the component terminating
untrusted traffic had no format check, no Dialyzer and no dependency audit at all
([reference audit](../../history/reference-audit.md), `docs/history/reference-audit.md:253`). A
declared tool nobody invokes reads in review as instrumentation and is none — which is why every
target here refuses when `mix` is absent instead of skipping.

## The plural flag

`--warnings-as-errors`. The prior art's local guardrail ran `--warning-as-errors` — singular,
therefore silently inert — while CI ran the correct spelling, for months
([reference audit](../../history/reference-audit.md)). It is set in `mix.exs` as well as on the
command line, so the two invocations cannot disagree about it.

## No Phoenix endpoint, and no middleware on proxied traffic

[D5](../../decisions/d05-pipeline-before-middleware.md). Proxied traffic terminates before any
application middleware: no body parser, no method override, no HEAD folding, no content negotiation,
no session, no CSRF. This is not a preference about layering — `Plug.Parsers` consuming request bodies
before the proxy read them is the direct cause of the prior art's worst defect, and it broke GraphQL
and JSON-RPC through the endpoint pipeline rather than through anything protocol-specific.

The skeleton therefore has no endpoint at all. One arrives when the dedicated pipeline does, not as a
default stack something is later carved out of.

## The constructs that are refused

Not restated here — each is [its own banned pattern](../banned-patterns/) with the defect it prevents
and its citation. The ones that bite Elixir specifically:
[headers as a map](../banned-patterns/headers-as-a-map.md) — `Map.new` or `Enum.into(…, %{})` over
header fields, with `Set-Cookie` as the case that proves it;
[a term rendering on the wire](../banned-patterns/inspect-on-a-wire-payload.md) — `inspect/1` on a
payload, which no client can branch on; and
[an unbounded accumulator](../banned-patterns/unbounded-accumulator.md), against a code base that had
exactly one bounded queue in twenty thousand lines.

Two more are checklist items rather than notes, because they are shapes rather than constructs: a
monitoring `GenServer` started without `trap_exit`, and `with` in a controller action with no `else`.
Both are [blocking objections](../reviewing.md#blocking-objections).

## What is deliberately absent

No runtime dependency. The four in `mix.exs` are quality tools, `only: [:dev, :test]` and
`runtime: false`. A dependency chosen before the code that needs it is a dependency chosen without a
reason, and the contract is frozen first.
