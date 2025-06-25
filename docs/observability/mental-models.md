# Mental Models

This document presents the core conceptual models that shape the observability architecture. Understanding these models is essential for effective system design and implementation.

## Resource Lifecycle Model

Observability handlers operate in two fundamentally different modes:

### Stateless Handlers
Pure event processors that handle each event independently:
- No persistent state between events
- No initialization or cleanup required
- Examples: `PrintHandler`, `filtered()`, `sampled()`

### Stateful Handlers
Resource managers that maintain state across events:
- Manage persistent resources (files, connections, threads)
- Require explicit start/stop lifecycle
- Amortize initialization costs across many events
- Examples: `ManagedFileHandler`, `QueuedHandler`, `NetworkHandler`

```
Stateless Processing          Stateful Management
Event → Process → Done        Start → Process Events → Stop
(ephemeral)                   (persistent resources)
```

## Orchestration Model

The ObservabilityContext acts as a conductor, orchestrating handler lifecycles in a predictable manner:

```
Application Lifecycle
    ↓
Context.start()
    ├─→ Handler₁.start() [acquire resources]
    ├─→ Handler₂.start() [open connections]
    └─→ Handler₃.start() [spawn threads]
    
Event Processing
    ├─→ emit(event)
    └─→ dispatch to all handlers
    
Context.stop()
    ├─→ Handler₃.stop() [drain queues]
    ├─→ Handler₂.stop() [close connections]
    └─→ Handler₁.stop() [flush buffers]
```

Key principles:
- Start handlers in registration order
- Stop handlers in reverse order
- Ensure graceful shutdown
- Prevent resource leaks

## Two-Phase Construction

Handlers separate configuration from resource acquisition, enabling predictable lifecycle management:

### Phase 1: Configuration
No side effects or resource allocation:
```python
handler = FileHandler('app.log', buffer_size=8192)
context.attach_handler(handler)
```

### Phase 2: Resource Acquisition
Explicit resource management:
```python
context.start()  # Resources acquired here
# ... process many events ...
context.stop()   # Resources released here
```

This separation enables:
- Testability without side effects
- Predictable resource management
- Clear error boundaries
- Composable configurations

## Event Flow Models

The architecture supports two complementary approaches to event processing:

### Pipeline Model
For stateless transformations:
```
Event → Filter → Transform → Output
```

Characteristics:
- Linear data flow
- No persistent state
- Composable operations
- Pure transformations

### Plumbing Model
For stateful resource management:
```
Event Source ──┐
              ├→ Buffer Tank (batch writes)
              ├→ Queue Reservoir (async processing)
              └→ Network Pipe (remote delivery)
```

Characteristics:
- Resource pooling
- State management
- Async operations
- Efficiency optimization

## Temporal Domain Model

Each observability domain captures different temporal characteristics:

### Logging Domain
**Temporal Model**: Discrete points in time
- Captures forensic snapshots
- Preserves causal ordering
- Enables narrative reconstruction

### Tracing Domain
**Temporal Model**: Durations with relationships
- Captures execution journeys
- Shows causal dependencies
- Measures latency distribution

### Metrics Domain
**Temporal Model**: Time series for aggregation
- Captures quantitative trends
- Enables statistical analysis
- Supports alerting thresholds

```
Time →
Logging:  • • • • • • • •  (discrete events)
Tracing:  |---span1---|    (durations)
          |--span2--|
Metrics:  ▁▃▅▇▅▃▁▃▅▇     (aggregated series)
```

## Context Propagation Model

Context flows implicitly through execution paths using Python's contextvars:

```
Main Thread
├─→ trace_id = "abc"
├─→ Async Task 1 (inherits trace_id)
│   └─→ emit(event) [includes trace_id]
└─→ Async Task 2 (inherits trace_id)
    └─→ emit(event) [includes trace_id]
```

Benefits:
- Automatic correlation
- Thread-safe propagation
- Async-aware context
- Zero manual passing

## Zero-Overhead Model

The system maintains a fundamental performance guarantee:

```python
# When disabled (no handlers):
if not self._handlers:  # Single boolean check
    return              # Immediate exit

# Cost: <1ns
```

This model ensures:
- Pervasive instrumentation is practical
- Production code pays no penalty
- Debugging capability is always available
- Performance concerns don't limit observability