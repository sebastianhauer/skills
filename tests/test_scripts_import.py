"""Import smoke test for every shipped skill script.

Auto-discovers each ``plugins/*/skills/*/scripts/**/*.py`` and imports
it in a fresh Python 3.9 subprocess, so a newly added script that fails to
import (a 3.11-only stdlib call, a broken relative import) is caught
even when it has no dedicated unit test. Syntax is covered separately
by the py_compile gate; this covers import-time execution.

Fresh subprocesses give full isolation: no shared sys.modules/sys.path
between scripts, and standalone scripts, packages, and package
submodules all import by their real dotted name.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"

# Imports the module named argv[2] with the scripts dir argv[1] on the
# path -- run in a subprocess so each import is fully isolated.
_IMPORT_SNIPPET = (
    "import importlib, sys; sys.path.insert(0, sys.argv[1]); "
    "importlib.import_module(sys.argv[2])"
)


def _scripts_dir(script: Path) -> Path:
    for parent in script.parents:
        if parent.name == "scripts":
            return parent
    raise AssertionError(f"no scripts/ ancestor for {script}")


def _module_name(script: Path, scripts_dir: Path) -> str:
    parts = list(script.relative_to(scripts_dir).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


_SCRIPTS = sorted(PLUGINS_DIR.glob("*/skills/*/scripts/**/*.py"))
_IDS = [str(p.relative_to(PLUGINS_DIR)) for p in _SCRIPTS]


@pytest.mark.parametrize("script", _SCRIPTS, ids=_IDS)
def test_script_imports(script: Path) -> None:
    scripts_dir = _scripts_dir(script)
    module = _module_name(script, scripts_dir)
    result = subprocess.run(
        [sys.executable, "-c", _IMPORT_SNIPPET, str(scripts_dir), module],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"importing {module} failed:\n{result.stderr}"
