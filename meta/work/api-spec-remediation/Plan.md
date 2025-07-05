# API-Spec-Remediation Plan

This document details a plan to remediate medium and high severity API specification compliance issues in the Observability package to ensure alignment with PyAPISpec.md standards before release.

## Goals, Outcomes & Success Criteria

The intent of this plan is to bring the Observability package into full compliance with the PyAPISpec.md standard by addressing all medium and high severity issues identified during the comprehensive review, ensuring the package provides a consistent, well-documented API that meets the quality standards for release.

At conclusion of this plan, the following outcomes should be seen:

- All critical API contract violations are resolved (missing handler imports in main stub)
- Handler type definitions are centralized in types.py following architectural best practices
- Domain stub files have proper section organization (current_span and constants placement)
- All stub files accurately reflect their implementation counterparts
- Type checking passes with mypy --strict on all stub files
- A validation test suite exists to prevent future drift between stubs and implementations

To gauge your success of actualizing this plan, use the following success criteria:

- All handlers exported in __init__.py are also exported in __init__.pyi with matching signatures
- HandlerChain, HandlerPredicate, and protocol definitions exist in types.py and are imported from there
- current_span in tracing.pyi is in the Core Types section
- Logging constants (DEBUG, INFO, etc.) in logging.pyi are in the Type Definitions section
- `mypy --strict src/observability` passes without errors
- A new test file test_api_spec_compliance.py exists and passes, validating stub-implementation alignment
- No type definitions are duplicated across multiple files

## Scope & Constraints

Scope your efforts to addressing only the medium and high severity API specification compliance issues identified in the review. Focus specifically on:
- Fixing missing exports in stub files that break the API contract
- Centralizing type definitions to prevent duplication and drift
- Correcting section organization violations in domain stub files
- Creating minimal validation infrastructure to prevent regression

Do not address low-severity formatting preferences (like section separator styles) or make any changes to the implementation files themselves. The scope is limited to stub file corrections and type organization to ensure API specification compliance without disrupting the existing codebase.

Throughout your work, you should be mindful of your constraints. You MUST preserve all existing functionality and API surface area - no breaking changes are allowed. You MUST ensure all changes maintain backward compatibility. You SHOULD make minimal changes to achieve compliance - avoid refactoring beyond what's necessary. You MUST NOT modify any implementation (.py) files unless absolutely required for type definition moves. You SHOULD preserve existing documentation content while only adjusting its location if needed. You CAN add new type definitions to types.py but MUST NOT remove any existing ones. You MUST run type checking after each change to ensure no regressions.

Throughout your efforts be mindful of the following:

