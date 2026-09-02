# The reference audit

**Scope.** `reference/Plugboard` at `6756a07` (Elixir/Phoenix, 14,593 lines `lib/`, 20,810 lines
`test/`) and `reference/Telephone` at `9ccba86` (Go, ~6,000 lines `pkg/`, 6,765 lines of tests).

**Method.** Seven independent auditors over test depth, code quality, and the cross-component
contract. Each auditor's top claims were handed to an adversarial verifier instructed to refute them
and to default to *refuted* when uncertain. One completeness critic ran over the whole digest. 15
agents, 741 tool calls, 98 findings — 66 confirmed, 28 downgraded or made more precise, 4 killed.
Read-only throughout; nothing was executed.

A published report with collapsible evidence per finding:
<https://claude.ai/code/artifact/a77b983b-3c37-43f0-9814-4e9a6ddf220f>

## The headline

**The system does not work.** It works for `GET` requests returning text. The two elementary
obligations of a reverse proxy — carry the request through, carry the bytes through unchanged — are
both broken, and 27,000 lines of tests never noticed.

## Blocking defects

### 1. Request bodies never reach the sidecar

```
  client                Endpoint            ProxyController        Telephone
  POST /call/api  -->  Plug.Parsers   -->  read_body(conn)   -->  "body" => ""
  {"a":1}              reads body to        returns {:ok, ""}      (empty)
                       completion; no
                       :body_reader, so
                       nothing caches it
```

- `endpoint.ex:118` — `plug(PlugboardWeb.Plugs.Parsers)` runs before `plug(Router)` at `:134`.
- `parsers.ex:31` — `parsers: [:urlencoded, :multipart, :json], pass: ["*/*"]`, no `:body_reader`.
- `proxy_controller.ex:250` — `read_body(conn)` on an already-consumed body.
- `proxy_controller.ex:302` — `"body" => body`, forwarding `""`.

Content types no parser claims (`application/octet-stream`, `text/plain`) *are* left unread and do
forward, which is why this went unnoticed.

**A second, independent consumption path.** `executor.ex:86` reads the body for hooks, merges the
enriched result, and stores it at `conn.private[:raw_body]` (`executor.ex:413-419`). `grep -rn
raw_body lib/` returns three hits: two comments and the write. **Nothing ever reads it.** The
codebase documents its own gap at `executor.ex:406`:

> …or **could be extended** to read from `conn.private[:raw_body]` if hooks modified it.

It never was. So "hooks enrich the request body" — the entire documented purpose of a subsystem with a
37KB specification — does not happen.

**The test that should have caught it** is `proxy_controller_test.exs:835`, named *"correctly passes
request payload to telephone"*. It uses `GET` and asserts only on `payload["method"]`.

### 2. Binary payloads are corrupted in transit

- `telephone.go:853` — `chunks = append(chunks, string(buf[:n]))`, `[]byte` → `string`.
- `telephone.go:914` — `"body": resp.Body`.
- `message.go:65` — `json.Marshal(arr)`.

`encoding/json`: *"String values encode as JSON strings coerced to valid UTF-8, replacing invalid bytes
with the Unicode replacement rune."* Every image, PDF, protobuf, gzip and media segment is mangled.
Because each chunk converts independently, **even valid UTF-8 text breaks when a multi-byte character
straddles a read boundary.** Present in the request direction too (`telephone.go:791`). Compounded by
Plugboard relaying `Content-Length` verbatim (`proxy_controller.ex:445-449`) — U+FFFD substitution
changes the byte length.

The WebSocket path, written later, gets it right: `websocket.go:201` base64-encodes
(`manager.go:377`). **Same codebase, two body paths, no shared abstraction, one wrong.**

### 3. Neither container boots

- `runtime.exs:93` raises for a missing `LIVE_VIEW_SIGNING_SALT` under prod. `grep` across
  `.github/`, `docker-compose.yml` and `Dockerfile` finds it nowhere; the only occurrence in the repo
  is `.env.example:44`.
- `Dockerfile:50-51` sets the two session salts as `ENV` **in the builder stage**, which ends at
  `Dockerfile:86`. They never cross the `FROM` into the runtime image. `Dockerfile:104` sets
  `MIX_ENV=prod`.
