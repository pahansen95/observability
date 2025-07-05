#!/usr/bin/env python3
"""
Example 44: Handler Queued

Demonstrates:
- Creating QueuedHandler wrapping another handler
- Queue size and timeout parameters
- Starting worker thread
- Burst event handling
- Graceful shutdown with stop()
"""

import time
import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import QueuedHandler, PrintHandler
from observability.domains.logging import Logger, DEBUG


def main():
    """Main example logic."""
    print("=== Example 44: Handler Queued ===\n")

    # Create base handler that simulates slow processing
    print("1. Creating QueuedHandler with PrintHandler")

    # Custom print handler with delay simulation
    class SlowPrintHandler:
        def __init__(self, stream=sys.stdout):
            self.stream = stream

        def __call__(self, event):
            # Simulate slow processing
            time.sleep(0.01)  # 10ms per event
            print(f"[SLOW] {event['type']}: {event['value']}", file=self.stream)

    slow_handler = SlowPrintHandler()

    # Wrap in QueuedHandler
    queued_handler = QueuedHandler(wrapped_handler=slow_handler)

    print("   Queue size: 100")
    print("   Timeout: 1.0 second")

    # Create context
    config = ObservabilityConfig(handlers=[queued_handler])
    context = ObservabilityContext(config)

    # Start handlers
    print("\n2. Starting handlers (initializes worker thread)")
    queued_handler.start()
    context.start()
    print("   Worker thread started")

    # Emit burst of events
    print("\n3. Emitting burst of 20 events")
    start_time = time.time()

    for i in range(20):
        context.emit("burst.event", f"Event {i}")

    emit_time = time.time() - start_time
    print(f"   All events queued in {emit_time:.3f} seconds")
    print("   Note: Events are processed asynchronously")

    # Give worker time to process some events
    time.sleep(0.1)

    # Emit more events while processing
    print("\n4. Emitting more events while processing")
    for i in range(20, 25):
        context.emit("concurrent.event", f"Event {i}")
        time.sleep(0.05)  # Emit slowly

    # Demonstrate queue overflow handling
    print("\n5. Testing queue size limit")

    # Create handler with small queue
    small_queue_handler = QueuedHandler(
        PrintHandler(sys.stdout, format="[SMALL_Q] {type}: {value}")
    )

    config2 = ObservabilityConfig(handlers=[small_queue_handler])
    context2 = ObservabilityContext(config2)
    small_queue_handler.start()
    context2.start()

    # Rapid burst exceeding queue size
    print("   Emitting 10 events to queue of size 5")
    for i in range(10):
        context2.emit("overflow.test", f"Overflow {i}")

    # Stop and wait for processing
    print("\n6. Stopping handler (draining queue)")
    stop_start = time.time()
    context.stop()
    queued_handler.stop()
    stop_time = time.time() - stop_start
    print(f"   Queue drained and stopped in {stop_time:.3f} seconds")

    # Also stop second handler
    context2.stop()
    small_queue_handler.stop()

    # Demonstrate multiple queued handlers
    print("\n7. Multiple queued handlers with different rates")

    fast_handler = QueuedHandler(
        PrintHandler(sys.stdout, format="[FAST] {type}")
    )

    slow_handler = QueuedHandler(
        SlowPrintHandler()
    )

    config3 = ObservabilityConfig(handlers=[fast_handler, slow_handler])
    context3 = ObservabilityContext(config3)
    fast_handler.start()
    slow_handler.start()
    context3.start()

    # Emit events
    logger = Logger("multi.queue", context3, DEBUG)
    for i in range(5):
        logger.info(f"Message {i}")

    print("   Both handlers processing same events at different rates")

    # Final cleanup
    time.sleep(0.5)  # Let processing finish
    context3.stop()
    fast_handler.stop()
    slow_handler.stop()

    print("\n8. Benefits of queued handlers:")
    print("   - Non-blocking event emission")
    print("   - Smooth out processing bursts")
    print("   - Prevent slow handlers from blocking app")
    print("   - Graceful shutdown with queue draining")


if __name__ == '__main__':
    main()
