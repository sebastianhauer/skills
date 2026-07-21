#!/usr/bin/env python3
"""Scaffold a structurally valid Agent Skill starter.

The name and CLI shape follow the init_skill convention from the
Anthropic/OpenAI skill-creator scaffolders; the implementation is
original to this skill.
"""

import argparse
import sys
from pathlib import Path

# PYTHONSAFEPATH (3.11+) drops the script dir from sys.path; put it
# back so the sibling skillkit package always resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skillkit import (
    RESERVED_NAME_WORDS,
    SPEC_NAME_MAX_CHARS,
    SPEC_NAME_PATTERN,
)

VALID_RESOURCES = ("scripts", "references", "assets")

# Emitted as ONE line: frontmatter values must be single-line.
DESCRIPTION_PLACEHOLDER = (
    "TODO one line, third person -- WHAT the skill does, then WHEN, "
    'phrased as users ask ("Use when the user wants to X, asks about '
    'Y, or mentions Z"). Single line, under 1024 chars, no block '
    "scalars, no unquoted colon-space."
)

TEMPLATE = """\
---
name: {name}
description: {description}
---

# {title}

TODO: one or two sentences orienting the agent -- what this skill covers and
what outcome it produces.

## Workflow

TODO: the happy path, imperative form, only what the agent does not already
know. Link reference files with when-to-read guidance, e.g.
See [details.md](references/details.md) when handling X. For non-procedural
skills, replace this section with the structure patterns.md suggests
(template, quick-reference table, ...).

## Checklist

- [ ] TODO: the 2-3 checks that matter most for this skill
"""

NEXT_STEPS = """\
Created {skill_dir}

Next steps:
  1. Write the description (the trigger surface -- most important line)
  2. Fill in the workflow
  3. Lint:   python3 {budget} {skill_dir}
  4. Review: fresh-eyes review + trigger eval (see the skill-authoring skill)
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Create a new Agent Skill directory with a "
        "SKILL.md starter that passes the structural lint (single-line "
        "frontmatter, checklist stub); resolve its TODOs before "
        "shipping.",
        epilog="exit codes:\n"
        "  0  skill created\n"
        "  2  invalid name, unknown --resources entry, or the target "
        "directory already exists\n\n"
        "example:\n"
        "  python3 init_skill.py review-changes --path ~/.agents/skills "
        "--resources scripts,references",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "name",
        help="skill name: lowercase letters, digits, hyphens; under "
        f"{SPEC_NAME_MAX_CHARS} chars; becomes the directory name",
    )
    parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="parent directory to create the skill in (default: cwd)",
    )
    parser.add_argument(
        "--resources",
        default="",
        metavar="LIST",
        help="comma-separated subdirectories to create: " + ",".join(VALID_RESOURCES),
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    name = args.name
    if len(name) > SPEC_NAME_MAX_CHARS or not SPEC_NAME_PATTERN.match(name):
        print(
            f"error: invalid name '{name}': lowercase [a-z0-9-], no "
            f"leading/trailing/consecutive hyphens, max "
            f"{SPEC_NAME_MAX_CHARS} chars",
            file=sys.stderr,
        )
        return 2
    for word in RESERVED_NAME_WORDS:
        if word in name:
            print(
                f"warning: name contains reserved word '{word}' "
                f"(rejected by Anthropic's platform validator)",
                file=sys.stderr,
            )

    resources = [r for r in args.resources.split(",") if r]
    invalid = [r for r in resources if r not in VALID_RESOURCES]
    if invalid:
        print(
            f"error: unknown resource dir(s): {', '.join(invalid)} "
            f"(valid: {', '.join(VALID_RESOURCES)})",
            file=sys.stderr,
        )
        return 2

    # Display the path as given; resolve only for filesystem checks
    # (macOS resolves /tmp to /private/tmp, which confuses readers).
    display_dir = Path(args.path) / name
    skill_dir = Path(args.path).resolve() / name
    if skill_dir.exists():
        print(
            f"error: {skill_dir} already exists; refusing to overwrite",
            file=sys.stderr,
        )
        return 2

    skill_dir.mkdir(parents=True)
    title = name.replace("-", " ").title()
    (skill_dir / "SKILL.md").write_text(
        TEMPLATE.format(name=name, title=title, description=DESCRIPTION_PLACEHOLDER),
        encoding="utf-8",
    )
    for resource in resources:
        (skill_dir / resource).mkdir()

    budget = Path(__file__).resolve().parent / "skill_budget.py"
    print(NEXT_STEPS.format(skill_dir=display_dir, budget=budget))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
