# Violating input: proxy-tooling

- **Checked by:** `ci/proxy-tooling-check.py` — a script, not a gate. There is no
  `ci/gates/proxy_tooling.py`, and the naming rule that pairs a directory here to a gate module is
  answered instead by `gate_policy.script_paired_inputs` in `ci/vault.json`; see *Why this is not a
  gate* below. The script asserts that that entry and `expect.json`'s `checked_by` name it, so the
  pairing cannot be half-declared.
- **Subject:** the `lint` recipe of `ci/make/elixir.mk`, reached as `make -C proxy lint`.
- **Principle it applies:** [gates are demonstrated to fail](../../../docs/method/rules/gates-are-demonstrated-to-fail.md),
  extended from this repository's own gates to the third-party tools the proxy's lint target invokes.
- **Task:** `rebuild-plugboard` 2.2.
- **Declaration:** `expect.json`, which is what asserts; nothing in this note is read as one.

## The six inputs, one per tool in the recipe

| tree | tool | what is planted | what fails |
|---|---|---|---|
| `tree-compile` | `mix compile --warnings-as-errors` | an argument bound and never read | `compile`, `dialyzer` |
| `tree-format` | `mix format --check-formatted` | a body indented six columns, not four | `format` |
| `tree-credo` | `mix credo --strict` | a public function with no `@spec` | `credo` |
| `tree-dialyzer` | `mix dialyzer` | a `@spec` of `:ok` over a body returning `:error` | `dialyzer` |
| `tree-sobelow` | `mix sobelow --exit` | `Code.eval_string/1` on a caller-supplied binary | `sobelow` |
| `tree-deps-audit` | `mix deps.audit` | a lockfile entry for `plug` 1.3.0 | `deps-audit` |

This table is a reading aid. Every column of it is stated in `expect.json` — `tool`, `plants`,
`fails` — and read there; a row here that drifts from the declaration changes nothing the check does.

Each tree is laid over a copy of `proxy/`, not over the repository — a tree here holds only the files
it plants. Five of the six make exactly one tool refuse while the other five stay silent, which is
the property the directory exists for: a tool that fires on everything is no more informative than a
tool that fires on nothing.

## The declaration has to BIND, not just label

