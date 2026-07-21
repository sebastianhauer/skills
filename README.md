# Skills

A personal, growing collection of
[agent skills](https://github.com/anthropics/skills) by Sebastian Hauer. Each
skill ships as its own self-contained plugin under [`plugins/`](./plugins) and
is portable across coding agents (Claude Code, Cursor, Codex, and others).

## Install

The repo installs three ways:

- the cross-agent vercel `skills` CLI
- the Claude Code plugin marketplace
- the Codex plugin marketplace

### vercel `npx skills` (cross-agent)

The [`skills` CLI](https://github.com/vercel-labs/skills) reads each skill's
`SKILL.md` directly and installs it into whichever agent you target with `-a`:

```bash
# Interactive picker for every skill in this repo
npx skills add sebastianhauer/skills

# List available skills
npx skills add sebastianhauer/skills --list

# Install one skill into a specific agent
npx skills add sebastianhauer/skills --skill skill-authoring -a claude-code

# Try a skill without installing it
npx skills use sebastianhauer/skills@skill-authoring | claude
```

### Claude Code plugin marketplace

The repo ships a `.claude-plugin/marketplace.json`, so it works as a Claude Code
plugin marketplace. Each skill is its own plugin, so install them individually:

```text
/plugin marketplace add sebastianhauer/skills
/plugin install skill-authoring@psicode
/plugin install conventional-commits@psicode
```

### Codex plugin marketplace

The repo also ships a Codex marketplace at `.agents/plugins/marketplace.json`
plus a per-plugin `.codex-plugin/plugin.json`. Add the marketplace, then install
a plugin from the Codex Plugins directory (the `/plugins` browser):

```bash
codex plugin marketplace add sebastianhauer/skills
# then open /plugins in Codex and install conventional-commits / skill-authoring
```

### Manual install

Copy or symlink any skill directory into your agent's skills path, e.g. for
Claude Code:

```bash
ln -s "$PWD/plugins/skill-authoring/skills/skill-authoring" \
  ~/.claude/skills/skill-authoring
```

## Using a skill

Once installed, there is nothing to run. Each skill is instructions your agent
loads on demand: when a task matches a skill's description, the agent reads its
`SKILL.md` and follows it -- ask about a commit message, for example, and
`conventional-commits` kicks in. Most agents also let you invoke one by name.

## Contributing

Repository layout, the dev toolchain, how to package a new skill, and the PR
workflow live in [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

[Apache License 2.0](./LICENSE). Each skill also carries its own `LICENSE` so it
stays licensed when copied out on its own.
