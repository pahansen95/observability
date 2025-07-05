#!/usr/bin/env python3
"""
Example 12: Logging Structured

Demonstrates:
- Logging with structured data via kwargs
- Different data types in structured fields
- Using same key with different values
- Args parameter for message formatting
- Accessing logger properties
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import JsonHandler, BufferHandler
from observability.domains.logging import Logger, INFO


def main():
    """Main example logic."""
    print("=== Example 12: Logging Structured ===\n")
    
    # Create context with JsonHandler for structured output
    print("1. Creating context with JsonHandler and BufferHandler")
    json_handler = JsonHandler(sys.stdout)
    buffer_handler = BufferHandler()
    config = ObservabilityConfig(handlers=[json_handler, buffer_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Create logger
    print("\n2. Creating logger for structured logging")
    logger = Logger(
        name="app.structured",
        context=context,
        min_level=INFO
    )
    
    # Log with various kwargs
    print("\n3. Logging with structured data (kwargs):")
    
    # String fields
    logger.info("User logged in", 
                username="alice",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0")
    
    # Numeric fields
    logger.info("Request processed",
                status_code=200,
                response_time_ms=45.3,
                bytes_sent=1024)
    
    # Complex data types
    logger.info("Batch processed",
                items=["item1", "item2", "item3"],
                metadata={"source": "api", "version": "2.0"},
                success=True,
                failed_count=0)
    
    # Same key with different values
    print("\n4. Using same key with different values:")
    logger.info("Process started", status="running", pid=1234)
    logger.info("Process completed", status="success", duration_s=10.5)
    logger.info("Process failed", status="error", error_code="TIMEOUT")
    
    # Using args parameter for formatting
    print("\n5. Using args parameter for message formatting:")
    logger.info("Processing %d items from %s", 42, "queue", 
                source="batch_processor",
                priority="high")
    
    # Access logger properties
    print("\n6. Logger configuration:")
    print(f"   Logger created with name: app.structured")
    print(f"   Logger min_level: INFO")
    print(f"   Using structured logging with JsonHandler")
    
    # Examine captured structured data
    print("\n7. Examining captured structured events:")
    events = buffer_handler.get_events()
    if events:
        # Show first event structure
        first_event = events[0]
        print("\n   First event structure:")
        print(f"   - type: {first_event.get('type')}")
        print(f"   - logger: {first_event.get('logger')}")
        print(f"   - message: {first_event.get('message')}")
        print(f"   - username: {first_event.get('username')}")
        print(f"   - ip_address: {first_event.get('ip_address')}")
        
        # Count structured fields
        print(f"\n   Total events captured: {len(events)}")
        for i, event in enumerate(events[:3]):
            custom_fields = [k for k in event.keys() 
                           if k not in ['type', 'value', 'timestamp_ns', 
                                       'logger', 'severity', 'message']]
            print(f"   Event {i+1} has {len(custom_fields)} custom fields: {custom_fields}")
    
    context.stop()


if __name__ == '__main__':
    main()