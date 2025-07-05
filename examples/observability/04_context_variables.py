#!/usr/bin/env python3
"""
Example 04: Context Variables

Demonstrates:
- Using trace_id, request_id, operation_id context variables
- Setting context variables
- Events automatically including context variables
- Clearing context variables
"""

from observability import (
    ObservabilityContext, ObservabilityConfig,
    trace_id, request_id, operation_id
)
from observability.handlers import BufferHandler


def main():
    """Main example logic."""
    print("=== Example 04: Context Variables ===\n")
    
    # Create context with BufferHandler to capture events
    print("1. Creating context with BufferHandler")
    buffer_handler = BufferHandler()
    config = ObservabilityConfig(handlers=[buffer_handler])
    context = ObservabilityContext(config)
    context.start()
    print("   Context created and started")
    
    # Set context variables
    print("\n2. Setting context variables")
    trace_id.set("trace-123")
    request_id.set("req-456")
    operation_id.set("op-789")
    print("   trace_id: trace-123")
    print("   request_id: req-456")
    print("   operation_id: op-789")
    
    # Emit event with context variables
    print("\n3. Emitting event with context variables")
    context.emit('test.with_context', 'Event with context')
    
    # Check captured event
    events = buffer_handler.get_events()
    if events:
        event = events[0]
        print("   Captured event includes:")
        print(f"     trace_id: {event.get('trace_id')}")
        print(f"     request_id: {event.get('request_id')}")
        print(f"     operation_id: {event.get('operation_id')}")
    
    # Clear context variables
    print("\n4. Clearing context variables")
    trace_id.set(None)
    request_id.set(None)
    operation_id.set(None)
    print("   Context variables cleared")
    
    # Emit event without context variables
    print("\n5. Emitting event without context variables")
    context.emit('test.without_context', 'Event without context')
    
    # Check second event
    events = buffer_handler.get_events()
    if len(events) >= 2:
        event = events[1]
        print("   Captured event:")
        print(f"     trace_id: {event.get('trace_id', 'not present')}")
        print(f"     request_id: {event.get('request_id', 'not present')}")
        print(f"     operation_id: {event.get('operation_id', 'not present')}")
    
    context.stop()


if __name__ == '__main__':
    main()