# api-test-coverage Plan

This document details a plan to ensure comprehensive test coverage for all exported API elements defined in the observability package stub files.

## Goals, Outcomes & Success Criteria

The intent of this plan is to achieve 100% test coverage for all public API elements exported in the .pyi stub files, ensuring that every documented API behavior is validated through automated tests.

At conclusion of this plan, the following outcomes should be seen:

- All exported classes, methods, functions, and constants from stub files have corresponding tests
- Tests validate both successful usage patterns and error conditions
- API contracts defined in stubs are enforced through test assertions
- Test documentation clearly maps to API specifications
- No untested public API surface remains

To gauge your success of actualizing this plan, use the following success criteria:

- Every exported element in .pyi files has at least one test case
- All test files pass with 100% success rate
- Code coverage for API elements reaches 100%
- Test names clearly indicate which API element they validate
- Error handling paths are tested for all applicable APIs

## Scope & Constraints

Scope your efforts to testing only the public API elements that are exported in the .pyi stub files. Focus on behavioral testing rather than implementation details. Tests should validate that the implementation matches the documented API contracts. Do not test private methods or internal implementation details. Prioritize testing the most critical APIs first (those used most frequently in examples and integration tests).

Throughout your work, you should be mindful of your constraints. You MUST only test against the public API as defined in the stub files. You MUST NOT modify any existing API implementations. You SHOULD write tests that are independent and can run in any order. You SHOULD follow existing test patterns and conventions in the codebase. You MUST ensure all new tests are deterministic and do not depend on external resources or timing.

Throughout your efforts be mindful of the following:

