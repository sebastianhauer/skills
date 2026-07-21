# Contributing

## Development

The dev toolchain is managed by [uv](https://github.com/astral-sh/uv) on a
vanilla stock CPython 3.9 -- the lowest version any shipped script must run on.
`make check` is the gate; the git hooks and CI run the same targets.

```bash
make bootstrap   # vanilla 3.9 venv + git hooks
make             # list all targets
make check       # py_compile + ruff + pyright + mypy + markdownlint + pytest
make format      # ruff --fix, then ruff format
```

## How changes land

`master` is protected -- no direct pushes; every change goes through a pull
request.

- Branch off `master` with a Conventional Branch name -- `feat/`, `fix/`,
  `chore/`, `hotfix/`, or `release/`.
- Write commit messages as
  [Conventional Commits](https://www.conventionalcommits.org); the `commit-msg`
  hook and CI both enforce it.
- A PR merges once CI is green (`lint`, `test` on 3.9 and 3.13,
  `conventional-commits`) and it has one approving review.
- PRs **squash-merge**: the PR title and body become the final commit message,
  so write them like one.

## Commit authorship

Commits and their trailers name real people only. Never add an AI or any other
non-human identity as an author, `Co-authored-by`, or `Signed-off-by`. A
`Signed-off-by` or `Co-authored-by` is valid only when a human explicitly
directs it and names a real person -- so decline when a tool offers to add
itself.

## Git hooks

- **commit-msg** -- [Conventional Commits](https://www.conventionalcommits.org)
  are mandatory (types:
  `feat fix docs refactor perf test build style ci revert chore`).
- **pre-commit** (fast) -- hygiene, `ruff` lint + format, `markdownlint`.
- **pre-push** (slower) -- `py_compile`, `pyright`, `mypy`, `pytest`.

## Python 3.9 compatibility

Shipped scripts must run on stock CPython 3.9. Three layers enforce it:

- `py_compile` byte-compiles every tracked script on 3.9, catching 3.10+ syntax
  such as `match` even in scripts with no test.
- `ruff` (target `py39`), `pyright`, and `mypy` all target 3.9; ruff `FA102`
  requires `from __future__ import annotations` before any PEP 604 `X | Y`
  union.
- CI runs `py_compile` + `pytest` on a 3.9 and a latest-stable matrix.

Write scripts with `from __future__ import annotations` so modern annotation
syntax stays 3.9-safe. Ruff `FA102` enforces it, and the test files under
`tests/` all carry the import as the worked example.

## Tests

Tests live at the repo root under `tests/`, deliberately **outside** `plugins/`,
so `npx skills add` never copies them. Mirror each skill under
`tests/<skill_name>/`. Three fixtures reach a skill's code:

```python
def test_unit(load_package):     # package submodule, relative imports ok
    fm = load_package("skill-authoring", "skillkit.frontmatter")
    fields, violations, _ = fm.parse_frontmatter("---\nname: x\n---\n")
    assert violations == []

def test_cli(load_script):       # in-process main([...]) -> exit code
    main = load_script("skill-authoring", "init_skill").main
    assert main(["my-skill", "--path", str(tmp_path)]) == 0

def test_e2e(run_script):        # subprocess: real 3.9 __main__ path
    result = run_script("skill-authoring", "init_skill", "smoke", "--path", str(tmp_path))
    assert result.returncode == 0
```

Every `plugins/*/skills/*/scripts/**/*.py` is auto import-smoke-tested, so a new
script that fails to import on 3.9 is caught even without its own test.

## Repository layout

```text
skills/                               # repo root = marketplace root
├── README.md
├── CONTRIBUTING.md
├── LICENSE                           # Apache-2.0 (whole repo)
├── .claude-plugin/
│   └── marketplace.json              # Claude marketplace (read by Claude Code)
├── .agents/
│   └── plugins/
│       └── marketplace.json          # Codex marketplace (read by Codex)
└── plugins/
    └── <plugin-name>/                # one self-contained plugin per skill
        ├── .claude-plugin/
        │   └── plugin.json           # Claude plugin manifest (strict mode)
        ├── .codex-plugin/
        │   └── plugin.json           # Codex plugin manifest
        └── skills/
            └── <plugin-name>/
                ├── SKILL.md          # required; shared by all three install paths
                └── LICENSE           # Apache-2.0 (per skill, if copied out)
```

## Cross-agent packaging

Each skill has a single shared `SKILL.md`, wrapped by native manifests for each
ecosystem: a `.claude-plugin/plugin.json` and a `.codex-plugin/plugin.json` per
plugin, and two root marketplaces (`.claude-plugin/marketplace.json` for Claude,
`.agents/plugins/marketplace.json` for Codex). The vercel `skills` CLI needs no
manifest -- it reads the `SKILL.md` directly. One skill tree, three install
paths.

## Adding a skill

1. Scaffold it with the authoring skill's own generator, run from the repo root.
   Each skill is its own plugin, so create the plugin's `skills/` parent first:

   ```bash
   mkdir -p plugins/<new-skill-name>/skills
   python3 plugins/skill-authoring/skills/skill-authoring/scripts/init_skill.py \
     <new-skill-name> --path plugins/<new-skill-name>/skills
   ```

   The directory name must match the `name` field in its `SKILL.md` frontmatter,
   which the scaffolder handles.

1. Fill in the `SKILL.md`; add a per-skill `LICENSE`.

1. Add a plugin manifest at
   `plugins/<new-skill-name>/.claude-plugin/plugin.json` (at minimum a `name`
   matching the directory; skills auto-discover under strict mode) **and** a
   `plugins/<new-skill-name>/.codex-plugin/plugin.json` (`name`, semver
   `version`, `description`, `skills: "./skills/"`, and an
   `interface.displayName`). Keep `version` in sync between the two.

1. Add an entry to **both** root marketplaces -- this two-marketplace upkeep is
   manual. In `.claude-plugin/marketplace.json` (Claude schema, string
   `source`):

   ```json
   { "name": "<new-skill-name>", "source": "./plugins/<new-skill-name>" }
   ```

   In `.agents/plugins/marketplace.json` (Codex schema: object `source` +
   `policy` + `category`):

   ```json
   {
     "name": "<new-skill-name>",
     "source": { "source": "local", "path": "./plugins/<new-skill-name>" },
     "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
     "category": "Productivity"
   }
   ```

## Third-party code

When a skill bundles third-party code, record its origin and license where the
code ships: for a small vendored snippet an inline notice in the file header
plus a line in the skill's `LICENSE` suffices (as `skill-authoring` does for
`scripts/trigger_eval.py`); add a `THIRD_PARTY_NOTICES.md` only when the bundled
components grow beyond that.

## License

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](./LICENSE), the same license as the project.
