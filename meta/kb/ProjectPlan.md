**Meta-Prompt**: Use the template below to generate a prescriptive plan for another autonomous development agent to implement. You should replace any template variables (i.e. `<VAR:.../>`)

Template Variables take two forms:

- `<VAR:name desc="Description..."/>`: Variable Declaration; defines a template unique name & a required description of the variable.
- `<VAR:name/>` : A reference to an existing variable

Procedural Instructions & Normative Metadata about the template will be provided as follows:

- `<!-- Template Start|Stop -->`
- `<!-- Template Instruct — ... -->`
- `<!-- Template Block Start|Stop -->`

<!-- Template Start -->

# <VAR:plan_slug desc="Some short descriptive name for the plan"/> Plan

This document details a plan to <VAR:plan_desc desc="A salient executive summary of the plan."/>

## Goals, Outcomes & Success Criteria

The intent of this plan is to <VAR:plan_goals desc="A precise articulation of what you want the plan to achieve"/>.

At conclusion of this plan, the following outcomes should be seen:

<VAR:plan_outcomes desc="An itemized list of concrete targets for the autonomous agent to complete"/>

To gauge your success of actualizing this plan, use the following success criteria:

<VAR:succ_crit desc="An itemized list of success criteria; can be qualitative, quantitative, heuristics or any other concrete mechanism the autonomous agent can use to measure & gauge it's success."/>

## Scope & Constraints

Scope your efforts to <VAR:scope desc="A precise articulation of the boundaries of the work; you don't need to be exhaustive (ie. Do this; don't do this) but you should paint a picture of where to autonomous agent should focus it's efforts & provide heuristics the agent can use to gauge if it is working outside the scope you set. The size of the scope implicitly dictates the total work completed, time required for completion & probability of success; large scopes become chaotic; tight scopes are focused."/>

Throughout your work, you should be mindful of your constraints. <VAR:constraints desc="A precise articulation of what constraints the agent has placed on it; constraints can have varying levels of control (ie. MUST, SHOULD, CAN, etc...). Be prescriptive in what constraints are set; loose or ambiguous constraints allow the agent to diverge from your expectations. Be mindful not to over constrain the agent as not to limit it's capability to accomplish the goals you laid out. Strike a balance while providing firm guidance."/>

Throughout your efforts be mindful of the following:

