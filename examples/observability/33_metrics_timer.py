#!/usr/bin/env python3
"""
Example 33: Metrics Timer

Demonstrates:
- Creating Histogram for timing
- Using Timer context manager
- Passing labels to Timer constructor
- Nesting timers for sub-operations
- Automatic duration recording
"""

import time
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler, PrintHandler
from observability.domains.metrics import Histogram


def main():
    """Main example logic."""
    print("=== Example 33: Metrics Timer ===\n")
    
    # Create context with handlers
    print("1. Creating context with handlers")
    buffer_handler = BufferHandler()
    print_handler = PrintHandler(format="[{type}] {name}: {measurement:.3f}")
    config = ObservabilityConfig(handlers=[buffer_handler, print_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Create histogram for timing operations
    print("\n2. Creating Histogram for timing measurements")
    operation_timer = Histogram(
        name="operation_duration_seconds",
        context=context,
        help="Duration of various operations",
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
        service="processor"
    )
    
    # Use Timer context manager
    print("\n3. Using Timer context manager")
    with operation_timer.time():
        print("   Starting timed operation...")
        time.sleep(0.1)  # Simulate 100ms operation
        print("   Operation completed")
    print("   Duration automatically recorded")
    
    # Timer with labels
    print("\n4. Timer with dynamic labels")
    with operation_timer.time(operation="database_query", query_type="select"):
        time.sleep(0.05)  # Simulate 50ms query
    print("   Recorded with operation and query_type labels")
    
    # Multiple operations with different labels
    print("\n5. Timing different operations")
    
    # API calls
    with operation_timer.time(operation="api_call", endpoint="/users"):
        time.sleep(0.02)
    
    with operation_timer.time(operation="api_call", endpoint="/orders"):
        time.sleep(0.04)
    
    # Cache operations
    with operation_timer.time(operation="cache_lookup", hit=True):
        time.sleep(0.001)  # Cache hit is fast
    
    with operation_timer.time(operation="cache_lookup", hit=False):
        time.sleep(0.05)   # Cache miss is slower
    
    print("   Timed various operations with different labels")
    
    # Nested timers
    print("\n6. Nested timers for sub-operations")
    
    # Create separate histograms for different granularities
    main_timer = Histogram(
        name="request_duration_seconds",
        context=context,
        help="Total request duration"
    )
    
    sub_timer = Histogram(
        name="request_phase_duration_seconds",
        context=context,
        help="Request phase duration"
    )
    
    # Time overall operation and sub-operations
    with main_timer.time(request_id="REQ-123"):
        print("   Starting main operation")
        
        # Phase 1: Authentication
        with sub_timer.time(phase="authentication", request_id="REQ-123"):
            time.sleep(0.01)
            print("   - Authentication completed")
        
        # Phase 2: Validation
        with sub_timer.time(phase="validation", request_id="REQ-123"):
            time.sleep(0.02)
            print("   - Validation completed")
        
        # Phase 3: Processing
        with sub_timer.time(phase="processing", request_id="REQ-123"):
            time.sleep(0.05)
            print("   - Processing completed")
        
        # Phase 4: Response
        with sub_timer.time(phase="response", request_id="REQ-123"):
            time.sleep(0.01)
            print("   - Response sent")
    
    print("   Main operation and all phases timed")
    
    # Demonstrate timer in loops
    print("\n7. Using timer in loops")
    batch_timer = Histogram(
        name="batch_item_duration_seconds",
        context=context,
        help="Duration to process each batch item"
    )
    
    items = ["item1", "item2", "item3", "item4", "item5"]
    for i, item in enumerate(items):
        with batch_timer.time(item_id=item, batch_position=i):
            # Simulate variable processing time
            time.sleep(0.01 * (i + 1))
    print(f"   Processed {len(items)} items with individual timing")
    
    # Examine timing events
    print("\n8. Examining timing measurements:")
    events = buffer_handler.get_events()
    histogram_events = [e for e in events if e['type'] == 'metric.histogram']
    
    # Group by histogram name
    timings_by_name = {}
    for event in histogram_events:
        name = event['value']  # metric name is in 'value' field
        if name not in timings_by_name:
            timings_by_name[name] = []
        timings_by_name[name].append(event.get('measurement', 0))
    
    # Show statistics
    print("\n9. Timing statistics by operation:")
    for name, values in timings_by_name.items():
        if values:
            min_val = min(values)
            max_val = max(values)
            avg_val = sum(values) / len(values)
            print(f"   {name}:")
            print(f"     Count: {len(values)}")
            print(f"     Min: {min_val:.3f}s")
            print(f"     Max: {max_val:.3f}s")
            print(f"     Avg: {avg_val:.3f}s")
    
    # Show label usage
    print("\n10. Label usage in timing measurements:")
    # Extract labels from events (everything except standard fields)
    labeled_events = []
    for e in histogram_events:
        labels = {k: v for k, v in e.items() 
                 if k not in ['type', 'value', 'measurement', 'metric_type', 'help', 'timestamp_ns', 'category', 'buckets']}
        if len(labels) > 1:  # More than just the static label
            labeled_events.append((e, labels))
    
    print(f"   Events with multiple labels: {len(labeled_events)}")
    
    # Show a few examples
    for event, labels in labeled_events[:3]:
        event_name = event.get('value', event.get('type', 'unknown'))
        print(f"   - {event_name}: {labels}")
    
    context.stop()


if __name__ == '__main__':
    main()