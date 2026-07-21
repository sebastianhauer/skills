"""Unit and in-process CLI tests for trigger_eval.py.

All external seams are injected (``root=``/``which=``), so nothing here
spawns an agent or touches the real eval-projects root.
"""

from __future__ import annotations

import json
import os

import pytest


def _te(load_script):
    return load_script("skill-authoring", "trigger_eval")


# --- matchers ------------------------------------------------------


def test_tool_use_mentions_skill_exact(load_script):
    te = _te(load_script)
    assert te._tool_use_mentions("pdf", "Skill", {"skill": "pdf"})
    assert not te._tool_use_mentions("pdf", "Skill", {"skill": "other"})


def test_tool_use_mentions_read_field_scoped(load_script):
    te = _te(load_script)
    # A read of report.pdf must NOT count as consulting the "pdf" skill.
    assert not te._tool_use_mentions("pdf", "Read", {"file_path": "report.pdf"})
    assert te._tool_use_mentions(
        "pdf", "Read", {"file_path": "/x/.claude/skills/pdf/SKILL.md"}
    )


def test_tool_use_mentions_windows_path(load_script):
    te = _te(load_script)
    assert te._tool_use_mentions(
        "pdf", "Read", {"file_path": "C:\\proj\\skills\\pdf\\SKILL.md"}
    )


def test_tool_use_mentions_other_tool(load_script):
    te = _te(load_script)
    assert not te._tool_use_mentions("pdf", "Bash", {"command": "ls"})


def _stream(se_type, **payload):
    return {"type": "stream_event", "event": {"type": se_type, **payload}}


def test_claude_match_event_stream_sequence(load_script):
    te = _te(load_script)
    state: dict = {}
    start = _stream(
        "content_block_start",
        content_block={"type": "tool_use", "name": "Skill"},
    )
    delta = _stream(
        "content_block_delta",
        delta={"type": "input_json_delta", "partial_json": '{"skill": "myskill"}'},
    )
    stop = _stream("content_block_stop")
    assert te._claude_match_event(start, "myskill", state) is None
    assert te._claude_match_event(delta, "myskill", state) is None
    assert te._claude_match_event(stop, "myskill", state) is True


def test_claude_match_event_result_is_false(load_script):
    te = _te(load_script)
    assert te._claude_match_event({"type": "result"}, "myskill", {}) is False


def test_claude_match_event_unrelated_is_none(load_script):
    te = _te(load_script)
    event = _stream("content_block_start", content_block={"type": "text"})
    assert te._claude_match_event(event, "myskill", {}) is None


def test_claude_match_event_assistant_tool_use(load_script):
    te = _te(load_script)
    event = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Skill", "input": {"skill": "myskill"}}
            ]
        },
    }
    assert te._claude_match_event(event, "myskill", {}) is True


def test_codex_match_event(load_script):
    te = _te(load_script)
    started = {
        "type": "item.started",
        "item": {
            "type": "command_execution",
            "command": "cat .agents/skills/myskill/SKILL.md",
        },
    }
    assert te._codex_match_event(started, "myskill", {}) is True
    assert te._codex_match_event({"type": "turn.completed"}, "myskill", {}) is False
    assert te._codex_match_event({"type": "item.started"}, "myskill", {}) is None


# --- command builders ----------------------------------------------


def test_claude_cmd(load_script):
    te = _te(load_script)
    cmd = te._claude_cmd("claude", "q", "/proj", None)
    assert cmd[:3] == ["claude", "-p", "q"]
    assert "--model" not in cmd
    with_model = te._claude_cmd("claude", "q", "/proj", "sonnet")
    assert with_model[-2:] == ["--model", "sonnet"]


def test_codex_cmd(load_script):
    te = _te(load_script)
    cmd = te._codex_cmd("codex", "q", "/proj", None)
    assert cmd[:2] == ["codex", "exec"]
    assert cmd[-1] == "q"
    assert "-m" not in cmd
    assert "-m" in te._codex_cmd("codex", "q", "/proj", "gpt")


# --- summarize_eval ------------------------------------------------


