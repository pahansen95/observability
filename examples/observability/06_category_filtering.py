#!/usr/bin/env python3
"""
Example 06: Category Filtering

Demonstrates:
- Category-based event filtering
- enable_category() and disable_category()
- Events in different categories
- BufferHandler for capturing filtered results
"""

from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler


def main():
    """Main example logic."""
    print("=== Example 06: Category Filtering ===\n")

    # Create context with BufferHandler
    print("1. Creating context with BufferHandler")
    buffer_handler = BufferHandler()
    # Note: enabled_categories might not filter by default
    config = ObservabilityConfig(
        handlers=[buffer_handler]
    )
    context = ObservabilityContext(config)
    context.start()
    print("   Context created with BufferHandler")

    # Emit events in different categories
    print("\n2. Emitting events in different categories")
    context.emit('log.info', 'Log message 1')
    context.emit('metric.counter', {'name': 'requests', 'value': 1})
    context.emit('trace.span.start', {'operation': 'http_request'})
    print("   Emitted: log.info, metric.counter, trace.span.start")

    # Check captured events
    events = buffer_handler.get_events()
    print(f"\n3. Captured events (count: {len(events)})")
    for event in events:
        print(f"   - {event['type']}")

    # Enable metrics category
    print("\n4. Enabling 'metrics' category")
    context.enable_category('metrics')
    buffer_handler.clear()

    # Emit more events
    print("\n5. Emitting more events")
    context.emit('log.debug', 'Debug message')
    context.emit('metric.gauge', {'name': 'memory', 'value': 1024})
    context.emit('trace.span.end', {'operation': 'http_request'})
    print("   Emitted: log.debug, metric.gauge, trace.span.end")

    # Check captured events
    events = buffer_handler.get_events()
    print(f"\n6. Captured events (count: {len(events)})")
    for event in events:
        print(f"   - {event['type']}")

    # Disable logging category
    print("\n7. Disabling 'logging' category")
    context.disable_category('logging')
    buffer_handler.clear()

    # Emit final events
    print("\n8. Emitting final events")
    context.emit('log.error', 'Error message')
    context.emit('metric.histogram', {'name': 'latency', 'value': 100})
    print("   Emitted: log.error, metric.histogram")

    # Check final captured events
    events = buffer_handler.get_events()
    print(f"\n9. Captured events (count: {len(events)})")
    for event in events:
        print(f"   - {event['type']}")
    print("   Note: Only metrics events captured (logging disabled)")

    print("\n10. Summary:")
    print("    - Events are filtered based on their type prefix")
    print("    - 'log.*' events go to 'logging' category")
    print("    - 'metric.*' events go to 'metrics' category")
    print("    - 'trace.*' events go to 'tracing' category")

    context.stop()


if __name__ == '__main__':
    main()
