# Observability Framework Examples Implementation Plan

This document details a plan to create comprehensive examples demonstrating all capabilities and functionality of the Observability Framework, using only the published API specifications.

## Goals, Outcomes & Success Criteria

The intent of this plan is to develop a complete set of executable examples that demonstrate every aspect of the Observability Framework's API surface, enabling users to understand and effectively utilize all framework capabilities through practical, runnable code.

At conclusion of this plan, the following outcomes should be seen:

- 43 executable Python example files in `./examples/observability/`
- Coverage of 100% of public API methods defined in stub files
- Each example produces verifiable console output demonstrating its functionality
- Examples numbered sequentially from 01-72 with descriptive names
- A README.md file mapping examples to API features
- Performance benchmarks proving <1ns overhead when handlers not attached
- Integration patterns for asyncio and web frameworks

To gauge your success of actualizing this plan, use the following success criteria:

- Every class constructor in the stub files is instantiated in at least one example
- Every public method in the stub files is called with all parameter variations
- Each example executes without errors when run as `python examples/observability/XX_name.py`
- Performance example shows measurements proving zero-overhead design
- BufferHandler examples capture and verify at least 10 different event types
- Handler composition examples demonstrate at least 3 levels of nesting

## Scope & Constraints

Scope your efforts to creating executable Python examples in the `./examples/observability/` directory. Each example must import only from the observability package public API as defined in the .pyi stub files. Examples must produce console output that clearly demonstrates the feature being shown. Include timing measurements where performance is relevant. Create a progression from basic usage (context creation) to advanced patterns (multi-tenant production configurations).

Throughout your work, you should be mindful of your constraints. You MUST only import from: `observability`, `observability.handlers`, `observability.domains.logging`, `observability.domains.tracing`, `observability.domains.metrics`. You MUST NOT access any private attributes (those starting with underscore). You MUST include a module docstring in each example file explaining what it demonstrates. You MUST handle import errors gracefully if the package is not installed. You MUST use only Python standard library beyond the observability package. You SHOULD include output comments showing expected results. You MUST test each example in isolation before committing.

Throughout your efforts be mindful of the following:

