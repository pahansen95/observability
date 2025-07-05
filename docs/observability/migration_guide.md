# Observability API Migration Guide

This guide helps you update code to match the observability framework's API specifications.

## Method Renames

### Logger Methods

**Old:**
```python
logger = Logger("app", context)
child_logger = logger.getChild("module")
logger.setLevel(WARNING)
```

**New:**
```python
logger = Logger("app", context)
child_logger = logger.get_child("module")
logger.min_level = WARNING  # Property assignment
```

### Property Access

**Old:**
```python
# Private attribute access
span._operation
histogram._buckets
```

**New:**
```python
# Public property access
span.operation
histogram.buckets
```

## Parameter Order

### filtered() Function

**Old:**
```python
# Handler first, predicate second (incorrect)
handler = filtered(
    PrintHandler(sys.stdout),
    lambda e: e['type'] == 'log.error'
)
```

**New:**
```python
# Predicate first, handler second (correct)
handler = filtered(
    lambda e: e['type'] == 'log.error',
    PrintHandler(sys.stdout)
)
```

### sampled() Function

The parameter order remains: `sampled(rate, handler, seed=None)`

```python
# Correct usage
sampled_handler = sampled(0.1, PrintHandler(sys.stdout))
```

## Constructor Patterns

### Handler Constructors

Most handlers now require keyword arguments for clarity:

**Old:**
```python
print_handler = PrintHandler(sys.stdout)
queued_handler = QueuedHandler(slow_handler)
```

**New:**
```python
print_handler = PrintHandler(sys.stdout)  # stream is positional
queued_handler = QueuedHandler(wrapped_handler=slow_handler)
```

## Event Structure Changes

### Span Events

Use the dedicated methods instead of manual emission:

**Old:**
```python
context.emit("span.event", {"name": "payment_started", "attributes": {...}})
```

**New:**
```python
span.add_event("payment_started", {"amount": 99.99, "currency": "USD"})
```

### Span Status

**Old:**
```python
span.set_attribute("status", "success")
```

**New:**
```python
span.set_status(True, "Operation completed successfully")
# or
span.set_status(False, "Operation failed: timeout")
```

## Metric Labels

Static labels should be passed as kwargs to the constructor:

**Old:**
```python
counter = Counter("requests", context, labels={"service": "api", "env": "prod"})
```

**New:**
```python
counter = Counter("requests", context, service="api", env="prod")
```

## Timer Usage

Use the Timer context manager with histograms:

**Old:**
```python
histogram = Histogram("duration", context)
start = time.time()
# ... operation ...
histogram.observe((time.time() - start) * 1000)
```

**New:**
```python
from observability.domains.metrics import Timer

histogram = Histogram("duration", context)
with Timer(histogram, operation="query", table="users"):
    # ... operation ...
    pass  # Duration recorded automatically
```

## Conditional Logging

Use `is_enabled_for()` to avoid expensive operations:

**Old:**
```python
# Always computes expensive debug info
debug_info = compute_expensive_debug_info()
if logger.min_level <= DEBUG:
    logger.debug("Debug info", **debug_info)
```

**New:**
```python
# Only computes if DEBUG is enabled
if logger.is_enabled_for(DEBUG):
    debug_info = compute_expensive_debug_info()
    logger.debug("Debug info", **debug_info)
```

## Common Patterns

### Multi-level Handler Composition

```python
# Correct composition order
handler = filtered(
    lambda e: e.get('level', 0) >= ERROR,
    sampled(
        0.1,
        QueuedHandler(
            wrapped_handler=JsonHandler(sys.stdout)
        )
    )
)
```

### Static + Dynamic Labels

```python
# Static labels in constructor
gauge = Gauge("memory", context, service="api", host="server-01")

# Dynamic labels in method calls
gauge.set(1024 * 1024 * 512, process="worker-1", pool="default")
```

## Migration Checklist

- [ ] Replace all `getChild()` with `get_child()`
- [ ] Replace all `setLevel()` with `min_level =` 
- [ ] Remove underscore prefixes from attribute access
- [ ] Fix `filtered()` parameter order (predicate first)
- [ ] Update `QueuedHandler` to use `wrapped_handler=`
- [ ] Use `span.add_event()` for span events
- [ ] Use `span.set_status()` for span status
- [ ] Move static labels to constructor kwargs
- [ ] Use `Timer` class for duration measurements
- [ ] Add `is_enabled_for()` checks before expensive operations

## Validation

Use the provided validation script to check your code:

```bash
python scripts/validate_observability_examples.py
```

This will report any remaining API divergences.