# Carry-forward

Things the reference got **right**, with citations. Ported deliberately rather than rediscovered by
breaking production.

All citations are `reference/Plugboard` at `6756a07` and `reference/Telephone` at `9ccba86`, relative
to each component root.

**How to use this document.** Before implementing anything in these areas, read the cited code. The
value is often not the code but the *reason*, and several of these reasons are recorded nowhere in the
reference itself.

---

## The one that would most likely be lost

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

### Reads go straight to ETS, tables `:protected`

`mount_store.ex:85-99` and `:169-181` call `:ets.lookup` **from the caller process** — no GenServer hop
on the hot path — with tables `:protected` (`:293-305`) so only the owning process writes. Correct shape
for a routing cache; avoids a single-process bottleneck.

### The one bounded buffer in the system

`proxy_handler.ex:34-35` and `:107-136`. Pre-connect WebSocket frame buffering bounded on **both** axes
(`@max_buffer_frames 100`, `@max_buffer_bytes 1_048_576`), emitting a distinguishing telemetry reason
(`:frame_count` vs `:byte_size`) and closing with WebSocket code 1009 on overflow.

Bounded-buffer-with-explicit-failure is exactly right. **Nothing else in the codebase bounds a queue.**
Generalise this.

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

### Named database `CHECK` constraints as the backstop

`path_no_slashes`, `path_valid_chars`, `path_length` (`20251031092344:41-54`); `valid_role`
(`20251101135346:25-29`); `valid_domain_format` (`20251117075257:24-28`); `valid_target_type`,
`valid_target_config`, `valid_timeout`, `valid_execution_order` (`20251118141933:53-82`).

**Named** constraints Ecto can map back to changeset errors — unlike the `RAISE`-based triggers, which
surface as unhandled exceptions because they set `ERRCODE` without `CONSTRAINT`
(`20251031092344:142-146`). The right model: named DB constraints as the source of truth, declared once
on the changeset. Fix the triggers to name their constraints, or replace them with named constraints.

### `accounts.ex` as the quality baseline

297 lines of untouched, idiomatic `phx.gen.auth` (magic-link flavour). Single responsibility, no
duplicated projection, no bolted-on second resource. **It is the cleanest context in the tree**, and the
hand-written contexts drifted away from it. Carry it forward unchanged and generate the resource
contexts to the same shape.

---

## Security

### Boot-time secret validation

`application.ex:64-97`. Runs **before** the supervision tree starts and rejects three distinct failures:
a nil `SECRET_KEY_BASE` (`:68`), one shorter than 64 bytes *with the actual size in the message*
(`:74-79`), and — the thoughtful one — **the literal dev default secret being used in production**
(`:81-86`, constant at `:96`).

Uncredited by all seven audit dimensions. Fail-fast on credential misconfiguration is the right default.
Extend it to cover the salts that currently only fail deep inside `runtime.exs`.

### Purpose-scoped key derivation with a version suffix

`crypto.ex:74-79` — `:crypto.mac(:hmac, :sha256, secret_key_base, "plugboard_#{purpose}_v1")`, with the
rationale recorded at `:59-61`: compromise of the JWT key must not compromise other uses of
`secret_key_base`. **Rotation was designed in.** Keep the scheme and the `_v1`.

Caveat: `Crypto` has **no test file**, and `doctest` appears nowhere in the repository, so its six
`iex>` examples are decorative. Test the primitive directly. Delete `Crypto.legacy_hash/1` or keep it
with a migration test — shipping a dead crypto function is worse than either.

### Changeset-level SSRF validation

`hook.ex:192-211` requires an http/https scheme and non-empty host; `:247-257` matches **parsed address
tuples** — `{10,_,_,_}`, `{172,b,_,_} when b >= 16 and b <= 31`, `{169,254,_,_}`, `{0,0,0,0}`,
`{0,0,0,0,0,0,0,1}`, `{0xFE80,...}` — instead of regexing strings. Carries a metadata-endpoint list at
`:25-38` (AWS, `metadata.google.internal`, Alibaba `100.100.100.200`, ECS `169.254.170.2`).

**Materially better than the executor's runtime check**; consolidate on this one. Add DNS resolution,
post-redirect re-validation, IPv4-mapped IPv6, and `fc00::/7`. And note SSRF blocking is disabled
suite-wide in the reference's test config with zero tests — see
[the audit](03-reference-audit.md).

