---
type: rule
status: current
authority: rationale
---

# A gate says what it does not decide

**Gate:** none — preference, not obligation

A check whose limits are unwritten gets read as coverage. So a gate module carries a short passage
naming what it deliberately leaves undecided and what owns that instead. Nothing enforces this, and
it may not be raised as a blocking objection — a reviewer who wants the passage asks for it as an
improvement, not as a refusal.

## Why

Because a green signal was read as a guarantee once already, by seven readers in a row. The prior
art emitted telemetry from seventy-five sites and attached not one handler; its only reporter was
commented out (`telemetry.ex:16`), and five of the seven auditors cited the telemetry as evidence of
good instrumentation. In the same code base a doc comment claimed errors were logged where no logging
call existed (`proxy_controller.ex:51`). Both are in
[the reference audit](../../../history/reference-audit.md), and the pattern in both is the same: a
mechanism that appeared to cover something covered nothing, and no reader could tell from the outside.

A gate is exactly that kind of mechanism, and its passing output is the claim most likely to be
over-read. The [citation gate](../../../method/rules/citations.md) can refuse a normative modal in a
note and cannot see a confident unsourced sentence written in the indicative; the
[duplication gate](../../../method/rules/one-copy-of-requirement-text.md) catches copy-paste and is
blind to paraphrase. Both say so in their own modules, which is what keeps a green run from being
mistaken for "every claim is sourced" or "the spine and the specifications agree".

## Why it stays unenforced

The passage is prose about a negative, and no check can tell an honest account of a gate's limits
from a paragraph that merely sounds like one. A gate that fired on the absence of a heading would be
satisfied by an empty heading, which is the failure mode this preference exists to prevent, arriving
one level up. Filing it as taste keeps it out of
[the blocking objections](../../reviewing.md#blocking-objections) while leaving it written down where
the next gate's author reads it.
