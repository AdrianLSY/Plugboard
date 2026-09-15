# The Elixir half of the same lost edge. `lint` and `test-fast` declare `stamp`;
# `test-integration` does not, and `mix compile --warnings-as-errors` over a
# missing Plugboard.BuildStamp is a failed build, not a warning.
#
# This tree exists because the first version of ci/gates/build_prerequisites.py
# named only the Go make files, so this exact defect reached CI while the gate
# reported green.
MIX ?= mix
STAMP := lib/plugboard/build_stamp.ex

stamp:
	@python3 $(REPO_ROOT)/ci/stamp.py --component proxy --language elixir > $(STAMP)

lint: stamp
	$(MIX) compile --warnings-as-errors

test-integration:
	$(MIX) test --exclude test --include integration
