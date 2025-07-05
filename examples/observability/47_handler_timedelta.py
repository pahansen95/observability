#!/usr/bin/env python3
"""
Example 47: Handler TimeDelta

Demonstrates:
- Creating TimeDeltaHandler wrapping another handler
- delta_ns field automatically added
- Sequence of events with delays
- First event has delta=0
"""

import time
import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import TimeDeltaHandler, JsonHandler, BufferHandler
from observability.domains.logging import Logger, INFO


def main():
    """Main example logic."""
    print("=== Example 47: Handler TimeDelta ===\n")
    
    # Create base handlers
    json_handler = JsonHandler(sys.stdout)
    buffer_handler = BufferHandler()
    
    # Wrap with TimeDeltaHandler
    print("1. Creating TimeDeltaHandler wrapping JsonHandler")
    timedelta_handler = TimeDeltaHandler(json_handler)
    
    config = ObservabilityConfig(handlers=[timedelta_handler, buffer_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Emit sequence of events
    print("\n2. Emitting sequence of events with delays:")
    
    print("   Event 1 (immediate)")
    context.emit("sequence.start", "First event")
    
    time.sleep(0.1)  # 100ms delay
    print("   Event 2 (after 100ms)")
    context.emit("sequence.middle", "Second event")
    
    time.sleep(0.05)  # 50ms delay
    print("   Event 3 (after 50ms)")
    context.emit("sequence.end", "Third event")
    
    # Rapid sequence
    print("\n3. Rapid event sequence:")
    for i in range(5):
        context.emit("rapid.event", f"Rapid {i}")
        time.sleep(0.01)  # 10ms between events
    
    # Examine time deltas
    print("\n4. Examining time deltas from buffer:")
    events = buffer_handler.get_events()
    
    print("   Event time deltas:")
    for i, event in enumerate(events):
        delta_ns = event.get('delta_ns', 0)
        delta_ms = delta_ns / 1_000_000
        print(f"   Event {i}: {delta_ms:.1f}ms since previous")
    
    # Using with Logger
    print("\n5. Using TimeDeltaHandler with Logger:")
    
    buffer_handler.clear()
    logger = Logger("timing.test", context, INFO)
    
    logger.info("Operation started")
    
    # Simulate work phases
    time.sleep(0.2)
    logger.info("Phase 1 completed")
    
    time.sleep(0.15)
    logger.info("Phase 2 completed")
    
    time.sleep(0.1)
    logger.info("Operation finished")
    
    # Show timing analysis
    print("\n6. Timing analysis from logged operations:")
    events = buffer_handler.get_events()
    
    total_time_ns = 0
    for i, event in enumerate(events):
        if i > 0:  # Skip first event (delta=0)
            delta_ns = event.get('delta_ns', 0)
            total_time_ns += delta_ns
            delta_ms = delta_ns / 1_000_000
            print(f"   {event['value']}: {delta_ms:.1f}ms")
    
    total_ms = total_time_ns / 1_000_000
    print(f"   Total operation time: {total_ms:.1f}ms")
    
    # Multiple TimeDeltaHandlers
    print("\n7. Multiple independent TimeDeltaHandlers:")
    
    # Create separate buffer handlers to track
    buffer1 = BufferHandler()
    buffer2 = BufferHandler()
    
    handler1 = TimeDeltaHandler(buffer1)
    handler2 = TimeDeltaHandler(buffer2)
    
    config2 = ObservabilityConfig(handlers=[handler1, handler2])
    context2 = ObservabilityContext(config2)
    context2.start()
    
    # Emit events
    context2.emit("multi.test", "Event 1")
    time.sleep(0.05)
    context2.emit("multi.test", "Event 2")
    
    # Each handler tracks its own deltas
    events1 = buffer1.get_events()
    events2 = buffer2.get_events()
    
    print(f"   Handler 1 delta: {events1[1]['delta_ns'] / 1_000_000:.1f}ms")
    print(f"   Handler 2 delta: {events2[1]['delta_ns'] / 1_000_000:.1f}ms")
    print("   Both handlers track time independently")
    
    # Performance monitoring use case
    print("\n8. Performance monitoring use case:")
    
    perf_buffer = BufferHandler()
    perf_handler = TimeDeltaHandler(perf_buffer)
    
    config3 = ObservabilityConfig(handlers=[perf_handler])
    context3 = ObservabilityContext(config3)
    context3.start()
    
    # Simulate request processing
    context3.emit("request.received", {"id": "req-123"})
    
    time.sleep(0.01)  # Auth check
    context3.emit("request.authenticated", {"id": "req-123"})
    
    time.sleep(0.03)  # Database query
    context3.emit("request.data_fetched", {"id": "req-123"})
    
    time.sleep(0.02)  # Processing
    context3.emit("request.processed", {"id": "req-123"})
    
    time.sleep(0.005)  # Response
    context3.emit("request.completed", {"id": "req-123"})
    
    # Analyze request phases
    print("\n9. Request processing phases:")
    events = perf_buffer.get_events()
    
    for i in range(1, len(events)):
        prev_event = events[i-1]
        curr_event = events[i]
        delta_ms = curr_event['delta_ns'] / 1_000_000
        
        phase = f"{prev_event['type'].split('.')[-1]} -> {curr_event['type'].split('.')[-1]}"
        print(f"   {phase}: {delta_ms:.1f}ms")
    
    # Clean up
    context.stop()
    context2.stop()
    context3.stop()


if __name__ == '__main__':
    main()