#!/usr/bin/env python3
"""
Example 76: Handler Protocols

Demonstrates:
- Implementing EventHandler protocol
- Implementing ManagedHandler protocol
- Custom handler lifecycle management
- Handler state management
- Protocol compliance patterns
"""

import sys
import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler
from observability.types import EventDict, EventHandler


class MetricsAccumulator:
    """Custom handler that implements EventHandler protocol."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
    
    def __call__(self, event: EventDict) -> None:
        """Process metric events by accumulating values."""
        if event['type'].startswith('metric.'):
            metric_name = event.get('value', {}).get('name', 'unknown')
            measurement = event.get('measurement', 0)
            
            with self.lock:
                if metric_name not in self.metrics:
                    self.metrics[metric_name] = []
                self.metrics[metric_name].append(measurement)
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all metrics."""
        summary = {}
        
        with self.lock:
            for name, values in self.metrics.items():
                if values:
                    summary[name] = {
                        'count': len(values),
                        'sum': sum(values),
                        'mean': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
        
        return summary


class RateLimitingHandler:
    """Handler that implements rate limiting."""
    
    def __init__(self, wrapped_handler: EventHandler, max_events_per_second: int = 100):
        self.wrapped_handler = wrapped_handler
        self.max_events_per_second = max_events_per_second
        self.min_interval = 1.0 / max_events_per_second
        self.last_event_time = 0
        self.lock = threading.Lock()
        self.dropped_count = 0
    
    def __call__(self, event: EventDict) -> None:
        """Process event with rate limiting."""
        current_time = time.time()
        
        with self.lock:
            time_since_last = current_time - self.last_event_time
            
            if time_since_last >= self.min_interval:
                self.last_event_time = current_time
                self.wrapped_handler(event)
            else:
                self.dropped_count += 1
    
    def get_stats(self) -> Dict[str, int]:
        """Get rate limiting statistics."""
        with self.lock:
            return {
                'dropped_events': self.dropped_count,
                'max_events_per_second': self.max_events_per_second
            }


class BatchingHandler:
    """Handler implementing ManagedHandler protocol with batching."""
    
    def __init__(self, wrapped_handler: EventHandler, batch_size: int = 100, 
                 flush_interval: float = 1.0):
        self.wrapped_handler = wrapped_handler
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch: List[EventDict] = []
        self.lock = threading.Lock()
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.stats = {
            'batches_sent': 0,
            'events_processed': 0
        }
    
    def __call__(self, event: EventDict) -> None:
        """Add event to batch."""
        with self.lock:
            self.batch.append(event)
            
            if len(self.batch) >= self.batch_size:
                self._flush_batch()
    
    def start(self) -> None:
        """Start background worker for periodic flushing."""
        self.stop_event.clear()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        print(f"   BatchingHandler started (batch_size={self.batch_size})")
    
    def stop(self) -> None:
        """Stop worker and flush remaining events."""
        print("   BatchingHandler stopping...")
        self.stop_event.set()
        
        if self.worker_thread:
            self.worker_thread.join(timeout=0.2)
        
        # Final flush
        with self.lock:
            if self.batch:
                self._flush_batch()
        
        print(f"   BatchingHandler stopped (processed {self.stats['events_processed']} events)")
    
    def _worker(self) -> None:
        """Background worker for periodic flushing."""
        while not self.stop_event.is_set():
            time.sleep(self.flush_interval)
            
            with self.lock:
                if self.batch:
                    self._flush_batch()
    
    def _flush_batch(self) -> None:
        """Flush current batch to wrapped handler."""
        if not self.batch:
            return
        
        # Create batch event
        batch_event = {
            'type': 'batch',
            'timestamp': time.time(),
            'timestamp_ns': time.time_ns(),
            'value': {
                'events': self.batch,
                'batch_size': len(self.batch)
            }
        }
        
        # Send to wrapped handler
        self.wrapped_handler(batch_event)
        
        # Update stats
        self.stats['batches_sent'] += 1
        self.stats['events_processed'] += len(self.batch)
        
        # Clear batch
        self.batch = []


class CircuitBreakerHandler:
    """Handler with circuit breaker pattern for failure protection."""
    
    def __init__(self, wrapped_handler: EventHandler, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 0.5):
        self.wrapped_handler = wrapped_handler
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_opened_at: Optional[float] = None
        self.lock = threading.Lock()
        self.stats = {
            'total_events': 0,
            'failed_events': 0,
            'circuit_opens': 0
        }
    
    def __call__(self, event: EventDict) -> None:
        """Process event with circuit breaker protection."""
        with self.lock:
            self.stats['total_events'] += 1
            
            # Check if circuit should be reset
            if self.circuit_open and self.circuit_opened_at:
                if time.time() - self.circuit_opened_at > self.recovery_timeout:
                    self.circuit_open = False
                    self.failure_count = 0
                    print("   Circuit breaker reset")
            
            # If circuit is open, drop event
            if self.circuit_open:
                return
            
            # Try to process event
            try:
                self.wrapped_handler(event)
                # Reset failure count on success
                self.failure_count = 0
            except Exception as e:
                self.failure_count += 1
                self.stats['failed_events'] += 1
                
                if self.failure_count >= self.failure_threshold:
                    self.circuit_open = True
                    self.circuit_opened_at = time.time()
                    self.stats['circuit_opens'] += 1
                    print(f"   Circuit breaker opened after {self.failure_count} failures")


def demonstrate_custom_handlers(context):
    """Demonstrate various custom handler implementations."""
    # Test MetricsAccumulator
    print("\n2. Testing MetricsAccumulator:")
    accumulator = MetricsAccumulator()
    
    # Emit some metrics
    for i in range(10):
        context.emit("metric.counter", {"name": "requests", "value": 1}, measurement=1)
        context.emit("metric.gauge", {"name": "cpu_usage", "value": 40 + i}, measurement=40 + i)
    
    # Get summary
    summary = accumulator.get_summary()
    print("   Metrics summary:")
    for name, stats in summary.items():
        print(f"     {name}: mean={stats['mean']:.1f}, min={stats['min']}, max={stats['max']}")
    
    # Test RateLimitingHandler
    print("\n3. Testing RateLimitingHandler:")
    print_handler = PrintHandler(sys.stdout, format="[RATE_LIMITED] {value}")
    rate_limiter = RateLimitingHandler(print_handler, max_events_per_second=5)
    
    # Emit events rapidly
    for i in range(10):
        rate_limiter({'type': 'test', 'value': f'Event {i}', 'timestamp': time.time(), 'timestamp_ns': time.time_ns()})
        time.sleep(0.01)  # 100 events per second attempt
    
    stats = rate_limiter.get_stats()
    print(f"   Rate limiting stats: {stats}")


def main():
    """Main example logic."""
    print("=== Example 76: Handler Protocols ===\n")
    
    # Example 1: ManagedHandler implementation
    print("1. BatchingHandler implementing ManagedHandler protocol:")
    
    # Create handler that will receive batches
    batch_receiver = PrintHandler(sys.stdout, format="[BATCH] {value}")
    batching_handler = BatchingHandler(batch_receiver, batch_size=5, flush_interval=0.1)
    
    config = ObservabilityConfig(handlers=[batching_handler])
    context = ObservabilityContext(config)
    
    # Start lifecycle
    context.start()  # This calls batching_handler.start()
    
    # Emit events
    for i in range(12):
        context.emit("test.event", f"Event {i}")
        time.sleep(0.01)
    
    # Stop lifecycle
    context.stop()  # This calls batching_handler.stop()
    
    print(f"   Final stats: {batching_handler.stats}")
    
    # Example 2-3: Custom handlers
    demonstrate_custom_handlers(context)
    
    # Example 4: Circuit breaker pattern
    print("\n4. Testing CircuitBreakerHandler:")
    
    # Create failing handler
    class FailingHandler:
        def __init__(self, fail_rate=0.5):
            self.fail_rate = fail_rate
            
        def __call__(self, event):
            if time.time() % 1 < self.fail_rate:
                raise RuntimeError("Handler failure")
            print(f"   [SUCCESS] {event['value']}")
    
    failing_handler = FailingHandler(fail_rate=0.7)
    circuit_breaker = CircuitBreakerHandler(failing_handler, failure_threshold=3)
    
    # Test circuit breaker
    for i in range(10):
        event = {
            'type': 'test',
            'value': f'Event {i}',
            'timestamp': time.time(),
            'timestamp_ns': time.time_ns()
        }
        circuit_breaker(event)
        time.sleep(0.01)
    
    print(f"   Circuit breaker stats: {circuit_breaker.stats}")
    
    # Best practices
    print("\n5. Handler protocol best practices:")
    print("   - Implement __call__(event: EventDict) -> None for EventHandler")
    print("   - Add start() and stop() methods for ManagedHandler")
    print("   - Ensure thread safety for concurrent access")
    print("   - Handle exceptions gracefully")
    print("   - Consider implementing statistics/monitoring")
    print("   - Use composition to extend existing handlers")


if __name__ == '__main__':
    main()