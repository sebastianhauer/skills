---
name: skill-authoring
description: Best practices, conventions, and tooling for authoring Agent Skills -- SKILL.md structure, frontmatter rules, description writing, token budgets, trigger evals, and a review rubric. Use when the user wants to create, review, improve, or split a skill, write or update a SKILL.md, package a workflow or runbook as a reusable skill, teach an agent a repeatable capability, check skill conventions or guidelines, or measure skill token cost.
license: LICENSE
compatibility: Python 3.9+ for bundled scripts; trigger_eval.py additionally requires the Claude Code CLI or the Codex CLI (--agent codex)
metadata:
  short-description: Create or review an Agent Skill
---

# Skill Authoring

Authoring guide for Agent Skills: decide whether a skill should exist, write one
that triggers reliably, keep it cheap in context, and prove it works.

The process: understand, plan, implement, review, iterate. Creating a new skill?
Read "When not to create a skill", then start at Workflow step 1; the scaffolder
arrives at step 3 (`python3 scripts/init_skill.py <name> --path <dir>`).
Reviewing or improving one? Jump to step 4 and
[review-rubric.md](references/review-rubric.md); splitting an overgrown one is
covered there too. Measuring cost?
`python3 scripts/skill_budget.py <skill-dir>`. Script paths are relative to this
skill's directory.

## Dependencies

None required -- rules, references, linter, eval harness, scaffolder, and the
markdownlint config in `assets/` all ship with this skill. Optional at runtime:
`trigger_eval.py` needs the Claude Code CLI or, via `--agent codex`, the Codex
CLI (see `compatibility`); with neither, use the manual spot-check in
[trigger-evals.md](references/trigger-evals.md). Skills authored with this skill
follow the same rule: independent by default, dependencies named explicitly or
not at all.

## Core principles

- The context window is a public good, shared with the system prompt, the
  conversation, and every other skill. Each layer has a price (see Token
  budget); spend deliberately.
- The agent is already smart. Add only what it does not know -- conventions,
  non-obvious domain facts, fragile procedures. Every paragraph must justify its
  token cost.
- Match freedom to fragility: concise text for flexible tasks, exact scripts for
  fragile ones. Scale: [patterns.md](references/patterns.md).

## When not to create a skill

Every skill charges the fleet a standing trigger cost; it must earn its place.
Do not create one when:

- the task is one-off -- do the task, skip the packaging
- the agent already does it well unaided -- baseline first, fill only measured
  gaps
- one or two lines of project instructions would cover it
- an existing skill covers the domain -- extend it instead of adding a competing
  trigger surface

## Spec reference

Frontmatter fields, optional directories, progressive disclosure, and
validation: [spec-quick-ref.md](references/spec-quick-ref.md).

## Workflow

### 1. Understand

If the idea comes out of live work ("turn this into a skill"), mine the
conversation first -- tools used, step sequence, corrections, input and output
formats -- then fill gaps by asking. Either way, answer:

- What queries or tasks should trigger this skill?
- What does the agent need to know that it does not already know?
- What scripts, references, or assets would be reused across invocations?

Calibrate communication: authors range from developers to domain experts with no
coding background, so briefly explain terms like "frontmatter" when in doubt.
Match the style of existing skills in the target collection.

### 2. Plan

- Name: lowercase letters, digits, hyphens; under 64 chars; gerund or verb-led
  (`processing-pdfs`, `review-changes`), one style per collection. Directory
  matches. No vague names (`helper`, `utils`), no reserved words `anthropic` or
  `claude`.
