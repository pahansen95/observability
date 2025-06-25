# Observability

A unified event emission infrastructure providing zero-overhead instrumentation for logging, tracing, and metrics collection. The system implements a context-based architecture where all observability state is encapsulated in explicit context objects.

## Quick Start

```python
from observability import ObservabilityContext, ObservabilityConfig
from observability.domains.logging import Logger
from observability.handlers import JsonHandler

# Create and configure context
config = ObservabilityConfig(handlers=[JsonHandler(sys.stderr)])
context = ObservabilityContext(config)
context.start()

# Use domains
logger = Logger('myapp', context)
logger.info('Application started', version='1.0')

# Cleanup
context.stop()
```

## Architecture Overview

```
Application Code
    ↓
ObservabilityContext ←── SharedContext.get()
    ↓ emit()
Domain Objects ──────────→ Events
    ↓
Handler Tree
    ├─→ Sink (I/O operations)
    ├─→ Control (filtering/sampling)
    └─→ Composite (coordination)
```

## Documentation Structure

### Conceptual Foundation
- **[Mental Models](mental-models.md)** - Core concepts and thinking patterns
- **[Architecture](architecture.md)** - System design and structure
- **[Foundations](foundations.md)** - Assumptions and design predicates

### Implementation
- **[Implementation Guide](implementation.md)** - Technical details and APIs
- **[Domains](domains.md)** - Logging, tracing, metrics, and custom domains
- **[Handlers](handlers.md)** - Event processing and handler development

## Key Features

**Zero-Overhead Design**: When no handlers are attached, the entire system reduces to a single boolean check, ensuring production code pays no performance penalty for unused instrumentation.

**Context-Based Architecture**: All observability state lives within explicit context objects, eliminating global state and enabling isolated testing.

**Unified Event Pipeline**: A single event emission mechanism serves logging, tracing, and metrics through specialized domain objects.

**Resource Orchestration**: Distinguishes between stateless event processors and stateful resource managers with explicit lifecycle management.

## When to Use Each Document

| Goal | Document |
|------|----------|
| Understand the conceptual model | [Mental Models](mental-models.md) |
| Learn system architecture | [Architecture](architecture.md) |
| Understand design decisions | [Foundations](foundations.md) |
| Implement observability | [Implementation](implementation.md) |
| Create custom domains | [Domains](domains.md) |
| Build event handlers | [Handlers](handlers.md) |

## Design Principles

1. **Explicit over Implicit**: All context and configuration is passed explicitly
2. **Zero Cost When Disabled**: Instrumentation has no runtime cost when not in use
3. **Unified Event Model**: All observability data flows through a common pipeline
4. **Lifecycle Separation**: Configuration is separate from resource acquisition