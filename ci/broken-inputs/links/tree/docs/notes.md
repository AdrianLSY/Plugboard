---
type: essay
status: current
authority: rationale
---

# Notes

Two links here do not resolve, for two different reasons. The gate must name
both in a single run and say which cause each one is.

## Violations

- [ghost file](ghost.md) -- no such file in the tree: cause `missing-file`
- [ghost anchor](target.md#no-such-heading) -- the file is there, the heading is
  not: cause `missing-anchor`

## Controls

Nothing below may fail, or the fixture would stop proving the two causes above.

- [the target file](target.md) -- a plain relative link that resolves
- [a real anchor](target.md#real-section) -- fragment present in the target
- [this very section](#controls) -- a bare fragment against this file
- [an external page](https://example.invalid/whatever) -- external scheme, skipped
- [a line-numbered citation](snippet.ex:3) -- resolve the file, ignore the line
- [a line fragment](snippet.ex#L3) -- the forge's line anchor on a code file
- [a reference link][target-ref] -- resolved through its definition below
- an inline code sample: `[not a link](nowhere.md)` renders literally

A fenced block is not link syntax either:

```markdown
[also not a link](nowhere.md)
[nor this one](target.md#invented)
```

[target-ref]: target.md