- Description: third person, WHAT plus WHEN, phrased as users ask ("use when the
  user wants to X, asks about Y, or mentions Z"). Agents under-trigger, so
  enumerate concrete scenarios -- bounded by the spec limit, the per-session
  cost (see Token budget), and near-miss negative tests
  ([trigger-evals.md](references/trigger-evals.md)) against over-triggering.
- For skills that do destructive or expensive work, consider invocation gating:
  say in the description that the skill applies only on explicit user request.
  That wording works everywhere; per-platform gating fields are in
  [platform-extensions.md](references/platform-extensions.md).
- Split out reference files for anything detailed or domain-specific; wrap
  interchangeable backends with the contract/provider split
  ([patterns.md](references/patterns.md)).
- Decide degrees of freedom: text for flexible tasks, scripts for fragile
  operations ([patterns.md](references/patterns.md)).

#### Layer responsibilities

Default to this split unless there is a strong reason not to:

- `SKILL.md`: trigger conditions, guardrails, happy-path workflow, pointers
- CLI `--help`: commands, flags, defaults, exit behavior, minimal examples
- `references/`: setup, config, troubleshooting, extended workflows, caveats
- `scripts/`: executable behavior and repeated operations, not prose

#### Token budget

Each layer has a different context price:

- Trigger cost: `name` + `description` load in EVERY session, used or not.
  Across a fleet, description bytes are the standing tax -- and some platforms
  hard-cap the skills list, silently dropping skills beyond it
  ([platform-extensions.md](references/platform-extensions.md)).
- Invoke cost: the body loads on every trigger. Keep it navigational.
- On-demand: `references/` load only when opened. Detail is nearly free.
- Free: `scripts/` execute without entering context.

`python3 scripts/skill_budget.py <skill-dir>` reports a skill's costs and rule
violations; point it at a skills root for fleet totals.

### 3. Implement

Scaffold: `python3 scripts/init_skill.py <name> --path <dir>` (optionally
`--resources scripts,references,assets`) creates a structurally valid starter;
resolve its TODOs before the checklist counts it as done.

#### Directory layout

`SKILL.md` (required) plus optional `scripts/`, `references/`, `assets/` --
diagram in [spec-quick-ref.md](references/spec-quick-ref.md). Install location
is governed by the canonical-directory rule under Conventions.

#### SKILL.md body

- Under 500 lines and ~5000 tokens -- lint failures in `skill_budget.py`, not
  suggestions; restructure before shipping a body that exceeds them.
- Imperative/infinitive form
- Concrete examples over verbose explanations
- Consistent terminology throughout
- No time-sensitive information; park deprecated material in a collapsed "old
  patterns" block ([patterns.md](references/patterns.md))
- Link every reference file with when-to-read guidance:
  `See [ref.md](references/ref.md) for details.`
- Reference MCP tools by fully qualified name (`ServerName:tool_name`)
- CLI-backed skills stay navigational: no `--help` duplication, no deep recipes
  in the top-level file

References stay one level deep. Reference files over 100 lines get a table of
contents (lint-enforced) so partial reads reveal full scope; for very large
references, add grep hints in SKILL.md
(`grep -i "revenue" references/finance.md`).

#### Cross-platform portability

Skills are cross-platform by design. Never reference platform-specific config
from skill content -- no Cursor rules (`.cursor/rules/`), no `CLAUDE.md`,
`GEMINI.md`, `AGENTS.md`, or `.cursorrules`; state conventions inline or in
references so any agent can read them.

Platform-specific frontmatter fields (Claude Code `context: fork`, Cursor
`disable-model-invocation`) are safe: unknown fields are ignored at runtime,
though some validators flag them
([platform-extensions.md](references/platform-extensions.md)).

#### Scripts

- Solve problems; do not punt errors to the agent -- handle them explicitly with
  helpful messages
- Document dependencies; justify constants (no magic numbers)
- Clarify intent: execute vs. read as reference
- Give every script a real `--help`: agents discover scripts through it, so
  usage, defaults, and exit codes belong there
- Target macOS, Linux, AND Windows unless a platform is explicitly scoped out;
  prefer Python. Verify uncertain flags against man pages or `--help`. Decision
  hierarchy, BSD vs GNU, Windows guidance:
  [command-portability.md](references/command-portability.md).
- Lint every script when tooling exists (linter table in
  [command-portability.md](references/command-portability.md)); note in the
  review when no linter ran.
- For high-stakes batch or destructive operations, use plan-validate-execute
  ([patterns.md](references/patterns.md)).

### 4. Review

Run a **fresh-eyes review** in a separate agent context -- authoring assumptions
mask gaps. [review-rubric.md](references/review-rubric.md) covers: spawning a
review subagent, the review dimensions, behavioral testing (paired
with/without-skill runs -- build eval tasks and a no-skill baseline BEFORE
writing extensive documentation), and decomposition heuristics.

Then confirm a fresh agent can trigger the skill from natural prompts, pick the
right first step, load only the needed references, and finish without wandering.
Test every model tier the skill will serve: smaller tiers need more guidance,
larger ones less.

For high-value skills or ambiguous triggering, run a quantitative trigger eval
over a reviewed query set with near-miss negatives
([trigger-evals.md](references/trigger-evals.md)).

Finish with a prose-tightening pass over the whole package: cut verbose wording;
rules and clarity are non-negotiable, word count is not.

Before shipping publicly, get at least one review from a different agent
architecture than the author's (mechanics in
[review-rubric.md](references/review-rubric.md)): reviewer families share blind
spots with their authors. Triage its findings -- it lacks your context and will
re-litigate settled decisions.

### 5. Iterate

Use the skill on real tasks; update the full package; re-review after
significant changes. When improving from observed usage:

