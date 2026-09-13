# The Elixir component targets, in one copy. Same reason as ci/make/go.mk: the
# duplication threshold is a rule here, and a build file is not exempt from it.
#
# Every target refuses when `mix` is absent rather than skipping. A lint target
# that succeeds because its tool is missing is the prior art's exact shape --
# `credo` declared as a dependency and never invoked, which reads in review as
# instrumentation and is none.

MIX       ?= mix
REPO_ROOT ?= ..

.PHONY: fmt lint test test-fast test-integration test-conformance gen dev deps require-mix stamp

require-mix:
	@command -v $(MIX) >/dev/null 2>&1 || { \
	  echo "make: mix is not on PATH, so nothing ran for this component." >&2; \
	  echo "      Install Elixir and re-run -- a target that skips when its" >&2; \
	  echo "      toolchain is absent reports green over an unchecked module." >&2; \
	  exit 1; }

deps: require-mix
	$(MIX) deps.get

fmt: require-mix
	$(MIX) format

# Five tools, and the reference invoked none of them on this component. Each is
# named separately so a failure says which one refused. `compile` is here with
# the PLURAL flag: rebuild-plugboard task 2.1, and the singular spelling is the
# defect it is named after.
lint: require-mix stamp
	$(MIX) compile --warnings-as-errors
	$(MIX) format --check-formatted
	$(MIX) credo --strict
	$(MIX) dialyzer
	$(MIX) sobelow --exit
	$(MIX) deps.audit

test: test-fast test-integration test-conformance

# The three tiers, separately invocable (rebuild-plugboard task 2.7). ExUnit tags
# rather than directories, for the same reason as the Go side: a test declares
# its tier beside its subject. Untagged is FAST, so a test needing Postgres has
# to say so -- the prior attempt split by whether the subject was synchronous,
# and pure-function tests required a database.
#
# NOT `--only <tag>`. A tier with no tests in this component is a no-op here,
# never a missing target and never a failure -- the same promise ci/make/go.mk
# makes, where `go test -tags=integration ./...` over no tagged file is simply
# zero tests. `mix test --only integration` breaks that promise: when the tag
# selects nothing it prints "The --only option was given to mix test but no test
# was executed" and exits 1, so a component that has not written an integration
# test yet fails its integration tier. Observed in CI, on this component.
#
# `--exclude test --include <tag>` is what `--only <tag>` expands to internally
# and selects exactly the same tests -- measured: both report
# "Result: 1 passed, 3 excluded" against one tagged test -- without the empty-set
# exit. What it does NOT do is swallow a failure: a tagged test that fails still
# exits non-zero (measured: 2). That distinction is the whole point, and a
# `|| true` here would have bought the same green by giving up the tier.
test-fast: require-mix stamp
	$(MIX) test --exclude integration --exclude conformance

test-integration: require-mix stamp
	$(MIX) test --exclude test --include integration

test-conformance: require-mix stamp
	$(MIX) test --exclude test --include conformance

gen: require-mix stamp

dev: require-mix stamp
	$(MIX) run --no-halt

## -- the build stamp --------------------------------------------------------

# The stamp is NOT reimplemented here. ci/make/go.mk holds the one copy of the
# discovery -- version, commit, dirty-tree marker, build time -- and emits
# either language from it (rebuild-plugboard task 3.13); this target hands it
# the three things that are per-component and nothing else.
#
# A second copy is the failure this arrangement exists to prevent: the prior art
# reached exactly that state with its linters, where each side drifted toward
# whatever it found inconvenient and neither drift was visible from the other.
# Delegating rather than copying costs one recursive make invocation.
#
# STAMP_COMPONENT is DERIVED, not written. It used to read `STAMP_COMPONENT=proxy`
# -- a per-component value inside the fragment shared by every Elixir component,
# which is the one place this rule says a per-component value must not live. A
# second Elixir component would have shipped stamped `component=proxy` and
# nothing here would have noticed: the gate decides where values come from and
# not what they are, and the proxy's own test asserting `{"component", "proxy"}`
# goes on passing in the proxy no matter what the fragment does to anyone else.
# `$(notdir $(CURDIR))` is the spelling ci/make/go.mk:95 already uses for the
# same field, so the two languages now derive it the same way and the proxy
# keeps the value it had.
STAMP_COMPONENT ?= $(notdir $(CURDIR))

stamp:
	@$(MAKE) --no-print-directory -f $(REPO_ROOT)/ci/make/go.mk stamp \
	  REPO_ROOT='$(REPO_ROOT)' \
	  STAMP_COMPONENT='$(STAMP_COMPONENT)' \
	  STAMP_LANGUAGE=elixir \
	  STAMP_OUT=lib/plugboard/build_stamp.ex