- The sidecar dies on `BACKEND_SCHEME` — its `Dockerfile` `ENV` block sets only `PLUGBOARD_URL`,
  `BACKEND_HOST`, `BACKEND_PORT`.
- `deployment.yml:70` "proves the app runs" by curling for HTTP 200, while `runtime.exs:106` defaults
  `FORCE_SSL` to true (→ 301) and `runtime.exs:39` defaults `DATABASE_SSL` to true with
  `verify: :verify_peer` against a compose Postgres serving no TLS.

**The workflow that claims to prove the product runs cannot pass.** The env-var contract lives in
three places that drift, and no CI step asserts container health.

## Structural defects

| finding | evidence |
|---|---|
| **Method allowlist** — seven verbs, so WebDAV/CalDAV/CardDAV are structurally unreachable, not merely unimplemented | `router.ex:63-69`, `:169-175`; enforced independently at both ends (`telephone.go:27-35`) |
| **Headers as `map<string,string>`** in both directions — every `Set-Cookie` past the first is silently deleted | `proxy_controller.ex:496` `Enum.into(conn.req_headers, %{})`; `telephone.go:85` |
| **"Streaming" does not stream** — the whole body is read into `[]string`, *then* `chunked := len(chunks) > 1`, then every chunk ships inside **one** message | `telephone.go:829-901`, `:881` |
| **One reply per correlation id** — makes 1xx, trailers and any abort signal unrepresentable | `telephone_channel.ex:302-309` |
| **One global timeout, capped at 300s**, covering the entire buffered exchange — SSE cannot exist | `path.ex:67`; `proxy_controller.ex:246` |
| **No backpressure at any hop.** One channel process serialises every request and frame for a mount, fed by unbounded `send/2` | `proxy_handler.ex:275`; `telephone_channel.ex:364-375` |
| **The multi-tenant path is content-type restricted.** The `/call` pipeline deliberately removed `:accepts`; the domain-affinity pipeline — the one custom domains use — kept it | `router.ex:157` `plug(:accepts, ["json", "html"])` |
| **Auth scans every credential.** Every sidecar join loads all active tokens and runs Argon2 against each, inside a transaction holding a pool connection | `telephone_tokens.ex:384-397`; `crypto.ex:51` |
| **Expired JWTs still reach the scan** — `Joken.verify_and_validate(%{}, …)` with an empty token config never checks `exp` | `telephone_tokens.ex:446-460` |
| **Cross-tenant write.** `update_token/2` takes no actor at all, unlike its sibling `revoke_token/2` | `telephone_tokens.ex:353-363` vs `:175-181` |
| **Global projection rebuild per tenant event** — full-table `SELECT` plus full-keyspace ETS diff on any tenant's change | `mount_store.ex:402-412` (no tenant scoping) |
| **`reorder_hooks` cannot reorder.** Non-deferrable unique index, one-by-one updates, and a bare `Ecto.Changeset.change/2` declaring no `unique_constraint` — so a collision raises `Postgrex.Error` rather than returning a changeset. Drag-and-drop returns 500 | `hooks.ex:370-378`; `20251118141933_create_hooks_table.exs:47-50` |
| **Soft delete does not cascade.** Deleting a path leaves its domain affinities active, permanently squatting the partial unique index on `domain` | `paths.ex:365-406`; `hook_store.ex:187-192` |
| **`create_path` restores another user's soft-deleted path** and grants the caller owner role, while the original owner's `user_paths` row and unrevoked tokens survive | `paths.ex:219-241` (no user scoping on the `FOR UPDATE` lookup) |
| **Dead reconnect path.** `Postgrex.Notifications.start_link` links without `trap_exit`, so the notifier dies before its `:DOWN` clause can run; the documented exponential backoff is unreachable ceremony, and recovery happens only by supervisor restart, which triggers no reload | `mount_notifier.ex:120`, `:74-97`, `:128` |

## The test suite is bimodal

The split is **not** by subsystem. It is by whether the subject is synchronous.

