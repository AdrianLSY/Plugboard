# Violating input: component-boundaries

- **Gate:** `ci/gates/component_boundaries.py` (`component_boundaries`)
- **Rule note:** `docs/code/rules/component-boundary-stated-once.md`
- **Requirement:** `docs/code-standards` — "A component's boundary is stated once".

## Violations, one per enumerated case

1. `proxy/` exists with no boundary note at `docs/code/boundaries/proxy.md`.
2. `docs/code/boundaries/conformance.md` states a boundary for a component that is absent.
3. `sidecar/README.md` states the component's boundary itself under a "What it owns" heading rather
   than linking the canonical note — which is where the second copy of a boundary always appears.

## Expected

Exit 1, three violations. Note the real tree passes this gate *vacuously*: no component directory
exists until rebuild-plugboard task 1.1 creates them, which is why this fixture has to construct
two.
