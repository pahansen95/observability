#!/usr/bin/env python3
"""
Example 67: Correlation Patterns

Demonstrates:
- Trace ID correlation across operations
- Request correlation through services
- Parent-child span relationships
- Cross-domain correlation
- Correlation context propagation
"""

import sys
import time
import uuid
import threading
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler, BufferHandler
from observability.domains.logging import Logger, INFO
from observability.domains.tracing import Span
from observability.domains.metrics import Counter


class CorrelationContext:
    """Manages correlation IDs across operations."""
    _local = threading.local()
    
    @classmethod
    def get_trace_id(cls):
        """Get current trace ID."""
        if not hasattr(cls._local, 'trace_id'):
            cls._local.trace_id = str(uuid.uuid4())
        return cls._local.trace_id
    
    @classmethod
    def set_trace_id(cls, trace_id):
        """Set trace ID for current thread."""
        cls._local.trace_id = trace_id
    
    @classmethod
    def get_request_id(cls):
        """Get current request ID."""
        return getattr(cls._local, 'request_id', None)
    
    @classmethod
    def set_request_id(cls, request_id):
        """Set request ID for current thread."""
        cls._local.request_id = request_id
    
    @classmethod
    def clear(cls):
        """Clear correlation context."""
        if hasattr(cls._local, 'trace_id'):
            del cls._local.trace_id
        if hasattr(cls._local, 'request_id'):
            del cls._local.request_id


class CorrelatedHandler:
    """Handler that adds correlation IDs to events."""
    def __init__(self, wrapped):
        self.wrapped = wrapped
    
    def __call__(self, event):
        # Add correlation IDs
        trace_id = CorrelationContext.get_trace_id()
        request_id = CorrelationContext.get_request_id()
        
        if trace_id:
            event['trace_id'] = trace_id
        if request_id:
            event['request_id'] = request_id
        
        self.wrapped(event)


def simulate_service_call(name, context):
    """Simulate a service call with correlation."""
    logger = Logger(name, context, INFO)
    counter = Counter(f"{name}_requests", context)
    
    # Create span with correlation
    with Span(f"{name}_operation", context) as span:
        # Add correlation IDs as attributes
        trace_id = CorrelationContext.get_trace_id()
        request_id = CorrelationContext.get_request_id()
        
        span.set_attribute("trace_id", trace_id)
        if request_id:
            span.set_attribute("request_id", request_id)
        
        logger.info(f"Starting {name} operation")
        counter.increment(1.0)
        
        # Simulate work
        time.sleep(0.05)
        
        # Simulate nested call
        if name == "service_a":
            simulate_service_call("service_b", context)
        
        logger.info(f"Completed {name} operation")


def process_request(request_id, context):
    """Process a request with full correlation."""
    # Set correlation context
    CorrelationContext.set_request_id(request_id)
    
    logger = Logger("api", context, INFO)
    
    try:
        # Start request processing
        with Span("handle_request", context) as span:
            span.set_attribute("request_id", request_id)
            span.set_attribute("trace_id", CorrelationContext.get_trace_id())
            
            logger.info(f"Processing request {request_id}")
            
            # Call services
            simulate_service_call("service_a", context)
            
            logger.info(f"Request {request_id} completed")
            
    finally:
        # Clear request ID
        CorrelationContext.clear()


