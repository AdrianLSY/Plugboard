# Declares only the fast tier.
GO ?= go

test-fast:
	$(GO) test -race ./...