- Read the transcripts, not just the outputs. If the skill causes unproductive
  work, remove the instructions causing it and re-test.
- Delete instructions that are not pulling their weight.
- Generalize from feedback instead of overfitting; reframe the underlying issue
  so the fix transfers beyond the tested prompt.
- If every real use rewrites the same helper, bundle it into `scripts/`.
- Explain why instead of stacking bare ALL-CAPS rules; reasoning generalizes
  where mandates do not.
- Prune the fleet: re-run the fleet budget lint periodically and retire skills
  that no longer earn their trigger cost.

When the same structural lesson appears across skills, promote it into this
meta-skill or a shared reference.

## Common patterns

Workflow, template, conditional, feedback-loop, quick-reference-table,
contract/provider, plan-validate-execute, and safety patterns (draft-first,
dry-run, confirmation gate): [patterns.md](references/patterns.md).

## Platform-specific features

Directory conventions per platform, symlink setup, and frontmatter extensions:
[platform-extensions.md](references/platform-extensions.md).

## Conventions

This skill's opinionated house rules. They go beyond the spec on purpose; adopt
them as hard rules for any collection this skill governs.

- Principle of least surprise: a skill's contents must never surprise a user who
  has read its description -- no hidden side effects, no misleading skills,
  nothing that could compromise the user's system or data.
- The canonical install directory is `.agents/skills/`. Never install into
  platform directories (`.claude/`, `.cursor/`, `.codex/`, `.gemini/`); symlinks
  from those to `.agents/skills/` are the compatibility mechanism
  ([platform-extensions.md](references/platform-extensions.md)). Drafting in a
  scratch directory is fine -- the rule governs where skills live.
- Documentation style: 80-char width (fill toward the maximum), ASCII only, no
  trailing whitespace. Width is enforced by MD013 in the bundled markdownlint
  config; table-pipe alignment by MD060.
- Every frontmatter value is a single physical line (plain or quoted scalar).
  Block scalars (`|`, `|-`, `>`, `>-`) and wrapped multiline values are
  disallowed: grep-based and naive line parsers get empty or truncated values
  from them (`grep '^description:'` must return the whole value). Unquoted
  values must not contain ": " (invalid YAML). One-level nested maps like
  `metadata` are fine when each entry is a single-line `key: value` pair. The
  80-char rule does NOT apply inside frontmatter -- never wrap a value for
  width.
- `LICENSE` (or `LICENSE.txt`) is the one permitted top-level file besides
  SKILL.md, referenced from the `license` frontmatter field. No README,
  CHANGELOG, or other extraneous files -- a skill is agent-facing, and git
  history is the changelog.

## Checklist

Before finalizing a skill:

### Frontmatter and spec

- [ ] `name` matches parent directory
- [ ] `description` is third person, WHAT + WHEN, phrased as users ask
- [ ] All frontmatter values single-line; no unquoted ": "
- [ ] `python3 scripts/skill_budget.py <skill-dir>` passes: spec limits, body
  size, frontmatter style, reference ToCs
- [ ] `agentskills validate` passes when the official skills-ref package is
  available (see spec-quick-ref.md)

### Body and references

- [ ] Body contains only non-obvious info
- [ ] References one level deep, individually focused, each linked from SKILL.md
  with when-to-read guidance
- [ ] Consistent terminology throughout
- [ ] Only LICENSE beyond SKILL.md at top level (no README, CHANGELOG)
- [ ] Follows doc style (80 chars filled, ASCII); markdownlint clean via
  `npx -y markdownlint-cli2`, using `assets/markdownlint.jsonc` when the repo
  has no config
- [ ] Markdown tables have aligned columns (padded pipes)

### Scripts and portability

- [ ] Commands and scripts portable across macOS, Linux, and Windows (unless a
  platform is explicitly scoped out)
- [ ] Scripts prefer Python; every script has a real `--help`
- [ ] Scripts linted (py_compile, shellcheck, PSScriptAnalyzer, as applicable)
- [ ] No references to platform-specific config (Cursor rules, CLAUDE.md,
  GEMINI.md, AGENTS.md)

### Validation and review

- [ ] Fresh-eyes review completed (see review-rubric.md)
- [ ] For publicly shipped skills: reviewed by a second agent architecture (see
  review-rubric.md)
- [ ] Fresh-agent prompt test completed; tested on every model tier served
- [ ] Behavioral eval with no-skill baseline for skills that change agent output
  (see review-rubric.md)
- [ ] Trigger eval run for high-value or ambiguous skills (see trigger-evals.md)
- [ ] Prose-tightening pass done: verbose wording cut, duplication removed,
  rules and clarity intact
