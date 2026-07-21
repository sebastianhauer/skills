"""Agent Skills spec constants (agentskills.io/specification)."""

import re

SPEC_NAME_MAX_CHARS = 64
SPEC_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SPEC_DESCRIPTION_MAX_CHARS = 1024
# Anthropic's platform validator rejects these inside names.
RESERVED_NAME_WORDS = ("anthropic", "claude")
