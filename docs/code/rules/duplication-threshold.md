---
type: rule
status: planned
authority: rationale
---

# Ten identical non-comment lines in two places is a duplication failure

**Gate:** planned — rebuild-plugboard task 3.6 builds the duplication gate
([tasks.md](../../../openspec/changes/rebuild-plugboard/tasks.md), task 3.6). Until it runs, the
threshold is an obligation with no automated check.

Ten consecutive non-comment lines appearing at two locations is refused, whether the two locations
are two modules or two places in one module, and whether or not identifiers were renamed between
them. This threshold is about source; requirement *text* duplicated between the spine and a
specification is [a different rule](../../method/rules/one-copy-of-requirement-text.md).

## Why

`MountStore` and `HookStore` were the same GenServer twice: 128 of `hook_store.ex`'s 199 non-comment
lines appear verbatim in `mount_store.ex`, including a byte-identical twelve-line reconcile block
with its comments ([harness](../../method/harness.md), `docs/method/harness.md:68-70`). Domain
affinities were then bolted *inside* `MountStore`, because two copies had left no third slot — so the
cost of the duplication was not the duplicated lines but the shape it forced on everything added
afterwards.

The mirrored copy inside one module has line-level citations that the history notes do carry:
`mount_store.ex:414-430` and the mirrored domain version at `:520-536`, recorded under
[insert-before-evict reconciliation](../../history/carry-forward.md#insert-before-evict-reconciliation).
Seventeen lines, duplicated once, with the good part of the design in both copies — which is what
makes it the honest example: duplication arrives attached to code worth keeping.

**Where 10 comes from.** The smallest cited instance is the twelve-line reconcile block. A threshold
of ten sits below it, so the *weakest* demonstrated case fails rather than only the flagrant one; a
threshold of twenty would have passed the block that was copied byte for byte.

**What it would have caught.** The 128-line overlap between `hook_store.ex` and `mount_store.ex`, at
roughly thirteen times the threshold, and the twelve-line reconcile block on its own. It would have
fired on the second `Store` rather than the third resource, which is the moment the abstraction was
still cheap. Task 3.6's verification plants a second copy of a 60-line module with only its name
changed, so a gate keyed on identifiers rather than on structure fails that fixture.

**A gap in the citation, stated rather than hidden.** The 128-of-199 figure is recorded in the
harness note at the lines cited above, without a `file:line`; the mirrored-block citation above is
the one with lines. Both modules are retrievable from the pinned prior art via
[the obtaining instructions](../../history/obtaining-the-reference.md).
