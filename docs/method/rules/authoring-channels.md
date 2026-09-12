---
type: rule
status: current
authority: rationale
---

# Conventions reach both authoring channels

**Gate:** `ci/gates/authoring_channels.py`

Every convention is supplied where an author reads it, through two channels keyed on one
enumeration: the planning tool's configuration for anyone authoring a proposal, specification,
design or task list, and [a generated note](../conventions.md) the entry files link for anyone
authoring a note. A convention added to the gates without reaching both fails, and so does a
convention the two channels state differently: presence of an id in each channel is not agreement,
and the generated channel cannot drift, so a disagreement is always the hand-maintained one's.

## Why two, and not the obvious one

The plan originally named a single hook, the planning tool's configuration. But its per-artifact
`rules:` block is keyed to *that tool's* artifact types, so it cannot express an obligation on a note
at all — and a note author never opens it. The one substitution the change rests on could not reach
the author it most needed to reach.

## The failure worth remembering

Writing that configuration by hand produced a YAML indentation error, and the tool responded by
printing a warning and **ignoring the entire file**. An unparsed configuration is indistinguishable
from an empty one to anyone who does not read stderr — so the gate asserts the file parses and that
every convention is present in it, rather than that the file exists.
