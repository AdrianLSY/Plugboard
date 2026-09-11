# Violating input: capability-notes

- **Gate:** `ci/gates/capability_notes.py` (`capability_notes`)
- **Rule note:** `docs/method/rules/capability-notes.md`
- **Requirement:** `docs/knowledge-base` — "Each capability has a concept note".

## Violations, one per enumerated direction

1. **Specification with no concept note.** `tunnel/listener` has a spec and no
   `docs/capabilities/tunnel-listener.md`.
2. **Concept note with no specification.** `docs/capabilities/ghost-capability.md` describes a
   capability nobody specified — its subject does not exist.
3. **Unlinked dependency.** `tunnel/wire-contract`'s spec names `` `tunnel/listener` `` as a
   dependency, and `docs/capabilities/tunnel-wire-contract.md` does not link its note.

## Expected

Exit 1, three violations, each naming the capability and the path it wanted.
