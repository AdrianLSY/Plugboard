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
- **Good first issues are the reserved-but-unimplemented frame types.** Trailers, 1xx interim responses,
  Range — each is a bounded piece of work against an existing primitive with a conformance fixture
  already written.
- **`CONTRIBUTING.md` exists**, at [the repository root](../../CONTRIBUTING.md). The reference's
  README linked to it, and to `FUTURE_WORK.md`, and **both were dead links** — first impressions of a
  portfolio project are made of exactly this. It landed with the propagation check that keeps it
  honest rather than before one, so the three canonical enumerations it carries are read from
  [reviewing](reviewing.md) on every run: an item added there fails the build until `CONTRIBUTING.md`
  names it, and a copy of an item's text fails whether or not the number is cited.
  → [the rule](rules/review-obligations-single-sourced.md)

> Orientation, not behaviour. The specifications win.
