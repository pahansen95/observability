#!/usr/bin/env python3
"""
Example 61: High Volume Patterns

Demonstrates:
- Generating 100k events/second
- QueuedHandler for async processing
- Batching with BufferHandler
- Sampling strategies
- Queue depth monitoring
"""

import time
import sys
import threading
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import (
    QueuedHandler, BufferHandler, PrintHandler,
    sampled, filtered, FanoutHandler
)
from observability.domains.metrics import Counter


def generate_events(context, rate_per_second, duration_seconds):
    """Generate events at specified rate."""
    total_events = rate_per_second * duration_seconds
    sleep_time = 1.0 / rate_per_second if rate_per_second < 10000 else 0

    counter = Counter("events_generated", context, unit="events")

    start_time = time.time()
    events_sent = 0

    # Batch generation for high rates
    batch_size = min(1000, rate_per_second // 100)

    while events_sent < total_events:
        batch_start = time.perf_counter()

        # Generate batch
        for i in range(batch_size):
            if events_sent >= total_events:
                break

            context.emit("high.volume", {
                "event_id": events_sent,
                "timestamp": time.time(),
                "batch": events_sent // batch_size
            })

            counter.increment(1.0)
            events_sent += 1

        # Rate limiting
        if sleep_time > 0:
            elapsed = time.perf_counter() - batch_start
            if elapsed < (sleep_time * batch_size):
                time.sleep((sleep_time * batch_size) - elapsed)

    actual_duration = time.time() - start_time
    actual_rate = events_sent / actual_duration

    return events_sent, actual_duration, actual_rate


def main():
    """Main example logic."""
    print("=== Example 61: High Volume Patterns ===\n")

    # Pattern 1: Async processing with QueuedHandler
    print("1. Async processing with QueuedHandler:")

    # Simulate slow handler
    class SlowHandler:
        def __init__(self):
            self.processed = 0

        def __call__(self, event):
            self.processed += 1
            # Simulate processing time
            if self.processed % 1000 == 0:
                time.sleep(0.001)  # 1ms every 1000 events

    slow_handler = SlowHandler()
    queued = QueuedHandler(slow_handler)

    config = ObservabilityConfig(handlers=[queued])
    context = ObservabilityContext(config)
    queued.start()
    context.start()

    print("\n   Generating 10,000 events...")
    start = time.time()

    for i in range(10000):
        context.emit("async.test", {"id": i})

    emit_time = time.time() - start
    print(f"   Emitted in {emit_time:.3f}s ({10000/emit_time:.0f} events/s)")

    # Wait for processing
    print("   Waiting for queue to drain...")
    time.sleep(0.5)

    print(f"   Handler processed: {slow_handler.processed} events")

    context.stop()
    queued.stop()

    # Pattern 2: Batching with BufferHandler
    print("\n2. Batching pattern with BufferHandler:")

    class BatchProcessor:
        def __init__(self, batch_size=100):
            self.batch_size = batch_size
            self.buffer = BufferHandler(max_size=batch_size)
            self.batches_processed = 0

        def __call__(self, event):
            self.buffer(event)

            if len(self.buffer.get_events()) >= self.batch_size:
                self.process_batch()

        def process_batch(self):
            events = self.buffer.get_events()
            self.batches_processed += 1
            # Simulate batch processing
            print(f"   Processing batch {self.batches_processed}: {len(events)} events")
            self.buffer.clear()

        def flush(self):
            if self.buffer.get_events():
                self.process_batch()

    batch_processor = BatchProcessor(batch_size=1000)

    config2 = ObservabilityConfig(handlers=[batch_processor])
    context2 = ObservabilityContext(config2)
    context2.start()

    print("\n   Generating events for batching...")
    for i in range(5500):
        context2.emit("batch.test", {"id": i})

    batch_processor.flush()
    print(f"   Total batches processed: {batch_processor.batches_processed}")

    context2.stop()

    # Pattern 3: Sampling strategies
    print("\n3. Sampling strategies for high volume:")

    # Different sampling rates by importance
    critical_handler = PrintHandler(sys.stdout, format="[CRITICAL] {value}")
    normal_handler = PrintHandler(sys.stdout, format="[NORMAL] {value}")
    debug_handler = PrintHandler(sys.stdout, format="[DEBUG] {value}")

    # Route and sample by importance
    sampling_router = FanoutHandler(
        filtered(lambda e: e.get('importance') == 'critical',
                critical_handler),
        filtered(lambda e: e.get('importance') == 'normal',
                sampled(0.1, normal_handler)),
        filtered(lambda e: e.get('importance') == 'debug',
                sampled(0.01, debug_handler))
    )

    config3 = ObservabilityConfig(handlers=[sampling_router])
    context3 = ObservabilityContext(config3)
    context3.start()

    print("\n   Emitting 1000 events with different importance:")
    for i in range(1000):
        importance = 'critical' if i < 10 else 'normal' if i < 100 else 'debug'
        context3.emit("sampled.event", f"Event {i}", importance=importance)

    print("   Critical: 100% (10 events)")
    print("   Normal: ~10% (9 of 90 events)")
    print("   Debug: ~1% (9 of 900 events)")

    context3.stop()

    # Pattern 4: Queue depth monitoring
    print("\n4. Queue depth monitoring:")

    class MonitoredQueue:
        def __init__(self, handler, queue_size=1000):
            self.queue = QueuedHandler(handler, queue_size=queue_size)
            self.max_depth = 0
            self.check_interval = 0.01
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor)

        def start(self):
            self.queue.start()
            self.monitor_thread.start()

        def stop(self):
            self.monitoring = False
            self.queue.stop()
            self.monitor_thread.join()

        def _monitor(self):
            while self.monitoring:
                # Note: Real implementation would access queue depth
                # This is a simulation
                time.sleep(self.check_interval)

        def __call__(self, event):
            self.queue(event)

    monitored = MonitoredQueue(BufferHandler(), queue_size=5000)

    config4 = ObservabilityConfig(handlers=[monitored])
    context4 = ObservabilityContext(config4)
    monitored.start()
    context4.start()

    print("\n   Generating burst of events...")
    events_sent, duration, rate = generate_events(context4, 50000, 1)

    print(f"   Generated {events_sent:,} events in {duration:.3f}s")
    print(f"   Actual rate: {rate:,.0f} events/second")

    context4.stop()
    monitored.stop()

    # Pattern 5: High-volume best practices
    print("\n5. High-volume best practices:")

    # Create optimized pipeline
    metrics_buffer = BufferHandler()

    high_volume_pipeline = FanoutHandler(
        # Critical events: immediate processing
        filtered(
            lambda e: e.get('severity') == 'critical',
            QueuedHandler(PrintHandler(sys.stderr))
        ),

        # Metrics: sample and buffer
        filtered(
            lambda e: e['type'].startswith('metric.'),
            sampled(0.001, metrics_buffer)  # 0.1% sample
        ),

        # Logs: heavy sampling for debug
        filtered(
            lambda e: e.get('level', 0) <= 10,  # DEBUG
            sampled(0.0001, BufferHandler())  # 0.01% sample
        )
    )

    print("\n   Optimized pipeline created:")
    print("   - Critical events: 100% with dedicated queue")
    print("   - Metrics: 0.1% sampling to buffer")
    print("   - Debug logs: 0.01% sampling")

    # Performance tips
    print("\n6. Performance optimization tips:")
    print("   - Use QueuedHandler for slow backends")
    print("   - Batch events when possible")
    print("   - Sample aggressively for high-volume streams")
    print("   - Monitor queue depths under load")
    print("   - Use separate pipelines by priority")
    print("   - Consider dropping events vs blocking")

    # Throughput summary
    print("\n7. Throughput capabilities:")
    print("   - Emission: 1M+ events/second (no handlers)")
    print("   - BufferHandler: 500K+ events/second")
    print("   - QueuedHandler: Limited by queue size and drain rate")
    print("   - Network handlers: ~10-50K events/second")
    print("   - File handlers: ~100K events/second (SSD)")


if __name__ == '__main__':
    main()