def _summary(te, triggers, should_trigger, threshold=0.5):
    return te.summarize_eval(
        {"q": triggers},
        {"q": {"query": "q", "should_trigger": should_trigger}},
        threshold,
        "myskill",
        "desc",
    )


def test_summarize_should_trigger_above_threshold(load_script):
    te = _te(load_script)
    out = _summary(te, [True, True], should_trigger=True)
    assert out["results"][0]["pass"] is True
    assert out["summary"] == {"total": 1, "passed": 1, "failed": 0}


def test_summarize_should_trigger_below_threshold(load_script):
    te = _te(load_script)
    out = _summary(te, [False, False], should_trigger=True)
    assert out["results"][0]["pass"] is False
    assert out["summary"]["failed"] == 1


def test_summarize_at_threshold(load_script):
    te = _te(load_script)
    # rate exactly 0.5 -- passes a should_trigger query, fails a
    # should-not-trigger one.
    assert _summary(te, [True, False], should_trigger=True)["results"][0]["pass"]
    assert not _summary(te, [True, False], should_trigger=False)["results"][0]["pass"]


def test_summarize_should_not_trigger_below_threshold(load_script):
    te = _te(load_script)
    out = _summary(te, [False, False], should_trigger=False)
    assert out["results"][0]["pass"] is True


def test_summarize_counts(load_script):
    te = _te(load_script)
    result = _summary(te, [True, False, True], should_trigger=True)["results"][0]
    assert result["triggers"] == 2
    assert result["runs"] == 3


# --- injected seams ------------------------------------------------


def test_create_eval_project_valid(load_script, tmp_path):
    te = _te(load_script)
    project = te.create_eval_project("myskill", "does a thing", "claude", root=tmp_path)
    assert project.parent == tmp_path
    assert any(project.rglob("SKILL.md"))


def test_create_eval_project_invalid_name(load_script, tmp_path):
    te = _te(load_script)
    with pytest.raises(ValueError):
        te.create_eval_project("Bad Name", "d", "claude", root=tmp_path)


def test_create_eval_project_traversal_name(load_script, tmp_path):
    te = _te(load_script)
    with pytest.raises(ValueError):
        te.create_eval_project("../evil", "d", "claude", root=tmp_path)


def test_sweep_stale_eval_projects(load_script, tmp_path):
    te = _te(load_script)
    old = tmp_path / "old"
    fresh = tmp_path / "fresh"
    old.mkdir()
    fresh.mkdir()
    aged = os.stat(old).st_mtime - 100 * 3600
    os.utime(old, (aged, aged))
    te._sweep_stale_eval_projects(12.0, root=tmp_path)
    assert not old.exists()
    assert fresh.exists()


def test_resolve_cli_found(load_script):
    te = _te(load_script)
    assert te.resolve_cli("claude", which=lambda _: "/x/claude") == "/x/claude"


def test_resolve_cli_missing(load_script):
    te = _te(load_script)
    with pytest.raises(RuntimeError):
        te.resolve_cli("claude", which=lambda _: None)


# --- CLI paths that short-circuit before any agent spawn -----------


def _eval_set(tmp_path):
    path = tmp_path / "evals.json"
    path.write_text(
        json.dumps([{"query": "do x", "should_trigger": True}]), encoding="utf-8"
    )
    return path


def test_main_missing_eval_set(load_script, tmp_path):
    te = _te(load_script)
    argv = ["--eval-set", str(tmp_path / "nope.json"), "--skill-path", str(tmp_path)]
    assert te.main(argv) == 2


def test_main_bad_json(load_script, tmp_path):
    te = _te(load_script)
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert te.main(["--eval-set", str(bad), "--skill-path", str(tmp_path)]) == 2


def test_main_no_skill_md(load_script, tmp_path):
    te = _te(load_script)
    evals = _eval_set(tmp_path)
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    assert te.main(["--eval-set", str(evals), "--skill-path", str(skill_dir)]) == 2


def test_main_no_description(load_script, tmp_path):
    te = _te(load_script)
    evals = _eval_set(tmp_path)
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: myskill\n---\n", encoding="utf-8")
    assert te.main(["--eval-set", str(evals), "--skill-path", str(skill_dir)]) == 2
