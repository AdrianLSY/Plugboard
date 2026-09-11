---
type: banned-pattern
status: planned
authority: rationale
---

# Nothing in the application's request pipeline touches mount-destined traffic

<a id="middleware-on-proxied-traffic"></a>

**Gate:** planned — the single-pipeline structural test of rebuild-plugboard task 35.1, with the
method-rewriting removal of task 45.2 and the exemption bound of
[task 51.3](../../../openspec/changes/rebuild-plugboard/tasks.md)

Prohibited on the proxied path: body parsers, method override, `HEAD` folding, content negotiation
(`:accepts`), session, and cross-site protection. One pipeline carries mount-destined traffic and it
contains none of those stages; the proxy's own endpoints keep the ordinary processing they need.

## Why

This is the defect that made the previous attempt not work. `endpoint.ex:118` ran
`plug(PlugboardWeb.Plugs.Parsers)` before the router at `:134`; `parsers.ex:31` declared
`pass: ["*/*"]` with no `:body_reader`, so the parser consumed the body and cached nothing;
`proxy_controller.ex:250` then read an already-consumed body and `proxy_controller.ex:302` forwarded
`""`. Every `POST` body a parser claimed was dropped — the two elementary obligations of a reverse
proxy, and 27,000 lines of tests never noticed
([the audit](../../history/reference-audit.md)).

Content negotiation did the same thing to whole content types: the `/call` pipeline had deliberately
removed `:accepts`, and the domain-affinity pipeline — the one custom domains use — kept it
(`router.ex:157`). One pipeline, or the two drift.

The test that should have caught it, `proxy_controller_test.exs:835`, is named *"correctly passes
request payload to telephone"*, uses `GET`, and asserts only on `payload["method"]`. Hence the
first test of the rebuild is an octet-digest `POST` written before the proxy exists.

## Related

- [The method token passes through unread](method-allowlists.md) — override and `HEAD` folding.
- [A proxied body is emitted as it arrives](read-all-on-a-proxied-body.md).