- You MUST keep your working directory at the project root (i.e. `./`).
- You MUST adhere to the [Contributor's Guide](./CONTRIBUTOR.md) & the [Agent Guide](./AGENT.md)
- You SHOULD create Temporary Files under `./.cache/tmp/api-spec-remediation`
- You SHOULD record your efforts under `./meta/work/api-spec-remediation`
  - This should include any subplans, summaries, commit messages or other general information regarding your efforts.
- You SHOULD use the Python venv at `./.venv`.
- You MAY prompt the user for feedback, guidance or general help when ambiguity arises that you are unable to traverse.

## Procedures

The remediation will be executed in four phases: First, addressing critical API contract violations by adding missing handler exports. Second, centralizing all type definitions to eliminate duplication. Third, correcting section organization in domain stubs. Finally, creating validation infrastructure to prevent future compliance drift. Each phase builds on the previous, with validation at each step to ensure no regressions are introduced.

### Phase 1 — Critical API Contract Fixes

**Summary** — Fix missing handler imports in main __init__.pyi that break the API contract, ensuring users can discover all available handlers through type information.

**Prerequisites** — Before beginning this phase, ensure:

- Current branch is clean with no uncommitted changes
- All existing tests pass
- mypy is available in the environment
- Understanding of which handlers are exported in __init__.py

**Dependencies** — This phase depends on:

- Access to both __init__.py and __init__.pyi files
- List of handlers from implementation that need to be added to stub

**Tasks** — The following phase is composed of the following tasks:

1. Compare exports in src/observability/__init__.py with src/observability/__init__.pyi
2. Add missing handler imports to __init__.pyi from handlers submodule
3. Ensure __all__ in stub file matches implementation
4. Run mypy to verify no type errors introduced
5. Create test to verify export parity going forward

**Project State** — At conclusion of this phase; the desired project state should be:

- __init__.pyi contains all handler imports that exist in __init__.py
- Both files have matching __all__ exports
- Type checking passes on the main module
- A basic export verification test exists

**Validation Criteria** — To confirm successful phase completion, validate:

- `mypy src/observability/__init__.pyi` produces no errors
- All handlers can be imported from observability package in type stubs
- Export verification test passes
- No implementation behavior has changed

**Validation Actions** — If validation fails:

- Revert changes using git
- Analyze mypy error output to identify issue
- Check for typos in handler names or import paths
- Verify handler modules exist and are properly typed
- If unclear, request user guidance on specific handler signatures

### Phase 2 — Type Definition Centralization

**Summary** — Move all handler-related type definitions from handlers/__init__.pyi to types.py, establishing a single source of truth for type definitions.

**Prerequisites** — Before beginning this phase, ensure:

- Phase 1 is complete and validated
- Understanding of which types need to be moved (HandlerChain, HandlerPredicate, protocols)
- types.py is accessible and modifiable

**Dependencies** — This phase depends on:

- Successful completion of Phase 1
- Access to handlers/__init__.pyi and types.py
- Understanding of protocol definitions

**Tasks** — The following phase is composed of the following tasks:

1. Identify all type definitions in handlers/__init__.pyi (HandlerChain, HandlerPredicate, ManagedHandler, LifecycleHandler)
2. Move type definitions to appropriate section in types.py
3. Update handlers/__init__.pyi to import these types from types module
4. Update types.py __all__ export list
5. Verify all imports still work correctly

**Project State** — At conclusion of this phase; the desired project state should be:

- All handler-related types exist only in types.py
- handlers/__init__.pyi imports types from ..types
- No duplicate type definitions exist
- All type imports resolve correctly

**Validation Criteria** — To confirm successful phase completion, validate:

- No type definitions remain in handlers/__init__.pyi (only imports)
- types.py contains all moved definitions with proper documentation
- `mypy src/observability/handlers/` passes without errors
- Handler type annotations still work correctly

**Validation Actions** — If validation fails:

- Check for circular import issues
- Verify import paths are correct
- Ensure all moved types are added to types.py __all__
- Review any mypy errors for missing type imports
- Document any discovered circular dependencies for user review

### Phase 3 — Domain Stub Organization

**Summary** — Correct the placement of constants and context variables in domain stub files to match PyAPISpec.md section organization requirements.

**Prerequisites** — Before beginning this phase, ensure:

- Phases 1 and 2 are complete and validated
- Understanding of correct section organization per PyAPISpec.md
- Access to all three domain stub files

**Dependencies** — This phase depends on:

- Successful completion of previous phases
- Access to logging.pyi, tracing.pyi stub files
- Clear understanding of Type Definitions vs Core Types sections

**Tasks** — The following phase is composed of the following tasks:

1. Move DEBUG, INFO, WARNING, ERROR, CRITICAL constants in logging.pyi to Type Definitions section
2. Move current_span ContextVar in tracing.pyi to Core Types section
3. Verify section headers are consistent across all domain stubs
4. Run mypy on each modified domain module
5. Update any affected imports if necessary

**Project State** — At conclusion of this phase; the desired project state should be:

- logging.pyi has severity constants in Type Definitions section
- tracing.pyi has current_span in Core Types section
- All domain stubs follow consistent section organization
- Type checking still passes on all modules

**Validation Criteria** — To confirm successful phase completion, validate:

- Constants appear after type definitions section header in logging.pyi
- current_span appears in core types section in tracing.pyi
- `mypy src/observability/domains/` passes without errors
- Domain module imports still work correctly

**Validation Actions** — If validation fails:

- Verify items were moved to correct sections
- Check for any broken internal references
- Ensure section headers weren't accidentally modified
- Review line numbers in any mypy errors
- Revert and retry with more careful placement

### Phase 4 — Validation Infrastructure

**Summary** — Create test infrastructure to ensure ongoing compliance between stub files and implementations, preventing future drift.

**Prerequisites** — Before beginning this phase, ensure:

- All previous phases are complete and validated
- pytest is available in the environment
- Understanding of which aspects need ongoing validation

**Dependencies** — This phase depends on:

- Successful completion of all previous phases
- Access to test directory structure
- pytest and mypy available

**Tasks** — The following phase is composed of the following tasks:

1. Create tests/test_api_spec_compliance.py
2. Implement test to verify __all__ exports match between .py and .pyi files
3. Implement test to verify no duplicate type definitions exist
4. Implement test to verify all public methods in implementations exist in stubs
5. Add compliance test to CI configuration if applicable

**Project State** — At conclusion of this phase; the desired project state should be:

- test_api_spec_compliance.py exists with comprehensive validation
- All compliance tests pass
- Future changes that break compliance will be caught by tests
- Documentation exists on how to maintain compliance

**Validation Criteria** — To confirm successful phase completion, validate:

- pytest tests/test_api_spec_compliance.py passes
- Tests catch if exports are removed from stubs
- Tests catch if type definitions are duplicated
- Tests are fast and focused
- Clear error messages when compliance is broken

**Validation Actions** — If validation fails:

- Debug specific test failures
- Adjust test logic if too strict
- Ensure tests aren't brittle to minor changes
- Document any intentional spec deviations
- Add skip markers with justification if needed

## Work Process

### Git Branch Management

Create and switch to branch **`dev/api-spec-remediation`**:

```bash
git switch -c dev/api-spec-remediation
```

All work must occur on this branch.

**Committing Changes**

Commit changes using precise pathspecs. Write file paths to **`./.cache/tmp/api-spec-remediation/pathspec.txt`**, one per line. Write descriptive commit messages to **`./.cache/tmp/api-spec-remediation/commit.txt`** using present tense.

```bash
git add --pathspec-from-file=./.cache/tmp/api-spec-remediation/pathspec.txt
git commit --pathspec-from-file=./.cache/tmp/api-spec-remediation/pathspec.txt -F ./.cache/tmp/api-spec-remediation/commit.txt
rm ./.cache/tmp/api-spec-remediation/pathspec.txt ./.cache/tmp/api-spec-remediation/commit.txt
```

### Work Recording

Track progress through append-only task files and contextual journal entries.

**Task Files**: `./meta/work/api-spec-remediation/tasks/PhaseNN-TaskMMM.md`

Create a new file when starting each task, then append entries as events occur.

**On Start** — Create the file when beginning a task:

```bash
cat > ./meta/work/api-spec-remediation/tasks/Phase01-Task001.md << EOF
# Phase 01 - Task 001: ${TASK_NAME}

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Started
Attempts: 1
Beginning ${TASK_DESCRIPTION}.
EOF
```

**On Update** — Append after each commit, milestone reached, or issue encountered:

```bash
cat >> ./meta/work/api-spec-remediation/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Progress
${UPDATE_DESCRIPTION}
Commit: $(git rev-parse --short HEAD) "$(git log -1 --pretty=%s)"
EOF
```

**On Completion** — Append once when task succeeds:

```bash
START_TIME=$(grep "Started" ./meta/work/api-spec-remediation/tasks/Phase01-Task001.md | head -1 | cut -d' ' -f2)
cat >> ./meta/work/api-spec-remediation/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Completed
Task completed successfully.
Total duration: $(date -d "$(date -u +%Y-%m-%dT%H:%M:%SZ)" +%s -d "$START_TIME" +%s | awk '{print int(($1-$2)/60) " minutes"}')
EOF
```

**On Failure** — Append when task fails, before retrying:

```bash
cat >> ./meta/work/api-spec-remediation/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Failed
Error: ${ERROR_MESSAGE}
Will retry with: ${RETRY_STRATEGY}
EOF
```

**Journal Entries**: `./meta/work/api-spec-remediation/journal/YYYYMMDDTHHMMSSZ.md`

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
git log --reverse --pretty=format:'%H|%ad|%an|%s' --date=iso-strict > ./meta/work/api-spec-remediation/history/commits.txt
git log --reverse --name-status --pretty=format:'----%n%H|%ad|%s' > ./meta/work/api-spec-remediation/history/changes.txt
```

Generate summary at **`./meta/work/api-spec-remediation/SUMMARY.md`** containing phase timings, key decisions, and error patterns.

Commit all metadata:

```bash
git add ./meta/work/api-spec-remediation/
git commit -m "Archive work history for api-spec-remediation"
git tag -a "work-complete-api-spec-remediation" -m "Work history archived"
```

Merge to trunk using squash commit:

```bash
git checkout trunk
git merge --squash dev/api-spec-remediation
```

Write merge message to **`./.cache/tmp/api-spec-remediation/merge-commit.txt`**:

```
api-spec-remediation: Fix API specification compliance issues for release

Summary of changes:
- Add missing handler exports to main __init__.pyi
- Centralize type definitions in types.py
- Fix section organization in domain stub files
- Add API specification compliance tests

Work history preserved in ./meta/work/api-spec-remediation/
```

```bash
git commit -F ./.cache/tmp/api-spec-remediation/merge-commit.txt
rm ./.cache/tmp/api-spec-remediation/merge-commit.txt
```

Do not delete the **`dev/api-spec-remediation`** branch - it contains detailed commit history for future reference.

## Context

This remediation plan addresses issues discovered during a comprehensive review of the Observability package against the PyAPISpec.md standard. The review identified several compliance issues that could impact users' ability to properly use the package with type checking tools and understand the available API surface.

The most critical issue is that handler classes (PrintHandler, JsonHandler, etc.) are exported in the implementation's __init__.py but missing from __init__.pyi. This breaks the fundamental API contract - users cannot discover these handlers through type information, and type checkers will fail when importing them.

The second architectural issue involves type definitions being scattered across multiple stub files rather than centralized. Specifically, HandlerChain and HandlerPredicate are defined in handlers/__init__.pyi but should be in types.py. This violates the DRY principle and could lead to drift between definitions.

The domain stub files have section organization issues where items are placed in incorrect sections according to PyAPISpec.md:
- In logging.pyi, the severity constants (DEBUG, INFO, etc.) are placed before the Type Definitions section but should be within it
- In tracing.pyi, the current_span ContextVar is in the Type Definitions section but should be in Core Types as it's functional, not a type

These issues represent a mix of critical API contract violations and important organizational problems that should be fixed before release to ensure the package meets the quality standards established in PyAPISpec.md and provides a consistent, well-documented experience for users.

The remediation focuses only on stub file fixes and type organization, making no changes to the actual implementation to minimize risk. The four-phase approach ensures systematic correction with validation at each step, concluding with test infrastructure to prevent regression.