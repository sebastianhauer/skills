# Skill Patterns

Common patterns for structuring skill content.

## Contents

- Structural patterns (workflow, template, conditional, feedback loop,
  quick-reference table, contract/provider split, old-patterns block)
- Safety patterns (draft-first, dry-run, plan-validate-execute, confirmation
  gate, choosing a safety level)
- Progressive disclosure patterns
- Degrees of freedom
- Anti-patterns

## Structural patterns

### Workflow

Numbered steps with an optional checklist for progress tracking. Best for
multi-step procedures.

```markdown
## Deployment workflow

- [ ] Step 1: Run pre-flight checks
- [ ] Step 2: Build artifacts
- [ ] Step 3: Deploy to staging
- [ ] Step 4: Validate staging
- [ ] Step 5: Promote to production

### Step 1: Run pre-flight checks

Run: `scripts/preflight.sh`
...
```

### Template

Output format with placeholders. Best when consistent structure matters more
than specific content. Match strictness to need: "ALWAYS use this exact
structure" for machine-consumed output, "sensible default, adapt as needed" for
prose.

```markdown
## Incident summary structure

# [Incident title] ([date])

## Impact
[Who/what was affected, for how long]

## Timeline
- [HH:MM] event

## Root cause
[One paragraph]

## Follow-ups
1. [Owner] action item
```

### Conditional

Decision points with branches. Best when different inputs require different
approaches.

```markdown
## Choose approach

**Creating new content?**
  -> Follow "Creation workflow" below

**Editing existing content?**
  -> Follow "Editing workflow" below
```

### Feedback loop

Validate, fix, repeat. Best for quality-critical tasks.

```markdown
## Edit process

1. Make edits
2. Validate: `scripts/validate.py output/`
3. If validation fails, fix and re-validate
4. Only proceed when validation passes
```

### Quick reference table

Scannable command/option tables. Highly effective for CLI-wrapping skills.

```markdown
## Commands

| Command           | Description    |
|-------------------|----------------|
| `tool search <q>` | Keyword search |
| `tool query <q>`  | Hybrid search  |
| `tool ask <q>`    | AI answer      |

### Options

| Flag     | Default | Description |
|----------|---------|-------------|
| `-n`     | 5       | Max results |
| `--json` | false   | JSON output |
```

### Contract/provider split

When a skill wraps a family of interchangeable backends, split it: one contract
skill defines the generic verbs and workflow; one provider skill per backend
supplies the specific commands. Domain skills depend only on the contract, so
adding a backend never touches them.

```text
cloud-deploy/            # contract: verbs, workflow, safety gates
aws-deploy/              # provider: AWS-specific commands
gcp-deploy/              # provider: GCP-specific commands
```

### Old patterns block

Never write time-sensitive instructions ("before August 2025, use the old API").
Document the current method, and park deprecated material in a collapsed block
so history is available without cluttering the main path:

```markdown
## Current method

Use the v2 endpoint: `api.example.com/v2/messages`

<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>

The v1 API used `api.example.com/v1/messages`. No longer supported.

</details>
```

## Safety patterns

Consider these patterns when a skill performs side-effecting operations (sending
messages, deploying, deleting). The skill author decides the appropriate level
based on risk and reversibility -- not every skill needs confirmation gates.
Read-only or low-risk operations should always run autonomously.

### Draft-first

For operations that send or publish content. Create a draft, show a preview, let
the user decide.

```markdown
## Sending workflow

1. Create draft: `tool draft --to "user@example.com"`
2. Show preview to user
3. Send only after user confirms:
   `tool send --draft-id "123" --confirm YES`
```

### Dry-run

For operations with observable side effects. Preview the result before
committing.

```markdown
## Apply changes

1. Show what will be affected
2. Run with `--dry-run` first
3. If output looks correct, apply for real
```

### Plan-validate-execute

For batch or destructive operations where a wrong step is costly: have the agent
emit its plan as a machine-checkable file, validate the plan with a script, and
only then execute. Errors surface before anything is touched, and the agent can
iterate on the plan without side effects.

```markdown
## Bulk update workflow

1. Analyze inputs: `python scripts/analyze.py > plan.json`
2. Edit plan.json with the intended changes
3. Validate: `python scripts/validate_plan.py plan.json`
4. Fix and re-validate until clean -- do not proceed on errors
5. Apply: `python scripts/apply_plan.py plan.json`
6. Verify the result
```

Make validators verbose: "field 'signature_date' not found; available:
customer_name, order_total" lets the agent fix the plan in one step.

### Confirmation gate

For destructive or irreversible operations where autonomous execution would be
dangerous.

```markdown
## Delete workflow

1. List items to delete
2. Display count and details
3. Ask: "Delete N items? This cannot be undone."
4. Proceed only on explicit "yes"
```

### Choosing a safety level

- **No gate**: read-only, idempotent, or trivially reversible operations
  (search, format, lint)
- **Dry-run**: operations with side effects that can be previewed (apply config,
  migrate data)
- **Draft-first**: operations that send/publish content to external recipients
- **Confirmation gate**: destructive or irreversible operations (delete,
  overwrite, deploy to prod)

## Progressive disclosure patterns

### High-level guide with references

Keep SKILL.md focused on the workflow. Move variant details to reference files.

```markdown
# PDF Processing

## Quick start
Use pdfplumber for text extraction:
[core example]

## Advanced features
- Form filling: see [FORMS.md](references/FORMS.md)
- API reference: see [REFERENCE.md](references/REFERENCE.md)
```

### Domain-specific organization

Organize references by domain so the agent loads only what is relevant.

```text
bigquery-skill/
  SKILL.md                  # Overview + navigation
  references/
    finance.md              # Revenue, billing
    sales.md                # Pipeline, deals
    product.md              # Usage, features
```

### Framework/variant organization

Organize by variant when a skill supports multiple frameworks or providers.

```text
cloud-deploy/
  SKILL.md                  # Workflow + selection
  references/
    aws.md                  # AWS patterns
    gcp.md                  # GCP patterns
    azure.md                # Azure patterns
```

## Degrees of freedom

Match specificity to task fragility:

- **High** (text instructions) -- multiple valid approaches, context-dependent
  decisions
- **Medium** (pseudocode/templates) -- preferred pattern, some variation
  acceptable
- **Low** (specific scripts) -- fragile operations, consistency critical, exact
  sequence required

Think of the agent exploring a path: a narrow bridge needs guardrails (low
freedom), an open field allows many routes (high freedom).

## Anti-patterns

- Vague names (`helper`, `utils`, `tools`)
- Too many options without a clear default
- Time-sensitive information ("before August 2025...")
- Inconsistent terminology across the skill
- Windows-style backslash paths
- Putting "When to Use" sections in the body (description is the only trigger
  mechanism)
- Duplicating content between SKILL.md and references
- Offering choices when there is one right answer
