#!/usr/bin/env python3
"""
Example 43: Handler Buffer

Demonstrates:
- Creating BufferHandler with max_size limit
- Emitting more events than max_size
- Using get_events() to retrieve list
- Using clear() to empty buffer
- Events are defensive copies
"""

from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler
from observability.domains.logging import Logger, INFO
from observability.domains.metrics import Counter


def main():
    """Main example logic."""
    print("=== Example 43: Handler Buffer ===\n")
    
    # Create BufferHandler with max_size
    print("1. Creating BufferHandler with max_size=10")
    buffer_handler = BufferHandler(max_size=10)
    
    config = ObservabilityConfig(handlers=[buffer_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Emit exactly max_size events
    print("\n2. Emitting 10 events (exactly max_size)")
    for i in range(10):
        context.emit("test.event", f"Event {i}")
    
    events = buffer_handler.get_events()
    print(f"   Buffer contains {len(events)} events")
    print(f"   First event: {events[0]['value']}")
    print(f"   Last event: {events[-1]['value']}")
    
    # Emit more events than max_size
    print("\n3. Emitting 5 more events (exceeding max_size)")
    for i in range(10, 15):
        context.emit("test.overflow", f"Event {i}")
    
    events = buffer_handler.get_events()
    print(f"   Buffer still contains {len(events)} events (max_size enforced)")
    print(f"   First event now: {events[0]['value']}")
    print(f"   Last event now: {events[-1]['value']}")
    print("   Note: Oldest events were dropped")
    
    # Clear buffer
    print("\n4. Clearing buffer")
    buffer_handler.clear()
    events = buffer_handler.get_events()
    print(f"   Buffer now contains {len(events)} events")
    
    # Demonstrate defensive copies
    print("\n5. Demonstrating defensive copies")
    context.emit("test.defensive", {"mutable": ["list"]})
    
    # Get events and modify
    events = buffer_handler.get_events()
    original_event = events[0]
    print(f"   Original event value: {original_event['value']}")
    
    # Try to modify the returned event
    original_event['value']['mutable'].append("modified")
    print(f"   Modified returned event: {original_event['value']}")
    
    # Get events again
    events_again = buffer_handler.get_events()
    print(f"   Buffer event unchanged: {events_again[0]['value']}")
    print("   Note: Modifications don't affect buffer")
    
    # Use with different event types
    print("\n6. Capturing different event types")
    buffer_handler.clear()
    
    # Logging events
    logger = Logger("buffer.test", context, INFO)
    logger.info("Log message 1")
    logger.warning("Log message 2")
    
    # Metric events
    counter = Counter("test_counter", context)
    counter.increment(1.0)
    counter.increment(2.0)
    
    # Direct events
    context.emit("custom.event", "Custom value")
    
    # Examine captured events
    events = buffer_handler.get_events()
    print(f"\n7. Captured event types ({len(events)} total):")
    for event in events:
        print(f"   - {event['type']}: {event['value']}")
    
    # Buffer without max_size
    print("\n8. Creating BufferHandler without max_size limit")
    unlimited_buffer = BufferHandler()  # No max_size
    
    config2 = ObservabilityConfig(handlers=[unlimited_buffer])
    context2 = ObservabilityContext(config2)
    context2.start()
    
    # Emit many events
    for i in range(100):
        context2.emit("unlimited.test", i)
    
    events = unlimited_buffer.get_events()
    print(f"   Buffer contains all {len(events)} events")
    
    # Event inspection utilities
    print("\n9. Event inspection utilities")
    buffer_handler.clear()
    
    # Emit event with metadata
    context.emit("inspect.test", "Test value",
                 user_id=123,
                 action="click",
                 timestamp="2024-01-01")
    
    events = buffer_handler.get_events()
    if events:
        event = events[0]
        print("   Event structure:")
        print(f"     type: {event.get('type')}")
        print(f"     value: {event.get('value')}")
        print(f"     timestamp_ns: {event.get('timestamp_ns')}")
        print("     metadata:")
        for key, value in event.items():
            if key not in ['type', 'value', 'timestamp_ns']:
                print(f"       {key}: {value}")
    
    # Clean up
    context.stop()
    context2.stop()


if __name__ == '__main__':
    main()