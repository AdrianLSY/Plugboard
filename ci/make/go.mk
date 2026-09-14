# The Go component targets, in one copy. Each Go module's Makefile includes this
# and sets CMD; nothing else is per-module.
#
# Three copies of these recipes is how the prior art ended up with thirty
# linters on one side and no format check at all on the other. The duplication
# threshold is a rule here (docs/code/rules/duplication-threshold.md) and a build
# file is not exempt from it.
#
# REPO_ROOT is set by the including Makefile, because a component is built from
# its own directory and the one linter configuration lives at the root.

GO        ?= go
GOLANGCI  ?= golangci-lint
VAULT     := $(REPO_ROOT)/ci/vault.json
LINT_CFG  := $(REPO_ROOT)/.golangci.yml
# The tiers behind build tags are linted too. Without these, code compiled only
# under `gating` or `integration` is invisible to the linter: its helpers read as
# unused, and -- the half that matters -- the tiers go UNLINTED while the target
# reports green. CI hit the first symptom; this target had the same blind spot and
# had apparently never been run. The same list belongs in the workflow's action
# args, and does.
LINT_TAGS := gating,integration

.PHONY: fmt lint test test-fast test-integration test-conformance gen dev

fmt:
	$(GO) fmt ./...

lint:
	@command -v $(GOLANGCI) >/dev/null 2>&1 || { \
	  echo "make lint: golangci-lint is not on PATH, so nothing was linted." >&2; \
	  echo "           Install it, then re-run -- a lint target that skips when its" >&2; \
	  echo "           tool is absent reports green over an unlinted module:" >&2; \
	  echo "           go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest" >&2; \
	  exit 1; }
	$(GOLANGCI) run --config $(LINT_CFG) --build-tags $(LINT_TAGS) ./...

# -race is not a flag a contributor is asked to remember. It IS the invocation:
# rebuild-plugboard task 2.5, and there is no target here that runs `go test`
# without it. A data race in a proxy is a corrupted response body, and it is the
# defect class least likely to reproduce under a rerun.
test: test-fast test-integration test-conformance

# The three tiers, separately invocable (rebuild-plugboard task 2.7). A tier with
# no tests in this module is a no-op here, never a missing target: a dispatch
# that silently skips a component is the shape this repository keeps refusing.
#
# Tiers are build tags rather than directories, so a test declares its own tier
# beside its subject and moving one is a one-line edit rather than a file move.
# The fast tier is what compiles with no tag at all, which makes the DEFAULT the
# strict tier -- a test that needs Postgres has to say so.
test-fast:
	$(GO) test -race ./...

test-integration:
	$(GO) test -race -tags=integration ./...

test-conformance:
	$(GO) test -race -tags=conformance ./...

gen:
	$(GO) generate ./...

dev:
	$(GO) run ./cmd/$(CMD)
