#!/usr/bin/env python3
"""
Example 31: Metrics Gauge

Demonstrates:
- Creating Gauge with all parameters
- Using set() with various values
- Using increment() and decrement()
- Showing negative values are allowed
- Mixing static and dynamic labels
"""

from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler, PrintHandler
from observability.domains.metrics import Gauge


def main():
    """Main example logic."""
    print("=== Example 31: Metrics Gauge ===\n")
    
    # Create context with handlers
    print("1. Creating context with handlers")
    buffer_handler = BufferHandler()
    print_handler = PrintHandler(format="[{type}] {name}: {measurement}")
    config = ObservabilityConfig(handlers=[buffer_handler, print_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Create gauge with all parameters
    print("\n2. Creating Gauge with all parameters")
    memory_gauge = Gauge(
        name="memory_usage_bytes",
        context=context,
        help="Current memory usage in bytes",
        process="api_server", 
        host="server-1"
    )
    print(f"   Gauge created: memory_usage_bytes")
    
    # Set various values
    print("\n3. Setting gauge to various values")
    memory_gauge.set(1024 * 1024 * 100)  # 100 MB
    print("   Set to 100 MB")
    
    memory_gauge.set(1024 * 1024 * 150)  # 150 MB
    print("   Set to 150 MB")
    
    memory_gauge.set(1024 * 1024 * 75)   # 75 MB
    print("   Set to 75 MB (decreased)")
    
    # Use increment and decrement
    print("\n4. Using increment() and decrement()")
    memory_gauge.increment(1024 * 1024 * 10)  # +10 MB
    print("   Incremented by 10 MB")
    
    memory_gauge.decrement(1024 * 1024 * 5)   # -5 MB
    print("   Decremented by 5 MB")
    
    # Create temperature gauge that can go negative
    print("\n5. Creating temperature gauge (allows negative values)")
    temp_gauge = Gauge(
        name="temperature_celsius",
        context=context,
        help="Current temperature reading"
    )
    
    temp_gauge.set(20.5, location="indoor", sensor_id="TEMP-001")
    temp_gauge.set(-5.2, location="outdoor", sensor_id="TEMP-002")
    temp_gauge.set(-15.7, location="freezer", sensor_id="TEMP-003")
    print("   Set positive and negative temperature values")
    
    # Mix static and dynamic labels
    print("\n6. Mixing static and dynamic labels")
    queue_gauge = Gauge(
        name="queue_depth",
        context=context,
        help="Current queue depth",
        queue_type="task"  # Static label
    )
    
    # Add dynamic labels
    queue_gauge.set(100, priority="high", worker="worker-1")
    queue_gauge.set(250, priority="normal", worker="worker-2")
    queue_gauge.set(50, priority="low", worker="worker-3")
    print("   Static label: queue_type=task")
    print("   Dynamic labels: priority and worker")
    
    # Demonstrate gauge value changes over time
    print("\n7. Simulating gauge changes over time")
    active_connections = Gauge(
        name="active_connections",
        context=context,
        help="Number of active connections"
    )
    
    # Simulate connection changes
    active_connections.set(0)
    active_connections.increment(5)    # 5 new connections
    active_connections.increment(3)    # 3 more connections
    active_connections.decrement(2)   # 2 disconnected
    active_connections.increment(4)    # 4 new connections
    active_connections.decrement(3)   # 3 disconnected
    print("   Simulated connection pool changes")
    
    # Examine metric events
    print("\n8. Examining gauge metric events:")
    events = buffer_handler.get_events()
    gauge_events = [e for e in events if e['type'] == 'metric.gauge']
    
    print(f"   Total gauge events: {len(gauge_events)}")
    
    # Show negative values
    print("\n9. Gauges with negative values:")
    negative_events = [e for e in gauge_events if e.get('measurement', 0) < 0]
    for event in negative_events:
        print(f"   {event['value']}: {event['measurement']}")
        if 'labels' in event:
            labels = {k: v for k, v in event.items() 
                     if k not in ['type', 'value', 'measurement', 'metric_type', 'help', 'timestamp_ns', 'category', 'unit', 'delta']}
            if labels:
                print(f"     Labels: {labels}")
    
    # Show final values for each gauge
    print("\n10. Latest values by gauge name:")
    latest_values = {}
    for event in gauge_events:
        name = event['value']  # metric name is in 'value' field
        latest_values[name] = event.get('measurement', 0)
    
    for name, value in latest_values.items():
        print(f"   {name}: {value}")
    
    context.stop()


if __name__ == '__main__':
    main()