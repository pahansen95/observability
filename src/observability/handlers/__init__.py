"""
Handler implementations for event processing and output.

Handlers consume events from the observability pipeline, producing side effects
like formatted output, storage, or transmission. They form a tree-based dispatch
system where events flow from root to leaves through control nodes.

## Architecture

Events propagate through handler trees:

    Event → Root
             ├─→ Filter(severity >= ERROR) → FileHandler("errors.log")
             ├─→ Sample(0.01) → NetworkHandler("metrics.local")
             └─→ Queue(10000) → BufferHandler(size=1000)

## Handler Types

**Sink Handlers**: Terminal consumers that perform I/O operations
- Manage external resources (files, sockets, memory)
- Define output formats
- Examples: PrintHandler, JsonHandler, ManagedFileHandler

**Control Handlers**: Modify execution flow without consuming events
- Implement policies (filtering, sampling, queuing)
- Preserve handler interface
- Examples: filtered, sampled, QueuedHandler

**Composite Handlers**: Coordinate multiple handlers
- Enable fan-out patterns
- Isolate failure domains
- Examples: FanoutHandler, FallbackHandler

## Resource Management

**Session-Based**: Long-lived resources across events
- Amortized acquisition cost
- Configurable batching
- High-volume optimized

**Ephemeral**: Per-event resource lifecycle
- Simple implementation
- Higher overhead
- Low-volume suitable

## Design Principles

- Single responsibility per handler
- Composable through standard patterns
- Fail-safe operation
- Resource-efficient I/O batching
- Predictable performance characteristics
"""

# Import handler classes directly
from .sink import PrintHandler, JsonHandler
from .control import filtered, sampled, TimeDeltaHandler
from .composite import FanoutHandler, FallbackHandler
from .resource import ManagedFileHandler, BufferHandler
from .queued import QueuedHandler

# Export public API - classes only, no factories
__all__ = [
  # Sink handlers
  "PrintHandler",
  "JsonHandler",
  # Control handlers
  "filtered",
  "sampled",
  "TimeDeltaHandler",
  # Composite handlers
  "FanoutHandler",
  "FallbackHandler",
  # Resource handlers
  "ManagedFileHandler",
  "BufferHandler",
  # Queued handler
  "QueuedHandler",
]
