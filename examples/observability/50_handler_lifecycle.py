#!/usr/bin/env python3
"""
Example 50: Handler Lifecycle

Demonstrates:
- Handlers with start/stop methods
- Lifecycle order in ObservabilityContext
- Auto-start on attach
- Reverse-order stop
- Lifecycle error handling
"""

import sys
import time
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import ManagedFileHandler, QueuedHandler, PrintHandler, BufferHandler


def main():
    """Main example logic."""
    print("=== Example 50: Handler Lifecycle ===\n")

    # Create custom handler with lifecycle
    print("1. Creating custom handler with lifecycle methods")

    class LifecycleHandler:
        def __init__(self, name):
            self.name = name
            self.started = False
            self.events_processed = 0

        def start(self):
            print(f"   [{self.name}] Starting...")
            self.started = True
            time.sleep(0.05)  # Simulate startup time
            print(f"   [{self.name}] Started successfully")

        def stop(self):
            print(f"   [{self.name}] Stopping...")
            print(f"   [{self.name}] Processed {self.events_processed} events")
            self.started = False
            time.sleep(0.05)  # Simulate cleanup time
            print(f"   [{self.name}] Stopped successfully")

        def __call__(self, event):
            if not self.started:
                raise RuntimeError(f"{self.name} not started!")
            self.events_processed += 1
            print(f"   [{self.name}] Processing: {event['type']}")

    # Create handlers
    handler1 = LifecycleHandler("Handler1")
    handler2 = LifecycleHandler("Handler2")
    handler3 = LifecycleHandler("Handler3")

    # Create context with handlers
    print("\n2. Creating context with lifecycle handlers")
    config = ObservabilityConfig(handlers=[handler1, handler2, handler3])
    context = ObservabilityContext(config)

    # Start context - handlers start in order
    print("\n3. Starting context (handlers start in order):")
    context.start()

    # Emit some events
    print("\n4. Emitting events:")
    context.emit("test.event1", "First event")
    context.emit("test.event2", "Second event")

    # Stop context - handlers stop in reverse order
    print("\n5. Stopping context (handlers stop in reverse order):")
    context.stop()

    # Demonstrate auto-start on attach
    print("\n6. Demonstrating auto-start on attach")

    context2 = ObservabilityContext()
    context2.start()  # Start context first

    handler4 = LifecycleHandler("Handler4")
    print("\n   Attaching handler to running context:")
    context2.attach_handler(handler4)
    print("   Handler was auto-started on attach")

    context2.emit("attach.test", "Testing attached handler")

    context2.stop()

    # Mixed handler types
    print("\n7. Mixed handler types (with and without lifecycle)")

    # Handlers with lifecycle
    queued = QueuedHandler(PrintHandler(sys.stdout, format="[Q] {value}"))
    managed_file = ManagedFileHandler("/tmp/lifecycle.log")

    # Handler without lifecycle
    simple_buffer = BufferHandler()

    config3 = ObservabilityConfig(handlers=[queued, managed_file, simple_buffer])
    context3 = ObservabilityContext(config3)

    print("\n   Starting mixed handlers:")
    context3.start()
    print("   Managed handlers started, simple handler ready")

    context3.emit("mixed.test", "Message to all handlers")

    print("\n   Stopping mixed handlers:")
    context3.stop()
    print("   Managed handlers stopped, simple handler unaffected")

    # Error handling during lifecycle
    print("\n8. Error handling during lifecycle")

    class FaultyHandler:
        def __init__(self, name, fail_on_start=False, fail_on_stop=False):
            self.name = name
            self.fail_on_start = fail_on_start
            self.fail_on_stop = fail_on_stop

        def start(self):
            if self.fail_on_start:
                raise Exception(f"{self.name} failed to start!")
            print(f"   [{self.name}] Started")

        def stop(self):
            if self.fail_on_stop:
                raise Exception(f"{self.name} failed to stop!")
            print(f"   [{self.name}] Stopped")

        def __call__(self, event):
            print(f"   [{self.name}] Processing event")

    # Handler that fails on start
    print("\n   Testing handler that fails on start:")
    faulty_start = FaultyHandler("FaultyStart", fail_on_start=True)
    good_handler = LifecycleHandler("GoodHandler")

    config4 = ObservabilityConfig(handlers=[faulty_start, good_handler])
    context4 = ObservabilityContext(config4)

    try:
        context4.start()
    except Exception as e:
        print(f"   Error during start: {e}")
        print("   Note: Other handlers may still be started")

    # Handler that fails on stop
    print("\n   Testing handler that fails on stop:")
    faulty_stop = FaultyHandler("FaultyStop", fail_on_stop=True)

    config5 = ObservabilityConfig(handlers=[good_handler, faulty_stop])
    context5 = ObservabilityContext(config5)

    context5.start()

    try:
        context5.stop()
    except Exception as e:
        print(f"   Error during stop: {e}")
        print("   Note: Other handlers still stopped")

    # Lifecycle state verification
    print("\n9. Lifecycle state verification")

    class StateTrackingHandler:
        def __init__(self):
            self.state = "INIT"
            self.state_history = ["INIT"]

        def start(self):
            self.state = "STARTED"
            self.state_history.append("STARTED")
            print(f"   State: {self.state}")

        def stop(self):
            self.state = "STOPPED"
            self.state_history.append("STOPPED")
            print(f"   State: {self.state}")

        def __call__(self, event):
            if self.state != "STARTED":
                print(f"   WARNING: Processing event in state {self.state}")

    tracker = StateTrackingHandler()

    config6 = ObservabilityConfig(handlers=[tracker])
    context6 = ObservabilityContext(config6)

    print("\n   Handler state transitions:")
    print(f"   Initial: {tracker.state}")

    context6.start()
    context6.emit("state.test", "Test event")
    context6.stop()

    print(f"   History: {' -> '.join(tracker.state_history)}")

    # Best practices
    print("\n10. Handler lifecycle best practices:")
    print("   - Acquire resources in start(), release in stop()")
    print("   - Make stop() idempotent (safe to call multiple times)")
    print("   - Handle errors gracefully in lifecycle methods")
    print("   - Quick startup/shutdown for better responsiveness")
    print("   - Consider timeout mechanisms for long operations")


if __name__ == '__main__':
    main()
