# Observability Package - Behavioral Test Plan

## Test Philosophy

Validate happy path behaviors and core functionality during active framework development. Focus on ensuring documented features work correctly and domains integrate smoothly.

## 1. Core Functionality

### 1.1 Basic Event Emission
```python
def test_basic_event_emission():
    """Events flow from context to handlers."""
    received = []
    
    context = ObservabilityContext()
    context.attach_handler(lambda e: received.append(e))
    
    context.emit('test.event', 'hello', custom='metadata')
    
    assert len(received) == 1
    assert received[0]['type'] == 'test.event'
    assert received[0]['value'] == 'hello'
    assert received[0]['custom'] == 'metadata'
    assert 'timestamp_ns' in received[0]
```

### 1.2 Context Variable Propagation
```python
def test_context_variables_flow():
    """Context variables automatically attach to events."""
    from observability import trace_id, request_id, operation_id
    
    captured = {}
    
    context = ObservabilityContext()
    context.attach_handler(lambda e: captured.update(e))
    
    # Set context variables
    trace_id.set('trace-123')
    request_id.set('req-456')
    operation_id.set('op-789')
    
    context.emit('test', 'value')
    
    assert captured['trace_id'] == 'trace-123'
    assert captured['request_id'] == 'req-456'
    assert captured['operation_id'] == 'op-789'
```

### 1.3 Handler Lifecycle Management
```python
def test_handler_lifecycle():
    """Stateful handlers start and stop properly."""
    lifecycle = []
    
    class ManagedHandler:
        def start(self):
            lifecycle.append('started')
        def stop(self):
            lifecycle.append('stopped')
        def __call__(self, event):
            lifecycle.append('called')
    
    context = ObservabilityContext()
    context.attach_handler(ManagedHandler())
    
    context.start()
    context.emit('test', 'value')
    context.stop()
    
    assert lifecycle == ['started', 'called', 'stopped']
```

## 2. Domain Integration

### 2.1 Logger Domain
```python
def test_logger_domain():
    """Logger domain emits structured log events."""
    from observability.domains.logging import Logger
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('myapp', context)
    logger.info("Application started", version='1.0')
    logger.error("Connection failed", retry_count=3)
    
    assert len(events) == 2
    assert events[0]['type'] == 'log.20'  # INFO level
    assert events[0]['value'] == "Application started"
    assert events[0]['version'] == '1.0'
    assert events[1]['type'] == 'log.40'  # ERROR level
```

### 2.2 Tracing Domain
```python
def test_tracing_domain():
    """Span domain tracks execution flow."""
    from observability.domains.tracing import Span
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('process_request', context) as span:
        span.set_attribute('user_id', 12345)
        span.set_attribute('endpoint', '/api/users')
    
    assert len(events) == 2
    assert events[0]['type'] == 'trace.span.start'
    assert events[1]['type'] == 'trace.span.end'
    assert events[1]['attributes']['user_id'] == 12345
    assert 'duration_ns' in events[1]['value']
```

### 2.3 Metrics Domain
```python
def test_metrics_domain():
    """Metrics domain emits measurement events."""
    from observability.domains.metrics import Counter, Gauge, Histogram
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    # Counter usage
    counter = Counter('api_requests', context, endpoint='/users')
    counter.increment()
    counter.increment(5)
    
    # Gauge usage
    gauge = Gauge('queue_size', context)
    gauge.set(42)
    
    # Histogram usage
    histogram = Histogram('response_time', context)
    histogram.observe(0.123)
    
    assert len(events) == 5
    assert events[0]['type'] == 'metric.counter'
    assert events[0]['value'] == 1.0
    assert events[2]['type'] == 'metric.gauge'
    assert events[3]['type'] == 'metric.histogram'
```

### 2.4 Multi-Domain Integration
```python
def test_domains_work_together():
    """Multiple domains share context and handlers."""
    from observability.domains.logging import Logger
    from observability.domains.tracing import Span
    from observability.domains.metrics import Counter
    from observability import trace_id
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('webapp', context)
    counter = Counter('requests', context)
    
    # Simulate request handling
    trace_id.set('abc-123')
    
    with Span('handle_request', context):
        logger.info("Request started")
        counter.increment()
        
        with Span('database_query', context):
            logger.debug("Querying database")
        
        logger.info("Request completed")
    
    # All events should have the trace ID
    for event in events:
        assert event.get('trace_id') == 'abc-123'
    
    # Should have mixed event types
    event_types = [e['type'] for e in events]
    assert any(t.startswith('log.') for t in event_types)
    assert any(t.startswith('trace.') for t in event_types)
    assert any(t.startswith('metric.') for t in event_types)
```

## 3. Handler Patterns

