# Graph Report - .  (2026-09-25)

## Corpus Check
- 208 files · ~106,266 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 745 nodes · 1102 edges · 80 communities (44 shown, 36 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 101 edges (avg confidence: 0.82)
- Token cost: unmetered (host-agent extraction usage unavailable)

## Graph Health
- 102 raw AST edges refer to external or excluded symbols and are absent from the graph (95 Go package imports, 5 Obsidian ignore-list references, 2 other imports).
- 43 raw edges collapse onto existing endpoint pairs in the default undirected graph; 3 also share directed endpoints. Relation detail may be lost for those pairs.

## Community Hubs (Navigation)
- [[_COMMUNITY_Go Conformance Harness|Go Conformance Harness]]
- [[_COMMUNITY_Architecture and Wire Flow|Architecture and Wire Flow]]
- [[_COMMUNITY_Repository Checks and PRs|Repository Checks and PRs]]
- [[_COMMUNITY_Capability Documentation|Capability Documentation]]
- [[_COMMUNITY_Protocol Fidelity|Protocol Fidelity]]
- [[_COMMUNITY_Decision and Index Rules|Decision and Index Rules]]
- [[_COMMUNITY_Custom Domain Routing|Custom Domain Routing]]
- [[_COMMUNITY_Banned Traffic Patterns|Banned Traffic Patterns]]
- [[_COMMUNITY_Code Quality Rules|Code Quality Rules]]
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
- `Pull request template` --conceptually_related_to--> `Pull request policy`  [INFERRED]
  .github/pull_request_template.md → CONTRIBUTING.md
- `Permanent asymmetric version skew` --references--> `Telephone sidecar`  [EXTRACTED]
  docs/why/version-skew.md → README.md
- `Outbound sidecar tunnel` --references--> `Telephone sidecar`  [EXTRACTED]
  docs/why/what-it-is.md → README.md

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

## Communities (80 total, 36 thin omitted)

### Community 0 - "Go Conformance Harness"
Cohesion: 0.05
Nodes (71): Closer, Cmd, TestATransferCodingIsStillRefusedAsUnimplemented(), TestMalformedFramingIsRefusedRatherThanGuessedAt(), TestWellFramedBodiesAreStillRead(), closing(), Conn, main() (+63 more)

### Community 1 - "Architecture and Wire Flow"
Cohesion: 0.06
Nodes (59): The architecture, Contract/specification/decision/note precedence, How it is carried, What is carried, Where it runs, Sidecar-proven backend liveness, Enumerated error space, The failure taxonomy (+51 more)

### Community 2 - "Repository Checks and PRs"
Cohesion: 0.05
Nodes (52): Dependabot GitHub Actions updates, Weekly GitHub Actions dependency updates, Pull request template, Wire contract impact declaration, Vault check workflow, DCO sign-off workflow, Contract change guard, Dependabot auto-merge workflow (+44 more)

### Community 3 - "Capability Documentation"
Cohesion: 0.07
Nodes (49): Code standards, Rule-to-gate correspondence, Knowledge base, Bidirectional documentation currency, Capability index, Observability, Partial installation answer, Signal delivery (+41 more)

### Community 4 - "Protocol Fidelity"
Cohesion: 0.06
Nodes (47): Open-ended method tokens, Capability negotiation and refusal, Domain ownership verification, Fair per-stream multiplexing, Graceful stream drain, Sidecar gRPC-Web bridge, Incremental streaming and backpressure, Interim responses (+39 more)

### Community 5 - "Decision and Index Rules"
Cohesion: 0.08
Nodes (42): Exactly one decision register, Generated indexes cannot drift, Alternatives to Plugboard, Cloudflare Tunnel, Dynamic-configuration reverse proxy, frp, Tailscale Funnel, Multi-tenant platform ingress (+34 more)

### Community 6 - "Custom Domain Routing"
Cohesion: 0.06
Nodes (40): Claim-bound challenge, Connection-time certificate selection, Custom-domain traffic parity, Custom domains, Hostname ownership claim, Ownership verification gate, Verification lapse and recheck, Wildcard delegation and exact precedence (+32 more)

### Community 7 - "Banned Traffic Patterns"
Cohesion: 0.13
Nodes (29): Body octets end to end, Ordered header-field pairs, Banned patterns index, Typed wire error codes, Opaque method token, Dedicated proxied-traffic pipeline, Chunkwise proxied-body emission, Per-hop framing authority (+21 more)

### Community 8 - "Code Quality Rules"
Cohesion: 0.12
Nodes (25): Recorded red gate debt, Banned defect classes, Binary asset provenance, Single source build provenance, Single component boundary statement, Conformance suite authority, Ten line duplication threshold, Fast tier latency budget (+17 more)

### Community 9 - "Packaging and Operability"
Cohesion: 0.11
Nodes (22): Declared version ranges, Fixed build provenance, Generated configuration declaration, Negative gate demonstration, Packaging, Published artifact release gate, Stopped artifact declaration, Verifiable artifact content (+14 more)

### Community 10 - "Documentation Method"
Cohesion: 0.19
Nodes (22): Authority precedence, Conventions for authoring a note, Documentation rules, The harness and its findings, Method index, Conventions reach both authoring channels, Cited artifacts are obtainable, Gate coverage is an assertion (+14 more)

### Community 11 - "Core Architecture Decisions"
Cohesion: 0.33
Nodes (17): D2 Frame-shaped tunnel exchange, D4 Elixir proxy and Go sidecar runtime, D8 Tenant scoping in keys and signatures, D16 HTTP/2 client edge in v1, D17 Capability scope and deferrals, D20 Multi-instance proxy installation, D21 Rebuild from scratch, D23 Contract-first conformance suite (+9 more)

### Community 12 - "Outstanding Specification Gaps"
Cohesion: 0.12
Nodes (17): CODEOWNERS review blocking gap, Undeclared correspondence drift, Credential and key-custody specification link gap, Dependency licensing follow-up, Follow-ups, Forge behavior verification gap, Gate coverage count/list mismatch, Harness size ceiling gap (+9 more)

### Community 13 - "Operational Scope Decisions"
Cohesion: 0.22
Nodes (15): Audit retention conflict, Pre-service configuration validation, Deferred human-facing control plane, Self-contained deployable artifacts, End-to-end sidecar liveness, Installation-wide observability, Migration action surface gap, Multi-instance installation (+7 more)

### Community 14 - "Project Glossary"
Cohesion: 0.17
Nodes (12): Glossary, Docs index, Bounded accumulators, Conformance suite authority, Fast test tier latency budget, Gate planned rule, Gated rule, No owned behaviour in spine (+4 more)

### Community 15 - "Certificate Key Custody"
Cohesion: 0.20
Nodes (11): Certificate lifecycle, Allowed key parameters, Closed custody inventory, Key custody, Key replacement and destruction, Protection at rest, Subject-scoped distribution, Custody class (+3 more)

### Community 16 - "Transport Primitive Decisions"
Cohesion: 0.18
Nodes (11): Bidirectional frame stream, D1 — Three transport primitives, QUIC streams with datagrams, Request/response byte stream, D26 — WebTransport deferred, Deferred WebTransport and HTTP/3 edge, Reserved datagram frame class, Adversarial review of load-bearing conclusions (+3 more)

### Community 17 - "Sidecar Lifecycle"
Cohesion: 0.22
Nodes (9): Backend hop ownership, Sidecar configuration lifecycle, Sidecar lifecycle, Sidecar program, Tenant-side diagnosis, Drain, Hop, Liveness (+1 more)

### Community 18 - "Telemetry and Test Coverage"
Cohesion: 0.28
Nodes (9): Attached metric sink and structured logger, D27 — Observability before hot path, Telemetry consumer attachment test, Real-server WebSocket wire tests, Contract tests against two fictions, Slow feedback incentivizes weak tests, Unconsumed telemetry events, Completeness critic (+1 more)

### Community 19 - "Contract Conformance"
Cohesion: 0.25
Nodes (9): Conformance run, Conformance suite, Contract version, Implementation under test, Contract-first implementation, Permanent asymmetric version skew, Suite latency as correctness control, Three protocol primitives (+1 more)

### Community 20 - "Framing and Codecs"
Cohesion: 0.29
Nodes (8): Contradictory-framing refusal, D6 — Per-hop framing authority, Per-hop framing declarations, Binary interface definition, D18 — Generated binary frame codecs, Generated frame codecs, Raw body octets, Binary payload corruption in JSON

### Community 21 - "Reference Artifact Provenance"
Cohesion: 0.36
Nodes (8): History notes index, Reference citation verification, A cited artifact is obtainable, Obtaining the reference, Pinned Plugboard revision 6756a07, Pinned Telephone revision 9ccba86, Reference fetch source gap, Prior art is not behavioural authority

### Community 22 - "Obsidian Settings"
Cohesion: 0.25
Nodes (7): alwaysUpdateLinks, attachmentFolderPath, newLinkFormat, showUnsupportedFiles, strictLineBreaks, useMarkdownLinks, userIgnoreFilters

### Community 23 - "Listener Trust Boundary"
Cohesion: 0.33
Nodes (6): Installation trust boundary, Connection phase, Credential presentation, Listener, Observed source, Tunnel

### Community 24 - "Capability Declaration"
Cohesion: 0.33
Nodes (6): gRPC-Web translation, Baseline, Capability declaration, Capability term collision, Declaration-based skip, Refusal

### Community 25 - "Credential Scanning"
Cohesion: 0.40
Nodes (5): Credential scan of tree and review range, Combined-diff merge scan, Non-disclosing credential findings, Prefix-anchored credential detection, Dated credential scan suppression

### Community 26 - "Proxy Traffic Pipeline"
Cohesion: 0.40
Nodes (5): Administrative middleware pipeline, D5 — Dedicated proxied traffic path, Proxy path before application middleware, Buffered body disguised as streaming, Request body loss before sidecar

### Community 27 - "Timeout Taxonomy"
Cohesion: 0.40
Nodes (5): D7 — Timeout taxonomy, Six independently configured timeout bounds, Route class without a total time bound, Per-request Task.async isolation, Single global request timeout

### Community 28 - "Credential Roles"
Cohesion: 0.40
Nodes (5): Credential, Credential store, Issuing credential, Origin-facing role, Sidecar

### Community 29 - "Elixir Mix Project"
Cohesion: 0.50
Nodes (3): Plugboard.MixProject, deps(), project()

### Community 30 - "Security Scan Workflow"
Cohesion: 0.50
Nodes (4): Dependency vulnerability scan, Elixir security scan, Go vulnerability scan, Security scan workflow

### Community 31 - "Gate Documentation Rules"
Cohesion: 0.67
Nodes (4): Failure messages name the consequence, Gate docstring names requirement and defect, Gate states what it does not decide, Preference rules index

### Community 32 - "Capability Refusal"
Cohesion: 0.67
Nodes (4): D3 — Capability negotiation and refusal, Reasoned refusal of unsupported request, Sidecar capability declaration, Typed error-reason vocabulary

### Community 33 - "Prior Art Carry Forward"
Cohesion: 0.50
Nodes (4): Cited prior-art inventory, D10 — Explicit cited carry-forward, Strip-one-segment mount lookup, Terminal-mount invariant

### Community 34 - "Repository Structure"
Cohesion: 0.50
Nodes (4): D22 — One repository, No-submodules CI guard, Single repository tree, Unreviewed dependency update chain

### Community 35 - "Affinity Registry"
Cohesion: 0.50
Nodes (4): Affinity binding, Affinity key, Eligibility, Registry entry

### Community 36 - "Resource Bound Definitions"
Cohesion: 0.50
Nodes (4): Bound, Bound definition gap, Occupancy dimension, Standing-resource dimension

### Community 39 - "Tunnel Transport Choice"
Cohesion: 0.67
Nodes (3): D19 — v1 tunnel transport, Transport-independent tunnel framing, WebSocket over TLS on port 443

### Community 40 - "Capability Note Conventions"
Cohesion: 0.67
Nodes (3): Every capability has a concept note, Every note carries a classification, Every tracked note lives under a declared root

## Knowledge Gaps
- **83 isolated node(s):** `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks`, `attachmentFolderPath`, `showUnsupportedFiles` (+78 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **36 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Tunnel` connect `Listener Trust Boundary` to `Affinity Registry`, `Custom Domain Routing`, `Sidecar Lifecycle`, `Contract Conformance`, `Capability Declaration`, `Credential Roles`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `Sidecar program` connect `Sidecar Lifecycle` to `Custom Domain Routing`, `Packaging and Operability`, `Contract Conformance`, `Listener Trust Boundary`, `Capability Declaration`, `Credential Roles`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `Key custody` connect `Certificate Key Custody` to `Credential Roles`, `Custom Domain Routing`, `Listener Trust Boundary`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **What connects `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks` to the rest of the system?**
  _230 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Go Conformance Harness` be split into smaller, more focused modules?**
  _Cohesion score 0.052850877192982454 - nodes in this community are weakly interconnected._
- **Should `Architecture and Wire Flow` be split into smaller, more focused modules?**
  _Cohesion score 0.05727644652250146 - nodes in this community are weakly interconnected._
- **Should `Repository Checks and PRs` be split into smaller, more focused modules?**
  _Cohesion score 0.053544494720965306 - nodes in this community are weakly interconnected._