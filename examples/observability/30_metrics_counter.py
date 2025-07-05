#!/usr/bin/env python3
"""
Example 30: Metrics Counter

Demonstrates:
- Creating Counter with name, context, unit, description
- Using static labels in constructor
- Calling increment() with default value
- Calling increment() with specific value
- Using dynamic labels in increment()
"""

from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler, PrintHandler
from observability.domains.metrics import Counter


def main():
    """Main example logic."""
    print("=== Example 30: Metrics Counter ===\n")
    
    # Create context with handlers
    print("1. Creating context with handlers")
    buffer_handler = BufferHandler()
    print_handler = PrintHandler(format="[{type}] {name}: {value} {unit}")
    config = ObservabilityConfig(handlers=[buffer_handler, print_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Create counter with static labels
    print("\n2. Creating Counter with static labels")
    request_counter = Counter(
        name="http_requests_total",
        context=context,
        unit="requests",
        description="Total number of HTTP requests",
        service="api",
        environment="production"
    )
    print(f"   Counter created: http_requests_total")
    print(f"   Static labels: service=api, environment=production")
    
    # Increment with default value (1.0)
    print("\n3. Incrementing counter with default value")
    request_counter.increment()
    print("   Incremented by 1.0 (default)")
    
    # Increment with specific values
    print("\n4. Incrementing with specific values")
    request_counter.increment(5.0)
    print("   Incremented by 5.0")
    
    request_counter.increment(2.5)
    print("   Incremented by 2.5")
    
    # Increment with dynamic labels
    print("\n5. Incrementing with dynamic labels")
    request_counter.increment(1.0, method="GET", status_code="200")
    request_counter.increment(1.0, method="POST", status_code="201")
    request_counter.increment(1.0, method="GET", status_code="404")
    request_counter.increment(3.0, method="POST", status_code="500")
    print("   Added method and status_code as dynamic labels")
    
    # Create another counter without static labels
    print("\n6. Creating counter without static labels")
    error_counter = Counter(
        name="errors_total",
        context=context,
        unit="errors",
        description="Total number of errors"
    )
    
    # Use only dynamic labels
    error_counter.increment(1.0, error_type="timeout", severity="warning")
    error_counter.increment(2.0, error_type="connection", severity="error")
    error_counter.increment(1.0, error_type="validation", severity="info")
    print("   Using only dynamic labels")
    
    # Examine metric events
    print("\n7. Examining captured metric events:")
    events = buffer_handler.get_events()
    metric_events = [e for e in events if e['type'].startswith('metric.')]
    
    print(f"   Total metric events: {len(metric_events)}")
    
    # Show event details
    print("\n8. Metric event details:")
    for i, event in enumerate(metric_events[:5]):
        print(f"   Event {i+1}:")
        print(f"     Name: {event.get('name')}")
        print(f"     Value: {event.get('value')}")
        print(f"     Unit: {event.get('unit')}")
        labels = event.get('labels', {})
        if labels:
            print(f"     Labels: {labels}")
    
    # Note about counter properties
    print("\n9. Counter configuration:")
    print(f"   Name: http_requests_total")
    print(f"   Unit: requests")
    print(f"   Description: Total number of HTTP requests")
    print(f"   Static labels: service=api, environment=production")
    
    context.stop()


if __name__ == '__main__':
    main()