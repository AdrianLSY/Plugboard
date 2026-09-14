# Violating input: runner

Exercises [`ci/gates/runner.py`](../../gates/runner.py), which enforces
[every blocking gate runs without a person's initiative](../../../docs/method/rules/the-gates-actually-run.md).

## Violations

**Six** violations, exit 1, across **two** declared workflows:

1. `check.yml` carries `branches:` — a branch filter.
2. `check.yml` carries `continue-on-error:` — a non-zero exit that does not fail the job.
3. `check.yml` triggers on `push` only, missing `pull_request`.
4. `dco.yml` triggers on `push` only, missing the `pull_request` **it declares for itself**.
5. The `check` recipe begins with `-`, so make ignores its exit status.
6. The same recipe ends with `|| true`.

Cases 5 and 6 are separate because they are separate mistakes with one effect, and a fixture that
merged them would let either fix alone appear to work.

Case 4 is why the tree carries a second workflow. `ci/vault.json` declares each workflow's own
required triggers, so `dco.yml` is held to `pull_request` where `check.yml` is held to both — a
workflow that deliberately runs on fewer events states that as a decision the gate holds, rather than
differing from its sibling for no recorded reason. Before the declaration became a mapping, `dco.yml`
was named in no gate at all: a branch filter and a `continue-on-error:` could be added to it and
`make check` still reported every gate passing, which is the condition
[the rule](../../../docs/method/rules/the-gates-actually-run.md) exists to refuse.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/runner.py --root ci/broken-inputs/runner/tree` | exit 1, five violations |
| `python3 ci/gates/runner.py` | exit 0 against the declared runner |

## Not violations here

An absent configuration. It is checked, and planting it would stop the run before reaching the four
clause cases, which are this fixture's subject.

## The three undeclared-workflow cases, added by task 3.1

`ci/vault.json` declares five workflows since D29 settled task 3.1, and this tree carries two. The
other three are therefore reported as declared-but-absent — which is the same case the tree already
demonstrated for one file, now demonstrated for the set.

That is the point of the case rather than an accident of the fixture. `ci/gates/runner.py` checks the
forbidden clauses ONLY on declared workflows, so an undeclared one is a blocking job whose path
filters, branch filters and `continue-on-error` nothing reads. Three of the repository's five were in
exactly that state until D29. The reverse direction — a workflow file that exists and is declared
nowhere — is held by the `runner-workflows` correspondence in `ci/gates/correspondences.py`, because
this gate is keyed on the declaration and cannot see a file the declaration omits.
