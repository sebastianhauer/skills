"""In-process CLI and end-to-end tests for init_skill.py."""

from __future__ import annotations


def test_valid_create(load_script, tmp_path, capsys):
    main = load_script("skill-authoring", "init_skill").main
    assert main(["my-skill", "--path", str(tmp_path)]) == 0
    skill_md = (tmp_path / "my-skill" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: my-skill" in skill_md
    assert "# My Skill" in skill_md
    assert "Next steps" in capsys.readouterr().out


def test_resources_create_exactly_those_dirs(load_script, tmp_path):
    main = load_script("skill-authoring", "init_skill").main
    assert (
        main(["my-skill", "--path", str(tmp_path), "--resources", "scripts,references"])
        == 0
    )
    skill_dir = tmp_path / "my-skill"
    assert (skill_dir / "scripts").is_dir()
    assert (skill_dir / "references").is_dir()
    assert not (skill_dir / "assets").exists()


def test_invalid_name(load_script, tmp_path):
    main = load_script("skill-authoring", "init_skill").main
    assert main(["Bad_Name", "--path", str(tmp_path)]) == 2


def test_unknown_resource(load_script, tmp_path):
    main = load_script("skill-authoring", "init_skill").main
    assert main(["my-skill", "--path", str(tmp_path), "--resources", "bogus"]) == 2


def test_existing_target(load_script, tmp_path):
    main = load_script("skill-authoring", "init_skill").main
    assert main(["my-skill", "--path", str(tmp_path)]) == 0
    assert main(["my-skill", "--path", str(tmp_path)]) == 2


def test_reserved_word_warns_but_succeeds(load_script, tmp_path, capsys):
    main = load_script("skill-authoring", "init_skill").main
    assert main(["claude-helper", "--path", str(tmp_path)]) == 0
    assert "reserved word" in capsys.readouterr().err


def test_scaffold_lints_clean(load_script, tmp_path):
    init_main = load_script("skill-authoring", "init_skill").main
    budget_main = load_script("skill-authoring", "skill_budget").main
    assert init_main(["fresh-skill", "--path", str(tmp_path)]) == 0
    assert budget_main([str(tmp_path / "fresh-skill")]) == 0


def test_cli_end_to_end(run_script, tmp_path):
    result = run_script(
        "skill-authoring", "init_skill", "smoke-skill", "--path", str(tmp_path)
    )
    assert result.returncode == 0
    assert (tmp_path / "smoke-skill" / "SKILL.md").is_file()
