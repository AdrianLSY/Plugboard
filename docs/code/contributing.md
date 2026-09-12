---
type: essay
status: current
authority: rationale
---

# Contributor experience

Three audiences with conflicting wants ([who it is for](../why/audiences.md)); this is the part
that serves contributors specifically.

- **`make dev` works from a clean clone.** No 16-variable scavenger hunt. The no-defaults configuration
  policy is right for production and hostile for development — resolve it by shipping a complete
  `.env.example` generated from the schema, reporting *every* missing variable at once, and providing a
  dev profile.
- **The fast suite runs without Postgres.**
  Non-negotiable, per the correctness argument in [testing](testing.md).
- **The conformance suite is the on-ramp.** "Write a sidecar in your language; here is the suite that
  tells you when you are done" is the best-scoped, highest-status contribution an outside contributor
  can make, and it exists as a side effect of [`D23`](../decisions/d23-contract-first.md) — `D3` in the
  [superseded register](../decisions/superseded-register.md).
- **Good first issues are the conformance fixtures.** Each is a bounded piece of work against an
  existing primitive, and the corpus is written before the code it gates, so a fixture can land
  ahead of the implementation it holds to account. Trailers, 1xx interim responses and Range are not
  on that list — they are v1 work carrying their own task sections, not spare capacity. The one frame
  type reserved and unimplemented at v1 is the datagram kind
  ([`D2`](../decisions/d02-frame-shaped-tunnel.md)).
- **[`CONTRIBUTING.md`](../../CONTRIBUTING.md) exists**, written before the code rather than after it.
  The reference's README linked to it, and to `FUTURE_WORK.md`, and **both were dead links.** First
  impressions of a portfolio project are made of exactly this. What keeps it from decaying into the
  same thing is that it names every item of the three review enumerations and nothing else states
  them, so a new item fails the build until it is named —
  [the rule](rules/review-obligations-single-sourced.md).

> Orientation, not behaviour. The specifications win.
