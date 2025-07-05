#!/usr/bin/env python3
"""
Example 74: Logger Enabled Check

Demonstrates:
- Using is_enabled_for() to avoid expensive operations
- Conditional debug info generation
- Performance optimization patterns
- Level-based processing
- Lazy evaluation benefits
"""

import sys
import time
import json
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler, BufferHandler
from observability.domains.logging import Logger, DEBUG, INFO, WARNING, ERROR


def compute_expensive_debug_info(data):
    """Simulate expensive debug info calculation."""
    print("   [Computing expensive debug info...]")
    time.sleep(0.1)  # Simulate expensive operation
    
    # Complex object introspection
    debug_info = {
        "data_type": type(data).__name__,
        "data_size": len(str(data)),
        "data_repr": repr(data),
        "memory_estimate": len(str(data)) * 8,  # Rough estimate
        "detailed_analysis": {
            "keys": list(data.keys()) if isinstance(data, dict) else None,
            "length": len(data) if hasattr(data, '__len__') else None,
            "attributes": dir(data)[:10]  # First 10 attributes
        }
    }
    
    return debug_info


def process_data_with_conditional_logging(data, logger):
    """Process data with conditional debug logging."""
    logger.info("Starting data processing", data_id=data.get('id'))
    
    # Only compute expensive debug info if DEBUG is enabled
    if logger.is_enabled_for(DEBUG):
        debug_info = compute_expensive_debug_info(data)
        logger.debug("Detailed debug information", **debug_info)
    else:
        print("   [Skipped expensive debug computation]")
    
    # Simulate processing
    time.sleep(0.01)
    
    # Conditional warning details
    if data.get('size', 0) > 1000:
        if logger.is_enabled_for(WARNING):
            # Only analyze if warnings are enabled
            analysis = {
                "size": data['size'],
                "threshold": 1000,
                "excess": data['size'] - 1000
            }
            logger.warning("Large data size detected", **analysis)
    
    logger.info("Data processing completed")


def benchmark_conditional_logging(context):
    """Benchmark the performance impact of conditional logging."""
    # Logger with INFO level (DEBUG disabled)
    logger = Logger("benchmark", context, INFO)
    
    print("\n   Running benchmark with INFO level (DEBUG disabled):")
    
    # Process without debug overhead
    start_time = time.time()
    for i in range(5):
        data = {"id": i, "size": 500, "content": f"data-{i}" * 100}
        process_data_with_conditional_logging(data, logger)
    
    info_time = time.time() - start_time
    print(f"   Time with INFO level: {info_time:.3f}s")
    
    # Change to DEBUG level
    logger.min_level = DEBUG
    print("\n   Running benchmark with DEBUG level (DEBUG enabled):")
    
    # Process with debug overhead
    start_time = time.time()
    for i in range(5):
        data = {"id": i + 5, "size": 500, "content": f"data-{i}" * 100}
        process_data_with_conditional_logging(data, logger)
    
    debug_time = time.time() - start_time
    print(f"   Time with DEBUG level: {debug_time:.3f}s")
    
    print(f"\n   Performance impact: {(debug_time - info_time):.3f}s ({(debug_time/info_time - 1)*100:.1f}% slower)")


def demonstrate_level_patterns(context):
    """Demonstrate various patterns for level-based processing."""
    logger = Logger("patterns", context, INFO)
    
    # Pattern 1: Expensive serialization
    large_object = {"data": [{"id": i, "values": list(range(100))} for i in range(10)]}
    
    if logger.is_enabled_for(DEBUG):
        # Only serialize if needed
        logger.debug("Large object state", 
                    json_repr=json.dumps(large_object, indent=2))
    
    # Pattern 2: Conditional metric collection
    metrics = {}
    
    if logger.is_enabled_for(DEBUG):
        # Collect detailed metrics only in debug mode
        metrics['detailed'] = {
            'memory_usage': 1024 * 1024,  # Would be actual memory check
            'cpu_percent': 45.2,          # Would be actual CPU check
            'thread_count': 8             # Would be actual thread count
        }
    
    logger.info("Operation completed", **metrics)
    
    # Pattern 3: Multi-level detail
    error_occurred = True
    
    if error_occurred:
        basic_error = "Database connection failed"
        
        if logger.is_enabled_for(ERROR):
            logger.error(basic_error)
            
            if logger.is_enabled_for(WARNING):
                # Add more context at warning level
                logger.warning("Connection retry information",
                             retry_count=3,
                             retry_delay=5)
                
                if logger.is_enabled_for(DEBUG):
                    # Full diagnostics at debug level
                    logger.debug("Detailed connection diagnostics",
                               host="db.example.com",
                               port=5432,
                               ssl_enabled=True,
                               connection_pool_size=10)


def main():
    """Main example logic."""
    print("=== Example 74: Logger Enabled Check ===\n")
    
    # Setup
    buffer = BufferHandler()
    config = ObservabilityConfig(handlers=[
        PrintHandler(sys.stdout, format="[{level_name}] {logger}: {value}"),
        buffer
    ])
    context = ObservabilityContext(config)
    context.start()
    
    # Example 1: Basic conditional logging
    print("1. Basic conditional debug logging:")
    logger = Logger("example", context, INFO)
    
    # This expensive operation won't run
    if logger.is_enabled_for(DEBUG):
        expensive_data = compute_expensive_debug_info({"test": "data"})
        logger.debug("Debug info", data=expensive_data)
    else:
        print("   Debug logging skipped (INFO level set)")
    
    # Example 2: Process with conditional logging
    print("\n2. Processing with conditional debug info:")
    test_data = {
        "id": "TEST-001",
        "size": 1500,
        "type": "large_dataset"
    }
    process_data_with_conditional_logging(test_data, logger)
    
    # Example 3: Performance benchmark
    print("\n3. Performance impact benchmark:")
    benchmark_conditional_logging(context)
    
    # Example 4: Various level-based patterns
    print("\n4. Level-based processing patterns:")
    demonstrate_level_patterns(context)
    
    # Example 5: Analyze logged events
    print("\n5. Analyzing conditional logging impact:")
    events = buffer.get_events()
    
    level_counts = {}
    for event in events:
        level_name = event.get('level_name', 'UNKNOWN')
        level_counts[level_name] = level_counts.get(level_name, 0) + 1
    
    print("   Events by level:")
    for level, count in sorted(level_counts.items()):
        print(f"     - {level}: {count}")
    
    # Best practices
    print("\n6. Best practices for conditional logging:")
    print("   - Always check is_enabled_for() before expensive operations")
    print("   - Use for serialization, introspection, or I/O operations")
    print("   - Particularly important in hot code paths")
    print("   - Combine with lazy evaluation patterns")
    print("   - Consider level-appropriate detail gradation")
    
    context.stop()


if __name__ == '__main__':
    main()