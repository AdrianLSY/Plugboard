# Violating input: note-roots

- **Gate:** `ci/gates/note_roots.py`
- **Rule note:** `docs/method/rules/note-roots.md`
- **Violation:** `tree/marketing/pitch.md` sits under no declared note root, and
  `tree/STRAY.md` is a root-level note that is not a declared entry file.
- **Expected:** two failures in one run, each naming the path and the declared set.
