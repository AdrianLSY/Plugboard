---
type: essay
status: current
authority: rationale
---

# Reviewing a change

The canonical note with a structural defect rather than a propagation one.

### The change-description questions

1. **What breaks if this is wrong.**
2. **The wire-contract impact.**

### The review checklist

In brief:

1. **Body.**
2. **Headers.**

## Pull requests

A second section bearing the same heading follows, which is the defect: the canonical enumeration is
stated twice, and the earlier stub would win a first-match search.

### The review checklist

1. **Does the body survive?**
2. **Are headers still an ordered list of pairs?**
3. **Does the method pass through unmodified?**

### Blocking objections

1. Headers as a map, in any form: `map[string]string`, `Map.new`, or an `Enum.into` over header
   fields, with `Set-Cookie` as the case that proves it.
2. A body carried as a string.

### PR template

The template the forge serves is stated here and published where the forge reads it. The two are held
byte-identical, so editing either alone fails.

```markdown
## What breaks if this is wrong?

## Wire contract impact
- [ ] None
```
