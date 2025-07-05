#!/usr/bin/env python3
"""
Example 40: Handler Print

Demonstrates:
- Creating PrintHandler with default parameters
- Custom format string with multiple fields
- Setting include_context=True
- Emitting various event types
- Missing field handling
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig, trace_id
from observability.handlers import PrintHandler
from observability.domains.logging import Logger, INFO


def main():
    """Main example logic."""
    print("=== Example 40: Handler Print ===\n")
    
    # Default PrintHandler
    print("1. Creating PrintHandler with default parameters")
    default_handler = PrintHandler()
    print("   Default handler created (writes to stderr)")
    
    # Custom format string
    print("\n2. Creating PrintHandler with custom format")
    custom_handler = PrintHandler(
        stream=sys.stdout,
        format="{timestamp_ns} [{type}] {value} (trace={trace_id})"
    )
    
    config = ObservabilityConfig(handlers=[custom_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Set trace ID for context
    trace_id.set("trace-456")
    
    # Emit various event types
    print("\n3. Emitting various event types:")
    context.emit("app.start", "Application starting")
    context.emit("user.action", {"action": "login", "user": "alice"})
    context.emit("metric.gauge", {"name": "memory", "value": 1024})
    
    # Show include_context parameter
    print("\n4. Creating handler with include_context=True")
    context.stop()
    
    context_handler = PrintHandler(
        stream=sys.stdout,
        format="{type}: {value}",
        include_context=True
    )
    config2 = ObservabilityConfig(handlers=[context_handler])
    context2 = ObservabilityContext(config2)
    context2.start()
    
    print("   Handler will include all event fields in output")
    context2.emit("test.event", "With full context", custom_field="custom_value")
    
    # Demonstrate missing field handling
    print("\n5. Demonstrating missing field handling")
    missing_field_handler = PrintHandler(
        stream=sys.stdout,
        format="[{severity}] {message} - {undefined_field}"
    )
    config3 = ObservabilityConfig(handlers=[missing_field_handler])
    context3 = ObservabilityContext(config3)
    context3.start()
    
    context3.emit("log.info", "Test message")
    print("   Note: Missing fields show format error")
    
    # Complex format example
    print("\n6. Complex format example")
    complex_handler = PrintHandler(
        stream=sys.stdout,
        format="[{timestamp_ns}] {type} | value={value} | trace={trace_id}"
    )
    config4 = ObservabilityConfig(handlers=[complex_handler])
    context4 = ObservabilityContext(config4)
    context4.start()
    
    # Use with logger for structured output
    logger = Logger("app.handler", context4, INFO)
    logger.info("Structured log message", request_id="req-789", duration_ms=45.2)
    
    # Multiple handlers with different formats
    print("\n7. Multiple PrintHandlers with different formats")
    simple_handler = PrintHandler(sys.stdout, format="{type}: {value}")
    detailed_handler = PrintHandler(sys.stderr, format="[{timestamp_ns}] {type} - {value}")
    
    config5 = ObservabilityConfig(handlers=[simple_handler, detailed_handler])
    context5 = ObservabilityContext(config5)
    context5.start()
    
    print("   Emitting to both stdout and stderr with different formats")
    context5.emit("dual.output", "Message to both handlers")
    
    # Clean up
    context2.stop()
    context3.stop()
    context4.stop()
    context5.stop()


if __name__ == '__main__':
    main()