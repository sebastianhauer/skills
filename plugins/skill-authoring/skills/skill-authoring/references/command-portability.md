# Command Portability

Portable command guidance for skill scripts and examples. Always prefer the
simplest, most portable approach that gets the job done.

## Contents

- Scope (platform target, local vs remote)
- Decision hierarchy
- Script linting
- macOS vs Linux defaults
- Key BSD vs GNU differences (awk, sed, grep, date, stat, xargs, find)
- Optional tool checks
- Shell portability tips

## Scope

These rules apply to commands and scripts that run **locally** on a developer's
machine. The default portability target is macOS, Linux, AND Windows; a skill
may narrow that, but only by stating the exclusion explicitly in its body (e.g.
"Linux-only: relies on systemd"). Commands executed on **remote Linux hosts**
(e.g., over SSH or another remote transport) can assume a GNU userland and do
not need BSD or Windows compatibility.

## Decision hierarchy

When choosing how to implement a command or pipeline:

1. **Python (stdlib)** -- preferred for scripts; the only option that runs
   unmodified on macOS, Linux, and Windows. Use `pathlib`, explicit UTF-8
   encoding, and avoid shelling out.
1. **POSIX shell + common Unix tools** -- for doc examples aimed at Unix shells,
   and for scripts in skills that explicitly scope Windows out: `sh`, `grep`,
   `awk`, `sed`, `cut`, `sort`, `xargs`, `tr`
1. **Optional tools with availability check** -- `jq`, `yq`, `rg` are fine but
   gate on `command -v` first
1. **PowerShell or batch** -- only for inherently Windows-specific tasks; prefer
   PowerShell (it has a linter) over batch

## Script linting

Lint every script a skill bundles, when tooling is available; note in the skill
review when none ran.

| Language   | Linter                                  |
| ---------- | --------------------------------------- |
| Python     | `python3 -m py_compile` (always works); |
|            | `ruff` or `pyflakes` when installed     |
| Shell      | `shellcheck` when installed;            |
|            | `sh -n` / `bash -n` always work         |
| PowerShell | PSScriptAnalyzer                        |
| Batch      | no standard linter; prefer PowerShell   |

Gate optional linters on `command -v` like any other optional tool.

## macOS vs Linux defaults

| Tool    | macOS            | Linux              |
| ------- | ---------------- | ------------------ |
| `awk`   | BWK awk (nawk)   | gawk or mawk       |
| `sed`   | BSD sed          | GNU sed            |
| `grep`  | BSD grep         | GNU grep           |
| `date`  | BSD date         | GNU coreutils date |
| `stat`  | BSD stat         | GNU stat           |
| `xargs` | BSD xargs        | GNU xargs          |
| `tar`   | BSD tar (bsdtar) | GNU tar            |
| `find`  | BSD find         | GNU find           |

## Key BSD vs GNU differences

### `awk`

macOS ships BWK awk (Brian Kernighan's "one true awk"). Stick to POSIX awk
features. Avoid gawk extensions:

- `gensub()` -- gawk only; use `sub()`/`gsub()` instead
- `BEGINFILE` / `ENDFILE` -- gawk only
- `@include` -- gawk only
- `length(array)` -- gawk only; iterate and count
- `--csv` flag -- gawk 5.3+ only
- `-i inplace` -- gawk only

When unsure, check `man awk` on macOS or test with `/usr/bin/awk` (not a
Homebrew-installed gawk).

### `sed`

The `-i` (in-place edit) flag differs:

```bash
# BSD sed (macOS) -- requires backup extension arg
sed -i '' 's/old/new/' file.txt

# GNU sed (Linux) -- no arg needed
sed -i 's/old/new/' file.txt

# Portable workaround
sed 's/old/new/' file.txt > file.tmp && mv file.tmp file.txt
```

Extended regex flag also differs:

```bash
# BSD sed
sed -E 's/pattern/replace/' file.txt

# GNU sed (both work)
sed -E 's/pattern/replace/' file.txt   # preferred
sed -r 's/pattern/replace/' file.txt   # deprecated
```

Use `-E` on both platforms (supported by modern GNU sed).

### `grep`

- `grep -P` (Perl regex) -- GNU only; use `grep -E` for extended regex on both
  platforms
- `grep -o` -- works on both but output may differ for edge cases

### `date`

```bash
# GNU date -- relative dates
date -d '+1 day'
date -d '2025-01-15'

# BSD date (macOS) -- different flags
date -v+1d
date -j -f '%Y-%m-%d' '2025-01-15'

# Portable -- use Python for date math
python3 -c "from datetime import *; print(
  (datetime.now() + timedelta(days=1)).isoformat())"
```

### `stat`

Format strings are completely different:

```bash
# GNU stat -- file size
stat -c '%s' file.txt

# BSD stat (macOS)
stat -f '%z' file.txt

# Portable
wc -c < file.txt
```

### `xargs`

```bash
# GNU xargs -- -d for delimiter
echo "a:b:c" | xargs -d ':'

# BSD xargs -- no -d flag; use tr instead
echo "a:b:c" | tr ':' '\n' | xargs
```

### `find`

```bash
# GNU find -- -printf for formatted output
find . -name '*.md' -printf '%f\n'

# BSD find -- no -printf; pipe through basename
find . -name '*.md' -exec basename {} \;
```

## Optional tool checks

Tools like `jq`, `yq`, and `rg` are not installed by default on most systems.
Check before using:

```bash
if command -v jq >/dev/null 2>&1; then
    # jq is available
    curl -s "$url" | jq '.results[]'
else
    # fall back to grep/awk
    curl -s "$url" | grep -o '"name":"[^"]*"'
fi
```

For skills that rely heavily on an optional tool, declare it as a prerequisite
in the skill body or in the `compatibility` frontmatter field:

```yaml
compatibility: Requires jq for JSON processing
```

## Shell portability tips

- Use `#!/usr/bin/env bash` for bash scripts, not `#!/bin/bash` (path varies
  across systems)
- Use `#!/bin/sh` for POSIX shell scripts
- Prefer `$()` over backticks for command substitution
- Prefer `[[ ]]` only in bash; use `[ ]` in sh
- Use `printf` instead of `echo -e` (behavior varies)
- Quote variables: `"$var"` not `$var`
- Use `command -v` instead of `which` (POSIX portable)
