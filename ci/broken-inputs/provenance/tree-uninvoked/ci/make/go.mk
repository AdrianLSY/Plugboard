# The Go component rules, with no stamp target.
#
# Nothing here generates a stamp, so the buildstamp package keeps whatever it
# last held -- or, on a clean checkout, nothing at all. The binary starts,
# prints an empty provenance line, and looks exactly like a binary built before
# stamping existed.
GO ?= go

lint:
	$(GO) vet ./...

test-fast:
	$(GO) test -race ./...
