# observability-api-implementation Plan

This document details a plan to implement missing functionality in the observability framework to match the API specifications defined in the Python stub files.

## Goals, Outcomes & Success Criteria

The intent of this plan is to bridge the gap between the observability framework's API specifications (stub files) and its actual implementation, ensuring all promised functionality is available and working correctly.

At conclusion of this plan, the following outcomes should be seen:

- All methods defined in stub files are implemented and functional
- Property accessors replace direct attribute access where specified
- Method names follow snake_case convention as defined in stubs
- Handler constructors accept parameters as specified in stubs
- All examples run successfully without modification
- No divergence between API specification and implementation

To gauge your success of actualizing this plan, use the following success criteria:

- `python helpers/test_all_examples.py` shows 100% success rate
- `python scripts/validate_observability_examples.py` reports 0 functional divergences
- All unit tests pass (if they exist)
- Manual testing confirms each implemented feature works as specified
- Code follows existing patterns and conventions in the codebase

## Scope & Constraints

Scope your efforts to implementing only the missing functionality identified in the API vs implementation analysis. This includes adding missing methods, converting attributes to properties, updating method names, and aligning constructor signatures. Do not refactor existing working functionality unless required for the implementation. Focus on maintaining backward compatibility where possible while achieving API compliance.

Throughout your work, you should be mindful of your constraints. You MUST preserve existing functionality - ensure no regression in current behavior. You MUST follow the patterns established in the existing codebase for consistency. You SHOULD implement properties using Python's @property decorator. You MUST ensure thread safety where the existing code has it. You SHOULD add docstrings matching those in the stub files. You MUST NOT modify the stub files - they represent the contract. You CAN add deprecation warnings for old method names before removing them.

Throughout your efforts be mindful of the following:

- You MUST keep your working directory at the project root (i.e. `./`)
- You MUST adhere to the [Contributor's Guide](./CONTRIBUTOR.md) & the [Agent Guide](./AGENT.md)
- You SHOULD create Temporary Files under `./.cache/tmp/observability-api-implementation`
- You SHOULD record your efforts under `./meta/work/observability-api-implementation/`
  - This should include any subplans, summaries, commit messages or other general information regarding your efforts.
- You SHOULD use the Python venv at `./.venv`
- You MAY prompt the user for feedback, guidance or general help when ambiguity arises that you are unable to traverse.

## Procedures

The implementation will be completed in four phases: first implementing missing Logger functionality, then adding property accessors to domain objects, followed by updating handler constructor signatures, and finally validating all changes work correctly with the examples.

### Phase 1 — Logger API Implementation

**Summary** — Implement missing Logger methods and convert method names to snake_case while maintaining backward compatibility.

**Prerequisites** — Before beginning this phase, ensure:

- Access to `src/observability/domains/logging.py` and `src/observability/domains/logging.pyi`
- Understanding of current Logger implementation patterns
- All current tests (if any) pass

**Dependencies** — This phase depends on:

- No external dependencies
- Current Logger class implementation
- Python @property decorator functionality

**Tasks** — The following phase is composed of the following tasks:

- Add `min_level` property with getter and setter that wraps internal `_min_level` attribute
- Add `get_child()` method that calls existing `getChild()` internally
- Implement `is_enabled_for(level)` method that checks if level >= self._min_level
- Add deprecation warnings to `setLevel()` and `getChild()` methods
- Ensure thread safety is maintained for all new methods

**Project State** — At conclusion of this phase; the desired project state should be:

- Logger has working `min_level` property (getter and setter)
- Logger has `get_child()` method working identically to `getChild()`
- Logger has `is_enabled_for()` method properly checking log levels
- Deprecation warnings added to old methods
- All logger examples (10, 11, 74) pass tests

**Validation Criteria** — To confirm successful phase completion, validate:

- Run `python examples/observability/10_logging_basics.py` - should complete without errors
- Run `python examples/observability/11_logging_hierarchical.py` - should complete without errors
- Run `python examples/observability/74_logger_enabled_check.py` - should complete without errors
- Verify `logger.min_level = WARNING` works correctly
- Verify `logger.is_enabled_for(DEBUG)` returns correct boolean

**Validation Actions** — If validation fails:

- Check property decorator syntax and implementation
- Verify thread safety locks are properly applied
- Review error messages for missing imports or typos
- Test each method individually with simple test script
- Rollback changes and retry with simpler implementation

### Phase 2 — Domain Object Properties

**Summary** — Add property accessors for Span and Histogram objects to expose internal attributes as specified in stubs.

**Prerequisites** — Before beginning this phase, ensure:

- Phase 1 completed successfully
- Access to tracing and metrics domain modules
- Understanding of property patterns from Phase 1

**Dependencies** — This phase depends on:

- Successful Logger property implementation pattern
- Current Span and Histogram implementations
- No external dependencies

**Tasks** — The following phase is composed of the following tasks:

- Add `operation` property (readonly) to Span class exposing `_operation`
- Add `span_id` property (readonly) to Span class exposing `_span_id`
- Add `parent_id` property (readonly) to Span class exposing `_parent_id`
- Add `buckets` property (readonly) to Histogram class exposing `_buckets`
- Add `name` property (readonly) to Counter, Gauge, and Histogram classes

**Project State** — At conclusion of this phase; the desired project state should be:

- Span.operation property returns the operation name
- Span.span_id property returns the span ID
- Span.parent_id property returns the parent span ID
- Histogram.buckets property returns the bucket list
- All metric classes have .name property
- Examples 20, 32 pass tests

**Validation Criteria** — To confirm successful phase completion, validate:

- Run `python examples/observability/20_tracing_basics.py` - should complete without errors
- Run `python examples/observability/32_metrics_histogram.py` - should complete without errors
- Create test script verifying each property returns expected values
- Ensure properties are read-only (assignment raises AttributeError)

**Validation Actions** — If validation fails:

- Verify property is accessing correct internal attribute
- Check that @property decorator is applied correctly
- Ensure no typos in property names
- Test properties with direct attribute access comparison
- Add debug print statements to diagnose issues

### Phase 3 — Handler Constructor Alignment

**Summary** — Update QueuedHandler and JsonHandler constructors to match stub specifications while maintaining backward compatibility.

**Prerequisites** — Before beginning this phase, ensure:

- Phases 1-2 completed successfully
- Access to handlers module implementation
- Understanding of current handler usage patterns

**Dependencies** — This phase depends on:

- Current handler implementations
- Understanding of parameter compatibility requirements
- Examples using these handlers

**Tasks** — The following phase is composed of the following tasks:

- Update QueuedHandler to accept both `wrapped` and `wrapped_handler` parameters
- Map `queue_size` parameter to `max_queued` internally
- Update JsonHandler to accept `indent` and `sort_keys` parameters
- Map JsonHandler parameters to existing `pretty` functionality
- Ensure backward compatibility for existing parameter names

**Project State** — At conclusion of this phase; the desired project state should be:

- QueuedHandler accepts `wrapped_handler` as parameter alias for `wrapped`
- QueuedHandler accepts `queue_size` as parameter alias for `max_queued`
- JsonHandler accepts `indent` parameter (None or int)
- JsonHandler accepts `sort_keys` boolean parameter
- Examples 44, 73, 75, 77 pass tests
- Existing code using old parameters still works

**Validation Criteria** — To confirm successful phase completion, validate:

- Run `python examples/observability/44_handler_queued.py` - should complete without errors
- Run examples 73, 75, 77 successfully
- Verify both old and new parameter names work
- Check JsonHandler produces properly formatted output with indent

**Validation Actions** — If validation fails:

- Check constructor parameter handling logic
- Verify parameter mapping is correct
- Test with both positional and keyword arguments
- Review error messages for parameter conflicts
- Ensure **kwargs handling doesn't break functionality

### Phase 4 — Final Integration and Testing

**Summary** — Export missing constants, run comprehensive tests, and ensure all examples work correctly.

**Prerequisites** — Before beginning this phase, ensure:

- Phases 1-3 completed successfully
- All individual components tested
- Understanding of module exports

**Dependencies** — This phase depends on:

- All previous phase implementations
- Example test runner functionality
- Complete API implementation

**Tasks** — The following phase is composed of the following tasks:

- Export DEFAULT_BUCKETS from metrics module __init__.py
- Run complete example test suite
- Fix any remaining issues discovered
- Update any deprecation warnings or compatibility shims
- Document any implementation decisions or limitations

**Project State** — At conclusion of this phase; the desired project state should be:

- All 47 examples run successfully
- API validation shows no functional divergences
- DEFAULT_BUCKETS importable from observability.domains.metrics
- All functionality matches stub specifications
- Implementation is thread-safe and backward compatible

**Validation Criteria** — To confirm successful phase completion, validate:

- Run `python helpers/test_all_examples.py` - 100% success rate
- Run `python scripts/validate_observability_examples.py` - 0 functional divergences
- Import and use all newly implemented features in test script
- Verify no regression in existing functionality
- Check performance is not significantly impacted

**Validation Actions** — If validation fails:

- Review specific failing examples for root cause
- Check for missing imports or exports
- Verify thread safety in concurrent tests
- Test each feature in isolation
- Review implementation against stub specifications

## Work Process

### Git Branch Management

Create and switch to branch **`dev/observability-api-implementation`**:

```bash
git switch -c dev/observability-api-implementation
```

All work must occur on this branch.

**Committing Changes**

Commit changes using precise pathspecs. Write file paths to **`./.cache/tmp/observability-api-implementation/pathspec.txt`**, one per line. Write descriptive commit messages to **`./.cache/tmp/observability-api-implementation/commit.txt`** using present tense.

```bash
git add --pathspec-from-file=./.cache/tmp/observability-api-implementation/pathspec.txt
git commit --pathspec-from-file=./.cache/tmp/observability-api-implementation/pathspec.txt -F ./.cache/tmp/observability-api-implementation/commit.txt
rm ./.cache/tmp/observability-api-implementation/pathspec.txt ./.cache/tmp/observability-api-implementation/commit.txt
```

### Work Recording

Track progress through append-only task files and contextual journal entries.

**Task Files**: `./meta/work/observability-api-implementation/tasks/PhaseNN-TaskMMM.md`

Create a new file when starting each task, then append entries as events occur.

**On Start** — Create the file when beginning a task:

```bash
cat > ./meta/work/observability-api-implementation/tasks/Phase01-Task001.md << EOF
# Phase 01 - Task 001: ${TASK_NAME}

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Started
Attempts: 1
Beginning ${TASK_DESCRIPTION}.
EOF
```

**On Update** — Append after each commit, milestone reached, or issue encountered:

```bash
cat >> ./meta/work/observability-api-implementation/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Progress
${UPDATE_DESCRIPTION}
Commit: $(git rev-parse --short HEAD) "$(git log -1 --pretty=%s)"
EOF
```

**On Completion** — Append once when task succeeds:

```bash
START_TIME=$(grep "Started" ./meta/work/observability-api-implementation/tasks/Phase01-Task001.md | head -1 | cut -d' ' -f2)
cat >> ./meta/work/observability-api-implementation/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Completed
Task completed successfully.
Total duration: $(date -d "$(date -u +%Y-%m-%dT%H:%M:%SZ)" +%s -d "$START_TIME" +%s | awk '{print int(($1-$2)/60) " minutes"}')
EOF
```

**On Failure** — Append when task fails, before retrying:

```bash
cat >> ./meta/work/observability-api-implementation/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Failed
Error: ${ERROR_MESSAGE}
Will retry with: ${RETRY_STRATEGY}
EOF
```

**Journal Entries**: `./meta/work/observability-api-implementation/journal/YYYYMMDDTHHMMSSZ.md`

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
git log --reverse --pretty=format:'%H|%ad|%an|%s' --date=iso-strict > ./meta/work/observability-api-implementation/history/commits.txt
git log --reverse --name-status --pretty=format:'----%n%H|%ad|%s' > ./meta/work/observability-api-implementation/history/changes.txt
```

Generate summary at **`./meta/work/observability-api-implementation/SUMMARY.md`** containing phase timings, key decisions, and error patterns.

Commit all metadata:

```bash
git add ./meta/work/observability-api-implementation/
git commit -m "Archive work history for observability-api-implementation"
git tag -a "work-complete-observability-api-implementation" -m "Work history archived"
```

Merge to trunk using squash commit:

```bash
git checkout trunk
git merge --squash dev/observability-api-implementation
```

Write merge message to **`./.cache/tmp/observability-api-implementation/merge-commit.txt`**:

```
observability-api-implementation: Implement missing functionality in the observability framework to match the API specifications defined in the Python stub files

Summary of changes:
- Add missing Logger methods: min_level property, get_child(), is_enabled_for()
- Add property accessors to Span and Histogram classes
- Update handler constructors to match API specifications
- Export DEFAULT_BUCKETS from metrics module
- Maintain backward compatibility with deprecation warnings

Work history preserved in ./meta/work/observability-api-implementation/
```

```bash
git commit -F ./.cache/tmp/observability-api-implementation/merge-commit.txt
rm ./.cache/tmp/observability-api-implementation/merge-commit.txt
```

Do not delete the **`dev/observability-api-implementation`** branch - it contains detailed commit history for future reference.

## Context

The observability framework has a significant disconnect between its API specifications (defined in .pyi stub files) and its actual implementation. This plan addresses these specific gaps:

**Logger API Mismatches:**
- The stub defines `min_level` as a property, but implementation has `setLevel()` method
- The stub defines `get_child()` method, but implementation has `getChild()`  
- The stub defines `is_enabled_for()` method, but it's not implemented
- These affect examples 10, 11, 63, 74

**Domain Object Properties:**
- Span class has internal `_operation`, `_span_id`, `_parent_id` but no property accessors
- Histogram class has internal `_buckets` but no property accessor
- Metric classes lack `name` property accessor
- These affect examples 20, 32

**Handler Constructor Mismatches:**
- QueuedHandler expects `wrapped` but stub defines `wrapped_handler`
- QueuedHandler expects `max_queued` but stub defines `queue_size`
- JsonHandler has completely different parameters than stub (pretty/ensure_ascii vs indent/sort_keys)
- These affect examples 44, 73, 75, 77

**Missing Exports:**
- DEFAULT_BUCKETS exists in Histogram class but isn't exported from metrics module
- This affects example 75

The implementation follows different conventions (camelCase vs snake_case) and design decisions than specified in the stubs. This plan implements the missing functionality while maintaining backward compatibility through deprecation warnings and parameter aliasing. The goal is to achieve 100% example success rate and full API compliance without breaking existing code.