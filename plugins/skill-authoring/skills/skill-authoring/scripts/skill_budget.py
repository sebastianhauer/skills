#!/usr/bin/env python3
"""Static token-budget report and lint for Agent Skills."""

import argparse
import sys
from pathlib import Path

# PYTHONSAFEPATH (3.11+) drops the script dir from sys.path; put it
# back so the sibling skillkit package always resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skillkit import (
    RESERVED_NAME_WORDS,
    SPEC_DESCRIPTION_MAX_CHARS,
    SPEC_NAME_MAX_CHARS,
    SPEC_NAME_PATTERN,
    parse_frontmatter,
)

# Body-size guidance from the spec's progressive-disclosure section,
# enforced here as lint failures per this skill's house rules.
BODY_MAX_LINES = 500
BODY_MAX_TOKENS = 5000
# Reference files longer than this need a "## Contents" section so
# partial reads still reveal full scope (per vendor best practices).
REFERENCE_TOC_MIN_LINES = 100
# Codex documents this cap for the whole skills list; reported as a
# fleet warning since it is platform-specific.
CODEX_SKILLS_LIST_BUDGET_CHARS = 8000
# Rough prose heuristic; good enough for budget comparisons.
CHARS_PER_TOKEN = 4

EXIT_CODES_HELP = """\
exit codes:
  0  no violations
  1  one or more violations found
  2  usage error (bad path, no skills found)

examples:
  python3 skill_budget.py path/to/my-skill
  python3 skill_budget.py ~/.agents/skills     # fleet report
"""


def est_tokens(chars: int) -> int:
    return max(1, round(chars / CHARS_PER_TOKEN))


def check_spec_limits(skill_dir: Path, name: str, description: str):
    """Return (violations, warnings) for name/description rules."""
    violations = []
    warnings = []
    if not name:
        violations.append("missing 'name' in frontmatter")
    else:
        if len(name) > SPEC_NAME_MAX_CHARS:
            violations.append(
                f"name is {len(name)} chars (spec max {SPEC_NAME_MAX_CHARS})"
            )
        if not SPEC_NAME_PATTERN.match(name):
            violations.append(
                "name must be lowercase [a-z0-9-] with no leading, "
                "trailing, or consecutive hyphens"
            )
        if name != skill_dir.name:
            violations.append(
                f"name '{name}' does not match directory '{skill_dir.name}'"
            )
        for word in RESERVED_NAME_WORDS:
            if word in name:
                warnings.append(
                    f"name contains reserved word '{word}' "
                    f"(rejected by Anthropic's platform validator)"
                )
    if not description:
        violations.append("missing 'description' in frontmatter")
    else:
        if len(description) > SPEC_DESCRIPTION_MAX_CHARS:
            violations.append(
                f"description is {len(description)} chars "
                f"(spec max {SPEC_DESCRIPTION_MAX_CHARS})"
            )
        if "<" in description or ">" in description:
            violations.append("description contains angle brackets")
    return violations, warnings


def check_reference_tocs(skill_dir: Path) -> list:
    """Long reference files need a Contents section up top."""
    violations: list[str] = []
    ref_dir = skill_dir / "references"
    if not ref_dir.is_dir():
        return violations
    for ref in sorted(ref_dir.glob("*.md")):
        lines = ref.read_text(encoding="utf-8-sig", errors="replace")
        line_list = lines.splitlines()
        if len(line_list) <= REFERENCE_TOC_MIN_LINES:
            continue
        if not any(ln.strip().startswith("## Contents") for ln in line_list):
            violations.append(
                f"references/{ref.name} is {len(line_list)} lines "
                f"(over {REFERENCE_TOC_MIN_LINES}) with no "
                f"'## Contents' section"
            )
    return violations


