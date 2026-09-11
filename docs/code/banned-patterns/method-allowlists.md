---
type: banned-pattern
status: planned
authority: rationale
---

# The method token passes through unread and unrewritten

<a id="method-allowlists"></a>

**Gate:** planned — the method-allowlist defective counterpart of rebuild-plugboard task 15.3 and
the method-rewriting removal of
[task 45.2](../../../openspec/changes/rebuild-plugboard/tasks.md)

Prohibited: an allowlist of methods on any mount-destined route, a per-method branch that decides
whether traffic is carried at all, and any rewriting of the token — method override from a body or
query parameter, or folding `HEAD` into `GET`.

## Why

The prior attempt enumerated seven verbs in its router (`router.ex:63-69`, `:169-175`) and enforced
the same list independently in the sidecar (`telephone.go:27-35`), so WebDAV, CalDAV and CardDAV
were structurally unreachable rather than merely unimplemented
([the audit](../../history/reference-audit.md)). Two copies of an allowlist also drift: a verb added
at one end is refused at the other, and the refusal names neither.

A method token is an opaque string to a hop that is carrying traffic, so an allowlist buys nothing a
backend cannot decide for itself while removing whole protocols from reach — the case behind
*three primitives, not twelve protocols*. The fixture is a `PROPFIND`
([testing](../testing.md#conformance-fixtures-seeded-adversarially)).

## Related

- [Nothing in the application's pipeline touches mount-destined traffic](middleware-on-proxied-traffic.md)
  — method override and `HEAD` folding arrive as middleware, not as code someone wrote on purpose.
