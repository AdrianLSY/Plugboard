# Graph Report - .  (2026-09-25)

## Corpus Check
- 210 files · ~106,382 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 764 nodes · 1136 edges · 82 communities (46 shown, 36 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 100 edges (avg confidence: 0.82)
- Token cost: unmetered (host-agent extraction usage unavailable)

## Graph Health
- The initial full extraction omitted 102 raw AST edges to external or excluded symbols and collapsed 43 raw edges onto existing endpoint pairs. Those losses remain in this incremental graph.
- This refresh added 4 nodes and 9 edges, with no lost nodes or edges; all edge endpoints exist and there are no self-loops.

## Community Hubs (Navigation)
- [[_COMMUNITY_Go Conformance Harness|Go Conformance Harness]]
- [[_COMMUNITY_Architecture and Wire Flow|Architecture and Wire Flow]]
- [[_COMMUNITY_Capability Documentation|Capability Documentation]]
- [[_COMMUNITY_Protocol Fidelity|Protocol Fidelity]]
- [[_COMMUNITY_Decision and Index Rules|Decision and Index Rules]]
- [[_COMMUNITY_Repository Checks and PRs|Repository Checks and PRs]]
- [[_COMMUNITY_Custom Domain Routing|Custom Domain Routing]]
- [[_COMMUNITY_Banned Traffic Patterns|Banned Traffic Patterns]]
- [[_COMMUNITY_Code Quality Rules|Code Quality Rules]]
- [[_COMMUNITY_Python Tooling and Component CI|Python Tooling and Component CI]]
- [[_COMMUNITY_Packaging and Operability|Packaging and Operability]]
- [[_COMMUNITY_Documentation Method|Documentation Method]]
- [[_COMMUNITY_Core Architecture Decisions|Core Architecture Decisions]]
- [[_COMMUNITY_Outstanding Specification Gaps|Outstanding Specification Gaps]]
- [[_COMMUNITY_Operational Scope Decisions|Operational Scope Decisions]]
- [[_COMMUNITY_Project Glossary|Project Glossary]]
- [[_COMMUNITY_Certificate Key Custody|Certificate Key Custody]]
- [[_COMMUNITY_Transport Primitive Decisions|Transport Primitive Decisions]]
- [[_COMMUNITY_Sidecar Lifecycle|Sidecar Lifecycle]]
- [[_COMMUNITY_Telemetry and Test Coverage|Telemetry and Test Coverage]]
- [[_COMMUNITY_Contract Conformance|Contract Conformance]]
- [[_COMMUNITY_Framing and Codecs|Framing and Codecs]]
- [[_COMMUNITY_Reference Artifact Provenance|Reference Artifact Provenance]]
- [[_COMMUNITY_Obsidian Settings|Obsidian Settings]]
- [[_COMMUNITY_Listener Trust Boundary|Listener Trust Boundary]]
- [[_COMMUNITY_Capability Declaration|Capability Declaration]]
- [[_COMMUNITY_Credential Scanning|Credential Scanning]]
- [[_COMMUNITY_Proxy Traffic Pipeline|Proxy Traffic Pipeline]]
- [[_COMMUNITY_Timeout Taxonomy|Timeout Taxonomy]]
- [[_COMMUNITY_Credential Roles|Credential Roles]]
- [[_COMMUNITY_Elixir Mix Project|Elixir Mix Project]]
- [[_COMMUNITY_Security Scan Workflow|Security Scan Workflow]]
- [[_COMMUNITY_Gate Documentation Rules|Gate Documentation Rules]]
- [[_COMMUNITY_Capability Refusal|Capability Refusal]]
- [[_COMMUNITY_Prior Art Carry Forward|Prior Art Carry Forward]]
- [[_COMMUNITY_Repository Structure|Repository Structure]]
- [[_COMMUNITY_Affinity Registry|Affinity Registry]]
- [[_COMMUNITY_Resource Bound Definitions|Resource Bound Definitions]]
- [[_COMMUNITY_Proxy Startup Banner|Proxy Startup Banner]]
- [[_COMMUNITY_Go Sidecar Entry Point|Go Sidecar Entry Point]]
- [[_COMMUNITY_Go Lint Configuration|Go Lint Configuration]]
- [[_COMMUNITY_Tunnel Transport Choice|Tunnel Transport Choice]]
- [[_COMMUNITY_Capability Note Conventions|Capability Note Conventions]]
- [[_COMMUNITY_Domain Ownership Proof|Domain Ownership Proof]]
- [[_COMMUNITY_Schema Migration|Schema Migration]]
- [[_COMMUNITY_WebSocket Buffer Bounds|WebSocket Buffer Bounds]]
- [[_COMMUNITY_Configuration Validation|Configuration Validation]]
- [[_COMMUNITY_Tenant Cache Reconciliation|Tenant Cache Reconciliation]]
- [[_COMMUNITY_Markdown Link Integrity|Markdown Link Integrity]]
- [[_COMMUNITY_Outbound Sidecar Architecture|Outbound Sidecar Architecture]]
- [[_COMMUNITY_Elixir Proxy Test|Elixir Proxy Test]]
- [[_COMMUNITY_Clean Clone Development|Clean Clone Development]]
- [[_COMMUNITY_Language Specific Conventions|Language Specific Conventions]]
- [[_COMMUNITY_Degraded Condition|Degraded Condition]]
- [[_COMMUNITY_Backend Path Validation|Backend Path Validation]]
- [[_COMMUNITY_Boot Secret Validation|Boot Secret Validation]]
- [[_COMMUNITY_SSRF Changeset Validation|SSRF Changeset Validation]]
- [[_COMMUNITY_Protected ETS Reads|Protected ETS Reads]]
- [[_COMMUNITY_Disconnect Failure Propagation|Disconnect Failure Propagation]]
- [[_COMMUNITY_Hook Header Denylist|Hook Header Denylist]]
- [[_COMMUNITY_Hook Cycle Detection|Hook Cycle Detection]]
- [[_COMMUNITY_Reconnect Jitter|Reconnect Jitter]]
- [[_COMMUNITY_Database Check Constraints|Database Check Constraints]]
- [[_COMMUNITY_Versioned Key Derivation|Versioned Key Derivation]]
- [[_COMMUNITY_Soft Deletion Indexes|Soft Deletion Indexes]]
- [[_COMMUNITY_WebSocket Subprotocol Negotiation|WebSocket Subprotocol Negotiation]]
- [[_COMMUNITY_Token Store Encryption|Token Store Encryption]]
- [[_COMMUNITY_Cross Tenant Token Authorization|Cross Tenant Token Authorization]]
- [[_COMMUNITY_Duplicate Header Preservation|Duplicate Header Preservation]]
- [[_COMMUNITY_Notifier Test Helper|Notifier Test Helper]]
- [[_COMMUNITY_Correlation Reply Uniqueness|Correlation Reply Uniqueness]]
- [[_COMMUNITY_Protocol Runtime Research|Protocol Runtime Research]]
- [[_COMMUNITY_Out of Scope Files|Out of Scope Files]]
- [[_COMMUNITY_Tracked Reader Settings|Tracked Reader Settings]]
- [[_COMMUNITY_Conformance Go Module|Conformance Go Module]]
- [[_COMMUNITY_Sidecar Go Module|Sidecar Go Module]]
- [[_COMMUNITY_Terminator Go Module|Terminator Go Module]]

## God Nodes (most connected - your core abstractions)
1. `T` - 31 edges
2. `Protocol fidelity` - 25 edges
3. `Code rules index` - 21 edges
4. `Topology and runtime` - 18 edges
5. `Follow-ups` - 17 edges
6. `Decisions in force` - 16 edges
7. `Decision notes index` - 16 edges
8. `Method rules index` - 16 edges
9. `Operator view` - 15 edges
10. `Start()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `Contract change guard` --conceptually_related_to--> `Versioned wire schema`  [INFERRED]
  .github/workflows/dependabot-auto-merge.yml → README.md
- `Versioned contract artifact` --conceptually_related_to--> `Versioned wire schema`  [INFERRED]
  contract/README.md → README.md
- `Conformance suite` --conceptually_related_to--> `Conformance suite as contributor on-ramp`  [INFERRED]
  conformance/README.md → CONTRIBUTING.md
- `Pull request template` --conceptually_related_to--> `Pull request policy`  [INFERRED]
  .github/pull_request_template.md → CONTRIBUTING.md
- `Scheduled gates and parity checks` --conceptually_related_to--> `Documentation vault gates`  [INFERRED]
  .github/workflows/scheduled.yml → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Outbound proxy–tunnel–sidecar flow** — docs_start_here_proxy, docs_glossary_tunnel, docs_glossary_sidecar [EXTRACTED 1.00]
- **Request dispatch flow** — docs_capabilities_routing_mount_points_document, docs_capabilities_tunnel_sidecar_registry_document, docs_capabilities_tunnel_wire_contract_document [EXTRACTED 1.00]
- **Change verification flow** — docs_code_adding_a_feature_document, docs_code_testing_document, docs_code_reviewing_document [EXTRACTED 1.00]
- **One wire contract across all implementations** — docs_code_boundaries_contract_contract, docs_code_boundaries_conformance_conformance, docs_code_boundaries_proxy_proxy, docs_code_boundaries_sidecar_sidecar, docs_code_boundaries_terminator_terminator [EXTRACTED 1.00]
- **Three tier test model** — docs_code_rules_test_tiers_fast_test_tier, docs_code_rules_test_tiers_integration_test_tier, docs_code_rules_test_tiers_conformance_test_tier [EXTRACTED 1.00]
- **Architecture: what, how, and where** — docs_how_architecture_what_is_carried, docs_how_architecture_how_it_is_carried, docs_how_architecture_where_it_runs [EXTRACTED 1.00]
- **Outbound ingress flow** — proxy_readme_component, docs_why_what_it_is_tunnel, sidecar_readme_component, docs_why_what_it_is_mounts, docs_why_what_it_is_registration [EXTRACTED 1.00]

## Communities (82 total, 36 thin omitted)

### Community 0 - "Go Conformance Harness"
Cohesion: 0.05
Nodes (71): TestMalformedFramingIsRefusedRatherThanGuessedAt(), TestWellFramedBodiesAreStillRead(), TestATransferCodingIsStillRefusedAsUnimplemented(), main(), run(), serve(), Conn, closing() (+63 more)

### Community 1 - "Architecture and Wire Flow"
Cohesion: 0.06
Nodes (59): The tenant's view, The failure taxonomy, Frame-shaped tunnel, Topology and runtime, Three transport primitives, The architecture, docs/how index, Outbound sidecar dial (+51 more)

### Community 2 - "Capability Documentation"
Cohesion: 0.07
Nodes (49): HTTP fidelity, Edge hygiene, WebSocket, Wire contract, Tunnel listener, Conformance suite, Sidecar registry, Tenant isolation (+41 more)

### Community 3 - "Protocol Fidelity"
Cohesion: 0.06
Nodes (47): Threat model, Request smuggling, SSRF through the sidecar, Cross-tenant cookie scoping, Certificate issuance from an unverified claim, Cross-tenant writes, Open relay via tunnelling method, Compression amplification (+39 more)

### Community 4 - "Decision and Index Rules"
Cohesion: 0.08
Nodes (44): Exactly one decision register, Generated indexes cannot drift, Alternatives to Plugboard, Multi-tenant platform ingress, ngrok, Cloudflare Tunnel, frp, Tailscale Funnel (+36 more)

### Community 5 - "Repository Checks and PRs"
Cohesion: 0.07
Nodes (45): Contribution policy, make check, Conformance suite as contributor on-ramp, Three test tiers, Fast tier ten-second budget, Review checklist, Blocking objections, Developer Certificate of Origin sign-off (+37 more)

### Community 6 - "Custom Domain Routing"
Cohesion: 0.06
Nodes (40): Node, Mount point, Terminal mount point, Remainder, Longest-prefix match, Reserved path, Routing entry, Hostname claim (+32 more)

### Community 7 - "Banned Traffic Patterns"
Cohesion: 0.15
Nodes (27): Contributor experience, Conformance fixtures as good first issues, Body octets end to end, Dedicated proxied-traffic pipeline, Bounded accumulators and overflow reasons, Ordered header-field pairs, Chunkwise proxied-body emission, Per-hop framing authority (+19 more)

### Community 8 - "Code Quality Rules"
Cohesion: 0.12
Nodes (25): Review obligations single sourcing, Single source build provenance, Ten line duplication threshold, Banned defect classes, Generate sources before compilation, Fast tier latency budget, Recorded red gate debt, Three test tiers (+17 more)

### Community 9 - "Python Tooling and Component CI"
Cohesion: 0.11
Nodes (23): Python quality tooling, Component test workflow, Python tooling CI job, Fast test job, Integration test job, Component lint job, Expected-outcome gating tests, Conformance build job (+15 more)

### Community 10 - "Packaging and Operability"
Cohesion: 0.11
Nodes (22): Instance, Deployable, Client-facing terminator, Lookup surface, Client-facing role, Artifact, Build input, Artifact identity (+14 more)

### Community 11 - "Documentation Method"
Cohesion: 0.19
Nodes (22): The harness and its findings, Documentation rules, Conventions for authoring a note, Supply chain, changelog and versioning, Authority precedence, Method index, Published and computed enumerations reconcile, Gate coverage is an assertion (+14 more)

### Community 12 - "Core Architecture Decisions"
Cohesion: 0.33
Nodes (17): Superseded decision register, Decisions in force, D30 Durable state in PostgreSQL, D31 Out-of-scope declaration containment, D28 Apache-2.0 licensing of authored tree, Decision notes index, D29 Discover gate roster and reconcile invocations, D16 HTTP/2 client edge in v1 (+9 more)

### Community 13 - "Outstanding Specification Gaps"
Cohesion: 0.12
Nodes (17): Follow-ups, Undeclared correspondence drift, CODEOWNERS review blocking gap, Gate coverage count/list mismatch, Configuration/provenance name collision verification, make check latency, Harness size ceiling gap, Forge behavior verification gap (+9 more)

### Community 14 - "Operational Scope Decisions"
Cohesion: 0.22
Nodes (15): Operator view, Multi-instance installation, Self-contained deployable artifacts, Pre-service configuration validation, Operator-supplied root material, Installation-wide observability, Stuck exchange diagnostics, Sidecar registry inspection (+7 more)

### Community 15 - "Project Glossary"
Cohesion: 0.17
Nodes (12): Start here, Docs index, Rule index, Gated rule, Gate planned rule, Preference rule, No owned behaviour in spine, Ordered header fields (+4 more)

### Community 16 - "Certificate Key Custody"
Cohesion: 0.20
Nodes (11): Installation, Custody class, Protection material, Root material, Key custody, Closed custody inventory, Allowed key parameters, Protection at rest (+3 more)

### Community 17 - "Transport Primitive Decisions"
Cohesion: 0.18
Nodes (11): D1 — Three transport primitives, Request/response byte stream, Bidirectional frame stream, QUIC streams with datagrams, D26 — WebTransport deferred, Reserved datagram frame class, Deferred WebTransport and HTTP/3 edge, Adversarial review of load-bearing conclusions (+3 more)

### Community 18 - "Sidecar Lifecycle"
Cohesion: 0.22
Nodes (9): Hop, Liveness, Readiness, Drain, Sidecar program, Sidecar configuration lifecycle, Sidecar lifecycle, Backend hop ownership (+1 more)

### Community 19 - "Telemetry and Test Coverage"
Cohesion: 0.28
Nodes (9): D27 — Observability before hot path, Attached metric sink and structured logger, Telemetry consumer attachment test, Real-server WebSocket wire tests, Contract tests against two fictions, Unconsumed telemetry events, Slow feedback incentivizes weak tests, Adversarially verified prior-art audit (+1 more)

### Community 20 - "Contract Conformance"
Cohesion: 0.25
Nodes (9): Contract version, Conformance suite, Implementation under test, Conformance run, Permanent asymmetric version skew, Wire schema irreversibility, Three protocol primitives, Contract-first implementation (+1 more)

### Community 21 - "Framing and Codecs"
Cohesion: 0.29
Nodes (8): D6 — Per-hop framing authority, Per-hop framing declarations, Contradictory-framing refusal, D18 — Generated binary frame codecs, Binary interface definition, Generated frame codecs, Raw body octets, Binary payload corruption in JSON

### Community 22 - "Reference Artifact Provenance"
Cohesion: 0.36
Nodes (8): Obtaining the reference, Pinned Plugboard revision 6756a07, Pinned Telephone revision 9ccba86, Reference fetch source gap, Reference citation verification, A cited artifact is obtainable, Prior art is not behavioural authority, History notes index

### Community 23 - "Obsidian Settings"
Cohesion: 0.25
Nodes (7): useMarkdownLinks, newLinkFormat, alwaysUpdateLinks, attachmentFolderPath, showUnsupportedFiles, strictLineBreaks, userIgnoreFilters

### Community 24 - "Listener Trust Boundary"
Cohesion: 0.33
Nodes (6): Tunnel, Listener, Observed source, Connection phase, Credential presentation, Installation trust boundary

### Community 25 - "Capability Declaration"
Cohesion: 0.33
Nodes (6): Capability declaration, Baseline, Refusal, Declaration-based skip, Capability term collision, gRPC-Web translation

### Community 26 - "Credential Scanning"
Cohesion: 0.40
Nodes (5): Credential scan of tree and review range, Combined-diff merge scan, Dated credential scan suppression, Prefix-anchored credential detection, Non-disclosing credential findings

### Community 27 - "Proxy Traffic Pipeline"
Cohesion: 0.40
Nodes (5): D5 — Dedicated proxied traffic path, Proxy path before application middleware, Administrative middleware pipeline, Request body loss before sidecar, Buffered body disguised as streaming

### Community 28 - "Timeout Taxonomy"
Cohesion: 0.40
Nodes (5): D7 — Timeout taxonomy, Six independently configured timeout bounds, Route class without a total time bound, Per-request Task.async isolation, Single global request timeout

### Community 29 - "Credential Roles"
Cohesion: 0.40
Nodes (5): Sidecar, Origin-facing role, Credential, Issuing credential, Credential store

### Community 30 - "Elixir Mix Project"
Cohesion: 0.50
Nodes (3): Plugboard.MixProject, project(), deps()

### Community 31 - "Security Scan Workflow"
Cohesion: 0.50
Nodes (4): Security scan workflow, Go vulnerability scan, Dependency vulnerability scan, Elixir security scan

### Community 32 - "Gate Documentation Rules"
Cohesion: 0.50
Nodes (4): Gate states what it does not decide, Gate docstring names requirement and defect, Preference rules index, Failure messages name the consequence

### Community 33 - "Capability Refusal"
Cohesion: 0.67
Nodes (4): D3 — Capability negotiation and refusal, Sidecar capability declaration, Reasoned refusal of unsupported request, Typed error-reason vocabulary

### Community 34 - "Prior Art Carry Forward"
Cohesion: 0.50
Nodes (4): D10 — Explicit cited carry-forward, Cited prior-art inventory, Terminal-mount invariant, Strip-one-segment mount lookup

### Community 35 - "Repository Structure"
Cohesion: 0.50
Nodes (4): D22 — One repository, Single repository tree, No-submodules CI guard, Unreviewed dependency update chain

### Community 36 - "Affinity Registry"
Cohesion: 0.50
Nodes (4): Affinity key, Affinity binding, Registry entry, Eligibility

### Community 37 - "Resource Bound Definitions"
Cohesion: 0.50
Nodes (4): Occupancy dimension, Standing-resource dimension, Bound, Bound definition gap

### Community 40 - "Go Lint Configuration"
Cohesion: 0.67
Nodes (3): Shared Go lint configuration, Strict Go lint settings, Narrow test lint exclusions

### Community 41 - "Tunnel Transport Choice"
Cohesion: 0.67
Nodes (3): D19 — v1 tunnel transport, WebSocket over TLS on port 443, Transport-independent tunnel framing

### Community 42 - "Capability Note Conventions"
Cohesion: 0.67
Nodes (3): Every capability has a concept note, Every tracked note lives under a declared root, Every note carries a classification

## Knowledge Gaps
- **96 isolated node(s):** `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks`, `attachmentFolderPath`, `showUnsupportedFiles` (+91 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **36 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Plugboard dynamic ingress` connect `Repository Checks and PRs` to `Python Tooling and Component CI`, `Decision and Index Rules`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `Reviewing a change` connect `Capability Documentation` to `Repository Checks and PRs`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `Python quality tooling` connect `Python Tooling and Component CI` to `Repository Checks and PRs`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks` to the rest of the system?**
  _239 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Go Conformance Harness` be split into smaller, more focused modules?**
  _Cohesion score 0.052850877192982454 - nodes in this community are weakly interconnected._
- **Should `Architecture and Wire Flow` be split into smaller, more focused modules?**
  _Cohesion score 0.05727644652250146 - nodes in this community are weakly interconnected._
- **Should `Capability Documentation` be split into smaller, more focused modules?**
  _Cohesion score 0.07397959183673469 - nodes in this community are weakly interconnected._
