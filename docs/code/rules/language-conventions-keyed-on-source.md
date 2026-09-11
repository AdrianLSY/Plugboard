---
type: rule
status: current
authority: rationale
---

# Language conventions are keyed on the languages present

**Gate:** `ci/gates/language_coverage.py`

Every language holding tracked source has a conventions note, and no language without tracked source
has one. Introducing a language without its conventions fails; conventions for a language that is no
longer present fail too. A conventions note states *this project's* obligations, not what the
language's own formatter already enforces.

## Why

A guide describing conventions for a language the repository does not contain is describing a system
that does not exist — the failure mode the vault is built to refuse. Today Python is the only
language with tracked source: the gate modules, the index generator and the aggregating runner.
Elixir and Go conventions arrive with their source, and until then writing them would trip this
rule's own second case.

Fixture files are not source. The single `.ex` file in the tree is a test input for the link gate,
and counting it would have produced Elixir conventions on the strength of one deliberately broken
example.
