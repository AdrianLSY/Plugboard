---
type: rule
status: current
authority: rationale
---

# Currency runs in both directions

**Gate:** `ci/gates/currency.py`

Four properties. A note whose subject was removed is deleted or marked superseded; a superseded note
names its replacement; a note describing something not yet built is marked planned and links the work
that builds it; and **a planned marker is retired once its subject exists** — checked either by a
named subject path appearing in the tree, or by the named task's checkbox being ticked.

## Why the fourth property is the one that matters

An adversarial review found the requirement ran one way only. This change lands *before* the task
that creates `contract/`, `proxy/`, `sidecar/`, `terminator/` and `conformance/`, so nearly the whole
spine is marked planned against directories that appear almost immediately afterwards — and nothing
would ever un-mark them.

`status: planned` would have become the default value across the vault at the exact moment CI started
passing, which is the value an agent reads to decide whether a note can be trusted. A currency
guarantee enforced only in the direction that is empty today would have reported green over a vault
that had gone stale everywhere.
