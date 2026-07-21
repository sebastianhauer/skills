# Skill Review Rubric

## Contents

- Fresh-eyes review process (how to run, when to review, fresh-agent evaluation)
- Behavioral testing (paired with/without-skill evaluation)
- Review dimensions (focus, trigger accuracy, token efficiency, terminology,
  reference structure, spec compliance, portability)
- Decomposition heuristics (when and how to split)

## Fresh-eyes review process

After creating or substantially editing a skill, review it with a **fresh agent
context** -- one that was not involved in authoring. This prevents the authoring
agent's implicit assumptions from masking gaps in the skill.

### The review prompt

Every platform uses the same instructions; only the launch mechanics differ.
Substitute the skill path for `<skill-dir>`:

```text
You are a fresh-eyes reviewer who did not author this skill. Review
the Agent Skill package at <skill-dir> against its own rubric in
references/review-rubric.md. Read SKILL.md, every file in
references/, every script in scripts/, assets/, and LICENSE. Score
each rubric dimension (focus, trigger accuracy, token efficiency,
terminology consistency, reference structure, spec compliance,
cross-platform portability) as pass, needs-work, or fail, with
file:line evidence. Also check: does the skill obey its own stated
conventions? Do documented commands, flags, defaults, and exit codes
match what the scripts actually implement? Report prioritized
findings as severity, location, issue, and concrete fix, then state
whether the skill should be split. An empty review is acceptable
only if the package is genuinely clean.
```

### How to run it

Any coding-agent CLI that runs headless works: give it the review prompt, read
access to the skill directory, and the platform's read-only or plan mode when
one exists. Exact flags drift across versions -- discover the current invocation
from `<binary> --help` first, the same rule the Scripts section applies to
commands. Skinny hints per platform:

- Claude Code: a forked read-only agent (`context: fork`, `agent: Explore`)
  wrapping the prompt as a slash command, or a headless `claude -p` run
- Cursor CLI: `cursor agent -p --mode ask "<prompt>"` (one-time
  `cursor agent login`); in the IDE, a `readonly: true` subagent whose body is
  the prompt
- Codex CLI: `codex exec -s read-only "<prompt>"`; its native
  `codex exec review --base <branch>` reviews diffs with built-in instructions
  (`--base` excludes custom prompts -- frame via `--title`)
- Copilot CLI: `copilot -p "<prompt>"` with a read-only tool whitelist
  (`--available-tools`) and `--no-custom-instructions`

Whatever the platform: triage findings before applying them -- an external
reviewer lacks your context and may re-litigate settled decisions, while still
catching defects your own family of reviewers reliably misses.

No subagent capability in the current environment? Degrade gracefully: ask the
user to run the review prompt in a fresh session, or at minimum re-read the
whole package top-to-bottom in a later, separate context and score the same
rubric. A same-context self-review is the weakest form; label it as such in the
report.

### When to review

- After initial skill creation
- After significant restructuring
- When adding or removing reference files
- When description or trigger scope changes
- Before committing a skill to version control

### Fresh-agent evaluation

After the review, run a small fresh-agent evaluation with realistic prompts.
This complements the static review by testing discoverability and first-use
behavior.

Suggested process:

1. Use a fresh readonly agent context that did not author the skill
1. Use `3-5` natural prompts that should trigger the skill
1. Do not name the skill explicitly in the prompts
1. Compare the agent's behavior against the intended workflow

Score:

- discoverability
- first-step correctness
- reference selection
- task success
- obvious wandering

For high-value skills or ambiguous trigger scope, follow up with a measured
trigger eval over a reviewed query set (near-miss negatives included). See
[trigger-evals.md](trigger-evals.md).

## Behavioral testing (paired with/without-skill evaluation)

Trigger evals prove the skill fires; behavioral testing proves it helps. Paired
evaluation -- the same task run with and without the skill -- is the measurement
standard for skill efficacy, and it works best when built EARLY: write 2-3
realistic task prompts and run the no-skill baseline before writing extensive
documentation, so the skill fills measured gaps instead of imagined ones.

Process (fully conversational; no viewers or servers):

1. Pick 2-3 realistic tasks the skill should improve.
1. For each task, run two fresh subagents in the same turn: one told to read and
   follow the skill, one without it (or with the previous version when improving
   an existing skill). Save outputs to separate directories.
