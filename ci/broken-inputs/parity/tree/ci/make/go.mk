# The local invocation, with a flag the CI side does not pass.
GOLANGCI  ?= golangci-lint
LINT_CFG  := $(REPO_ROOT)/.golangci.yml
LINT_TAGS := gating,integration

lint:
	$(GOLANGCI) run --config $(LINT_CFG) --build-tags $(LINT_TAGS) --timeout 5m ./...