### Header denylist for hook targets

`hook.ex:299-339` refuses to forward `cookie`, `set-cookie`, `authorization`, `x-api-key`,
`x-auth-token`, `proxy-authorization`, `x-forwarded-for`, `x-real-ip` (`@blocked_headers`, `:49-58`),
with a message naming the offenders. Thoughtful secure default. Enforce at both write time and send time
from **one** module.

### Correct XSS escaping on reflected input

`http_error.ex:365` and `:390` route both `reason` and formatted `details` through
`html_escape_text/1`, which (`:399-407`) replaces `&` **first**, then `<`, `>`, `"`, `'` — the correct
order, so no double-unescaping hole. Load-bearing, because `details` carries attacker-controlled values
(`proxy_controller.ex:126`, `:170`). Tested properly at `http_error_test.exs:68-80`, asserting both
`refute =~ "<script>"` and `assert =~ "&lt;script&gt;"`.

### An explicitly documented security omission

`router.ex:47-49`:

> CSRF protection is intentionally omitted here because this is a reverse proxy. Proxied requests
> originate from external clients and should not require CSRF tokens.

A control deliberately dropped, with the reasoning next to the code. **This is the documentation
standard the other 148 KB of prose never met.** Carry the habit, not just the comment.

---

## The sidecar's small correct pieces

### `validateBackendPath`

`telephone.go:656-697`. A genuinely layered traversal guard: rejects non-slash-prefixed paths,
protocol-relative `//host`, any scheme, any host, and post-`Clean` escapes, while preserving the query
string. Real table-driven coverage at `telephone_test.go:792-921`, and correctly reused by the WebSocket
path (`websocket.go:281`). **Port close to verbatim.**

### Token-store crypto

`token_store.go:73-79`, `:139-148`. PBKDF2-SHA256 at 100,000 iterations for key derivation; AES-256-GCM
with a fresh nonce per record prepended via `gcm.Seal(nonce, nonce, ...)`; base64 for storage; key
zeroed on `Close` (`:325-329`). Textbook-correct authenticated encryption with no rolled crypto.

Keep the whole scheme. One fix: `Close` mutates the key without holding `ts.mu`.

Its tests are the only ones in either repo that prove a *security* property rather than a happy path:
`token_store_test.go:561-599` `TestTokenStoreWrongSecretKey` and `:159-188`
`TestTokenStoreDecryptInvalidData`.

### Hop-by-hop stripping and subprotocol negotiation

`manager.go:19-32` — a correct lowercase-keyed denylist for `sec-websocket-key`/`-version`/
`-extensions`, `upgrade`, `connection`. `manager.go:96-115` and `:133` — comma-separated
`sec-websocket-protocol` parsed into `dialer.Subprotocols`, returning `conn.Subprotocol()` rather than
forwarding raw. Covered by `manager_test.go:199`. Small, correct, easy to get wrong on a rewrite.

### Jitter, applied in both places

`reconnect.go:234-238` — ±25% on reconnect backoff. `telephone.go:451-456` — ±5% on token refresh. Both
drawn from `crypto/rand` via `secureRandomDuration` (`telephone.go:43-60`), which correctly returns 0
for a non-positive bound. Combined with the `reconnectFlag` guard (`reconnect.go:16-29`) serialising
concurrent reconnect attempts, the thundering-herd defence is present and deliberate.

Defeated only by an int64 overflow in the exponent (`reconnect.go:226` — at ~attempt 35, backoff
collapses to `InitialBackoff` forever, turning a long outage into a 1-per-second hammer). One-line fix;
keep the design.

### Response-body closing discipline

Genuinely complete, including the easily-missed error-case handshake responses: `client.go:165-168`
(closes before the `err` check), `manager.go:118-122` and `:418-422`, `telephone.go:820-824`.
`bodyclose` compliance here is real, not linter-shaped.

### Sentinel errors and a real health server

`errors.go:6-25` with `errors.Is` dispatch at `reconnect.go:172` and `:204`; consistent `%w` wrapping so
cause chains survive; `health.go:50-53` sets **all four** timeouts and serves `/health`, `/ready`,
`/live` plus Kubernetes-style aliases.

### `cmd/telephone/main.go` in full

