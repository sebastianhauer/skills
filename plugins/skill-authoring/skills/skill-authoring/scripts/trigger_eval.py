#!/usr/bin/env python3
"""Measure whether a skill's description triggers agent invocation.

Each query runs through a real headless agent session inside an
isolated temp project holding the candidate skill; the backend's
event stream decides "consulted or not". Details are in --help.
Backends are pluggable: one Backend entry in BACKENDS supplies the
CLI name, skills directory, command builder, and event matcher.

Vendored from anthropics/skills skill-creator run_eval.py as fixed
by PR #1298 (Apache-2.0; see LICENSE). Modified: standalone,
Python 3.9 floor, backend registry (Claude Code, Codex), 300s
default timeout, exit 1 when queries fail, spec-validated skill
names, and per-query-run project isolation (upstream shares one
project across workers; parallel agents can mutate it mid-run).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections import deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from queue import Empty, Queue
from typing import Callable, NamedTuple, Optional

# PYTHONSAFEPATH (3.11+) drops the script dir from sys.path; put it
# back so the sibling skillkit package always resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skillkit import (
    SPEC_NAME_MAX_CHARS,
    SPEC_NAME_PATTERN,
    parse_frontmatter,
)

# All eval projects live under this root in the OS temp directory.
EVAL_PROJECTS_ROOT = Path(tempfile.gettempdir()) / "agent-skill-evals"

# Leftover eval projects must be at least this old (hours) before the
# sweep removes them: long enough to survive a paused debugging
# session, short enough not to accumulate cruft.
DEFAULT_STALE_ARTIFACT_HOURS = 12.0

# Wall clock per query, including CLI startup and thinking time.
DEFAULT_TIMEOUT_SECONDS = 300


class Backend(NamedTuple):
    """Everything backend-specific about measuring one agent CLI.

    The event matcher receives each decoded JSON event plus a
    per-query mutable state dict (for protocols that spread one
    signal across several events) and returns True (skill consulted),
    False (terminal event, not consulted), or None (keep watching).

    Framing contract a new backend must satisfy: the CLI streams
    line-delimited JSON on stdout, discovers skills from a SKILL.md
    placed in skills_root inside the working root, and emits some
    terminal event the matcher can map to False (otherwise
    non-triggering runs only end at --timeout).
    """

    binary: str
    # Project-relative directory the backend scans for skills.
    skills_root: Path
    # Home-relative directory of user-level skills (shadow warning).
    user_skills_root: Path
    # Env vars to drop so the CLI runs nested under another agent.
    env_strip: tuple[str, ...]
    build_cmd: Callable[[str, str, str, Optional[str]], list]
    match_event: Callable[[dict, str, dict], Optional[bool]]


# --- Claude Code backend -------------------------------------------

# Bounds conversation length for queries that never trigger, so cost
# and wall-clock time stay capped without cutting off legitimate
# multi-turn runs where the agent explores before invoking the skill.
CLAUDE_MAX_TURNS = 8


def _claude_cmd(cli: str, query: str, project_dir: str, model: Optional[str]) -> list:
    cmd = [
        cli,
        "-p",
        query,
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--max-turns",
        str(CLAUDE_MAX_TURNS),
    ]
    if model:
        cmd.extend(["--model", model])
    return cmd


def _tool_use_mentions(eval_skill_name: str, tool_name: str, tool_input: dict) -> bool:
    """Whether a tool_use block is the agent consulting the skill.

    Field-scoped on purpose: a plain substring test over the
    serialized input produces false positives for short names (a
    skill named "pdf" would count a Read of "report.pdf"). Only an
    exact skill invocation, or a file read inside the skill's own
    directory, is a genuine consult.
    """
    if tool_name == "Skill":
        return (tool_input.get("skill") or "").strip() == eval_skill_name
    if tool_name == "Read":
        # Normalize separators so the match holds on Windows paths.
        path = (tool_input.get("file_path") or "").replace("\\", "/")
        return f"/{eval_skill_name}/" in path
    return False


def _claude_match_event(event: dict, skill_name: str, state: dict) -> Optional[bool]:
    """Claude Code exposes skills via Skill/Read tool_use blocks whose
    input streams across several events; state accumulates it."""
    etype = event.get("type", "")

    if etype == "stream_event":
        se = event.get("event", {})
        se_type = se.get("type", "")

        if se_type == "content_block_start":
            cb = se.get("content_block", {})
            if cb.get("type") == "tool_use":
                if cb.get("name", "") in ("Skill", "Read"):
                    state["pending_tool"] = cb.get("name", "")
                    state["input_json"] = ""
                else:
                    state["pending_tool"] = None

        elif se_type == "content_block_delta" and state.get("pending_tool"):
            delta = se.get("delta", {})
            if delta.get("type") == "input_json_delta":
                # Accumulate only; the input must be parsed whole to
                # field-scope the match.
                state["input_json"] += delta.get("partial_json", "")

        elif se_type == "content_block_stop":
            pending = state.get("pending_tool")
            if pending:
                try:
                    tool_input = (
                        json.loads(state["input_json"])
                        if state.get("input_json")
                        else {}
                    )
                except json.JSONDecodeError:
                    tool_input = {}
                if _tool_use_mentions(skill_name, pending, tool_input):
                    return True
            state["pending_tool"] = None

    elif etype == "assistant":
        for content_item in event.get("message", {}).get("content", []):
            if content_item.get("type") != "tool_use":
                continue
            if _tool_use_mentions(
                skill_name,
                content_item.get("name", ""),
                content_item.get("input", {}),
            ):
                return True

    elif etype == "result":
        return False
    return None


# --- Codex backend -------------------------------------------------


def _codex_cmd(cli: str, query: str, project_dir: str, model: Optional[str]) -> list:
    # Codex has no turn cap; --timeout is the only cost bound, and
    # workspace-write confines any real work to the temp project.
    cmd = [
        cli,
        "exec",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C",
        project_dir,
        "-s",
        "workspace-write",
    ]
    if model:
        cmd.extend(["-m", model])
    cmd.append(query)
    return cmd


def _codex_match_event(event: dict, skill_name: str, state: dict) -> Optional[bool]:
    """Codex has no skill tool; it reads SKILL.md via shell, so a
    command touching the skill's directory is the consult signal."""
    etype = event.get("type", "")
    if etype in ("item.started", "item.completed"):
        item = event.get("item", {})
        if item.get("type") == "command_execution":
            command = (item.get("command") or "").replace("\\", "/")
            if f"skills/{skill_name}/" in command:
                return True
    elif etype in ("turn.completed", "turn.failed"):
        return False
    return None


