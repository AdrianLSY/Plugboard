---
type: rule
status: current
authority: rationale
---

# Relations

One wiki-style link with a pipe alias, whose target is locatable: [[architecture|the architecture]].

One transclusion, whose target is not in this tree: ![[glossary#Terms]]

One root-anchored link: see [the architecture](/docs/how/architecture.md).

## Specimens that must not fail

Inline code holds a specimen: `[[architecture]]`, `![[architecture]]`, and the
WebIDL internal slot `[[Reliability]]` that docs/04-protocol-fidelity.md:221
quotes from the W3C definition. A double-backtick span holds one too:
`` `[[Reliability]]` ``.

A fenced block holds the whole forbidden set:

```markdown
[[how/architecture]]
[[how/architecture|the architecture]]
![[how/architecture]]
[the architecture](/docs/how/architecture.md)
[the architecture](obsidian://open?vault=Plugboard&file=how/architecture)
```

A tilde fence, with a longer run and an info string, holds it as well:

~~~~text
[[how/architecture]]
![[how/architecture]]
```
[the architecture](/docs/how/architecture.md)
~~~~
