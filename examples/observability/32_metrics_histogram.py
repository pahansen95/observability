#!/usr/bin/env python3
"""
Example 32: Metrics Histogram

Demonstrates:
- Creating Histogram with custom buckets
- Calling observe() with values across bucket ranges
- Using default buckets (Histogram.DEFAULT_BUCKETS)
- Accessing buckets property
- Observations with labels
"""

from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler, JsonHandler
from observability.domains.metrics import Histogram
import sys
import random


def main():
    """Main example logic."""
    print("=== Example 32: Metrics Histogram ===\n")
    
    # Create context with handlers
    print("1. Creating context with handlers")
    buffer_handler = BufferHandler()
    json_handler = JsonHandler(sys.stdout)
    config = ObservabilityConfig(handlers=[buffer_handler, json_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Show default buckets
    print("\n2. Default histogram buckets:")
    print(f"   DEFAULT_BUCKETS: {Histogram.DEFAULT_BUCKETS}")
    
    # Create histogram with custom buckets
    print("\n3. Creating Histogram with custom buckets")
    response_time_histogram = Histogram(
        name="http_response_time_seconds",
        context=context,
        description="HTTP response time distribution",
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
        service="api"
    )
    print(f"   Custom buckets: {response_time_histogram.buckets}")
    
    # Observe values across bucket ranges
    print("\n4. Observing values across different buckets")
    
    # Fast responses (< 0.05s)
    for _ in range(20):
        response_time_histogram.observe(random.uniform(0.001, 0.049))
    print("   Added 20 fast responses (0.001-0.049s)")
    
    # Normal responses (0.05s - 0.5s)
    for _ in range(50):
        response_time_histogram.observe(random.uniform(0.05, 0.5))
    print("   Added 50 normal responses (0.05-0.5s)")
    
    # Slow responses (0.5s - 2.5s)
    for _ in range(10):
        response_time_histogram.observe(random.uniform(0.5, 2.5))
    print("   Added 10 slow responses (0.5-2.5s)")
    
    # Very slow responses (> 2.5s)
    for _ in range(5):
        response_time_histogram.observe(random.uniform(2.5, 4.0))
    print("   Added 5 very slow responses (2.5-4.0s)")
    
    # Create histogram with default buckets
    print("\n5. Creating Histogram with default buckets")
    request_size_histogram = Histogram(
        name="http_request_size_bytes",
        context=context,
        description="HTTP request size distribution"
        # buckets parameter omitted - will use DEFAULT_BUCKETS
    )
    print(f"   Using default buckets: {request_size_histogram.buckets}")
    
    # Observe with labels
    print("\n6. Observing values with dynamic labels")
    
    # Different endpoints
    request_size_histogram.observe(1024, endpoint="/api/users", method="GET")
    request_size_histogram.observe(2048, endpoint="/api/users", method="POST")
    request_size_histogram.observe(512, endpoint="/api/health", method="GET")
    request_size_histogram.observe(4096, endpoint="/api/upload", method="POST")
    print("   Added observations with endpoint and method labels")
    
    # Create histogram for measuring percentiles
    print("\n7. Creating histogram for latency percentiles")
    latency_histogram = Histogram(
        name="operation_latency_ms",
        context=context,
        description="Operation latency in milliseconds",
        buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
    )
    
    # Generate realistic latency distribution
    print("\n8. Generating realistic latency distribution")
    # Most requests are fast
    for _ in range(900):
        latency_histogram.observe(random.uniform(1, 100), operation="read")
    # Some are medium
    for _ in range(90):
        latency_histogram.observe(random.uniform(100, 500), operation="write")
    # Few are slow
    for _ in range(10):
        latency_histogram.observe(random.uniform(500, 2000), operation="batch")
    print("   Added 1000 observations with realistic distribution")
    
    # Examine histogram events
    print("\n9. Examining histogram observations:")
    events = buffer_handler.get_events()
    histogram_events = [e for e in events if e['type'] == 'metric.histogram']
    
    print(f"   Total histogram observations: {len(histogram_events)}")
    
    # Show bucket information in events
    print("\n10. Histogram event structure:")
    if histogram_events:
        sample_event = histogram_events[0]
        print("   Sample histogram event:")
        print(f"     Name: {sample_event.get('value')}")
        print(f"     Value: {sample_event.get('measurement')}")
        print(f"     Buckets: {sample_event.get('buckets')}")
        # Extract labels (everything except standard fields)
        labels = {k: v for k, v in sample_event.items() 
                 if k not in ['type', 'value', 'measurement', 'metric_type', 'help', 'timestamp_ns', 'category', 'buckets']}
        if labels:
            print(f"     Labels: {labels}")
    
    # Demonstrate bucket boundaries
    print("\n11. Understanding bucket boundaries:")
    print("   Buckets define upper bounds for value ranges")
    print("   Example with buckets [10, 25, 50, 100]:")
    print("     - Value 5 goes to bucket 10")
    print("     - Value 15 goes to bucket 25")
    print("     - Value 30 goes to bucket 50")
    print("     - Value 75 goes to bucket 100")
    print("     - Value 150 goes to +Inf bucket")
    
    context.stop()


if __name__ == '__main__':
    main()