# --- Registry ------------------------------------------------------

BACKENDS = {
    "claude": Backend(
        binary="claude",
        skills_root=Path(".claude") / "skills",
        user_skills_root=Path(".claude") / "skills",
        # The CLI refuses to nest inside an interactive session of
        # itself; programmatic subprocess use is safe, so drop the
        # guard variable.
        env_strip=("CLAUDECODE",),
        build_cmd=_claude_cmd,
        match_event=_claude_match_event,
    ),
    # Flags and event schema verified against codex-cli 0.144.1.
    "codex": Backend(
        binary="codex",
        skills_root=Path(".agents") / "skills",
        user_skills_root=Path(".agents") / "skills",
        # Codex ignores CLAUDECODE; dropping it keeps the env uniform
        # when evals run nested inside a Claude Code session.
        env_strip=("CLAUDECODE",),
        build_cmd=_codex_cmd,
        match_event=_codex_match_event,
    ),
}
DEFAULT_AGENT = "claude"


def resolve_cli(
    agent: str, which: Callable[[str], Optional[str]] = shutil.which
) -> str:
    """Resolve the backend executable to a full path.

    On Windows, Popen only finds .exe files by bare name; npm installs
    provide .cmd shims that raise FileNotFoundError unless resolved to
    a full path first. shutil.which handles both.
    """
    binary = BACKENDS[agent].binary
    resolved = which(binary)
    if not resolved:
        raise RuntimeError(
            f"Could not find the `{binary}` CLI on PATH. Install it "
            f"or pick another backend via --agent."
        )
    return resolved


def _pump_lines(stream, sink) -> None:
    """Read a binary stream line by line into sink; EOF sends None."""
    try:
        for raw in iter(stream.readline, b""):
            sink(raw)
    finally:
        sink(None)


