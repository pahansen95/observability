#!/usr/bin/env python3
"""
Example 45: Handler Filtered

Demonstrates:
- Creating filter predicates
- Using filtered() to wrap handlers
- Lambda predicates checking event fields
- Type filtering
- Severity filtering
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import filtered, PrintHandler, BufferHandler
from observability.domains.logging import Logger, DEBUG, INFO, WARNING, ERROR


def main():
    """Main example logic."""
    print("=== Example 45: Handler Filtered ===\n")
    
    # Create base handlers
    print_handler = PrintHandler(sys.stdout, format="[{type}] {value}")
    buffer_handler = BufferHandler()
    
    # Filter by event type
    print("1. Creating type-based filter")
    
    def is_log_event(event):
        return event['type'].startswith('log.')
    
    log_only_handler = filtered(is_log_event, print_handler)
    
    config = ObservabilityConfig(handlers=[log_only_handler, buffer_handler])
    context = ObservabilityContext(config)
    context.start()
    
    print("\n2. Emitting various event types:")
    context.emit("log.info", "This will print")
    context.emit("metric.gauge", {"name": "cpu", "value": 45.2})
    context.emit("trace.span.start", {"operation": "request"})
    context.emit("log.error", "This will also print")
    
    print("\n   Only log.* events were printed")
    
    # Lambda predicate for severity filtering
    print("\n3. Creating severity-based filter with lambda")
    
    severity_handler = filtered(
        lambda e: e.get('level', 0) >= WARNING,
        PrintHandler(sys.stdout, format="[SEVERE] {value}")
    )
    
    config2 = ObservabilityConfig(handlers=[severity_handler])
    context2 = ObservabilityContext(config2)
    context2.start()
    
    logger = Logger("filter.test", context2, DEBUG)
    
    print("\n4. Logging at different severities:")
    logger.debug("Debug message - won't print")
    logger.info("Info message - won't print")
    logger.warning("Warning message - will print")
    logger.error("Error message - will print")
    
    # Complex filter conditions
    print("\n5. Complex filter with multiple conditions")
    
    def complex_filter(event):
        # Only events with specific fields and values
        return (
            event.get('type', '').startswith('metric.') and
            event.get('value', {}).get('name', '').startswith('api_') and
            event.get('labels', {}).get('environment') == 'production'
        )
    
    metric_prod_handler = filtered(
        complex_filter,
        PrintHandler(sys.stdout, format="[PROD_METRIC] {value}")
    )
    
    config3 = ObservabilityConfig(handlers=[metric_prod_handler, buffer_handler])
    context3 = ObservabilityContext(config3)
    context3.start()
    
    print("\n6. Emitting metrics with different attributes:")
    context3.emit("metric.counter", {"name": "api_requests", "value": 1}, 
                  labels={"environment": "production"})
    context3.emit("metric.counter", {"name": "api_requests", "value": 1}, 
                  labels={"environment": "staging"})
    context3.emit("metric.counter", {"name": "db_queries", "value": 1}, 
                  labels={"environment": "production"})
    
    print("   Only production API metrics were printed")
    
    # Chaining filters
    print("\n7. Chaining multiple filters")
    
    # First filter: only errors
    error_filter = lambda e: e.get('level', 0) >= ERROR
    
    # Second filter: only from specific logger
    logger_filter = lambda e: e.get('logger', '').startswith('app.critical')
    
    chained_handler = filtered(
        logger_filter,
        filtered(
            error_filter,
            PrintHandler(sys.stdout, format="[CRITICAL] {value}")
        )
    )
    
    config4 = ObservabilityConfig(handlers=[chained_handler])
    context4 = ObservabilityContext(config4)
    context4.start()
    
    logger1 = Logger("app.critical.auth", context4, DEBUG)
    logger2 = Logger("app.normal.tasks", context4, DEBUG)
    
    print("\n8. Testing chained filters:")
    logger1.error("Critical auth error - will print")
    logger2.error("Normal task error - won't print")
    logger1.warning("Critical warning - won't print")
    
    # Performance consideration
    print("\n9. Filter performance patterns")
    
    # Efficient: check simple conditions first
    efficient_filter = lambda e: (
        e['type'] == 'log.error' and  # Fast string comparison
        'error_code' in e and         # Fast key check
        e.get('error_code').startswith('CRITICAL_')  # More expensive
    )
    
    # Demonstrate with BufferHandler inspection
    print("\n10. Inspecting filtered results with BufferHandler")
    
    events = buffer_handler.get_events()
    print(f"   Total events captured: {len(events)}")
    
    # Count by type
    type_counts = {}
    for event in events:
        event_type = event['type'].split('.')[0]
        type_counts[event_type] = type_counts.get(event_type, 0) + 1
    
    print("   Events by type:")
    for event_type, count in sorted(type_counts.items()):
        print(f"     {event_type}: {count}")
    
    # Clean up
    context.stop()
    context2.stop()
    context3.stop()
    context4.stop()


if __name__ == '__main__':
    main()