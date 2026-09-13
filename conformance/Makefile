# conformance. The shared recipes, plus the cross-compiled release build the
# suite needs in order to be runnable by someone who is not building it.
REPO_ROOT := ..
CMD       := conformance
include $(REPO_ROOT)/ci/make/go.mk

BINARY    := $(shell python3 -c "import json;print(json.load(open('$(VAULT)'))['code_standards']['conformance']['binary'])")
PLATFORMS := $(shell python3 -c "import json;print(' '.join(json.load(open('$(VAULT)'))['code_standards']['conformance']['platforms']))")
DIST      := dist

.PHONY: build

# One statically linked binary per DECLARED platform. CGO off, so the artifact
# runs on a machine with no matching libc -- the suite is handed to a contributor
# writing a sidecar in a language this repository has never seen, and "it does
# not start on my distribution" is the first way that offer fails.
#
# The platform set is read from ci/vault.json rather than listed here, so the
# declaration and the build cannot disagree.
#
# `stamp` first, and not as a convenience: these five artifacts are the ones
# handed to someone who did not build them, so the account each gives of its own
# build is the only account its recipient has. The stamp comes from the one place
# (ci/make/go.mk) like every other component's.
build: stamp
	@rm -rf $(DIST) && mkdir -p $(DIST)
	@for p in $(PLATFORMS); do \
	  os=$${p%%/*}; arch=$${p##*/}; \
	  ext=""; [ "$$os" = "windows" ] && ext=".exe"; \
	  out="$(DIST)/$(BINARY)-$$os-$$arch$$ext"; \
	  echo "==> $$p -> $$out"; \
	  CGO_ENABLED=0 GOOS=$$os GOARCH=$$arch $(GO) build -trimpath -o "$$out" ./cmd/$(CMD) || exit $$?; \
	done
	@echo "built $$(ls -1 $(DIST) | wc -l | tr -d ' ') binary(ies) for $$(echo $(PLATFORMS) | wc -w | tr -d ' ') declared platform(s)"

## -- the second entry point ---------------------------------------------------

# This component ships TWO `package main` binaries, and both are spawned in a
# run: the suite itself, and the recording origin the harness puts at the far end
# of the chain. A recorded exchange is evidence, and evidence carrying no account
# of the instrument that took it is an anecdote -- so the instrument is stamped
# and reports itself exactly as the suite does.
#
# The stamp still comes from the one place (ci/make/go.mk). What is handed over
# here is the second output path and nothing else: STAMP_COMPONENT is left at its
# default, which is this directory's name, because the field names the COMPONENT
# and both binaries are this one.
stamp: stamp-recording-origin

.PHONY: stamp-recording-origin

stamp-recording-origin:
	@$(MAKE) --no-print-directory -f $(REPO_ROOT)/ci/make/go.mk stamp \
	  REPO_ROOT='$(REPO_ROOT)' \
	  STAMP_OUT=cmd/recording-origin/build_stamp.go
