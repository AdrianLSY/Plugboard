# Violating input: wikilinks

- **Gate:** `ci/gates/wikilinks.py`
- **Rule note:** `docs/method/rules/relative-markdown-links.md`
- **Violation:** four refused link forms, one per case the requirement names.
  - `tree/docs/how/relations.md:9` -- a wiki-style link with a pipe alias,
    `[[architecture|the architecture]]`, whose target is locatable in the tree.
  - `tree/docs/how/relations.md:11` -- a transclusion, `![[glossary#Terms]]`,
    whose target is not in the tree.
  - `tree/docs/how/relations.md:13` -- a root-anchored link,
    `(/docs/how/architecture.md)`.
  - `tree/docs/how/reader-links.md:10` -- a reader-only `obsidian://` URI.
- **Expected:** four failures in one run, no more and no fewer. Each names the
  note, the line and column, the offending text, and the equivalent relative
  markdown form -- a real relative path (`[the architecture](architecture.md)`)
  where the target is locatable, the shape with a placeholder
  (`[glossary](<relative-path-to>/glossary.md#terms)`) where it is not. The
  wikilink and the transclusion are reported as distinct kinds, and the
  `forms:` line reads `wikilink=1 transclusion=1 root-anchored=1
  reader-only=1`.
- **Must NOT fail:** the specimens under "Specimens that must not fail" in
  `tree/docs/how/relations.md` -- every forbidden form inside a fenced block
  (backtick and tilde, with and without an info string) and inside inline code
  spans (single and double backtick). This is not hypothetical: the tree
  already carries one at `docs/04-protocol-fidelity.md:221`, where
  `[[Reliability]]` is a WebIDL internal slot quoted from the W3C definition,
  and the note documenting this rule has to be able to show the syntax it
  forbids.
