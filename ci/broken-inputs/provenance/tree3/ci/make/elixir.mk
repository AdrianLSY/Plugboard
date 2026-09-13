# The shared Elixir fragment, with the second copy of the discovery that the
# rule exists to prevent. It has no stamp target either -- what it has is its own
# idea of a version, which is how the two fragments come to disagree about what
# a build is without either side being able to see the other.
#
# The copy below is a VERBATIM PASTE of ci/make/go.mk's discovery: the same three
# reads, the same `-C '$(STAMP_SRC)'`, the same `--no-optional-locks`. That is
# how this defect actually arrives -- a second language needs a stamp, delegating
# looks like a detour, and the recipe that already works gets copied. A check
# testing for the substring `git rev-parse` would find nothing in any of these
# three lines, so the likeliest real copy would have been the one copy invisible
# to the rule forbidding it. The gate matches git's option syntax instead, and
# this tree is what proves it on the hard case rather than the easy one.

MIX ?= mix

.PHONY: test release

test:
	$(MIX) test

release:
	@set -e; \
	commit=$$(git -C '$(STAMP_SRC)' rev-parse HEAD 2>/dev/null || echo unknown); \
	version=$$(git -C '$(STAMP_SRC)' describe --tags 2>/dev/null || echo untagged); \
	if [ -n "$$(git --no-optional-locks -C '$(STAMP_SRC)' status --porcelain 2>/dev/null)" ]; \
	  then tree=dirty; else tree=clean; fi; \
	echo "releasing $$version $$commit $$tree"
