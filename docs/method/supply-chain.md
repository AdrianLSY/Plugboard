---
type: essay
status: current
authority: rationale
---

# Supply chain, changelog and versioning

Two version streams and four dependency rules. Both halves exist because the previous attempt shipped
neither — see [the finding table](harness.md#the-finding-to-constraint-table).

---

## Changelog and versioning

The reference has **no changelog anywhere** and 119 commits of `updated code`. Two version streams
matter and they are independent:

**The wire contract** is versioned separately from the software, and is the one users depend on.
`contract/CHANGELOG.md` records every version with:
- what was added (new frame type, new capability flag, new optional field)
- what was deprecated, and the earliest version that may drop it
- **which sidecar versions remain compatible** — the question a tenant actually has

Contract changes are **additive by default**. A breaking contract change requires a new major version,
a capability flag, and a documented period during which both are served. Since old sidecars are
permanent, "breaking" means "supported forever in parallel", so the bar is high.

**The software** (proxy, sidecar, terminator) uses semantic versioning with conventional commits, which
the sidecar already did well (`#2`–`#32`) and the proxy did not. Changelog entries are generated from
commit messages, so commit messages are a reviewed artifact.

**Release notes state the contract version range**, because that is what determines whether a tenant
must act.

---

## Supply chain

- **Dependabot on**, auto-merge gated on `version-update:semver-patch` **only**. The reference invoked
  `fetch-metadata` and never referenced its `update-type` output, so major bumps merged on the same terms
  as patches.
- **`govulncheck` and Trivy on push, PR, and a weekly cron**, so newly disclosed CVEs surface without a
  code change. Port the sidecar's `security.yml`; add the equivalent for the proxy, which has none.
- **No automated pointer advance for anything encoding the wire protocol.** A human approves.
- **Establish provenance for every binary asset.** The reference ships 85 JPEGs of unestablished origin
  under a blanket MIT claim with no attribution — for a feature that is inert in production for three
  independent reasons.

> Orientation, not behaviour. The specifications win.
