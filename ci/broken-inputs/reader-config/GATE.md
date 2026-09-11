# Violating input: reader-config

- **Gate:** `ci/gates/reader_config.py` (`reader_config`)
- **Rule note:** `docs/method/rules/reader-configuration.md`
- **Requirement:** `docs/knowledge-base` — "The repository is one vault with one spine",
  the clause on vault reader configuration.

## Violations, all in one tree

1. `.obsidian/workspace.json` is present, i.e. per-person pane layout has become
   tracked repository state.
2. `.obsidian/cache/state.bin` is present, i.e. a reader cache has become tracked.
3. `.obsidian/app.json` sets `useMarkdownLinks: false` and `newLinkFormat: "shortest"` —
   a file that satisfies a presence check while inverting RDV2 for every reader.
4. `.obsidian/core-plugins.json` is absent, i.e. a declared-tracked setting file missing.

## Expected

Exit 1, every violation named in one run, each naming the offending path. Case 3 must be
caught on its *values*, not on the file's absence — that is the case a presence-only check
would pass.
