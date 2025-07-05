# observability-api-alignment Plan

This document details a plan to align all observability examples with the defined API specifications in the Python stub files and extend examples to demonstrate all API functionality.

## Goals, Outcomes & Success Criteria

The intent of this plan is to ensure complete API compliance across all observability examples while providing comprehensive demonstration of every API feature defined in the stub files.

At conclusion of this plan, the following outcomes should be seen:

- All 72 existing examples correctly use API methods, parameters, and patterns as defined in stub files
- New examples created to demonstrate previously unused API functionality
- Zero divergences between example usage and API specifications
- Complete API coverage with at least one example per public method/class
- Updated README documenting API coverage matrix

To gauge your success of actualizing this plan, use the following success criteria:

- Automated validation script confirms 100% API compliance across all examples
- Every public API method has at least one example demonstrating its usage
- All examples execute without errors or warnings
- API coverage report shows no gaps in demonstration
- Code review confirms examples follow best practices from stub documentation

## Scope & Constraints

Scope your efforts to the observability package examples under `./examples/observability/` and their alignment with API specifications in `./src/observability/**/*.pyi` files. Focus on correcting existing examples first, then creating new examples only for API gaps. Maintain backward compatibility of example numbering scheme. Do not modify the stub files or core implementation - only update examples to match the defined API.

Throughout your work, you should be mindful of your constraints. You MUST preserve the existing example numbering scheme (01-72). You MUST maintain the progressive learning path structure. You SHOULD create new examples starting from number 73 for additional API coverage. You MUST NOT modify any stub files or core implementation code. You SHOULD preserve helpful comments that explain concepts, even when fixing API usage. You MUST ensure all examples remain executable and demonstrate their intended concepts clearly.

Throughout your efforts be mindful of the following:

