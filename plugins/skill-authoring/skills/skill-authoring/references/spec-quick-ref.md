# Agent Skills Spec Quick Reference

Distilled from the canonical specification at
<https://agentskills.io/specification>

## Contents

- Frontmatter (fields, description guidelines, allowed-tools)
- Body content
- Optional directories (scripts, references, assets)
- Progressive disclosure
- File references
- Validation
- What NOT to include

## Frontmatter (YAML between `---` markers)

| Field           | Req | Constraints                    |
| --------------- | --- | ------------------------------ |
| `name`          | Yes | 1-64 chars, `[a-z0-9-]`, no    |
|                 |     | leading/trailing/consecutive   |
|                 |     | hyphens, must match parent dir |
| `description`   | Yes | 1-1024 chars, non-empty, no    |
|                 |     | angle brackets; WHAT + WHEN    |
| `license`       | No  | License name or bundled file   |
| `compatibility` | No  | 1-500 chars; env requirements  |
| `metadata`      | No  | String key-value map           |
| `allowed-tools` | No  | Space-delimited tool list      |
|                 |     | (experimental)                 |

Anthropic's platform validator additionally rejects the reserved words
"anthropic" and "claude" inside `name`.

### Description guidelines

The description is the **primary trigger mechanism**; agents read it at startup
to decide relevance. Spec constraints: third person, 1-1024 chars, no angle
brackets. Drafting guidance (WHAT+WHEN, user-phrased triggers) lives in
SKILL.md, Workflow step 2.

Scalar style: the spec permits any YAML scalar style; our house rule is
stricter. See the frontmatter rule under "Conventions" in SKILL.md.

### `allowed-tools` syntax

Pre-approved tools the skill may use. Syntax varies by platform but generally
follows:

```text
allowed-tools: Bash(git:*) Bash(jq:*) Read Write
```

Support is experimental and varies across agent implementations.

## Body content

No format restrictions. Write what helps the agent perform the task. Recommended
sections:

- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

The agent loads the full body once the skill activates. Split longer content
into reference files.

## Optional directories

```text
skill-name/
  SKILL.md              # Required
  scripts/              # Executable code
  references/           # Docs loaded on demand
  assets/               # Templates, data files
```

### `scripts/`

Executable code (Python, Bash, JS). Scripts should:

- Be self-contained or document dependencies
- Include helpful error messages
- Handle edge cases gracefully
- Clarify intent: execute vs. read as reference

### `references/`

Additional documentation loaded when needed:

- Domain-specific files (`finance.md`, `legal.md`)
- Detailed technical reference (`REFERENCE.md`)
- Templates and structured formats

Keep individual files focused. Smaller files mean less context consumed per
load.

### `assets/`

Static resources not loaded into context but used in output:

- Templates (config, document)
- Images (diagrams, examples)
- Data files (lookup tables, schemas)

## Progressive disclosure

Three loading levels manage context efficiently:

1. **Metadata** -- `name` and `description`, loaded at startup for ALL skills
1. **Instructions** -- SKILL.md body, loaded when the skill activates
1. **Resources** -- `scripts/`, `references/`, `assets/`, loaded only when
   needed; scripts can execute without entering context

What each level costs, and the size limits, are covered by Token budget and the
body rules in SKILL.md; the responsibility split across SKILL.md, CLI `--help`,
references, and scripts is under "Layer responsibilities" there.

## File references

Use relative paths from the skill root:

```markdown
See [reference guide](references/REFERENCE.md) for
details.

Run the extraction script: `scripts/extract.py`
```

Reference depth and ToC rules are under "SKILL.md body" in SKILL.md.

## Validation

Two complementary layers:

- `python3 scripts/skill_budget.py <skill-dir>` (bundled with the
  skill-authoring skill) -- house rules plus core spec limits; no dependencies
  beyond Python.
- `agentskills validate`, the agentskills.io reference validator -- spec
  conformance checked by the standard's own implementation (frontmatter format,
  required fields, naming).

The reference validator is the official Python package `skills-ref` on PyPI
(Apache-2.0, published by the Agent Skills authors); it installs a CLI named
`agentskills` and requires Python 3.11+. Run it without a permanent install:

```bash
uvx --from skills-ref agentskills validate ./my-skill
# pipx alternative; add --python when pipx's default is older than 3.11:
# pipx run --python python3.13 --spec skills-ref agentskills validate ./my-skill
```

For frequent use, `pip install skills-ref` (or `pipx install skills-ref`). When
no Python 3.11+ or installer is available, the bundled linter still covers the
house rules and core spec limits; note the skipped check in the review. Do NOT
use the `skills-ref` package on npm: it is not published by the Agent Skills
project.

## What NOT to include

- README.md, CHANGELOG.md, INSTALLATION_GUIDE.md (LICENSE is the one permitted
  extra top-level file; see Conventions in SKILL.md)
- User-facing documentation
- Setup, smoke tests, or troubleshooting in top-level `SKILL.md` when they fit
  better in `references/` or `scripts/`
- Information the agent already knows