1. Compare the outputs with the user in chat: correctness, convention adherence,
   and cost (tokens/time per run when the harness reports them).
1. Feed the differences back into the skill; rerun the pair after meaningful
   edits.

If the with-skill runs are not clearly better, the skill body is not earning its
invoke cost: cut it, sharpen it, or question the skill's existence.

## Review dimensions

Score each dimension pass/needs-work/fail:

### 1. Focus (single responsibility)

- Does the skill do one thing well?
- Can the description be stated without "and" joining unrelated capabilities?
- Would different user queries activate different, non-overlapping sections?

### 2. Trigger accuracy

- Does the description include specific trigger terms?
- Is it third-person and actionable?
- Does it cover both WHAT and WHEN?
- Would an agent correctly match it to relevant queries?
- Would it falsely trigger on unrelated queries?

### 3. Token efficiency

- Is the SKILL.md body under 500 lines?
- Is `SKILL.md` mostly navigational when the skill has CLI help or deeper
  references?
- Is detailed content in reference files, not inlined?
- Does every paragraph justify its token cost?
- Is the agent told only what it does not already know?
- Does `python3 <skill-authoring-dir>/scripts/skill_budget.py <skill>` report no
  violations?
- Does the description justify its trigger cost (see Token budget in SKILL.md)?

### 4. Terminology consistency

- Is one term used throughout for each concept?
- No mixing of synonyms (e.g., "endpoint" vs "route" vs "path" for the same
  thing)?

### 5. Reference structure

- Are references one level deep from SKILL.md?
- Does SKILL.md clearly state when to read each reference file?
- Is responsibility clear between `SKILL.md`, CLI `--help`, references, and
  scripts?
- Are reference files individually focused?
- For files over 100 lines, is there a table of contents at the top?
- No duplicated content between SKILL.md and references?
- Are scripts and assets still necessary, clear, and minimally duplicative?

### 6. Spec compliance

- Frontmatter has required `name` and `description`?
- `name` matches parent directory?
- `name` follows naming rules (lowercase, hyphens, no consecutive hyphens, 1-64
  chars)?
- `description` under 1024 chars, no angle brackets?
- No extraneous files (README, CHANGELOG)?
- Markdown tables have columns padded to align pipe characters vertically?

### 7. Cross-platform portability

- Skill placed in `.agents/skills/` for broadest compatibility?
- Commands and scripts work on macOS, Linux, and Windows (unless a platform is
  explicitly scoped out)?
- Bundled scripts linted (see command-portability.md, Script linting)?
- No provider-specific assumptions baked in?
- No references to platform-specific config (Cursor rules, CLAUDE.md, GEMINI.md,
  AGENTS.md)?
- Conventions stated inline or in reference files, not via external config
  references?
- Symlinks documented if needed for Claude Code or Gemini CLI?

## Decomposition heuristics

Split a skill into multiple skills when:

- **Dual triggers**: the description needs "and" to cover its scope, joining
  unrelated capabilities (e.g., "deploys apps AND manages DNS records")
- **Mixed concerns**: domain knowledge is tangled with backend or provider
  details (use the contract/provider split from patterns.md, e.g. a
  `cloud-deploy` contract skill with `aws-deploy` / `gcp-deploy` providers)
- **Partial relevance**: different user queries would need different,
  non-overlapping sections of the body
- **Size after extraction**: body exceeds ~300 lines even after moving detail to
  reference files
- **Reuse potential**: a section would be useful to other skills independently

Focused beats exhaustive: benchmark evidence shows skills with at most about
three modules outperform larger bundles (SkillsBench,
<https://arxiv.org/abs/2602.12670>).

### How to split

1. Identify the distinct responsibilities
1. Create a new skill directory for each
1. Move the relevant SKILL.md content and references
1. Write focused descriptions for each new skill
1. If the original skill was a workflow combining the parts, keep a thin
   orchestration skill that references the others
1. Review each new skill against this rubric

### When NOT to split

- The sections are tightly coupled steps of one workflow
- Splitting would force agents to discover and load two skills for every
  invocation
- The skill is already under ~150 lines with no reference files
