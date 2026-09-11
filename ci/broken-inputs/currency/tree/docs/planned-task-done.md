---
type: essay
status: planned
authority: rationale
---

# Planned, task already complete

Describes what [demo task 1.1](../openspec/changes/demo/tasks.md) builds.

The task id sits inside the LINK LABEL, which is how the vault writes it and the only form the
gate reads: an id is scoped to the list the link names, because two changes in flight both have a
task 1.1 and an unscoped read cleared a marker against the wrong one. Written with the id in the
prose and a generic label, this case was silent and the fourth currency property went
undemonstrated while the fixture still failed on the other three.
