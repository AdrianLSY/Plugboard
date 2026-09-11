---
type: essay
status: current
authority: rationale
---

# Success criteria

[Who it is for](audiences.md) names three audiences, names the conflict between their requirements,
and states a bar for none of them. This is the bar.

One rule governs all three. **A criterion nobody can check is not a criterion.** So each one below
says what would be observed and which artifact decides it. "Good isolation" is not on this page;
"a cross-tenant read is not expressible" is, because something can be run against it.

Two honest qualifications first. Most of what would decide these criteria is not built: the
specifications exist as planning artifacts and the checks that would run them are open tasks in
[the rebuild's task list](../../openspec/changes/rebuild-plugboard/tasks.md), so most rows below are
a bar to be met rather than one already met — the exceptions are the decision register and the vault
gates, which exist today. And where a criterion names a requirement, the specification owns it: this
page points, it does not restate.

## Operators

The audience that sets hard requirements, and the reason the tie-break in
[who it is for](audiences.md) goes their way.
[D25 — positioning](../decisions/d25-positioning.md) records the question this bar answers: what
stops one tenant affecting another, asked first, and answerable only structurally. D25 also prices
it, so a criterion here is not free — it is the thing the positioning was chosen to buy.

| the bar | judged met when | owned by |
|---|---|---|
| Isolation is a property of the schema and of each operation's contract, not a convention | the requirement "Every read is scoped to the requesting principal's tenancy" holds in the form its scenario **An unscoped read cannot be expressed** demands — the check is that no caller *can* write the cross-tenant read, not that none did — and "Authorization is intrinsic to the mutation" holds with its scenario **Every mutation in the administrative surface is covered**, which makes the coverage enumerable instead of sampled. Not met by one administrative mutation that takes no acting principal. | [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md), and [D8 — tenant scoping](../decisions/d08-tenant-scoping.md) for why it is a schema decision |
| Failure is predictable per tenant | "One tenant at its ceiling does not degrade another" and "Faults are contained to the tenant that caused them" are demonstrated the way they are written — one tenant driven to a declared bound while another's service is measured — rather than argued from the design | [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md) |
| One audit trail, ordered, covering every mutation | any mutation can be found in *one* trail with a stated ordering: "Every mutation is recorded in an audit trail" plus "The audit trail is one trail for the installation, with a stated ordering". Not met by per-instance logs that have to be merged by eye. | [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md), [operability/observability](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md) |
| Upgrades are boring for the tenant who never upgrades | the tenant on the eight-month-old sidecar of [version skew](version-skew.md) has to do nothing — "A migration never requires a tenant to act" — a rollback across a migration is a declared property, "A code version can be rolled back across a migration", and what the old sidecar cannot back is refused rather than quietly downgraded, which is what [D3](../decisions/d03-capability-negotiation.md) settles | [operability/schema-migration](../../openspec/changes/rebuild-plugboard/specs/operability/schema-migration/spec.md), [D24 — version skew](../decisions/d24-version-skew.md), [D3 — capability negotiation](../decisions/d03-capability-negotiation.md) |

## Contributors

The bar is time-to-first-useful-change, and every part of it is measurable in seconds or in a CI job.

| the bar | judged met when | owned by |
|---|---|---|
| `make dev` works from a clean clone | a CI job clones fresh, runs `make dev`, and asserts the proxy, a sidecar and the terminator each report ready through their own readiness signal. **Planned** — today's `Makefile` carries the vault gates only; the dispatching targets are task 1.7 and the clean-clone job is task 73.4. | [rebuild tasks 1.7, 73.4](../../openspec/changes/rebuild-plugboard/tasks.md), [contributor experience](../code/contributing.md) |
| The fast tier runs with no Postgres and no network, under ten seconds | the fast tier runs in a CI job with neither, and a planted fast-tier test that opens a database connection makes the tier *fail rather than skip* (task 2.7); a latency budget check reports elapsed time and fails above ten seconds, proven by planting a fifteen-second sleep (task 2.8). **Planned** — no suite exists yet. | [rebuild tasks 2.7, 2.8, 73.1](../../openspec/changes/rebuild-plugboard/tasks.md), and [testing](../code/testing.md) for why latency is a correctness control rather than a comfort |
| The conformance suite is the on-ramp: an outside implementer can tell when they are done without asking | the suite is "an independently executable artifact" in the sense its scenarios fix — **Third party runs the suite against their own implementation**, **No reference implementation is required**, **The suite runs offline** — and it answers completeness, "Every normative requirement is covered", whose scenario **Uncovered requirement is named** makes an incomplete answer legible instead of silent | [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md), [D23 — contract-first](../decisions/d23-contract-first.md) **Planned** — no `conformance/` tree exists yet; built by [tasks 12–17](../../openspec/changes/rebuild-plugboard/tasks.md). |
| A first issue is closeable by making an already-written fixture pass | the fixtures precede the code they gate — "Cases exist before the behaviour they cover" — so the reserved-but-unimplemented frame types named in [contributor experience](../code/contributing.md) are bounded work against an existing primitive rather than open design | [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md), [contributor experience](../code/contributing.md) **Planned** — the fixtures are built by [tasks 12–17](../../openspec/changes/rebuild-plugboard/tasks.md); none exists today. |

## The portfolio

[Who it is for](audiences.md) says this audience wants legible judgment and decisions defensible
under questioning, that the temptation is over-engineering, and that the mitigation is writing every
decision down — depth *documented* rather than *built*. That makes the criterion a property of
[the register](../decisions/in-force.md), not of the size of the system.

| the bar | judged met when | owned by |
|---|---|---|
| A reader who disagrees can reach the end of the argument without asking the author | every decision in force has an entry with its rationale and the alternatives it ruled out, reachable from its note — twenty-two of them — and the argument terminates somewhere nameable: [D8](../decisions/d08-tenant-scoping.md) looks like over-engineering for an early version, and [D25](../decisions/d25-positioning.md) is where that argument stops. Not met by a note that states an outcome and not the argument. | [decisions in force](../decisions/in-force.md) |
| A reversal is recorded as a reversal, with its cause | [D4 — runtime](../decisions/d04-runtime.md) is in force *and* overturns the earlier recommendation, and records what an adversarial review found about the premise that had forced it — a fabrication, not a difference of opinion. The bar is that the reversal is the readable part; deleting it would be the failure. | [D4](../decisions/d04-runtime.md), and [decisions in force](../decisions/in-force.md) for why that history is the first thing to read before reopening anything |
| A cost is named rather than discovered | [D25](../decisions/d25-positioning.md) states what choosing multi-tenant ingress made foundational instead of deferrable, and says re-opening the isolation work means re-opening the positioning. A decision recording only its upside does not meet this. | [D25](../decisions/d25-positioning.md) |
| Refusing scope counts as depth | the refusals are written with their reasons and separated from what is merely deferred — [scope and refusals](scope-refusals.md), and [D26](../decisions/d26-webtransport-deferred.md) for something designed for and not shipped | [scope and refusals](scope-refusals.md) |
| The bookkeeping holds up under citation | a citation written against the superseded register still resolves: retired identifiers are recorded rather than recycled, with the collision table naming all fifteen, and `ci/gates/decision_register.py` refuses an unnamespaced `D<n>` introduced outside the register | [decisions in force](../decisions/in-force.md), [the collision table](../decisions/superseded-register.md) |

> **Unverified.** That a reader evaluating this work would go to the register rather than straight to
> the code is an assumption about the reader and not an observation — it needs checking against an
> actual review by someone outside the project, of which there has been none.

## How this page fails

Two ways, both checkable against the page itself:

1. **A criterion no artifact decides.** If the "owned by" column is empty, or points at prose rather
   than at a specification, a task or a gate, the row is an aspiration and not a criterion.
2. **A criterion still unmet with nothing scheduled.** Every **Planned** marker above names the task
   that would clear it; a marker naming no task is a defect.

Requirement titles are quoted rather than paraphrased so that a rename in the owning specification
leaves a quotation here resolving to nothing. No gate checks that — review does — and where this
page and a specification disagree, this page is wrong.

## Read next

- [Who it is for](audiences.md) — the three audiences and the conflict this page states a bar against.
- [Contributor experience](../code/contributing.md) — what the contributor bar became in practice.
- [Version skew](version-skew.md) — the constraint the operator bar's last row rests on.

> Orientation, not behaviour. The specifications win.

## On the requirement titles quoted above

Several criteria are stated by naming a specification's own requirement — that is deliberate, because
a bar phrased in the specification's words is one a reader can check rather than interpret. Those
summaries are **non-normative**: the owning specification wins where it and this note disagree, and
where a criterion here is narrower or wider than the requirement it names, the requirement is right.
