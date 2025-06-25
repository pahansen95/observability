# Handlers

Handlers process events emitted through the observability pipeline. They form a composable tree structure enabling sophisticated event processing while maintaining simplicity.

## Handler Types

### Stateless Handlers

Pure functions that process events without maintaining state:

```python
def print_handler(event: EventDict) -> None:
    """Simple stateless handler."""
    print(f"[{event['type']}] {event['value']}")

# Or as a class
class PrintHandler:
    def __init__(self, file=None):
        self.file = file or sys.stderr
    
    def __call__(self, event: EventDict) -> None:
        print(f"[{event['type']}] {event['value']}", file=self.file)
```

Characteristics:
- No resource management needed
- Thread-safe by default
- Composable without coordination
- No initialization overhead

### Stateful Handlers

Manage persistent resources across multiple events:

```python
class ManagedFileHandler:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._file = None
    
    def start(self) -> None:
        """Acquire resources."""
        self._file = open(self.filepath, 'a')
    
    def stop(self) -> None:
        """Release resources."""
        if self._file:
            self._file.close()
    
    def __call__(self, event: EventDict) -> None:
        """Process using resources."""
        if self._file:
            json.dump(event, self._file)
            self._file.write('\n')
```

Characteristics:
- Explicit lifecycle management
- Resource efficiency through reuse
- Potential for batching/buffering
- Cleanup guarantees

## Built-in Handlers

### I/O Handlers

**PrintHandler** - Human-readable output:
```python
handler = PrintHandler(sys.stderr)
# Output: [log.info] User logged in
```

**JsonHandler** - Structured JSON output:
```python
handler = JsonHandler(sys.stdout)
# Output: {"type": "log.info", "value": "User logged in", ...}
```

**ManagedFileHandler** - Persistent file storage:
```python
handler = ManagedFileHandler('/var/log/app.log')
# Manages file lifecycle, handles rotation
```

### Control Handlers

**filtered()** - Conditional processing:
```python
error_handler = filtered(
    lambda e: e.get('level') == 'error',
    EmailHandler('alerts@example.com')
)
```

**sampled()** - Statistical sampling:
```python
sampled_handler = sampled(
    0.01,  # 1% sample rate
    ExpensiveHandler()
)
```

**rate_limited()** - Throttle event rate:
```python
limited_handler = rate_limited(
    100,  # events per second
    downstream_handler
)
```

### Composite Handlers

**QueuedHandler** - Asynchronous processing:
```python
handler = QueuedHandler(
    NetworkHandler('telemetry.service'),
    queue_size=10000
)
```

**BufferHandler** - Batch processing:
```python
handler = BufferHandler(
    size=1000,
    timeout_ms=5000,
    handler=BulkUploadHandler()
)
```

**FanOutHandler** - Multiple destinations:
```python
handler = FanOutHandler([
    JsonHandler(sys.stderr),
    ManagedFileHandler('app.log'),
    NetworkHandler('metrics.local')
])
```

## Handler Composition

Handlers compose naturally through wrapping:

```python
# Development configuration
dev_handler = PrintHandler()

# Production configuration
prod_handler = sampled(0.01,              # Sample 1%
    rate_limited(1000,                    # Max 1000/sec
        QueuedHandler(                    # Async processing
            BufferHandler(                # Batch for efficiency
                size=100,
                handler=NetworkHandler('telemetry.service')
            )
        )
    )
)

# Conditional routing
handler = FanOutHandler([
    filtered(lambda e: e['type'].startswith('metric.'),
        MetricsHandler()),
    filtered(lambda e: e['type'].startswith('log.'),
        LoggingHandler()),
    filtered(lambda e: e.get('level') == 'error',
        AlertHandler())
])
```

## Custom Handler Development

### Basic Handler Pattern

```python
class MyHandler:
    """Minimal custom handler."""
    
    def __call__(self, event: EventDict) -> None:
        # Process event
        process_event(event)
```

### Stateful Handler Pattern

```python
class DatabaseHandler:
    """Handler with resource management."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._conn = None
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Initialize database connection."""
        self._conn = create_connection(self.connection_string)
        self._conn.execute("PREPARE insert_event AS ...")
    
    def stop(self) -> None:
        """Close connection gracefully."""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
    
    def __call__(self, event: EventDict) -> None:
        """Insert event into database."""
        with self._lock:
            if self._conn:
                self._conn.execute("EXECUTE insert_event", event)
```

