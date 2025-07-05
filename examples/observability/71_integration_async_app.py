#!/usr/bin/env python3
"""
Example 71: Async Application Integration (Simplified)

Demonstrates:
- AsyncIO integration patterns
- Async context propagation
- Concurrent operation tracing
- Async handler patterns
- Task correlation
"""

import sys
import time
import asyncio
from contextlib import asynccontextmanager
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler, BufferHandler, QueuedHandler
from observability.domains.logging import Logger, INFO, WARNING
from observability.domains.tracing import Span
from observability.domains.metrics import Counter, Gauge


async def simple_async_task(name, duration, context):
    """Simple async task with observability."""
    logger = Logger(f"task.{name}", context, INFO)
    
    with Span(f"task_{name}", context) as span:
        logger.info(f"Task {name} started")
        await asyncio.sleep(duration)
        logger.info(f"Task {name} completed")
        return f"{name} done"


async def main_async():
    """Async main function."""
    print("=== Example 71: Async Application Integration (Simplified) ===\n")
    
    # Setup
    buffer = BufferHandler()
    config = ObservabilityConfig(handlers=[
        PrintHandler(sys.stdout, format="{type}: {value}"),
        buffer
    ])
    context = ObservabilityContext(config)
    context.start()
    
    # Example 1: Basic async task tracking
    print("1. Basic async task tracking:")
    
    # Run multiple async tasks concurrently
    results = await asyncio.gather(
        simple_async_task("task1", 0.01, context),
        simple_async_task("task2", 0.02, context),
        simple_async_task("task3", 0.03, context)
    )
    
    print(f"   Results: {results}")
    
    # Example 2: Async context propagation
    print("\n2. Async context propagation:")
    
    async def parent_task(context):
        """Parent task that spawns children."""
        with Span("parent_operation", context) as parent_span:
            logger = Logger("parent", context, INFO)
            logger.info("Parent task started")
            
            # Spawn child tasks
            await asyncio.gather(
                simple_async_task("child1", 0.01, context),
                simple_async_task("child2", 0.01, context)
            )
            
            logger.info("Parent task completed")
    
    await parent_task(context)
    
    # Example 3: Analyze concurrent operations
    print("\n3. Async pattern analysis:")
    
    events = buffer.get_events()
    span_events = [e for e in events if e['type'].startswith('span.')]
    log_events = [e for e in events if e['type'].startswith('log.')]
    
    print(f"   Total spans: {len(span_events) // 2}")  # Divide by 2 for start/end pairs
    print(f"   Total logs: {len(log_events)}")
    
    # Best practices
    print("\n4. Async integration best practices:")
    print("   - Use async-aware handlers for better performance")
    print("   - Propagate context through async tasks")
    print("   - Track task lifecycle and concurrency")
    print("   - Handle errors in async contexts properly")
    
    # Cleanup
    context.stop()


def main():
    """Main entry point."""
    # Run async main
    asyncio.run(main_async())


if __name__ == '__main__':
    main()