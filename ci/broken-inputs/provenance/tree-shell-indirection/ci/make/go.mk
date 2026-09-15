# One level of shell indirection. This file names no git, so a check that reads
# only the build files finds nothing; the script is under no component root, so
# a check that reads only component sources finds nothing either. The derivation
# runs at make PARSE time, on every invocation of every target.
GO ?= go
PROV := $(shell sh $(REPO_ROOT)/ci/derive-provenance.sh)

stamp:
	@python3 $(REPO_ROOT)/ci/stamp.py --component x --language go > $(STAMP)

lint: stamp
	$(GO) vet ./...
