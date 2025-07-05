#!/usr/bin/env python3
"""
Example 11: Logging Hierarchical

Demonstrates:
- Creating root logger
- Using get_child() for hierarchical naming
- Creating grandchild loggers
- Different min_levels on each logger
- Hierarchical naming in output
- Child loggers inherit context but not level
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler
from observability.domains.logging import Logger, DEBUG, INFO, WARNING, ERROR


def main():
    """Main example logic."""
    print("=== Example 11: Logging Hierarchical ===\n")

    # Create context with PrintHandler showing logger names
    print("1. Creating context with PrintHandler")
    handler = PrintHandler(
        sys.stdout,
        format="[{level}] {value}"
    )
    config = ObservabilityConfig(handlers=[handler])
    context = ObservabilityContext(config)
    context.start()

    # Create root logger
    print("\n2. Creating root logger 'app'")
    root_logger = Logger(
        name="app",
        context=context,
        min_level=INFO
    )
    print("   Root logger created")

    # Create child loggers
    print("\n3. Creating child loggers with get_child()")
    db_logger = root_logger.get_child("database")
    api_logger = root_logger.get_child("api")
    print("   Database logger created: app.database")
    print("   API logger created: app.api")

    # Create grandchild logger
    print("\n4. Creating grandchild logger")
    auth_logger = api_logger.get_child("auth")
    print("   Auth logger created: app.api.auth")

    # Set different min_levels
    print("\n5. Setting different min_levels on each logger")
    root_logger.min_level = WARNING
    db_logger.min_level = DEBUG
    api_logger.min_level = INFO
    auth_logger.min_level = ERROR
    print("   Root logger level: WARNING")
    print("   Database logger level: DEBUG")
    print("   API logger level: INFO")
    print("   Auth logger level: ERROR")

    # Demonstrate hierarchical naming
    print("\n6. Logging from different loggers:")
    root_logger.warning("Application started")
    root_logger.info("This won't appear - level too low")

    db_logger.debug("Connected to database")
    db_logger.info("Executing query")
    db_logger.warning("Query took 2.5 seconds")

    api_logger.info("API endpoint called")
    api_logger.warning("Rate limit approaching")

    auth_logger.error("Authentication failed for user")
    auth_logger.warning("This won't appear - level too low")

    # Show child loggers inherit context
    print("\n7. Child loggers inherit context but not level:")
    print("   All loggers share same context provider")
    print("   But have independent severity levels")

    # Create orphan logger
    print("\n8. Creating logger without parent")
    orphan_logger = Logger(
        name="standalone.service",
        context=context,
        min_level=INFO
    )
    orphan_logger.info("Independent logger without parent hierarchy")

    context.stop()


if __name__ == '__main__':
    main()
