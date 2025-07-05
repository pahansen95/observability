#!/usr/bin/env python3
"""
Example 41: Handler JSON

Demonstrates:
- Creating JsonHandler with stream
- Pretty printing with indent=2
- Sorting keys with sort_keys=True
- Emitting complex nested events
- JSON serialization of all types
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import JsonHandler
from observability.domains.logging import Logger, INFO
from observability.domains.metrics import Counter, Histogram


def main():
    """Main example logic."""
    print("=== Example 41: Handler JSON ===\n")

    # Default JsonHandler
    print("1. Creating JsonHandler with default settings")
    default_handler = JsonHandler(sys.stdout)

    config = ObservabilityConfig(handlers=[default_handler])
    context = ObservabilityContext(config)
    context.start()

    print("\n2. Emitting simple event (compact JSON):")
    context.emit("simple.event", "Hello JSON")

    context.stop()

    # Pretty-printed JSON
    print("\n3. Creating JsonHandler with pretty printing")
    pretty_handler = JsonHandler(sys.stdout)

    config2 = ObservabilityConfig(handlers=[pretty_handler])
    context2 = ObservabilityContext(config2)
    context2.start()

    print("\n4. Emitting complex nested event:")
    context2.emit("complex.event", {
        "user": {
            "id": 123,
            "name": "Alice",
            "roles": ["admin", "user"]
        },
        "metadata": {
            "ip": "192.168.1.1",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    })

    # Sorted keys
    print("\n5. Creating JsonHandler with sorted keys")
    sorted_handler = JsonHandler(sys.stdout)

    config3 = ObservabilityConfig(handlers=[sorted_handler])
    context3 = ObservabilityContext(config3)
    context3.start()

    print("\n6. Emitting event with sorted keys:")
    context3.emit("sorted.event", "Keys will be alphabetized",
                  zebra="last",
                  alpha="first",
                  middle="center")

    # Various data types
    print("\n7. JSON serialization of various types:")
    context3.emit("types.showcase", {
        "string": "text value",
        "integer": 42,
        "float": 3.14159,
        "boolean": True,
        "null": None,
        "list": [1, 2, 3],
        "dict": {"nested": "object"},
        "unicode": "Hello 世界 🌍"
    })

    # Using with Logger
    print("\n8. Using JsonHandler with Logger:")
    logger = Logger("json.logger", context3, INFO)
    logger.info("User action",
                action="purchase",
                user_id=456,
                items=["book", "pen"],
                total=29.99,
                success=True)

    # Using with Metrics
    print("\n9. Using JsonHandler with Metrics:")
    counter = Counter("api_requests", context3, unit="requests")
    counter.increment(1.0, endpoint="/api/users", method="GET", status=200)

    histogram = Histogram("response_time", context3, unit="seconds",
                         buckets=[0.1, 0.5, 1.0, 2.0])
    histogram.observe(0.234, endpoint="/api/users")

    # Error scenarios
    print("\n10. Handling non-serializable objects:")
    class CustomObject:
        def __repr__(self):
            return "CustomObject()"

    # This will use the string representation
    context3.emit("custom.object", CustomObject())

    # Large nested structure
    print("\n11. Large nested structure:")
    large_event = {
        "level1": {
            "level2": {
                "level3": {
                    "level4": {
                        "data": "deeply nested"
                    }
                }
            }
        },
        "array": list(range(10))
    }
    context3.emit("nested.structure", large_event)

    # Clean up
    context2.stop()
    context3.stop()


if __name__ == '__main__':
    main()
