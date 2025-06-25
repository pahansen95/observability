# Event-Driven Observability Architecture

## Executive Summary

The Event-Driven Observability Architecture unifies logging, tracing, and metrics collection through a context-based event pipeline. This design provides explicit dependency injection for testability while offering a shared context singleton for convenience. The architecture distinguishes between system observability (infrastructure concerns) and domain observability (business logic), maintaining zero-overhead characteristics when instrumentation is disabled.

## Mental Model

Observability flows through your application as structured events emitted from explicit contexts. Each domain captures different temporal characteristics of system behavior:

- **Logging**: Discrete points in time (forensic snapshots)
- **Tracing**: Durations with relationships (execution journeys)
- **Metrics**: Time series for aggregation (quantitative trends)

```
Application Boundary
    ↓ 
ObservabilityContext ←── SharedContext (singleton)
    ↓ emit()              ↑ thread-safe access
Domain Objects ──────────→ Events
    ↓
Handler Tree
    ├─→ Sink (I/O operations)
    ├─→ Control (filtering/sampling)
    └─→ Composite (coordination)
```

The architecture answers three fundamental questions:
- "What happened?" → Logging domain
- "How did it flow?" → Tracing domain
- "How much/often?" → Metrics domain

The architecture provides two access patterns:
- **Explicit Contexts**: Direct instantiation for testing and isolation
- **Shared Context**: Singleton pattern for convenient ambient access

## Architectural Overview

The system implements a four-layer event processing pipeline:

1. **Context Layer**: Encapsulates mutable state and configuration
2. **Event System**: Routes structured events with zero allocation
3. **Domain Layer**: Translates domain operations into events
4. **Handler Layer**: Processes events through composable trees

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

## Context Layer

### ObservabilityContext

The primary abstraction encapsulating all observability state:

```python
class ObservabilityContext:
    def __init__(self, config: Optional[ObservabilityConfig] = None):
        self._handlers: List[EventHandler] = []
        self._start_time_ns = time.perf_counter_ns()
        self._lock = threading.Lock()
    
    def emit(self, event_type: str, value: Any, **metadata) -> None:
        """Zero-overhead emission when no handlers attached."""
        if not self._handlers:  # Single boolean check
            return
        # Event construction and dispatch
```

### SharedContext Pattern

A thread-safe singleton providing ambient observability access:

```python
class SharedContext:
    _ctx: Optional[ObservabilityContext] = None
    _lock: threading.Lock = threading.Lock()
    
    @classmethod
    def setup(cls, config: Optional[ObservabilityConfig] = None):
        """Initialize shared context once at application boundary."""
        with cls._lock:
            if cls._ctx is not None:
                raise RuntimeError("Already initialized")
            cls._ctx = ObservabilityContext(config)
    
    @classmethod
    def get(cls) -> ObservabilityContext:
        """Retrieve shared context for ambient access."""
        if cls._ctx is None:
            raise RuntimeError("Not initialized")
        return cls._ctx
```

### Configuration

Immutable configuration loaded at application boundaries:

```python
@dataclass(frozen=True)
class ObservabilityConfig:
    handlers: List[EventHandler] = field(default_factory=list)
    sampling_rate: float = 1.0
    enabled_categories: Set[str] = field(default_factory=set)
```

## Event System

### EventDict Structure

Events flow as structured dictionaries with layered fields:

```python
EventDict = Dict[str, Any]
# Core fields: type, value, timestamp_ns, context_name
# Context fields: trace_id, request_id, operation_id
# Domain fields: logger_name, span_id, metric_labels
# User metadata: arbitrary kwargs
```

### Context Variables

Ambient context enrichment via Python's contextvars:

```python
# Exported directly from observability package
trace_id = contextvars.ContextVar("trace_id", default=None)
request_id = contextvars.ContextVar("request_id", default=None)
operation_id = contextvars.ContextVar("operation_id", default=None)
```

### Performance Characteristics

| State | Overhead | Operation |
|-------|----------|-----------|
| No handlers | <1ns | Single boolean check |
| With handlers | ~100ns | Event construction + dispatch |
| Context lookup | ~20ns | Cached contextvar access |

## Domain Layer

Domains provide specialized APIs that emit structured events. Each domain captures different temporal characteristics of system behavior.

### Domain Differentiation

| Domain | Temporal Model | Data Structure | Primary Question |
|--------|---------------|----------------|------------------|
| Logging | Discrete points | Independent events | "What happened?" |
| Tracing | Durations with relationships | Hierarchical spans | "How did it flow?" |
| Metrics | Time series | Aggregatable values | "How much/often?" |

### Direct Instantiation

```python
from observability.domains.logging import Logger
from observability.domains.tracing import Span
from observability.domains.metrics import Counter

# Create domain objects directly
logger = Logger('myapp.service', context)
span = Span('operation', context)
counter = Counter('requests', context)
```

### Event Type Constants

Pre-computed constants eliminate runtime string construction:

```python
# logging.py
LOG_40: Final[str] = "log.40"  # ERROR level
LOG_20: Final[str] = "log.20"  # INFO level

# tracing.py  
SPAN_START: Final[str] = "span.start"
SPAN_END: Final[str] = "span.end"
```

## Domain Selection Guide

### When to Use Each Domain

Choose domains based on the questions you need to answer about system behavior.

**Use Logging when:**
- Investigating specific incidents with rich context
- Building audit trails requiring who/what/when
- Capturing detailed state snapshots for debugging
- Recording business events that stand alone

