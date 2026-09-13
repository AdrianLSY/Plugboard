# The shared Go fragment with no stamp target at all: every component it serves
# is built with no provenance, and each of them looks exactly as it did before.

GO ?= go

.PHONY: fmt test

fmt:
	$(GO) fmt ./...

test:
	$(GO) test -race ./...
