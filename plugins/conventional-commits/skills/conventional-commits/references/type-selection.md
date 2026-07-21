# Choosing a type

The types come from `@commitlint/config-conventional`; only the tie-breakers
below are non-obvious. Decide by what the change *does*, not which files it
touches.

## Tie-breakers

- Behavior changed for users? A new capability is `feat`; corrected behavior is
  `fix`.
- Restructured with no behavior change is `refactor` -- but if the point is
  speed it is `perf`, and if it is only whitespace or formatting it is `style`.
- Not source behavior at all? Dependencies, build, or packaging are `build`; the
  CI pipeline is `ci`; other housekeeping is `chore` (the catch-all -- try a
  specific type first).
- Comments and docstrings are `docs`, not `refactor`.
- Test-only changes are `test`, even when fixing a bug in a test.

## By type

- `feat` -- adds a user-facing capability, not a refactor or fix:
  `feat(auth): add password reset via email`
- `fix` -- corrects wrong behavior; not a restructure:
  `fix(parser): handle empty input without crashing`
- `refactor` -- restructures code with no behavior change; not `perf` or
  `style`: `refactor(parser): split the tokenizer into its own module`
- `perf` -- a change whose point is speed or resource use:
  `perf(cache): reuse buffers to cut allocation churn`
- `style` -- formatting or whitespace only, no code meaning changes:
  `style(api): normalize indentation and trailing commas`
- `docs` -- documentation, including code comments and docstrings:
  `docs(readme): document the retry backoff`
- `test` -- tests only, even when fixing a broken test:
  `test(parser): cover empty-input edge case`
- `build` -- dependencies, build config, or packaging; not `ci`:
  `build(deps): bump serde to 1.0.200`
- `ci` -- CI pipeline config only: `ci(release): cache the cargo registry`
- `chore` -- housekeeping that fits no specific type; the catch-all:
  `chore: delete a leftover scratch script`
- `revert` -- undoes an earlier commit; its body should name the reverted
  commit: `revert(auth): revert password reset via email`