```
  SYNCHRONOUS / PURE / DB-CONSTRAINT       ASYNCHRONOUS / DISTRIBUTED
  ==================================       ==========================
  genuinely good -- port these             worthless to actively harmful
  (see 06-carry-forward.md)

  telephone_tokens_test.exs                mount_notifier_test.exs   \ 947 lines
    forges a real JWT with the             hook_notifier_test.exs    / that cannot
    derived secret; makes expired                                      observe a
    and revoked indistinguishable          NOTIFY at all

  telephone_socket_test.exs                every "concurrent" test runs on ONE
    22 tests incl. refute                  sandbox connection, so the FOR UPDATE
    Map.has_key?(assigns, :token_hash)     locks the schema depends on are never
                                           contended
  executor_test.exs (HTTP hooks)
    real Bypass servers, chained,          cluster_connector_test.exs asserts only
    ordered, asserts accumulated           that the process is still alive -- one of
    body from INSIDE hook two              70 such assertions in test/plugboard

  paths_test.exs:827-1098                  reconnect.go -- 250 lines, the sidecar's
    triggers, both partial unique          most fragile subsystem, ZERO coverage;
    indexes, FK cascade vs RESTRICT,       the only test named for it is an
    rollback leaves no orphans             unconditional skip

  validate_path_test.exs                   711 lines of Go integration tests skip
    51 segments rejected vs exactly        unconditionally in CI -- they need a live
    50 accepted; 256 bytes vs 255          Plugboard on :4000 that CI never starts
```

### The self-defeating helper

The showpiece finding, and the most instructive thing in the audit:

> `pg_notify` inside a trigger is **transactional**. The Ecto sandbox **never commits**. So the
> notifier's `handle_info` is never invoked by any test. The tests pass because on timeout their own
> wait helper calls `MountStore.reload_all()` — **the helper repairs the state it is waiting for** —
> and then reports success.

- `data_case.ex:46` — `Sandbox.start_owner!(Repo, shared: not tags[:async])`
- `20251102153313_add_mount_notify_trigger.exs:18` — `PERFORM pg_notify(...)` inside the uncommitted
  transaction
- `mount_notifier_test.exs:554-560` — the fallback, and both tests claiming to prove NOTIFY (`:56`,
  `:287`) route through it
- `hook_notifier_test.exs:371-376` — same pattern; callers discard the return value entirely

**947 lines of tests for the cache-invalidation mechanism, and the mechanism has never run under
test.** Rule derived: never let a wait helper repair the state it is waiting for.

### Tests written around defects

Three tests accommodate bugs instead of exposing them, and one preserves the model's abandoned
reasoning as committed comments:

```elixir
# hooks_test.exs:425
# Now try to change hook's target to another_mount
# This creates: hook.path -> another_mount -> hook.target
# Actually this shouldn't be circular... let me think again
...
# Let's just test that changing target_type works
```

```elixir
# hooks_test.exs:538
# Use new execution_order values that don't conflict with existing ones
# (The implementation updates one-by-one, so we need non-overlapping values)
```

```elixir
# executor_test.exs:465
# Mount point hook test is skipped due to Horde registry timing issues
# The functionality is tested via proxy_controller integration tests
@tag :skip          # <- the deferral claim is false
```

Transitive cycle detection (A→B→C→A) has no test at all; the one cycle test is satisfied at depth 1
(`hooks.ex:261`) before the recursive branch at `:265` is reached.

### The test config deletes production properties

- `config/test.exs:4` — `config :argon2_elixir, t_cost: 1, m_cost: 8`. `m_cost` 8 means 2^8 KiB
  against a library default exponent of 16, removing exactly the cost that makes the linear token scan
  dangerous.
- `config/test.exs:96` — `config :plugboard, :allow_localhost_hooks, true`, whose own comment says
  *"This disables SSRF protection for localhost/127.0.0.1"*. SSRF blocking is an advertised security
  feature with two independent implementations and **zero tests anywhere**.

The pattern is the finding: the test environment is tuned for speed and quiet, and each such setting
removes the property that most needed a test.

### The contract is asserted twice against two fictions

