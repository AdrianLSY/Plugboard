GOLANGCI ?= golangci-lint
LINT_CFG := $(REPO_ROOT)/.golangci.yml

lint:
	$(GOLANGCI) run --config $(LINT_CFG) ./...
