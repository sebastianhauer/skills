"""SKILL.md frontmatter parsing against the house rules."""

import re

# Block-scalar indicator with optional modifiers/comment: |, >-, >2 ...
BLOCK_INDICATOR = re.compile(r"^[|>][+-]?[0-9]*\s*(#.*)?$")


def is_indented(line: str) -> bool:
    return line[:1] in (" ", "\t")


def _unquote(value: str) -> str:
    """Strip matching quotes and decode their YAML escape forms.

    Double quotes: backslash escapes for the quote and the backslash
    itself. Single quotes: doubled '' means a literal '. Other escape
    sequences pass through verbatim (the house rule keeps values to
    plain text).
    """
    if len(value) >= 2 and value[0] == value[-1]:
        if value[0] == '"':
            return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        if value[0] == "'":
            return value[1:-1].replace("''", "'")
    return value


def parse_frontmatter(text: str):
    """Return (fields, violations, body_start_index).

    Line-based on purpose: this parser accepts exactly the house rule
    (single-line values, one level of nested map) and reports
    everything else as a violation. Multiline values are still
    reconstructed so length checks see the full value. On malformed
    frontmatter, fields is empty and violations carries the error.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, ["SKILL.md does not start with '---' frontmatter"], 0

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, ["frontmatter has no closing '---'"], 0

    fields = {}
    violations = []
    last_key = None
    i = 1
    while i < end:
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if is_indented(line):
            if last_key is not None:
                joined = f"{fields.get(last_key, '')} {stripped}"
                fields[last_key] = joined.strip()
            violations.append(
                f"line {i + 1}: wrapped multiline value in frontmatter; "
                f"values must be a single line"
            )
            i += 1
            continue
        if ":" not in line:
            violations.append(f"line {i + 1}: not a 'key: value' line")
            i += 1
            continue
        key, _, value = line.partition(":")
        key = key.strip().strip("\"'")
        value = value.strip()
        if BLOCK_INDICATOR.match(value):
            parts = []
            i += 1
            while i < end and (is_indented(lines[i]) or not lines[i].strip()):
                parts.append(lines[i].strip())
                i += 1
            fields[key] = " ".join(p for p in parts if p)
            last_key = None
            violations.append(
                f"'{key}' uses a block scalar ({value}); frontmatter "
                f"values must be a single line"
            )
            continue
        if not value:
            # Nested map (e.g. the spec's `metadata`): one level deep,
            # each entry a single-line `key: value` pair.
            i += 1
            saw_entry = False
            while i < end and (is_indented(lines[i]) or not lines[i].strip()):
                nested = lines[i].strip()
                if not nested or nested.startswith("#"):
                    i += 1
                    continue
                saw_entry = True
                nested_value = nested.partition(":")[2].strip()
                if ":" not in nested:
                    violations.append(
                        f"line {i + 1}: nested '{key}' entry is not a "
                        f"single-line 'key: value' pair"
                    )
                elif not nested_value or BLOCK_INDICATOR.match(nested_value):
                    violations.append(
                        f"line {i + 1}: nested '{key}' entry must be a "
                        f"single-line scalar (no deeper nesting or "
                        f"block scalars)"
                    )
                i += 1
            fields[key] = ""
            last_key = None
            if not saw_entry:
                violations.append(f"'{key}' has an empty value")
            continue
        quoted = value[:1] in ('"', "'") and value[-1:] == value[:1]
        if not quoted and ": " in value:
            violations.append(
                f"'{key}' is an unquoted value containing ': ' -- "
                f"invalid YAML plain scalar; rephrase or quote it"
            )
        fields[key] = _unquote(value)
        last_key = key
        i += 1
    return fields, violations, end + 1
