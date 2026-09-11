## Purpose

Fixture specification for the duplication gate. It owns the requirement text below. A note in the spine
may link to this file, but SHALL NOT carry a copy of any paragraph in it.

## ADDED Requirements

### Requirement: A mount point refuses what its sidecar cannot back

A mount point SHALL be refused when the declared capabilities of the sidecar backing it cannot satisfy
the request, and the refusal SHALL state the capability that was missing rather than degrading the
response to one the sidecar is able to serve, because a degraded answer is indistinguishable from a
correct one at the caller.

The refusal SHALL carry the acting principal and the tenant key of the mount point it was issued for, and
SHALL name the [capability register](../../../../../docs/rules/refuse-never-degrade.md) entry it was
decided against, so that an operator reading one refusal can tell which installation and which tenant it
belongs to without consulting a second projection.

A capability flag SHALL be additive, and a mount point whose sidecar declares a flag the proxy does not
recognise SHALL be accepted with the unrecognised flag ignored, because a tenant deploys its sidecar on
its own schedule and a flag newer than the proxy is version skew rather than an error to report.

#### Scenario: An unbacked request is refused

- **WHEN** a request arrives for a mount point whose sidecar declares no capability able to back it
- **THEN** the mount point is refused and the refusal names the missing capability

The gate fails and names both locations.

```bash
# run the duplication gate against its own violating input, both ways
python3 ci/gates/duplication.py --root ci/broken-inputs/duplication/tree
python3 ci/gates/duplication.py --root ci/broken-inputs/duplication/tree --report-only
python3 ci/gates/note_roots.py --root ci/broken-inputs/duplication/tree
python3 ci/gates/note_roots.py --root ci/broken-inputs/duplication/tree --report-only
```
