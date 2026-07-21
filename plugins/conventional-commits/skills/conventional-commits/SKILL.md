---
name: conventional-commits
description: Conventional Commits format and style rules for git commit messages -- types, scopes, subject and body, trailers, and prohibited patterns. Use when writing, reviewing, or fixing a commit message, choosing a commit type or scope, or asking about commit message conventions or Conventional Commits.
license: LICENSE
metadata:
  short-description: Write a Conventional Commits message
---

# Conventional Commits

Conventional Commits v1.0.0 with the preferences below. Encodes only the delta
from the standard -- format, imperative mood, and what the types mean are
assumed known.

## Format

`<type>[(<scope>)][!]: <description>`, then an optional body one blank line
below. `!` before the colon marks a breaking change; add a `BREAKING CHANGE:`
footer, or let the description carry it.

## Types

The types according to `@commitlint/config-conventional`, always lowercase:
`build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`,
`style`, `test`.

Unsure which type fits? See [type-selection.md](references/type-selection.md)
for tie-breakers between the easily-confused pairs.

## Subject line

- Imperative mood, no trailing period, lowercase start -- avoid Sentence-case,
  Title Case, and ALL-CAPS subjects (commitlint `subject-case`); keep real
  acronyms (API, TTL) as-is
- At most 70 characters -- GitHub truncates an auto-generated PR title (taken
  from the first commit's subject) near 72, so 70 keeps it whole
- Plain text -- no markdown, no backticks; it renders literally in
  `git log --oneline` and on GitHub
- Scope is the primary affected module or theme (`auth`, `api`, `parser`, `ci`);
  use a unifying theme when a change spans modules
- Multiple scopes are allowed when the change genuinely touches distinct modules
  with no shared theme -- separate them with `/` (`feat(api/ui):`), one of the
  delimiters commitlint's `scope-delimiter-style` recognizes; prefer one scope
  when a theme fits

## Body

Lead with WHY. The first paragraph states the rationale -- the problem or
high-level reason the change exists -- not what or how, which the diff already
shows.

**If the WHY cannot be inferred from the diff and available context, ask the
user. Never invent a rationale.**

Then:

- Separate from the subject with one blank line; wrap at 72; ASCII only
- Omit entirely when the subject says it all; when present, aim for 1-6 lines --
  more suggests the commit should be split
- Multi-part change: one line of context, then bullets -- not a wall of prose
- Do NOT restate the subject, narrate steps, or use filler -- see the Bad
  example

## Backticks (body only)

Backticks are forbidden in the subject and used in the body for things you could
grep for in source -- identifiers, flags, paths, literal values, commands
(`parse_config`, `--dry-run`, `src/main.rs`, `null`, `git rebase`). Leave
concepts and proper nouns plain (pagination, backpressure, OAuth).

## Trailers and footers

Default: run `git commit -m` with the message only, and never self-inject any
trailer. Conventional Commits permits issue and reference footers
(`Closes #123`, `Refs: #456`, `Reviewed-by:` a real person; rules 8-10), but
prefer to keep issue and ticket links in the PR description -- add such a footer
only when the human explicitly asks for it on the commit.

`Signed-off-by` and `Co-authored-by` are valid ONLY on explicit human direction
naming a real natural person -- a DCO sign-off the human makes, or a real human
co-author -- never on your own initiative. Absolute rule: an AI agent must
NEVER, under any circumstances, add itself or any non-human identity as a
`Co-authored-by`, `Signed-off-by`, or author. No exceptions, no overrides.

## Prohibited

- Emoji or Unicode anywhere in the message
- `()` appended to function names -- write `parse_config`, not `parse_config()`
- AI self-attribution as author, co-author, or signer

## Examples

```text
feat(auth): add password reset via email
```

```text
refactor(api/ui): extract the shared request-retry helper

Both the client and the dashboard carried near-identical retry
loops, so every change had to be made and reviewed twice.
```

```text
fix(parser): handle empty input without crashing

Empty files reached the tokenizer as a null slice and
panicked on the first index. Treat them as a zero-token
document instead.
```

```text
feat(api)!: paginate list endpoints by default

BREAKING CHANGE: list endpoints now return a single page;
clients that expected the full collection must follow the
`next` cursor.
```

```text
feat(export): add CSV export for reports

Users could only read reports in the browser and asked to
pull the numbers into their own spreadsheets.

- Stream rows behind the `--format csv` flag
- Persist the default output path in `config/export.toml`
```

**Bad** -- verbose, restates the diff, filler:

```text
refactor(store): move query building out of the request handler

This commit changes `store.py`. In order to make the code
cleaner, the query building logic is moved out of the request
handler into its own function, and the handler is updated to
call it.
```

**Good** -- WHY first, prose then bullet:

```text
refactor(store): move query building out of the request handler

The handler parsed the request and assembled the query in one
place, so neither could be unit-tested on its own.

- Build queries in `build_query`, called from the handler
```
