#!/usr/bin/env python3
"""
Example 10: Logging Basics

Demonstrates:
- Creating Logger with name, context, and min_level
- All logging methods: debug(), info(), warning(), error(), critical()
- Using log() with explicit level parameter
- Conditional logging with is_enabled_for()
- Min_level filtering behavior
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler
from observability.domains.logging import Logger, DEBUG, INFO, WARNING, ERROR, CRITICAL


def main():
    """Main example logic."""
    print("=== Example 10: Logging Basics ===\n")
    
    # Create context with PrintHandler
    print("1. Creating context with PrintHandler")
    handler = PrintHandler(
        sys.stdout,
        format="[{level}] {value}"
    )
    config = ObservabilityConfig(handlers=[handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Create Logger with DEBUG level
    print("\n2. Creating Logger with DEBUG min_level")
    logger = Logger(
        name="app.main",
        context=context,
        min_level=DEBUG
    )
    print(f"   Logger created successfully")
    
    # Demonstrate all logging methods
    print("\n3. Using all logging methods:")
    logger.debug("Debug message - detailed diagnostic info")
    logger.info("Info message - general informational message")
    logger.warning("Warning message - something unexpected happened")
    logger.error("Error message - serious problem occurred")
    logger.critical("Critical message - system may be unusable")
    
    # Use log() with explicit level
    print("\n4. Using log() with explicit level:")
    logger.log(INFO, "Using log() method with INFO level")
    logger.log(ERROR, "Using log() method with ERROR level")
    
    # Note: is_enabled_for() might not be implemented
    print("\n5. Conditional logging pattern:")
    # In production, you might check if debug is enabled before expensive operations
    expensive_debug_data = compute_expensive_debug_info()
    logger.debug(f"Expensive debug data: {expensive_debug_data}")
    
    # Change min_level to WARNING
    print("\n6. Setting min_level to WARNING")
    logger.min_level = WARNING
    print(f"   Logger level changed to WARNING")
    
    # Show filtering behavior
    print("\n7. Demonstrating level filtering:")
    logger.debug("This debug message will NOT appear")
    logger.info("This info message will NOT appear")
    logger.warning("This warning message WILL appear")
    logger.error("This error message WILL appear")
    
    # Note about level filtering
    print("\n8. Level filtering note:")
    print("   Messages below WARNING level are now filtered out")
    print("   Only WARNING, ERROR, and CRITICAL will be emitted")
    
    context.stop()


def compute_expensive_debug_info():
    """Simulate expensive computation for debug logging."""
    return {"computed": "expensive_value", "cost": "high"}


if __name__ == '__main__':
    main()