#!/usr/bin/env python3
"""
Example 22: Tracing Async

Demonstrates:
- Creating spans in async functions
- Using asyncio.gather for concurrent spans
- Trace context propagation across tasks
- Span timing for async operations
- Using asyncio.run() to execute
"""

import asyncio
from observability import ObservabilityContext, ObservabilityConfig, trace_id
from observability.handlers import BufferHandler, PrintHandler
from observability.domains.tracing import Span


async def fetch_user_data(user_id: str, context: ObservabilityContext):
    """Simulate async user data fetch."""
    with Span(f"fetch_user_{user_id}", context) as span:
        span.set_attribute("user_id", user_id)
        await asyncio.sleep(0.1)  # Simulate API call
        span.set_attribute("status", "success")
        return {"id": user_id, "name": f"User {user_id}"}


async def fetch_user_orders(user_id: str, context: ObservabilityContext):
    """Simulate async order fetch."""
    with Span(f"fetch_orders_{user_id}", context) as span:
        span.set_attribute("user_id", user_id)
        await asyncio.sleep(0.15)  # Simulate database query
        order_count = 5
        span.set_attribute("order_count", order_count)
        return [f"order_{i}" for i in range(order_count)]


async def process_user(user_id: str, context: ObservabilityContext):
    """Process a single user with nested async operations."""
    with Span(f"process_user_{user_id}", context) as span:
        span.set_attribute("user_id", user_id)
        
        # Fetch user data and orders concurrently
        user_data, orders = await asyncio.gather(
            fetch_user_data(user_id, context),
            fetch_user_orders(user_id, context)
        )
        
        span.set_attribute("orders_found", len(orders))
        return {"user": user_data, "orders": orders}


async def main_async():
    """Async main function."""
    print("=== Example 22: Tracing Async ===\n")
    
    # Create context with handlers
    print("1. Creating context with handlers")
    buffer_handler = BufferHandler()
    print_handler = PrintHandler(format="[{type}] {operation}")
    config = ObservabilityConfig(handlers=[buffer_handler, print_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Set trace ID for correlation
    print("\n2. Setting trace ID for correlation")
    trace_id.set("async-trace-123")
    print(f"   Trace ID: {trace_id.get()}")
    
    # Create root span for entire operation
    print("\n3. Creating root span and processing users concurrently")
    with Span("batch_process_users", context) as root_span:
        root_span.set_attribute("batch_size", 3)
        
        # Process multiple users concurrently
        user_ids = ["user1", "user2", "user3"]
        results = await asyncio.gather(*[
            process_user(user_id, context)
            for user_id in user_ids
        ])
        
        root_span.set_attribute("processed_count", len(results))
    
    # Examine concurrent execution
    print("\n4. Examining concurrent span execution:")
    events = buffer_handler.get_events()
    span_events = [e for e in events if e['type'].startswith('trace.span')]
    
    # Group by operation type
    fetch_user_spans = [e for e in span_events if 'fetch_user_' in e.get('operation', '')]
    fetch_order_spans = [e for e in span_events if 'fetch_orders_' in e.get('operation', '')]
    
    print(f"   Fetch user spans: {len(fetch_user_spans) // 2}")  # Divide by 2 for start+end
    print(f"   Fetch order spans: {len(fetch_order_spans) // 2}")
    
    # Verify trace context propagation
    print("\n5. Verifying trace context propagation:")
    trace_ids = set()
    for event in span_events:
        if 'trace_id' in event:
            trace_ids.add(event['trace_id'])
    
    print(f"   Unique trace IDs: {len(trace_ids)}")
    print(f"   All spans share same trace: {len(trace_ids) == 1}")
    
    # Show timing of concurrent operations
    print("\n6. Timing of concurrent operations:")
    span_timings = {}
    
    for event in span_events:
        if event['type'] == 'trace.span.start':
            span_timings[event['span_id']] = {'start': event['timestamp_ns']}
        elif event['type'] == 'trace.span.end':
            if event['span_id'] in span_timings:
                span_timings[event['span_id']]['end'] = event['timestamp_ns']
                span_timings[event['span_id']]['operation'] = event['operation']
                span_timings[event['span_id']]['duration_ms'] = event['duration_ns'] / 1_000_000
    
    # Find overlapping spans
    overlapping = []
    spans_list = list(span_timings.values())
    for i in range(len(spans_list)):
        for j in range(i + 1, len(spans_list)):
            span1 = spans_list[i]
            span2 = spans_list[j]
            if ('start' in span1 and 'end' in span1 and 
                'start' in span2 and 'end' in span2):
                # Check if spans overlap
                if (span1['start'] < span2['end'] and 
                    span2['start'] < span1['end']):
                    overlapping.append((span1['operation'], span2['operation']))
    
    print(f"   Found {len(overlapping)} overlapping span pairs")
    for op1, op2 in overlapping[:3]:  # Show first 3
        print(f"   - {op1} overlapped with {op2}")
    
    context.stop()


def main():
    """Synchronous entry point."""
    asyncio.run(main_async())


if __name__ == '__main__':
    main()