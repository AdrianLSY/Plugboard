---
type: rule
status: planned
authority: rationale
---

# A security or correctness property is never weakened or disabled in test configuration

<a id="no-property-weakened-in-test-config"></a>

**Gate:** planned — the production-equivalent cost parameters of
[rebuild-plugboard task 30.2](../../../openspec/changes/rebuild-plugboard/tasks.md), asserting the
parameters in force under test equal the production values and that no configuration path lowers
them

Prohibited: a test environment that lowers a work factor, switches off a protection, or relaxes a
validation that production applies. If a property makes the suite slow, the architecture is the
thing to change.

## Why

The prior attempt's test configuration set `reference/Plugboard/config/test.exs:4`
(`t_cost: 1, m_cost: 8` against a library default exponent of 16) and
`reference/Plugboard/config/test.exs:96` (`allow_localhost_hooks: true`, whose own comment says it
disables SSRF protection for localhost). The first removed exactly the cost that made a linear token
scan dangerous; the second disabled an advertised security feature that had two independent
implementations and zero tests anywhere ([the audit](../../history/reference-audit.md)).

The pattern is the finding: **the test environment was tuned for speed and quiet, and each such
setting removed the property that most needed a test.** A weakened property under test is not a
faster test of the same thing — it is a test of something else.

Speed belongs to [the tier boundary and the fast-tier budget](fast-tier-latency-budget.md), which is
the sanctioned way to buy it.
