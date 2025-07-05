#!/usr/bin/env python3
"""
Example 51: Handler Composition

Demonstrates:
- 3-level handler tree
- Combining filtered, sampled, and queued
- Fanout with different targets
- Complex routing rules
- Composition patterns
"""

import sys
import tempfile
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import (
    filtered, sampled, 
    FanoutHandler, FallbackHandler,
    QueuedHandler, TimeDeltaHandler,
    PrintHandler, JsonHandler, BufferHandler, ManagedFileHandler
)
from observability.domains.logging import Logger, DEBUG, INFO, WARNING, ERROR
from observability.domains.metrics import Counter, Histogram
from observability.domains.tracing import Span


def main():
    """Main example logic."""
    print("=== Example 51: Handler Composition ===\n")
    
    # Build complex handler tree
    print("1. Building 3-level handler composition tree")
    
    # Level 1: Base handlers
    console_handler = PrintHandler(sys.stdout, format="[CONSOLE] {type}: {value}")
    json_handler = JsonHandler(sys.stderr)
    metrics_buffer = BufferHandler()
    logs_buffer = BufferHandler()
    
    # Level 2: Add filtering and sampling
    
    # High-priority logs (ERROR+) go to console immediately
    high_priority_console = filtered(
        lambda e: e.get('level', 0) >= ERROR,
        console_handler
    )
    
    # Sample 10% of INFO/DEBUG logs to JSON
    sampled_json = filtered(
        lambda e: e.get('level', 0) < WARNING,
        sampled(0.1, json_handler)
    )
    
    # All metrics to metrics buffer
    metrics_only = filtered(
        lambda e: e['type'].startswith('metric.'),
        metrics_buffer
    )
    
    # All logs to logs buffer
    logs_only = filtered(
        lambda e: e['type'].startswith('log.'),
        logs_buffer
    )
    
    # Level 3: Compose into higher-level structures
    
    # Logging pipeline
    logging_pipeline = FanoutHandler(
        high_priority_console,  # Errors to console
        sampled_json,          # Sample of info/debug to JSON
        logs_only              # All logs to buffer
    )
    
    # Metrics pipeline with time delta
    metrics_pipeline = TimeDeltaHandler(
        FanoutHandler(
            metrics_only,
            filtered(
                lambda e: e['type'] == 'metric.counter',
                PrintHandler(sys.stdout, format="[METRIC] {name}={measurement} Δ{delta_ns}ns")
            )
        )
    )
    
    # Production handler with fallback
    temp_file = tempfile.mktemp(suffix='.log')
    production_handler = FallbackHandler([
        QueuedHandler(ManagedFileHandler(temp_file)),  # Primary: async file
        QueuedHandler(console_handler),                # Secondary: console
        BufferHandler()                                # Last resort: memory
    ])
    
    # Root composition
    root_handler = FanoutHandler([
        logging_pipeline,
        metrics_pipeline,
        production_handler
    ])
    
    print("   Tree structure:")
    print("   Root (Fanout)")
    print("   ├── Logging Pipeline (Fanout)")
    print("   │   ├── High Priority Console (Filtered)")
    print("   │   ├── Sampled JSON (Filtered + Sampled)")
    print("   │   └── Logs Buffer (Filtered)")
    print("   ├── Metrics Pipeline (TimeDelta)")
    print("   │   └── Fanout")
    print("   │       ├── Metrics Buffer (Filtered)")
    print("   │       └── Counter Print (Filtered)")
    print("   └── Production Handler (Fallback)")
    print("       ├── Queued File (Primary)")
    print("       ├── Queued Console (Secondary)")
    print("       └── Buffer (Last Resort)")
    
    # Start lifecycle handlers
    root_handler.start()
    
    # Create context
    config = ObservabilityConfig(handlers=[root_handler])
    context = ObservabilityContext(config)
    context.start()
    
    # Test with various events
    print("\n2. Testing with various event types:")
    
    # Create logger
    logger = Logger("composition.test", context, DEBUG)
    
    print("\n   Logging at different levels:")
    logger.debug("Debug message - 10% chance of JSON output")
    logger.info("Info message - 10% chance of JSON output")
    logger.warning("Warning message - no special handling")
    logger.error("Error message - goes to console immediately")
    logger.critical("Critical message - goes to console immediately")
    
    print("\n   Metrics with time deltas:")
    counter = Counter("requests_total", context)
    counter.increment(1.0)
    import time
    time.sleep(0.1)
    counter.increment(2.0)
    time.sleep(0.05)
    counter.increment(3.0)
    
    # Create histogram
    histogram = Histogram("response_time", context, buckets=[0.1, 0.5, 1.0])
    histogram.observe(0.234)
    histogram.observe(0.567)
    
    # Demonstrate routing
    print("\n3. Examining event routing:")
    
    print(f"\n   Logs buffer captured: {len(logs_buffer.get_events())} events")
    print(f"   Metrics buffer captured: {len(metrics_buffer.get_events())} events")
    
    # Advanced composition patterns
    print("\n4. Advanced composition pattern:")
    
    # Per-environment routing
    def create_environment_handler(env_name):
        if env_name == "production":
            return FallbackHandler([
                QueuedHandler(
                    ManagedFileHandler(f"/tmp/{env_name}.log")
                ),
                sampled(0.01, JsonHandler(sys.stderr))  # 1% sampling
            ])
        elif env_name == "staging":
            return FanoutHandler(
                JsonHandler(sys.stdout),
                BufferHandler()
            )
        else:  # development
            return PrintHandler(sys.stdout, include_context=True)
    
    # Dynamic handler selection
    current_env = "staging"  # Could come from config
    env_handler = create_environment_handler(current_env)
    
    print(f"   Created handler for {current_env} environment")
    
    # Category-based routing
    print("\n5. Category-based routing pattern:")
    
    # Different handlers for different categories
    security_handler = filtered(
        lambda e: 'security' in e.get('tags', []),
        FanoutHandler(
            ManagedFileHandler("/tmp/security.log"),
            PrintHandler(sys.stderr, format="[SECURITY] {value}")
        )
    )
    
    performance_handler = filtered(
        lambda e: 'performance' in e.get('tags', []),
        TimeDeltaHandler(
            BufferHandler()
        )
    )
    
    category_router = FanoutHandler(
        security_handler,
        performance_handler,
        BufferHandler()  # Catch-all
    )
    
    config2 = ObservabilityConfig(handlers=[category_router])
    context2 = ObservabilityContext(config2)
    category_router.start()
    context2.start()
    
    # Emit categorized events
    context2.emit("auth.failed", "Invalid password", tags=["security"])
    context2.emit("db.query", "SELECT * FROM users", tags=["performance"])
    context2.emit("app.start", "Application started", tags=["lifecycle"])
    
    # Lambda composition pattern
    print("\n6. Lambda composition for complex filtering:")
    
    # Combine multiple conditions
    complex_filter = lambda e: (
        e['type'].startswith('log.') and
        e.get('level', 0) >= WARNING and
        'user_id' in e and
        e.get('environment') == 'production'
    )
    
    complex_handler = filtered(
        complex_filter,
        QueuedHandler(
            JsonHandler(sys.stderr)
        )
    )
    
    print("   Created handler with complex multi-condition filter")
    
    # Performance optimized composition
    print("\n7. Performance-optimized composition:")
    
    # Fast path for high-frequency events
    fast_path = sampled(
        0.001,  # 0.1% sampling
        BufferHandler()
    )
    
    # Slow path for important events
    slow_path = QueuedHandler(
        FanoutHandler(
            ManagedFileHandler("/tmp/important.log"),
            JsonHandler(sys.stderr)
        )
    )
    
    # Route based on importance
    perf_router = FanoutHandler(
        filtered(lambda e: e.get('importance', 'low') == 'low', fast_path),
        filtered(lambda e: e.get('importance', 'low') != 'low', slow_path)
    )
    
    print("   High-frequency events: 0.1% sampling to buffer")
    print("   Important events: Full processing with persistence")
    
    # Clean up
    print("\n8. Cleaning up complex handler tree:")
    context.stop()
    root_handler.stop()
    context2.stop()
    category_router.stop()
    
    print("   All handlers stopped in correct order")
    
    # Best practices
    print("\n9. Handler composition best practices:")
    print("   - Filter early to reduce processing")
    print("   - Sample high-volume events")
    print("   - Use queues for slow handlers")
    print("   - Add fallbacks for critical paths")
    print("   - Monitor handler performance")
    print("   - Document complex compositions")


if __name__ == '__main__':
    main()