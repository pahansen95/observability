#!/usr/bin/env python3
"""
Example 48: Handler Fanout

Demonstrates:
- Creating FanoutHandler with multiple handlers
- Handlers that might fail
- All handlers receive events
- Failure isolation
- Lifecycle management
"""

import sys
import os
import tempfile
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import FanoutHandler, PrintHandler, JsonHandler, BufferHandler, ManagedFileHandler, filtered, sampled
from observability.domains.logging import Logger, INFO


def main():
    """Main example logic."""
    print("=== Example 48: Handler Fanout ===\n")
    
    # Create multiple handlers
    print("1. Creating multiple handlers for fanout")
    
    print_handler = PrintHandler(sys.stdout, format="[PRINT] {type}: {value}")
    json_handler = JsonHandler(sys.stderr)  # Different stream
    buffer_handler = BufferHandler()
    
    # Create FanoutHandler
    print("\n2. Creating FanoutHandler with 3 handlers")
    fanout = FanoutHandler(print_handler, json_handler, buffer_handler)
    
    config = ObservabilityConfig(handlers=[fanout])
    context = ObservabilityContext(config)
    context.start()
    
    # Emit events - all handlers receive them
    print("\n3. Emitting events to all handlers:")
    context.emit("fanout.test", "Message to all handlers")
    context.emit("fanout.data", {"key": "value", "number": 42})
    
    print("\n   All handlers processed the events")
    
    # Check buffer to confirm
    events = buffer_handler.get_events()
    print(f"   Buffer captured {len(events)} events")
    
    # Demonstrate failure isolation
    print("\n4. Demonstrating failure isolation")
    
    class FailingHandler:
        def __call__(self, event):
            if event['type'] == 'fail.trigger':
                raise ValueError("Handler failed!")
            print(f"[FAILING] {event['type']}: {event['value']}")
    
    failing_handler = FailingHandler()
    safe_handler = PrintHandler(sys.stdout, format="[SAFE] {type}: {value}")
    
    fanout2 = FanoutHandler([failing_handler, safe_handler, buffer_handler])
    
    config2 = ObservabilityConfig(handlers=[fanout2])
    context2 = ObservabilityContext(config2)
    context2.start()
    
    print("\n5. Emitting events with one failing handler:")
    context2.emit("normal.event", "This works fine")
    context2.emit("fail.trigger", "This causes handler 1 to fail")
    context2.emit("after.failure", "Other handlers still work")
    
    print("\n   Safe handler and buffer still received all events")
    
    # Lifecycle management
    print("\n6. Demonstrating lifecycle management")
    
    temp_file = tempfile.mktemp(suffix='.log')
    file_handler = ManagedFileHandler(temp_file)
    
    lifecycle_fanout = FanoutHandler(
        PrintHandler(sys.stdout, format="[LC] {value}"),
        file_handler,
        BufferHandler()
    )
    
    # Start handlers
    print("   Starting fanout with managed handlers")
    lifecycle_fanout.start()
    
    config3 = ObservabilityConfig(handlers=[lifecycle_fanout])
    context3 = ObservabilityContext(config3)
    context3.start()
    
    # Use it
    logger = Logger("lifecycle.test", context3, INFO)
    logger.info("Message during lifecycle")
    
    # Stop handlers
    print("   Stopping fanout handlers")
    context3.stop()
    lifecycle_fanout.stop()
    
    # Verify file was written
    if os.path.exists(temp_file):
        print(f"   File handler wrote to: {temp_file}")
        os.unlink(temp_file)
    
    # Complex fanout tree
    print("\n7. Complex fanout tree")
    
    # Create nested fanout
    group1 = FanoutHandler(
        PrintHandler(sys.stdout, format="[G1-A] {value}"),
        PrintHandler(sys.stdout, format="[G1-B] {value}")
    )
    
    group2 = FanoutHandler(
        PrintHandler(sys.stdout, format="[G2-A] {value}"),
        PrintHandler(sys.stdout, format="[G2-B] {value}")
    )
    
    root_fanout = FanoutHandler([group1, group2, buffer_handler])
    
    config4 = ObservabilityConfig(handlers=[root_fanout])
    context4 = ObservabilityContext(config4)
    context4.start()
    
    print("\n8. Emitting to nested fanout structure:")
    context4.emit("nested.fanout", "Broadcast message")
    
    print("   Message delivered to all nested handlers")
    
    # Performance characteristics
    print("\n9. Fanout performance characteristics:")
    print("   - Events are delivered sequentially to each handler")
    print("   - Slow handlers can impact overall throughput")
    print("   - Failures are isolated per handler")
    print("   - Consider QueuedHandler for async fanout")
    
    # Different handlers for different purposes
    print("\n10. Specialized handlers in fanout:")
    
    from observability.handlers import filtered, sampled
    
    # Errors to file
    error_file_handler = filtered(
        ManagedFileHandler(tempfile.mktemp(suffix='-errors.log')),
        lambda e: e.get('level', 0) >= 40  # ERROR and above
    )
    
    # Sample 10% to metrics
    metrics_handler = filtered(
        lambda e: e['type'].startswith('metric.'),
        sampled(
            0.1,
            PrintHandler(sys.stdout, format="[METRICS] {type}")
        )
    )
    
    # Everything to buffer for testing
    test_buffer = BufferHandler()
    
    specialized_fanout = FanoutHandler(
        error_file_handler,
        metrics_handler,
        test_buffer
    )
    
    specialized_fanout.start()
    
    config5 = ObservabilityConfig(handlers=[specialized_fanout])
    context5 = ObservabilityContext(config5)
    context5.start()
    
    # Emit various events
    logger2 = Logger("specialized.test", context5, INFO)
    
    for i in range(10):
        context5.emit("metric.counter", {"name": "requests", "value": i})
    
    logger2.info("Normal operation")
    logger2.error("Error occurred!")
    logger2.warning("Just a warning")
    
    print("   Each handler processed relevant events only")
    
    # Cleanup
    context5.stop()
    specialized_fanout.stop()
    
    # Stop remaining contexts
    context.stop()
    context2.stop()
    context4.stop()


if __name__ == '__main__':
    main()