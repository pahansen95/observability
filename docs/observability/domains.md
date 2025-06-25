# Domains

Domains provide specialized APIs for different observability concerns. Each domain captures distinct temporal characteristics of system behavior while emitting events through the unified pipeline.

## Domain Differentiation

Each domain answers different questions about system behavior:

| Domain | Temporal Model | Primary Question | Data Structure |
|--------|---------------|------------------|----------------|
| Logging | Discrete points in time | "What happened?" | Independent events |
| Tracing | Durations with relationships | "How did it flow?" | Hierarchical spans |
| Metrics | Time series for aggregation | "How much/often?" | Aggregatable values |

The architecture recognizes these as fundamentally different ways of observing time:

```
Time →
Logging:  • • • • • • • •  (forensic snapshots)
Tracing:  |---span1---|    (execution journeys)
          |--span2--|
Metrics:  ▁▃▅▇▅▃▁▃▅▇     (quantitative trends)
```

## Logging Domain

Captures discrete events for forensic analysis and debugging.

### API Design

```python
class Logger:
    def __init__(self, name: str, context: ObservabilityContext):
        self.name = name
        self._context = context
    
    def log(self, level: str, message: str, **kwargs) -> None:
        if not self._context.has_handlers():
            return
        
        self._context.emit(
            f'log.{level}',
            message,
            logger_name=self.name,
            **kwargs
        )
    
    # Convenience methods
    def debug(self, message: str, **kwargs) -> None:
        self.log('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self.log('info', message, **kwargs)
```

### Event Schema

```python
# Logging events
{
    'type': 'log.info',
    'value': 'User authenticated',
    'timestamp_ns': 123456789,
    'logger_name': 'auth.service',
    'user_id': 'usr_123',
    'method': 'oauth2'
}
```

## Tracing Domain

Captures execution flows with parent-child relationships.

### API Design

```python
class Span:
    def __init__(self, name: str, context: ObservabilityContext, 
                 parent: Optional['Span'] = None):
        self.name = name
        self.span_id = generate_span_id()
        self.parent_id = parent.span_id if parent else None
        self._context = context
        self._start_ns = time.perf_counter_ns()
        self._attributes = {}
    
    def __enter__(self) -> 'Span':
        if self._context.has_handlers():
            self._context.emit(
                'trace.span.start',
                {'name': self.name, 'span_id': self.span_id},
                parent_id=self.parent_id
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context.has_handlers():
            duration_ns = time.perf_counter_ns() - self._start_ns
            self._context.emit(
                'trace.span.end',
                {'duration_ns': duration_ns},
                span_id=self.span_id,
                attributes=self._attributes,
                error=exc_type is not None
            )
    
    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value
```

### Event Schema

```python
# Span start event
{
    'type': 'trace.span.start',
    'value': {'name': 'http_request', 'span_id': 'spn_abc'},
    'timestamp_ns': 123456789,
    'parent_id': 'spn_parent',
    'trace_id': 'trc_xyz'
}

# Span end event
{
    'type': 'trace.span.end',
    'value': {'duration_ns': 1500000},
    'timestamp_ns': 124956789,
    'span_id': 'spn_abc',
    'attributes': {'status_code': 200, 'method': 'GET'},
    'error': False
}
```

## Metrics Domain

Captures measurements for statistical analysis and monitoring.

### API Design

```python
class Counter:
    def __init__(self, name: str, context: ObservabilityContext,
                 unit: str = '1', description: str = ''):
        self.name = name
        self.unit = unit
        self.description = description
        self._context = context
    
    def increment(self, delta: float = 1.0, **labels) -> None:
        if not self._context.has_handlers():
            return
        
        self._context.emit(
            'metric.counter.increment',
            delta,
            metric_name=self.name,
            metric_type='counter',
            metric_unit=self.unit,
            metric_labels=labels
        )

class Gauge:
    def __init__(self, name: str, context: ObservabilityContext,
                 unit: str = '1', description: str = ''):
        self.name = name
        self.unit = unit
        self._context = context
    
    def set(self, value: float, **labels) -> None:
        if not self._context.has_handlers():
            return
        
        self._context.emit(
            'metric.gauge.set',
            value,
            metric_name=self.name,
            metric_type='gauge',
            metric_unit=self.unit,
            metric_labels=labels
        )
```

### Event Schema

```python
# Counter increment
{
    'type': 'metric.counter.increment',
    'value': 1.0,
    'timestamp_ns': 123456789,
    'metric_name': 'requests_total',
    'metric_type': 'counter',
    'metric_unit': '1',
    'metric_labels': {'endpoint': '/api/users', 'method': 'GET'}
}

# Gauge update
{
    'type': 'metric.gauge.set',
    'value': 42.5,
    'timestamp_ns': 123456789,
    'metric_name': 'memory_usage_bytes',
    'metric_type': 'gauge',
    'metric_unit': 'bytes',
    'metric_labels': {'process': 'worker-1'}
}
```