### 3.1 Handler Composition
```python
def test_handler_composition():
    """Handlers compose through standard patterns."""
    from observability.handlers import filtered, sampled, FanoutHandler
    
    results = {'all': [], 'errors': [], 'sampled': []}
    
    # All events
    all_handler = lambda e: results['all'].append(e['value'])
    
    # Only errors
    error_handler = filtered(
        lambda e: e.get('level') == 'error',
        lambda e: results['errors'].append(e['value'])
    )
    
    # 10% sample
    sampled_handler = sampled(
        0.1,
        lambda e: results['sampled'].append(e['value'])
    )
    
    fanout = FanoutHandler(all_handler, error_handler, sampled_handler)
    
    context = ObservabilityContext()
    context.attach_handler(fanout)
    
    # Emit various events
    context.emit('log', 'info1', level='info')
    context.emit('log', 'error1', level='error')
    context.emit('log', 'info2', level='info')
    context.emit('log', 'error2', level='error')
    
    assert results['all'] == ['info1', 'error1', 'info2', 'error2']
    assert results['errors'] == ['error1', 'error2']
    assert len(results['sampled']) < 4  # Roughly 10%
```

### 3.2 Resource Handlers
```python
def test_resource_handlers():
    """Resource-based handlers manage lifecycle."""
    from observability.handlers import ManagedFileHandler, BufferHandler, QueuedHandler
    import tempfile
    import os
    
    # File handler
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filepath = tmp.name
    
    file_handler = ManagedFileHandler(filepath, format='json')
    
    # Buffer handler
    buffer = BufferHandler(max_size=100)
    
    # Queued handler wraps file handler
    queued = QueuedHandler(file_handler)
    
    context = ObservabilityContext()
    context.attach_handler(buffer)
    context.attach_handler(queued)
    
    context.start()
    
    # Emit events
    for i in range(5):
        context.emit('test', f'event_{i}')
    
    context.stop()
    
    # Buffer should have all events
    assert len(buffer.get_events()) == 5
    
    # File should have events (after queue drain)
    assert os.path.exists(filepath)
    with open(filepath) as f:
        content = f.read()
        assert 'event_0' in content
    
    os.unlink(filepath)
```

## 4. Configuration

### 4.1 Configuration Application
```python
def test_configuration_applied():
    """Configuration properly initializes context."""
    from observability import ObservabilityConfig
    
    events = []
    handler = lambda e: events.append(e)
    
    config = ObservabilityConfig(
        handlers=[handler],
        sampling_rate=1.0,
        enabled_categories={'log', 'metric'}
    )
    
    context = ObservabilityContext(config)
    
    # Should have handler attached
    context.emit('log.info', 'test')
    assert len(events) == 1
    
    # Category filtering works
    context.emit('trace.span', 'filtered')
    assert len(events) == 1  # Not increased
    
    context.emit('metric.counter', 'allowed')
    assert len(events) == 2
```

### 4.2 SharedContext Pattern
```python
def test_shared_context():
    """SharedContext provides singleton access."""
    from observability import SharedContext, ObservabilityConfig
    from observability.domains.logging import Logger
    
    events = []
    config = ObservabilityConfig(handlers=[lambda e: events.append(e)])
    
    # Reset for test
    SharedContext._ctx = None
    SharedContext.setup(config)
    
    # Create logger with lazy binding
    logger = Logger('service', SharedContext.get)
    logger.info("Using shared context")
    
    # Direct access also works
    ctx = SharedContext.get()
    ctx.emit('custom', 'event')
    
    assert len(events) == 2
```

## 5. Custom Domain Implementation

### 5.1 Basic Custom Domain
```python
def test_custom_domain_implementation():
    """Custom domains integrate with the system."""
    from typing import Final
    
    # Define custom domain
    class SecurityAuditor:
        """Custom domain for security events."""
        
        AUDIT_PREFIX: Final[str] = "security.audit"
        
        def __init__(self, context):
            self._context = context
        
        def login_attempt(self, username: str, success: bool):
            if not self._context.has_handlers():
                return
            
            self._context.emit(
                f"{self.AUDIT_PREFIX}.login",
                {"username": username, "success": success},
                severity="info" if success else "warning"
            )
        
        def permission_check(self, user: str, resource: str, granted: bool):
            if not self._context.has_handlers():
                return
                
            self._context.emit(
                f"{self.AUDIT_PREFIX}.permission",
                {"user": user, "resource": resource, "granted": granted}
            )
    
    # Use custom domain
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    auditor = SecurityAuditor(context)
    auditor.login_attempt("alice", True)
    auditor.permission_check("alice", "/admin", False)
    
    assert len(events) == 2
    assert events[0]['type'] == 'security.audit.login'
    assert events[0]['value']['username'] == 'alice'
    assert events[1]['type'] == 'security.audit.permission'
```

