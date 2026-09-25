# Graph Report - .  (2026-09-25)

## Corpus Check
- 219 files · ~115,663 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 929 nodes · 1645 edges · 84 communities (52 shown, 32 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 238 edges (avg confidence: 0.85)
- Token cost: unmetered (host-agent extraction usage unavailable)

## Graph Health
- The initial full extraction omitted 102 raw AST edges to external or excluded symbols and collapsed 43 raw edges onto existing endpoint pairs. Those losses remain for the files this refresh did not re-extract.
- This refresh re-extracted 32 tracked files, 15 code and 17 documents, changed on this branch. It left out the four gitignored build stamps, which the graph has never indexed. Every node and edge it extracted was traced into `graph.json`: 96/96 AST nodes and 258/258 AST edges, and 122/122 semantic nodes and 273/273 semantic edges, each present under its own relation. From the previous graph, all 674 nodes and 1,115 links for files it did not touch are present, and so are its 3 hyperedges.
- Four kinds of loss were resolved rather than accepted:
  - **Imports:** 70 import edges pointed at packages that had no node. They now end at 23 labelled package stubs, and the stub for this repository's own `recorder` package contains its two file nodes.
  - **Cross-document references:** 47 references used a document's bare path stem. They now end at that document's primary node.
  - **Files outside the corpus:** 17 references named files outside the corpus in `ci/`, `openspec/` and `.claude/`. They now end at stubs labelled with each path.
  - **Merge and build losses:** graphify's merge drops the existing graph's hyperedges, and 9 links from unchanged files named nodes the re-extraction renamed. The hyperedges and the remapped links are carried forward. Three pairs held two relations each; they are folded into one edge that lists both, where the build would keep only the last.
- Two defects were fixed at the source:
  - **A lowercase ID collision** merged `Record` and `record` in `conformance/recorder/recorder.go` into one node. The private method was renamed `store`, and no other tracked code file has such a collision.
  - **Fuzzy deduplication** merged two different out-of-corpus design documents, so this refresh ran with it off.
- Health: no dangling or missing endpoints, no self-loops and no collapsed edges. Semantic extraction used 250,209 subagent tokens, with no input and output split available.

## Community Hubs (Navigation)
- [[_COMMUNITY_Review and Testing Discipline|Review and Testing Discipline]]
- [[_COMMUNITY_Architecture and Wire Flow|Architecture and Wire Flow]]
- [[_COMMUNITY_Entry Routers and Conventions|Entry Routers and Conventions]]
- [[_COMMUNITY_Go Conformance Harness|Go Conformance Harness]]
- [[_COMMUNITY_Vault Gates and Stage 0 Rules|Vault Gates and Stage 0 Rules]]
- [[_COMMUNITY_Positioning and Scope Refusals|Positioning and Scope Refusals]]
- [[_COMMUNITY_Dependabot and Unattended Merges|Dependabot and Unattended Merges]]
- [[_COMMUNITY_Capability Documentation|Capability Documentation]]
- [[_COMMUNITY_Threat Model and Operator View|Threat Model and Operator View]]
- [[_COMMUNITY_Build Provenance and Test CI|Build Provenance and Test CI]]
- [[_COMMUNITY_Protocol Fidelity|Protocol Fidelity]]
- [[_COMMUNITY_Recorder Instrument|Recorder Instrument]]
- [[_COMMUNITY_Packaging and Terminator Edge|Packaging and Terminator Edge]]
- [[_COMMUNITY_Recording Origin Server|Recording Origin Server]]
- [[_COMMUNITY_Request Body Framing|Request Body Framing]]
- [[_COMMUNITY_Certificate Key Custody|Certificate Key Custody]]
- [[_COMMUNITY_Decision Register|Decision Register]]
- [[_COMMUNITY_Custom Domain Claims|Custom Domain Claims]]
- [[_COMMUNITY_Sidecar Lifecycle|Sidecar Lifecycle]]
- [[_COMMUNITY_Tunnel Frame Vocabulary|Tunnel Frame Vocabulary]]
- [[_COMMUNITY_Recording Origin Imports|Recording Origin Imports]]
- [[_COMMUNITY_Reference Artifact Provenance|Reference Artifact Provenance]]
- [[_COMMUNITY_Reply Mode Tests|Reply Mode Tests]]
- [[_COMMUNITY_Transport Primitives and WebTransport|Transport Primitives and WebTransport]]
- [[_COMMUNITY_Chunked Framing Tests|Chunked Framing Tests]]
- [[_COMMUNITY_Mount Point Routing|Mount Point Routing]]
- [[_COMMUNITY_Make Check Budget|Make Check Budget]]
- [[_COMMUNITY_Observability Before Hot Path|Observability Before Hot Path]]
- [[_COMMUNITY_Contract and Conformance|Contract and Conformance]]
- [[_COMMUNITY_Proxy Traffic Pipeline|Proxy Traffic Pipeline]]
- [[_COMMUNITY_Framing and Codecs|Framing and Codecs]]
- [[_COMMUNITY_Obsidian Settings|Obsidian Settings]]
- [[_COMMUNITY_Lingering Close Tests|Lingering Close Tests]]
- [[_COMMUNITY_Origin Reply Heads|Origin Reply Heads]]
- [[_COMMUNITY_Capability Declaration|Capability Declaration]]
- [[_COMMUNITY_Explicit Carry-Forward|Explicit Carry-Forward]]
- [[_COMMUNITY_Elixir Mix Project|Elixir Mix Project]]
- [[_COMMUNITY_Credential Scan Design|Credential Scan Design]]
- [[_COMMUNITY_Frame-Shaped Tunnel|Frame-Shaped Tunnel]]
- [[_COMMUNITY_Timeout Taxonomy|Timeout Taxonomy]]
- [[_COMMUNITY_Security Scan Workflow|Security Scan Workflow]]
- [[_COMMUNITY_Gate Documentation Rules|Gate Documentation Rules]]
- [[_COMMUNITY_Affinity Registry|Affinity Registry]]
- [[_COMMUNITY_Resource Bound Definitions|Resource Bound Definitions]]
- [[_COMMUNITY_Terminator Entry Point|Terminator Entry Point]]
- [[_COMMUNITY_Go Lint Configuration|Go Lint Configuration]]
- [[_COMMUNITY_Tunnel Transport Choice|Tunnel Transport Choice]]
- [[_COMMUNITY_Note Classification Rules|Note Classification Rules]]
- [[_COMMUNITY_Capability Note Glob|Capability Note Glob]]
- [[_COMMUNITY_Schema Migration|Schema Migration]]
- [[_COMMUNITY_WebSocket Backpressure Gap|WebSocket Backpressure Gap]]
- [[_COMMUNITY_Cache Reconciliation|Cache Reconciliation]]
- [[_COMMUNITY_Gate Runner Coverage|Gate Runner Coverage]]
- [[_COMMUNITY_Link Resolution Rules|Link Resolution Rules]]
- [[_COMMUNITY_Outbound Sidecar Architecture|Outbound Sidecar Architecture]]
- [[_COMMUNITY_Proxy Unit Test|Proxy Unit Test]]
- [[_COMMUNITY_Clean-Clone Development|Clean-Clone Development]]
- [[_COMMUNITY_Language Conventions|Language Conventions]]
- [[_COMMUNITY_Degraded Condition|Degraded Condition]]
- [[_COMMUNITY_Backend Path Validation|Backend Path Validation]]
- [[_COMMUNITY_Boot-Time Secret Validation|Boot-Time Secret Validation]]
- [[_COMMUNITY_SSRF Validation|SSRF Validation]]
- [[_COMMUNITY_Protected ETS Reads|Protected ETS Reads]]
- [[_COMMUNITY_Hook Header Denylist|Hook Header Denylist]]
- [[_COMMUNITY_Hook Cycle Traversal|Hook Cycle Traversal]]
- [[_COMMUNITY_Jittered Reconnect|Jittered Reconnect]]
- [[_COMMUNITY_Named Check Constraints|Named Check Constraints]]
- [[_COMMUNITY_Versioned Key Derivation|Versioned Key Derivation]]
- [[_COMMUNITY_Soft-Delete Unique Indexes|Soft-Delete Unique Indexes]]
- [[_COMMUNITY_WebSocket Subprotocols|WebSocket Subprotocols]]
- [[_COMMUNITY_Token-Store Encryption|Token-Store Encryption]]
- [[_COMMUNITY_Duplicate Header Loss|Duplicate Header Loss]]
- [[_COMMUNITY_Protocol Research Pass|Protocol Research Pass]]
- [[_COMMUNITY_Generated Artifact Oracle|Generated Artifact Oracle]]
- [[_COMMUNITY_Tracked Reader Settings|Tracked Reader Settings]]
- [[_COMMUNITY_Conformance Go Module|Conformance Go Module]]
- [[_COMMUNITY_Sidecar Go Module|Sidecar Go Module]]
- [[_COMMUNITY_Terminator Go Module|Terminator Go Module]]
- [[_COMMUNITY_Buffered Reader Type|Buffered Reader Type]]

## God Nodes (most connected - your core abstractions)
1. `Decisions in force` - 33 edges
2. `Scope refusals` - 29 edges
3. `Protocol fidelity` - 27 edges
4. `Claude router (CLAUDE.md)` - 26 edges
5. `Agent router (AGENTS.md)` - 25 edges
6. `T` - 23 edges
7. `Blocking objections` - 22 edges
8. `Code rules index` - 21 edges
9. `Reviewing a change` - 20 edges
10. `Topology and runtime` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Pull request policy` --semantically_similar_to--> `One-sitting PR size limit`  [INFERRED] [semantically similar]
  CONTRIBUTING.md → docs/code/reviewing.md
- `PR checks self-test` --semantically_similar_to--> `Every gate is demonstrated to fail`  [INFERRED] [semantically similar]
  .github/workflows/pr.yml → docs/method/rules/gates-are-demonstrated-to-fail.md
- `Agent router (AGENTS.md)` --semantically_similar_to--> `Claude router (CLAUDE.md)`  [INFERRED] [semantically similar]
  AGENTS.md → CLAUDE.md
- `ci/provenance-check.py (startup provenance check)` --references--> `provenance_line()`  [EXTRACTED]
  docs/code/rules/build-provenance-from-one-place.md → proxy/lib/plugboard.ex
- `Every gate demonstrated to fail` --semantically_similar_to--> `ci/proxy-tooling-check.py (planted proxy lint violations)`  [INFERRED] [semantically similar]
  README.md → .github/workflows/test.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Refuse rather than pass on incomplete evidence** — _github_workflows_dependabot_auto_merge_truncation_refusal, _github_workflows_check_full_history_checkout, docs_code_rules_build_provenance_from_one_place_inconclusive_dirty_probe, _github_workflows_dependabot_auto_merge_disarm_step [INFERRED 0.75]
- **Unattended dependency advance control** — _github_dependabot_dependabot_updates, _github_workflows_dependabot_auto_merge_dependabot_auto_merge, _github_workflows_dependabot_auto_merge_patch_only_merge, _github_workflows_dependabot_auto_merge_contract_change_guard, _github_codeowners, ci_gates_correspondences, _github_workflows_test_python_tooling_job [EXTRACTED 1.00]
- **Build provenance derivation and verification chain** — ci_stamp, ci_gates_provenance, ci_provenance_check, docs_code_rules_build_provenance_from_one_place_startup_provenance_line, proxy_lib_plugboard_application_plugboard_application_start, docs_code_rules_build_provenance_from_one_place_single_source_build_provenance [EXTRACTED 1.00]
- **Out-of-scope declaration control enforced by ci/gates/out_of_scope.py** — ci_gates_out_of_scope, docs_method_rules_out_of_scope_containment, docs_method_rules_out_of_scope_byte_unchanged_rule, docs_decisions_d31_out_of_scope_containment, docs_method_follow_ups_refused_specification_revisions [EXTRACTED 1.00]
- **Size ceilings and the declared Python exclusion carried as a follow-up** — ci_gates_size_ceilings, docs_code_rules_module_size_ceiling, docs_code_rules_function_size_ceiling_function_size_ceiling, docs_code_rules_module_size_ceiling_python_out_of_scope, docs_method_follow_ups_harness_size_ceiling_gap [EXTRACTED 1.00]
- **Every exclusion or deferral carries a visible reason and the condition that ends it** — docs_code_rules_no_credential_in_tree_or_history_not_a_live_credential_marker, docs_method_follow_ups_ending_condition, docs_decisions_d31_out_of_scope_containment_declared_vacuity, docs_code_rules_module_size_ceiling_python_out_of_scope [INFERRED 0.75]
- **PR description enforcement chain** — docs_code_reviewing_change_description_questions, docs_code_reviewing_pr_template, _github_pull_request_template_pull_request_template, docs_code_reviewing_review_obligations_gate, docs_code_reviewing_pr_creation_preflight, _github_workflows_pr_pr_body_checks [EXTRACTED 1.00]
- **Single-sourced review enumerations** — docs_code_reviewing_change_description_questions, docs_code_reviewing_review_checklist, docs_code_reviewing_blocking_objections, docs_code_rules_review_obligations_single_sourced_review_obligations_single_sourcing [EXTRACTED 1.00]
- **Adversarial fixtures against banned patterns** — docs_code_testing_adversarial_fixtures, docs_code_banned_patterns_headers_as_a_map_ordered_headers, docs_code_banned_patterns_body_as_a_string_body_octets, docs_code_banned_patterns_method_allowlists_opaque_method_token, docs_code_banned_patterns_read_all_on_a_proxied_body_streaming_body [INFERRED 0.85]

## Communities (84 total, 32 thin omitted)

### Community 0 - "Review and Testing Discipline"
Cohesion: 0.06
Nodes (71): Tests answer (wrong implementation each test rejects), Blocking objections (numbered summary), Contribution policy, Fast tier ten-second budget, Pull request policy, Review checklist (numbered summary), Three test tiers, Contract-first feature sequence (+63 more)

### Community 1 - "Architecture and Wire Flow"
Cohesion: 0.06
Nodes (61): The architecture, Contract/specification/decision/note precedence, How it is carried, What is carried, Where it runs, Sidecar-proven backend liveness, Enumerated error space, The failure taxonomy (+53 more)

### Community 2 - "Entry Routers and Conventions"
Cohesion: 0.06
Nodes (59): .claude/THIRD-PARTY-NOTICES.md (outside the graph corpus), Pull request description, Pre-submit checklist, Pull request template, What breaks if this is wrong, Wire contract impact declaration, Pinned OpenSpec 1.13.0 install, PR body passed via environment (+51 more)

### Community 3 - "Go Conformance Harness"
Cohesion: 0.08
Nodes (41): Cmd, dial(), getAndRead(), Conn, itoa(), lastRecording(), postAndRead(), buildRecordingOrigin() (+33 more)

### Community 4 - "Vault Gates and Stage 0 Rules"
Cohesion: 0.05
Nodes (55): Full-history checkout (fetch-depth 0), No path filter, branch filter or continue-on-error, Vault check workflow, Files-endpoint truncation refusal, Obligation parity check, Scheduled gates and parity checks, ci/gates/code_duplication.py (outside the graph corpus), ci/gates/coverage.py (outside the graph corpus) (+47 more)

### Community 5 - "Positioning and Scope Refusals"
Cohesion: 0.06
Nodes (47): D3 — Capability negotiation and refusal, Reasoned refusal of unsupported request, Sidecar capability declaration, D17 Capability scope and deferrals, Typed error-reason vocabulary, No specification names CORS or Access-Control-Expose-Headers, Exactly one decision register, Generated indexes cannot drift (+39 more)

### Community 6 - "Dependabot and Unattended Merges"
Cohesion: 0.06
Nodes (44): .github/CODEOWNERS, Dependabot update configuration, GitHub Actions ecosystem updates, Go modules ecosystem updates (sidecar, terminator, conformance), Mix ecosystem updates (/proxy), pip ecosystem updates (requirements-dev.txt), Weekly dependency update schedule, Refusal of unattended advance over reviewed paths (+36 more)

### Community 7 - "Capability Documentation"
Cohesion: 0.10
Nodes (38): Code standards, Rule-to-gate correspondence, Knowledge base, Bidirectional documentation currency, Capability index, Observability, Partial installation answer, Signal delivery (+30 more)

### Community 8 - "Threat Model and Operator View"
Cohesion: 0.07
Nodes (36): Matched credential value is never printed, Audit retention conflict, Pre-service configuration validation, Deferred human-facing control plane, Self-contained deployable artifacts, End-to-end sidecar liveness, Installation-wide observability, Migration action surface gap (+28 more)

### Community 9 - "Build Provenance and Test CI"
Cohesion: 0.06
Nodes (32): Component test workflow, Conformance build job, Fast test job, Expected-outcome gating tests, Integration test job, Startup provenance check step, Application (Elixir module outside this repository), ci/expected-outcomes.py (gating baseline check) (+24 more)

### Community 10 - "Protocol Fidelity"
Cohesion: 0.10
Nodes (33): Dual credit windows with liveness and datagram exemption, Reserved v1 frame vocabulary, HTTP/1.1-only edge alternative (rejected), Reserved datagram frame class, Open-ended method tokens, Capability negotiation and refusal, Domain ownership verification, Fair per-stream multiplexing (+25 more)

### Community 11 - "Recorder Instrument"
Cohesion: 0.15
Nodes (17): NewOrdered(), Persist(), T, TestAllOctetsCarriesEveryValueAndALoneContinuationByte(), TestOrderedIsFaithful(), TestPersistWritesOneFilePerExchange(), crypto/sha256 (Go standard library package), encoding/base64 (Go standard library package) (+9 more)

### Community 12 - "Packaging and Terminator Edge"
Cohesion: 0.10
Nodes (23): Declared version ranges, Fixed build provenance, Generated configuration declaration, Negative gate demonstration, Packaging, Published artifact release gate, Stopped artifact declaration, Verifiable artifact content (+15 more)

### Community 13 - "Recording Origin Server"
Cohesion: 0.24
Nodes (17): Closer, closing(), Conn, Reader, isToken(), lingerClose(), main(), readFields() (+9 more)

### Community 14 - "Request Body Framing"
Cohesion: 0.24
Nodes (14): Buffer, chunkSize(), copyOctets(), Reader, octetCount(), readBody(), readChunked(), readFramingLine() (+6 more)

### Community 15 - "Certificate Key Custody"
Cohesion: 0.13
Nodes (16): Certificate lifecycle, Allowed key parameters, Closed custody inventory, Key custody, Key replacement and destruction, Protection at rest, Subject-scoped distribution, Connection phase (+8 more)

### Community 16 - "Decision Register"
Cohesion: 0.22
Nodes (16): D4 Elixir proxy and Go sidecar runtime, D8 Tenant scoping in keys and signatures, Custom-domain claim, proof, issuance sequence, D9 — Domain ownership before issuance, D20 Multi-instance proxy installation, D23 Contract-first conformance suite, D24 Permanent asymmetric version skew, D25 Multi-tenant platform ingress positioning (+8 more)

### Community 17 - "Custom Domain Claims"
Cohesion: 0.17
Nodes (15): Claim-bound challenge, Connection-time certificate selection, Custom-domain traffic parity, Custom domains, Hostname ownership claim, Ownership verification gate, Verification lapse and recheck, Wildcard delegation and exact precedence (+7 more)

### Community 18 - "Sidecar Lifecycle"
Cohesion: 0.15
Nodes (15): Installation trust boundary, Backend hop ownership, Sidecar configuration lifecycle, Sidecar lifecycle, Sidecar program, Tenant-side diagnosis, Credential presentation, Credential store (+7 more)

### Community 19 - "Tunnel Frame Vocabulary"
Cohesion: 0.15
Nodes (13): Bidirectional stream, Cause, Close vocabulary, Commit point, Correlation identifier, Datagram, Exchange, Frame (+5 more)

### Community 20 - "Recording Origin Imports"
Cohesion: 0.29
Nodes (9): T, TestAnEmptyRequestIsStillAQuietEndRatherThanAFinding(), TestATruncatedBodyIsReportedRatherThanReadAsACleanClose(), errors (Go standard library package), io (Go standard library package), net (Go standard library package), plugboard/conformance/recorder (Go package in this repository), testing (Go standard library package) (+1 more)

### Community 21 - "Reference Artifact Provenance"
Cohesion: 0.24
Nodes (11): DCO sign-off workflow, ci/gates/citations.py (outside the graph corpus), Developer Certificate of Origin sign-off, History notes index, Reference citation verification, A cited artifact is obtainable, Obtaining the reference, Pinned Plugboard revision 6756a07 (+3 more)

### Community 22 - "Reply Mode Tests"
Cohesion: 0.24
Nodes (10): exchange(), T, newReply(), T, TestAContradictoryReplyIsRefusedAtStartup(), TestEachFlagCombinationSelectsTheReplyItNames(), TestEachReplyModeWritesWhatItStates(), bytes (Go standard library package) (+2 more)

### Community 23 - "Transport Primitives and WebTransport"
Cohesion: 0.18
Nodes (11): Bidirectional frame stream, D1 — Three transport primitives, QUIC streams with datagrams, Request/response byte stream, Capsule framing alternative (HTTP/2 WebTransport draft), D26 — WebTransport deferred, Deferred WebTransport and HTTP/3 edge, Adversarial review of load-bearing conclusions (+3 more)

### Community 24 - "Chunked Framing Tests"
Cohesion: 0.47
Nodes (9): assertRefused(), chunk(), firstLine(), T, TestAChunkedBodyIsRecordedDeframed(), TestAFieldLineWithoutATokenForItsNameIsRefused(), TestAFramingFieldWhoseNameIsNotATokenIsRefused(), TestMalformedChunkingIsRefused() (+1 more)

### Community 25 - "Mount Point Routing"
Cohesion: 0.22
Nodes (10): Locally configured backend origin, Longest-prefix match, Mount-boundary rewriting, Mount point, Node, Remainder, Reserved path, Role (+2 more)

### Community 26 - "Make Check Budget"
Cohesion: 0.25
Nodes (9): ci/gates/_common.py (outside the graph corpus), ci/gates/meta.py (outside the graph corpus), ci/run-gates.py (outside the graph corpus), D32 — make check holds every tree property on change, inside a declared budget, Meta-gate isolation cross-product, make check wall-clock budget (gate_policy.budget_seconds), docs/decisions generated index, ci/gates/_common.py has no gate of its own (+1 more)

### Community 27 - "Observability Before Hot Path"
Cohesion: 0.28
Nodes (9): Attached metric sink and structured logger, D27 — Observability before hot path, Telemetry consumer attachment test, Real-server WebSocket wire tests, Contract tests against two fictions, Slow feedback incentivizes weak tests, Unconsumed telemetry events, Completeness critic (+1 more)

### Community 28 - "Contract and Conformance"
Cohesion: 0.25
Nodes (9): Conformance run, Conformance suite, Contract version, Implementation under test, Contract-first implementation, Permanent asymmetric version skew, Suite latency as correctness control, Three protocol primitives (+1 more)

### Community 29 - "Proxy Traffic Pipeline"
Cohesion: 0.25
Nodes (8): Administrative middleware pipeline, D5 — Dedicated proxied traffic path, Proxy path before application middleware, D21 Rebuild from scratch, Buffered body disguised as streaming, Request body loss before sidecar, Prior art (reference Plugboard and Telephone), Test volume is not evidence

### Community 30 - "Framing and Codecs"
Cohesion: 0.29
Nodes (8): Contradictory-framing refusal, D6 — Per-hop framing authority, Per-hop framing declarations, Binary interface definition, D18 — Generated binary frame codecs, Generated frame codecs, Raw body octets, Binary payload corruption in JSON

### Community 31 - "Obsidian Settings"
Cohesion: 0.25
Nodes (7): alwaysUpdateLinks, attachmentFolderPath, newLinkFormat, showUnsupportedFiles, strictLineBreaks, useMarkdownLinks, userIgnoreFilters

### Community 32 - "Lingering Close Tests"
Cohesion: 0.53
Nodes (6): Conn, T, serveOnTCP(), TestARefusalOverTCPEndsInACloseRatherThanAReset(), TestARefusedPeerStillSendingIsCutOffAtTheCap(), Pattern()

### Community 33 - "Origin Reply Heads"
Cohesion: 0.67
Nodes (5): writeHead(), writeReply(), writeStatus(), reply, Writer

### Community 34 - "Capability Declaration"
Cohesion: 0.33
Nodes (6): gRPC-Web translation, Baseline, Capability declaration, Capability term collision, Declaration-based skip, Refusal

### Community 35 - "Explicit Carry-Forward"
Cohesion: 0.40
Nodes (6): Cited prior-art inventory, D10 — Explicit cited carry-forward, D10 number collision with the superseded register, Strip-one-segment mount lookup, Terminal-mount invariant, Prior art is not behavioural authority

### Community 36 - "Elixir Mix Project"
Cohesion: 0.40
Nodes (4): Mix.Project (Elixir module outside this repository), Plugboard.MixProject, deps(), project()

### Community 37 - "Credential Scan Design"
Cohesion: 0.50
Nodes (5): ci/gates/decision_register.py (outside the graph corpus), Secret-scan negative controls, Prefix-anchored credential detection (errs toward false negatives), Decision identifier namespacing (unnamespaced D<n> belongs to the register), Generalising the one-register rule to any identifier family (cut)

### Community 38 - "Frame-Shaped Tunnel"
Cohesion: 0.50
Nodes (5): Frame with stream identifier, D2 Frame-shaped tunnel exchange, Correlation-id machinery refusal, Single reply per correlation ID, Frame-shaped streaming tunnel

### Community 39 - "Timeout Taxonomy"
Cohesion: 0.40
Nodes (5): D7 — Timeout taxonomy, Six independently configured timeout bounds, Route class without a total time bound, Per-request Task.async isolation, Single global request timeout

### Community 40 - "Security Scan Workflow"
Cohesion: 0.50
Nodes (4): Dependency vulnerability scan, Elixir security scan, Go vulnerability scan, Security scan workflow

### Community 41 - "Gate Documentation Rules"
Cohesion: 0.50
Nodes (4): Failure messages name the consequence, Gate docstring names requirement and defect, Gate states what it does not decide, Preference rules index

### Community 42 - "Affinity Registry"
Cohesion: 0.50
Nodes (4): Affinity binding, Affinity key, Eligibility, Registry entry

### Community 43 - "Resource Bound Definitions"
Cohesion: 0.50
Nodes (4): Bound, Bound definition gap, Occupancy dimension, Standing-resource dimension

### Community 45 - "Go Lint Configuration"
Cohesion: 0.67
Nodes (3): Narrow test lint exclusions, Shared Go lint configuration, Strict Go lint settings

### Community 46 - "Tunnel Transport Choice"
Cohesion: 0.67
Nodes (3): D19 — v1 tunnel transport, Transport-independent tunnel framing, WebSocket over TLS on port 443

### Community 47 - "Note Classification Rules"
Cohesion: 0.67
Nodes (3): Every capability has a concept note, Every note carries a classification, Every tracked note lives under a declared root

## Knowledge Gaps
- **95 isolated node(s):** `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks`, `attachmentFolderPath`, `showUnsupportedFiles` (+90 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Decisions in force` connect `Decision Register` to `Entry Routers and Conventions`, `Explicit Carry-Forward`, `Vault Gates and Stage 0 Rules`, `Positioning and Scope Refusals`, `Credential Scan Design`, `Frame-Shaped Tunnel`, `Timeout Taxonomy`, `Capability Documentation`, `Dependabot and Unattended Merges`, `Tunnel Transport Choice`, `Transport Primitives and WebTransport`, `Make Check Budget`, `Observability Before Hot Path`, `Proxy Traffic Pipeline`, `Framing and Codecs`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `Claude router (CLAUDE.md)` connect `Entry Routers and Conventions` to `Review and Testing Discipline`, `Architecture and Wire Flow`, `Build Provenance and Test CI`, `Decision Register`, `Reference Artifact Provenance`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `Agent router (AGENTS.md)` connect `Entry Routers and Conventions` to `Review and Testing Discipline`, `Architecture and Wire Flow`, `Build Provenance and Test CI`, `Decision Register`, `Reference Artifact Provenance`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Scope refusals` (e.g. with `Edge hygiene` and `HTTP fidelity`) actually correct?**
  _`Scope refusals` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Claude router (CLAUDE.md)` (e.g. with `Agent router (AGENTS.md)` and `Ordered header-field pairs`) actually correct?**
  _`Claude router (CLAUDE.md)` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Agent router (AGENTS.md)` (e.g. with `Claude router (CLAUDE.md)` and `Ordered header-field pairs`) actually correct?**
  _`Agent router (AGENTS.md)` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks` to the rest of the system?**
  _207 weakly-connected nodes found - possible documentation gaps or missing edges._