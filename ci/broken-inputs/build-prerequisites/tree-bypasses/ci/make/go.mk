# Four bypasses of the first version of this gate, in one file. Each was found by
# a reviewer attacking it, and each passed before the fix.
GO ?= go

stamp:
	@python3 $(REPO_ROOT)/ci/stamp.py --component x --language go > $(STAMP)

# (1) An underscore in the target name. The rule regex demanded [a-z][a-z0-9-]*,
# so this target's recipe was never read at all -- silent non-coverage.
test_fast:
	$(GO) test -race ./...

# (2) A literal `go`, reached after `&&`, where the markers were `$(GO) <verb>`
# literal strings.
release:
	cd sidecar && go build ./...

# (3) A verb that was not on the list. `go install` type-checks; on a stampless
# tree it fails exactly as `go build` does.
install-all:
	$(GO) install ./...
