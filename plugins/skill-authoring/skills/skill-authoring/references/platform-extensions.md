# Platform Extensions

Features and directory conventions beyond the base Agent Skills spec, per
platform.

## Contents

- Skill directory conventions (project, user, compatibility reads, canonical
  location)
- Nested directory limitations
- Frontmatter field compatibility
- Codex CLI specifics
- Claude Code specifics
- Cursor specifics
- Gemini CLI specifics
- Amp specifics

## Skill directory conventions

### Project-level (version-controlled)

| Platform    | Directory                                  |
| ----------- | ------------------------------------------ |
| Cursor      | `.agents/skills/`, `.cursor/skills/`       |
| Codex CLI   | `.agents/skills/` (scans CWD to repo root) |
| Claude Code | `.claude/skills/`                          |
| Gemini CLI  | `.gemini/skills/`                          |
| Amp         | `.agents/skills/`                          |
| Augment     | `.agents/skills/`, `.claude/skills/`       |

### User-level (global, not committed)

| Platform    | Directory                                 |
| ----------- | ----------------------------------------- |
| Cursor      | `~/.cursor/skills/`                       |
| Codex CLI   | `~/.agents/skills/`, `/etc/codex/skills`  |
| Claude Code | `~/.claude/skills/`                       |
| Gemini CLI  | `~/.gemini/skills/`                       |
| Amp         | `~/.config/agents/skills/`                |
| Augment     | `~/.augment/skills/`, `~/.agents/skills/` |

### Compatibility reads

Cursor also reads: `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`,
`~/.codex/skills/`

Augment also reads: `~/.claude/skills/`

### Recommended canonical location

Use `.agents/skills/` as the canonical, version-controlled location. It is
natively read by Cursor, Codex, Amp, and Augment.

For platforms that don't read `.agents/skills/`, create symlinks:

```bash
# Claude Code compatibility
ln -sfn .agents/skills .claude/skills

# Gemini CLI compatibility
ln -sfn .agents/skills .gemini/skills
```

Add the symlink targets to `.gitignore` if the symlinks themselves should not be
committed, or commit them if all contributors use the same platforms.

Gemini CLI also has a built-in link command:

```bash
gemini skills link .agents/skills --scope workspace
```

## Nested directory limitations

**Within a skill** -- subdirectories like `references/`, `scripts/`, `assets/`
are universally supported. This is part of the Agent Skills spec.

**Within the skills folder** -- organizing skills into category subdirectories
(e.g., `skills/infra/deploy/SKILL.md`) is NOT portable:

- Claude Code only scans the top level of its skills directory; nested skills
  are not discovered (open feature request)
- Other platforms generally expect the flat structure
  `skills/<skill-name>/SKILL.md`

If you need categories, use name prefixes instead: `infra-deploy`,
`infra-monitor`, `data-pipeline`.

## Frontmatter field compatibility

The Agent Skills spec defines these frontmatter fields: `name`, `description`,
`license`, `compatibility`, `metadata`, `allowed-tools`. The spec does not
prohibit additional fields.

Platform-specific fields (e.g., Claude Code's `context`, `agent`, `hooks`;
Cursor's `disable-model-invocation`) are **ignored at runtime** by platforms
that do not recognize them. It is safe to include them.

**Caveat**: some validation tools reject unknown fields. Codex's bundled
`quick_validate.py` has a hardcoded allowlist and will fail on any field not in
`{name, description, license, allowed-tools, metadata}`. The agentskills.io
reference validator (`agentskills validate`) is more permissive and follows the
spec.

If strict cross-tool validation matters, put platform-specific configuration in
the `metadata` map instead:

```yaml
metadata:
  claude-context: fork
  claude-agent: Explore
```

However, platform runtimes typically only read their own named fields, not
`metadata` equivalents. In practice, include platform-specific fields directly
and accept that some validators may warn.

## Codex CLI specifics

Codex scans upward from CWD to repo root, discovering skills in parent
directories. Useful for monorepos where shared skills live at the repo root and
package-specific skills live deeper.

Codex also supports:

- `agents/openai.yaml` -- UI metadata for skill lists and chips (display name,
  short description, default prompt, icon, brand color), plus
  `dependencies.tools` declaring MCP tools the skill needs; the file never
  enters model context
- `policy.allow_implicit_invocation` -- when false, the skill is not injected
  into context by default; must be invoked explicitly via `$skill-name`

Codex documents a context budget for the skills list: at most 2% of the model's
context window, or 8000 chars when the window is unknown. Descriptions beyond
the cap get cut from the list, so fleet-wide description size has a hard failure
mode there, not just a cost.

## Claude Code specifics

Claude Code extends the Agent Skills standard with several frontmatter fields:

| Field                      | Purpose                       |
| -------------------------- | ----------------------------- |
| `disable-model-invocation` | `true` = only user invokes    |
| `user-invocable`           | `false` = only Claude invokes |
| `context`                  | `fork` = run in subagent      |
| `agent`                    | Subagent type when forked     |
| `model`                    | Model override for this skill |
| `allowed-tools`            | Tools pre-approved to run     |
| `argument-hint`            | Autocomplete hint for `/`     |
| `hooks`                    | Lifecycle hooks for skill     |

### String substitutions

| Variable               | Description                   |
| ---------------------- | ----------------------------- |
| `$ARGUMENTS`           | All arguments passed          |
| `$ARGUMENTS[N]`        | Nth argument (0-based)        |
| `$N`                   | Shorthand for `$ARGUMENTS[N]` |
| `${CLAUDE_SESSION_ID}` | Current session ID            |

### Dynamic context injection

The `!`command\`\` syntax runs shell commands before the skill content is sent
to Claude. Output replaces the placeholder:

```markdown
## PR context
- Diff: !`gh pr diff`
- Comments: !`gh pr view --comments`
```

## Cursor specifics

Cursor supports `disable-model-invocation`. When `true`, the skill behaves like
a slash command -- only included in context when explicitly invoked via
`/skill-name`.

Skills appear in Cursor Settings > Rules > Agent Decides section.

Symlink support was broken before Cursor v2.5 but is now fixed.

## Gemini CLI specifics

Gemini CLI discovers skills from `.gemini/skills/` (workspace) and
`~/.gemini/skills/` (user).

Built-in skill management commands:

```bash
gemini skills list
gemini skills link /path/to/skills-repo
gemini skills link /path/to/skills --scope workspace
gemini skills install <source>
```

In interactive sessions, use `/skills reload` to refresh discovery without
restarting.

## Amp specifics

Amp reads `.agents/skills/` natively and also supports `.claude/skills/` for
compatibility. Migrating slash commands to skills follows the standard SKILL.md
format with frontmatter.
