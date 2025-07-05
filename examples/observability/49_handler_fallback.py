#!/usr/bin/env python3
"""
Example 49: Handler Fallback

Demonstrates:
- Creating FallbackHandler with handler list
- Deliberately failing handlers
- Fallback behavior
- Successful handler stops chain
- All handlers tried on failure
"""

import sys
import tempfile
import os
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import FallbackHandler, PrintHandler, JsonHandler, ManagedFileHandler, BufferHandler
from observability.domains.logging import Logger, ERROR


def main():
    """Main example logic."""
    print("=== Example 49: Handler Fallback ===\n")

    # Create handlers with different failure modes
    print("1. Creating handlers with failure scenarios")

    class NetworkHandler:
        def __init__(self, name, fail_rate=0):
            self.name = name
            self.fail_rate = fail_rate
            self.attempt_count = 0

        def __call__(self, event):
            self.attempt_count += 1
            if self.attempt_count <= self.fail_rate:
                raise ConnectionError(f"{self.name}: Network unreachable")
            print(f"[{self.name}] Successfully sent: {event['type']}")

    # Handler that always fails
    always_fails = NetworkHandler("PRIMARY", fail_rate=999)

    # Handler that fails first 2 times
    flaky_handler = NetworkHandler("SECONDARY", fail_rate=2)

    # Handler that always works
    reliable_handler = PrintHandler(sys.stdout, format="[RELIABLE] {type}: {value}")

    # Create fallback chain
    print("\n2. Creating FallbackHandler chain")
    fallback = FallbackHandler(always_fails, flaky_handler, reliable_handler)

    config = ObservabilityConfig(handlers=[fallback])
    context = ObservabilityContext(config)
    context.start()

    # First event - primary fails, secondary fails, reliable works
    print("\n3. First event (all handlers attempted):")
    context.emit("test.event", "First message")

    # Second event - primary fails, secondary fails, reliable works
    print("\n4. Second event (secondary still failing):")
    context.emit("test.event", "Second message")

    # Third event - primary fails, secondary now works
    print("\n5. Third event (secondary now working):")
    context.emit("test.event", "Third message")
    print("   Note: Reliable handler not called (secondary succeeded)")

    # File-based fallback scenario
    print("\n6. File-based fallback scenario")

    # Primary: Network destination (simulated)
    class RemoteHandler:
        def __call__(self, event):
            raise ConnectionError("Remote server unavailable")

    # Secondary: Local file
    local_file = tempfile.mktemp(suffix='-fallback.log')
    file_handler = ManagedFileHandler(local_file)

    # Tertiary: In-memory buffer
    buffer_handler = BufferHandler()

    file_fallback = FallbackHandler(
        RemoteHandler(),
        file_handler,
        buffer_handler
    )

    file_fallback.start()  # Start managed handlers

    config2 = ObservabilityConfig(handlers=[file_fallback])
    context2 = ObservabilityContext(config2)
    context2.start()

    print("\n7. Emitting events with remote failure:")
    logger = Logger("fallback.test", context2, ERROR)

    logger.error("Critical error message")
    logger.error("Another error message")

    print("   Remote failed, events written to local file")

    # Stop to flush file
    context2.stop()
    file_fallback.stop()

    # Check file
    if os.path.exists(local_file):
        with open(local_file, 'r') as f:
            lines = f.readlines()
        print(f"   Local file contains {len(lines)} events")
        os.unlink(local_file)

    # Demonstrate successful handler stops chain
    print("\n8. Successful handler stops the chain")

    call_tracker = []

    class TrackingHandler:
        def __init__(self, name, should_fail=False):
            self.name = name
            self.should_fail = should_fail

        def __call__(self, event):
            call_tracker.append(self.name)
            if self.should_fail:
                raise Exception(f"{self.name} failed")
            print(f"[{self.name}] Handled event")

    chain_fallback = FallbackHandler(
        TrackingHandler("Handler1", should_fail=True),
        TrackingHandler("Handler2", should_fail=False),
        TrackingHandler("Handler3", should_fail=False)  # Never called
    )

    config3 = ObservabilityConfig(handlers=[chain_fallback])
    context3 = ObservabilityContext(config3)
    context3.start()

    context3.emit("chain.test", "Testing chain")

    print(f"   Handlers called: {call_tracker}")
    print("   Handler3 was not called (Handler2 succeeded)")

    # Complex fallback patterns
    print("\n9. Complex fallback patterns")

    # Different fallbacks for different severity
    high_priority_fallback = FallbackHandler(
        RemoteHandler(),
        JsonHandler(sys.stderr),  # Fallback to stderr
        BufferHandler()           # Last resort
    )

    low_priority_fallback = FallbackHandler(
        BufferHandler()  # Just buffer low priority
    )

    from observability.handlers import filtered

    # Route by severity
    high_priority_filtered = filtered(
        high_priority_fallback,
        lambda e: e.get('level', 0) >= ERROR
    )

    low_priority_filtered = filtered(
        low_priority_fallback,
        lambda e: e.get('level', 0) < ERROR
    )

    config4 = ObservabilityConfig(handlers=[high_priority_filtered, low_priority_filtered])
    context4 = ObservabilityContext(config4)
    context4.start()

    logger2 = Logger("priority.test", context4, ERROR)

    print("\n10. Priority-based fallback routing:")
    logger2.error("High priority error")
    logger2.info("Low priority info")

    print("   Errors went through fallback chain")
    print("   Info went directly to buffer")

    # Best practices
    print("\n11. Fallback handler best practices:")
    print("   - Order handlers from most preferred to least")
    print("   - Fast/cheap handlers last (e.g., BufferHandler)")
    print("   - Consider retry logic in custom handlers")
    print("   - Monitor fallback usage for operational health")

    # Clean up
    context.stop()
    context3.stop()
    context4.stop()


if __name__ == '__main__':
    main()