def main():
    """Main example logic."""
    print("=== Example 67: Correlation Patterns ===\n")
    
    # Create context with correlation handler
    buffer_handler = BufferHandler()
    correlated_handler = CorrelatedHandler(
        PrintHandler(sys.stdout, format="[{trace_id}] {type}: {value}")
    )
    
    config = ObservabilityConfig(handlers=[correlated_handler, buffer_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Example 1: Basic trace correlation
    print("1. Basic trace correlation:")
    
    logger = Logger("app", context, INFO)
    
    # Set trace ID
    trace_id = str(uuid.uuid4())
    CorrelationContext.set_trace_id(trace_id)
    
    logger.info("Starting operation")
    with Span("main_operation", context) as span:
        span.set_attribute("trace_id", trace_id)
        logger.info("Inside span")
    logger.info("Operation complete")
    
    # Example 2: Request correlation
    print("\n2. Request correlation:")
    
    # Simulate multiple requests
    for i in range(3):
        request_id = f"REQ-{i:04d}"
        print(f"\n   Processing {request_id}")
        process_request(request_id, context)
    
    # Example 3: Cross-thread correlation
    print("\n3. Cross-thread correlation:")
    
    def threaded_operation(thread_id, parent_trace_id):
        """Operation in a thread with inherited trace ID."""
        # Inherit parent trace ID
        CorrelationContext.set_trace_id(parent_trace_id)
        
        logger = Logger(f"thread-{thread_id}", context, INFO)
        logger.info(f"Thread {thread_id} starting")
        
        with Span(f"thread_{thread_id}_work", context) as span:
            span.set_attribute("trace_id", parent_trace_id)
            span.set_attribute("thread_id", thread_id)
            time.sleep(0.1)
        
        logger.info(f"Thread {thread_id} complete")
    
    # Get parent trace ID
    parent_trace = CorrelationContext.get_trace_id()
    
    # Start threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=threaded_operation, args=(i, parent_trace))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    print("\n   All threads completed with same trace ID")
    
    # Example 4: Correlation analysis
    print("\n4. Correlation analysis:")
    
    events = buffer_handler.get_events()
    
    # Group by trace ID
    traces = {}
    for event in events:
        trace_id = event.get('trace_id')
        if trace_id:
            if trace_id not in traces:
                traces[trace_id] = []
            traces[trace_id].append(event)
    
    print(f"   Found {len(traces)} unique traces")
    
    # Analyze a trace
    for trace_id, trace_events in list(traces.items())[:1]:
        print(f"\n   Trace {trace_id[:8]}...:")
        print(f"     Events: {len(trace_events)}")
        
        # Count by type
        type_counts = {}
        for event in trace_events:
            event_type = event['type'].split('.')[0]
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        for event_type, count in type_counts.items():
            print(f"     - {event_type}: {count}")
    
    # Example 5: Request flow visualization
    print("\n5. Request flow visualization:")
    
    # Find a request with spans
    request_events = [e for e in events if 'request_id' in e]
    if request_events:
        request_id = request_events[0]['request_id']
        request_trace = [e for e in request_events if e.get('request_id') == request_id]
        
        print(f"\n   Request {request_id} flow:")
        
        # Show span hierarchy
        spans = [e for e in request_trace if e['type'].startswith('span.')]
        for event in spans:
            if event['type'] == 'span.start':
                indent = "  " * (1 if 'parent_id' in event else 0)
                print(f"   {indent}→ {event['value']}")
    
    # Example 6: Distributed context
    print("\n6. Distributed context patterns:")
    
    class DistributedContext:
        """Simulates context propagation across services."""
        def __init__(self):
            self.headers = {}
        
        def inject(self):
            """Inject correlation into headers."""
            self.headers['X-Trace-ID'] = CorrelationContext.get_trace_id()
            request_id = CorrelationContext.get_request_id()
            if request_id:
                self.headers['X-Request-ID'] = request_id
            return self.headers
        
        def extract(self, headers):
            """Extract correlation from headers."""
            if 'X-Trace-ID' in headers:
                CorrelationContext.set_trace_id(headers['X-Trace-ID'])
            if 'X-Request-ID' in headers:
                CorrelationContext.set_request_id(headers['X-Request-ID'])
    
    # Simulate service-to-service call
    print("\n   Service A calling Service B:")
    
    # Service A
    dist_ctx = DistributedContext()
    headers = dist_ctx.inject()
    print(f"   Service A sends headers: {headers}")
    
    # Service B receives
    dist_ctx.extract(headers)
    logger = Logger("service-b", context, INFO)
    logger.info("Service B processing with propagated context")
    
    context.stop()
    
    print("\n   Correlation enables tracing requests across distributed systems")


if __name__ == '__main__':
    main()