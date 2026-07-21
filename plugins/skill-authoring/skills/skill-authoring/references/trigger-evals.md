# Trigger Evals

Quantitative measurement of whether a skill's description makes an agent invoke
the skill when it should -- and stay away when it should not. This complements
the qualitative fresh-agent test in the review workflow. Run it for high-value
skills, for skills whose domain overlaps a neighboring skill, and after any
description change.

## Contents

- Eval set design (agent-agnostic)
- Bundled harness (Claude Code or Codex)
- Caveats (shadowing, model tier, cost, isolation)
- Interpreting results
- Other platforms

## Eval set design (agent-agnostic)

An eval set is a JSON array of queries with expected trigger behavior:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Aim for 16-20 queries total. The set is reusable across platforms and harnesses.

Queries must read like something a real user would type: concrete file names,
personal context, casual phrasing, abbreviations, the occasional typo. Abstract
one-liners measure nothing.

Bad: "clean up this file"

Good: "hey, the marketing export from last tuesday (downloads folder, named
something like leads_export_v3_final.csv) has dupe rows -- drop them and add a
region column based on the country field"

- Should-trigger (8-10): vary the phrasing and formality. Include cases that
  never name the skill or file type but clearly need it, uncommon use cases, and
  cases where this skill competes with another but should win.
- Should-NOT-trigger (8-10): near-misses only. Adjacent domains, keyword
  overlaps that a naive match would catch, and tasks the agent should handle
  with basic tools. Obviously irrelevant negatives ("write a fibonacci function"
  against a PDF skill) test nothing.

One more design constraint: agents only consult skills for tasks they cannot
trivially do themselves. A one-step query may correctly not trigger even with a
perfect description -- make positives substantive.

## Bundled harness (Claude Code or Codex)

This skill bundles the harness at `scripts/trigger_eval.py` (vendored from
anthropics/skills PR #1298, Apache-2.0; see the script header for local
changes). It measures with the Claude Code CLI by default, or the Codex CLI via
`--agent codex`; with neither installed, use the manual spot-check or the
alternatives below.

Run a measurement:

```bash
python3 scripts/trigger_eval.py \
  --eval-set /path/to/eval_set.json \
  --skill-path /path/to/skill-dir \
  [--model <model-id>] \
  --runs-per-query 3 \
  --verbose
```

`--model` is optional (the CLI's configured default applies); the per-query
`--timeout` defaults to 300 seconds.

Add `--agent codex` to measure with Codex instead. Backend differences the
numbers inherit: trigger rates are agent- and model-specific, so measure with
the runtime the skill's users actually have; Codex detects the consult by the
shell read of SKILL.md rather than a Skill tool call; and Codex has no turn cap,
so non-triggering runs work until done or `--timeout` (writes stay confined to
the throwaway project).

The harness installs the candidate description as a real skill inside a
throwaway temp project, runs the selected agent CLI headless per query
(`claude -p`, or `codex exec`), watches the event stream for the skill being
consulted, and cleans the temp project up. Test a candidate description without
editing the skill via `--description "..."` -- this is how to A/B a rewrite
against the current description.

Keep the whole loop conversational: design the eval set with the user in chat,
run the harness, read the JSON, propose a sharper description yourself, and
re-measure. No browser or review server is needed. (The optional skill-creator
skill offers an automated multi-iteration optimizer, `run_loop.py`, if hands-off
iteration is wanted.)

## Caveats

- Shadowing: if the same-named skill is installed user-level
  (`~/.claude/skills/` for Claude Code, `~/.agents/skills/` for Codex), it loads
  in every session and its description competes with the candidate under test.
  The harness warns; move the installed copy aside for the duration of the run,
  then restore it.
- Model tier: trigger rates are model-dependent. Smaller tiers may never consult
  a skill that larger tiers trigger reliably. Eval with the model the skill's
  users actually run (`--model`).
- Cost: every query run is a real headless agent session. 20 queries x 3 runs =
  60 sessions per iteration. Budget accordingly; use `--runs-per-query 1` for a
  cheap first pass.
- Isolation: runs execute inside a temp project, so eval queries that sound
  imperative ("set up X") cannot write into your real projects.

## Interpreting results

Each query reports a trigger rate over its runs; a positive passes at rate >=
0.5, a negative at rate < 0.5 (default `--trigger-threshold`).

- Positives failing: the description is too narrow or too abstract. Add the
  missing trigger scenarios.
- Negatives firing: the description is too broad or too pushy. Sharpen the WHEN
  wording; name what the skill is NOT for if needed.
- Iterate the description, not the eval set. Only change the eval set when a
  query itself is unrealistic.

## Other platforms

The eval set JSON is portable; the bundled harness covers Claude Code and Codex.
Options for other runtimes:

- Codex-native alternative: the `plugin-eval` example plugin
  (github.com/openai/plugins) generates a benchmark config and runs real
  `codex exec` sessions; its `analyze` and `explain-budget` commands add static
  description/budget checks.
- Any other runtime: a manual spot-check works everywhere -- run the agent
  headless with 2-3 positives and 2-3 near-miss negatives and observe whether
  the skill is consulted. The same eval-set discipline applies.
