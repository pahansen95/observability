#!/usr/bin/env python3
"""
Example 46: Handler Sampled

Demonstrates:
- Creating sampled() handler with different rates
- Using seed for deterministic sampling
- Statistical sampling verification
- Combining with filtered()
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import sampled, filtered, BufferHandler, PrintHandler
from observability.domains.logging import Logger, INFO


def main():
    """Main example logic."""
    print("=== Example 46: Handler Sampled ===\n")
    
    # Create base handler
    buffer_handler = BufferHandler()
    
    # 10% sampling rate
    print("1. Creating sampled handler with 10% rate")
    sampled_10 = sampled(
        0.1,
        PrintHandler(sys.stdout, format="[SAMPLED] {type}: {value}")
    )
    
    config = ObservabilityConfig(handlers=[sampled_10, buffer_handler])
    context = ObservabilityContext(config)
    context.start()
    
    print("\n2. Emitting 20 events with 10% sampling:")
    for i in range(20):
        context.emit("test.event", f"Event {i}")
    
    print("   Approximately 2 events should be printed")
    
    # Deterministic sampling with seed
    print("\n3. Deterministic sampling with seed")
    
    # Create buffer handlers separately to track them
    buffer1 = BufferHandler()
    buffer2 = BufferHandler()
    
    sampled_seeded1 = sampled(
        0.5,
        buffer1,
        seed=42
    )
    
    sampled_seeded2 = sampled(
        0.5,
        buffer2,
        seed=42  # Same seed
    )
    
    config2 = ObservabilityConfig(handlers=[sampled_seeded1, sampled_seeded2])
    context2 = ObservabilityContext(config2)
    context2.start()
    
    # Emit events
    for i in range(10):
        context2.emit("deterministic.test", f"Event {i}")
    
    # Check both handlers got same events
    events1 = buffer1.get_events()
    events2 = buffer2.get_events()
    
    print(f"   Handler 1 sampled: {len(events1)} events")
    print(f"   Handler 2 sampled: {len(events2)} events")
    print(f"   Same events sampled: {len(events1) == len(events2)}")
    
    # Statistical verification with large sample
    print("\n4. Statistical sampling verification (1% rate)")
    
    one_percent_buffer = BufferHandler()
    one_percent_sampled = sampled(0.01, one_percent_buffer)
    
    config3 = ObservabilityConfig(handlers=[one_percent_sampled])
    context3 = ObservabilityContext(config3)
    context3.start()
    
    # Emit 1000 events
    print("   Emitting 1000 events...")
    for i in range(1000):
        context3.emit("sample.test", i)
    
    sampled_events = one_percent_buffer.get_events()
    sample_rate = len(sampled_events) / 1000
    print(f"   Expected ~10 events (1%)")
    print(f"   Actually sampled: {len(sampled_events)} events")
    print(f"   Actual rate: {sample_rate:.1%}")
    
    # Different sampling rates for different event types
    print("\n5. Different sampling rates by event type")
    
    # High-frequency events: 0.1% sampling
    high_freq_sampled = sampled(
        0.001,
        PrintHandler(sys.stdout, format="[HIGH_FREQ] {value}")
    )
    
    # Low-frequency events: 100% sampling
    low_freq_handler = PrintHandler(sys.stdout, format="[LOW_FREQ] {value}")
    
    # Route based on event type
    high_freq_filtered = filtered(
        lambda e: e['type'] == 'high.frequency',
        high_freq_sampled
    )
    
    low_freq_filtered = filtered(
        lambda e: e['type'] == 'low.frequency',
        low_freq_handler
    )
    
    config4 = ObservabilityConfig(handlers=[high_freq_filtered, low_freq_filtered])
    context4 = ObservabilityContext(config4)
    context4.start()
    
    print("\n6. Emitting high and low frequency events:")
    
    # Many high frequency events
    for i in range(100):
        context4.emit("high.frequency", f"High freq {i}")
    
    # Few low frequency events
    for i in range(5):
        context4.emit("low.frequency", f"Low freq {i}")
    
    print("   High frequency: ~0.1% sampled")
    print("   Low frequency: 100% printed")
    
    # Combining sampling with logging
    print("\n7. Sampling debug logs in production")
    
    # Sample debug logs at 5%, but keep all warnings and above
    debug_sampled = sampled(
        0.05,
        PrintHandler(sys.stdout, format="[DEBUG_SAMPLE] {value}")
    )
    
    debug_filtered = filtered(
        lambda e: e.get('level', 0) <= INFO,
        debug_sampled
    )
    
    important_handler = filtered(
        lambda e: e.get('level', 0) > INFO,
        PrintHandler(sys.stdout, format="[IMPORTANT] {value}")
    )
    
    config5 = ObservabilityConfig(handlers=[debug_filtered, important_handler])
    context5 = ObservabilityContext(config5)
    context5.start()
    
    logger = Logger("sampled.logger", context5, INFO)
    
    print("\n8. Logging with sampling:")
    for i in range(10):
        logger.info(f"Info message {i}")  # 5% sampled
    
    logger.warning("This warning always appears")  # 100%
    logger.error("This error always appears")      # 100%
    
    # Examine total events
    print("\n9. Summary of all events:")
    all_events = buffer_handler.get_events()
    print(f"   Total events emitted: {len(all_events)}")
    
    # Clean up
    context.stop()
    context2.stop()
    context3.stop()
    context4.stop()
    context5.stop()


if __name__ == '__main__':
    main()