def run_single_query(
    query: str,
    eval_skill_name: str,
    description: str,
    timeout: int,
    model: Optional[str] = None,
    cli: Optional[str] = None,
    agent: str = DEFAULT_AGENT,
) -> bool:
    """Run one query; return whether the eval skill was triggered.

    Each run gets its own throwaway project: agents may legally
    create or delete files while working a query, so sharing one
    project across parallel workers would let runs contaminate each
    other. Streams the backend CLI's JSON output through the
    backend's event matcher and returns True as soon as it reports a
    consult; other activity is ignored, since agents often explore
    before consulting a skill. Returns False only on a terminal
    event, process exit, or timeout.
    """
    backend = BACKENDS[agent]
    project_dir = create_eval_project(eval_skill_name, description, agent)
    eval_project_dir = str(project_dir)
    cmd = backend.build_cmd(cli or resolve_cli(agent), query, eval_project_dir, model)

    env = {k: v for k, v in os.environ.items() if k not in backend.env_strip}

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # Some CLIs wait on stdin when it looks piped; close it so
        # the run starts immediately.
        stdin=subprocess.DEVNULL,
        cwd=eval_project_dir,
        env=env,
    )

    # select() only works on sockets on Windows, so stream reading
    # goes through reader threads + a queue on every platform.
    stdout_queue: Queue = Queue()
    stderr_tail: deque = deque(maxlen=40)
    threading.Thread(
        target=_pump_lines, args=(process.stdout, stdout_queue.put), daemon=True
    ).start()
    threading.Thread(
        target=_pump_lines,
        args=(
            process.stderr,
            lambda raw: stderr_tail.append(raw) if raw else None,
        ),
        daemon=True,
    ).start()

    def stderr_excerpt() -> str:
        tail = b"".join(stderr_tail).decode("utf-8", errors="replace")
        return tail.strip()[:500]

    deadline = time.time() + timeout
    match_state: dict = {}

    try:
        while True:
            if time.time() > deadline:
                print(
                    f"Warning: query timed out after {timeout}s; counting as "
                    f"not-triggered: {query[:60]}",
                    file=sys.stderr,
                )
                return False

            try:
                raw = stdout_queue.get(timeout=0.5)
            except Empty:
                continue
            if raw is None:  # EOF: process finished, output drained
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    return False
                if process.returncode != 0:
                    print(
                        f"Warning: {agent} CLI exited with code "
                        f"{process.returncode} for query: {query[:60]}\n"
                        f"  stderr: {stderr_excerpt()}",
                        file=sys.stderr,
                    )
                return False

            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            verdict = backend.match_event(event, eval_skill_name, match_state)
            if verdict is not None:
                return verdict
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        # A failure between project creation and this try block can
        # leak one directory; the stale sweep collects those.
        shutil.rmtree(project_dir, ignore_errors=True)


def _sweep_stale_eval_projects(
    stale_hours: float, root: Path = EVAL_PROJECTS_ROOT
) -> None:
    """Remove eval projects left behind by crashed or killed runs."""
    if not root.is_dir():
        return
    cutoff = time.time() - stale_hours * 3600
    for entry in root.iterdir():
        if entry.is_dir():
            try:
                if entry.stat().st_mtime < cutoff:
                    shutil.rmtree(entry, ignore_errors=True)
            except OSError:
                pass


def _warn_if_shadowed(skill_name: str, agent: str) -> None:
    """Warn when a same-named user-level skill also loads.

    User-level skills load in every session; an installed copy
    carries its own description, so triggers it attracts are decided
    by the wrong description and skew measurement.
    """
    installed = Path.home() / BACKENDS[agent].user_skills_root / skill_name
    if installed.is_dir():
        print(
            f"Warning: user-level skill at {installed} shares the eval "
            f"skill's name and also loads during evals; move it aside "
            f"while measuring, then restore it.",
            file=sys.stderr,
        )


