"""
Tests for real-world usage patterns.

Demonstrates how the observability system works in common application
scenarios like web applications and background task processing.
"""

import pytest
import io
import json
import time
import uuid
import threading
from observability import (
    ObservabilityContext,
    ObservabilityConfig,
    SharedContext,
    trace_id,
    request_id,
    operation_id,
    JsonHandler,
    BufferHandler,
    filtered,
)
from observability.domains.logging import Logger
from observability.domains.tracing import Span
from observability.domains.metrics import Counter, Histogram, Gauge


def test_web_application_pattern():
    """Common web app observability setup."""
    # Setup shared context with multiple handlers
    json_output = io.StringIO()
    error_buffer = BufferHandler()
    
    config = ObservabilityConfig(handlers=[
        JsonHandler(json_output),
        filtered(lambda e: e.get('level') == 40, error_buffer)  # ERROR level
    ])
    
    SharedContext._ctx = None
    SharedContext.setup(config)
    
    # Create domain objects
    logger = Logger('webapp', SharedContext.get())
    request_counter = Counter('http_requests', SharedContext.get())
    response_time = Histogram('http_response_time', SharedContext.get())
    
    # Simulate request handling
    def handle_request(path: str):
        trace_id.set(f'trace-{path.replace("/", "-")}')
        
        with Span('http_request', SharedContext.get()) as span:
            span.set_attribute('path', path)
            
            logger.info("Request received", path=path)
            request_counter.increment(path=path)
            
            # Simulate work
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
    json_lines = json_output.getvalue().strip().split('\n')
    assert len(json_lines) > 0
    
    # Parse first line to verify structure
    first_event = json.loads(json_lines[0])
    assert 'type' in first_event
    assert 'timestamp_ns' in first_event
    
    # No errors should have occurred
    assert error_buffer.get_events() == []
    
    SharedContext.teardown()


def test_background_task_pattern():
    """Background task observability."""
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
        time.sleep(0.001)
        
        logger.debug("Task completed")
        tasks_processed.increment()
        queue_size.set(queue_len - 1)
    
    # Process some tasks
    process_task("TASK-001", 10)
    process_task("TASK-002", 9)
    
    # Each task should have unique operation_id
    operation_ids = [e.get('operation_id') for e in events if e.get('operation_id')]
    unique_ids = set(operation_ids)
    assert len(unique_ids) == 2  # Two unique IDs
    
    # Verify metrics were recorded
    counter_events = [e for e in events if e['type'] == 'metric.counter']
    assert len(counter_events) == 2
    
    gauge_events = [e for e in events if e['type'] == 'metric.gauge']
    assert len(gauge_events) == 4  # 2 sets per task


def test_microservice_pattern():
    """Microservice with distributed tracing."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('order-service', context)
    
    def process_order(order_id: str, incoming_trace_id: str):
        # Propagate trace ID from incoming request
        trace_id.set(incoming_trace_id)
        request_id.set(f'req-{order_id}')
        
        with Span('process_order', context) as span:
            span.set_attribute('order_id', order_id)
            
            logger.info("Processing order", order_id=order_id)
            
            # Validate order
            with span.start_child('validate_order'):
                logger.debug("Validating order")
                time.sleep(0.001)
            
            # Check inventory
            with span.start_child('check_inventory') as inv_span:
                logger.debug("Checking inventory")
                inv_span.set_attribute('items_checked', 3)
                time.sleep(0.002)
            
            # Process payment
            with span.start_child('process_payment'):
                logger.debug("Processing payment")
                time.sleep(0.001)
            
            logger.info("Order processed successfully")
    
    # Process an order
    process_order("ORD-12345", "trace-abc-123")
    
    # Verify trace propagation
    trace_events = [e for e in events if e.get('trace_id') == 'trace-abc-123']
    assert len(trace_events) == len(events)  # All events have trace ID
    
    # Verify span hierarchy
    span_starts = [e for e in events if e['type'] == 'span.start']
    assert len(span_starts) == 4  # Main + 3 children


def test_api_gateway_pattern():
    """API gateway with request routing and monitoring."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('api-gateway', context)
    route_counter = Counter('api_routes', context)
    auth_counter = Counter('auth_attempts', context)
    latency = Histogram('gateway_latency', context)
    
    class APIGateway:
        def __init__(self):
            self.routes = {
                '/api/users': 'user-service',
                '/api/orders': 'order-service',
                '/api/products': 'product-service',
            }
        
        def handle_request(self, method: str, path: str, auth_token: str):
            req_id = str(uuid.uuid4())
            request_id.set(req_id)
            
            with Span('gateway_request', context) as span:
                span.set_attribute('method', method)
                span.set_attribute('path', path)
                
                # Authentication
                with span.start_child('authenticate') as auth_span:
                    auth_success = self._authenticate(auth_token)
                    auth_span.set_attribute('auth_success', auth_success)
                    auth_counter.increment(auth_success=str(auth_success).lower())
                    
                    if not auth_success:
                        logger.warning("Authentication failed", path=path)
                        return 401
                
                # Route request
                with span.start_child('route') as route_span:
                    service = self.routes.get(path)
                    if not service:
                        logger.warning("Route not found", path=path)
                        return 404
                    
                    route_span.set_attribute('target_service', service)
                    route_counter.increment(service=service, method=method)
                    
                    # Simulate service call
                    start = time.time()
                    time.sleep(0.005)
                    duration = time.time() - start
                    
                    latency.observe(duration, service=service)
                    logger.info("Request routed", service=service, duration_ms=duration*1000)
                
                return 200
        
        def _authenticate(self, token: str) -> bool:
            return token == "valid-token"
    
    # Use the gateway
    gateway = APIGateway()
    
    # Successful request
    status = gateway.handle_request('GET', '/api/users', 'valid-token')
    assert status == 200
    
    # Failed auth
    status = gateway.handle_request('POST', '/api/orders', 'invalid-token')
    assert status == 401
    
    # Not found
    status = gateway.handle_request('GET', '/api/unknown', 'valid-token')
    assert status == 404
    
    # Verify metrics
    auth_events = [e for e in events if e['type'] == 'metric.counter' and e['value'] == 'auth_attempts']
    assert len(auth_events) == 3