### Async Handler Pattern

```python
class AsyncNetworkHandler:
    """Non-blocking network handler."""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._session = None
        self._executor = None
    
    def start(self) -> None:
        self._session = aiohttp.ClientSession()
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    def stop(self) -> None:
        if self._executor:
            self._executor.shutdown(wait=True)
        if self._session:
            asyncio.run(self._session.close())
    
    def __call__(self, event: EventDict) -> None:
        # Submit to thread pool for async execution
        if self._executor:
            self._executor.submit(self._send_event, event)
    
    async def _send_event(self, event: EventDict) -> None:
        async with self._session.post(self.endpoint, json=event) as resp:
            await resp.text()
```

## Resource Management

### Lifecycle Best Practices

1. **Acquire Late**: Initialize resources in `start()`, not `__init__`
2. **Release Early**: Clean up promptly in `stop()`
3. **Handle Failures**: Gracefully degrade on resource errors
4. **Idempotent Operations**: Make start/stop safe to call multiple times

```python
class RobustHandler:
    def start(self) -> None:
        if hasattr(self, '_started') and self._started:
            return  # Already started
        
        try:
            self._resource = acquire_resource()
            self._started = True
        except Exception as e:
            logger.error(f"Failed to start handler: {e}")
            # Don't re-raise - degrade gracefully
    
    def stop(self) -> None:
        if hasattr(self, '_started') and self._started:
            try:
                self._resource.close()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                self._started = False
```

### Thread Safety

Stateful handlers must handle concurrent access:

```python
class ThreadSafeHandler:
    def __init__(self):
        self._lock = threading.Lock()
        self._buffer = []
    
    def __call__(self, event: EventDict) -> None:
        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= 100:
                self._flush()
    
    def _flush(self) -> None:
        # Must be called with lock held
        send_batch(self._buffer)
        self._buffer.clear()
```

### Error Handling

Handlers should never crash the application:

```python
class SafeHandler:
    def __call__(self, event: EventDict) -> None:
        try:
            self._process_event(event)
        except Exception as e:
            # Log but don't propagate
            error_logger.error(f"Handler error: {e}", exc_info=True)
```

## Performance Optimization

### Batching Strategy

```python
class BatchingHandler:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self._batch = []
        self._lock = threading.Lock()
    
    def __call__(self, event: EventDict) -> None:
        with self._lock:
            self._batch.append(event)
            if len(self._batch) >= self.batch_size:
                self._send_batch()
    
    def stop(self) -> None:
        # Flush remaining events
        with self._lock:
            if self._batch:
                self._send_batch()
```

### Memory Management

```python
class MemoryEfficientHandler:
    def __init__(self, max_memory_mb: int = 100):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._current_size = 0
    
    def __call__(self, event: EventDict) -> None:
        event_size = sys.getsizeof(event)
        
        if self._current_size + event_size > self.max_memory_bytes:
            self._flush()
        
        self._buffer_event(event)
        self._current_size += event_size
```

## Testing Handlers

### Unit Testing

```python
def test_handler_processes_events():
    # Arrange
    handler = MyHandler()
    event = {
        'type': 'test.event',
        'value': 'test data',
        'timestamp_ns': 123456789
    }
    
    # Act
    handler(event)
    
    # Assert
    assert handler.processed_count == 1
```

### Lifecycle Testing

```python
def test_handler_lifecycle():
    handler = StatefulHandler()
    
    # Test initialization
    handler.start()
    assert handler.is_connected()
    
    # Test processing
    handler({'type': 'test', 'value': 'data'})
    
    # Test cleanup
    handler.stop()
    assert not handler.is_connected()
    
    # Test idempotency
    handler.stop()  # Should not error
```

### Integration Testing

```python
def test_handler_with_context():
    # Create test context
    buffer = BufferHandler()
    context = ObservabilityContext(
        ObservabilityConfig(handlers=[buffer])
    )
    context.start()
    
    try:
        # Emit events
        logger = Logger('test', context)
        logger.info('Test message')
        
        # Verify handler received event
        events = buffer.get_events()
        assert len(events) == 1
        assert events[0]['value'] == 'Test message'
    finally:
        context.stop()
```