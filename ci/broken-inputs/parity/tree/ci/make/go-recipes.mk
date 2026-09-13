GOLANGCI ?= golangci-lint
LINT_CFG := $(REPO_ROOT)/.golangci.yml

# No --config. The workflow's action step passes one, so the two invocations of
# one obligation are two different invocations.
lint:
	$(GOLANGCI) run ./...
