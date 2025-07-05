#!/usr/bin/env python3
"""
Example 20: Tracing Basics

Demonstrates:
- Creating Span with operation name and context
- Using span as context manager
- Accessing span_id, parent_id, operation properties
- Setting attributes with various types
- Automatic timing on span exit
"""

import time
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler, PrintHandler
from observability.domains.tracing import Span


def main():
    """Main example logic."""
    print("=== Example 20: Tracing Basics ===\n")
    
    # Create context with handlers
    print("1. Creating context with BufferHandler and PrintHandler")
    buffer_handler = BufferHandler()
    print_handler = PrintHandler(format="[{type}] {operation}: {value}")
    config = ObservabilityConfig(handlers=[buffer_handler, print_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Create span manually and access properties
    print("\n2. Creating span and accessing properties")
    span = Span(
        operation="process_request",
        context=context
    )
    print(f"   Span ID: {span.span_id}")
    print(f"   Parent ID: {span.parent_id}")
    print(f"   Operation: {span._operation}")
    
    # Use span as context manager
    print("\n3. Using span as context manager:")
    with span:
        print("   Span started (emits trace.span.start event)")
        
        # Set various attribute types
        print("\n4. Setting span attributes:")
        span.set_attribute("user_id", "user-123")
        span.set_attribute("request_size", 1024)
        span.set_attribute("compression_ratio", 0.75)
        span.set_attribute("tags", ["api", "v2", "authenticated"])
        span.set_attribute("metadata", {"region": "us-east-1", "tier": "premium"})
        print("   Set string, int, float, list, and dict attributes")
        
        # Simulate some work
        time.sleep(0.1)  # 100ms of work
        
    print("   Span ended (emits trace.span.end event)")
    
    # Create another span to show timing
    print("\n5. Creating span with automatic timing:")
    with Span("fast_operation", context) as fast_span:
        time.sleep(0.01)  # 10ms of work
        fast_span.set_attribute("processed_items", 100)
    
    with Span("slow_operation", context) as slow_span:
        time.sleep(0.05)  # 50ms of work
        slow_span.set_attribute("processed_items", 500)
    
    # Examine captured span events
    print("\n6. Examining captured span events:")
    events = buffer_handler.get_events()
    
    # Filter span events
    span_starts = [e for e in events if e['type'] == 'trace.span.start']
    span_ends = [e for e in events if e['type'] == 'trace.span.end']
    
    print(f"   Span start events: {len(span_starts)}")
    print(f"   Span end events: {len(span_ends)}")
    
    # Show timing information
    print("\n7. Span timing information:")
    for i, end_event in enumerate(span_ends):
        operation = end_event.get('operation', 'unknown')
        duration_ns = end_event.get('duration_ns', 0)
        duration_ms = duration_ns / 1_000_000
        print(f"   {operation}: {duration_ms:.2f}ms")
    
    # Show span attributes in events
    print("\n8. Span attributes in end events:")
    if span_ends:
        first_end = span_ends[0]
        attributes = first_end.get('attributes', {})
        print(f"   Attributes: {attributes}")
    else:
        print("   No span end events found")
    
    context.stop()


if __name__ == '__main__':
    main()