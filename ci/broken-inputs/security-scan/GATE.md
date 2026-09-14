# Violating input: security-scan

- **Gate:** `ci/gates/security_scan.py` (`security_scan`)
- **Rule note:** `docs/method/rules/declared-scanners-are-invoked.md`
- **Task:** `rebuild-plugboard` task 3.4.

## Violations, one per case

1. **`govulncheck` is named and never executed.** The step's `name:` carries
   `govulncheck ./...` and its `run:` is `echo skipping`. This is not a hypothetical:
   an earlier version of this gate matched the whole step block, `name:` included, and reported
   `scanners invoked: 4 of 4` against exactly this shape. That version was reverted, and this case
   exists so it cannot come back.
2. **`trivy` is invoked without `severity: HIGH,CRITICAL`.**
3. **…without `exit-code: '1'`.** A scan that reports and exits zero is a report, not a refusal.
4. **…without `skip-dirs: ci/broken-inputs`.** The violating input for `mix deps.audit` pins
   plug 1.3.0 with two HIGH advisories deliberately; a scan that reads it fails every push over the
   defect the fixture exists to be.
5. **No `schedule` trigger.** The weekly run is the half that matters — a vulnerability is published
   against code that has not changed, so a scan bound only to change finds it only when somebody
   happens to edit a file.

## The controls, in the same tree

`sobelow` and `deps.audit` are both genuinely executed in a `run:` body, and neither is reported. A
gate that failed every scanner would emit seven violations here; `expect.json` says five.

## What this tree does NOT demonstrate

Path filters, branch filters and `continue-on-error`. Those are `ci/gates/runner.py`'s, against
`ci/vault.json`'s `runner.forbidden_clauses`, and `.github/workflows/security.yml` is declared in
`runner.workflows` so it is covered there. The reverted version's own header claimed it checked those
and did not, which is a comment standing in for enforcement.