def create_eval_project(
    skill_name: str,
    skill_description: str,
    agent: str,
    root: Path = EVAL_PROJECTS_ROOT,
) -> Path:
    """Create an isolated throwaway project with the candidate skill.

    Rejects names outside the spec pattern: path joins with an
    absolute or traversal-containing name would escape the root, and
    the cleanup rmtree must never point at a real directory.
    """
    if len(skill_name) > SPEC_NAME_MAX_CHARS or not SPEC_NAME_PATTERN.match(skill_name):
        raise ValueError(
            f"invalid skill name {skill_name!r}: must match the spec "
            f"pattern (lowercase [a-z0-9-])"
        )

    project_dir = root / f"{skill_name}-{uuid.uuid4().hex}"
    skill_dir = project_dir / BACKENDS[agent].skills_root / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    # Block scalar on purpose: the candidate description is arbitrary
    # text (quotes, colons); this artifact is consumed only by the
    # eval session's YAML parser, never by naive tooling.
    indented_desc = "\n  ".join(skill_description.split("\n"))
    skill_content = (
        f"---\n"
        f"name: {skill_name}\n"
        f"description: |\n"
        f"  {indented_desc}\n"
        f"---\n\n"
        f"# {skill_name}\n\n"
        f"This skill handles: {skill_description}\n\n"
        f"(Temporary trigger-eval artifact; safe to delete.)\n"
    )
    (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
    return project_dir


def run_eval(
    eval_set: list,
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: Optional[str] = None,
    stale_artifact_hours: float = DEFAULT_STALE_ARTIFACT_HOURS,
    agent: str = DEFAULT_AGENT,
) -> dict:
    """Run the full eval set and return results.

    Every query run builds and removes its own throwaway project;
    see run_single_query.
    """
    cli = resolve_cli(agent)
    _sweep_stale_eval_projects(stale_artifact_hours)
    _warn_if_shadowed(skill_name, agent)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                # Workers get the backend NAME and re-resolve it
                # from BACKENDS after import: Backend holds
                # functions, which do not pickle across processes.
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    model,
                    cli,
                    agent,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict = {}
        query_items: dict = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(
                    f"Warning: query failed ({type(e).__name__}: {e}); "
                    f"counting as not-triggered: {query[:60]}",
                    file=sys.stderr,
                )
                query_triggers[query].append(False)

    return summarize_eval(
        query_triggers, query_items, trigger_threshold, skill_name, description
    )


def summarize_eval(
    query_triggers: dict,
    query_items: dict,
    trigger_threshold: float,
    skill_name: str,
    description: str,
) -> dict:
    """Turn per-query trigger runs into pass/fail results and a summary.

    A query with should_trigger passes when its trigger rate reaches
    the threshold; a query without it passes when the rate stays below.
    """
    results = []
    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append(
            {
                "query": query,
                "should_trigger": should_trigger,
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "runs": len(triggers),
                "pass": did_pass,
            }
        )

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Measure whether a skill's description makes an "
        "agent invoke the skill: runs every eval query through a real "
        "headless agent session and reports per-query trigger rates "
        "as JSON on stdout. Backends: " + ", ".join(sorted(BACKENDS)) + ".",
        epilog="""\
cost: every query run is a real agent session; 20 queries x 3 runs =
60 sessions. Use --runs-per-query 1 for a cheap first pass. Backends
without a turn cap (codex) work on non-triggering queries until done
or --timeout; writes stay confined to the throwaway project.

output: JSON object with per-query results ("query",
"should_trigger", "trigger_rate", "pass") and a "summary" block
(total/passed/failed).

exit codes:
  0  all queries passed
  1  one or more queries failed
  2  usage error (bad path, missing description)

examples:
  python3 trigger_eval.py --eval-set evals.json \\
    --skill-path path/to/my-skill --model claude-sonnet-5 --verbose
  python3 trigger_eval.py --eval-set evals.json \\
    --skill-path path/to/my-skill --agent codex --verbose
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument(
        "--description", default=None, help="Override description to test"
    )
    parser.add_argument(
        "--num-workers", type=int, default=10, help="Number of parallel workers"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout per query in seconds (wall clock incl. CLI startup "
        "and thinking; slower models need more)",
    )
    parser.add_argument(
        "--runs-per-query", type=int, default=3, help="Number of runs per query"
    )
    parser.add_argument(
        "--trigger-threshold",
        type=float,
        default=0.5,
        help="Trigger rate threshold",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model for the agent CLI (default: its configured model)",
    )
    parser.add_argument(
        "--agent",
        choices=sorted(BACKENDS),
        default=DEFAULT_AGENT,
        help=f"Agent CLI backend to measure with (default: {DEFAULT_AGENT})",
    )
    parser.add_argument(
        "--stale-artifact-hours",
        type=float,
        default=DEFAULT_STALE_ARTIFACT_HOURS,
        help="Age (hours) before leftover eval projects are swept",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print progress to stderr"
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        eval_set = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
    except OSError as e:
        print(f"Error: cannot read --eval-set: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"Error: --eval-set is not valid JSON: {e}", file=sys.stderr)
        return 2
    skill_path = Path(args.skill_path)
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        return 2

    fields, _, _ = parse_frontmatter(
        skill_md.read_text(encoding="utf-8-sig", errors="replace")
    )
    name = fields.get("name", "") or skill_path.resolve().name
    if len(name) > SPEC_NAME_MAX_CHARS or not SPEC_NAME_PATTERN.match(name):
        print(
            f"Error: skill name {name!r} does not match the spec "
            f"pattern (lowercase [a-z0-9-], max {SPEC_NAME_MAX_CHARS})",
            file=sys.stderr,
        )
        return 2
    description = args.description or fields.get("description", "")
    if not description:
        print(
            "Error: no description in frontmatter or --description",
            file=sys.stderr,
        )
        return 2

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
        stale_artifact_hours=args.stale_artifact_hours,
        agent=args.agent,
    )

    if args.verbose:
        summary = output["summary"]
        print(
            f"Results: {summary['passed']}/{summary['total']} passed",
            file=sys.stderr,
        )
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(
                f"  [{status}] rate={rate_str} "
                f"expected={r['should_trigger']}: {r['query'][:70]}",
                file=sys.stderr,
            )

    print(json.dumps(output, indent=2))
    if output["summary"]["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
