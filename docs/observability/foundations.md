# Foundations

This document articulates the fundamental assumptions and design predicates upon which the observability architecture is built. Understanding these foundations is essential for extending or modifying the system.

## Core Assumptions

### Context Ownership
**Assumption**: Every piece of observability state belongs to exactly one context.

Implications:
- No global variables or module-level state
- All configuration is context-scoped
- Testing requires no global cleanup
- Multiple contexts can coexist independently

### Event Immutability
**Assumption**: Once created, events are immutable data structures.

Implications:
- Events can be safely shared between threads
- No defensive copying required
- Handlers cannot modify events
- Event replay is deterministic

### Lifecycle Separation
**Assumption**: Configuration, initialization, and operation are distinct phases.

Implications:
- Handlers are configured before starting
- Resource acquisition is explicit
- Side effects occur only during operation
- Testing can verify configuration without resources

### Zero-Cost Abstraction
**Assumption**: Unused instrumentation has zero runtime cost.

Implications:
- All work is guarded by handler checks
- No background threads without handlers
- No memory allocation when disabled
- Instrumentation can be pervasive

## Design Predicates

### Handler Classification Predicate
**Predicate**: A handler is either stateless or stateful, never both.

```python
# Stateless: f(event) → None
def stateless_handler(event: EventDict) -> None:
    print(event)  # No persistent state

# Stateful: Manages resources across events
class StatefulHandler:
    def start(self) -> None: ...  # Acquire
    def __call__(self, event: EventDict) -> None: ...
    def stop(self) -> None: ...   # Release
```

This binary classification enables:
- Clear lifecycle requirements
- Predictable resource management
- Composability guarantees

### Synchronous Lifecycle Predicate
**Predicate**: All lifecycle operations are synchronous and blocking.

```python
context.start()  # Blocks until all handlers ready
context.stop()   # Blocks until all handlers stopped
```

Rationale:
- Predictable initialization order
- Guaranteed cleanup completion
- Simple error propagation
- No race conditions

### Event Ordering Predicate
**Predicate**: Events are processed in emission order within a thread.

Guarantees:
- Causal relationships preserved
- Log narrative coherence
- Trace parent-child relationships
- No out-of-order surprises

Does not guarantee:
- Cross-thread ordering
- Cross-process ordering
- Wall-clock ordering

### Handler Failure Predicate
**Predicate**: Handler failures do not affect event emission.

```python
def emit(self, event_type: str, value: Any, **metadata) -> None:
    event = self._create_event(event_type, value, metadata)
    for handler in self._handlers:
        try:
            handler(event)
        except Exception:
            # Log but continue
            pass
```

This ensures:
- Observability doesn't break applications
- One bad handler doesn't affect others
- System remains debuggable under failure

## Performance Guarantees

### Disabled Performance
**Guarantee**: When no handlers attached, overhead is <1ns.

Implementation:
```python
if not self._handlers:  # Single boolean check
    return              # No further work
```

### Enabled Performance
**Guarantee**: Event emission overhead is ~100ns + handler time.

Breakdown:
- Event construction: ~50ns
- Context capture: ~20ns  
- Dispatch overhead: ~30ns
- Handler execution: Variable

### Memory Overhead
**Guarantee**: No heap allocations when disabled.

When enabled:
- One dict allocation per event
- Reused handler list iteration
- No intermediate copies

## Resource Ownership Model

### Single Owner Principle
**Principle**: Each resource has exactly one managing handler.

```python
# GOOD: Clear ownership
file_handler = ManagedFileHandler('app.log')

# BAD: Shared resource
shared_file = open('app.log', 'a')
handler1 = CustomHandler(shared_file)
handler2 = AnotherHandler(shared_file)
```

### Lifecycle Bracket Principle
**Principle**: Resources acquired in start() must be released in stop().

```python
class ResourceHandler:
    def start(self):
        self.resource = acquire_resource()
    
    def stop(self):
        if hasattr(self, 'resource'):
            self.resource.release()
```

### Graceful Degradation Principle
**Principle**: Resource failures degrade functionality, not availability.

- Failed handler start: Skip handler, log warning
- Failed handler stop: Log error, continue shutdown
- Failed event handling: Log error, continue emission

## Threading Model

### Thread Safety Assumptions
**Assumption**: Contexts are thread-safe for emission, not configuration.

Safe operations:
- `context.emit()` from any thread
- `SharedContext.get()` from any thread

Unsafe operations:
- `context.attach_handler()` during emission
- `context.start()` from multiple threads

### Context Variable Propagation
**Assumption**: Python's contextvars handle async propagation.

```python
# Parent task sets context
trace_id.set('abc-123')

# Child tasks inherit automatically
async def child_task():
    # trace_id is 'abc-123' here
    context.emit('event', {})
```

## Error Handling Philosophy

### Fail-Safe Principle
Observability errors should never break the application:

```python
try:
    # Observability operation
    logger.info("Starting process")
except Exception:
    # Silent failure is acceptable
    pass
```

### Fail-Fast Configuration
Configuration errors should fail immediately:

```python
# GOOD: Fail at startup
context = ObservabilityContext(invalid_config)
context.start()  # Raises ConfigurationError

# BAD: Fail during operation
context.emit('event', value)  # Should not fail here
```

## Extension Principles

### Domain Independence
**Principle**: New domains don't require core changes.

A new domain only needs:
- Event type namespace
- Domain API class
- Optional specialized handler

### Handler Composability  
**Principle**: Handlers compose without coordination.

```python
# Any handler can wrap any other
filtered_handler = filtered(condition, any_handler)
sampled_handler = sampled(rate, any_handler)
queued_handler = QueuedHandler(any_handler)
```

### Forward Compatibility
**Principle**: New event fields don't break old handlers.

Events are dictionaries, allowing:
- New fields without handler updates
- Optional field handling
- Graceful version evolution