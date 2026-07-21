"""Pytest configuration for the skills repo.

Tests live at the repo root (``tests/``), deliberately OUTSIDE
``plugins/`` so they are never copied when a plugin or skill is
installed. This helper loads a script module directly from a skill's
``scripts/`` directory by path, avoiding any need to package the
scripts or put them on ``sys.path`` permanently.

Each skill ships as a self-contained plugin, so its scripts live at
``plugins/<skill>/skills/<skill>/scripts/`` -- the plugin directory
name, the inner skill directory name, and the ``skill`` argument to
these helpers are all identical.
"""

from __future__ import annotations

import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent
PLUGINS_DIR = REPO_ROOT / "plugins"


def _scripts_dir(skill: str) -> Path:
    """Return ``plugins/<skill>/skills/<skill>/scripts`` for a skill."""
    return PLUGINS_DIR / skill / "skills" / skill / "scripts"


def _load_script(skill: str, module: str) -> ModuleType:
    """Import a skill's ``scripts/<module>.py`` as a module.

    In-process import for direct unit testing of functions. For scripts
    that live inside a package (relative imports) or whose CLI you want
    to exercise end-to-end, use the ``run_script`` fixture instead.
    """
    path = _scripts_dir(skill) / f"{module}.py"
    spec = importlib.util.spec_from_file_location(f"{skill}.{module}", path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load script: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_package(skill: str, dotted: str) -> ModuleType:
    """Import a package submodule from a skill's ``scripts`` directory.

    Unlike ``_load_script``, this puts the scripts directory on
    ``sys.path`` (once) so intra-package relative imports resolve, then
    imports by dotted name -- e.g.
    ``_load_package("skill-authoring", "skillkit.frontmatter")``.
    """
    scripts_dir = str(_scripts_dir(skill))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return importlib.import_module(dotted)


def _run_script(
    skill: str, module: str, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run a skill's ``scripts/<module>.py`` as a subprocess.

    Uses the venv interpreter (``sys.executable`` -- the vanilla stock
    3.9), so this exercises the real ``__main__``/argparse path on the
    interpreter we support, not just an in-process function call.
    Returns the CompletedProcess (stdout/stderr captured as text).
    """
    path = _scripts_dir(skill) / f"{module}.py"
    return subprocess.run(
        [sys.executable, str(path), *args],
        capture_output=True,
        text=True,
    )


@pytest.fixture
def load_script():
    """Return the in-process script loader (see :func:`_load_script`)."""
    return _load_script


@pytest.fixture
def load_package():
    """Return the package-submodule loader (see :func:`_load_package`)."""
    return _load_package


@pytest.fixture
def run_script():
    """Return the subprocess script runner (see :func:`_run_script`)."""
    return _run_script
