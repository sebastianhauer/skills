# Syncing and publishing

Read this at S8 and S9 of the parent skill. The parent owns the Safe remote
update gate; this file holds the integration and change-request mechanics.

## What an upstream change invalidates

After integrating the target branch at S8, repeat the work those changes
invalidate:

- Conflict resolutions repeat the verification cycle, S4 to S6.
- Other upstream changes repeat S4 and S5, and S6 as well when they touch the
  same behavior.
- If integration requires new uncommitted changes, a changed commit message, or
  a new commit of its own, a merge commit's message included, return to S7.

## Change-request conventions

Follow discovered conventions for title, body, reviewers, and assignees. Absent
a convention, assign the change request to its author: it keeps the request
findable while S10 tends it, and ownership is part of what S10 reports at
handoff.

When I1, the description reference, is the selected method, put the
provider-supported reference on the final line of the description.

## Verify the issue link registered

For any selected linking method, read the change request back and verify that
the provider registered the issue link when it exposes that state. When
registration state is unavailable, verify the configured syntax and report
recognition as pending.

If registration failed, prefer a fallback that changes nothing already
published, which by S9 usually means editing the change-request description. The
other methods are not free at this point: I2 renames a pushed branch and
detaches the open change request, and I3 amends an approved commit, which is a
published-history rewrite. Before either, ask the current user, then route the
work through S7 for approval and the Safe remote update gate. A link never
justifies rewriting published history without both.