A `tool` field is a label. The roster assertion — every command in the `lint` recipe is named by some
input — is satisfied by the label alone, and the two assertions that would catch a wrong one (the
declared `case` appears in the failing tool's output, and `make -C proxy lint` refuses the tree) are
both decidable only when the named tool is among the tools that actually failed. Swap two trees'
`tool` fields and nothing measured changes, both of those skip, and the run reports ok over two tools
bound to no input at all. That was demonstrated, not imagined, so the declaration now carries four
requirements the check reads before any process starts:

- **`tool` is in `fails`.** Without it the input is bound to no tool: the measured set is compared
  against `fails`, and the case and target assertions skip.
- **`case` is present.** A tree with no `case` accepts any non-zero exit at all as a demonstration of
  the rule the tool is supposed to enforce.
- **`plants` names exactly the files the tree lays over `proxy/`,** checked in both directions. A
  declared file that is absent planted nothing; a file in the tree that is undeclared changes the
  copied tree in a way nothing asserts about, which is how a fixture grows a second violation and the
  `fails` set quietly starts meaning something else. A plant that lands on top of a real
  `proxy/` file must also be declared `derived_from` it.
- **`why_not_alone` is a `because` plus a `forced_by` citation** — a file and a string in it that the
  check looks up — for every tool in `fails` other than `tool`. A sentence alone licensed an
  arbitrarily large declared failing set for the price of writing one.

## The two that were expected not to be plantable, and were

**Sobelow reports on this project despite there being no Phoenix router.** It prints a warning that
it cannot find one and then runs its non-Phoenix checks over `lib/` anyway; `RCE.CodeModule` is one
of them. So a green Sobelow on the proxy is a scan that found nothing rather than a scan that looked
at nothing — which was the open question, and it is now answered by an input rather than by reading
the tool's source. What is still undecided is how much of Sobelow's check set is inapplicable here:
several checks do need a router, a controller or a Phoenix config, and this input says nothing about
those.

**`mix deps.audit` is demonstrated without pinning a vulnerable dependency anywhere real.**
`tree-deps-audit/mix.lock` is `proxy/mix.lock` plus one line naming `plug` 1.3.0, which carries
[GHSA-2q6v-32mr-8p8x](https://github.com/advisories/GHSA-2q6v-32mr-8p8x) — a published advisory, not
an invented one. Three things keep that honest:

1. It exists only in this fixture. `proxy/mix.exs` declares no `plug` dependency and `proxy/mix.lock`
   has no such entry; the line is applied to a scratch copy that is deleted when the run ends.
2. Both of its checksums are zeros, so `mix deps.get` could never fetch it. The line is readable by
   `mix_audit`, which reads a name and a version, and is inert to everything else.
3. `ci/proxy-tooling-check.py` refuses the fixture if it stops containing every line of the real
   lockfile, so it cannot quietly become a stale copy of a dependency set nobody uses.

`mix_audit` synchronises its advisory database from a clone under `~/.local/share/` on every run. If
that database is empty or unreachable, `mix deps.audit` reports "No vulnerabilities found" and exits
zero — a green that means nothing. That is the case this input catches: the check fails, naming
`deps-audit` as a tool that did not refuse its own violating input.

## The one that cannot be demonstrated alone, and why that is recorded rather than fixed

`tree-compile` fails two tools. `mix dialyzer` builds the project before analysing it, and
`proxy/mix.exs` sets `elixirc_options: [warnings_as_errors: true]` in every environment, so any input
that makes the compiler refuse makes Dialyzer refuse as well. The alternative — hunting for a warning
Dialyzer does not notice — would be a fixture shaped by the check rather than by the tool. So the set
is declared as two in `expect.json`, and the reason is not prose: `why_not_alone.dialyzer.forced_by`
cites `proxy/mix.exs` for the `warnings_as_errors` string, and the check reads that file and fails
when the string is gone — the wider set then has to be re-measured rather than re-declared. Half of
the mechanism is decidable that way; the other half is dialyxir's build-then-analyse behaviour, which
was measured rather than cited. The other four tools stay silent on this tree, and that is asserted.

## What the check asserts, beyond "the tool exits non-zero"

- The **declaration binds** before anything runs: the four requirements above.
- The **exact set** of failing tools equals the declared set. A tool that saw an input it should have
  been blind to fails the check just as a tool that missed its own input does.
- The failing tool's output carries the declared `case` substring. A tool exiting non-zero for an
  unrelated reason demonstrates nothing about the rule it enforces — the inference
  `ci/gates/meta.py` makes with its neuter test, made here against output instead.
- `make -C proxy lint` itself refuses each input. This is not implied by the tool refusing: a recipe
  line prefixed with `-` swallows its command's exit status, and the target then passes over a tool
  that refused. Demonstrated by prefixing the Sobelow line with `-` in a scratch copy of
  `ci/make/elixir.mk`, which the check reports as *installed and not reachable from the target*.
- A clean copy of `proxy/` passes all six and passes `make -C proxy lint`. Every result above means
  nothing without it.
- Every command in the `lint` recipe is paired with an input naming it. The roster is parsed from the
  recipe rather than declared, so a tool added to lint and demonstrated by nothing is a failure.
- `expect.json`'s `checked_by` and `ci/vault.json`'s `gate_policy.script_paired_inputs` entry name
  the same script. Two declarations of who checks this directory drift; the check reads both.

## What a green run here does NOT say

It says the configured tool fires. It does not say the configuration is the right one — that is
review's, and the boundary matters most for Credo: `proxy/.credo.exs` enables exactly three checks
(`Readability.Specs`, `Design.TagTODO`, `Design.TagFIXME`), so `mix credo --strict` as wired by task
2.1 runs three checks, and `tree-credo` demonstrates one of them. Read the row above as *Credo
refuses a violation of the rules it is configured to enforce*, never as *Credo is broadly
instrumented on this component*. The same boundary applies to Sobelow's reach, above, and to which
Dialyzer flags are set.

## Why this is not a gate

A gate's subject is a property of the tree, it starts no process, and it runs inside `make check` —
the command a contributor runs on every commit. This starts six external processes against a copied
tree, seven times over including the clean baseline, and takes about a minute warm. Putting that
inside `make check` would buy one demonstration at the cost of the latency budget the repository
treats as a correctness control ([fast-tier latency budget](../../../docs/code/rules/fast-tier-latency-budget.md)).

So `ci/broken-inputs/proxy-tooling/` pairs to a script rather than to `ci/gates/proxy_tooling.py`,
and that pairing is declared in `ci/vault.json` under `gate_policy.script_paired_inputs` — which is
what makes a directory here with no gate module of its name a decision rather than an orphan.
`ci/gates/meta.py` and `ci/gates/fixture_declarations.py` both leave it alone: the first iterates
gate modules, and the second skips a directory with no module of its name.

## What still has no automatic runner

Nothing invokes this script. It is in no `make` target and in no workflow, so it re-runs when a human
types it and not when `ci/make/elixir.mk`, `proxy/.credo.exs` or `proxy/mix.exs` changes — the edits
that can silently unbind a tool from its input. The wiring is one step in
`.github/workflows/test.yml`, beside the existing `- run: make -C proxy lint`:

```yaml
      - run: python3 ci/proxy-tooling-check.py
```

It belongs after that line, which is what creates `proxy/_build` and `proxy/deps`; the script refuses
rather than skips when either is absent, so ordering it earlier turns the job red for the wrong
reason. Until that step exists, `rebuild-plugboard` task 3.3 — the lint gate verified "against its
planted violation from tasks 2.2 and 2.3" — is verified by hand or not at all.

## Expected

```
python3 ci/proxy-tooling-check.py     # exit 0, six inputs, five of them failing one tool alone
python3 ci/proxy-tooling-check.py --list
python3 ci/proxy-tooling-check.py --only credo
```

Prerequisites: `mix` on `PATH`, and `proxy/deps` and `proxy/_build` present — `make -C proxy deps`
and one `make -C proxy lint` create them. A missing one is refused rather than skipped, because the
scratch copy inherits them and every tool would otherwise fail for that reason instead of the planted
one. The cached PLT under `proxy/priv/plts/` is inherited by the copy too; without it Dialyzer builds
a PLT inside each throwaway tree, which is slow enough to stop the check being run.
