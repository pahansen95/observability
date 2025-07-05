#!/usr/bin/env python3
"""
Example 05: Event Emission

Demonstrates:
- Emitting events with different value types
- Events with metadata (kwargs)
- Automatic timestamp_ns addition
- Checking has_handlers() before emission
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler


def main():
    """Main example logic."""
    print("=== Example 05: Event Emission ===\n")
    
    # Create context with PrintHandler
    print("1. Creating context with PrintHandler")
    handler = PrintHandler(
        sys.stdout,
        format="{timestamp_ns} [{type}] {value}"
    )
    config = ObservabilityConfig(handlers=[handler])
    context = ObservabilityContext(config)
    context.start()
    print("   Context created with custom format PrintHandler\n")
    
    # Check has_handlers before emission
    print("2. Checking has_handlers()")
    if context.has_handlers():
        print("   Handlers present, safe to emit events\n")
    
    # Simple event emission
    print("3. Simple event emission:")
    context.emit('app.start', 'Starting application')
    
    # Event with metadata
    print("\n4. Event with metadata:")
    context.emit('user.login', {'id': 123}, username='alice', ip='192.168.1.1')
    
    # Complex value event
    print("\n5. Complex value event:")
    context.emit('data.processed', [1, 2, 3], count=3, status='success')
    
    # Demonstrate timestamp_ns is automatic
    print("\n6. Note: timestamp_ns is automatically added to all events")
    print("   (visible in the output above)")
    
    # Show conditional emission pattern
    print("\n7. Conditional emission pattern:")
    print("   if context.has_handlers():")
    print("       # Only compute expensive values if handlers present")
    print("       expensive_data = compute_expensive_data()")
    print("       context.emit('expensive.event', expensive_data)")
    
    context.stop()


def compute_expensive_data():
    """Placeholder for expensive computation."""
    return "expensive result"


if __name__ == '__main__':
    main()