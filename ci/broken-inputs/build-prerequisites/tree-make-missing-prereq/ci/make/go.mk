# A make graph that lost the edge. `stamp` still exists and `lint` still
# declares it, so a reader comparing the two targets sees nothing odd -- but
# test-fast type-checks the generated package without generating it, and fails
# on any clean checkout.
GO ?= go
STAMP := internal/buildstamp/stamp.go

stamp:
	@python3 ../ci/stamp.py --component $(notdir $(CURDIR)) --language go > $(STAMP)

lint: stamp
	golangci-lint run

test-fast:
	$(GO) test -race ./...