def test_batch_processing_pattern():
    """Batch job processing with progress tracking."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('batch-processor', context)
    batch_counter = Counter('batches_processed', context)
    items_counter = Counter('items_processed', context)
    progress_gauge = Gauge('batch_progress', context)
    error_counter = Counter('processing_errors', context)
    
    class BatchProcessor:
        def process_batch(self, batch_id: str, items: list):
            trace_id.set(f'batch-{batch_id}')
            
            with Span('batch_processing', context) as span:
                span.set_attribute('batch_id', batch_id)
                span.set_attribute('item_count', len(items))
                
                logger.info(f"Starting batch {batch_id}", item_count=len(items))
                
                processed = 0
                errors = 0
                
                for i, item in enumerate(items):
                    with span.start_child(f'process_item_{i}') as item_span:
                        item_span.set_attribute('item_id', item['id'])
                        
                        try:
                            # Simulate processing
                            if item.get('error'):
                                raise ValueError(f"Error processing {item['id']}")
                            
                            time.sleep(0.001)
                            items_counter.increment()
                            processed += 1
                            
                        except Exception as e:
                            logger.error(f"Item processing failed", item_id=item['id'], error=str(e))
                            error_counter.increment()
                            errors += 1
                        
                        # Update progress
                        progress = (i + 1) / len(items) * 100
                        progress_gauge.set(progress, batch_id=batch_id)
                
                batch_counter.increment()
                logger.info(f"Batch completed", processed=processed, errors=errors)
    
    # Process a batch
    processor = BatchProcessor()
    items = [
        {'id': 'item1'},
        {'id': 'item2'},
        {'id': 'item3', 'error': True},  # This will fail
        {'id': 'item4'},
    ]
    
    processor.process_batch('batch-001', items)
    
    # Verify processing
    item_events = [e for e in events if e['type'] == 'metric.counter' and e['value'] == 'items_processed']
    assert len(item_events) == 3  # 3 successful
    
    error_events = [e for e in events if e['type'] == 'metric.counter' and e['value'] == 'processing_errors']
    assert len(error_events) == 1  # 1 error
    
    # Check progress updates
    progress_events = [e for e in events if e['type'] == 'metric.gauge' and e['value'] == 'batch_progress']
    assert len(progress_events) == 4  # One per item
    assert progress_events[-1]['measurement'] == 100.0  # Final progress


def test_cache_aware_service():
    """Service with cache monitoring."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('cache-service', context)
    cache_hits = Counter('cache_hits', context)
    cache_misses = Counter('cache_misses', context)
    cache_latency = Histogram('cache_latency', context)
    
    class CachedService:
        def __init__(self):
            self.cache = {}
        
        def get_data(self, key: str):
            with Span('get_data', context) as span:
                span.set_attribute('key', key)
                
                start = time.time()
                
                # Check cache
                if key in self.cache:
                    duration = time.time() - start
                    cache_latency.observe(duration, result='hit')
                    cache_hits.increment()
                    logger.debug("Cache hit", key=key)
                    span.set_attribute('cache_hit', True)
                    return self.cache[key]
                
                # Cache miss - fetch data
                with span.start_child('fetch_data'):
                    logger.debug("Cache miss, fetching data", key=key)
                    cache_misses.increment()
                    
                    # Simulate data fetch
                    time.sleep(0.005)
                    data = f"data_for_{key}"
                    
                    # Store in cache
                    self.cache[key] = data
                    span.set_attribute('cache_hit', False)
                
                duration = time.time() - start
                cache_latency.observe(duration, result='miss')
                
                return data
    
    # Use the service
    service = CachedService()
    
    # First calls - all misses
    service.get_data('key1')
    service.get_data('key2')
    
    # Second calls - all hits
    service.get_data('key1')
    service.get_data('key2')
    
    # Verify metrics
    hit_events = [e for e in events if e['type'] == 'metric.counter' and e['value'] == 'cache_hits']
    miss_events = [e for e in events if e['type'] == 'metric.counter' and e['value'] == 'cache_misses']
    
    assert len(hit_events) == 2
    assert len(miss_events) == 2