83 lines: flag parsing, optional `.env` behind an `os.Stat` guard (`:33`), **distinct non-zero exits**
for config, construction and start failures (`:47`, `:59`, `:65`), `SIGINT`/`SIGTERM` via a buffered
channel (`:68-69`), and a graceful `tel.Stop()` whose error is logged rather than swallowed (`:78-80`).
A correct, boring entrypoint. Match this shape on both sides.

### Build provenance

`Makefile:6-7` — `VERSION ?= $(shell git describe --tags --always --dirty)` feeding
`-X main.version=$(VERSION)`, consumed at `main.go:30` and logged at startup; the same ldflags repeated
for all eight release targets. **An operator can tell which build is running.** The proxy has no
equivalent — do this on both sides.

---

## Protocol semantics worth preserving

- **String opcode names on the wire** — `"text"`/`"binary"`/`"ping"`/`"pong"` rather than numeric
  RFC 6455 opcodes. Defined once per side (`types.go:8-11`, `proxy_handler.ex:278-287`) and they agree
  exactly. Far more debuggable in a text protocol than integers.
- **Base64 for WebSocket frame data, both directions, unconditionally** (`telephone_channel.ex:459`,
  `manager.go:377`). Correct encoding discipline — **extend it to HTTP bodies rather than abandon it.**
- **The close-code vocabulary** — 1000 client-disconnected, 1001 handler-terminated /
  telephone-disconnected, 1009 buffer overflow, 1014 backend-unreachable-or-timeout
  (`proxy_handler.ex:122`, `:131`, `:195`, `:207`, `:222`, `:236`; `telephone_channel.ex:408`). Carry
  the mapping, **add validation**: `proxy_handler.ex:195` echoes whatever integer arrived in `ws_closed`
  straight to the browser with no range check.
- **A typed error-reason vocabulary** — `connection_refused`, `connection_timeout`, `invalid_upgrade`,
  `backend_error`, `invalid_frame_data`, `invalid_path` (`types.go:63-76`). Stable machine-readable
  codes. Contrast the refresh-token error path, which ships `inspect(reason)`
  (`telephone_channel.ex:106`) — an Elixir term rendering no client can branch on. **Standardise on the
  typed style everywhere.**
