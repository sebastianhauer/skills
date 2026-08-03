---
name: land-it
description: Orchestrates a code change from problem through verification, independent review, and an approved commit to a merged pull or merge request. Use when the user asks to land, ship, finish and land, get work merged, or take it through a pull or merge request, including work already in progress. Excludes deploying or releasing, quick or implementation-only work, and doing one part alone, such as a standalone review, commit, change-request creation, or tending an open PR or MR.
license: LICENSE
metadata:
  short-description: Land a change through merge
---

# Land a change

Carry one change through a merged change request without dropping the steps that
agents skip in flow.

Change request means the provider's reviewable, mergeable unit: a pull request,
a merge request, or the equivalent under another name. Land means merge the
change request; it never means deploy or release. Issue means the single unit of
tracking for this change, whatever the tracker calls it: an issue, a ticket, a
story, a task, or a work item. It is never a project, cycle, sprint, or
initiative.

Steps are S1 to S10. Gates are named, apply wherever a step names them, and are
stated once under Gates.

## Authority and discovery

This skill orchestrates; it does not own the mechanics. Discovered guidance
supplies how a step is done. This skill owns which steps run, in what order, and
what must be true before advancing. Discovered guidance therefore wins on
mechanics but never waives a gate. Only the current user does that.

Apply guidance in this order:

1. Current user instructions.
2. Matched repository instructions, documentation, and project skills.
3. Matched home and runtime-specific skills.
4. The defaults in this skill.

Report which guidance source won any conflict.

Match tools and skills by their descriptions before each step. Start with the
runtime's exposed and plugin-provided guidance, and load only what the current
step needs. If no match is exposed, inspect the repository and user-level
`.agents/skills/` directories, then any other skill locations the runtime
documents.

Guidance rarely announces itself by role, so match on described behavior rather
than name. Look for anything covering issue, ticket, or work tracking; prose,
language, and documentation style; worktrees and branch naming; verification,
testing, and local gates; code review, fresh eyes, a second opinion, or review
orchestration; commit message conventions; change-request titles, bodies, and
creation; and watching, babysitting, monitoring, or tending a change request
through merge.

## Gates

**Verification.** Nothing advances until the check ran, its output matched the
expected result, and it exercised the changed path. A green suite that misses
the change is not coverage.

**Independent review.** Independence has two parts, and they are not the same
gate. Session independence is the floor: a change reaches S7 only after at least
one reviewer, running in a fresh session that did not author the change,
returned findings or an explicit `No findings.`. Model independence is what
makes that review worth reading: a reviewer running the model that wrote the
change shares that model's blind spots, so review on other models, and prefer
different model families over different tools on the same model. Run two such
reviewers when two are available; never more than two unless the current user
asks. When only the authoring model is available, it still clears the floor, so
run it and report the result as a same-model review whose findings carry less
weight. If no reviewer can run safely, stop and report
`done pending independent review`.

**Approval.** This gate governs commits created or rewritten in this session;
treat pre-existing commits as evidence to review, and seek approval only to
change their message or contents. Draft the exact commit message, show it to the
current user, and wait. Do not commit, push, or open the change request before
approval. Ask again if the message changes; tending amends need no repeated
approval unless current user or repository policy requires it.

**Authorship.** Never attribute authorship to an agent, regardless of discovered
guidance: no AI or non-human identity as author, committer, `Co-authored-by`, or
`Signed-off-by`, and no generated-by or tool-attribution lines in commit
messages or change-request text.

**Safe remote update.** Before rewriting or amending published history, record
the remote branch's current object ID. Repeat S4 to S6 against the resulting
state, then update the remote only while its object ID still equals the recorded
value. Abort on any mismatch. Never refresh the recorded value merely because
another writer advanced the remote; integrate their commits into the topic
branch with the repository's required method, repeat S4 to S6 on the result, and
record a fresh value before retrying.

An explicit request to land, ship, or merge authorizes the final merge once all
gates pass. Otherwise ask before merging.

## Scope

If your prompt says you are a reviewer, or another agent spawned you to review a
change, do not run this workflow: review the change as instructed, return the
findings, and spawn nothing further. S6 launches reviewers, so a reviewer that
re-entered here would recurse.

Use a narrower workflow for a review, commit, change-request creation, or
change-request tending request on its own. A quick edit or convention question
does not need this workflow; discover the matching workflow by its described
behavior. Deployment, release, and promotion are out of scope; this skill ends
at a merged change request.

## Resuming

Enter at the first unfinished step. Resume from evidence, not assumption:
existing code still needs verification, committed work still needs review, and
an open change request re-enters at the earliest unmet gate before tending.

Inspect worktree and branch status, pushed commits, open change-request state,
checks, and reviews. Mark a step complete only when that evidence shows its
gates passed; then resume at the earliest unmet step.

Existing work stays in its current branch and worktree. Do not relocate
uncommitted changes or overwrite an existing branch or worktree.

## Prose and reporting

Authored prose means documentation, comments, issues, plans, commit messages,
change-request text, and review replies. Before showing or publishing any of it,
apply discovered prose-quality guidance. Such guidance names itself
inconsistently, so match on behavior: editing, tightening, or reviewing prose
and drafts; removing AI writing patterns, tells, or slop; humanizing text that
reads as machine-written; and writing, style, tone, or documentation standards.

Without such guidance: write for a low-attention reader, every sentence earning
its place; preserve facts, evidence, uncertainty, and meaning exactly; cut
filler, hedging, throat-clearing, and contrast that carries no content, such as
"not just X, but Y"; never invent detail, strengthen a claim, or add attitude
the source did not earn; flag a passage that lacks substance instead of
rewriting it into a stronger point.

