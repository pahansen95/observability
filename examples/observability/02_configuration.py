#!/usr/bin/env python3
"""
Example 02: Configuration

Demonstrates:
- Creating ObservabilityConfig with all parameters
- Accessing all config properties
- Config immutability
- PrintHandler usage in configuration
"""

import sys
from observability import ObservabilityConfig
from observability.handlers import PrintHandler


def main():
    """Main example logic."""
    print("=== Example 02: Configuration ===\n")
    
    # Create PrintHandler for stdout
    print("1. Creating PrintHandler for stdout")
    print_handler = PrintHandler(sys.stdout)
    print("   PrintHandler created")
    
    # Create ObservabilityConfig with all parameters
    print("\n2. Creating ObservabilityConfig with all parameters")
    config = ObservabilityConfig(
        handlers=[print_handler],
        sampling_rate=0.5,
        enabled_categories={'logging', 'metrics'}
    )
    print("   Config created with full parameters")
    
    # Access all config properties
    print("\n3. Accessing config properties:")
    print(f"   handlers: {config.handlers} (count: {len(config.handlers)})")
    print(f"   sampling_rate: {config.sampling_rate}")
    print(f"   enabled_categories: {config.enabled_categories}")
    
    # Demonstrate config immutability
    print("\n4. Config immutability:")
    print("   # The following would fail if uncommented:")
    print("   # config.enabled = False  # AttributeError: can't set attribute")
    print("   # config.handlers.append(another_handler)  # AttributeError")
    print("   Config properties are read-only")


if __name__ == '__main__':
    main()