def report_skill(skill_dir: Path):
    """Print a budget report for one skill.

    Returns (violation_count, trigger_chars) for fleet aggregation.
    """
    skill_md = skill_dir / "SKILL.md"
    # utf-8-sig transparently strips a BOM (common on Windows).
    text = skill_md.read_text(encoding="utf-8-sig", errors="replace")
    fields, violations, body_start = parse_frontmatter(text)
    warnings = []

    name = fields.get("name", "")
    description = fields.get("description", "")
    if body_start > 0:
        spec_violations, warnings = check_spec_limits(skill_dir, name, description)
        violations += spec_violations
    violations += check_reference_tocs(skill_dir)

    # splitlines() so a newline-terminated 500-line body counts as 500.
    body_lines = text.splitlines()[body_start:]
    body_chars = sum(len(ln) + 1 for ln in body_lines)
    trigger_chars = len(name) + len(description)

    if len(body_lines) > BODY_MAX_LINES:
        violations.append(f"body is {len(body_lines)} lines (limit {BODY_MAX_LINES})")
    if est_tokens(body_chars) > BODY_MAX_TOKENS:
        violations.append(
            f"body is ~{est_tokens(body_chars)} tokens (limit {BODY_MAX_TOKENS})"
        )

    print(f"{skill_dir.name}")
    print(
        f"  trigger cost: {trigger_chars} chars "
        f"(~{est_tokens(trigger_chars)} tokens) -- paid every session"
    )
    print(
        f"  invoke cost:  {len(body_lines)} body lines "
        f"(~{est_tokens(body_chars)} tokens) -- paid on trigger"
    )
    ref_dir = skill_dir / "references"
    if ref_dir.is_dir():
        refs = sorted(ref_dir.glob("*.md"))
        # st_size approximates chars well enough for ASCII-first prose.
        ref_chars = sum(r.stat().st_size for r in refs)
        print(
            f"  on demand:    {len(refs)} reference files "
            f"(~{est_tokens(ref_chars)} tokens) -- paid when opened"
        )
    for w in warnings:
        print(f"  warning: {w}", file=sys.stderr)
    for v in violations:
        print(f"  VIOLATION: {v}")
    return len(violations), trigger_chars


def collect_skill_dirs(paths):
    """Expand args into skill dirs; a dir without SKILL.md is treated
    as a skills root and its children with SKILL.md are used.

    Raises ValueError on a path that is not a directory or a skills
    root with no skill children.
    """
    dirs = []
    for arg in paths:
        # resolve() so "." still yields a real directory name for the
        # name-matches-directory check.
        path = Path(arg).resolve()
        if not path.is_dir():
            raise ValueError(f"not a directory: {arg}")
        if (path / "SKILL.md").is_file():
            dirs.append(path)
            continue
        children = sorted(c for c in path.iterdir() if (c / "SKILL.md").is_file())
        if not children:
            raise ValueError(f"{arg} has no SKILL.md and no child skill directories")
        dirs.extend(children)
    return dirs


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Report what each Agent Skill costs in context "
        "(trigger cost paid every session vs invoke cost paid on "
        "trigger) and lint it against the Agent Skills spec limits "
        "and this skill's house rules (single-line frontmatter, "
        "body size, reference ToCs).",
        epilog=EXIT_CODES_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="skill directory (contains SKILL.md), or a skills root "
        "whose children are skill directories (adds fleet totals)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        skill_dirs = collect_skill_dirs(args.paths)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    total_violations = 0
    total_trigger_chars = 0
    for skill_dir in skill_dirs:
        violations, trigger_chars = report_skill(skill_dir)
        total_violations += violations
        total_trigger_chars += trigger_chars

    if len(skill_dirs) > 1:
        print(
            f"fleet: {len(skill_dirs)} skills, standing trigger cost "
            f"{total_trigger_chars} chars "
            f"(~{est_tokens(total_trigger_chars)} tokens per session)"
        )
        if total_trigger_chars > CODEX_SKILLS_LIST_BUDGET_CHARS:
            print(
                f"warning: fleet trigger cost exceeds Codex's "
                f"documented skills-list budget "
                f"({CODEX_SKILLS_LIST_BUDGET_CHARS} chars); skills "
                f"beyond the cap are silently dropped there",
                file=sys.stderr,
            )
    if total_violations:
        print(f"{total_violations} violation(s) found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
