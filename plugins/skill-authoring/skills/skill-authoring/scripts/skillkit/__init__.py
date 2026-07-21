"""Shared library for the skill-authoring scripts.

Importing this package enforces the Python floor (skillkit.runtime)
and re-exports the spec constants and the frontmatter parser so entry
scripts can `from skillkit import ...` without knowing the layout.
"""

from . import runtime  # must come first: fires the version guard
from .frontmatter import BLOCK_INDICATOR, is_indented, parse_frontmatter
from .spec import (
    RESERVED_NAME_WORDS,
    SPEC_DESCRIPTION_MAX_CHARS,
    SPEC_NAME_MAX_CHARS,
    SPEC_NAME_PATTERN,
)

__all__ = [
    "BLOCK_INDICATOR",
    "RESERVED_NAME_WORDS",
    "SPEC_DESCRIPTION_MAX_CHARS",
    "SPEC_NAME_MAX_CHARS",
    "SPEC_NAME_PATTERN",
    "is_indented",
    "parse_frontmatter",
    "runtime",
]
