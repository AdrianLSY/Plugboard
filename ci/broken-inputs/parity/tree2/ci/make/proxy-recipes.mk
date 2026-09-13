MIX ?= mix

lint:
	$(MIX) compile --warnings-as-errors
	$(MIX) format --check-formatted