- You MUST keep your working directory at the project root (i.e. `./`).
- You MUST adhere to the [Contributor's Guide](./CONTRIBUTOR.md) & the [Agent Guide](./AGENT.md)
- You SHOULD create Temporary Files under `./.cache/tmp/observability-api-alignment`
- You SHOULD record your efforts under `./meta/work/observability-api-alignment/`
  - This should include any subplans, summaries, commit messages or other general information regarding your efforts.
- You SHOULD use the Python venv at `./.venv`.
- You MAY prompt the user for feedback, guidance or general help when ambiguity arises that you are unable to traverse.

## Procedures

This plan systematically aligns observability examples with API specifications through automated validation, targeted fixes, and comprehensive gap coverage. The process begins with building validation tools, proceeds through methodical correction of existing examples, and concludes with creating new examples for complete API demonstration.

### Phase 1 — Validation Infrastructure

**Summary** — Build automated validation tools to detect and report API divergences between examples and stub specifications.

**Prerequisites** — Before beginning this phase, ensure:

- Python stub files are accessible at `./src/observability/**/*.pyi`
- Example files are accessible at `./examples/observability/*.py`
- Python AST module is available for code parsing
- Write permissions for `./.cache/tmp/observability-api-alignment/`

**Dependencies** — This phase depends on:

- Python standard library (ast, re, pathlib)
- Access to both stub files and example files
- No external packages required

**Tasks** — The following phase is composed of the following tasks:

- Create AST parser extracting from stub files: class names, method signatures, parameter names/types/defaults, return types, property definitions
- Build example analyzer identifying: import statements, class instantiations with arguments, method calls with parameters, property access patterns
- Implement divergence detector checking: method name exact matches, parameter count and ordering, keyword vs positional usage, property getter/setter patterns
- Generate JSON divergence report with structure: `{"file": "01_basic_setup.py", "line": 42, "type": "method_name", "found": "getChild", "expected": "get_child"}`
- Create Markdown API coverage matrix listing: every class/method from stubs, example files using each, coverage percentage per module

**Project State** — At conclusion of this phase; the desired project state should be:

- Validation script at `./scripts/validate_observability_examples.py` with main() function
- Divergence report at `./.cache/tmp/observability-api-alignment/divergence_report.json` containing all issues
- API coverage matrix at `./.cache/tmp/observability-api-alignment/api_coverage.md` in table format
- Summary statistics: total divergences by type, API coverage percentage, affected files list

**Validation Criteria** — To confirm successful phase completion, validate:

- Script executes: `python ./scripts/validate_observability_examples.py` without errors
- JSON report contains entries matching known issues: getChild, setLevel, filtered parameter order
- Coverage matrix shows < 100% coverage for: add_event(), set_status(), is_enabled_for()
- Script processes all 72 examples in under 10 seconds

**Validation Actions** — If validation fails:

- Add debug output showing parsed AST nodes
- Test parser on single file: `10_logging_basics.py`
- Verify stub parsing extracts: `get_child(self, suffix: str) -> "Logger"`
- Compare manual count of divergences with report total

### Phase 2 — Method and Property Corrections

**Summary** — Fix all method naming inconsistencies and property access patterns across existing examples.

**Prerequisites** — Before beginning this phase, ensure:

- Divergence report from Phase 1 is complete at `./.cache/tmp/observability-api-alignment/divergence_report.json`
- Backup created: `cp -r ./examples/observability ./examples/observability.backup`
- Divergence report shows entries for: getChild, setLevel, _operation

**Dependencies** — This phase depends on:

- Completed divergence analysis from Phase 1
- Write access to example files
- Validation script for verification

**Tasks** — The following phase is composed of the following tasks:

- In files `11_logging_hierarchical.py`, `12_logging_structured.py`: Replace `root_logger.getChild("database")` with `root_logger.get_child("database")`
- In files `10_logging_basics.py`, `11_logging_hierarchical.py`: Replace `logger.setLevel(WARNING)` with `logger.min_level = WARNING`
- In file `20_tracing_basics.py` line ~35: Replace `span._operation` with `span.operation`
- In file `10_logging_basics.py`: Remove or comment out `is_enabled_for()` usage with note "Method not available in current implementation"
- Search all files for pattern `\._[a-zA-Z]` and replace with public property access

**Project State** — At conclusion of this phase; the desired project state should be:

- Zero occurrences of `getChild` in any example file
- Zero occurrences of `setLevel` in any example file  
- Zero occurrences of underscore-prefixed attribute access
- All property access uses public interfaces defined in stubs

**Validation Criteria** — To confirm successful phase completion, validate:

- Execute: `grep -r "getChild" ./examples/observability/` returns no results
- Execute: `grep -r "setLevel" ./examples/observability/` returns no results
- Execute: `grep -r "\._[a-zA-Z]" ./examples/observability/` returns no results
- Run corrected examples 10, 11, 20 without AttributeError

**Validation Actions** — If validation fails:

- Check exact error message from failed example
- Verify property exists in implementation: `hasattr(logger, 'min_level')`
- Add compatibility comment if implementation differs from stub
- Document divergence in `./.cache/tmp/observability-api-alignment/implementation_notes.md`

### Phase 3 — Parameter and Constructor Alignment

**Summary** — Correct all parameter ordering issues and constructor patterns to match API specifications.

**Prerequisites** — Before beginning this phase, ensure:

- Method naming corrections from Phase 2 are complete and committed
- File `./src/observability/handlers/__init__.pyi` accessible showing `filtered(predicate: HandlerPredicate, handler: EventHandler)`
- Examples 45, 46, 48 identified as having filtered() ordering issues

**Dependencies** — This phase depends on:

- Completed Phase 2 corrections
- Stub file parameter signatures
- Example execution environment

**Tasks** — The following phase is composed of the following tasks:

- In files using `filtered()` - Find pattern `filtered\s*\(\s*([^,]+),\s*lambda` and swap arguments to `filtered(lambda`
- In `44_handler_queued.py` - Change `QueuedHandler(slow_handler)` to `QueuedHandler(wrapped_handler=slow_handler)`
- In `30_metrics_counter.py` - Change `Counter(..., labels={"service": "api"})` to `Counter(..., service="api")` 
- In `33_metrics_timer.py` - Replace `histogram.time()` calls with `Timer(histogram, **labels)` context manager
- In all handler constructors - Convert positional args to keyword: `PrintHandler(sys.stdout)` to `PrintHandler(stream=sys.stdout)`

**Project State** — At conclusion of this phase; the desired project state should be:

- All `filtered()` calls match signature: `filtered(predicate_function, wrapped_handler)`
- All handler constructors use explicit keyword arguments
- Metric static labels passed as kwargs: `Counter("name", context, unit="1", service="api")`  
- Timer class imported and used: `from observability.domains.metrics import Timer`

**Validation Criteria** — To confirm successful phase completion, validate:

- Pattern search: `grep -E "filtered\([^,]+Handler" ./examples/observability/*.py` returns no matches
- All QueuedHandler instantiations use `wrapped_handler=` keyword
- No dict passed as labels parameter to metric constructors
- Timer class usage verified in example 33

**Validation Actions** — If validation fails:

- Print actual vs expected constructor signature
- Run example with both patterns to verify functionality
- Check if keyword argument names match stub exactly
- Add inline comment explaining the correction

### Phase 4 — Event Structure Standardization

**Summary** — Standardize event structures and emission patterns to match API expectations.

**Prerequisites** — Before beginning this phase, ensure:

- Parameter corrections from Phase 3 complete and tested
- Understanding that metric events should have 'name' not in 'value' field
- Example 23 identified as needing add_event() implementation

**Dependencies** — This phase depends on:

- Completed Phase 3 corrections
- Event structure specifications from stubs
- BufferHandler for event inspection

**Tasks** — The following phase is composed of the following tasks:

- In metric examples 30-32: Verify event structure has metric name as separate field, not embedded in 'value'
- In `23_tracing_events.py`: Replace manual `context.emit()` calls with `span.add_event("event_name", {"key": "value"})`
- In `47_handler_timedelta.py`: Replace references to `event['delta_ns']` with `event['time_delta_ns']`
- In span examples: Replace `span.set_attribute("status", "success")` with `span.set_status(True, "Success message")`
- Update all event inspection code expecting 'value' to contain structured data

**Project State** — At conclusion of this phase; the desired project state should be:

- All span events use `add_event()` method for custom events
- All span status updates use `set_status()` method
- Event field names match API: `time_delta_ns` not `delta_ns`
- Metric events have clear 'name' field separate from 'value'

**Validation Criteria** — To confirm successful phase completion, validate:

- Example 23 contains at least 3 `span.add_event()` calls
- No manual `context.emit()` calls for span-specific events in tracing examples
- Pattern `delta_ns` not found in any Python example file
- All `set_status()` calls use boolean first parameter

**Validation Actions** — If validation fails:

- Capture actual event structure with BufferHandler
- Compare event fields against expected structure
- Add debug print showing event dictionary keys
- Document any implementation-specific event fields

### Phase 5 — API Gap Coverage

**Summary** — Create new examples demonstrating all previously unused API functionality.

**Prerequisites** — Before beginning this phase, ensure:

- API coverage matrix shows gaps for: `add_event()`, `set_status()`, `is_enabled_for()`, Timer class
- All existing examples (01-72) are API-compliant
- Directory `./examples/observability/` has write permissions

**Dependencies** — This phase depends on:

- Completed corrections from Phases 1-4
- Complete API coverage analysis
- Understanding of example organization

**Tasks** — The following phase is composed of the following tasks:

- Create `73_span_events_status.py` demonstrating:
  ```python
  with Span("payment_process", context) as span:
      span.add_event("payment_initiated", {"amount": 99.99, "currency": "USD"})
      # process payment
      span.add_event("payment_authorized", {"auth_code": "ABC123"})
      span.set_status(True, "Payment completed successfully")
  ```
- Create `74_logger_enabled_check.py` demonstrating:
  ```python
  if logger.is_enabled_for(DEBUG):
      expensive_data = compute_expensive_debug_info()
      logger.debug("Debug info", data=expensive_data)
  ```
- Create `75_timer_proper_usage.py` demonstrating:
  ```python
  from observability.domains.metrics import Timer, Histogram
  histogram = Histogram("operation_duration", context)
  with Timer(histogram, operation="database_query", table="users"):
      results = query_database()
  ```
- Create `76_handler_protocols.py` implementing ManagedHandler protocol
- Create `77_static_labels_pattern.py` showing: `Counter("requests", context, service="api", environment="prod")`

**Project State** — At conclusion of this phase; the desired project state should be:

- Files 73-77 exist in `./examples/observability/`
- Each file has docstring explaining API feature demonstrated
- All new examples execute without errors
- API coverage matrix updated to show 100% coverage

**Validation Criteria** — To confirm successful phase completion, validate:

- Each new example file exists and is >50 lines with proper docstring
- Running `python ./examples/observability/73_span_events_status.py` succeeds
- API coverage report shows no remaining gaps
- New examples follow existing naming and structure patterns

**Validation Actions** — If validation fails:

- Check if API method exists in implementation
- Verify import paths are correct
- Test simplified version of example
- Mark as "Not Implemented" if API doesn't exist

### Phase 6 — Documentation and Finalization

**Summary** — Update all documentation, create final validation reports, and ensure long-term maintainability.

**Prerequisites** — Before beginning this phase, ensure:

- All 77 examples are corrected and execute successfully
- Validation script shows 0 divergences and 100% API coverage
- Git history contains all corrections from Phases 1-5

**Dependencies** — This phase depends on:

- Completed Phases 1-5
- All examples in final form
- Validation infrastructure functional

**Tasks** — The following phase is composed of the following tasks:

- Update `./examples/observability/README.md` by appending new examples section:
  ```markdown
  ### Extended API Coverage (73-77)
  | Example | Description | Key API Features |
  |---------|-------------|------------------|
  | 73_span_events_status.py | Span events and status | add_event(), set_status() |
  | 74_logger_enabled_check.py | Conditional logging | is_enabled_for() |
  | 75_timer_proper_usage.py | Timer measurement | Timer class |
  | 76_handler_protocols.py | Protocol implementation | ManagedHandler |
  | 77_static_labels_pattern.py | Metric static labels | kwargs labels |
  ```
- Create migration guide at `./docs/observability/migration_guide.md` with sections:
  - Method Renames: `getChild() → get_child()`, `setLevel() → min_level = `
  - Parameter Order: `filtered(handler, pred) → filtered(pred, handler)`
  - Event Structure Changes: field name mappings
- Generate final report: `python ./scripts/validate_observability_examples.py --report=final > ./meta/work/observability-api-alignment/final_report.txt`
- Add validation to CI by creating `.github/workflows/validate-observability.yml`
- Create `./docs/observability/maintainer_notes.md` documenting validation process

**Project State** — At conclusion of this phase; the desired project state should be:

- README contains complete example index with API coverage
- Migration guide helps users update their code
- CI/CD runs validation on every PR
- Final report shows 0 divergences, 100% coverage
- All documentation committed to repository

**Validation Criteria** — To confirm successful phase completion, validate:

- README table includes all 77 examples with descriptions
- Migration guide contains before/after code examples
- CI workflow file exists and has correct Python path
- Final report shows: "Total Divergences: 0", "API Coverage: 100%"

**Validation Actions** — If validation fails:

- Review documentation for missing examples
- Test CI workflow in fork first
- Regenerate report after any fixes
- Get user feedback on documentation clarity

## Work Process

### Git Branch Management

Create and switch to branch **`dev/observability-api-alignment`**:

```bash
git switch -c dev/observability-api-alignment
```

All work must occur on this branch.

**Committing Changes**

Commit changes using precise pathspecs. Write file paths to **`./.cache/tmp/observability-api-alignment/pathspec.txt`**, one per line. Write descriptive commit messages to **`./.cache/tmp/observability-api-alignment/commit.txt`** using present tense.

```bash
git add --pathspec-from-file=./.cache/tmp/observability-api-alignment/pathspec.txt
git commit --pathspec-from-file=./.cache/tmp/observability-api-alignment/pathspec.txt -F ./.cache/tmp/observability-api-alignment/commit.txt
rm ./.cache/tmp/observability-api-alignment/pathspec.txt ./.cache/tmp/observability-api-alignment/commit.txt
```

### Work Recording

Track progress through append-only task files and contextual journal entries.

**Task Files**: `./meta/work/observability-api-alignment/tasks/PhaseNN-TaskMMM.md`

Create a new file when starting each task, then append entries as events occur.

**On Start** — Create the file when beginning a task:

```bash
cat > ./meta/work/observability-api-alignment/tasks/Phase01-Task001.md << EOF
# Phase 01 - Task 001: ${TASK_NAME}

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Started
Attempts: 1
Beginning ${TASK_DESCRIPTION}.
EOF
```

**On Update** — Append after each commit, milestone reached, or issue encountered:

```bash
cat >> ./meta/work/observability-api-alignment/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Progress
${UPDATE_DESCRIPTION}
Commit: $(git rev-parse --short HEAD) "$(git log -1 --pretty=%s)"
EOF
```

**On Completion** — Append once when task succeeds:

```bash
START_TIME=$(grep "Started" ./meta/work/observability-api-alignment/tasks/Phase01-Task001.md | head -1 | cut -d' ' -f2)
cat >> ./meta/work/observability-api-alignment/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Completed
Task completed successfully.
Total duration: $(date -d "$(date -u +%Y-%m-%dT%H:%M:%SZ)" +%s -d "$START_TIME" +%s | awk '{print int(($1-$2)/60) " minutes"}')
EOF
```

**On Failure** — Append when task fails, before retrying:

```bash
cat >> ./meta/work/observability-api-alignment/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Failed
Error: ${ERROR_MESSAGE}
Will retry with: ${RETRY_STRATEGY}
EOF
```

**Journal Entries**: `./meta/work/observability-api-alignment/journal/YYYYMMDDTHHMMSSZ.md`

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
git log --reverse --pretty=format:'%H|%ad|%an|%s' --date=iso-strict > ./meta/work/observability-api-alignment/history/commits.txt
git log --reverse --name-status --pretty=format:'----%n%H|%ad|%s' > ./meta/work/observability-api-alignment/history/changes.txt
```

Generate summary at **`./meta/work/observability-api-alignment/SUMMARY.md`** containing phase timings, key decisions, and error patterns.

Commit all metadata:

```bash
git add ./meta/work/observability-api-alignment/
git commit -m "Archive work history for observability-api-alignment"
git tag -a "work-complete-observability-api-alignment" -m "Work history archived"
```

Merge to trunk using squash commit:

```bash
git checkout trunk
git merge --squash dev/observability-api-alignment
```

Write merge message to **`./.cache/tmp/observability-api-alignment/merge-commit.txt`**:

```
observability-api-alignment: Align all observability examples with API specifications and extend coverage

Summary of changes:
- Fixed method naming inconsistencies across all examples
- Corrected parameter ordering and constructor patterns
- Standardized event structures to match API
- Added examples 73-77 for complete API coverage
- Created automated validation infrastructure

Work history preserved in ./meta/work/observability-api-alignment/
```

```bash
git commit -F ./.cache/tmp/observability-api-alignment/merge-commit.txt
rm ./.cache/tmp/observability-api-alignment/merge-commit.txt
```

Do not delete the **`dev/observability-api-alignment`** branch - it contains detailed commit history for future reference.

## Context

The observability package provides a unified event emission infrastructure for logging, tracing, and metrics. The package includes comprehensive examples demonstrating its usage, but analysis revealed numerous divergences between these examples and the formal API defined in Python stub files (.pyi).

Key divergences identified include:
- Method naming inconsistencies (getChild vs get_child)
- Parameter ordering issues (filtered function arguments)
- Constructor pattern mismatches (positional vs keyword arguments)
- Unused API methods that lack demonstration
- Event structure variations

This plan addresses these issues systematically while maintaining the educational value of the examples. The validation infrastructure created will prevent future divergences and ensure ongoing API compliance.