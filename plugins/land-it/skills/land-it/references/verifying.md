# Implementing and verifying

Read this at S3 and S4 of the parent skill. The parent owns the Verification
gate; this file holds the implementation rules and the checks that satisfy it.

## Documentation and comments

S3 owns the scope rule. These two requirements complete it.

Check whether behavior changes require user, operator, API, configuration,
migration, or runnable-example documentation. Update and verify affected docs,
or record why no documentation change was needed.

Default to no new comment; add one only for non-obvious WHY, non-local coupling
or constraints, or a silent failure that code and tests cannot expose. Do not
touch an unrelated comment.

## Check order and failure handling

Take exact commands from discovered guidance and the repository's CI, build,
hook, and test configuration. Run the cheapest checks first: formatter in check
mode, documentation lint, linters with warnings as errors, the CI-equivalent
build, tests that exercise the changed path, and runnable documentation
examples.

Stop on the first failure. If the change caused it, fix it and restart from the
top. If evidence shows it is unrelated, report it and stop without expanding
scope. If repeated attempts make no progress, report the evidence and the
blocker instead of cycling.

Never invent a missing command or use destructive cleanup to obtain a clean run.
If a required check cannot run here, stop and report
`done pending verification on <env>` with the exact check owed.

## Coverage beyond unit tests

Run new and existing unit tests. Unit coverage is not enough when the changed
behavior crosses process, service, network, storage, account, or host
boundaries; when warranted, run end-to-end integration tests too.

If only an ad hoc integration test can exercise the behavior, follow discovered
policy when it resolves access, accounts, test-safe hosts, and cleanup. Ask the
current user only for choices no policy answers or that touch shared state or
cost. Never ask the user to paste a secret into chat.

## Evidence and cleanup

Verify state-changing behavior from actual running state. Where repeatability is
expected, confirm a second run is a no-op; for intentional one-shot behavior,
verify duplicate protection without repeating the action.

Before advancing, remove debug output, scratch files, and placeholders added by
this change, and confirm no secret entered the diff.
