# The Elixir component targets, in one copy. Same reason as ci/make/go.mk: the
# duplication threshold is a rule here, and a build file is not exempt from it.
#
# Every target refuses when `mix` is absent rather than skipping. A lint target
# that succeeds because its tool is missing is the prior art's exact shape --
# `credo` declared as a dependency and never invoked, which reads in review as
# instrumentation and is none.

MIX       ?= mix
REPO_ROOT ?= ..

.PHONY: fmt stamp warm lint test test-fast test-integration test-conformance gen dev deps require-mix

require-mix:
	@command -v $(MIX) >/dev/null 2>&1 || { \
	  echo "make: mix is not on PATH, so nothing ran for this component." >&2; \
	  echo "      Install Elixir and re-run -- a target that skips when its" >&2; \
	  echo "      toolchain is absent reports green over an unchecked module." >&2; \
	  exit 1; }

deps: require-mix
	$(MIX) deps.get

# BOTH environments. `mix compile` warms dev; `mix test` then compiles
# MIX_ENV=test from nothing, which is what the fast tier's budget was measuring.
# Build provenance, from the same one place the Go side uses.
STAMP := lib/plugboard/build_stamp.ex

stamp:
	@mkdir -p $(dir $(STAMP))
	@python3 $(REPO_ROOT)/ci/stamp.py --component $(notdir $(CURDIR)) --language elixir > $(STAMP)

warm: require-mix stamp
	$(MIX) compile
	MIX_ENV=test $(MIX) compile

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
test-fast: require-mix stamp
	$(MIX) test --exclude integration --exclude conformance

# `mix test --only <tag>` exits 2 when NO test carries the tag, so an empty tier
# FAILED instead of being a no-op -- observed in the first CI run this repository
# ever had. The stated design is the opposite: a tier with no tests in a given
# component is a no-op there, never a missing target. `--exclude test` with the
# tag re-included is ExUnit's own idiom for it, and it still runs every tagged
# test where one exists.
test-integration: require-mix
	$(MIX) test --exclude test --include integration

test-conformance: require-mix
	$(MIX) test --exclude test --include conformance

gen: require-mix
	@echo "proxy: nothing is generated yet"

dev: require-mix
	$(MIX) run --no-halt
