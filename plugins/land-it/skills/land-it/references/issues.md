# Issue tracking

Read this at S1 of the parent skill when an issue exists or creation is chosen.
The parent skill owns the optional-tracking gate, scope alignment, and
current-user precedence.

## Create an issue

Follow discovered tracker and workspace policy. Search for duplicates, then
draft the issue for current-user approval before the implementation plan:

- Name a checkable outcome, not an activity.
- Keep the body concise, high-level, and non-prescriptive.
- Put necessary evidence in an optional `Context` section, not an implementation
  recipe.
- Resolve required tracker containers and fields from discovered policy.
- For optional project grouping, search close fits and ask which applies,
  including none.
- Apply assignee, cycle, sprint, label, and state defaults only when discovered
  policy defines them.

If live access is unavailable, report the gap and ask rather than guessing.
After approval, create the issue in one write, read it back, and remember its
identifier.

## Select one linking method

Discover available methods and choose the highest-priority method selected by
current-user, repository, or tracker policy. When none selects one, use this
fallback order:

- **I1, description reference.** A provider-supported reference or magic-keyword
  line at the end of the change-request description, such as `Refs ABC-123`,
  `Closes ABC-123`, `Fixes #123`, or `Resolves #123`. This is the default.
- **I2, branch name.** The issue identifier in a new or already compliant branch
  name.
- **I3, commit body.** A provider-supported reference on the final line of the
  commit body.

Record which method won. S2, S7, and S9 each apply only the selected one.

Treat I2 as unavailable for an existing noncompliant branch unless policy or the
current user permits a safe rename or replacement branch. Use additional
locations only when policy requires them.

Use a closing form only when merge satisfies every done condition; otherwise use
a non-closing reference and ask when uncertain. Keep identifiers out of commit
subjects and change-request titles unless no other supported method exists.

S9 verifies that the provider registered the link. Falling back after the branch
is published is gated; see `publishing.md`.