**Use Tracing when:**
- Understanding request flow through services
- Identifying performance bottlenecks
- Analyzing component dependencies
- Correlating distributed operations

**Use Metrics when:**
- Monitoring system health trends
- Setting up threshold-based alerts
- Capacity planning from historical patterns
- Tracking quantitative KPIs

### The Overlap Zone

Some scenarios benefit from multiple domains:

```python
# Log the business fact
logger.info("Order submitted", order_id=123, amount=99.99)

# Trace the execution mechanics
with Span("process_order", order_id=123) as span:
    with Span("validate_inventory"):
        # Check stock
    with Span("charge_payment"):
        # Process payment
```

The log captures the business event. The trace captures how we processed it.

## Creating New Domains

Introduce a new domain when encountering novel temporal patterns that existing domains cannot efficiently capture.

### Domain Creation Criteria

1. **Novel Event Structure** - Data relationships not captured by existing domains
2. **Specialized Processing** - Unique transformation requirements
3. **Different Consumption** - New query patterns or visualizations
4. **Domain-Specific Context** - Specialized enrichment needs

Example: A profiling domain might emit sampled stack traces - neither logs nor traces, but statistical performance snapshots with their own temporal characteristics.

### Domain Design Principles

When creating a domain:
- Define the core temporal model
- Identify primary consumption patterns
- Design hierarchical event types
- Plan for schema evolution
- Maintain zero-overhead guarantees

## Handler Layer

### Handler Types

**Sink Handlers** - Terminal I/O operations:
- `PrintHandler`: Formatted console output
- `JsonHandler`: JSON serialization
- `ManagedFileHandler`: File writing with rotation

**Control Handlers** - Flow modification:
- `filtered()`: Predicate-based filtering
- `sampled()`: Probabilistic sampling
- `AsyncHandlerWorker`: Async queue processing

**Composite Handlers** - Multi-handler coordination:
- `FanoutHandler`: Broadcast to multiple handlers
- `FallbackHandler`: Failover between handlers

### Handler Composition

Direct class instantiation for explicit configuration:

```python
# Development setup
dev_handlers = [
    PrintHandler(sys.stderr),
    ManagedFileHandler('debug.log')
]

# Production setup  
prod_handlers = [
    filtered(
        lambda e: e.get('level', 0) >= ERROR,
        JsonHandler(sys.stderr)
    ),
    sampled(0.01, AsyncHandlerWorker(
        BufferHandler(size=1000)
    ))
]

config = ObservabilityConfig(handlers=prod_handlers)
```

## Usage Patterns

### System Observability (Shared Context)

For infrastructure concerns using ambient access:

```python
# infrastructure/cache.py
from observability.shared import SharedContext
from observability.domains.logging import Logger

logger = Logger(__name__, SharedContext.get())

def get_cached_value(key: str) -> Optional[Any]:
    logger.debug("Cache lookup", key=key)
    # Implementation
```

### Domain Observability (Explicit Context)

For business logic requiring isolation:

```python
class OrderService:
    def __init__(self, obs_context: ObservabilityContext):
        self.logger = Logger('orders', obs_context)
        self.metrics = Counter('orders_processed', obs_context)
    
    def process_order(self, order_id: str):
        with Span('process_order', self.obs_context) as span:
            span.set_attribute('order_id', order_id)
            self.logger.info("Processing order", order_id=order_id)
            self.metrics.increment()
```

## Initialization Patterns

### Application Entry Point

```python
# main.py
from observability import ObservabilityConfig, SharedContext
from observability.handlers import JsonHandler

def main():
    # Initialize shared context once w/ sane defaults (print to stderr)
    SharedContext.setup()
    
    # Application runs with ambient access
    run_application()
```

### Library Pattern

```python
# Libraries accept optional contexts
class DataProcessor:
    def __init__(self, obs: Optional[ObservabilityContext] = None):
        # Use provided context or shared
        self.context = obs or SharedContext.get()
        self.logger = Logger('processor', self.context)
```

## Implementation Strategy

### Phase 1: Single Domain Adoption
Start with the domain matching your primary observability need:
- Debugging focus → Logging
- Performance focus → Tracing
- Monitoring focus → Metrics

Initialize with SharedContext for convenience:
```python
SharedContext.setup()
logger = Logger('myapp', SharedContext.get())
```

### Phase 2: Domain Expansion
Add complementary domains as needs emerge:
- Logging + Tracing for distributed debugging
- Metrics + Tracing for performance optimization
- All three for comprehensive observability

### Phase 3: Explicit Contexts
Create isolated contexts where needed:
```python
special_context = ObservabilityContext(special_config)
special_context.start()

# Pass explicitly for isolation
service = Service(special_context)
```

### Phase 4: Custom Domains
Identify novel temporal patterns in your system that warrant new domains. Follow the domain creation criteria and design principles.

## Conclusion

The Event-Driven Observability Architecture provides a foundation for capturing different temporal characteristics of system behavior. By understanding domains as distinct temporal models rather than just API variations, teams can select the right observability tool for each question they need to answer.

The architecture balances explicit dependency management with practical convenience through the dual context pattern. The SharedContext singleton acknowledges the reality of ambient logging needs while maintaining the option for explicit context injection where isolation matters. 

The unified event pipeline preserves domain semantics while enabling cross-domain correlation and consistent processing. The zero-overhead guarantee ensures observability can be pervasive without performance penalty, making comprehensive instrumentation practical for production systems.