- You MUST keep your working directory at the project root (i.e. `./`).
- You MUST adhere to the [Contributor's Guide](./CONTRIBUTOR.md) & the [Agent Guide](./AGENT.md)
- You SHOULD create Temporary Files under `./.cache/tmp/project-examples`
- You SHOULD record your efforts under `./meta/work/project-examples/`
  - This should include any subplans, summaries, commit messages or other general information regarding your efforts.
- You SHOULD use the Python venv at `./.venv`.
- You MAY prompt the user for feedback, guidance or general help when ambiguity arises that you are unable to traverse.

## Procedures

The implementation will systematically create examples covering all aspects of the Observability Framework, organized into four phases: Foundation Examples (basic usage), Domain Examples (logging, tracing, metrics), Handler Examples (composition and lifecycle), and Advanced Examples (production patterns, integration, performance).

### Phase 1 — Foundation Examples

**Summary** — Create 6 examples demonstrating core ObservabilityContext, ObservabilityConfig, SharedContext usage, context variables, direct event emission, and category filtering.

**Prerequisites** — Before beginning this phase, ensure:

- Directory `./examples/observability/` exists
- Observability package stub files are readable at `./src/observability/*.pyi`
- Python environment can import from local src directory

**Dependencies** — This phase depends on:

- Files: `src/observability/__init__.pyi`, `src/observability/types.pyi`
- No external packages required
- Python 3.8+ for typing support

**Tasks** — The following phase is composed of the following tasks:

1. Create `01_basic_setup.py`:
   - Import ObservabilityContext, ObservabilityConfig
   - Create config with empty handlers list
   - Create context with config
   - Call context.start()
   - Verify context.has_handlers() returns False
   - Call context.stop()
   - Print "Context lifecycle: created -> started -> stopped"

2. Create `02_configuration.py`:
   - Create ObservabilityConfig with all parameters:
     - handlers=[PrintHandler(sys.stdout)]
     - sampling_rate=0.5
     - enabled_categories={'logging', 'metrics'}
     - enabled=True
   - Access all config properties
   - Print each property value
   - Verify config is immutable (comment showing assignment would fail)

3. Create `03_shared_context.py`:
   - Call SharedContext.setup(config)
   - Demonstrate SharedContext.get() vs SharedContext.get_context()
   - Call SharedContext.attach_handler(JsonHandler(sys.stdout))
   - Use SharedContext.emit('test.event', 'value')
   - Call SharedContext.teardown()
   - Show RuntimeError on get() after teardown

4. Create `04_context_variables.py`:
   - Import trace_id, request_id, operation_id from observability
   - Set each context variable
   - Create event through context.emit()
   - Verify event includes context variables
   - Clear context variables and emit again
   - Print events showing presence/absence of context vars

5. Create `05_event_emission.py`:
   - Create context with PrintHandler
   - Call emit() with different event types:
     - Simple: emit('app.start', 'Starting')
     - With metadata: emit('user.login', {'id': 123}, username='alice')
     - Complex value: emit('data.processed', [1, 2, 3], count=3)
   - Show timestamp_ns automatically added
   - Demonstrate has_handlers() check before emission

6. Create `06_category_filtering.py`:
   - Create context with BufferHandler
   - Emit events in different categories
   - Call enable_category('logging')
   - Emit more events
   - Call disable_category('metrics')
   - Emit more events
   - Retrieve buffer contents showing filtered results

**Project State** — At conclusion of this phase; the desired project state should be:

- Directory `./examples/observability/` contains files 01-06
- Each file has clear docstring: """Example N: Description..."""
- Each file has if __name__ == '__main__': main()
- Console output clearly labeled with section headers
- No import errors or runtime exceptions

**Validation Criteria** — To confirm successful phase completion, validate:

- Run: `python examples/observability/01_basic_setup.py` produces output
- Each example imports successfully from observability package only
- BufferHandler in example 06 captures exactly expected events
- Context variables appear in emitted events when set
- No private attributes (._anything) are accessed

**Validation Actions** — If validation fails:

- Check import paths match stub file exports exactly
- Verify no implementation details are assumed
- Add try/except around imports with helpful error messages
- Document any API ambiguities in journal with timestamp
- If API intent unclear, create journal entry and request user clarification

### Phase 2 — Domain Examples

**Summary** — Create 11 examples demonstrating complete usage of Logger, Span, Counter, Gauge, and Histogram classes with all methods and parameters.

**Prerequisites** — Before beginning this phase, ensure:

- Phase 1 examples execute successfully
- Domain stub files are accessible: `src/observability/domains/*.pyi`
- Understanding that ContextProvider accepts context or callable

**Dependencies** — This phase depends on:

- Files: All domain .pyi files in src/observability/domains/
- Phase 1 examples for context creation patterns
- Standard library modules: time, random, asyncio

**Tasks** — The following phase is composed of the following tasks:

1. Create `10_logging_basics.py`:
   - Create Logger with name, context, min_level=DEBUG
   - Call every method: debug(), info(), warning(), error(), critical()
   - Use log() with explicit level parameter
   - Demonstrate is_enabled_for() before expensive operation
   - Show min_level filtering by setting to WARNING
   - Print output showing filtered messages

2. Create `11_logging_hierarchical.py`:
   - Create root logger 'app'
   - Use get_child('database'), get_child('api')
   - Create grandchild with api_logger.get_child('auth')
   - Set different min_levels on each logger
   - Demonstrate hierarchical naming in output
   - Show child loggers inherit context but not level

3. Create `12_logging_structured.py`:
   - Create logger and emit with kwargs
   - Show all kwarg types: strings, numbers, lists, dicts
   - Use same key with different values
   - Demonstrate args parameter for formatting
   - Show logger property access
   - Print events showing structured data

4. Create `20_tracing_basics.py`:
   - Create Span with operation name and context
   - Use span as context manager
   - Access span_id, parent_id, operation properties
   - Call set_attribute() with various types
   - Show automatic timing on exit
   - Print span events (start and end)

5. Create `21_tracing_nested.py`:
   - Create parent span
   - Use start_child() to create child span
   - Create grandchild span
   - Verify parent_id relationships
   - Show all spans complete in reverse order
   - Print span tree visualization

6. Create `22_tracing_async.py`:
   - Create async function with span
   - Use asyncio.gather for concurrent spans
   - Verify trace context propagates across tasks
   - Show span timing for async operations
   - Use asyncio.run() to execute
   - Print concurrent span execution

7. Create `23_tracing_events.py`:
   - Create span and call add_event()
   - Add multiple events with attributes
   - Call set_status(True) and set_status(False, "reason")
   - Show exception in context manager sets error
   - Demonstrate status in span end event
   - Print all span events and status

8. Create `30_metrics_counter.py`:
   - Create Counter with name, context, unit, description
   - Use static labels in constructor
   - Call increment() with default value
   - Call increment(5.0) with specific value
   - Use dynamic labels in increment()
   - Print all emitted metric events

9. Create `31_metrics_gauge.py`:
   - Create Gauge with all parameters
   - Call set() with various values
   - Use increment() and decrement()
   - Show negative values allowed
   - Mix static and dynamic labels
   - Print gauge value changes

10. Create `32_metrics_histogram.py`:
    - Create Histogram with custom buckets
    - Call observe() with values across bucket ranges
    - Use default buckets (DEFAULT_BUCKETS)
    - Show buckets property access
    - Demonstrate observations with labels
    - Print histogram events with buckets

11. Create `33_metrics_timer.py`:
    - Create Histogram for timing
    - Use Timer context manager
    - Pass labels to Timer constructor
    - Nest timers for sub-operations
    - Show automatic duration recording
    - Print timing measurements

**Project State** — At conclusion of this phase; the desired project state should be:

- Files 10-33 exist in examples/observability/
- Every domain method is called at least once
- Logger shows all severity levels and filtering
- Spans demonstrate parent-child relationships
- Metrics show all three types with labels
- Async example properly handles context

**Validation Criteria** — To confirm successful phase completion, validate:

- Logger.get_child() returns new Logger instance with dotted name
- Span context manager emits both start and end events
- Counter.increment() only accepts non-negative values
- Histogram observations include bucket boundaries
- All examples run without exceptions

**Validation Actions** — If validation fails:

- Cross-check method signatures with stub files
- Ensure ContextProvider usage matches either context or callable
- Verify event types match expected patterns (log.*, trace.span.*, metric.*)
- Add error handling for any edge cases
- Document any behavioral discoveries in journal

### Phase 3 — Handler Examples

**Summary** — Create 12 examples demonstrating all handler types from the handlers module, including sink handlers, control handlers, composite handlers, and lifecycle management.

**Prerequisites** — Before beginning this phase, ensure:

- Phase 2 domain examples complete
- Understanding of EventHandler protocol
- Clear distinction between stateless and stateful handlers

**Dependencies** — This phase depends on:

- File: `src/observability/handlers/__init__.pyi`
- Understanding of EventDict structure from types.pyi
- File I/O for ManagedFileHandler examples

**Tasks** — The following phase is composed of the following tasks:

1. Create `40_handler_print.py`:
   - Create PrintHandler with default parameters
   - Create with custom format string using multiple fields
   - Set include_context=True and show context fields
   - Emit various event types to show formatting
   - Demonstrate missing field handling
   - Print formatted output examples

2. Create `41_handler_json.py`:
   - Create JsonHandler with stream=sys.stdout
   - Create with indent=2 for pretty printing
   - Create with sort_keys=True
   - Emit complex nested events
   - Show JSON serialization of all types
   - Print both compact and formatted JSON

3. Create `42_handler_file.py`:
   - Create ManagedFileHandler with all parameters
   - Call handler.start() explicitly
   - Emit events to write to file
   - Demonstrate rotation parameters
   - Call handler.stop() for cleanup
   - Read and print file contents

4. Create `43_handler_buffer.py`:
   - Create BufferHandler with max_size limit
   - Emit more events than max_size
   - Call get_events() to retrieve list
   - Call clear() and verify empty
   - Show events are defensive copies
   - Print captured event analysis

5. Create `44_handler_queued.py`:
   - Create QueuedHandler wrapping PrintHandler
   - Show queue_size and timeout parameters
   - Call start() to initialize worker
   - Emit burst of events
   - Call stop() to drain queue
   - Print timing showing async behavior

6. Create `45_handler_filtered.py`:
   - Create multiple filter predicates
   - Use filtered() to wrap handlers
   - Show lambda predicates checking event fields
   - Demonstrate type filtering
   - Show severity filtering
   - Print which events pass filters

7. Create `46_handler_sampled.py`:
   - Create sampled() with different rates
   - Use seed for deterministic sampling
   - Emit 1000 events with 0.01 rate
   - Show statistical sampling
   - Combine with filtered()
   - Print sampling statistics

8. Create `47_handler_timedelta.py`:
   - Create TimeDeltaHandler wrapping PrintHandler
   - Emit sequence of events
   - Show time_delta_ns field added
   - Create delays between events
   - Show first event has delta=0
   - Print events with time deltas

9. Create `48_handler_fanout.py`:
   - Create FanoutHandler with multiple handlers
   - Include handlers that might fail
   - Show all handlers receive events
   - Demonstrate failure isolation
   - Use start/stop lifecycle
   - Print output from each handler

10. Create `49_handler_fallback.py`:
    - Create FallbackHandler with handler list
    - Include deliberately failing handler
    - Show fallback behavior
    - Demonstrate successful handler stops chain
    - Show all handlers tried on failure
    - Print fallback sequence

11. Create `50_handler_lifecycle.py`:
    - Create handlers with start/stop methods
    - Show lifecycle order in ObservabilityContext
    - Demonstrate auto-start on attach
    - Show reverse-order stop
    - Handle lifecycle errors gracefully
    - Print lifecycle transitions

12. Create `51_handler_composition.py`:
    - Create 3-level handler tree
    - Combine filtered, sampled, and queued
    - Add fanout with different targets
    - Show complex routing rules
    - Demonstrate composition patterns
    - Print handler tree visualization

**Project State** — At conclusion of this phase; the desired project state should be:

- Files 40-51 exist demonstrating all handlers
- File handlers create actual files in examples/
- BufferHandler shows event capture
- Composition examples show 3+ levels
- Lifecycle methods properly sequenced

**Validation Criteria** — To confirm successful phase completion, validate:

- ManagedFileHandler creates file after start()
- BufferHandler.get_events() returns list copy, not reference
- QueuedHandler processes events asynchronously
- filtered() only passes matching events
- sampled() achieves statistical rate
- Lifecycle handlers start/stop in correct order

**Validation Actions** — If validation fails:

- Ensure file permissions for ManagedFileHandler
- Verify handler protocols match stub signatures
- Check async behavior with timing measurements
- Validate statistical sampling with larger sample size
- Add cleanup to remove test files after examples

### Phase 4 — Advanced Examples

**Summary** — Create 14 advanced examples demonstrating production patterns, performance validation, integration approaches, and a comprehensive README organizing all examples.

**Prerequisites** — Before beginning this phase, ensure:

- All previous phases complete with 39 examples
- Performance timing approach using time.perf_counter()
- Understanding of production deployment patterns

**Dependencies** — This phase depends on:

- All previous examples as building blocks
- Python standard library: asyncio, time, random
- No external framework dependencies

**Tasks** — The following phase is composed of the following tasks:

1. Create `60_zero_overhead_proof.py`:
   - Create empty context (no handlers)
   - Time 1 million logger calls
   - Add handler and time again
   - Show <1ns per call without handlers
   - Show ~100ns per call with handler
   - Print performance comparison table

2. Create `61_high_volume_patterns.py`:
   - Generate 100k events/second
   - Use QueuedHandler for async processing
   - Show batching with BufferHandler
   - Demonstrate sampling strategies
   - Monitor queue depths
   - Print throughput metrics

3. Create `62_error_handling.py`:
   - Create failing handlers
   - Show error isolation
   - Demonstrate handler recovery
   - Show context continues despite errors
   - Test lifecycle error handling
   - Print error scenarios and outcomes

4. Create `63_testing_patterns.py`:
   - Create test case with BufferHandler
   - Verify logging behavior
   - Assert on metrics values
   - Check span relationships
   - Show event inspection patterns
   - Print test assertions

5. Create `64_debugging_observability.py`:
   - Use BufferHandler to debug itself
   - Show handler pipeline inspection
   - Demonstrate event flow tracing
   - Add debug handlers dynamically
   - Show self-inspection patterns
   - Print internal behavior analysis

6. Create `65_migration_pattern.py`:
   - Show migration from Python logging
   - Create adapter for existing code
   - Demonstrate gradual migration
   - Show compatibility patterns
   - Maintain backward compatibility
   - Print migration steps

7. Create `66_multi_tenant.py`:
   - Create context per tenant
   - Show isolation between contexts
   - Demonstrate tenant-specific handlers
   - Add tenant ID to all events
   - Show concurrent tenant operations
   - Print multi-tenant event streams

8. Create `67_correlation_patterns.py`:
   - Set trace_id across operations
   - Show correlation through domains
   - Link logs to traces to metrics
   - Demonstrate request tracking
   - Show distributed correlation
   - Print correlated event sequences

9. Create `68_custom_domain.py`:
   - Define custom event types
   - Create domain-specific wrapper
   - Follow domain patterns
   - Integrate with handlers
   - Show domain extension
   - Print custom domain events

10. Create `69_production_config.py`:
    - Create production handler pipeline
    - Set up error isolation
    - Configure sampling rates
    - Add file rotation
    - Show monitoring integration
    - Print production configuration

11. Create `70_integration_web_framework.py`:
    - Simulate web framework middleware
    - Per-request context creation
    - Automatic trace correlation
    - Request/response logging
    - Error tracking integration
    - Print simulated HTTP handling

12. Create `71_integration_async_app.py`:
    - Create async application pattern
    - Show context propagation
    - Handle concurrent operations
    - Demonstrate async handlers
    - Show graceful shutdown
    - Print async execution flow

13. Create `72_monitoring_dashboard.py`:
    - Create real-time metrics aggregation
    - Show event rate calculation
    - Track error percentages
    - Display latency percentiles
    - Update console dashboard
    - Print monitoring summary

14. Create `README.md`:
    - Create example index table
    - Group by category
    - Map examples to API features
    - Provide learning path
    - Include execution instructions
    - Add troubleshooting section

**Project State** — At conclusion of this phase; the desired project state should be:

- All 72 example files exist and execute
- README provides navigation and learning path
- Performance benchmark proves zero-overhead
- Production patterns are realistic
- Integration examples are practical

**Validation Criteria** — To confirm successful phase completion, validate:

- Performance example shows <1ns overhead measurement
- Multi-tenant example maintains isolation
- Production config handles 1M+ events
- All examples in README are accurate
- No examples depend on external packages
- Every public API method is demonstrated

**Validation Actions** — If validation fails:

- Increase iteration count for performance accuracy
- Verify isolation with separate BufferHandlers
- Load test production configuration
- Cross-reference README with actual files
- Ensure only standard library imports
- Audit API coverage with stub files

## Work Process

### Git Branch Management

Create and switch to branch **`dev/project-examples`**:

```bash
git switch -c dev/project-examples
```

All work must occur on this branch.

**Committing Changes**

Commit changes using precise pathspecs. Write file paths to **`./.cache/tmp/project-examples/pathspec.txt`**, one per line. Write descriptive commit messages to **`./.cache/tmp/project-examples/commit.txt`** using present tense.

```bash
git add --pathspec-from-file=./.cache/tmp/project-examples/pathspec.txt
git commit --pathspec-from-file=./.cache/tmp/project-examples/pathspec.txt -F ./.cache/tmp/project-examples/commit.txt
rm ./.cache/tmp/project-examples/pathspec.txt ./.cache/tmp/project-examples/commit.txt
```

### Work Recording

Track progress through append-only task files and contextual journal entries.

**Task Files**: `./meta/work/project-examples/tasks/PhaseNN-TaskMMM.md`

Create a new file when starting each task, then append entries as events occur.

**On Start** — Create the file when beginning a task:

```bash
cat > ./meta/work/project-examples/tasks/Phase01-Task001.md << EOF
# Phase 01 - Task 001: ${TASK_NAME}

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Started
Attempts: 1
Beginning ${TASK_DESCRIPTION}.
EOF
```

**On Update** — Append after each commit, milestone reached, or issue encountered:

```bash
cat >> ./meta/work/project-examples/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Progress
${UPDATE_DESCRIPTION}
Commit: $(git rev-parse --short HEAD) "$(git log -1 --pretty=%s)"
EOF
```

**On Completion** — Append once when task succeeds:

```bash
START_TIME=$(grep "Started" ./meta/work/project-examples/tasks/Phase01-Task001.md | head -1 | cut -d' ' -f2)
cat >> ./meta/work/project-examples/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Completed
Task completed successfully.
Total duration: $(date -d "$(date -u +%Y-%m-%dT%H:%M:%SZ)" +%s -d "$START_TIME" +%s | awk '{print int(($1-$2)/60) " minutes"}')
EOF
```

**On Failure** — Append when task fails, before retrying:

```bash
cat >> ./meta/work/project-examples/tasks/Phase01-Task001.md << EOF

## $(date -u +%Y-%m-%dT%H:%M:%SZ) - Failed
Error: ${ERROR_MESSAGE}
Will retry with: ${RETRY_STRATEGY}
EOF
```

**Journal Entries**: `./meta/work/project-examples/journal/YYYYMMDDTHHMMSSZ.md`

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
git log --reverse --pretty=format:'%H|%ad|%an|%s' --date=iso-strict > ./meta/work/project-examples/history/commits.txt
git log --reverse --name-status --pretty=format:'----%n%H|%ad|%s' > ./meta/work/project-examples/history/changes.txt
```

Generate summary at **`./meta/work/project-examples/SUMMARY.md`** containing phase timings, key decisions, and error patterns.

Commit all metadata:

```bash
git add ./meta/work/project-examples/
git commit -m "Archive work history for observability-examples"
git tag -a "work-complete-observability-examples" -m "Work history archived"
```

Merge to trunk using squash commit:

```bash
git checkout trunk
git merge --squash dev/project-examples
```

Write merge message to **`./.cache/tmp/project-examples/merge-commit.txt`**:

```
observability-examples: Comprehensive examples demonstrating all framework capabilities

Summary of changes:
- Added 72 examples covering all API surface
- Created README with learning path
- Demonstrated zero-overhead performance
- Included production patterns

Work history preserved in ./meta/work/project-examples/
```

```bash
git commit -F ./.cache/tmp/project-examples/merge-commit.txt
rm ./.cache/tmp/project-examples/merge-commit.txt
```

Do not delete the **`dev/project-examples`** branch - it contains detailed commit history for future reference.

## Context

The Observability Framework provides a unified event emission infrastructure with zero-overhead instrumentation for logging, tracing, and metrics collection. The framework implements a context-based architecture where all observability state is encapsulated in explicit context objects, eliminating global state.

The framework's public API is defined through Python stub files (.pyi):
- `src/observability/__init__.pyi` - Core context and configuration classes
- `src/observability/types.pyi` - Type definitions and protocols
- `src/observability/handlers/__init__.pyi` - All handler implementations
- `src/observability/domains/logging.pyi` - Logger class and constants
- `src/observability/domains/tracing.pyi` - Span class and context variables
- `src/observability/domains/metrics.pyi` - Counter, Gauge, Histogram classes

Key API elements that must be demonstrated:

**Core Module**:
- ObservabilityContext: start(), stop(), emit(), attach_handler(), has_handlers(), enable_category(), disable_category()
- ObservabilityConfig: handlers, sampling_rate, enabled_categories, enabled
- SharedContext: setup(), get(), get_context(), teardown(), attach_handler()
- Context variables: trace_id, request_id, operation_id

**Handlers Module**:
- PrintHandler: format parameter, include_context parameter
- JsonHandler: indent parameter, sort_keys parameter
- ManagedFileHandler: max_bytes, backup_count, lifecycle methods
- BufferHandler: max_size, get_events(), clear()
- QueuedHandler: queue_size, timeout, worker thread
- filtered(): predicate function wrapping
- sampled(): rate and seed parameters
- TimeDeltaHandler: time_delta_ns enrichment
- FanoutHandler: multiple handler dispatch
- FallbackHandler: error recovery chain

**Logging Domain**:
- Logger: debug(), info(), warning(), error(), critical(), log()
- get_child() for hierarchical loggers
- is_enabled_for() for conditional logging
- min_level property for filtering
- Severity constants: DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50

**Tracing Domain**:
- Span: context manager protocol
- span_id, parent_id, operation properties
- set_attribute(), set_status(), add_event()
- start_child() for nested spans
- Automatic parent detection via current_span

**Metrics Domain**:
- Counter: increment() with value and labels
- Gauge: set(), increment(), decrement()
- Histogram: observe(), custom buckets
- Timer: context manager for histogram
- Static and dynamic labels

The examples must demonstrate that:
1. Without handlers, operations have <1ns overhead (single boolean check)
2. Handlers can be composed into complex processing trees
3. Context variables automatically propagate through async boundaries
4. State is isolated between different contexts
5. Lifecycle management ensures proper resource cleanup
6. Error isolation prevents handler failures from affecting the system

Each example should follow this structure:
```python
#!/usr/bin/env python3
"""
Example N: Title

Demonstrates:
- Specific feature 1
- Specific feature 2
"""

from observability import ...  # Only public imports

def main():
    """Main example logic."""
    # Example implementation
    
if __name__ == '__main__':
    main()
```

Examples must produce clear console output showing the demonstrated behavior, with section headers and explanatory comments. Performance examples must include timing measurements. Handler examples must show actual event processing.