- You MUST keep your working directory at the project root (i.e. `./`)
- You MUST adhere to the [Contributor's Guide](./CONTRIBUTOR.md) & the [Agent Guide](./AGENT.md)
- You SHOULD create Temporary Files under `./.cache/tmp/api-test-coverage`
- You SHOULD record your efforts under `./meta/work/api-test-coverage/`
  - This should include any subplans, summaries, commit messages or other general information regarding your efforts.
- You SHOULD use the Python venv at `./.venv`
- You MAY prompt the user for feedback, guidance or general help when ambiguity arises that you are unable to traverse.

## Procedures

The plan involves systematically reviewing each stub file to identify untested API elements, then creating focused test cases that validate the documented behavior. Tests will be organized by API domain and will include both positive and negative test cases where applicable.

### Phase 1 — API Test Gap Analysis

**Summary** — Conduct a comprehensive audit of all exported API elements and their current test coverage to identify gaps.

**Prerequisites** — Before beginning this phase, ensure:

- All stub files (.pyi) are accessible and up to date
- Test suite is running successfully with current tests
- Development environment is properly configured

**Dependencies** — This phase depends on:

- Access to all .pyi stub files in src/observability/
- Existing test suite in tests/
- grep and analysis tools for code inspection

**Tasks** — The following phase is composed of the following tasks:

- Create a comprehensive inventory of all exported API elements from each stub file
- Map existing tests to their corresponding API elements
- Identify API elements without test coverage
- Prioritize missing tests by importance and usage frequency
- Document findings in a gap analysis report

**Project State** — At conclusion of this phase; the desired project state should be:

- Complete API inventory documented at `./meta/work/api-test-coverage/api-inventory.md`
- Test coverage gap analysis report at `./meta/work/api-test-coverage/gap-analysis.md`
- Prioritized list of tests to implement

**Validation Criteria** — To confirm successful phase completion, validate:

- API inventory includes every exported element from all .pyi files
- Each API element is marked as tested or untested
- Gap analysis identifies specific test files and functions needed

**Validation Actions** — If validation fails:

- Re-scan stub files for missed exports
- Cross-reference with import statements in test files
- Document any ambiguous cases for user clarification

### Phase 2 — Core API Test Implementation

**Summary** — Implement missing tests for core API elements in the main observability module and SharedContext.

**Prerequisites** — Before beginning this phase, ensure:

- Phase 1 gap analysis is complete
- Test file structure is understood
- Core API documentation is available

**Dependencies** — This phase depends on:

- Gap analysis from Phase 1
- Access to observability/__init__.pyi
- Existing test patterns in test_core_functionality.py

**Tasks** — The following phase is composed of the following tasks:

- Add tests for SharedContext.start() and stop() methods
- Create explicit tests for type alias usage (EventDict, EventHandler, ContextProvider)
- Ensure all ObservabilityContext methods have error case tests
- Validate configuration edge cases

**Project State** — At conclusion of this phase; the desired project state should be:

- New test file `tests/test_observability/core/test_api_completeness.py` created
- All core API elements have corresponding tests
- Tests pass successfully

**Validation Criteria** — To confirm successful phase completion, validate:

- pytest runs successfully with new tests
- Coverage report shows 100% for core API elements
- No untested exports remain in observability/__init__.pyi

**Validation Actions** — If validation fails:

- Debug failing tests and fix issues
- Add missing test cases identified during validation
- Re-run coverage analysis

### Phase 3 — Handler Protocol Test Implementation  

**Summary** — Implement tests for handler protocols and type aliases to ensure contract compliance.

**Prerequisites** — Before beginning this phase, ensure:

- Phase 2 is complete
- Handler stub file structure is understood
- Protocol testing patterns are identified

**Dependencies** — This phase depends on:

- Access to handlers/__init__.pyi
- Understanding of Python Protocol testing
- Existing handler implementations

**Tasks** — The following phase is composed of the following tasks:

- Create protocol compliance tests for LifecycleHandler and ManagedHandler
- Add tests validating HandlerChain and HandlerPredicate type aliases
- Ensure all handler classes properly implement their protocols
- Test protocol runtime checking with isinstance()

**Project State** — At conclusion of this phase; the desired project state should be:

- New test file `tests/test_observability/handlers/test_protocols.py` created
- All handler protocols have compliance tests
- Type alias usage is validated

**Validation Criteria** — To confirm successful phase completion, validate:

- All protocols have at least one positive and one negative test
- Runtime protocol checking works correctly
- Type aliases are used correctly in tests

**Validation Actions** — If validation fails:

- Review Protocol documentation for proper testing approach
- Add additional test cases for edge conditions
- Verify protocol implementations match specifications

### Phase 4 — Domain API Test Completion

**Summary** — Complete test coverage for all domain-specific APIs including missing Logger, Span, and Histogram methods.

**Prerequisites** — Before beginning this phase, ensure:

- Previous phases are complete
- Domain stub files are reviewed
- Existing domain tests are understood

**Dependencies** — This phase depends on:

- Access to all domain .pyi files
- Understanding of domain-specific behaviors
- Existing test patterns in domain test files

**Tasks** — The following phase is composed of the following tasks:

- Add tests for Logger.is_enabled_for() method
- Implement Span.set_status() test cases with success/failure scenarios
- Create Span.add_event() tests with various event types
- Validate Histogram.DEFAULT_BUCKETS constant
- Ensure all domain APIs have comprehensive tests

**Project State** — At conclusion of this phase; the desired project state should be:

- Updated domain test files with missing test cases
- All domain API elements have test coverage
- Tests demonstrate both successful and error scenarios

**Validation Criteria** — To confirm successful phase completion, validate:

- All identified gaps from Phase 1 are addressed
- Domain tests pass successfully
- Coverage reports show 100% for domain APIs

**Validation Actions** — If validation fails:

- Identify specific untested code paths
- Add additional test scenarios
- Review domain documentation for missed behaviors

### Phase 5 — Integration and Validation

**Summary** — Validate complete API test coverage and create comprehensive test documentation.

**Prerequisites** — Before beginning this phase, ensure:

- All previous phases are complete
- All new tests pass successfully
- Coverage tools are configured

**Dependencies** — This phase depends on:

- Completed tests from all previous phases
- pytest and coverage tools
- API documentation

**Tasks** — The following phase is composed of the following tasks:

- Run full test suite with coverage analysis
- Generate API test coverage report
- Create test documentation mapping tests to API elements
- Validate no exported APIs remain untested
- Document any design decisions or test patterns

**Project State** — At conclusion of this phase; the desired project state should be:

- 100% test coverage for all exported API elements
- Complete test documentation at `./meta/work/api-test-coverage/test-mapping.md`
- All tests passing in CI/CD pipeline

**Validation Criteria** — To confirm successful phase completion, validate:

- Coverage report shows no untested exported APIs
- Test mapping document is complete and accurate
- All tests are deterministic and reliable

**Validation Actions** — If validation fails:

- Re-run gap analysis to find missed APIs
- Debug flaky or failing tests
- Update documentation with findings

## Work Process

### Git Branch Management

Create and switch to branch **`dev/api-test-coverage`**:

```bash
git switch -c dev/api-test-coverage
```

All work must occur on this branch.

**Committing Changes**

Commit changes using precise pathspecs. Write file paths to **`./.cache/tmp/api-test-coverage/pathspec.txt`**, one per line. Write descriptive commit messages to **`./.cache/tmp/api-test-coverage/commit.txt`** using present tense.

```bash
git add --pathspec-from-file=./.cache/tmp/api-test-coverage/pathspec.txt
git commit --pathspec-from-file=./.cache/tmp/api-test-coverage/pathspec.txt -F ./.cache/tmp/api-test-coverage/commit.txt
rm ./.cache/tmp/api-test-coverage/pathspec.txt ./.cache/tmp/api-test-coverage/commit.txt
```

### Work Recording

Track progress through append-only task files and contextual journal entries.

**Task Files**: `./meta/work/api-test-coverage/tasks/PhaseNN-TaskMMM.md`

Create a new file when starting each task, then append entries as events occur.

**On Start** — Create the file when beginning a task:

```bash
cat > ./meta/work/api-test-coverage/tasks/Phase01-Task001.md << EOF
# Phase 01 - Task 001: ${TASK_NAME}

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Started
Attempts: 1
Beginning ${TASK_DESCRIPTION}.
EOF
```

**On Update** — Append after each commit, milestone reached, or issue encountered:

```bash
cat >> ./meta/work/api-test-coverage/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Progress
${UPDATE_DESCRIPTION}
Commit: $(git rev-parse --short HEAD) "$(git log -1 --pretty=%s)"
EOF
```

**On Completion** — Append once when task succeeds:

```bash
START_TIME=$(grep "Started" ./meta/work/api-test-coverage/tasks/Phase01-Task001.md | head -1 | cut -d' ' -f2)
cat >> ./meta/work/api-test-coverage/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Completed
Task completed successfully.
Total duration: $(date -d "$(date -u +%Y-%m-%dT%H:%M:%SZ)" +%s -d "$START_TIME" +%s | awk '{print int(($1-$2)/60) " minutes"}')
EOF
```

**On Failure** — Append when task fails, before retrying:

```bash
cat >> ./meta/work/api-test-coverage/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Failed
Error: ${ERROR_MESSAGE}
Will retry with: ${RETRY_STRATEGY}
EOF
```

**Journal Entries**: `./meta/work/api-test-coverage/journal/YYYYMMDDTHHMMSSZ.md`

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
git log --reverse --pretty=format:'%H|%ad|%an|%s' --date=iso-strict > ./meta/work/api-test-coverage/history/commits.txt
git log --reverse --name-status --pretty=format:'----%n%H|%ad|%s' > ./meta/work/api-test-coverage/history/changes.txt
```

Generate summary at **`./meta/work/api-test-coverage/SUMMARY.md`** containing phase timings, key decisions, and error patterns.

Commit all metadata:

```bash
git add ./meta/work/api-test-coverage/
git commit -m "Archive work history for api-test-coverage"
git tag -a "work-complete-api-test-coverage" -m "Work history archived"
```

Merge to trunk using squash commit:

```bash
git checkout trunk
git merge --squash dev/api-test-coverage
```

Write merge message to **`./.cache/tmp/api-test-coverage/merge-commit.txt`**:

```
api-test-coverage: Ensure comprehensive test coverage for all exported API elements defined in the observability package stub files

Summary of changes:
- Added missing tests for SharedContext methods
- Implemented protocol compliance tests for handlers
- Completed domain API test coverage
- Created comprehensive test documentation

Work history preserved in ./meta/work/api-test-coverage/
```

```bash
git commit -F ./.cache/tmp/api-test-coverage/merge-commit.txt
rm ./.cache/tmp/api-test-coverage/merge-commit.txt
```

Do not delete the **`dev/api-test-coverage`** branch - it contains detailed commit history for future reference.

## Context

This plan addresses the gap identified during the API specification remediation work where several exported API elements lack test coverage. The analysis revealed that while the implementation has been aligned with the API specifications, several public methods and protocols defined in the stub files do not have corresponding tests.

Key gaps identified include:
- SharedContext.start() and stop() methods
- Handler protocols (LifecycleHandler, ManagedHandler) and type aliases
- Logger.is_enabled_for() method
- Span.set_status() and add_event() methods
- Histogram.DEFAULT_BUCKETS constant

These missing tests represent important API surface area that should be covered to ensure the implementation continues to match the stub specifications as the codebase evolves. The tests will serve as both validation and documentation of expected API behavior.