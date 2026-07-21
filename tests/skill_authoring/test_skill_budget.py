"""Unit and in-process CLI tests for skill_budget.py."""

from __future__ import annotations

from pathlib import Path

import pytest


def _write_skill(parent: Path, name: str, description: str) -> Path:
    skill_dir = parent / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nBody.\n",
        encoding="utf-8",
    )
    return skill_dir


def test_est_tokens_boundaries(load_script):
    est_tokens = load_script("skill-authoring", "skill_budget").est_tokens
    assert est_tokens(0) == 1
    assert est_tokens(4) == 1
    assert est_tokens(400) == 100


def test_check_spec_limits_missing_name_and_description(load_script):
    check = load_script("skill-authoring", "skill_budget").check_spec_limits
    violations, warnings = check(Path("some-skill"), "", "")
    assert any("missing 'name'" in v for v in violations)
    assert any("missing 'description'" in v for v in violations)


def test_check_spec_limits_name_mismatch(load_script):
    check = load_script("skill-authoring", "skill_budget").check_spec_limits
    violations, _ = check(Path("foo"), "bar", "desc")
    assert any("does not match directory" in v for v in violations)


def test_check_spec_limits_angle_brackets(load_script):
    check = load_script("skill-authoring", "skill_budget").check_spec_limits
    violations, _ = check(Path("x"), "x", "has <b> tags")
    assert any("angle brackets" in v for v in violations)


def test_check_spec_limits_reserved_word_is_warning_not_violation(load_script):
    check = load_script("skill-authoring", "skill_budget").check_spec_limits
    violations, warnings = check(Path("claude-thing"), "claude-thing", "desc")
    assert any("reserved word" in w for w in warnings)
    assert not any("reserved word" in v for v in violations)


def test_check_reference_tocs(load_script, tmp_path):
    check = load_script("skill-authoring", "skill_budget").check_reference_tocs
    ref_dir = tmp_path / "references"
    ref_dir.mkdir()
    long_no_toc = "\n".join(f"line {i}" for i in range(150)) + "\n"
    (ref_dir / "long.md").write_text(long_no_toc, encoding="utf-8")
    (ref_dir / "short.md").write_text("line\n", encoding="utf-8")
    (ref_dir / "long_toc.md").write_text(
        "## Contents\n" + long_no_toc, encoding="utf-8"
    )
    violations = check(tmp_path)
    assert any("long.md" in v for v in violations)
    assert not any("short.md" in v for v in violations)
    assert not any("long_toc.md" in v for v in violations)


def test_collect_skill_dirs_returns_skill_and_root(load_script, tmp_path):
    collect = load_script("skill-authoring", "skill_budget").collect_skill_dirs
    single = _write_skill(tmp_path, "solo", "Does a thing. Use when X.")
    assert collect([str(single)]) == [single.resolve()]

    root = tmp_path / "fleet"
    root.mkdir()
    a = _write_skill(root, "alpha", "Alpha. Use when A.")
    b = _write_skill(root, "beta", "Beta. Use when B.")
    assert collect([str(root)]) == [a.resolve(), b.resolve()]


def test_collect_skill_dirs_not_a_directory(load_script, tmp_path):
    collect = load_script("skill-authoring", "skill_budget").collect_skill_dirs
    with pytest.raises(ValueError):
        collect([str(tmp_path / "missing")])


def test_collect_skill_dirs_empty_root(load_script, tmp_path):
    collect = load_script("skill-authoring", "skill_budget").collect_skill_dirs
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError):
        collect([str(empty)])


def test_main_clean_skill(load_script, tmp_path, capsys):
    main = load_script("skill-authoring", "skill_budget").main
    skill = _write_skill(tmp_path, "clean-skill", "Does a thing. Use when X.")
    assert main([str(skill)]) == 0
    assert "VIOLATION" not in capsys.readouterr().out


def test_main_reports_violation(load_script, tmp_path, capsys):
    main = load_script("skill-authoring", "skill_budget").main
    long_name = "a" * 65
    skill = _write_skill(tmp_path, long_name, "Does a thing. Use when X.")
    assert main([str(skill)]) == 1
    assert "VIOLATION" in capsys.readouterr().out


def test_main_bad_path(load_script, tmp_path):
    main = load_script("skill-authoring", "skill_budget").main
    assert main([str(tmp_path / "nope")]) == 2
