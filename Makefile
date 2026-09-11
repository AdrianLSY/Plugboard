# Vault gates. The aggregating target tasks.md 1.11 requires.
#
# `make check` is the one command CI and a contributor both run. It enumerates
# every gate it ran, so the gate inventory is a build output rather than a prose
# count -- the change's own risk register having carried "seven new gates"
# against a task list introducing roughly thirty.

.PHONY: check check-report check-links check-gates

check:                ## run every vault gate; non-zero if a blocking gate fails
	@python3 ci/run-gates.py

check-report:         ## run every vault gate, report-only; always exits zero
	@python3 ci/run-gates.py --report-only

check-links:          ## the link resolution gate alone
	@python3 ci/gates/links.py

check-gates:          ## the meta-check: every gate proven to fail on its own input
	@python3 ci/gates/meta.py
