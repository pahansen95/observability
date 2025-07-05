#!/usr/bin/env python3
"""
Example 03: Shared Context

Demonstrates:
- SharedContext.setup() initialization
- Difference between get() and get_context()
- Dynamic handler attachment
- Direct event emission via SharedContext
- Teardown and error handling
"""

import sys
from observability import SharedContext, ObservabilityConfig
from observability.handlers import JsonHandler, PrintHandler


def main():
    """Main example logic."""
    print("=== Example 03: Shared Context ===\n")
    
    # Setup SharedContext with initial config
    print("1. Setting up SharedContext")
    config = ObservabilityConfig(handlers=[PrintHandler(sys.stdout)])
    SharedContext.setup(config)
    print("   SharedContext initialized")
    
    # Demonstrate get() vs get_context()
    print("\n2. Accessing SharedContext")
    shared = SharedContext.get()
    context = SharedContext.get_context()
    print(f"   get() returns: {type(shared).__name__}")
    print(f"   get_context() returns: {type(context).__name__}")
    
    # Attach additional handler dynamically
    print("\n3. Attaching JsonHandler dynamically")
    json_handler = JsonHandler(sys.stdout)
    SharedContext.attach_handler(json_handler)
    print("   JsonHandler attached")
    
    # Emit event through SharedContext
    print("\n4. Emitting event through SharedContext")
    SharedContext.emit('test.event', 'Hello from SharedContext')
    
    # Teardown SharedContext
    print("\n5. Tearing down SharedContext")
    SharedContext.teardown()
    print("   SharedContext torn down")
    
    # Show error after teardown
    print("\n6. Attempting to access after teardown")
    try:
        SharedContext.get()
    except RuntimeError as e:
        print(f"   RuntimeError: {e}")


if __name__ == '__main__':
    main()