- You MUST keep your working directory at the project root (i.e. `./`).
- You MUST adhere to the [Contributor's Guide](./CONTRIBUTOR.md) & the [Agent Guide](./AGENT.md)
- You SHOULD create Temporary Files under `./.cache/tmp/<VAR:plan_dir desc="A Filesafe & human readable name for the project"/>`
- You SHOULD record your efforts under `./meta/work/<VAR:plan_dir/>`
  - This should include any subplans, summaries, commit messages or other general information regarding your efforts.
- You SHOULD use the Python venv at `./.venv`.
- You MAY prompt the user for feedback, guidance or general help when ambiguity arises that you are unable to traverse.

## Procedures

<VAR:proc_sum desc="An executive summary of the holistic plan"/>

<!-- Template Block Start -->
<!-- Template Instruct — Add the following Block for each phase you have identified -->

### Phase <VAR:phase_n desc="The Phase Number"/> — <VAR:phase_slug desc="Short punchy description of the phase"/>

**Summary** — <VAR:phase_summary desc="A Salient Summary of this Phase"/>

**Prerequisites** — Before beginning this phase, ensure:

<VAR:phase_prereqs desc="An itemized list of conditions that must be true before starting (e.g., previous phase completion, external dependencies available, required tools installed)"/>

**Dependencies** — This phase depends on:

<VAR:phase_deps desc="An itemized list of dependencies including: other phases, external services, data sources, or resources that must be available during execution"/>

**Tasks** — The following phase is composed of the following tasks:

<VAR:phase_tasks desc="An Itemized List of tasks the agent should complete"/>

**Project State** — At conclusion of this phase; the desired project state should be:

<VAR:phase_state desc="An itemized list of substate items, each prescriptive & precise."/>

**Validation Criteria** — To confirm successful phase completion, validate:

<VAR:phase_validation desc="An itemized list of specific validation checks (e.g., unit tests pass, files exist at expected locations, services respond correctly, performance metrics met)"/>

**Validation Actions** — If validation fails:

<VAR:validation_failure desc="Procedures for handling validation failures including: rollback steps, error reporting format, retry logic, or escalation to user"/>

<!-- Template Block Stop -->

## Work Process

### Git Branch Management

Create and switch to branch **`dev/<VAR:plan_slug/>`**:

```bash
git switch -c dev/<VAR:plan_slug/>
```

All work must occur on this branch.

**Committing Changes**

Commit changes using precise pathspecs. Write file paths to **`./.cache/tmp/<VAR:plan_dir/>/pathspec.txt`**, one per line. Write descriptive commit messages to **`./.cache/tmp/<VAR:plan_dir/>/commit.txt`** using present tense.

```bash
git add --pathspec-from-file=./.cache/tmp/<VAR:plan_dir/>/pathspec.txt
git commit --pathspec-from-file=./.cache/tmp/<VAR:plan_dir/>/pathspec.txt -F ./.cache/tmp/<VAR:plan_dir/>/commit.txt
rm ./.cache/tmp/<VAR:plan_dir/>/pathspec.txt ./.cache/tmp/<VAR:plan_dir/>/commit.txt
```

### Work Recording

Track progress through append-only task files and contextual journal entries.

**Task Files**: `./meta/work/<VAR:plan_dir/>/tasks/PhaseNN-TaskMMM.md`

Create a new file when starting each task, then append entries as events occur.

**On Start** — Create the file when beginning a task:

```bash
cat > ./meta/work/<VAR:plan_dir/>/tasks/Phase01-Task001.md << EOF
# Phase 01 - Task 001: ${TASK_NAME}

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Started
Attempts: 1
Beginning ${TASK_DESCRIPTION}.
EOF
```

**On Update** — Append after each commit, milestone reached, or issue encountered:

```bash
cat >> ./meta/work/<VAR:plan_dir/>/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Progress
${UPDATE_DESCRIPTION}
Commit: $(git rev-parse --short HEAD) "$(git log -1 --pretty=%s)"
EOF
```

**On Completion** — Append once when task succeeds:

```bash
START_TIME=$(grep "Started" ./meta/work/<VAR:plan_dir/>/tasks/Phase01-Task001.md | head -1 | cut -d' ' -f2)
cat >> ./meta/work/<VAR:plan_dir/>/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Completed
Task completed successfully.
Total duration: $(date -d "$(date -u +%Y-%m-%dT%H:%M:%SZ)" +%s -d "$START_TIME" +%s | awk '{print int(($1-$2)/60) " minutes"}')
EOF
```

**On Failure** — Append when task fails, before retrying:

```bash
cat >> ./meta/work/<VAR:plan_dir/>/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Failed
Error: ${ERROR_MESSAGE}
Will retry with: ${RETRY_STRATEGY}
EOF
```

**Journal Entries**: `./meta/work/<VAR:plan_dir/>/journal/YYYYMMDDTHHMMSSZ.md`

Create entries for major decisions, errors, user interactions, phase transitions, and architectural insights. Include entry type, phase/task reference, and relevant commit SHAs.

### Checkpoints

Create git tags at recovery points:

```bash
git tag -a "checkpoint-$(date -u +%Y%m%dT%H%M%SZ)" -m "Phase: $PHASE, Task: $TASK"
```

### Error Handling

Respond to errors based on type:

- **Recoverable** (timeouts, rate limits) - Log error, retry with exponential backoff, maximum 3 attempts
- **Unrecoverable** (missing dependencies) - Document in journal, halt with actionable error
- **Ambiguous** (unclear requirements) - Request clarification, document assumptions if needed

### History Export and Final Merge

Preserve work history before merging to trunk.

Export git history to capture detailed commit information:

```bash
git log --reverse --pretty=format:'%H|%ad|%an|%s' --date=iso-strict > ./meta/work/<VAR:plan_dir/>/history/commits.txt
git log --reverse --name-status --pretty=format:'----%n%H|%ad|%s' > ./meta/work/<VAR:plan_dir/>/history/changes.txt
```

Generate summary at **`./meta/work/<VAR:plan_dir/>/SUMMARY.md`** containing phase timings, key decisions, and error patterns.

Commit all metadata:

```bash
git add ./meta/work/<VAR:plan_dir/>/
git commit -m "Archive work history for <VAR:plan_slug/>"
git tag -a "work-complete-<VAR:plan_slug/>" -m "Work history archived"
```

Merge to trunk using squash commit:

```bash
git checkout trunk
git merge --squash dev/<VAR:plan_slug/>
```

Write merge message to **`./.cache/tmp/<VAR:plan_dir/>/merge-commit.txt`**:

```
<VAR:plan_slug/>: <VAR:plan_desc/>

Summary of changes:
- [Major feature/change 1]
- [Major feature/change 2]

Work history preserved in ./meta/work/<VAR:plan_dir/>/
```

```bash
git commit -F ./.cache/tmp/<VAR:plan_dir/>/merge-commit.txt
rm ./.cache/tmp/<VAR:plan_dir/>/merge-commit.txt
```

Do not delete the **`dev/<VAR:plan_slug/>`** branch - it contains detailed commit history for future reference.

## Context

<VAR:plan_ctx desc="An exhaustive section detailing the context associated with this plan; this document must be able to stand alone."/>

<!-- Template Stop -->

Once you've generated the plan, review it, analyzing it for ambiguity or divergence from you desired outcomes. Continuously revise the plan until you feel it is prescriptive enough for an autonomous agent to follow or you feel you are splitting hairs in your edits. Be pragmatic.