Talk to the current user with the same discipline: brief, only facts verified
this session, detail on request.

## Workflow

Work S1 to S10 in ascending order. A step completes only when its named gates
pass. Returning to an earlier step invalidates every step after it, which must
then run again; where a step or its reference names a narrower repeat for a
specific return path, that narrower repeat governs.

- [ ] S1. Understand, align any issue, and plan
- [ ] S2. Select or create a worktree and branch
- [ ] S3. Implement the minimum change
- [ ] S4. Verify
- [ ] S5. Self-review the whole diff
- [ ] S6. Get an independent review
- [ ] S7. Get approval and commit
- [ ] S8. Sync with the target branch
- [ ] S9. Push and create or update the change request
- [ ] S10. Tend the change request until it merges or closes

S4 to S6 form the verification cycle. Any later change to the tested state
repeats it before the state may be published; the one narrower repeat is in
publishing.md, for upstream changes that touch no shared behavior.

### S1. Understand, align any issue, and plan

State the goal, constraints, and expected result. Resolve cheap, reversible
ambiguity with a reported assumption; ask before a destructive, shared-state, or
scope-changing choice.

Find an issue in the request, branch, change-request metadata, or repository
context. Tracking is optional. When an issue exists, read it before finalizing
the plan, compare its problem, scope, and done conditions with the request, and
surface mismatches before coding; the current user wins. Never rewrite the issue
silently.

If no issue exists, create one when current-user or repository policy requires
tracking; otherwise proceed untracked and report that choice at handoff.

Read [issues.md](references/issues.md) when an issue exists or creation is
chosen; it selects the single linking method that S2, S7, and S9 apply. Skip it
when proceeding untracked.

Then write or update an implementation plan before coding; keep it in the
session's task list unless repository policy names a location.

### S2. Select or create a worktree and branch

For new work, fetch first, identify the change request's target branch from
repository policy or the current user, and create a fresh worktree and branch
from its remote tip. Follow discovered branch guidance; otherwise use
Conventional Branch `<type>/<description>`: <https://conventionalbranch.org/>.

For work already in progress, continue in its current worktree and resolve its
target from the open change request, repository policy, or the current user;
otherwise use the fetched remote default.

Record the target for review, synchronization, and the change-request base. If
the current branch is that target, create a topic branch at the current `HEAD`
in the same worktree before committing or pushing. Never land commits directly
on the target branch.

Apply the branch name to the issue link only when the branch-name method I2 is
the selected method, in which case the tracker-required syntax overrides
Conventional Branch where the two are incompatible. Otherwise keep issue
identifiers out of the branch name.

Record the worktree path and report its disposition at handoff. Do not remove it
without repository policy or current-user direction.

### S3. Implement the minimum change

Every changed line must trace to the request. Add no speculative abstraction,
configuration, or flexibility; do not refactor or reformat adjacent code.
Mention unrelated problems without fixing or deleting them.

Read [verifying.md](references/verifying.md) for the documentation-impact and
comment rules this step must satisfy.

### S4. Verify

Satisfy the Verification gate.

Read [verifying.md](references/verifying.md) for where the exact commands come
from, check order, failure handling, coverage beyond unit tests, and the
evidence and cleanup required before advancing.

### S5. Self-review the whole diff

Read every changed line as a reviewer. Check scope, correctness, tests,
documentation impact, comments, prose, generated artifacts, and secrets. Return
to S4 after any change.

### S6. Get an independent review

Satisfy the Independent review gate. Prefer discovered review orchestration when
it can enforce the packet and findings contract. Look for guidance describing
pre-push or pre-merge review, fresh eyes, a second opinion, a sanity check, or
parallel independent reviewers.

Read [reviewing.md](references/reviewing.md) for the reviewer packet, the
findings contract, and the fallback mechanics when no orchestration was
discovered.

When reviews return, fix verified defects and rebut unsupported findings with
evidence, then repeat the verification cycle on the complete resulting change.
Stop and report when repeated review cycles make no material progress. Surface
any finding that would reshape the change or requires judgment.

### S7. Get approval and commit

Follow discovered commit conventions, including signing and trailers. If none
exist, use Conventional Commits: `<type>[(<scope>)][!]: <description>`. The
Authorship gate applies to every commit and trailer.

Write a concise subject that a technical reader can understand without hidden
context. When a body is needed, lead with WHY: the problem or high-level reason
for the change. Do not narrate WHAT or HOW when the diff already shows it. If
the rationale is not known, ask the current user rather than inventing one. Keep
issue identifiers out of the subject unless no other supported method exists;
when the commit-body method I3 is selected, put the provider-supported reference
on the final body line instead.

Stage only the intended, reviewed change and inspect the staged diff. Satisfy
the Approval gate, then commit the approved message and verify the committed
message kept any required reference on its final line.

### S8. Sync with the target branch

Fetch and integrate the recorded target branch using the repository's required
method; rewriting published history follows the Safe remote update gate.

Read [publishing.md](references/publishing.md) for which steps each kind of
upstream change repeats.

### S9. Push and create or update the change request

Use a plain push for unpublished history; a rewrite from S8 follows the Safe
remote update gate. Create or update the change request with the target recorded
in S2 as its base, then read it back and verify that base.

Read [publishing.md](references/publishing.md) for change-request conventions,
description linking, and verifying that the provider registered the issue link.

### S10. Tend the change request until it merges or closes

Prefer discovered tending guidance: anything describing babysitting, watching,
or monitoring a change request, or answering review and bot comments in a loop.

Investigate every failure and review claim until the change request merges,
closes, or the tending window expires. Never call an unmerged change request
done.

Read [tending.md](references/tending.md) for the polling loop, how to handle
findings and amendments, and what merge-ready requires.