## Custom Domains

New domains should be created when you identify novel temporal patterns that don't fit existing domains.

### When to Create a Custom Domain

Create a new domain when:
- You have a distinct temporal model (not points, durations, or aggregations)
- The data requires specialized processing
- Existing domains would distort the semantics
- You need domain-specific optimizations

Examples of potential custom domains:
- **Audit Domain**: Immutable compliance records with legal retention
- **Profile Domain**: Sampled stack traces for performance analysis
- **Feature Domain**: Feature flag evaluations with experiment tracking

### Domain Development Process

#### 1. Define Temporal Model

Identify what aspect of time your domain captures:
```python
# Example: Audit domain captures immutable records
# Temporal model: Append-only sequence with legal timestamps
AUDIT_TEMPORAL_MODEL = "immutable_sequence"
```

#### 2. Design Event Schema

Define event types and required fields:
```python
# Event type constants
AUDIT_RECORD: Final[str] = "audit.record"
AUDIT_COMPLIANCE: Final[str] = "audit.compliance"

# Schema definition
AuditEvent = TypedDict('AuditEvent', {
    'action': str,
    'actor': str,
    'resource': str,
    'outcome': str,
    'legal_timestamp': str,  # RFC3339
})
```

#### 3. Implement Domain API

Create intuitive interfaces that emit structured events:
```python
class AuditLog:
    def __init__(self, system: str, context: ObservabilityContext):
        self.system = system
        self._context = context
    
    def record(self, action: str, actor: str, resource: str,
               outcome: str = 'success') -> None:
        if not self._context.has_handlers():
            return
        
        self._context.emit(
            AUDIT_RECORD,
            {
                'action': action,
                'actor': actor,
                'resource': resource,
                'outcome': outcome,
                'legal_timestamp': datetime.utcnow().isoformat() + 'Z'
            },
            audit_system=self.system,
            audit_version='1.0'
        )
```

#### 4. Consider Domain-Specific Handlers

Some domains benefit from specialized handlers:
```python
class AuditHandler:
    """Handler ensuring audit compliance."""
    
    def __init__(self, archive_path: str):
        self.archive_path = archive_path
        self._file = None
    
    def start(self) -> None:
        # Open with specific flags for compliance
        self._file = open(self.archive_path, 'ab')  # append, binary
    
    def __call__(self, event: EventDict) -> None:
        if event['type'].startswith('audit.'):
            # Ensure immutability with checksums
            record = {
                'event': event,
                'checksum': calculate_checksum(event)
            }
            self._file.write(json.dumps(record).encode() + b'\n')
            self._file.flush()  # Immediate persistence
            os.fsync(self._file.fileno())  # Ensure disk write
```

#### 5. Document Integration Patterns

Show how the domain integrates with the system:
```python
# Application integration
config = ObservabilityConfig(handlers=[
    AuditHandler('/var/audit/app.audit'),
    JsonHandler(sys.stderr)  # Also goes to general log
])
context = ObservabilityContext(config)
context.start()

# Create domain instance
audit = AuditLog('payment_system', context)

# Use in business logic
def process_payment(user_id: str, amount: float):
    audit.record(
        action='payment.process',
        actor=user_id,
        resource=f'amount:{amount}',
        outcome='initiated'
    )
    # ... payment logic ...
```

### Domain Design Principles

1. **Single Temporal Model**: Each domain captures one way of observing time
2. **Zero Overhead**: Check handlers before any work
3. **Event Completeness**: Events should be self-describing
4. **Handler Agnostic**: Domains emit events, don't prescribe processing
5. **Semantic Clarity**: Event types clearly indicate domain and action

### Performance Considerations

Maintain zero-overhead guarantees:
```python
def expensive_operation(self) -> Dict[str, Any]:
    # WRONG: Always computes
    data = compute_expensive_data()
    self._context.emit('domain.event', data)
    
    # RIGHT: Compute only if needed
    if not self._context.has_handlers():
        return
    data = compute_expensive_data()
    self._context.emit('domain.event', data)
```

## Integration Patterns

Domains integrate through the standard pipeline:

```python
# Create unified context
config = ObservabilityConfig(handlers=[...])
context = ObservabilityContext(config)
context.start()

# Instantiate multiple domains
logger = Logger('app', context)
tracer = Tracer(context)
metrics = MetricsRegistry(context)
audit = AuditLog('app', context)

# Use naturally in code
with tracer.span('process_request') as span:
    logger.info('Request started', request_id='req_123')
    metrics.counter('requests').increment()
    
    # Business logic
    result = process_business_logic()
    
    audit.record('data.accessed', user_id, resource_id)
    span.set_attribute('result', result)
```

All domains emit through the same context, enabling:
- Unified handler configuration
- Cross-domain correlation
- Consistent lifecycle management
- Shared context propagation