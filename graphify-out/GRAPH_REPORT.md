# Graph Report - .  (2026-09-25)

## Corpus Check
- 210 files · ~106,501 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 789 nodes · 1329 edges · 80 communities (47 shown, 33 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 193 edges (avg confidence: 0.85)
- Token cost: unmetered (host-agent extraction usage unavailable)

## Graph Health
- The initial full extraction omitted 102 raw AST edges to external or excluded symbols and collapsed 43 raw edges onto existing endpoint pairs. Those losses remain in this incremental graph.
- This refresh re-extracted 11 documents: five vault notes edited on this branch, and six files changed on `main` after the previous refresh (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/code/reviewing.md`, the pull request template and `pr.yml`). It added 25 nodes and 223 edges and removed 30 edges the re-extraction corrected, with no lost nodes; all edge endpoints exist and there are no self-loops or collapsed edges. Semantic extraction used 134,805 subagent tokens, with no input and output split available.

## Community Hubs (Navigation)
- [[_COMMUNITY_Obsidian Settings|Obsidian Settings]]
- [[_COMMUNITY_Go Conformance Harness|Go Conformance Harness]]
- [[_COMMUNITY_Conformance Go Module|Conformance Go Module]]
- [[_COMMUNITY_Proxy Startup Banner|Proxy Startup Banner]]
- [[_COMMUNITY_Elixir Mix Project|Elixir Mix Project]]
- [[_COMMUNITY_Elixir Proxy Test|Elixir Proxy Test]]
- [[_COMMUNITY_Go Sidecar Entry Point|Go Sidecar Entry Point]]
- [[_COMMUNITY_Sidecar Go Module|Sidecar Go Module]]
- [[_COMMUNITY_Terminator Go Module|Terminator Go Module]]
- [[_COMMUNITY_Go Lint Configuration|Go Lint Configuration]]
- [[_COMMUNITY_Dependabot and Workflows|Dependabot and Workflows]]
- [[_COMMUNITY_Reference Artifact Provenance|Reference Artifact Provenance]]
- [[_COMMUNITY_Security Scan Workflow|Security Scan Workflow]]
- [[_COMMUNITY_Scheduled Gates and Parity|Scheduled Gates and Parity]]
- [[_COMMUNITY_Contract and Conformance|Contract and Conformance]]
- [[_COMMUNITY_Packaging and Operability|Packaging and Operability]]
- [[_COMMUNITY_Certificate Key Custody|Certificate Key Custody]]
- [[_COMMUNITY_Custom Domain Routing|Custom Domain Routing]]
- [[_COMMUNITY_Credential Roles|Credential Roles]]
- [[_COMMUNITY_Affinity Registry|Affinity Registry]]
- [[_COMMUNITY_Agent Routers and Glossary|Agent Routers and Glossary]]
- [[_COMMUNITY_Resource Bound Definitions|Resource Bound Definitions]]
- [[_COMMUNITY_Listener Trust Boundary|Listener Trust Boundary]]
- [[_COMMUNITY_Primitives and Frame Tunnel|Primitives and Frame Tunnel]]
- [[_COMMUNITY_Capability Declaration|Capability Declaration]]
- [[_COMMUNITY_Contract Conformance|Contract Conformance]]
- [[_COMMUNITY_Sidecar Lifecycle|Sidecar Lifecycle]]
- [[_COMMUNITY_Schema Migration|Schema Migration]]
- [[_COMMUNITY_Degraded Condition|Degraded Condition]]
- [[_COMMUNITY_Outbound Sidecar Architecture|Outbound Sidecar Architecture]]
- [[_COMMUNITY_Project Glossary|Project Glossary]]
- [[_COMMUNITY_Capability Documentation|Capability Documentation]]
- [[_COMMUNITY_PR Template and Contribution|PR Template and Contribution]]
- [[_COMMUNITY_Banned Traffic Patterns|Banned Traffic Patterns]]
- [[_COMMUNITY_Clean Clone Development|Clean Clone Development]]
- [[_COMMUNITY_Code Quality Rules|Code Quality Rules]]
- [[_COMMUNITY_Language Specific Conventions|Language Specific Conventions]]
- [[_COMMUNITY_Gate Documentation Rules|Gate Documentation Rules]]
- [[_COMMUNITY_Repository Structure|Repository Structure]]
- [[_COMMUNITY_Tunnel Transport Choice|Tunnel Transport Choice]]
- [[_COMMUNITY_Timeout Taxonomy|Timeout Taxonomy]]
- [[_COMMUNITY_Framing and Codecs|Framing and Codecs]]
- [[_COMMUNITY_Domain Ownership Proof|Domain Ownership Proof]]
- [[_COMMUNITY_Proxy Traffic Pipeline|Proxy Traffic Pipeline]]
- [[_COMMUNITY_Decision and Index Rules|Decision and Index Rules]]
- [[_COMMUNITY_Tenant Cache Reconciliation|Tenant Cache Reconciliation]]
- [[_COMMUNITY_Protected ETS Reads|Protected ETS Reads]]
- [[_COMMUNITY_WebSocket Buffer Bounds|WebSocket Buffer Bounds]]
- [[_COMMUNITY_Disconnect Failure Propagation|Disconnect Failure Propagation]]
- [[_COMMUNITY_Soft Deletion Indexes|Soft Deletion Indexes]]
- [[_COMMUNITY_Database Check Constraints|Database Check Constraints]]
- [[_COMMUNITY_Boot Secret Validation|Boot Secret Validation]]
- [[_COMMUNITY_Versioned Key Derivation|Versioned Key Derivation]]
- [[_COMMUNITY_SSRF Changeset Validation|SSRF Changeset Validation]]
- [[_COMMUNITY_Hook Header Denylist|Hook Header Denylist]]
- [[_COMMUNITY_Backend Path Validation|Backend Path Validation]]
- [[_COMMUNITY_Token Store Encryption|Token Store Encryption]]
- [[_COMMUNITY_WebSocket Subprotocol Negotiation|WebSocket Subprotocol Negotiation]]
- [[_COMMUNITY_Reconnect Jitter|Reconnect Jitter]]
- [[_COMMUNITY_Hook Cycle Detection|Hook Cycle Detection]]
- [[_COMMUNITY_Configuration Validation|Configuration Validation]]
- [[_COMMUNITY_Duplicate Header Preservation|Duplicate Header Preservation]]
- [[_COMMUNITY_Protocol Runtime Research|Protocol Runtime Research]]
- [[_COMMUNITY_Deferred Scope and Operability|Deferred Scope and Operability]]
- [[_COMMUNITY_Protocol Fidelity|Protocol Fidelity]]
- [[_COMMUNITY_Architecture and Wire Flow|Architecture and Wire Flow]]
- [[_COMMUNITY_Outstanding Specification Gaps|Outstanding Specification Gaps]]
- [[_COMMUNITY_Documentation Method|Documentation Method]]
- [[_COMMUNITY_Capability Note Conventions|Capability Note Conventions]]
- [[_COMMUNITY_Tracked Reader Settings|Tracked Reader Settings]]
- [[_COMMUNITY_Out of Scope Files|Out of Scope Files]]
- [[_COMMUNITY_Markdown Link Integrity|Markdown Link Integrity]]
- [[_COMMUNITY_Python Tooling and Component CI|Python Tooling and Component CI]]
- [[_COMMUNITY_Credential Scanning|Credential Scanning]]
- [[_COMMUNITY_PR Description Checks|PR Description Checks]]

## God Nodes (most connected - your core abstractions)
1. `T` - 31 edges
2. `Protocol fidelity` - 27 edges
3. `Scope refusals` - 27 edges
4. `Claude router (CLAUDE.md)` - 26 edges
5. `Agent router (AGENTS.md)` - 25 edges
6. `Blocking objections` - 22 edges
7. `Code rules index` - 21 edges
8. `Reviewing a change` - 19 edges
9. `Decisions in force` - 18 edges
10. `Topology and runtime` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Pull request policy` --semantically_similar_to--> `One-sitting PR size limit`  [INFERRED] [semantically similar]
  CONTRIBUTING.md → docs/code/reviewing.md
- `Every gate is demonstrated to fail` --semantically_similar_to--> `PR checks self-test`  [INFERRED] [semantically similar]
  docs/method/rules/gates-are-demonstrated-to-fail.md → .github/workflows/pr.yml
- `Agent router (AGENTS.md)` --semantically_similar_to--> `Claude router (CLAUDE.md)`  [INFERRED] [semantically similar]
  AGENTS.md → CLAUDE.md
- `Contract change guard` --conceptually_related_to--> `Versioned wire schema`  [INFERRED]
  .github/workflows/dependabot-auto-merge.yml → README.md
- `Versioned contract artifact` --conceptually_related_to--> `Versioned wire schema`  [INFERRED]
  contract/README.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **PR description enforcement chain** — docs_code_reviewing_change_description_questions, docs_code_reviewing_pr_template, _github_pull_request_template_pull_request_template, docs_code_reviewing_review_obligations_gate, docs_code_reviewing_pr_creation_preflight, _github_workflows_pr_pr_body_checks [EXTRACTED 1.00]
- **Single-sourced review enumerations** — docs_code_reviewing_change_description_questions, docs_code_reviewing_review_checklist, docs_code_reviewing_blocking_objections, docs_code_rules_review_obligations_single_sourced_review_obligations_single_sourcing [EXTRACTED 1.00]
- **Adversarial fixtures against banned patterns** — docs_code_testing_adversarial_fixtures, docs_code_banned_patterns_headers_as_a_map_ordered_headers, docs_code_banned_patterns_body_as_a_string_body_octets, docs_code_banned_patterns_method_allowlists_opaque_method_token, docs_code_banned_patterns_read_all_on_a_proxied_body_streaming_body [INFERRED 0.85]

## Communities (80 total, 33 thin omitted)

### Community 23 - "Obsidian Settings"
Cohesion: 0.25
Nodes (7): useMarkdownLinks, newLinkFormat, alwaysUpdateLinks, attachmentFolderPath, showUnsupportedFiles, strictLineBreaks, userIgnoreFilters

### Community 0 - "Go Conformance Harness"
Cohesion: 0.05
Nodes (71): TestMalformedFramingIsRefusedRatherThanGuessedAt(), TestWellFramedBodiesAreStillRead(), TestATransferCodingIsStillRefusedAsUnimplemented(), main(), run(), serve(), Conn, closing() (+63 more)

### Community 31 - "Elixir Mix Project"
Cohesion: 0.50
Nodes (3): Plugboard.MixProject, project(), deps()

### Community 41 - "Go Lint Configuration"
Cohesion: 0.67
Nodes (3): Shared Go lint configuration, Strict Go lint settings, Narrow test lint exclusions

### Community 18 - "Dependabot and Workflows"
Cohesion: 0.27
Nodes (10): Dependabot GitHub Actions updates, Weekly GitHub Actions dependency updates, Vault check workflow, Dependabot auto-merge workflow, Patch-only unattended merge, Contract change guard, Pull request checks workflow, Dependabot exemption from description job (+2 more)

### Community 20 - "Reference Artifact Provenance"
Cohesion: 0.31
Nodes (9): DCO sign-off workflow, Obtaining the reference, Pinned Plugboard revision 6756a07, Pinned Telephone revision 9ccba86, Reference fetch source gap, Reference citation verification, A cited artifact is obtainable, History notes index (+1 more)

### Community 32 - "Security Scan Workflow"
Cohesion: 0.50
Nodes (4): Security scan workflow, Go vulnerability scan, Dependency vulnerability scan, Elixir security scan

### Community 40 - "Scheduled Gates and Parity"
Cohesion: 0.67
Nodes (3): Scheduled gates and parity checks, Obligation parity check, Documentation vault gates

### Community 24 - "Contract and Conformance"
Cohesion: 0.33
Nodes (7): Conformance suite, Portable conformance binary, Versioned contract artifact, Generated wire codecs, Versioned wire schema, Contract-first development, Conformance suite as contributor on-ramp

### Community 14 - "Packaging and Operability"
Cohesion: 0.10
Nodes (23): Instance, Deployable, Client-facing terminator, Lookup surface, Client-facing role, Artifact, Build input, Artifact identity (+15 more)

### Community 17 - "Certificate Key Custody"
Cohesion: 0.20
Nodes (11): Installation, Custody class, Protection material, Root material, Key custody, Closed custody inventory, Allowed key parameters, Protection at rest (+3 more)

### Community 5 - "Custom Domain Routing"
Cohesion: 0.06
Nodes (37): Node, Mount point, Terminal mount point, Remainder, Longest-prefix match, Reserved path, Routing entry, Hostname claim (+29 more)

### Community 30 - "Credential Roles"
Cohesion: 0.40
Nodes (5): Sidecar, Origin-facing role, Credential, Issuing credential, Credential store

### Community 35 - "Affinity Registry"
Cohesion: 0.50
Nodes (4): Affinity key, Affinity binding, Registry entry, Eligibility

### Community 13 - "Agent Routers and Glossary"
Cohesion: 0.17
Nodes (23): Acting principal, Audit trail, Start here, Docs index, Rule index, Preference rule, Glossary, Permanent asymmetric version skew (+15 more)

### Community 36 - "Resource Bound Definitions"
Cohesion: 0.50
Nodes (4): Occupancy dimension, Standing-resource dimension, Bound, Bound definition gap

### Community 25 - "Listener Trust Boundary"
Cohesion: 0.33
Nodes (6): Tunnel, Listener, Observed source, Connection phase, Credential presentation, Installation trust boundary

### Community 2 - "Primitives and Frame Tunnel"
Cohesion: 0.09
Nodes (42): Correlation identifier, Superseded decision register, Decisions in force, D30 Durable state in PostgreSQL, D31 Out-of-scope declaration containment, D28 Apache-2.0 licensing of authored tree, Decision notes index, D29 Discover gate roster and reconcile invocations (+34 more)

### Community 26 - "Capability Declaration"
Cohesion: 0.33
Nodes (6): Capability declaration, Baseline, Refusal, Declaration-based skip, Capability term collision, gRPC-Web translation

### Community 16 - "Contract Conformance"
Cohesion: 0.18
Nodes (12): Contract version, Conformance suite, Implementation under test, Conformance run, Permanent asymmetric version skew, Wire schema irreversibility, Three protocol primitives, Contract-first implementation (+4 more)

### Community 21 - "Sidecar Lifecycle"
Cohesion: 0.22
Nodes (9): Hop, Liveness, Readiness, Drain, Sidecar program, Sidecar configuration lifecycle, Sidecar lifecycle, Backend hop ownership (+1 more)

### Community 37 - "Project Glossary"
Cohesion: 0.50
Nodes (4): Gated rule, No owned behaviour in spine, Ordered header fields, Fast test tier latency budget

### Community 6 - "Capability Documentation"
Cohesion: 0.10
Nodes (36): HTTP fidelity, Edge hygiene, WebSocket, Wire contract, Tunnel listener, Conformance suite, Sidecar registry, Tenant isolation (+28 more)

### Community 10 - "PR Template and Contribution"
Cohesion: 0.15
Nodes (25): Adding a feature, Fixing a bug, Contract-first feature sequence, Prior failing case, Review obligations single sourcing, Actorless cross-tenant token write, Self-repairing notifier test helper, Pull request template (+17 more)

### Community 9 - "Banned Traffic Patterns"
Cohesion: 0.15
Nodes (30): Contributor experience, Conformance fixtures as good first issues, Body octets end to end, Dedicated proxied-traffic pipeline, Bounded accumulators and overflow reasons, Ordered header-field pairs, Chunkwise proxied-body emission, Per-hop framing authority (+22 more)

### Community 4 - "Code Quality Rules"
Cohesion: 0.08
Nodes (37): Single source build provenance, Ten line duplication threshold, Banned defect classes, Generate sources before compilation, Fast tier latency budget, Recorded red gate debt, Three test tiers, Module size ceiling (+29 more)

### Community 33 - "Gate Documentation Rules"
Cohesion: 0.50
Nodes (4): Gate states what it does not decide, Gate docstring names requirement and defect, Preference rules index, Failure messages name the consequence

### Community 34 - "Repository Structure"
Cohesion: 0.50
Nodes (4): D22 — One repository, Single repository tree, No-submodules CI guard, Unreviewed dependency update chain

### Community 42 - "Tunnel Transport Choice"
Cohesion: 0.67
Nodes (3): D19 — v1 tunnel transport, WebSocket over TLS on port 443, Transport-independent tunnel framing

### Community 29 - "Timeout Taxonomy"
Cohesion: 0.40
Nodes (5): D7 — Timeout taxonomy, Six independently configured timeout bounds, Route class without a total time bound, Per-request Task.async isolation, Single global request timeout

### Community 22 - "Framing and Codecs"
Cohesion: 0.29
Nodes (8): D6 — Per-hop framing authority, Per-hop framing declarations, Contradictory-framing refusal, D18 — Generated binary frame codecs, Binary interface definition, Generated frame codecs, Raw body octets, Binary payload corruption in JSON

### Community 28 - "Proxy Traffic Pipeline"
Cohesion: 0.40
Nodes (5): D5 — Dedicated proxied traffic path, Proxy path before application middleware, Administrative middleware pipeline, Request body loss before sidecar, Buffered body disguised as streaming

### Community 3 - "Decision and Index Rules"
Cohesion: 0.08
Nodes (39): D3 — Capability negotiation and refusal, Sidecar capability declaration, Reasoned refusal of unsupported request, Typed error-reason vocabulary, Exactly one decision register, Generated indexes cannot drift, Alternatives to Plugboard, Multi-tenant platform ingress (+31 more)

### Community 7 - "Deferred Scope and Operability"
Cohesion: 0.08
Nodes (34): Threat model, Request smuggling, SSRF through the sidecar, Certificate issuance from an unverified claim, Cross-tenant writes, Open relay via tunnelling method, Compression amplification, Credential and key custody (+26 more)

### Community 8 - "Protocol Fidelity"
Cohesion: 0.11
Nodes (31): Cross-tenant cookie scoping, Mount-scoped cookies, Ordered header field pairs, Protocol fidelity, Opaque octet-stream bodies, Ordered repeatable header fields, Open-ended method tokens, Raw request target (+23 more)

### Community 1 - "Architecture and Wire Flow"
Cohesion: 0.05
Nodes (62): The tenant's view, The failure taxonomy, Frame-shaped tunnel, Topology and runtime, Three transport primitives, The architecture, docs/how index, Outbound sidecar dial (+54 more)

### Community 15 - "Outstanding Specification Gaps"
Cohesion: 0.12
Nodes (17): Follow-ups, Undeclared correspondence drift, CODEOWNERS review blocking gap, Gate coverage count/list mismatch, Configuration/provenance name collision verification, make check latency, Harness size ceiling gap, Forge behavior verification gap (+9 more)

### Community 11 - "Documentation Method"
Cohesion: 0.17
Nodes (24): The harness and its findings, Documentation rules, Conventions for authoring a note, Supply chain, changelog and versioning, Authority precedence, Method index, Published and computed enumerations reconcile, Gate coverage is an assertion (+16 more)

### Community 43 - "Capability Note Conventions"
Cohesion: 0.67
Nodes (3): Every capability has a concept note, Every tracked note lives under a declared root, Every note carries a classification

### Community 12 - "Python Tooling and Component CI"
Cohesion: 0.11
Nodes (23): Python quality tooling, Component test workflow, Python tooling CI job, Fast test job, Integration test job, Component lint job, Expected-outcome gating tests, Conformance build job (+15 more)

### Community 27 - "Credential Scanning"
Cohesion: 0.40
Nodes (5): Credential scan of tree and review range, Combined-diff merge scan, Dated credential scan suppression, Prefix-anchored credential detection, Non-disclosing credential findings

### Community 19 - "PR Description Checks"
Cohesion: 0.22
Nodes (9): Pull request description, Wire contract impact declaration, Pre-submit checklist, Pull request body checks (ci/pr/checks.py), PR description check, Wire contract impact check, Documentation change check, PR body passed via environment (+1 more)

## Knowledge Gaps
- **89 isolated node(s):** `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks`, `attachmentFolderPath`, `showUnsupportedFiles` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Claude router (CLAUDE.md)` connect `Agent Routers and Glossary` to `Architecture and Wire Flow`, `Primitives and Frame Tunnel`, `Banned Traffic Patterns`, `PR Template and Contribution`, `Documentation Method`, `PR Description Checks`, `Reference Artifact Provenance`, `Contract and Conformance`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Why does `Scope refusals` connect `Decision and Index Rules` to `Architecture and Wire Flow`, `Primitives and Frame Tunnel`, `Capability Documentation`, `Protocol Fidelity`, `Agent Routers and Glossary`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `Agent router (AGENTS.md)` connect `Agent Routers and Glossary` to `Architecture and Wire Flow`, `Primitives and Frame Tunnel`, `Banned Traffic Patterns`, `PR Template and Contribution`, `Documentation Method`, `PR Description Checks`, `Reference Artifact Provenance`, `Contract and Conformance`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Scope refusals` (e.g. with `HTTP fidelity` and `Edge hygiene`) actually correct?**
  _`Scope refusals` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Claude router (CLAUDE.md)` (e.g. with `Acting principal` and `Ordered header-field pairs`) actually correct?**
  _`Claude router (CLAUDE.md)` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Agent router (AGENTS.md)` (e.g. with `Acting principal` and `Ordered header-field pairs`) actually correct?**
  _`Agent router (AGENTS.md)` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks` to the rest of the system?**
  _219 weakly-connected nodes found - possible documentation gaps or missing edges._