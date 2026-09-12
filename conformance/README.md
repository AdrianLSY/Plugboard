---
type: guide
status: current
authority: rationale
---

# conformance

The executable suite that is the authority on the contract — adversarial fixtures, the runner, and the
coverage report that names which requirement each case proves.

**Boundary:** stated once, in [docs/code/boundaries/conformance.md](../docs/code/boundaries/conformance.md).
This file routes; it does not restate.

**Skeleton only.** The Go module builds one statically linked binary per declared platform — `make
-C conformance build`. What is not here is any case: the adversarial corpus is written before the
code it gates ([section 12](../openspec/changes/rebuild-plugboard/tasks.md)), and this binary exists
first so the corpus has something to be carried by.
