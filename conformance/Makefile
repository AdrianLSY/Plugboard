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
build:
	@rm -rf $(DIST) && mkdir -p $(DIST)
	@for p in $(PLATFORMS); do \
	  os=$${p%%/*}; arch=$${p##*/}; \
	  ext=""; [ "$$os" = "windows" ] && ext=".exe"; \
	  out="$(DIST)/$(BINARY)-$$os-$$arch$$ext"; \
	  echo "==> $$p -> $$out"; \
	  CGO_ENABLED=0 GOOS=$$os GOARCH=$$arch $(GO) build -trimpath -o "$$out" ./cmd/$(CMD) || exit $$?; \
	done
	@echo "built $$(ls -1 $(DIST) | wc -l | tr -d ' ') binary(ies) for $$(echo $(PLATFORMS) | wc -w | tr -d ' ') declared platform(s)"
