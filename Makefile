# The repository's targets. Two families, and the difference matters.
#
#   VAULT GATES -- `make check`, the one command CI runs. It enumerates every
#   gate it ran, so the gate inventory is a build output rather than a prose
#   count: the change's own risk register carried "seven new gates" against a
#   task list introducing roughly thirty.
#
#   PER-COMPONENT -- `fmt`, `lint`, `test`, `gen`, `dev`. Each dispatches to
#   every component that has a Makefile of its own, and FAILS BY NAME for a
#   declared component that has none. It does not skip it. A lint target that
#   succeeds over zero components reads exactly like one that succeeded over
#   five, which is the failure this repository exists to make unwritable.
#
# The component list is read from ci/vault.json, so it is not a second copy of
# the set ci/gates/component_boundaries.py keys on.

.PHONY: test-fast-unbudgeted
.PHONY: check check-report check-links check-gates \
        fmt lint test test-fast test-integration test-conformance \
        gen dev precommit hooks components help

# Named literally rather than read from ci/vault.json, so a reader of this file
# can see what wraps the fast tier. That makes it a second encoding of
# code_standards.test_tiers.budget_tool -- which is why ci/gates/test_tiers.py
# reconciles the two rather than trusting either.
BUDGET_TOOL := ci/fast-tier.py
COMPONENTS := $(shell python3 -c "import json;print(' '.join(c for c in json.load(open('ci/vault.json'))['code_standards']['components']['candidates'] if not c.startswith('_')))")
# Declared as having no toolchain to dispatch to, with a reason and an ending
# condition in ci/vault.json. Printed rather than refused -- and an entry whose
# component HAS grown a Makefile is a declaration that outlived its reason, so
# that fails.
NO_TOOLCHAIN := $(shell python3 -c "import json;print(' '.join(c for c in json.load(open('ci/vault.json'))['code_standards']['components'].get('no_toolchain',{}) if not c.startswith('_')))")
PRESENT    := $(strip $(foreach c,$(COMPONENTS),$(if $(wildcard $(c)/Makefile),$(c),)))
ABSENT     := $(filter-out $(PRESENT) $(NO_TOOLCHAIN),$(COMPONENTS))
STALE_DECL := $(strip $(foreach c,$(NO_TOOLCHAIN),$(if $(wildcard $(c)/Makefile),$(c),)))

help:                 ## list the targets
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | expand -t24

## -- vault gates ------------------------------------------------------------

check:                ## run every vault gate; non-zero if a blocking gate fails
	@python3 ci/run-gates.py

check-report:         ## run every vault gate, report-only; always exits zero
	@python3 ci/run-gates.py --report-only

check-links:          ## the link resolution gate alone
	@python3 ci/gates/links.py

check-gates:          ## the meta-check: every gate proven to fail on its own input
	@python3 ci/gates/meta.py

## -- per component ----------------------------------------------------------

components:           ## which components dispatch today, and which do not
	@echo "declared     : $(COMPONENTS)"
	@echo "present      : $(if $(PRESENT),$(PRESENT),none)"
	@echo "no toolchain : $(if $(NO_TOOLCHAIN),$(NO_TOOLCHAIN),none)  (declared in ci/vault.json, with the condition that ends it)"
	@echo "absent       : $(if $(ABSENT),$(ABSENT),none)"

# One recipe, six targets. `dispatch` runs the named target in every present
# component and then refuses if any declared component could not be reached --
# after the present ones have run, so a contributor sees real output as well as
# what is missing.
define dispatch
	@for c in $(PRESENT); do \
	  echo "==> $$c: $(1)"; \
	  $(MAKE) --no-print-directory -C $$c $(1) || exit $$?; \
	done
	@for c in $(NO_TOOLCHAIN); do \
	  echo "make $(1): $$c/ is declared as having no toolchain, so nothing ran for it. ci/vault.json code_standards.components.no_toolchain says why, and what ends the declaration."; \
	done
	@if [ -n "$(STALE_DECL)" ]; then \
	  for c in $(STALE_DECL); do \
	    echo "make $(1): $$c/ is declared as having no toolchain in ci/vault.json AND has a Makefile -- the declaration has outlived its reason; remove it" >&2; \
	  done; \
	  exit 1; \
	fi
	@if [ -n "$(ABSENT)" ]; then \
	  for c in $(ABSENT); do \
	    echo "make $(1): $$c/ has no Makefile, so nothing ran for it -- it is a declared component whose toolchain has not landed (see openspec/changes/rebuild-plugboard/tasks.md section 2)" >&2; \
	  done; \
	  exit 1; \
	fi
endef

stamp:                ## regenerate every component's build-provenance source
	$(call dispatch,stamp)

warm:                 ## populate every build cache the tiers use, running no test
	$(call dispatch,warm)

fmt:                  ## format every present component; fail naming any absent one
	$(call dispatch,fmt)

lint:                 ## lint every present component; fail naming any absent one
	$(call dispatch,lint)

test:                 ## every tier, every present component
	$(call dispatch,test)

# The fast tier is wrapped by its budget. The ceiling and the tool are declared
# in ci/vault.json, so the number the rule states and the number enforced are one
# number. Suite latency is treated as a defect class, not a target:
# docs/code/rules/fast-tier-latency-budget.md.
test-fast:            ## the fast tier, under its declared wall-clock budget
	@python3 $(BUDGET_TOOL) -- $(MAKE) --no-print-directory test-fast-unbudgeted

test-fast-unbudgeted:
	$(call dispatch,test-fast)

test-integration:     ## the integration tier: real Postgres, real sockets
	$(call dispatch,test-integration)

test-conformance:     ## the conformance tier: the wire contract, adversarially
	$(call dispatch,test-conformance)

gen:                  ## regenerate generated sources per component
	$(call dispatch,gen)

dev:                  ## bring up the development environment
	$(call dispatch,dev)

precommit:            ## what a pre-commit hook runs: the gates, then lint and test
	@$(MAKE) --no-print-directory check
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory test

## -- hooks ------------------------------------------------------------------

# Installed on request, never automatically. A hook a contributor did not ask
# for is a hook they disable at the first inconvenience, and a disabled hook is
# indistinguishable from no hook while still looking like protection.
hooks:                ## install the pre-commit and pre-push hooks
	@d=$$(git rev-parse --git-path hooks) && mkdir -p "$$d" && \
	printf '#!/bin/sh\nexec make precommit\n' > "$$d/pre-commit" && \
	cp ci/hooks/pre-push "$$d/pre-push" && \
	chmod +x "$$d/pre-commit" "$$d/pre-push" && \
	echo "installed pre-commit and pre-push in $$d"