- **The hook merge contract** — sequential by `execution_order` with a DB-level uniqueness guarantee on
  that order, root-level `Map.merge` where the hook wins on collision, stated in the moduledoc
  (`executor.ex:5-9`) and implemented at `:120-131`. Keep the contract; add **namespacing** (a hook can
  currently overwrite any client field, and a later hook any earlier hook's field, with no record) and a
  size bound on the merged result.
- **The hook cycle check is a real graph traversal**, not a self-reference check
  (`hooks.ex:243-272`) — a `MapSet` of visited paths recursing through each mount-point hook's target,
  so indirect A→B→A is detected. Two fixes rather than a discard: the visited set is not threaded across
  sibling branches (`:265` drops the recursive result), so diamond graphs are re-traversed; and it takes
  no locks, so two concurrent creates of A→B and B→A can both pass under `READ COMMITTED`.

---

## Tests worth porting

Named individually because test *volume* is not evidence — see [the audit](03-reference-audit.md).

- **`telephone_socket_test.exs` in full.** 22 tests over invalid signature, malformed, missing, nil and
  non-string tokens, expiry, revocation, deleted path, non-mount path, socket-id uniqueness (`:174`,
  `:196`), and assign minimality — `refute Map.has_key?(assigns, :token_hash)` (`:285`). **The model the
  rest of the suite should have followed.**
- **`telephone_tokens_test.exs`**, especially the forged-JWT case (`:212-231`) which signs with the real
  derived secret to reach the not-in-database path, and the deliberate indistinguishability of expired vs
  revoked (`:171`, `:186`) — a security decision encoded in a test.
- **`paths_test.exs:827-1098`** — CHECK constraints, both unique indexes including that soft-deleted rows
  do not block reuse (`:1042`), FK cascade vs RESTRICT (`:941-999`), and the two rollback tests (`:304`,
  `:322`) asserting no orphaned `user_paths` after a failed create.
- **`hook_store_test.exs:183-202`** — the *only* test in the codebase that simulates an external DB change
  (`Repo.delete_all`) and asserts the projection repairs itself. **Make this the template for every
  cache.**
- **`rate_limiter_test.exs:189-203`** (window expiry via ETS timestamp rewrite) and **`:157-176`** (true
  ETS concurrency with an exact 5-ok/5-denied split).
- **`validate_path_test.exs`** — both sides of every boundary: 51 segments rejected vs exactly 50
  accepted (`:86`, `:95`), 256 bytes rejected vs exactly 255 (`:77`, `:104`).
- **`telephone_registry_test.exs:330-356`** — registration is cleaned up when the owning process dies.
  Keep regardless of what replaces Horde.
- **`domain_affinity_test.exs:81-165`** — changeset negatives: wildcard in the middle, missing dot after
  the asterisk, leading/trailing dot, non-mount target, deleted target. Dense, cheap, each mapping to a
  real rejection.
- **The owner/maintainer/viewer/no-access matrix** in `hook_controller_test.exs` (`:35`, `:72`, `:91`,
  `:110`), `telephone_token_controller_test.exs` (`:28`, `:55`, `:73`, `:87`) and
  `domain_affinity_controller_test.exs` (`:25`, `:44`, `:61`, `:78`) — including the distinction between
  the two different 403 messages (`hook_controller_test.exs:107` vs `:124`).
- **`websocket_proxy_plug_test.exs:56-135`** — one pass-through test per excluded prefix, all eight,
  including `/telephone` (`:76`), which is what stops the sidecar's own socket being proxied through
  itself.
- **The LiveView selector convention** — address elements by `phx-click`/`phx-value-id` (e.g.
  `path_tokens_live/index_test.exs:670`) and assert on flash text plus a database re-read (`:254-257`),
  never on CSS classes or DOM structure. **Zero markup assertions across 2,400 lines** — so these tests
  survive a redesign.
- **`websocket_test.go`'s real-server pattern** — `createWSTestServer` (`:28-42`) using gorilla's
  `Upgrader` against `httptest`, and the four tests asserting actual bytes crossing the boundary in both
  directions (`:268`, `:594`, `:653`, `:236`). **Extend this to the HTTP tunnel, which has no
  equivalent.** Its assertion style — literal wire keys, base64-decoding the payload (`:527-541`) — is
  the one place in either repo where the contract is actually pinned down. Make it mandatory for every
  event.
- **`config_test.go:266-322`** `TestLoadFromEnvMissingVariables` — list-driven over all 16 required vars,
  asserting each error message names its own variable.
- **`token_test.go:135-263`** — 10 readers × 100 iterations against 5 writers × 50. The only tests in the
  Go suite that give `-race` anything to find. Keep them with the `tokenMu` RWMutex discipline they cover
  (`telephone.go:332-347`).
- **`client_test.go:527`, `:590`** — pin the exact Phoenix contract `?token=…&vsn=2.0.0` including the
  existing-query-params case, and the invariant that logged URLs never contain the JWT.

---

## Tooling worth porting

From the sidecar, which had the better harness:

- `make test` runs `-race` **by default** (`Makefile:45`); `precommit: fmt vet lint test` (`:103`);
  installable pre-commit and pre-push hooks (`:106-116`) where pre-push blocks pushes to `main` on lint
  or test failure.
- A 30-linter `golangci` v2 config with `govet` enable-all, `errcheck` `check-type-assertions` **plus**
  `check-blank`, and `gocyclo` at 15. Exclusions are narrow and defensible (bin/vendor paths;
  `gocyclo`/`errcheck`/`gosec` off for tests only) — **the linter is not defeated by config.** It *is*
  softened by 28 inline `//nolint:errcheck` in production code and two `//nolint:gocyclo` that suppress
  the complexity gate rather than splitting the function. Fix those rather than dropping the gate.
- `security.yml` as the template the proxy needs: `govulncheck` (`:37-59`) plus Trivy at
  `severity: HIGH,CRITICAL` with `exit-code: 1` (`:71-79`), on push, on PR, **and on a weekly cron**
  (`:24-26`) so newly disclosed CVEs surface without a code change. Apply it to the proxy, which has the
  larger attack surface and currently has nothing.
- Multi-stage `Dockerfile`, `CGO_ENABLED=0`, non-root UID 1000, pinned `alpine:3.23`, pure-Go SQLite so
  there is no libc in the runtime image.

**Do not port:** `dependabot-automerge.yml`. It auto-approves and merges every Dependabot PR with no
`update-type` gate — `fetch-metadata` is invoked and its output never referenced — over a suite with no
tests on `reconnect.go`. Gate on `version-update:semver-patch`, and never auto-advance a pointer that
encodes a wire protocol.

---

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
