#!/usr/bin/env python3
"""
Example 75: Timer Proper Usage

Demonstrates:
- Using Timer class with Histogram
- Automatic duration measurement
- Labels with Timer context manager
- Nested timing measurements
- Performance profiling patterns
"""

import sys
import time
import random
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import JsonHandler, BufferHandler
from observability.domains.metrics import Timer, Histogram, DEFAULT_BUCKETS


def simulate_database_query(query_type, table):
    """Simulate database query with variable duration."""
    base_time = {
        "select": 0.01,
        "insert": 0.02,
        "update": 0.025,
        "delete": 0.015
    }.get(query_type, 0.01)
    
    # Add some randomness
    duration = base_time * random.uniform(0.8, 1.5)
    time.sleep(duration)
    
    return f"{query_type.upper()} on {table}: {int(duration * 1000)}ms"


def profile_api_endpoints(context):
    """Profile different API endpoints with timers."""
    # Create histogram for API response times
    api_histogram = Histogram(
        "api_response_time",
        context,
        unit="milliseconds",
        description="API endpoint response times"
    )
    
    # Profile different endpoints
    endpoints = [
        ("GET", "/users", "list"),
        ("GET", "/users/123", "detail"),
        ("POST", "/users", "create"),
        ("PUT", "/users/123", "update"),
        ("DELETE", "/users/123", "delete")
    ]
    
    for method, path, operation in endpoints:
        with Timer(api_histogram, method=method, path=path, operation=operation):
            # Simulate endpoint processing
            print(f"   Processing {method} {path}")
            time.sleep(random.uniform(0.01, 0.05))
            
            # Nested timer for database operations
            db_histogram = Histogram("db_query_time", context)
            with Timer(db_histogram, operation=operation, table="users"):
                simulate_database_query(operation.replace("list", "select"), "users")


def measure_batch_processing(context):
    """Measure batch processing with detailed timing."""
    batch_histogram = Histogram(
        "batch_processing_time",
        context,
        buckets=[10, 25, 50, 100, 250, 500, 1000],  # milliseconds
        unit="milliseconds"
    )
    
    # Process batches of different sizes
    batch_sizes = [10, 50, 100, 500]
    
    for size in batch_sizes:
        with Timer(batch_histogram, batch_size=size, processor="async"):
            print(f"   Processing batch of {size} items")
            
            # Simulate per-item processing
            item_histogram = Histogram("item_processing_time", context)
            for i in range(min(size, 10)):  # Sample first 10
                with Timer(item_histogram, item_index=i, batch_size=size):
                    time.sleep(0.001)  # 1ms per item
            
            # Simulate batch overhead
            time.sleep(0.01)


def demonstrate_error_handling(context):
    """Show timer behavior with exceptions."""
    operation_histogram = Histogram("operation_duration", context)
    
    # Successful operation
    try:
        with Timer(operation_histogram, status="success", operation="normal"):
            time.sleep(0.02)
            print("   Normal operation completed")
    except Exception:
        pass
    
    # Failed operation - timer still records duration
    try:
        with Timer(operation_histogram, status="error", operation="failing"):
            time.sleep(0.01)
            raise ValueError("Simulated error")
    except ValueError:
        print("   Failed operation (duration still recorded)")
    
    # Operation with cleanup
    try:
        with Timer(operation_histogram, status="partial", operation="cleanup"):
            time.sleep(0.005)
            try:
                raise RuntimeError("Error during processing")
            finally:
                # Cleanup code
                time.sleep(0.005)
                print("   Cleanup performed")
    except RuntimeError:
        pass


def analyze_timing_patterns(buffer):
    """Analyze timing patterns from captured metrics."""
    events = buffer.get_events()
    
    # Filter histogram observations
    observations = [
        e for e in events 
        if e['type'] == 'metric.histogram' and 'observation' in e.get('name', '')
    ]
    
    # Group by metric name
    metrics_summary = {}
    for obs in observations:
        metric_name = obs['value']['name']
        value = obs['value']['observation']
        
        if metric_name not in metrics_summary:
            metrics_summary[metric_name] = {
                'count': 0,
                'sum': 0,
                'min': float('inf'),
                'max': 0
            }
        
        summary = metrics_summary[metric_name]
        summary['count'] += 1
        summary['sum'] += value
        summary['min'] = min(summary['min'], value)
        summary['max'] = max(summary['max'], value)
    
    print("\n   Timing Summary:")
    for metric, summary in sorted(metrics_summary.items()):
        if summary['count'] > 0:
            avg = summary['sum'] / summary['count']
            print(f"     {metric}:")
            print(f"       Count: {summary['count']}")
            print(f"       Average: {avg:.2f}ms")
            print(f"       Min: {summary['min']:.2f}ms")
            print(f"       Max: {summary['max']:.2f}ms")


def main():
    """Main example logic."""
    print("=== Example 75: Timer Proper Usage ===\n")
    
    # Setup
    buffer = BufferHandler()
    config = ObservabilityConfig(handlers=[
        JsonHandler(sys.stdout, indent=2, sort_keys=True),
        buffer
    ])
    context = ObservabilityContext(config)
    context.start()
    
    # Example 1: Basic timer usage
    print("1. Basic timer usage with histogram:")
    
    operation_histogram = Histogram(
        "operation_duration",
        context,
        buckets=DEFAULT_BUCKETS,
        unit="milliseconds",
        description="Various operation durations"
    )
    
    # Simple timing
    with Timer(operation_histogram, operation="database_query", table="users"):
        result = simulate_database_query("select", "users")
        print(f"   {result}")
    
    # Example 2: Timer with multiple labels
    print("\n2. Timer with multiple labels:")
    
    with Timer(operation_histogram, 
               operation="complex_calculation",
               algorithm="recursive",
               input_size="large",
               cache_enabled=True):
        print("   Performing complex calculation...")
        time.sleep(0.03)
    
    # Example 3: API endpoint profiling
    print("\n3. Profiling API endpoints:")
    profile_api_endpoints(context)
    
    # Example 4: Batch processing measurement
    print("\n4. Batch processing with nested timers:")
    measure_batch_processing(context)
    
    # Example 5: Error handling with timers
    print("\n5. Timer behavior with exceptions:")
    demonstrate_error_handling(context)
    
    # Example 6: Analyze timing data
    print("\n6. Analyzing captured timing data:")
    analyze_timing_patterns(buffer)
    
    # Best practices
    print("\n7. Timer best practices:")
    print("   - Use descriptive histogram names and units")
    print("   - Add relevant labels for grouping and filtering")
    print("   - Choose appropriate bucket boundaries")
    print("   - Timer records duration even if exception occurs")
    print("   - Nest timers for detailed performance breakdowns")
    print("   - Consider overhead for very fast operations")
    
    context.stop()


if __name__ == '__main__':
    main()