#!/usr/bin/env python3
"""
Example 01: Basic Setup

Demonstrates:
- Creating ObservabilityConfig with empty handlers
- Creating ObservabilityContext from config
- Basic context lifecycle (start, stop)
- Checking handler presence with has_handlers()
"""

from observability import ObservabilityContext, ObservabilityConfig


def main():
    """Main example logic."""
    print("=== Example 01: Basic Setup ===\n")

    # Create config with empty handlers list
    print("1. Creating ObservabilityConfig with empty handlers")
    config = ObservabilityConfig(handlers=[])
    print(f"   Config created: handlers={len(config.handlers)}")

    # Create context with config
    print("\n2. Creating ObservabilityContext from config")
    context = ObservabilityContext(config)
    print("   Context created successfully")

    # Check handler presence before start
    print("\n3. Checking handler presence before start")
    print(f"   has_handlers(): {context.has_handlers()}")

    # Start the context
    print("\n4. Starting context")
    context.start()
    print("   Context started")

    # Check handler presence after start
    print("\n5. Checking handler presence after start")
    print(f"   has_handlers(): {context.has_handlers()}")

    # Stop the context
    print("\n6. Stopping context")
    context.stop()
    print("   Context stopped")

    print("\nContext lifecycle: created -> started -> stopped")


if __name__ == '__main__':
    main()
