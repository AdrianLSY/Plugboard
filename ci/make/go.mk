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

.PHONY: fmt lint test test-fast test-integration test-conformance gen dev stamp

fmt:
	$(GO) fmt ./...

lint: stamp
	@command -v $(GOLANGCI) >/dev/null 2>&1 || { \
	  echo "make lint: golangci-lint is not on PATH, so nothing was linted." >&2; \
	  echo "           Install it, then re-run -- a lint target that skips when its" >&2; \
	  echo "           tool is absent reports green over an unlinted module:" >&2; \
	  echo "           go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest" >&2; \
	  exit 1; }
	$(GOLANGCI) run --config $(LINT_CFG) ./...

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
#
# Each tier depends on `stamp`, so the provenance a test asserts is the
# provenance of the tree the test is running against rather than whatever was
# left in the working directory by an earlier build.
test-fast: stamp
	$(GO) test -race ./...

test-integration: stamp
	$(GO) test -race -tags=integration ./...

test-conformance: stamp
	$(GO) test -race -tags=conformance ./...

gen: stamp
	$(GO) generate ./...

dev: stamp
	$(GO) run ./cmd/$(CMD)

## -- the build stamp --------------------------------------------------------

# ONE copy of the build-provenance stamp, and it serves BOTH languages
# (rebuild-plugboard task 3.13). ci/make/elixir.mk delegates to this target
# rather than carrying a second copy of the discovery: two copies is how one
# component comes to report a dirty tree while another reports nothing, and
# neither side can see the drift from where it stands.
#
# It lives in this fragment because ci/make holds exactly two of them and this
# is the one three of the four components already include. If a third fragment
# ever lands, move this block into it and leave both includes pointing there;
# what must not happen is a second copy.
#
# WHY BUILD-TIME STAMPING RATHER THAN A TOOL UNDER ci/gen/. A stamp carries a
# build time and a commit, so its output differs on every run -- and every tool
# under ci/gen/ is held against a PINNED expected output by
# ci/gates/generators.py, which such a tool can never satisfy. Nor is the stamp
# committed: a tracked generated stamp makes the tree dirty the moment it is
# regenerated, so the marker it carries would be a permanent lie. The generated
# source is therefore git-ignored beside its component, and a component that was
# never stamped does not compile -- a binary that cannot say what it was built
# from is not a binary this repository ships.
#
# Four facts about a build -- version, commit, dirty-tree marker, build time --
# and the component they belong to. They are reported under the five names
# ci/gates/provenance.py holds every component to, in this order.
#
# The dirty-tree read is `--no-optional-locks`, because this runs inside every
# build: a status that refreshes the index while a second build or an editor
# holds it is a lock contention nobody would trace back to a stamp.

STAMP_COMPONENT ?= $(notdir $(CURDIR))
STAMP_LANGUAGE  ?= go
STAMP_SRC       ?= $(REPO_ROOT)
STAMP_OUT       ?= cmd/$(CMD)/build_stamp.go

stamp:
	@set -e; \
	commit=$$(git -C '$(STAMP_SRC)' rev-parse HEAD 2>/dev/null || echo unknown); \
	if [ "$$commit" = unknown ]; then version=unknown; tree=unknown; else \
	  version=$$(git -C '$(STAMP_SRC)' describe --tags 2>/dev/null || echo untagged); \
	  if [ -n "$$(git --no-optional-locks -C '$(STAMP_SRC)' status --porcelain 2>/dev/null)" ]; \
	    then tree=dirty; else tree=clean; fi; \
	fi; \
	built_at=$$(python3 -c 'import os,time;print(time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(int(os.environ.get("SOURCE_DATE_EPOCH") or time.time()))))'); \
	mkdir -p "$$(dirname '$(STAMP_OUT)')"; \
	if [ '$(STAMP_LANGUAGE)' = elixir ]; then \
	  { printf '%s\n' \
	      '# Code generated by `make stamp` (ci/make/go.mk). DO NOT EDIT.' \
	      '' \
	      'defmodule Plugboard.BuildStamp do' \
	      '  @moduledoc false' \
	      '' \
	      '  @fields ['; \
	    printf '    {"%s", "%s"},\n' \
	      component "$(STAMP_COMPONENT)" version "$$version" commit "$$commit" tree "$$tree"; \
	    printf '    {"%s", "%s"}\n' built_at "$$built_at"; \
	    printf '%s\n' \
	      '  ]' \
	      '' \
	      '  @spec fields() :: [{String.t(), String.t()}]' \
	      '  def fields, do: @fields' \
	      '' \
	      '  @spec line() :: String.t()' \
	      '  def line do' \
	      '    pairs = Enum.map_join(@fields, " ", fn {name, value} -> name <> "=" <> value end)' \
	      '    "build-provenance " <> pairs' \
	      '  end' \
	      'end'; \
	  } > '$(STAMP_OUT)'; \
	else \
	  { printf '%s\n' \
	      '// Code generated by `make stamp` (ci/make/go.mk). DO NOT EDIT.' \
	      '' \
	      'package main' \
	      '' \
	      'import "strings"' \
	      '' \
	      '// buildStampOrder is the order the provenance fields are reported in.' \
	      'var buildStampOrder = []string{"component", "version", "commit", "tree", "built_at"}' \
	      '' \
	      '// buildStamp carries the provenance of this build, by field name.' \
	      'var buildStamp = map[string]string{'; \
	    printf '\t%-12s %s,\n' \
	      '"component":' '"$(STAMP_COMPONENT)"' '"version":' "\"$$version\"" \
	      '"commit":' "\"$$commit\"" '"tree":' "\"$$tree\"" '"built_at":' "\"$$built_at\""; \
	    printf '%s\n' \
	      '}' \
	      '' \
	      '// startupReport is what this component says about itself at startup: the' \
	      '// banner, then its build provenance. It is the seam the per-component test' \
	      '// asserts against, and the only renderer of the stamp.' \
	      'func startupReport(banner string) string {'; \
	    printf '\t%s\n' 'parts := make([]string, 0, len(buildStampOrder))' \
	      'for _, name := range buildStampOrder {'; \
	    printf '\t\t%s\n' 'parts = append(parts, name+"="+buildStamp[name])'; \
	    printf '\t%s\n' '}' 'return banner + "\nbuild-provenance " + strings.Join(parts, " ")'; \
	    printf '%s\n' '}'; \
	  } > '$(STAMP_OUT)'; \
	fi; \
	echo "stamp: component=$(STAMP_COMPONENT) version=$$version commit=$$commit tree=$$tree built_at=$$built_at -> $(STAMP_OUT)"
