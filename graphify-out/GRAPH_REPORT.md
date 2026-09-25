# Graph Report - .  (2026-09-25)

## Corpus Check
- 219 files · ~115,754 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 948 nodes · 1711 edges · 87 communities (55 shown, 32 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 258 edges (avg confidence: 0.85)
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
- A third pass re-extracted `.github/workflows/security.yml` after its Trivy scan began skipping `handoff/`, and traced it the same way: 8/8 nodes and 24/24 edges. Every node, link and hyperedge the graph held for other files is still present, and two parallel edges were folded with both relations kept.
- Health: no dangling or missing endpoints, no self-loops and no collapsed edges. Semantic extraction used 416,118 subagent tokens across the three passes, with no input and output split available.

## Community Hubs (Navigation)
- [[_COMMUNITY_Routers, Review and Testing|Routers, Review and Testing]]
- [[_COMMUNITY_Go Conformance Harness|Go Conformance Harness]]
- [[_COMMUNITY_Architecture and Wire Flow|Architecture and Wire Flow]]
- [[_COMMUNITY_Positioning and Scope Refusals|Positioning and Scope Refusals]]
- [[_COMMUNITY_Protocol Fidelity and Threats|Protocol Fidelity and Threats]]
- [[_COMMUNITY_Banned Patterns and Objections|Banned Patterns and Objections]]
- [[_COMMUNITY_Procedures and Code Rules|Procedures and Code Rules]]
- [[_COMMUNITY_Capability Documentation|Capability Documentation]]
- [[_COMMUNITY_Build Provenance and Stamps|Build Provenance and Stamps]]
- [[_COMMUNITY_Recorder Instrument|Recorder Instrument]]
- [[_COMMUNITY_Packaging and Terminator Edge|Packaging and Terminator Edge]]
- [[_COMMUNITY_Decision Register|Decision Register]]
- [[_COMMUNITY_Request Body Framing|Request Body Framing]]
- [[_COMMUNITY_Recording Origin Server|Recording Origin Server]]
- [[_COMMUNITY_Recording Origin Imports|Recording Origin Imports]]
- [[_COMMUNITY_Sidecar and Tunnel Roles|Sidecar and Tunnel Roles]]
- [[_COMMUNITY_Unattended Merge Refusal|Unattended Merge Refusal]]
- [[_COMMUNITY_Vault Checks and Security CI|Vault Checks and Security CI]]
- [[_COMMUNITY_Custom Domain Claims|Custom Domain Claims]]
- [[_COMMUNITY_Python Tool Configuration|Python Tool Configuration]]
- [[_COMMUNITY_Operator View|Operator View]]
- [[_COMMUNITY_Certificate Key Custody|Certificate Key Custody]]
- [[_COMMUNITY_Primitives and Frame Tunnel|Primitives and Frame Tunnel]]
- [[_COMMUNITY_Credential Scan and Follow-Ups|Credential Scan and Follow-Ups]]
- [[_COMMUNITY_Tunnel Frame Vocabulary|Tunnel Frame Vocabulary]]
- [[_COMMUNITY_Out-of-Scope Containment|Out-of-Scope Containment]]
- [[_COMMUNITY_Chunked Framing Tests|Chunked Framing Tests]]
- [[_COMMUNITY_Reference Provenance and Sign-Off|Reference Provenance and Sign-Off]]
- [[_COMMUNITY_Prior Art and Rebuild|Prior Art and Rebuild]]
- [[_COMMUNITY_Test Workflow Jobs|Test Workflow Jobs]]
- [[_COMMUNITY_Mount Point Routing|Mount Point Routing]]
- [[_COMMUNITY_One Repository|One Repository]]
- [[_COMMUNITY_Make Check Budget|Make Check Budget]]
- [[_COMMUNITY_Reply Mode Tests|Reply Mode Tests]]
- [[_COMMUNITY_Generated Frame Codecs|Generated Frame Codecs]]
- [[_COMMUNITY_Observability Before Hot Path|Observability Before Hot Path]]
- [[_COMMUNITY_Contract and Conformance|Contract and Conformance]]
- [[_COMMUNITY_Python Tooling in Lint|Python Tooling in Lint]]
- [[_COMMUNITY_Obsidian Settings|Obsidian Settings]]
- [[_COMMUNITY_Coverage Is an Assertion|Coverage Is an Assertion]]
- [[_COMMUNITY_Origin Reply Heads|Origin Reply Heads]]
- [[_COMMUNITY_Capability Declaration|Capability Declaration]]
- [[_COMMUNITY_Explicit Carry-Forward|Explicit Carry-Forward]]
- [[_COMMUNITY_Timeout Taxonomy|Timeout Taxonomy]]
- [[_COMMUNITY_Gate Documentation Rules|Gate Documentation Rules]]
- [[_COMMUNITY_Affinity Registry|Affinity Registry]]
- [[_COMMUNITY_Resource Bound Definitions|Resource Bound Definitions]]
- [[_COMMUNITY_Adversarial Research Review|Adversarial Research Review]]
- [[_COMMUNITY_Terminator Entry Point|Terminator Entry Point]]
- [[_COMMUNITY_Go Lint Configuration|Go Lint Configuration]]
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
- `Every gate demonstrated to fail` --semantically_similar_to--> `ci/proxy-tooling-check.py (planted proxy lint violations)`  [INFERRED] [semantically similar]
  README.md → .github/workflows/test.yml
- `Scheduled gates and parity checks` --conceptually_related_to--> `Documentation vault gates`  [INFERRED]
  .github/workflows/scheduled.yml → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Build-stamp prerequisite for scanners that bypass make** — _github_workflows_security_go_vulnerability_scan, _github_workflows_security_elixir_security_scan, makefile_stamp, ci_gates_build_prerequisites [INFERRED 0.85]
- **Declared-workflow enforcement of the security scan** — _github_workflows_security_security_workflow, ci_vault, ci_gates_runner, ci_gates_correspondences [EXTRACTED 1.00]
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

## Communities (87 total, 32 thin omitted)

### Community 0 - "Routers, Review and Testing"
Cohesion: 0.06
Nodes (66): Pull request description, Pre-submit checklist, Pull request template, Tests answer (wrong implementation each test rejects), What breaks if this is wrong, Wire contract impact declaration, PR body passed via environment, PR checks self-test (+58 more)

### Community 1 - "Go Conformance Harness"
Cohesion: 0.08
Nodes (41): Cmd, dial(), getAndRead(), Conn, itoa(), lastRecording(), postAndRead(), buildRecordingOrigin() (+33 more)

### Community 2 - "Architecture and Wire Flow"
Cohesion: 0.06
Nodes (55): The architecture, Contract/specification/decision/note precedence, How it is carried, What is carried, Where it runs, Sidecar-proven backend liveness, Enumerated error space, The failure taxonomy (+47 more)

### Community 3 - "Positioning and Scope Refusals"
Cohesion: 0.06
Nodes (52): D3 — Capability negotiation and refusal, Reasoned refusal of unsupported request, Sidecar capability declaration, D17 Capability scope and deferrals, Typed error-reason vocabulary, Request/response byte stream, Out-of-scope protocol families, No specification names CORS or Access-Control-Expose-Headers (+44 more)

### Community 4 - "Protocol Fidelity and Threats"
Cohesion: 0.06
Nodes (51): Matched credential value is never printed, Reserved v1 frame vocabulary, HTTP/1.1-only edge alternative (rejected), Open-ended method tokens, Capability negotiation and refusal, Domain ownership verification, Fair per-stream multiplexing, Graceful stream drain (+43 more)

### Community 5 - "Banned Patterns and Objections"
Cohesion: 0.08
Nodes (49): ci/gates/code_duplication.py (outside the graph corpus), ci/gates/decision_register.py (outside the graph corpus), ci/gates/size_ceilings.py (outside the graph corpus), ci/gen/rule_index.py (outside the graph corpus), Blocking objections (numbered summary), Body octets end to end, Ordered header-field pairs, Banned patterns index (+41 more)

### Community 6 - "Procedures and Code Rules"
Cohesion: 0.08
Nodes (45): Fast tier ten-second budget, Three test tiers, Absent-artifact check (ci/gates/entry_points.py), contract/ versioned schema directory, Contract-first feature sequence, Adding a feature, Failing fixture before implementation, Code placed in its owning component (+37 more)

### Community 7 - "Capability Documentation"
Cohesion: 0.10
Nodes (38): Code standards, Rule-to-gate correspondence, Knowledge base, Bidirectional documentation currency, Capability index, Observability, Partial installation answer, Signal delivery (+30 more)

### Community 8 - "Build Provenance and Stamps"
Cohesion: 0.07
Nodes (27): Dependency vulnerability scan, Elixir security scan, Trivy skip-dirs exclusion (ci/broken-inputs, handoff), Startup provenance check step, Application (Elixir module outside this repository), ci/gates/provenance.py (build provenance gate), ci/provenance-check.py (startup provenance check), ci/stamp.py (provenance stamp generator) (+19 more)

### Community 9 - "Recorder Instrument"
Cohesion: 0.15
Nodes (17): NewOrdered(), Persist(), T, TestAllOctetsCarriesEveryValueAndALoneContinuationByte(), TestOrderedIsFaithful(), TestPersistWritesOneFilePerExchange(), crypto/sha256 (Go standard library package), encoding/base64 (Go standard library package) (+9 more)

### Community 10 - "Packaging and Terminator Edge"
Cohesion: 0.10
Nodes (23): Declared version ranges, Fixed build provenance, Generated configuration declaration, Negative gate demonstration, Packaging, Published artifact release gate, Stopped artifact declaration, Verifiable artifact content (+15 more)

### Community 11 - "Decision Register"
Cohesion: 0.16
Nodes (20): .claude/THIRD-PARTY-NOTICES.md (outside the graph corpus), D4 Elixir proxy and Go sidecar runtime, D8 Tenant scoping in keys and signatures, Custom-domain claim, proof, issuance sequence, D9 — Domain ownership before issuance, D19 — v1 tunnel transport, Transport-independent tunnel framing, WebSocket over TLS on port 443 (+12 more)

### Community 12 - "Request Body Framing"
Cohesion: 0.23
Nodes (15): Buffer, chunkSize(), copyOctets(), Reader, octetCount(), readBody(), readChunked(), readFramingLine() (+7 more)

### Community 13 - "Recording Origin Server"
Cohesion: 0.26
Nodes (16): Closer, closing(), Conn, Reader, isToken(), lingerClose(), main(), readFields() (+8 more)

### Community 14 - "Recording Origin Imports"
Cohesion: 0.20
Nodes (14): Conn, T, serveOnTCP(), TestARefusalOverTCPEndsInACloseRatherThanAReset(), TestARefusedPeerStillSendingIsCutOffAtTheCap(), T, TestAnEmptyRequestIsStillAQuietEndRatherThanAFinding(), TestATruncatedBodyIsReportedRatherThanReadAsACleanClose() (+6 more)

### Community 15 - "Sidecar and Tunnel Roles"
Cohesion: 0.13
Nodes (17): Installation trust boundary, Backend hop ownership, Sidecar configuration lifecycle, Sidecar lifecycle, Sidecar program, Tenant-side diagnosis, Credential, Credential presentation (+9 more)

### Community 16 - "Unattended Merge Refusal"
Cohesion: 0.18
Nodes (15): .github/CODEOWNERS, Dependabot update configuration, GitHub Actions ecosystem updates, Go modules ecosystem updates (sidecar, terminator, conformance), Mix ecosystem updates (/proxy), Weekly dependency update schedule, Refusal of unattended advance over reviewed paths, Dependabot auto-merge workflow (+7 more)

### Community 17 - "Vault Checks and Security CI"
Cohesion: 0.20
Nodes (15): No path filter, branch filter or continue-on-error, Vault check workflow, Obligation parity check, Scheduled gates and parity checks, Security scan workflow, ci/gates/runner.py (runner declaration check), ci/proxy-tooling-check.py (planted proxy lint violations), ci/vault.json (gate declaration) (+7 more)

### Community 18 - "Custom Domain Claims"
Cohesion: 0.17
Nodes (15): Claim-bound challenge, Connection-time certificate selection, Custom-domain traffic parity, Custom domains, Hostname ownership claim, Ownership verification gate, Verification lapse and recheck, Wildcard delegation and exact precedence (+7 more)

### Community 19 - "Python Tool Configuration"
Cohesion: 0.19
Nodes (15): All violations in one run, Common --root and --report-only gate flags, Passing-run gate coverage, Python gate conventions, Python quality toolchain, Standard library only CI gate modules, basedpyright CI tooling configuration, Black Python 3.12 configuration (+7 more)

### Community 20 - "Operator View"
Cohesion: 0.22
Nodes (15): Audit retention conflict, Pre-service configuration validation, Deferred human-facing control plane, Self-contained deployable artifacts, End-to-end sidecar liveness, Installation-wide observability, Migration action surface gap, Multi-instance installation (+7 more)

### Community 21 - "Certificate Key Custody"
Cohesion: 0.15
Nodes (14): Certificate lifecycle, Allowed key parameters, Closed custody inventory, Key custody, Key replacement and destruction, Protection at rest, Subject-scoped distribution, Connection phase (+6 more)

### Community 22 - "Primitives and Frame Tunnel"
Cohesion: 0.16
Nodes (14): Frame with stream identifier, Bidirectional frame stream, D1 — Three transport primitives, QUIC streams with datagrams, Request/response byte stream, Capsule framing alternative (HTTP/2 WebTransport draft), Dual credit windows with liveness and datagram exemption, D2 Frame-shaped tunnel exchange (+6 more)

### Community 23 - "Credential Scan and Follow-Ups"
Cohesion: 0.17
Nodes (13): Full-history checkout (fetch-depth 0), Files-endpoint truncation refusal, ci/gates/secret_scan.py (credential scan gate), Binary asset provenance, A credential is absent from the tree, and absent from the range under review, Merge commits scanned through their combined diff, not-a-live-credential: marker (dated suppression), Placeholder-token escape (+5 more)

### Community 24 - "Tunnel Frame Vocabulary"
Cohesion: 0.15
Nodes (13): Bidirectional stream, Cause, Close vocabulary, Commit point, Correlation identifier, Datagram, Exchange, Frame (+5 more)

### Community 25 - "Out-of-Scope Containment"
Cohesion: 0.26
Nodes (12): ci/gates/out_of_scope.py (outside the graph corpus), ci/gen/indexes.py (outside the graph corpus), D31 — A declared out-of-scope set may not name its own declarant's tree, Containment: who may not declare, instead of who may not edit, declared_by read for a message, not for a decision, Emptied out-of-scope declaration recorded as a declared vacuity, Refused specification revisions (standing obligation), auth/sidecar-credentials names no key-custody cross-reference (+4 more)

### Community 26 - "Chunked Framing Tests"
Cohesion: 0.36
Nodes (11): assertRefused(), chunk(), firstLine(), T, TestAChunkedBodyIsRecordedDeframed(), TestAFieldLineWithoutATokenForItsNameIsRefused(), TestAFramingFieldWhoseNameIsNotATokenIsRefused(), TestMalformedChunkingIsRefused() (+3 more)

### Community 27 - "Reference Provenance and Sign-Off"
Cohesion: 0.24
Nodes (11): DCO sign-off workflow, ci/gates/citations.py (outside the graph corpus), Developer Certificate of Origin sign-off, History notes index, Reference citation verification, A cited artifact is obtainable, Obtaining the reference, Pinned Plugboard revision 6756a07 (+3 more)

### Community 28 - "Prior Art and Rebuild"
Cohesion: 0.18
Nodes (11): Unwired hooks body enrichment (prior attempt), Administrative middleware pipeline, D5 — Dedicated proxied traffic path, Proxy path before application middleware, D21 Rebuild from scratch, Explicit configuration policy, Both reference containers fail to boot, Buffered body disguised as streaming (+3 more)

### Community 29 - "Test Workflow Jobs"
Cohesion: 0.20
Nodes (10): Component test workflow, Conformance build job, Fast test job, Expected-outcome gating tests, Integration test job, ci/expected-outcomes.py (gating baseline check), ci/fast-tier.py (fast tier latency budget runner), Adversarial conformance corpus (+2 more)

### Community 30 - "Mount Point Routing"
Cohesion: 0.22
Nodes (10): Locally configured backend origin, Longest-prefix match, Mount-boundary rewriting, Mount point, Node, Remainder, Reserved path, Role (+2 more)

### Community 31 - "One Repository"
Cohesion: 0.22
Nodes (9): Pinned OpenSpec 1.13.0 install, Patch-only unattended merge, ci/gates/authoring_channels.py (authoring channels gate), D22 — One repository, No-submodules CI guard, Single repository tree, Unreviewed dependency update chain, Conventions reach both authoring channels (+1 more)

### Community 32 - "Make Check Budget"
Cohesion: 0.25
Nodes (9): ci/gates/_common.py (outside the graph corpus), ci/gates/meta.py (outside the graph corpus), ci/run-gates.py (outside the graph corpus), D32 — make check holds every tree property on change, inside a declared budget, Meta-gate isolation cross-product, make check wall-clock budget (gate_policy.budget_seconds), docs/decisions generated index, ci/gates/_common.py has no gate of its own (+1 more)

### Community 33 - "Reply Mode Tests"
Cohesion: 0.31
Nodes (8): newReply(), T, TestAContradictoryReplyIsRefusedAtStartup(), TestEachFlagCombinationSelectsTheReplyItNames(), TestEachReplyModeWritesWhatItStates(), bytes (Go standard library package), slices (Go standard library package), testing (Go standard library package)

### Community 34 - "Generated Frame Codecs"
Cohesion: 0.25
Nodes (9): Contradictory-framing refusal, D6 — Per-hop framing authority, Per-hop framing declarations, Binary interface definition, D18 — Generated binary frame codecs, Generated frame codecs, Raw body octets, Binary payload corruption in JSON (+1 more)

### Community 35 - "Observability Before Hot Path"
Cohesion: 0.28
Nodes (9): Attached metric sink and structured logger, D27 — Observability before hot path, Telemetry consumer attachment test, Real-server WebSocket wire tests, Contract tests against two fictions, Slow feedback incentivizes weak tests, Unconsumed telemetry events, Completeness critic (+1 more)

### Community 36 - "Contract and Conformance"
Cohesion: 0.25
Nodes (9): Conformance run, Conformance suite, Contract version, Implementation under test, Contract-first implementation, Permanent asymmetric version skew, Suite latency as correctness control, Three protocol primitives (+1 more)

### Community 37 - "Python Tooling in Lint"
Cohesion: 0.32
Nodes (8): pip ecosystem updates (requirements-dev.txt), Component lint job, Python tooling lint steps (in required lint job), ci/gates/linter_config.py (single linter config gate), ci/go-tooling-check.py (planted Go tooling violations), Single Go linter configuration, make lint-python, Python quality tooling

### Community 38 - "Obsidian Settings"
Cohesion: 0.25
Nodes (7): alwaysUpdateLinks, attachmentFolderPath, newLinkFormat, showUnsupportedFiles, strictLineBreaks, useMarkdownLinks, userIgnoreFilters

### Community 39 - "Coverage Is an Assertion"
Cohesion: 0.33
Nodes (7): Go vulnerability scan, ci/gates/build_prerequisites.py (build prerequisite gate), ci/gates/coverage.py (outside the graph corpus), Coverage gate rerunning every gate (removed double run), Coverage count and covered list can disagree, Gate coverage is an assertion, Violating inputs declare their failures

### Community 40 - "Origin Reply Heads"
Cohesion: 0.67
Nodes (5): writeHead(), writeReply(), writeStatus(), reply, Writer

### Community 41 - "Capability Declaration"
Cohesion: 0.33
Nodes (6): gRPC-Web translation, Baseline, Capability declaration, Capability term collision, Declaration-based skip, Refusal

### Community 42 - "Explicit Carry-Forward"
Cohesion: 0.40
Nodes (6): Cited prior-art inventory, D10 — Explicit cited carry-forward, D10 number collision with the superseded register, Strip-one-segment mount lookup, Terminal-mount invariant, Prior art is not behavioural authority

### Community 43 - "Timeout Taxonomy"
Cohesion: 0.40
Nodes (5): D7 — Timeout taxonomy, Six independently configured timeout bounds, Route class without a total time bound, Per-request Task.async isolation, Single global request timeout

### Community 44 - "Gate Documentation Rules"
Cohesion: 0.50
Nodes (4): Failure messages name the consequence, Gate docstring names requirement and defect, Gate states what it does not decide, Preference rules index

### Community 45 - "Affinity Registry"
Cohesion: 0.50
Nodes (4): Affinity binding, Affinity key, Eligibility, Registry entry

### Community 46 - "Resource Bound Definitions"
Cohesion: 0.50
Nodes (4): Bound, Bound definition gap, Occupancy dimension, Standing-resource dimension

### Community 47 - "Adversarial Research Review"
Cohesion: 0.50
Nodes (4): Adversarial review of load-bearing conclusions, Fabricated or misattributed runtime claims, Overturned Rust proxy recommendation, Reviewed WebTransport verdict

### Community 49 - "Go Lint Configuration"
Cohesion: 0.67
Nodes (3): Narrow test lint exclusions, Shared Go lint configuration, Strict Go lint settings

### Community 50 - "Note Classification Rules"
Cohesion: 0.67
Nodes (3): Every capability has a concept note, Every note carries a classification, Every tracked note lives under a declared root

## Knowledge Gaps
- **91 isolated node(s):** `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks`, `attachmentFolderPath`, `showUnsupportedFiles` (+86 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `make stamp (regenerate build-provenance source)` connect `Build Provenance and Stamps` to `Coverage Is an Assertion`?**
  _High betweenness centrality (0.260) - this node is a cross-community bridge._
- **Why does `Single source build provenance` connect `Build Provenance and Stamps` to `Routers, Review and Testing`, `Packaging and Terminator Edge`, `Procedures and Code Rules`?**
  _High betweenness centrality (0.210) - this node is a cross-community bridge._
- **Why does `ci/stamp.py (provenance stamp generator)` connect `Build Provenance and Stamps` to `Python Tooling in Lint`?**
  _High betweenness centrality (0.178) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Scope refusals` (e.g. with `Edge hygiene` and `HTTP fidelity`) actually correct?**
  _`Scope refusals` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Claude router (CLAUDE.md)` (e.g. with `Agent router (AGENTS.md)` and `Ordered header-field pairs`) actually correct?**
  _`Claude router (CLAUDE.md)` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Agent router (AGENTS.md)` (e.g. with `Claude router (CLAUDE.md)` and `Ordered header-field pairs`) actually correct?**
  _`Agent router (AGENTS.md)` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks` to the rest of the system?**
  _202 weakly-connected nodes found - possible documentation gaps or missing edges._