---
type: rule
status: current
authority: rationale
---

# Conventions for authoring a note

**Gate:** `ci/gates/authoring_channels.py`

Complete on purpose: this tree demonstrates two channels that DISAGREE, so every convention
must be present in both. Absence is the sibling tree's scenario.

| convention | what it requires | gate |
|---|---|---|
| `capability-note` | Every capability has one concept note under the declared ceiling, linking its spec and its dependencies. | `ci/gates/capability_notes.py` |
| `cited-or-unverified` | Every claim carries a citation into a tracked file or an obtainable artifact, or an explicit Unverified marker. | `ci/gates/citations.py` |
| `classification` | Every spine or component note declares type, status and authority from the closed enumerations. | `ci/gates/frontmatter.py` |
| `currency` | A planned note links the work that builds it, and its marker is retired once its subject exists. | `ci/gates/currency.py` |
| `declared-roots` | Every tracked note lives under a declared governed root; an exempt root records what owns its files. | `ci/gates/note_roots.py` |
| `entry-routes` | An entry file routes, stays under its ceiling, and names nothing the repository does not contain. | `ci/gates/entry_points.py` |
| `generated-indexes` | An index is generated, tracked, and byte-identical to a fresh regeneration. Never hand-edit one. | `ci/gates/index_drift.py` |
| `links-resolve` | Every link resolves, anchors included. | `ci/gates/links.py` |
| `no-owned-behaviour` | A note never states behaviour a specification owns; no normative modal in the spine. Link the owner. | `ci/gates/citations.py` |
| `one-copy` | Requirement text has one copy. Link the specification rather than restating it. | `ci/gates/duplication.py` |
| `one-register` | One decision register. A change's own decisions carry a namespace; a retired identifier is never reused. | `ci/gates/decision_register.py` |
| `precedence-once` | The authority precedence is stated in exactly one location; every other note links it. | `ci/gates/precedence.py` |
| `reachable` | Every note is reachable by links from a declared entry point. | `ci/gates/reachability.py` |
| `relative-links` | Relations are relative markdown links. No wikilinks, no transclusion, no absolute paths. | `ci/gates/wikilinks.py` |
| `rule-names-gate` | Every rule note names its gate, or `planned`, or `none` (preference, quarantined). | `ci/gates/rule_gate_correspondence.py` |
