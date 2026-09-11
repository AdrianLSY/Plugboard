---
type: essay
status: current
authority: rationale
---

# Carry-forward

Things the reference got **right**, with citations. Ported deliberately rather than rediscovered by
breaking production.

All citations are `reference/Plugboard` at `6756a07` and `reference/Telephone` at `9ccba86`, relative
to each component root.

**How to use this document.** Before implementing anything in these areas, read the cited code. The
value is often not the code but the *reason*, and several of these reasons are recorded nowhere in the
reference itself.

**The prior art is not in this repository.** `reference/` is gitignored and absent, so nothing below
is checkable until both trees are on disk at those two revisions. A line number resolved against any
other revision is not the line this note cites.

## Citing one item

Fifty items, and every one of them carries an explicit anchor derived from its subject rather than
from its position, so a citation survives an edit to the prose around it —
`docs/history/carry-forward.md#terminal-mount-invariant` still lands on the right item after this
note is rewritten around it.

It stays one note deliberately. Nothing cites an item individually yet, because the tasks that port
them have not run, and fifty separate notes would each need an inbound link to be reachable — the
only links available being fifty index entries written to satisfy a gate rather than to help anyone.
So the list keeps its anchors, and an item is split into a note of its own the first time a task
cites it: the split becomes cheap exactly when it becomes useful. That is `RDV7`
([design](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/design.md#rdv7-banned-patterns-are-atomic-carry-forward-is-not)),
and it is the opposite of the treatment the banned patterns get, because those are citation targets
already.

**What counts as an item, so the count is checkable.** One portable unit: a subsection below, one
bullet in a bullet-only section, the do-not-port ruling, or the closing configuration question. The
bullets that supply an item's *evidence* — two mount triggers, three reconciliation decisions, five
partial-index bullets, ten in all — are not items of their own and carry no anchor: an anchor on
evidence detached from the claim it supports is the unstable kind. Fifty items plus those ten
evidence bullets are the "about sixty" `RDV7` counts.

## Where behaviour is owned

This note is orientation, layer 4 of the precedence order, and it states no behaviour (`RDV8`). Three
items describe behaviour a specification now owns; the specification wins on every detail, and what
survives here is why the item is worth porting at all.

| Item | Behaviour owned by |
|---|---|
| [The terminal-mount invariant](#terminal-mount-invariant) | [`routing/mount-points`](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md) — mount points are terminal, enforced from both directions, and the matching rule that needs no tie-break |
| [The one bounded buffer](#bounded-websocket-frame-buffer) | [`proxy/websocket`](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md) — pre-join buffering bounded on both frames and octets, with the bound that was reached recorded |
| [A typed error-reason vocabulary](#typed-error-reason-vocabulary) | [`tunnel/wire-contract`](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md) — errors are machine-readable |

## Anchor index

**The one that would most likely be lost**

1. [The terminal-mount invariant, and its coupling to the lookup algorithm](#terminal-mount-invariant)

**Correctness patterns**

2. [Per-request `Task.async` isolation](#per-request-task-async-isolation)
3. [Insert-before-evict reconciliation, jittered, deferred at boot](#insert-before-evict-reconciliation)
4. [Reads go straight to ETS, tables `:protected`](#ets-reads-protected-tables)
5. [The one bounded buffer in the system](#bounded-websocket-frame-buffer)
6. [Failure fan-out on disconnect](#failure-fan-out-on-disconnect)

**Data model**

7. [Partial unique indexes gated on the soft-delete column](#partial-unique-indexes-soft-delete)
8. [Named database `CHECK` constraints as the backstop](#named-check-constraints)
9. [`accounts.ex` as the quality baseline](#accounts-ex-quality-baseline)

**Security**

10. [Boot-time secret validation](#boot-time-secret-validation)
11. [Purpose-scoped key derivation with a version suffix](#purpose-scoped-key-derivation)
12. [Changeset-level SSRF validation](#changeset-level-ssrf-validation)
13. [Header denylist for hook targets](#header-denylist-hook-targets)
14. [Correct XSS escaping on reflected input](#xss-escaping-reflected-input)
15. [An explicitly documented security omission](#documented-security-omission)

**The sidecar's small correct pieces**

16. [`validateBackendPath`](#validate-backend-path)
17. [Token-store crypto](#token-store-crypto)
18. [Hop-by-hop stripping and subprotocol negotiation](#hop-by-hop-stripping-subprotocol-negotiation)
19. [Jitter, applied in both places](#jitter-both-sides)
20. [Response-body closing discipline](#response-body-closing-discipline)
21. [Sentinel errors and a real health server](#sentinel-errors-health-server)
22. [`cmd/telephone/main.go` in full](#telephone-main-entrypoint)
23. [Build provenance](#build-provenance)

**Protocol semantics worth preserving**

24. [String opcode names on the wire](#string-opcode-names)
25. [Base64 for WebSocket frame data, both directions, unconditionally](#base64-frame-payloads)
26. [The close-code vocabulary](#close-code-vocabulary)
27. [A typed error-reason vocabulary](#typed-error-reason-vocabulary)
28. [The hook merge contract](#hook-merge-contract)
29. [The hook cycle check is a real graph traversal](#hook-cycle-graph-traversal)

**Tests worth porting**

30. [`telephone_socket_test.exs` in full](#test-telephone-socket)
31. [`telephone_tokens_test.exs`, the forged-JWT case](#test-telephone-tokens)
32. [`paths_test.exs`, the constraint and rollback block](#test-paths-constraints)
33. [`hook_store_test.exs`, projection self-repair](#test-hook-store-self-repair)
34. [`rate_limiter_test.exs`, window expiry and true ETS concurrency](#test-rate-limiter-ets)
35. [`validate_path_test.exs`, both sides of every boundary](#test-validate-path-boundaries)
36. [`telephone_registry_test.exs`, cleanup on owner death](#test-telephone-registry-cleanup)
37. [`domain_affinity_test.exs`, changeset negatives](#test-domain-affinity-negatives)
38. [The owner/maintainer/viewer/no-access matrix](#test-authorization-matrix)
39. [`websocket_proxy_plug_test.exs`, one test per excluded prefix](#test-websocket-proxy-plug-exclusions)
40. [The LiveView selector convention](#test-liveview-selector-convention)
41. [`websocket_test.go`'s real-server pattern](#test-websocket-real-server)
42. [`config_test.go`, every required variable named](#test-config-missing-variables)
43. [`token_test.go`, readers against writers under `-race`](#test-token-concurrency)
44. [`client_test.go`, the pinned Phoenix contract](#test-client-phoenix-contract)

**Tooling worth porting**

45. [`make test` runs `-race` by default, with the hooks](#tooling-make-test-race)
46. [A 30-linter `golangci` v2 config not defeated by config](#tooling-golangci-config)
47. [`security.yml`, including the weekly cron](#tooling-security-workflow)
48. [Multi-stage `Dockerfile`, non-root, pinned, no libc](#tooling-container-image)
49. [Do not port: `dependabot-automerge.yml`](#do-not-port-dependabot-automerge)

**The configuration philosophy question**

50. [The configuration philosophy question](#explicit-configuration-policy)

---

## The one that would most likely be lost

<a id="terminal-mount-invariant"></a>
### The terminal-mount invariant, and its coupling to the lookup algorithm

Two complementary Postgres triggers, each taking `FOR UPDATE` on the parent before checking, enforce
"a mount point has no children" from **both** directions under concurrency:

- `20251031092344_create_paths_table.exs:96-107` — `prevent_child_under_mount()`, on
  `BEFORE INSERT OR UPDATE OF parent_id` (`:121-127`)
- `:131-152` — `prevent_mount_when_has_children()`, on `BEFORE UPDATE OF mount_point` (`:154-160`),
  counting live children with `WHERE parent_id = NEW.id AND deleted_at IS NULL`

**The coupling nobody wrote down:** that invariant is *what makes* the routing algorithm correct.
Because mounts are terminal, `/a/b` being a mount guarantees no `/a/b/c` mount exists — so
strip-one-segment-and-retry terminates at the unique correct answer, with **no trie, no sort, and no
tie-break rule**. It is a data-model decision made to render the hot path trivial.

Port the invariant *and* the reason. Add the contended test the suite never had — every "concurrent"
test in the reference runs on one sandbox connection, so these `FOR UPDATE` locks have never actually
been contended.

Related: `mount_store.ex:84-99` with `do_match/2` at `:215-240` — normalise, exact ETS lookup, strip a
trailing segment, retry. O(depth) lookups with no scan, computing the forwarded path with
`String.replace_prefix/3`, wrapped in a telemetry span. *(Note: the README's headline claim of "O(1)
path matching" is wrong — it is O(depth). Fix the claim, keep the algorithm.)*

---

## Correctness patterns

<a id="per-request-task-async-isolation"></a>
### Per-request `Task.async` isolation

`proxy_controller.ex:310-315`. The rendezvous runs in a fresh process per request, so `self()` is a
private mailbox and **a late reply arriving after a timeout structurally cannot leak into another
request**. Backed by a selective `receive do {:proxy_res, ^request_id, response}` at `:419`.

This is genuinely good design and was the single biggest correctness worry going in. *Carry the
property, not the mechanism* — D7's stream ids subsume the correlation id, but the guarantee must
survive.

Contrast `executor.ex:421-441`, where the hooks executor does the same rendezvous with a bare `receive`
**in the request process**, so undelivered late replies accumulate permanently in a keep-alive
connection's mailbox. Same idea, one place safe and one place not — which is the argument for one
implementation.

<a id="insert-before-evict-reconciliation"></a>
### Insert-before-evict reconciliation, jittered, deferred at boot

Three deliberate decisions in one place:

- `mount_store.ex:414-430` (and the mirrored domain version at `:520-536`) — insert the whole new
  dataset **first**, then delete keys absent from it, so a concurrent reader never sees an empty table,
  only a superset. The comment at `:414-415` shows it was intentional.
- `:487-494` — `jitter = :rand.uniform(div(base_interval, 10))`, explicitly to avoid a cluster-wide
  thundering herd.
- `:309` — deferred initial load via `{:continue, :load_initial_data}`, so the supervisor is never
  blocked on the database at boot.

Keep all three. **Scope the query** — `:402-412` has no tenant scoping, so one tenant's change costs
every tenant O(all mounts). Both auditors who praised the ordering failed to ask about the scope.

<a id="ets-reads-protected-tables"></a>
### Reads go straight to ETS, tables `:protected`

`mount_store.ex:85-99` and `:169-181` call `:ets.lookup` **from the caller process** — no GenServer hop
on the hot path — with tables `:protected` (`:293-305`) so only the owning process writes. Correct shape
for a routing cache; avoids a single-process bottleneck.

<a id="bounded-websocket-frame-buffer"></a>
### The one bounded buffer in the system

`proxy_handler.ex:34-35` and `:107-136`. Pre-connect WebSocket frame buffering bounded on **both** axes
(`@max_buffer_frames 100`, `@max_buffer_bytes 1_048_576`), emitting a distinguishing telemetry reason
(`:frame_count` vs `:byte_size`) and closing with WebSocket code 1009 on overflow.

Bounded-buffer-with-explicit-failure is exactly right. **Nothing else in the codebase bounds a queue.**
Generalise this.

<a id="failure-fan-out-on-disconnect"></a>
### Failure fan-out on disconnect

`telephone_channel.ex:417-452` — `terminate/2` unregisters, then sends
`{:proxy_error, request_id, :telephone_disconnected}` to **every** waiting caller (`:426-428`), notifies
every WebSocket handler, and emits telemetry carrying `pending_requests` and `ws_connections` counts.
Callers fail fast instead of hanging to timeout.

Keep it, and trap exits so it always runs. Also carry `telephone_channel.ex:344`
`Process.monitor(handler_pid)` with its `:DOWN` clause at `:395-414` pushing `ws_close` code 1001 — the
WebSocket side monitors what the HTTP side does not. Apply the same monitor discipline everywhere.

---

## Data model

<a id="partial-unique-indexes-soft-delete"></a>
### Partial unique indexes gated on the soft-delete column

Applied consistently to **all seven** soft-deletable unique constraints, so a soft-deleted row can never
block a new one:

- `20251031092344_create_paths_table.exs:21-34` — `paths_unique_sibling_path`, `paths_unique_full_path`
  (`WHERE deleted_at IS NULL`)
- `20251117075257:15-18` — `domain_affinities_unique_domain`
- `20251118141933:39-50` — `hooks_unique_execution_order`, `hooks_path_order_index`
- `20251102140221:22-27` — `telephone_tokens_unique_hash` (`WHERE revoked_at IS NULL`)
- `20251104065912:22-33` — `service_accounts_unique_api_key`, `service_accounts_unique_name_per_user`

Make this the rule.

<a id="named-check-constraints"></a>
### Named database `CHECK` constraints as the backstop

`path_no_slashes`, `path_valid_chars`, `path_length` (`20251031092344:41-54`); `valid_role`
(`20251101135346:25-29`); `valid_domain_format` (`20251117075257:24-28`); `valid_target_type`,
`valid_target_config`, `valid_timeout`, `valid_execution_order` (`20251118141933:53-82`).

**Named** constraints Ecto can map back to changeset errors — unlike the `RAISE`-based triggers, which
surface as unhandled exceptions because they set `ERRCODE` without `CONSTRAINT`
(`20251031092344:142-146`). The right model: named DB constraints as the source of truth, declared once
on the changeset. Fix the triggers to name their constraints, or replace them with named constraints.

<a id="accounts-ex-quality-baseline"></a>
### `accounts.ex` as the quality baseline

297 lines of untouched, idiomatic `phx.gen.auth` (magic-link flavour). Single responsibility, no
duplicated projection, no bolted-on second resource. **It is the cleanest context in the tree**, and the
hand-written contexts drifted away from it. Carry it forward unchanged and generate the resource
contexts to the same shape.

---

## Security

<a id="boot-time-secret-validation"></a>
### Boot-time secret validation

`application.ex:64-97`. Runs **before** the supervision tree starts and rejects three distinct failures:
a nil `SECRET_KEY_BASE` (`:68`), one shorter than 64 bytes *with the actual size in the message*
(`:74-79`), and — the thoughtful one — **the literal dev default secret being used in production**
(`:81-86`, constant at `:96`).

Uncredited by all seven audit dimensions. Fail-fast on credential misconfiguration is the right default.
Extend it to cover the salts that currently only fail deep inside `runtime.exs`.

<a id="purpose-scoped-key-derivation"></a>
### Purpose-scoped key derivation with a version suffix

`crypto.ex:74-79` — `:crypto.mac(:hmac, :sha256, secret_key_base, "plugboard_#{purpose}_v1")`, with the
rationale recorded at `:59-61`: compromise of the JWT key must not compromise other uses of
`secret_key_base`. **Rotation was designed in.** Keep the scheme and the `_v1`.

Caveat: `Crypto` has **no test file**, and `doctest` appears nowhere in the repository, so its six
`iex>` examples are decorative. Test the primitive directly. Delete `Crypto.legacy_hash/1` or keep it
with a migration test — shipping a dead crypto function is worse than either.

<a id="changeset-level-ssrf-validation"></a>
### Changeset-level SSRF validation

`hook.ex:192-211` requires an http/https scheme and non-empty host; `:247-257` matches **parsed address
tuples** — `{10,_,_,_}`, `{172,b,_,_} when b >= 16 and b <= 31`, `{169,254,_,_}`, `{0,0,0,0}`,
`{0,0,0,0,0,0,0,1}`, `{0xFE80,...}` — instead of regexing strings. Carries a metadata-endpoint list at
`:25-38` (AWS, `metadata.google.internal`, Alibaba `100.100.100.200`, ECS `169.254.170.2`).

**Materially better than the executor's runtime check**; consolidate on this one. Add DNS resolution,
post-redirect re-validation, IPv4-mapped IPv6, and `fc00::/7`. And note SSRF blocking is disabled
suite-wide in the reference's test config with zero tests — see
[the audit](reference-audit.md).

<a id="header-denylist-hook-targets"></a>
### Header denylist for hook targets

`hook.ex:299-339` refuses to forward `cookie`, `set-cookie`, `authorization`, `x-api-key`,
`x-auth-token`, `proxy-authorization`, `x-forwarded-for`, `x-real-ip` (`@blocked_headers`, `:49-58`),
with a message naming the offenders. Thoughtful secure default. Enforce at both write time and send time
from **one** module.

<a id="xss-escaping-reflected-input"></a>
### Correct XSS escaping on reflected input

`http_error.ex:365` and `:390` route both `reason` and formatted `details` through
`html_escape_text/1`, which (`:399-407`) replaces `&` **first**, then `<`, `>`, `"`, `'` — the correct
order, so no double-unescaping hole. Load-bearing, because `details` carries attacker-controlled values
(`proxy_controller.ex:126`, `:170`). Tested properly at `http_error_test.exs:68-80`, asserting both
`refute =~ "<script>"` and `assert =~ "&lt;script&gt;"`.

<a id="documented-security-omission"></a>
### An explicitly documented security omission

`router.ex:47-49`:

> CSRF protection is intentionally omitted here because this is a reverse proxy. Proxied requests
> originate from external clients and should not require CSRF tokens.

A control deliberately dropped, with the reasoning next to the code. **This is the documentation
standard the other 148 KB of prose never met.** Carry the habit, not just the comment.

---

## The sidecar's small correct pieces

<a id="validate-backend-path"></a>
### `validateBackendPath`

`telephone.go:656-697`. A genuinely layered traversal guard: rejects non-slash-prefixed paths,
protocol-relative `//host`, any scheme, any host, and post-`Clean` escapes, while preserving the query
string. Real table-driven coverage at `telephone_test.go:792-921`, and correctly reused by the WebSocket
path (`websocket.go:281`). **Port close to verbatim.**

<a id="token-store-crypto"></a>
### Token-store crypto

`token_store.go:73-79`, `:139-148`. PBKDF2-SHA256 at 100,000 iterations for key derivation; AES-256-GCM
with a fresh nonce per record prepended via `gcm.Seal(nonce, nonce, ...)`; base64 for storage; key
zeroed on `Close` (`:325-329`). Textbook-correct authenticated encryption with no rolled crypto.

Keep the whole scheme. One fix: `Close` mutates the key without holding `ts.mu`.

Its tests are the only ones in either repo that prove a *security* property rather than a happy path:
`token_store_test.go:561-599` `TestTokenStoreWrongSecretKey` and `:159-188`
`TestTokenStoreDecryptInvalidData`.

<a id="hop-by-hop-stripping-subprotocol-negotiation"></a>
### Hop-by-hop stripping and subprotocol negotiation

`manager.go:19-32` — a correct lowercase-keyed denylist for `sec-websocket-key`/`-version`/
`-extensions`, `upgrade`, `connection`. `manager.go:96-115` and `:133` — comma-separated
`sec-websocket-protocol` parsed into `dialer.Subprotocols`, returning `conn.Subprotocol()` rather than
forwarding raw. Covered by `manager_test.go:199`. Small, correct, easy to get wrong on a rewrite.

<a id="jitter-both-sides"></a>
### Jitter, applied in both places

`reconnect.go:234-238` — ±25% on reconnect backoff. `telephone.go:451-456` — ±5% on token refresh. Both
drawn from `crypto/rand` via `secureRandomDuration` (`telephone.go:43-60`), which correctly returns 0
for a non-positive bound. Combined with the `reconnectFlag` guard (`reconnect.go:16-29`) serialising
concurrent reconnect attempts, the thundering-herd defence is present and deliberate.

Defeated only by an int64 overflow in the exponent (`reconnect.go:226` — at ~attempt 35, backoff
collapses to `InitialBackoff` forever, turning a long outage into a 1-per-second hammer). One-line fix;
keep the design.

<a id="response-body-closing-discipline"></a>
### Response-body closing discipline

Genuinely complete, including the easily-missed error-case handshake responses: `client.go:165-168`
(closes before the `err` check), `manager.go:118-122` and `:418-422`, `telephone.go:820-824`.
`bodyclose` compliance here is real, not linter-shaped.

<a id="sentinel-errors-health-server"></a>
### Sentinel errors and a real health server

`errors.go:6-25` with `errors.Is` dispatch at `reconnect.go:172` and `:204`; consistent `%w` wrapping so
cause chains survive; `health.go:50-53` sets **all four** timeouts and serves `/health`, `/ready`,
`/live` plus Kubernetes-style aliases.

<a id="telephone-main-entrypoint"></a>
### `cmd/telephone/main.go` in full

83 lines: flag parsing, optional `.env` behind an `os.Stat` guard (`:33`), **distinct non-zero exits**
for config, construction and start failures (`:47`, `:59`, `:65`), `SIGINT`/`SIGTERM` via a buffered
channel (`:68-69`), and a graceful `tel.Stop()` whose error is logged rather than swallowed (`:78-80`).
A correct, boring entrypoint. Match this shape on both sides.

<a id="build-provenance"></a>
### Build provenance

`Makefile:6-7` — `VERSION ?= $(shell git describe --tags --always --dirty)` feeding
`-X main.version=$(VERSION)`, consumed at `main.go:30` and logged at startup; the same ldflags repeated
for all eight release targets. **An operator can tell which build is running.** The proxy has no
equivalent — do this on both sides.

---

## Protocol semantics worth preserving

- <a id="string-opcode-names"></a>**String opcode names on the wire** — `"text"`/`"binary"`/`"ping"`/`"pong"` rather than numeric
  RFC 6455 opcodes. Defined once per side (`types.go:8-11`, `proxy_handler.ex:278-287`) and they agree
  exactly. Far more debuggable in a text protocol than integers.
- <a id="base64-frame-payloads"></a>**Base64 for WebSocket frame data, both directions, unconditionally** (`telephone_channel.ex:459`,
  `manager.go:377`). Correct encoding discipline — **extend it to HTTP bodies rather than abandon it.**
- <a id="close-code-vocabulary"></a>**The close-code vocabulary** — 1000 client-disconnected, 1001 handler-terminated /
  telephone-disconnected, 1009 buffer overflow, 1014 backend-unreachable-or-timeout
  (`proxy_handler.ex:122`, `:131`, `:195`, `:207`, `:222`, `:236`; `telephone_channel.ex:408`). Carry
  the mapping, **add validation**: `proxy_handler.ex:195` echoes whatever integer arrived in `ws_closed`
  straight to the browser with no range check.
- <a id="typed-error-reason-vocabulary"></a>**A typed error-reason vocabulary** — `connection_refused`, `connection_timeout`, `invalid_upgrade`,
  `backend_error`, `invalid_frame_data`, `invalid_path` (`types.go:63-76`). Stable machine-readable
  codes. Contrast the refresh-token error path, which ships `inspect(reason)`
  (`telephone_channel.ex:106`) — an Elixir term rendering no client can branch on. **Standardise on the
  typed style everywhere.**
- <a id="hook-merge-contract"></a>**The hook merge contract** — sequential by `execution_order` with a DB-level uniqueness guarantee on
  that order, root-level `Map.merge` where the hook wins on collision, stated in the moduledoc
  (`executor.ex:5-9`) and implemented at `:120-131`. Keep the contract; add **namespacing** (a hook can
  currently overwrite any client field, and a later hook any earlier hook's field, with no record) and a
  size bound on the merged result.
- <a id="hook-cycle-graph-traversal"></a>**The hook cycle check is a real graph traversal**, not a self-reference check
  (`hooks.ex:243-272`) — a `MapSet` of visited paths recursing through each mount-point hook's target,
  so indirect A→B→A is detected. Two fixes rather than a discard: the visited set is not threaded across
  sibling branches (`:265` drops the recursive result), so diamond graphs are re-traversed; and it takes
  no locks, so two concurrent creates of A→B and B→A can both pass under `READ COMMITTED`.

---

## Tests worth porting

Named individually because test *volume* is not evidence — see [the audit](reference-audit.md).

- <a id="test-telephone-socket"></a>**`telephone_socket_test.exs` in full.** 22 tests over invalid signature, malformed, missing, nil and
  non-string tokens, expiry, revocation, deleted path, non-mount path, socket-id uniqueness (`:174`,
  `:196`), and assign minimality — `refute Map.has_key?(assigns, :token_hash)` (`:285`). **The model the
  rest of the suite should have followed.**
- <a id="test-telephone-tokens"></a>**`telephone_tokens_test.exs`**, especially the forged-JWT case (`:212-231`) which signs with the real
  derived secret to reach the not-in-database path, and the deliberate indistinguishability of expired vs
  revoked (`:171`, `:186`) — a security decision encoded in a test.
- <a id="test-paths-constraints"></a>**`paths_test.exs:827-1098`** — CHECK constraints, both unique indexes including that soft-deleted rows
  do not block reuse (`:1042`), FK cascade vs RESTRICT (`:941-999`), and the two rollback tests (`:304`,
  `:322`) asserting no orphaned `user_paths` after a failed create.
- <a id="test-hook-store-self-repair"></a>**`hook_store_test.exs:183-202`** — the *only* test in the codebase that simulates an external DB change
  (`Repo.delete_all`) and asserts the projection repairs itself. **Make this the template for every
  cache.**
- <a id="test-rate-limiter-ets"></a>**`rate_limiter_test.exs:189-203`** (window expiry via ETS timestamp rewrite) and **`:157-176`** (true
  ETS concurrency with an exact 5-ok/5-denied split).
- <a id="test-validate-path-boundaries"></a>**`validate_path_test.exs`** — both sides of every boundary: 51 segments rejected vs exactly 50
  accepted (`:86`, `:95`), 256 bytes rejected vs exactly 255 (`:77`, `:104`).
- <a id="test-telephone-registry-cleanup"></a>**`telephone_registry_test.exs:330-356`** — registration is cleaned up when the owning process dies.
  Keep regardless of what replaces Horde.
- <a id="test-domain-affinity-negatives"></a>**`domain_affinity_test.exs:81-165`** — changeset negatives: wildcard in the middle, missing dot after
  the asterisk, leading/trailing dot, non-mount target, deleted target. Dense, cheap, each mapping to a
  real rejection.
- <a id="test-authorization-matrix"></a>**The owner/maintainer/viewer/no-access matrix** in `hook_controller_test.exs` (`:35`, `:72`, `:91`,
  `:110`), `telephone_token_controller_test.exs` (`:28`, `:55`, `:73`, `:87`) and
  `domain_affinity_controller_test.exs` (`:25`, `:44`, `:61`, `:78`) — including the distinction between
  the two different 403 messages (`hook_controller_test.exs:107` vs `:124`).
- <a id="test-websocket-proxy-plug-exclusions"></a>**`websocket_proxy_plug_test.exs:56-135`** — one pass-through test per excluded prefix, all eight,
  including `/telephone` (`:76`), which is what stops the sidecar's own socket being proxied through
  itself.
- <a id="test-liveview-selector-convention"></a>**The LiveView selector convention** — address elements by `phx-click`/`phx-value-id` (e.g.
  `reference/Plugboard/test/plugboard_web/live/path_tokens_live/index_test.exs:670`) and assert on flash text plus a database re-read (`:254-257`),
  never on CSS classes or DOM structure. **Zero markup assertions across 2,400 lines** — so these tests
  survive a redesign.
- <a id="test-websocket-real-server"></a>**`websocket_test.go`'s real-server pattern** — `createWSTestServer` (`:28-42`) using gorilla's
  `Upgrader` against `httptest`, and the four tests asserting actual bytes crossing the boundary in both
  directions (`:268`, `:594`, `:653`, `:236`). **Extend this to the HTTP tunnel, which has no
  equivalent.** Its assertion style — literal wire keys, base64-decoding the payload (`:527-541`) — is
  the one place in either repo where the contract is actually pinned down. Make it mandatory for every
  event.
- <a id="test-config-missing-variables"></a>**`config_test.go:266-322`** `TestLoadFromEnvMissingVariables` — list-driven over all 16 required vars,
  asserting each error message names its own variable.
- <a id="test-token-concurrency"></a>**`token_test.go:135-263`** — 10 readers × 100 iterations against 5 writers × 50. The only tests in the
  Go suite that give `-race` anything to find. Keep them with the `tokenMu` RWMutex discipline they cover
  (`telephone.go:332-347`).
- <a id="test-client-phoenix-contract"></a>**`client_test.go:527`, `:590`** — pin the exact Phoenix contract `?token=…&vsn=2.0.0` including the
  existing-query-params case, and the invariant that logged URLs never contain the JWT.

---

## Tooling worth porting

From the sidecar, which had the better harness:

- <a id="tooling-make-test-race"></a>`make test` runs `-race` **by default** (`Makefile:45`); `precommit: fmt vet lint test` (`:103`);
  installable pre-commit and pre-push hooks (`:106-116`) where pre-push blocks pushes to `main` on lint
  or test failure.
- <a id="tooling-golangci-config"></a>A 30-linter `golangci` v2 config with `govet` enable-all, `errcheck` `check-type-assertions` **plus**
  `check-blank`, and `gocyclo` at 15. Exclusions are narrow and defensible (bin/vendor paths;
  `gocyclo`/`errcheck`/`gosec` off for tests only) — **the linter is not defeated by config.** It *is*
  softened by 28 inline `//nolint:errcheck` in production code and two `//nolint:gocyclo` that suppress
  the complexity gate rather than splitting the function. Fix those rather than dropping the gate.
- <a id="tooling-security-workflow"></a>`security.yml` as the template the proxy needs: `govulncheck` (`:37-59`) plus Trivy at
  `severity: HIGH,CRITICAL` with `exit-code: 1` (`:71-79`), on push, on PR, **and on a weekly cron**
  (`:24-26`) so newly disclosed CVEs surface without a code change. Apply it to the proxy, which has the
  larger attack surface and currently has nothing.
- <a id="tooling-container-image"></a>Multi-stage `Dockerfile`, `CGO_ENABLED=0`, non-root UID 1000, pinned `alpine:3.23`, pure-Go SQLite so
  there is no libc in the runtime image.

<a id="do-not-port-dependabot-automerge"></a>**Do not port:** `dependabot-automerge.yml`. It auto-approves and merges every Dependabot PR with no
`update-type` gate — `fetch-metadata` is invoked and its output never referenced — over a suite with no
tests on `reconnect.go`. Gate on `version-update:semver-patch`, and never auto-advance a pointer that
encodes a wire protocol.

---

<a id="explicit-configuration-policy"></a>
## The configuration philosophy question

The sidecar's `config.go:117-239` enforces *"all configuration must be explicitly set — no defaults are
used"*, with `parsePositiveInt` validation and a list-driven test over all 16 required variables.
Contrast the proxy's `runtime.exs:202` style —
`System.get_env("MOUNT_STORE_RECONCILE_INTERVAL") || "300000"` — which silently accepts a missing value.

**For infrastructure carrying production traffic the sidecar's policy is correct**: a silently-defaulted
`MAX_RESPONSE_SIZE` or `REQUEST_TIMEOUT` is worse than a startup failure. Adopt it on both sides, with
two amendments the reference gets wrong:

1. **Report every missing variable at once**, not the first one. Sixteen sequential restarts is hostile.
2. **Ship a complete `.env.example` and generate the Dockerfile `ENV` block from the same schema.** The
   reference's published sidecar image cannot boot — its `ENV` block sets only `PLUGBOARD_URL`,
   `BACKEND_HOST` and `BACKEND_PORT`, so it dies on `BACKEND_SCHEME`. The policy is right; the
   *ergonomics* of discovering what to set were never built.
