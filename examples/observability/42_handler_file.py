#!/usr/bin/env python3
"""
Example 42: Handler File

Demonstrates:
- Creating ManagedFileHandler with all parameters
- Explicit start() call
- Writing events to file in JSON format
- Flush interval and time-based flushing
- Explicit stop() for cleanup
- Reading file contents
"""

import os
import tempfile
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import ManagedFileHandler
from observability.domains.logging import Logger, INFO, DEBUG


def main():
    """Main example logic."""
    print("=== Example 42: Handler File ===\n")

    # Create temporary directory for file output
    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "observability.log")

    print("1. Creating ManagedFileHandler")
    print(f"   File path: {log_file}")

    # Create handler with default JSON format
    file_handler = ManagedFileHandler(
        log_file,
        format="json",
        mode="a",
        encoding="utf-8",
        flush_interval=5,    # Flush every 5 events
        flush_time=1.0       # Or every 1 second
    )

    # Create context but don't start yet
    config = ObservabilityConfig(handlers=[file_handler])
    context = ObservabilityContext(config)

    # Explicitly start the handler
    print("\n2. Starting handler explicitly")
    file_handler.start()
    context.start()
    print("   Handler and context started")

    # Create logger and emit events
    print("\n3. Emitting events to file")
    logger = Logger("file.example", context, DEBUG)

    logger.info("Application started")
    logger.debug("Debug information", detail="verbose")
    logger.warning("This is a warning", code="W001")
    logger.error("An error occurred", error_id="E100")

    # Emit more events
    for i in range(10):
        logger.info(f"Processing item {i}",
                   item_id=i,
                   progress=f"{(i+1)*10}%")

    # Emit different event types
    context.emit("metric.counter", "requests", measurement=100)
    context.emit("trace.span.start", "process_batch", span_id="span-123")
    context.emit("trace.span.end", "process_batch", span_id="span-123", duration_ns=50000000)

    print("   Events written to file")

    # Stop handler to flush and close file
    print("\n4. Stopping handler to flush data")
    context.stop()
    file_handler.stop()
    print("   Handler stopped and file closed")

    # Read and display file contents
    print("\n5. Reading file contents:")
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            contents = f.read()
            lines = contents.strip().split('\n')
            print(f"   Total lines written: {len(lines)}")
            print("\n   First 5 lines:")
            for line in lines[:5]:
                print(f"   {line}")
            if len(lines) > 5:
                print(f"   ... and {len(lines) - 5} more lines")

    # Demonstrate different formats
    print("\n6. Creating handler with text format")

    # Create handler with text format
    text_file = os.path.join(temp_dir, "text_format.log")
    text_handler = ManagedFileHandler(
        text_file,
        format="text",  # Use text format instead of JSON
        mode="a"
    )

    config2 = ObservabilityConfig(handlers=[text_handler])
    context2 = ObservabilityContext(config2)
    text_handler.start()
    context2.start()

    # Write some events
    logger2 = Logger("text.format", context2, INFO)
    logger2.info("This is a text formatted message")
    logger2.warning("Warning in text format", code="W002")
    logger2.error("Error in text format", details="Something went wrong")

    context2.stop()
    text_handler.stop()

    # Show text file contents
    print("\n7. Text format file contents:")
    if os.path.exists(text_file):
        with open(text_file, 'r') as f:
            for line in f:
                print(f"   {line.strip()}")

    # Cleanup
    print("\n8. Cleanup note:")
    print(f"   Log files created in: {temp_dir}")
    print("   (Directory will persist for inspection)")


if __name__ == '__main__':
    main()
