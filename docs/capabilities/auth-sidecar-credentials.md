---
type: capability
status: planned
authority: rationale
---

# Sidecar credentials

**`auth/sidecar-credentials`** — how a sidecar proves it is entitled to serve one mount for one
tenant, and the whole life of the thing that carries the proof.

This is the gate in front of every tunnel, which is why its cost, its failure behaviour and the
promptness of revocation are treated as tenant-isolation properties rather than as convenience
features. A **credential** is bound at issuance to one mount and the tenant that owns it, and
[the glossary](../glossary.md#credentials-and-key-material) uses that word in no other sense.

The one idea worth carrying away is where authentication happens: once, at the tunnel handshake, not
per request — and the secret itself appears exactly once, when it is issued. What the installation
keeps afterwards is one-way, so a reader of the store cannot reconstruct anything presentable. Every
other obligation here is downstream of that shape: expiry checked at presentation, revocation that
has to reach connections already established, rotation that overlaps rather than interrupts, and an
audit trail that records the distinction between failure causes that the presenter is deliberately
not shown.

The prior art is instructive in both directions. Its sidecar-side token store was textbook-correct
authenticated encryption worth porting close to verbatim
([carry-forward](../history/carry-forward.md#token-store-crypto)), while the proxy side loaded every
active token and ran a password hash against each one inside a transaction holding a pool connection
(`telephone_tokens.ex:384-397`), never checked expiry at all (`:446-460`), and had one mutation that
took no acting principal while its sibling did (`:353-363`) — cost, expiry and authority, each
missed once.

## What it owns

- The scope fixed at issuance — one mount, one tenant, an expiry, a bounded maximum lifetime
- Secret generation the caller cannot influence, and its single presentation
- Stored state that cannot be turned back into a credential, and the sidecar's protection of its own
- Presentation bound to the tunnel; expiry and revocation reaching established connections too
- Rotation, fleet-spread renewal attempts, and renewal failure surfaced before it is an outage
- The issuing-credential class for automated issuance, and attribution of what it mints
- Rate limiting on an unforgeable attribute, the audit trail, last-use recording, and reaping

## What it does not own

- Custody classes and protection material — [key custody](security-key-custody.md)
- The store on the tenant's own disk — [the sidecar program](sidecar-program.md)
- Which registered sidecar then serves an exchange — [sidecar registry](tunnel-sidecar-registry.md)
- Who may create or delete the mount a credential is scoped to — [tenant isolation](tenancy-isolation.md)

## Depends on

- [tunnel/listener](tunnel-listener.md) — a third class of credential is owned here on the same terms
  as the other two: the one a client-facing terminator presents at the internal accept path, which
  that capability admits

This note previously read *"Nothing. Its specification names no other capability, in 877 lines"*, and
recorded that silence as a finding rather than a fact — a specification requiring purpose-separated,
versioned protection material and refusing startup under unsafe credential protection is plainly
coupled to something, and named nothing. The revision that added the client-facing terminator closed
it: the reference above is the specification's own, not an inference.

The remaining coupling is still unstated. [Key custody](security-key-custody.md) governs the
protection material this capability depends on, and packaging's specification names this capability in
the other direction; neither reference exists in this specification's text. Because the dependency
gate is one-directional by design it cannot see either, so both are linked from *What it does not own*
instead and the graph stays navigationally honest where the specification is silent.

## Shaped by

- [D8 — Tenant scoping in the data model, not in queries](../decisions/d08-tenant-scoping.md) — every
  credential operation is authorised against an acting principal rather than by a caller's habit
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) —
  revocation and expiry are properties of the installation, and authentication cost cannot grow with it
- [D21 — Rebuild from scratch](../decisions/d21-rebuild-from-scratch.md) — the three defects above
  are cited, not remembered, and the one correct piece is carried forward with its citation

## The specification

[`auth/sidecar-credentials`](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
