# Minimal, and only the two targets the declared obligations name.
BUDGET_TOOL := ci/fast-tier.py

check:
	@python3 ci/run-gates.py

test-fast:
	@python3 $(BUDGET_TOOL) -- $(MAKE) --no-print-directory test-fast-unbudgeted