- `Phoenix.ChannelTest` replaces the serializer with a **no-op**, provable from the test file itself:
  `telephone_channel_test.exs:101` asserts `%{ts: ^timestamp}` — an **atom** key, which cannot survive
  a JSON round trip (`telephone_channel.ex:87` pushes `%{ts: ts}`). No Plugboard test has ever
  exercised serialisation in either direction.
- The Go tests marshal a `ProxyResponse` **struct** (`telephone_test.go:473`) whose tags production
  never uses; the real payload is a hand-built map (`telephone.go:910`).
- **`proxy_res` — the most load-bearing message in the system — has zero key-level assertions on
  either side.**
- `ws_check` has zero tests on either side and is absent from all 457 lines of
  `TELEPHONE_WEBSOCKET.md`. Already drifted: Go hardcodes a 3s check timeout (`websocket.go:339`),
  Elixir uses a configurable 5s.

## What the completeness critic added

Six auditors examined code and tests exhaustively. None asked whether the system could be deployed,
observed, or contributed to.

**Zero observability.** 75 `:telemetry.execute` sites across 15 modules; **zero**
`:telemetry.attach`. The only reporter is commented out (`telemetry.ex:16`). Exactly one occurrence of
`"Logger."` in 14,600 lines of `lib/` — inside a doc comment at `proxy_controller.ex:51` claiming
errors are logged. No health endpoint. Dashboard compiled out of prod. *Five of seven auditors cited
the telemetry as evidence of good instrumentation.*

**The contributor loop is broken by construction.** 27 of 43 test files are `async: false`; every file
requires a live Postgres, including `validate_path_test.exs` whose subject touches no database. The
critic's conclusion is the most useful sentence in the entire audit:

> When feedback is slow, an agent (or a person) writes assertions that are cheap to satisfy rather
> than assertions that are expensive to satisfy.

**That is the root cause.** Not laziness — a harness that made the honest path expensive.

**Asymmetric hygiene.** The sidecar has 30 linters, `gosec`, `govulncheck` and Trivy on a weekly
cron. The proxy — which terminates untrusted internet traffic, runs the admin UI, and holds every
credential — has no static analysis, no format gate, no vulnerability scanning. Credo is a declared
dependency that nothing invokes. And the local guardrail never worked:

```
mix.exs           precommit: ["compile --warning-as-errors", ...]   # singular: WRONG
unit_test.yml:69  mix compile --warnings-as-errors                  # plural: correct
```

**Unreviewed supply chain.** Every Dependabot PR auto-merges with no update-type gate —
`fetch-metadata` is invoked and its `update-type` output never referenced — then
`notify-parent-repo.yml` fires a `repository_dispatch` and the parent commits a new submodule pointer
to `main`. A `gorilla/websocket` major bump reaches the parent repo with no human in the loop, over a
suite with no tests on `reconnect.go`.

**Untested crypto.** `Plugboard.Crypto` — which hashes every token and API key and derives the JWT
signing secret — has **no test file**, and its six `iex>` doctests never run because `doctest` appears
nowhere in the repository.

**Licensing.** 85 JPEGs in `public/img/http/` of unestablished provenance, under a blanket MIT
copyright claim with no attribution. The feature is also inert in production for three independent
reasons.

## Commit archaeology

| | Plugboard | Telephone |
|---|---|---|
| commits | 119 | 34 |
| style | `updated code` ×17, `updated styling` ×9, `fixes` | conventional commits with PR numbers |
| PRs | none — direct to `main` | `#2`–`#32` |
| changelog | none | none |

148 KB of prose documentation (README 60 KB, `feature.md` 37 KB, `AGENTS.md` 24 KB,
`TELEPHONE_WEBSOCKET.md` 17 KB, `CLAUDE.md` 9.5 KB) against a history of `updated code`. **The prose
is where intent was recorded, so it must be read — but it cannot be trusted on behaviour, only on
configuration.** The env-var tables are the reliable half; re-derive every behavioural claim from
code. Two documented claims are verifiably false: the README's headline "O(1) path matching" is
O(depth), and `proxy_controller.ex:51` claims `Logger.error/1` is called when no `Logger` call exists.
