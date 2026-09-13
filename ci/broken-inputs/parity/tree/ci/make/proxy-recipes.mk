MIX ?= mix

# `mix format --check-formatted` has been dropped from this target, so the
# elixir-format obligation is declared enforced locally and is not.
lint:
	$(MIX) compile --warnings-as-errors
	$(MIX) credo --strict
