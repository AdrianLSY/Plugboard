# sidecar, as this fixture has it.
REPO_ROOT := ..
CMD       := telephone
include $(REPO_ROOT)/ci/make/go.mk

# THE SECOND COPY, written out. This component asks version control what it is
# rather than taking the answer from the one place, so its idea of a dirty tree
# and the stamp's can differ with nothing able to see it.
#
# Written in the ONE PLACE'S OWN SPELLING -- `git -C '<path>' rev-parse` -- and
# not the bare `git rev-parse` a first draft reaches for. That is the whole
# demonstration. A copy of the discovery does not arrive here as something
# freshly invented; it arrives as a paste of ci/make/go.mk:102, because the
# person adding it wanted the behaviour that file already has. A check matching
# `git rev-parse` as a plain substring sees neither this line nor the line it was
# pasted from, so it would have caught only the copy nobody would write and
# passed over every copy of the real thing. The gate matches git's option syntax
# for that reason, and this fixture is what holds it to it.
version:
	@echo "telephone $$(git -C '$(REPO_ROOT)' rev-parse --short HEAD)"
