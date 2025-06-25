# Architecture

This document describes the structural design of the observability system, its layers, and how components interact to provide unified instrumentation.

## Executive Summary

The Event-Driven Observability Architecture unifies logging, tracing, and metrics collection through a context-based event pipeline with resource orchestration. The design provides explicit dependency injection for testability while offering a shared context singleton for convenience. The architecture distinguishes between system observability (infrastructure concerns) and domain observability (business logic), while recognizing the fundamental difference between stateless event processors and stateful resource managers.

## System Architecture Overview

The observability system implements a four-layer event processing pipeline:

```
┌─────────────────────────────────────────────────┐
│              Application Code                   │
├─────────────────────────────────────────────────┤
│ ObservabilityContext │ SharedContext.get()      │ ← Context Layer
├─────────────────────────────────────────────────┤
│  Logger │ Span │ Counter (Domain Objects)       │ ← Domain Layer
├─────────────────────────────────────────────────┤
│         EventDict (type, value, metadata)       │ ← Event System
├─────────────────────────────────────────────────┤
│    Handler Tree (Sink/Control/Composite)        │ ← Handler Layer
└─────────────────────────────────────────────────┘
```

### Layer Responsibilities

1. **Context Layer**: Encapsulates mutable state and configuration, orchestrates lifecycles
2. **Domain Layer**: Translates domain operations into events
3. **Event System**: Routes structured events with zero allocation
4. **Handler Layer**: Processes events through composable trees

## Context-Based Design

All observability state is encapsulated within explicit context objects, eliminating global state:

### ObservabilityContext
The primary abstraction encapsulating all observability state:
- Thread-safe event emission
- Handler lifecycle management
- Category-based filtering
- Zero-overhead when disabled

### SharedContext
A convenience singleton for ambient access:
- Optional for infrastructure concerns
- Initialized once at application startup
- Provides `get()` for implicit context access
- Auto-manages lifecycle with atexit

```python
# Explicit context (preferred for business logic)
context = ObservabilityContext(config)
logger = Logger('service', context)

# Shared context (convenience for infrastructure)
SharedContext.setup(config)
logger = Logger('cache', SharedContext.get())
```

## Event Pipeline Architecture

Events flow through a unified pipeline regardless of their domain:

```
Domain Operation
    ↓
emit(type, value, **metadata)
    ↓
EventDict Construction
    ├─ type: str
    ├─ value: Any
    ├─ timestamp_ns: int
    ├─ context vars (trace_id, etc.)
    └─ metadata: Dict[str, Any]
    ↓
Handler Dispatch
    ├─→ Handler₁(event)
    ├─→ Handler₂(event)
    └─→ Handler₃(event)
```

### Event Structure

All events share a common structure:
- **Core fields**: type, value, timestamp_ns
- **Context fields**: Automatically captured from contextvars
- **Domain fields**: Specific to logging/tracing/metrics
- **User metadata**: Arbitrary key-value pairs

## Handler Architecture

Handlers form a composable tree structure:

### Handler Categories

**Sink Handlers**: Terminal nodes performing I/O
- FileHandler, NetworkHandler, ConsoleHandler
- Responsible for final event delivery

**Control Handlers**: Intermediate nodes controlling flow
- filtered(), sampled(), batched()
- Apply policies without I/O

**Composite Handlers**: Orchestrate multiple handlers
- QueuedHandler, BufferHandler
- Manage complex processing pipelines

### Composition Pattern

```python
production_handler = sampled(0.01,
    QueuedHandler(
        BufferHandler(
            size=1000,
            handler=NetworkHandler('telemetry.service')
        )
    )
)
```

## System vs Domain Observability

The architecture supports two distinct usage patterns:

### System Observability
For infrastructure and cross-cutting concerns:
- Uses SharedContext for ambient access
- Suitable for caches, connection pools, middleware
- Reduces boilerplate in infrastructure code

### Domain Observability
For business logic and isolated components:
- Uses explicit ObservabilityContext injection
- Enables testing with isolated contexts
- Prevents hidden dependencies
- Supports multi-tenancy

## Zero-Overhead Architecture

The system maintains strict performance guarantees:

### Disabled State
When no handlers are attached:
```python
def emit(self, event_type: str, value: Any, **metadata) -> None:
    if not self._handlers:  # Single boolean check
        return             # Immediate exit
    # Event construction only happens if handlers exist
```

Cost: <1ns (single boolean check)

### Enabled State
With handlers attached:
1. Event construction (~50ns)
2. Context capture (~20ns)
3. Handler dispatch (~30ns per handler)

Total: ~100ns + handler processing time

## Lifecycle Management

The architecture enforces predictable resource management:

### Startup Sequence
```
Application.main()
    ↓
ObservabilityConfig(handlers=[...])
    ↓
ObservabilityContext(config)
    ↓
context.start()
    ├─→ handler₁.start()
    ├─→ handler₂.start()
    └─→ handler₃.start()
```

### Shutdown Sequence
```
context.stop() or atexit
    ├─→ handler₃.stop()  [reverse order]
    ├─→ handler₂.stop()
    └─→ handler₁.stop()
```

## Integration Points

The architecture provides clear integration boundaries:

### Application Integration
- Initialize context at application boundaries
- Pass context explicitly or use SharedContext
- Start/stop with application lifecycle

### Framework Integration
- Middleware can access SharedContext
- Request handlers receive explicit contexts
- Background tasks inherit context via contextvars

### Testing Integration
- Create isolated contexts per test
- Use BufferHandler for event capture
- No global state cleanup required