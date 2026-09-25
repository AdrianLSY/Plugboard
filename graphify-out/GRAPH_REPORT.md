# Graph Report - .  (2026-09-25)

## Corpus Check
- 219 files · ~115,726 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 944 nodes · 1692 edges · 99 communities (67 shown, 32 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 251 edges (avg confidence: 0.85)
- Token cost: unmetered (host-agent extraction usage unavailable)

## Graph Health
- The initial full extraction omitted 102 raw AST edges to external or excluded symbols and collapsed 43 raw edges onto existing endpoint pairs. Those losses remain for the files this branch did not re-extract.
- This branch re-extracted 34 tracked files in two passes: 15 code files and 19 documents. The second pass covered two procedure notes edited after the first. The four gitignored build stamps were left out, since the graph has never indexed them. Every node and edge extracted was traced into `graph.json`, each present under its own relation:
  - 96/96 AST nodes and 258/258 AST edges
  - 141/141 semantic nodes and 329/329 semantic edges
  - from the previous graph, every node and link for files not re-extracted, and all of its hyperedges
- Four kinds of loss were resolved rather than accepted:
  - **Imports:** 70 import edges pointed at packages that had no node. They now end at 23 labelled package stubs, and the stub for this repository's own `recorder` package contains its two file nodes.
  - **Cross-document references:** 47 references used a document's bare path stem. They now end at that document's primary node.
  - **Files outside the corpus:** 17 references named files outside the corpus in `ci/`, `openspec/` and `.claude/`. They now end at stubs labelled with each path.
  - **Merge and build losses:** graphify's merge drops the existing graph's hyperedges, and 9 links from unchanged files named nodes the re-extraction renamed. The hyperedges and the remapped links are carried forward. Three pairs held two relations each; they are folded into one edge that lists both, where the build would keep only the last.
- Two defects were fixed at the source:
  - **A lowercase ID collision** merged `Record` and `record` in `conformance/recorder/recorder.go` into one node. The private method was renamed `store`, and no other tracked code file has such a collision.
  - **Fuzzy deduplication** merged two different out-of-corpus design documents, so both passes ran with it off.
- Health: no dangling or missing endpoints, no self-loops and no collapsed edges. Semantic extraction used 340,787 subagent tokens, with no input and output split available.

## Community Hubs (Navigation)
- [[_COMMUNITY_Go Conformance Harness|Go Conformance Harness]]
- [[_COMMUNITY_Architecture and Wire Flow|Architecture and Wire Flow]]
- [[_COMMUNITY_Protocol Fidelity and Threats|Protocol Fidelity and Threats]]
- [[_COMMUNITY_Packaging and Build Provenance|Packaging and Build Provenance]]
- [[_COMMUNITY_Size Ceilings and Prior Art|Size Ceilings and Prior Art]]
- [[_COMMUNITY_Banned Patterns and Objections|Banned Patterns and Objections]]
- [[_COMMUNITY_Capability Documentation|Capability Documentation]]
- [[_COMMUNITY_Review and Contribution|Review and Contribution]]
- [[_COMMUNITY_Vault Gates and CI Jobs|Vault Gates and CI Jobs]]
- [[_COMMUNITY_Recorder Instrument|Recorder Instrument]]
- [[_COMMUNITY_Entry Routers and Facts|Entry Routers and Facts]]
- [[_COMMUNITY_Feature and Bug Procedures|Feature and Bug Procedures]]
- [[_COMMUNITY_Positioning and Alternatives|Positioning and Alternatives]]
- [[_COMMUNITY_Code Rules Index|Code Rules Index]]
- [[_COMMUNITY_Recording Origin Server|Recording Origin Server]]
- [[_COMMUNITY_Testing Discipline|Testing Discipline]]
- [[_COMMUNITY_Request Body Framing|Request Body Framing]]
- [[_COMMUNITY_Documentation Method|Documentation Method]]
- [[_COMMUNITY_Custom Domain Claims|Custom Domain Claims]]
- [[_COMMUNITY_Scope Refusals|Scope Refusals]]
- [[_COMMUNITY_Operator View|Operator View]]
- [[_COMMUNITY_Unattended Merge Refusal|Unattended Merge Refusal]]
- [[_COMMUNITY_Sidecar Program|Sidecar Program]]
- [[_COMMUNITY_Frame Tunnel and WebTransport|Frame Tunnel and WebTransport]]
- [[_COMMUNITY_Audiences and Success|Audiences and Success]]
- [[_COMMUNITY_Recording Origin Imports|Recording Origin Imports]]
- [[_COMMUNITY_Tunnel Trust Boundary|Tunnel Trust Boundary]]
- [[_COMMUNITY_Decision Register|Decision Register]]
- [[_COMMUNITY_Tunnel Frame Vocabulary|Tunnel Frame Vocabulary]]
- [[_COMMUNITY_Contract-First Conformance|Contract-First Conformance]]
- [[_COMMUNITY_Out-of-Scope Containment|Out-of-Scope Containment]]
- [[_COMMUNITY_Reply Mode Tests|Reply Mode Tests]]
- [[_COMMUNITY_Certificate Key Custody|Certificate Key Custody]]
- [[_COMMUNITY_Python Tooling in Lint|Python Tooling in Lint]]
- [[_COMMUNITY_Chunked Framing Tests|Chunked Framing Tests]]
- [[_COMMUNITY_Observability Before Hot Path|Observability Before Hot Path]]
- [[_COMMUNITY_Mount Point Routing|Mount Point Routing]]
- [[_COMMUNITY_Make Check Budget|Make Check Budget]]
- [[_COMMUNITY_Contract and Conformance|Contract and Conformance]]
- [[_COMMUNITY_Obsidian Settings|Obsidian Settings]]
- [[_COMMUNITY_Python Tool Configuration|Python Tool Configuration]]
- [[_COMMUNITY_Lingering Close Tests|Lingering Close Tests]]
- [[_COMMUNITY_Origin Reply Heads|Origin Reply Heads]]
- [[_COMMUNITY_Python Gate Conventions|Python Gate Conventions]]
- [[_COMMUNITY_Explicit Carry-Forward|Explicit Carry-Forward]]
- [[_COMMUNITY_HTTP2 Client Edge|HTTP/2 Client Edge]]
- [[_COMMUNITY_Elixir Mix Project|Elixir Mix Project]]
- [[_COMMUNITY_One Repository|One Repository]]
- [[_COMMUNITY_Coverage Is an Assertion|Coverage Is an Assertion]]
- [[_COMMUNITY_Follow-Ups and Deferrals|Follow-Ups and Deferrals]]
- [[_COMMUNITY_Timeout Taxonomy|Timeout Taxonomy]]
- [[_COMMUNITY_Generated Frame Codecs|Generated Frame Codecs]]
- [[_COMMUNITY_Credential Roles|Credential Roles]]
- [[_COMMUNITY_Security Scan Workflow|Security Scan Workflow]]
- [[_COMMUNITY_Standards and Knowledge Base|Standards and Knowledge Base]]
- [[_COMMUNITY_Gate Documentation Rules|Gate Documentation Rules]]
- [[_COMMUNITY_Three Transport Primitives|Three Transport Primitives]]
- [[_COMMUNITY_Capability Negotiation|Capability Negotiation]]
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
- `PR checks self-test` --semantically_similar_to--> `Every gate is demonstrated to fail`  [INFERRED] [semantically similar]
  .github/workflows/pr.yml → docs/method/rules/gates-are-demonstrated-to-fail.md
- `Pull request policy` --semantically_similar_to--> `One-sitting PR size limit`  [INFERRED] [semantically similar]
  CONTRIBUTING.md → docs/code/reviewing.md
- `Agent router (AGENTS.md)` --semantically_similar_to--> `Claude router (CLAUDE.md)`  [INFERRED] [semantically similar]
  AGENTS.md → CLAUDE.md
- `D2 Frame-shaped tunnel exchange` --conceptually_related_to--> `Frame-shaped streaming tunnel`  [INFERRED]
  docs/decisions/d02-frame-shaped-tunnel.md → README.md
- `ci/provenance-check.py (startup provenance check)` --references--> `provenance_line()`  [EXTRACTED]
  docs/code/rules/build-provenance-from-one-place.md → proxy/lib/plugboard.ex

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Five-step feature procedure** — docs_code_adding_a_feature_contract_first_sequence, docs_code_adding_a_feature_specify_before_code, docs_code_adding_a_feature_fixture_before_implementation, docs_code_adding_a_feature_owning_component_placement, docs_code_adding_a_feature_travelling_documentation, docs_code_adding_a_feature_procedure_verification [EXTRACTED 1.00]
- **Three-step bug-fix procedure** — docs_code_fixing_a_bug_prior_failing_case, docs_code_fixing_a_bug_discriminating_case, docs_code_fixing_a_bug_smallest_fix, docs_code_adding_a_feature_travelling_documentation, docs_code_fixing_a_bug_procedure_verification [EXTRACTED 1.00]
- **Observed-failing-before-code discipline** — docs_code_adding_a_feature_fixture_before_implementation, docs_code_fixing_a_bug_prior_failing_case, docs_code_fixing_a_bug_broken_input_demonstration, docs_method_rules_gates_are_demonstrated_to_fail_gates_are_demonstrated_to_fail [INFERRED 0.85]
- **Refuse rather than pass on incomplete evidence** — _github_workflows_dependabot_auto_merge_truncation_refusal, _github_workflows_check_full_history_checkout, docs_code_rules_build_provenance_from_one_place_inconclusive_dirty_probe, _github_workflows_dependabot_auto_merge_disarm_step [INFERRED 0.75]
- **Unattended dependency advance control** — _github_dependabot_dependabot_updates, _github_workflows_dependabot_auto_merge_dependabot_auto_merge, _github_workflows_dependabot_auto_merge_patch_only_merge, _github_workflows_dependabot_auto_merge_contract_change_guard, _github_codeowners, ci_gates_correspondences, _github_workflows_test_python_tooling_job [EXTRACTED 1.00]
- **Build provenance derivation and verification chain** — ci_stamp, ci_gates_provenance, ci_provenance_check, docs_code_rules_build_provenance_from_one_place_startup_provenance_line, proxy_lib_plugboard_application_plugboard_application_start, docs_code_rules_build_provenance_from_one_place_single_source_build_provenance [EXTRACTED 1.00]
- **Out-of-scope declaration control enforced by ci/gates/out_of_scope.py** — ci_gates_out_of_scope, docs_method_rules_out_of_scope_containment, docs_method_rules_out_of_scope_byte_unchanged_rule, docs_decisions_d31_out_of_scope_containment, docs_method_follow_ups_refused_specification_revisions [EXTRACTED 1.00]
- **Size ceilings and the declared Python exclusion carried as a follow-up** — ci_gates_size_ceilings, docs_code_rules_module_size_ceiling, docs_code_rules_function_size_ceiling_function_size_ceiling, docs_code_rules_module_size_ceiling_python_out_of_scope, docs_method_follow_ups_harness_size_ceiling_gap [EXTRACTED 1.00]
- **Every exclusion or deferral carries a visible reason and the condition that ends it** — docs_code_rules_no_credential_in_tree_or_history_not_a_live_credential_marker, docs_method_follow_ups_ending_condition, docs_decisions_d31_out_of_scope_containment_declared_vacuity, docs_code_rules_module_size_ceiling_python_out_of_scope [INFERRED 0.75]
- **PR description enforcement chain** — docs_code_reviewing_change_description_questions, docs_code_reviewing_pr_template, _github_pull_request_template_pull_request_template, docs_code_reviewing_review_obligations_gate, docs_code_reviewing_pr_creation_preflight, _github_workflows_pr_pr_body_checks [EXTRACTED 1.00]
- **Single-sourced review enumerations** — docs_code_reviewing_change_description_questions, docs_code_reviewing_review_checklist, docs_code_reviewing_blocking_objections, docs_code_rules_review_obligations_single_sourced_review_obligations_single_sourcing [EXTRACTED 1.00]
- **Adversarial fixtures against banned patterns** — docs_code_testing_adversarial_fixtures, docs_code_banned_patterns_headers_as_a_map_ordered_headers, docs_code_banned_patterns_body_as_a_string_body_octets, docs_code_banned_patterns_method_allowlists_opaque_method_token, docs_code_banned_patterns_read_all_on_a_proxied_body_streaming_body [INFERRED 0.85]

## Communities (99 total, 32 thin omitted)

### Community 0 - "Go Conformance Harness"
Cohesion: 0.08
Nodes (41): Cmd, dial(), getAndRead(), Conn, itoa(), lastRecording(), postAndRead(), buildRecordingOrigin() (+33 more)

### Community 1 - "Architecture and Wire Flow"
Cohesion: 0.06
Nodes (56): The architecture, Contract/specification/decision/note precedence, How it is carried, What is carried, Where it runs, Sidecar-proven backend liveness, Enumerated error space, The failure taxonomy (+48 more)

### Community 2 - "Protocol Fidelity and Threats"
Cohesion: 0.06
Nodes (52): Matched credential value is never printed, Reserved v1 frame vocabulary, HTTP/1.1-only edge alternative (rejected), Open-ended method tokens, Capability negotiation and refusal, Domain ownership verification, Fair per-stream multiplexing, Graceful stream drain (+44 more)

### Community 3 - "Packaging and Build Provenance"
Cohesion: 0.06
Nodes (37): Startup provenance check step, Application (Elixir module outside this repository), ci/gates/provenance.py (build provenance gate), ci/provenance-check.py (startup provenance check), ci/stamp.py (provenance stamp generator), Declared version ranges, Fixed build provenance, Generated configuration declaration (+29 more)

### Community 4 - "Size Ceilings and Prior Art"
Cohesion: 0.07
Nodes (35): DCO sign-off workflow, ci/gates/citations.py (outside the graph corpus), ci/gates/code_duplication.py (outside the graph corpus), ci/gates/size_ceilings.py (outside the graph corpus), Developer Certificate of Origin sign-off, Unwired hooks body enrichment (prior attempt), Function size ceiling, A module is at most 300 non-comment lines (+27 more)

### Community 5 - "Banned Patterns and Objections"
Cohesion: 0.13
Nodes (33): ci/gates/decision_register.py (outside the graph corpus), Blocking objections (numbered summary), Body octets end to end, Ordered header-field pairs, Banned patterns index, Typed wire error codes, Opaque method token, Dedicated proxied-traffic pipeline (+25 more)

### Community 6 - "Capability Documentation"
Cohesion: 0.12
Nodes (32): Capability index, Observability, Partial installation answer, Signal delivery, Migration decomposition rule, Schema migration, Unknown stored attribute preservation, Edge hygiene (+24 more)

### Community 7 - "Review and Contribution"
Cohesion: 0.13
Nodes (29): Pull request description, Pre-submit checklist, Pull request template, What breaks if this is wrong, Wire contract impact declaration, PR body passed via environment, PR checks self-test, PR description check (+21 more)

### Community 8 - "Vault Gates and CI Jobs"
Cohesion: 0.09
Nodes (27): Full-history checkout (fetch-depth 0), No path filter, branch filter or continue-on-error, Vault check workflow, Files-endpoint truncation refusal, Obligation parity check, Scheduled gates and parity checks, Component test workflow, Conformance build job (+19 more)

### Community 9 - "Recorder Instrument"
Cohesion: 0.15
Nodes (17): NewOrdered(), Persist(), T, TestAllOctetsCarriesEveryValueAndALoneContinuationByte(), TestOrderedIsFaithful(), TestPersistWritesOneFilePerExchange(), crypto/sha256 (Go standard library package), encoding/base64 (Go standard library package) (+9 more)

### Community 10 - "Entry Routers and Facts"
Cohesion: 0.17
Nodes (21): Agent router (AGENTS.md), Claude router (CLAUDE.md), Versioned contract artifact, Generated wire codecs, Graphify refresh before a PR, Acting principal, Audit trail, Glossary (+13 more)

### Community 11 - "Feature and Bug Procedures"
Cohesion: 0.13
Nodes (21): Absent-artifact check (ci/gates/entry_points.py), contract/ versioned schema directory, Contract-first feature sequence, Adding a feature, Failing fixture before implementation, Feature procedure verification criteria, Specify before code (four OpenSpec artifacts), Broken-input gate case (ci/broken-inputs/<gate>/) (+13 more)

### Community 12 - "Positioning and Alternatives"
Cohesion: 0.14
Nodes (20): Alternatives to Plugboard, Cloudflare Tunnel, Dynamic-configuration reverse proxy, frp, Tailscale Funnel, ngrok, Health-probe load balancing refusal, NTLM and SPNEGO refusal (+12 more)

### Community 13 - "Code Rules Index"
Cohesion: 0.14
Nodes (18): ci/gen/rule_index.py (outside the graph corpus), Code placed in its owning component, Tests written around defects (prior attempt), Recorded red gate debt, Banned defect classes, Binary asset provenance, Single component boundary statement, Ten line duplication threshold (+10 more)

### Community 14 - "Recording Origin Server"
Cohesion: 0.24
Nodes (17): Closer, closing(), Conn, Reader, isToken(), lingerClose(), main(), readFields() (+9 more)

### Community 15 - "Testing Discipline"
Cohesion: 0.19
Nodes (16): Tests answer (wrong implementation each test rejects), Three test tiers, Conformance suite authority, Fast tier latency budget, Wait helpers never repair awaited state, No weakened test properties, Conformance test tier, Fast test tier (+8 more)

### Community 16 - "Request Body Framing"
Cohesion: 0.24
Nodes (14): Buffer, chunkSize(), copyOctets(), Reader, octetCount(), readBody(), readChunked(), readFramingLine() (+6 more)

### Community 17 - "Documentation Method"
Cohesion: 0.20
Nodes (15): Pinned OpenSpec 1.13.0 install, ci/gates/authoring_channels.py (authoring channels gate), Spine-or-docs:n/a pull-request check (ci/pr/checks.py), Documentation travels with the change, Conventions for authoring a note, Documentation rules, The harness and its findings, Method index (+7 more)

### Community 18 - "Custom Domain Claims"
Cohesion: 0.17
Nodes (15): Claim-bound challenge, Connection-time certificate selection, Custom-domain traffic parity, Custom domains, Hostname ownership claim, Ownership verification gate, Verification lapse and recheck, Wildcard delegation and exact precedence (+7 more)

### Community 19 - "Scope Refusals"
Cohesion: 0.16
Nodes (15): D17 Capability scope and deferrals, Request/response byte stream, Out-of-scope protocol families, No specification names CORS or Access-Control-Expose-Headers, Response cache refusal, WHIP browser CORS gap, HTTP/3 edge deferral, Scope refusals (+7 more)

### Community 20 - "Operator View"
Cohesion: 0.22
Nodes (15): Audit retention conflict, Pre-service configuration validation, Deferred human-facing control plane, Self-contained deployable artifacts, End-to-end sidecar liveness, Installation-wide observability, Migration action surface gap, Multi-instance installation (+7 more)

### Community 21 - "Unattended Merge Refusal"
Cohesion: 0.20
Nodes (14): .github/CODEOWNERS, Dependabot update configuration, GitHub Actions ecosystem updates, Go modules ecosystem updates (sidecar, terminator, conformance), Mix ecosystem updates (/proxy), Weekly dependency update schedule, Refusal of unattended advance over reviewed paths, Dependabot auto-merge workflow (+6 more)

### Community 22 - "Sidecar Program"
Cohesion: 0.15
Nodes (13): gRPC-Web translation, Sidecar configuration lifecycle, Sidecar lifecycle, Sidecar program, Tenant-side diagnosis, Baseline, Capability declaration, Capability term collision (+5 more)

### Community 23 - "Frame Tunnel and WebTransport"
Cohesion: 0.18
Nodes (13): Capsule framing alternative (HTTP/2 WebTransport draft), Dual credit windows with liveness and datagram exemption, D2 Frame-shaped tunnel exchange, Correlation-id machinery refusal, D26 — WebTransport deferred, Deferred WebTransport and HTTP/3 edge, Reserved datagram frame class, Correlation identifier (+5 more)

### Community 24 - "Audiences and Success"
Cohesion: 0.21
Nodes (13): Exactly one decision register, Generated indexes cannot drift, Multi-tenant platform ingress, Three project audiences, Contributors, Operator tie-break, Platform operators, Author portfolio (+5 more)

### Community 25 - "Recording Origin Imports"
Cohesion: 0.29
Nodes (9): T, TestAnEmptyRequestIsStillAQuietEndRatherThanAFinding(), TestATruncatedBodyIsReportedRatherThanReadAsACleanClose(), errors (Go standard library package), io (Go standard library package), net (Go standard library package), plugboard/conformance/recorder (Go package in this repository), testing (Go standard library package) (+1 more)

### Community 26 - "Tunnel Trust Boundary"
Cohesion: 0.17
Nodes (12): Installation trust boundary, Backend hop ownership, Affinity binding, Affinity key, Connection phase, Credential presentation, Eligibility, Hop (+4 more)

### Community 27 - "Decision Register"
Cohesion: 0.29
Nodes (12): D4 Elixir proxy and Go sidecar runtime, D8 Tenant scoping in keys and signatures, Custom-domain claim, proof, issuance sequence, D9 — Domain ownership before issuance, D20 Multi-instance proxy installation, D21 Rebuild from scratch, D24 Permanent asymmetric version skew, D25 Multi-tenant platform ingress positioning (+4 more)

### Community 28 - "Tunnel Frame Vocabulary"
Cohesion: 0.17
Nodes (12): Bidirectional stream, Cause, Close vocabulary, Commit point, Datagram, Exchange, Frame, Frame term collision (+4 more)

### Community 29 - "Contract-First Conformance"
Cohesion: 0.22
Nodes (11): .claude/THIRD-PARTY-NOTICES.md (outside the graph corpus), Conformance suite, Portable conformance binary, Conformance suite as contributor on-ramp, Contributor experience, D23 Contract-first conformance suite, D28 Apache-2.0 licensing of authored tree, Implementer patent and IPR position for the wire contract (+3 more)

### Community 30 - "Out-of-Scope Containment"
Cohesion: 0.29
Nodes (11): ci/gates/out_of_scope.py (outside the graph corpus), ci/gen/indexes.py (outside the graph corpus), D31 — A declared out-of-scope set may not name its own declarant's tree, Containment: who may not declare, instead of who may not edit, declared_by read for a message, not for a decision, Emptied out-of-scope declaration recorded as a declared vacuity, Refused specification revisions (standing obligation), docs/method/rules generated index (+3 more)

### Community 31 - "Reply Mode Tests"
Cohesion: 0.24
Nodes (10): exchange(), T, newReply(), T, TestAContradictoryReplyIsRefusedAtStartup(), TestEachFlagCombinationSelectsTheReplyItNames(), TestEachReplyModeWritesWhatItStates(), bytes (Go standard library package) (+2 more)

### Community 32 - "Certificate Key Custody"
Cohesion: 0.20
Nodes (11): Certificate lifecycle, Allowed key parameters, Closed custody inventory, Key custody, Key replacement and destruction, Protection at rest, Subject-scoped distribution, Custody class (+3 more)

### Community 33 - "Python Tooling in Lint"
Cohesion: 0.29
Nodes (10): pip ecosystem updates (requirements-dev.txt), Component lint job, Python tooling lint steps (in required lint job), ci/gates/build_prerequisites.py (build prerequisite gate), ci/gates/linter_config.py (single linter config gate), ci/go-tooling-check.py (planted Go tooling violations), Single Go linter configuration, make lint-python (+2 more)

### Community 34 - "Chunked Framing Tests"
Cohesion: 0.47
Nodes (9): assertRefused(), chunk(), firstLine(), T, TestAChunkedBodyIsRecordedDeframed(), TestAFieldLineWithoutATokenForItsNameIsRefused(), TestAFramingFieldWhoseNameIsNotATokenIsRefused(), TestMalformedChunkingIsRefused() (+1 more)

### Community 35 - "Observability Before Hot Path"
Cohesion: 0.24
Nodes (10): Fast tier ten-second budget, Attached metric sink and structured logger, D27 — Observability before hot path, Telemetry consumer attachment test, Real-server WebSocket wire tests, Contract tests against two fictions, Slow feedback incentivizes weak tests, Unconsumed telemetry events (+2 more)

### Community 36 - "Mount Point Routing"
Cohesion: 0.22
Nodes (10): Locally configured backend origin, Longest-prefix match, Mount-boundary rewriting, Mount point, Node, Remainder, Reserved path, Role (+2 more)

### Community 37 - "Make Check Budget"
Cohesion: 0.25
Nodes (9): ci/gates/_common.py (outside the graph corpus), ci/gates/meta.py (outside the graph corpus), ci/run-gates.py (outside the graph corpus), D32 — make check holds every tree property on change, inside a declared budget, Meta-gate isolation cross-product, make check wall-clock budget (gate_policy.budget_seconds), docs/decisions generated index, ci/gates/_common.py has no gate of its own (+1 more)

### Community 38 - "Contract and Conformance"
Cohesion: 0.25
Nodes (9): Conformance run, Conformance suite, Contract version, Implementation under test, Contract-first implementation, Permanent asymmetric version skew, Suite latency as correctness control, Three protocol primitives (+1 more)

### Community 39 - "Obsidian Settings"
Cohesion: 0.25
Nodes (7): alwaysUpdateLinks, attachmentFolderPath, newLinkFormat, showUnsupportedFiles, strictLineBreaks, useMarkdownLinks, userIgnoreFilters

### Community 40 - "Python Tool Configuration"
Cohesion: 0.36
Nodes (8): basedpyright CI tooling configuration, Black Python 3.12 configuration, Excluded CI fixture trees, Python quality tool configuration, Ruff Python 3.12 configuration, basedpyright type checker 1.39.10, Black formatter 26.5.1, Ruff linter 0.16.8

### Community 41 - "Lingering Close Tests"
Cohesion: 0.53
Nodes (6): Conn, T, serveOnTCP(), TestARefusalOverTCPEndsInACloseRatherThanAReset(), TestARefusedPeerStillSendingIsCutOffAtTheCap(), Pattern()

### Community 42 - "Origin Reply Heads"
Cohesion: 0.67
Nodes (5): writeHead(), writeReply(), writeStatus(), reply, Writer

### Community 43 - "Python Gate Conventions"
Cohesion: 0.33
Nodes (6): All violations in one run, Common --root and --report-only gate flags, Passing-run gate coverage, Python gate conventions, Python quality toolchain, Standard library only CI gate modules

### Community 44 - "Explicit Carry-Forward"
Cohesion: 0.40
Nodes (6): Cited prior-art inventory, D10 — Explicit cited carry-forward, D10 number collision with the superseded register, Strip-one-segment mount lookup, Terminal-mount invariant, Prior art is not behavioural authority

### Community 45 - "HTTP/2 Client Edge"
Cohesion: 0.40
Nodes (6): D16 HTTP/2 client edge in v1, Proxy-alone edge topology, Separate contract-speaking HTTP/2 edge terminator, Client-facing role, Client-facing terminator, Full gRPC ingress refusal

### Community 46 - "Elixir Mix Project"
Cohesion: 0.40
Nodes (4): Mix.Project (Elixir module outside this repository), Plugboard.MixProject, deps(), project()

### Community 47 - "One Repository"
Cohesion: 0.40
Nodes (5): Patch-only unattended merge, D22 — One repository, No-submodules CI guard, Single repository tree, Unreviewed dependency update chain

### Community 48 - "Coverage Is an Assertion"
Cohesion: 0.50
Nodes (5): ci/gates/coverage.py (outside the graph corpus), Coverage gate rerunning every gate (removed double run), Coverage count and covered list can disagree, Gate coverage is an assertion, Violating inputs declare their failures

### Community 49 - "Follow-Ups and Deferrals"
Cohesion: 0.40
Nodes (5): not-a-live-credential: marker (dated suppression), Follow-ups, Conforming-input fixture tree per prose-shape gate, A deferral names what ends it, openspec/changes/archive/2026-09-12-harden-vault-harness/design.md (outside the graph corpus)

### Community 50 - "Timeout Taxonomy"
Cohesion: 0.40
Nodes (5): D7 — Timeout taxonomy, Six independently configured timeout bounds, Route class without a total time bound, Per-request Task.async isolation, Single global request timeout

### Community 51 - "Generated Frame Codecs"
Cohesion: 0.50
Nodes (5): Binary interface definition, D18 — Generated binary frame codecs, Generated frame codecs, Raw body octets, Dependency licensing audit (GPL-2.0-only) and notices file

### Community 52 - "Credential Roles"
Cohesion: 0.40
Nodes (5): Credential, Credential store, Issuing credential, Origin-facing role, Sidecar

### Community 53 - "Security Scan Workflow"
Cohesion: 0.50
Nodes (4): Dependency vulnerability scan, Elixir security scan, Go vulnerability scan, Security scan workflow

### Community 54 - "Standards and Knowledge Base"
Cohesion: 0.50
Nodes (4): Code standards, Rule-to-gate correspondence, Knowledge base, Bidirectional documentation currency

### Community 55 - "Gate Documentation Rules"
Cohesion: 0.50
Nodes (4): Failure messages name the consequence, Gate docstring names requirement and defect, Gate states what it does not decide, Preference rules index

### Community 56 - "Three Transport Primitives"
Cohesion: 0.50
Nodes (4): Bidirectional frame stream, D1 — Three transport primitives, QUIC streams with datagrams, Request/response byte stream

### Community 57 - "Capability Negotiation"
Cohesion: 0.67
Nodes (4): D3 — Capability negotiation and refusal, Reasoned refusal of unsupported request, Sidecar capability declaration, Typed error-reason vocabulary

### Community 58 - "Resource Bound Definitions"
Cohesion: 0.50
Nodes (4): Bound, Bound definition gap, Occupancy dimension, Standing-resource dimension

### Community 60 - "Go Lint Configuration"
Cohesion: 0.67
Nodes (3): Narrow test lint exclusions, Shared Go lint configuration, Strict Go lint settings

### Community 61 - "Tunnel Transport Choice"
Cohesion: 0.67
Nodes (3): D19 — v1 tunnel transport, Transport-independent tunnel framing, WebSocket over TLS on port 443

### Community 62 - "Note Classification Rules"
Cohesion: 0.67
Nodes (3): Every capability has a concept note, Every note carries a classification, Every tracked note lives under a declared root

## Knowledge Gaps
- **95 isolated node(s):** `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks`, `attachmentFolderPath`, `showUnsupportedFiles` (+90 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Decisions in force` connect `Decision Register` to `Observability Before Hot Path`, `Size Ceilings and Prior Art`, `Banned Patterns and Objections`, `Make Check Budget`, `Entry Routers and Facts`, `Explicit Carry-Forward`, `HTTP/2 Client Edge`, `One Repository`, `Timeout Taxonomy`, `Scope Refusals`, `Generated Frame Codecs`, `Contract-First Conformance`, `Unattended Merge Refusal`, `Frame Tunnel and WebTransport`, `Three Transport Primitives`, `Capability Negotiation`, `Tunnel Transport Choice`, `Out-of-Scope Containment`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `Claude router (CLAUDE.md)` connect `Entry Routers and Facts` to `Size Ceilings and Prior Art`, `Banned Patterns and Objections`, `Review and Contribution`, `Code Rules Index`, `Testing Discipline`, `Documentation Method`, `Decision Register`, `Contract-First Conformance`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `Agent router (AGENTS.md)` connect `Entry Routers and Facts` to `Size Ceilings and Prior Art`, `Banned Patterns and Objections`, `Review and Contribution`, `Code Rules Index`, `Testing Discipline`, `Documentation Method`, `Decision Register`, `Contract-First Conformance`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Scope refusals` (e.g. with `Edge hygiene` and `HTTP fidelity`) actually correct?**
  _`Scope refusals` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Claude router (CLAUDE.md)` (e.g. with `Agent router (AGENTS.md)` and `Ordered header-field pairs`) actually correct?**
  _`Claude router (CLAUDE.md)` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Agent router (AGENTS.md)` (e.g. with `Claude router (CLAUDE.md)` and `Ordered header-field pairs`) actually correct?**
  _`Agent router (AGENTS.md)` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks` to the rest of the system?**
  _206 weakly-connected nodes found - possible documentation gaps or missing edges._