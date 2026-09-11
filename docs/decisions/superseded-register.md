---
type: decision
status: current
authority: decision
---

# The superseded decision register

There was a period when this repository held **two** decision registers, both numbering their entries
`D1`–`Dn`, and they disagreed. `D9` meant "Runtime, reversed once" in one file and "domain ownership
verification precedes certificate issuance" in the other. Any citation of a bare number written during
that period is ambiguous, and citations written then still exist — in review comments, in commit
messages, in anything archived.

This note is what makes them resolvable. It records, for every identifier the superseded register used,
what it denoted **there** and what it denotes **now**.

The surviving register is
[`rebuild-plugboard`'s design](../../openspec/changes/rebuild-plugboard/design.md). It wins because it
is the stated authority, because the specifications cite it, and because most decision citations in the
task list already resolved against it. The superseded register was `docs/05-decision-log.md`, cited by
no artifact outside itself. It has been removed.

## Resolving a citation written against the old register

Read the left column, take the right.

| old `docs/05` | denoted there | now |
|---|---|---|
| `D1` | Rebuild from scratch, reference as prior art only | **`D21`** — carried, recorded nowhere else |
| `D2` | One repository | **`D22`** — carried, recorded nowhere else |
| `D3` | Contract-first, with a conformance suite | **`D23`** — carried, recorded nowhere else |
| `D4` | Version skew is the governing constraint | **`D24`** — carried, recorded nowhere else |
| `D5` | Positioning: multi-tenant platform ingress | **`D25`** — carried, recorded nowhere else |
| `D6` | Three primitives, not per-protocol handling | `D1` |
| `D7` | The tunnel exchange is frame-shaped | `D2` |
| `D8` | Capability negotiation with refusal, not degradation | `D3` |
| `D9` | Runtime — reversed once | `D4` |
| `D10` | WebTransport designed-for, not shipped | **`D26`** — carried, recorded nowhere else |
| `D11` | Proxied traffic terminates before application middleware | `D5` |
| `D12` | Framing authority is per-hop, never relayed | `D6` |
| `D13` | Tenant scoping in the data model | `D8` |
| `D14` | Domain ownership verification precedes certificate issuance | `D9` |
| `D15` | Observability before the hot path | **`D27`** — carried, recorded nowhere else |

Eight of the fifteen were the same decision under a different number. **Seven were recorded only in the
superseded register**, so removing it would have destroyed them; they were carried into the surviving
register as `D21`–`D27` *before* the removal, and a gate refuses the removal of a register that still
holds a decision recorded nowhere else.

## Why `D11`–`D15` are permanently unassigned

The surviving register jumps `D10` → `D16`. The superseded one filled `D11`–`D15` with five decisions of
its own — the right-hand column above shows they now live at `D5`, `D6`, `D8`, `D9` and `D27`.

Those five numbers are **retired, not recycled.** Assigning `D13` to something new would make a citation
written today ambiguous against every citation written against the old register — the same defect this
note exists to repair, reintroduced. A gate refuses the assignment and names what the identifier used to
denote.

## The rule this leaves behind

The unnamespaced `D<n>` sequence belongs to the surviving register alone. A change's own design rationale
may record decisions of its own, and those carry a prefix naming the change — this change's ten are
`RDV1`–`RDV10`. A namespaced set is not a register.

That rule exists because the change which consolidated these registers had itself numbered its own ten
decisions `D1`–`D10`, colliding one-for-one with the register's: `D1` was "vault root is the repository
root" here and "three primitives, not twelve protocols" there. The defect this note repairs was being
committed in the act of repairing it, and an adversarial review of the plan caught it.

Assignment is a heading. A number in a sentence, a table cell or backticks is a citation, which is why
this note can name all fifteen old identifiers without itself becoming a register.

## Checked by

- `ci/gates/decision_register.py` — one register; no assignment outside it; no reuse of a retired
  identifier; no removal of a register still holding a decision recorded nowhere else; and this note
  must exist once a register has been superseded.
