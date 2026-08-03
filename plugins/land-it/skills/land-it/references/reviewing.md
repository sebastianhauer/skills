# Independent review

Read this at S6 of the parent skill. The parent owns the Independent review
gate; this file holds the reviewer packet, the findings contract, and the
fallback mechanics for running reviewers when no orchestration was discovered.

## The reviewer packet

Review the complete intended change from the target merge base, including
staged, unstaged, and untracked work. Give every reviewer the same packet:

- repository root
- target branch and merge base
- exact change and path manifest
- concise intent, WHY, and scope
- issue done conditions when tracked
- applicable requirement paths
- instructions to read changed files and relevant tests in full

Omit the authoring transcript and any argument defending the implementation. A
reviewer that reads the defense reviews the defense.

## The findings contract

Require only actionable defects introduced by this change, each with severity,
file and line evidence, the affected scenario, and rationale. Accept an explicit
`No findings.` as a complete result. Preserve failures and empty results rather
than rerunning a reviewer until it produces something.

## Build the review target

Use the target recorded in S2. Resolve it from change-request metadata or
tracking configuration only when that record is missing or invalid; never
silently substitute another default. Fetch, compute the merge base, and review
what would merge, not a branch-tip comparison.

Materialize committed changes since that base plus staged, unstaged, and
relevant untracked changes. Exclude unrelated workspace changes, represent new
files in full, and include a changed-path manifest.

## Discover reviewers

Inspect the runtime and `PATH` for headless CLIs and built-in cold review.
Examples include Codex CLI, Claude Code, Gemini CLI, and GitHub Copilot CLI.
Read current help instead of assuming flags or command shapes.

The Independent review gate sets how many reviewers to run. To choose which
ones, prefer different external CLIs; pair one external CLI with built-in cold
review when necessary.

Discover supported models from current help or model listing. The Independent
review gate governs which models qualify; among those, prefer recent
high-capability coding or reasoning models. Do not hard-code or install models,
reconfigure accounts, or exceed a user cost or latency limit. Report the model
each reviewer actually ran, so a same-model review is visible as one.

Record unavailable or blocked reviewers once. Never inspect credential files,
environment secrets, keychains, or authentication stores.

## Enforce a cold, read-only session

- Start a new process and session, never an authoring-session continuation.
- Allow only reads, search, and read-only version-control inspection.
- Deny edits, file creation, staging, commits, pushes, and nested delegation.
- Disable customizations and recursive review orchestration where supported.
- Pass repository requirements in the packet.
- Skip a tool that cannot enforce a non-mutating run.

## Run in the background

Launch each reviewer through a background process so the calling session stays
responsive. Keep outputs separate and capture reviewer, model, status, output,
and reported cost. A successful process must return a complete result or an
explicit `No findings.`.

## Aggregate and repeat

Wait for every launched reviewer. Verify citations, reject unsupported claims,
deduplicate findings, mark consensus and isolated claims, and summarize every
result. Evidence outranks agreement.

Review fixes in new sessions and on the complete result; a fix-only delta can
hide integration defects.
