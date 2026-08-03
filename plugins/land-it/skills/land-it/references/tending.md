# Tending a change request

Read this at S10 of the parent skill. Prefer discovered tending guidance; these
requirements still apply on top of it.

## The polling loop

Honor the supplied tending window; default to 1 hour if absent. Poll on the
discovered cadence. If none exists, check after 5 minutes, then every 10
minutes.

Each cycle, inspect all required CI checks, target-branch freshness,
mergeability, inline threads, submitted reviews, conversation comments, and
automated findings.

## Handle every failure and claim

Fix valid defects; answer invalid or stylistic findings with evidence. Treat a
substantive bot comment exactly like a human one; skip only informational output
that makes no claim.

Apply the S3 implementation discipline to each fix, including documentation
impact and comments. Reply to or resolve every thread as appropriate.

When a review fix or target-branch update changes the tested state, route target
updates through S8 and repeat S4 to S6. Apply S7 before creating a new commit or
amending an existing one; the Approval gate's tending-amend exemption still
applies.

Amending follows the Safe remote update gate: amend only the state S4 to S6
reviewed, and re-run S4 to S6 if a commit hook changes that state.

## Merge

Merge-ready means required CI is green, required reviewer approvals are present,
the branch is current with and mergeable into its target, and every human or
automated review comment is resolved or answered with evidence.

When merge-ready, merge through the repository's required method when
authorized. Otherwise await approved automation or report the required human
action and continue tending within the window.

At expiry or loss of access, report the checks, target-branch status, every
unresolved comment, the merge blocker, and who acts next.