### 5.2 Custom Domain with Context Variables
```python
def test_custom_domain_with_context():
    """Custom domains can use context variables."""
    from observability import request_id
    import contextvars
    
    # Custom context variable
    user_id = contextvars.ContextVar('user_id', default=None)
    
    class APITracker:
        def __init__(self, context):
            self._context = context
        
        def track_call(self, method: str, path: str):
            if not self._context.has_handlers():
                return
            
            # Capture custom context
            metadata = {"method": method, "path": path}
            if uid := user_id.get():
                metadata['user_id'] = uid
            
            self._context.emit("api.call", metadata)
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    tracker = APITracker(context)
    
    # Set context and track
    request_id.set('req-789')
    user_id.set('user-123')
    tracker.track_call('GET', '/api/profile')
    
    event = events[0]
    assert event['request_id'] == 'req-789'
    assert event['value']['user_id'] == 'user-123'
```

### 5.3 Custom Domain Handler
```python
def test_custom_domain_specific_handler():
    """Custom handlers can process domain-specific events."""
    
    class BusinessMetricsHandler:
        """Handler that only processes business metrics."""
        
        def __init__(self):
            self.revenue_total = 0.0
            self.order_count = 0
        
        def __call__(self, event):
            if event['type'] == 'business.order.completed':
                self.order_count += 1
                self.revenue_total += event['value']['amount']
            elif event['type'] == 'business.refund.processed':
                self.revenue_total -= event['value']['amount']
    
    # Business domain
    class BusinessTracker:
        def __init__(self, context):
            self._context = context
        
        def order_completed(self, order_id: str, amount: float):
            self._context.emit(
                'business.order.completed',
                {'order_id': order_id, 'amount': amount}
            )
        
        def refund_processed(self, order_id: str, amount: float):
            self._context.emit(
                'business.refund.processed',
                {'order_id': order_id, 'amount': amount}
            )
    
    # Wire together
    handler = BusinessMetricsHandler()
    context = ObservabilityContext()
    context.attach_handler(handler)
    
    tracker = BusinessTracker(context)
    
    # Track business events
    tracker.order_completed('ORD-001', 99.99)
    tracker.order_completed('ORD-002', 150.00)
    tracker.refund_processed('ORD-001', 99.99)
    
    assert handler.order_count == 2
    assert handler.revenue_total == 150.00
```

## 6. Real Usage Patterns

### 6.1 Web Application Pattern
```python
def test_web_application_pattern():
    """Common web app observability setup."""
    from observability import SharedContext, ObservabilityConfig, trace_id
    from observability.handlers import JsonHandler, BufferHandler, filtered
    from observability.domains.logging import Logger
    from observability.domains.tracing import Span
    from observability.domains.metrics import Counter, Histogram
    import io
    
    # Setup shared context with multiple handlers
    json_output = io.StringIO()
    error_buffer = BufferHandler()
    
    config = ObservabilityConfig(handlers=[
        JsonHandler(json_output),
        filtered(lambda e: e.get('level') == 'error', error_buffer)
    ])
    
    SharedContext.setup(config)
    
    # Create domain objects
    logger = Logger('webapp', SharedContext.get)
    request_counter = Counter('http_requests', SharedContext.get)
    response_time = Histogram('http_response_time', SharedContext.get)
    
    # Simulate request handling
    def handle_request(path: str):
        trace_id.set(f'trace-{path}')
        
        with Span('http_request', SharedContext.get()) as span:
            span.set_attribute('path', path)
            
            logger.info("Request received", path=path)
            request_counter.increment(path=path)
            
            # Simulate work
            import time
            start = time.time()
            time.sleep(0.01)
            duration = time.time() - start
            
            response_time.observe(duration, path=path)
            logger.info("Request completed", duration=duration)
        
        return "OK"
    
    # Handle some requests
    handle_request('/api/users')
    handle_request('/api/posts')
    
    # Verify outputs
    assert '"Request received"' in json_output.getvalue()
    assert error_buffer.get_events() == []  # No errors
```

### 6.2 Background Task Pattern
```python
def test_background_task_pattern():
    """Background task observability."""
    from observability.domains.logging import Logger
    from observability.domains.metrics import Counter, Gauge
    from observability import operation_id
    import uuid
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('worker', context)
    tasks_processed = Counter('tasks_processed', context)
    queue_size = Gauge('queue_size', context)
    
    def process_task(task_id: str, queue_len: int):
        operation_id.set(str(uuid.uuid4()))
        
        logger.info(f"Processing task {task_id}")
        queue_size.set(queue_len)
        
        # Simulate work
        logger.debug("Task completed")
        tasks_processed.increment()
        queue_size.set(queue_len - 1)
    
    # Process some tasks
    process_task("TASK-001", 10)
    process_task("TASK-002", 9)
    
    # Each task should have unique operation_id
    operation_ids = [e.get('operation_id') for e in events if e.get('operation_id')]
    assert len(set(operation_ids)) == 2  # Two unique IDs
```

## Test Execution

These tests validate that:
1. Core functionality works as designed
2. All domains integrate properly
3. Handlers compose correctly
4. Custom domains can be implemented
5. Real-world patterns are supported

Focus remains on happy path validation during active framework development.