#!/usr/bin/env python3
"""
Example 64: Debugging Observability

Demonstrates:
- Using BufferHandler to debug itself
- Handler pipeline inspection
- Event flow tracing
- Adding debug handlers dynamically
- Self-inspection patterns
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import (
    BufferHandler, PrintHandler, FanoutHandler,
    filtered, sampled, TimeDeltaHandler
)
from observability.domains.logging import Logger, DEBUG, INFO


class DebugHandler:
    """Handler that logs its own activity."""
    def __init__(self, name, wrapped_handler=None):
        self.name = name
        self.wrapped_handler = wrapped_handler
        self.call_count = 0
        self.last_event = None
        
    def __call__(self, event):
        self.call_count += 1
        self.last_event = event
        
        # Log our own activity
        print(f"[DEBUG-{self.name}] Processing event #{self.call_count}")
        print(f"  Type: {event['type']}")
        print(f"  Value: {event.get('value', 'N/A')}")
        
        # Pass to wrapped handler if any
        if self.wrapped_handler:
            self.wrapped_handler(event)
            
    def get_stats(self):
        return {
            'name': self.name,
            'calls': self.call_count,
            'last_event_type': self.last_event['type'] if self.last_event else None
        }


def create_observable_pipeline():
    """Create a pipeline that can observe itself."""
    # Level 1: Base handlers
    buffer1 = BufferHandler()
    buffer2 = BufferHandler()
    
    # Level 2: Add debug wrappers
    debug1 = DebugHandler("Filter", buffer1)
    debug2 = DebugHandler("Sample", buffer2)
    
    # Level 3: Add control handlers
    filtered_handler = filtered(lambda e: e.get('important', False), debug1)
    sampled_handler = sampled(0.5, debug2, seed=42)
    
    # Level 4: Combine
    pipeline = FanoutHandler(filtered_handler, sampled_handler)
    
    return pipeline, {'buffer1': buffer1, 'buffer2': buffer2, 
                     'debug1': debug1, 'debug2': debug2}


def main():
    """Main example logic."""
    print("=== Example 64: Debugging Observability ===\n")
    
    # Pattern 1: Handler pipeline inspection
    print("1. Inspecting handler pipeline:")
    
    pipeline, components = create_observable_pipeline()
    
    config = ObservabilityConfig(handlers=[pipeline])
    context = ObservabilityContext(config)
    context.start()
    
    # Emit test events
    print("\n2. Emitting test events through pipeline:")
    for i in range(6):
        important = i % 2 == 0
        context.emit("debug.test", f"Event {i}", important=important)
    
    # Inspect results
    print("\n3. Pipeline inspection results:")
    print(f"   Debug1 (Filter) stats: {components['debug1'].get_stats()}")
    print(f"   Debug2 (Sample) stats: {components['debug2'].get_stats()}")
    print(f"   Buffer1 events: {len(components['buffer1'].get_events())}")
    print(f"   Buffer2 events: {len(components['buffer2'].get_events())}")
    
    context.stop()
    
    # Pattern 2: Event flow tracing
    print("\n4. Event flow tracing:")
    
    class FlowTracer:
        """Traces event flow through handlers."""
        def __init__(self):
            self.trace = []
            
        def create_tracer(self, name):
            def tracer(event):
                self.trace.append({
                    'handler': name,
                    'event_type': event['type'],
                    'timestamp': event['timestamp_ns']
                })
            return tracer
            
        def print_flow(self):
            print("   Event flow trace:")
            for entry in self.trace:
                print(f"   -> {entry['handler']}: {entry['event_type']}")
    
    flow_tracer = FlowTracer()
    
    # Create traced pipeline
    traced_pipeline = FanoutHandler([
        flow_tracer.create_tracer("Handler1"),
        flow_tracer.create_tracer("Handler2"),
        FanoutHandler([
            flow_tracer.create_tracer("Handler3.1"),
            flow_tracer.create_tracer("Handler3.2")
        ])
    ])
    
    config2 = ObservabilityConfig(handlers=[traced_pipeline])
    context2 = ObservabilityContext(config2)
    context2.start()
    
    context2.emit("trace.test", "Traced event")
    flow_tracer.print_flow()
    
    context2.stop()
    
    # Pattern 3: Dynamic debug handler injection
    print("\n5. Dynamic debug handler injection:")
    
    # Start with normal pipeline
    normal_buffer = BufferHandler()
    config3 = ObservabilityConfig(handlers=[normal_buffer])
    context3 = ObservabilityContext(config3)
    context3.start()
    
    # Emit some events
    logger = Logger("app", context3, INFO)
    logger.info("Normal operation")
    
    print(f"   Events before debug: {len(normal_buffer.get_events())}")
    
    # Inject debug handler
    print("\n   Injecting debug handler...")
    debug_handler = DebugHandler("Injected")
    context3.attach_handler(debug_handler)
    
    # Continue operation
    logger.info("With debug handler")
    logger.warning("Something interesting")
    
    print(f"\n   Debug handler saw {debug_handler.call_count} events after injection")
    
    context3.stop()
    
    # Pattern 4: Self-inspecting handlers
    print("\n6. Self-inspecting handlers:")
    
    class IntrospectiveHandler:
        """Handler that reports on its own behavior."""
        def __init__(self):
            self.events_by_type = {}
            self.total_bytes = 0
            self.processing_times = []
            
        def __call__(self, event):
            import time
            start = time.perf_counter_ns()
            
            # Track event types
            event_type = event['type']
            self.events_by_type[event_type] = self.events_by_type.get(event_type, 0) + 1
            
            # Track data size (rough estimate)
            self.total_bytes += len(str(event))
            
            # Simulate processing
            time.sleep(0.0001)  # 0.1ms
            
            # Track processing time
            elapsed = time.perf_counter_ns() - start
            self.processing_times.append(elapsed)
            
        def report(self):
            print("\n   Introspection Report:")
            print(f"   Total events: {sum(self.events_by_type.values())}")
            print(f"   Event types: {len(self.events_by_type)}")
            print(f"   Total data: ~{self.total_bytes} bytes")
            
            if self.processing_times:
                avg_time = sum(self.processing_times) / len(self.processing_times)
                print(f"   Avg processing: {avg_time/1e6:.2f}ms")
            
            print("\n   Events by type:")
            for event_type, count in sorted(self.events_by_type.items()):
                print(f"     {event_type}: {count}")
    
    introspective = IntrospectiveHandler()
    
    config4 = ObservabilityConfig(handlers=[introspective])
    context4 = ObservabilityContext(config4)
    context4.start()
    
    # Generate various events
    logger2 = Logger("introspect", context4, DEBUG)
    
    for i in range(10):
        logger2.debug(f"Debug {i}")
        logger2.info(f"Info {i}")
        if i % 3 == 0:
            logger2.warning(f"Warning {i}")
    
    from observability.domains.metrics import Counter
    counter = Counter("test_counter", context4)
    for i in range(5):
        counter.increment(1.0)
    
    introspective.report()
    
    context4.stop()
    
    # Pattern 5: Debug buffer analysis
    print("\n7. Debug buffer analysis:")
    
    analysis_buffer = BufferHandler()
    config5 = ObservabilityConfig(handlers=[
        TimeDeltaHandler(analysis_buffer)  # Add time deltas
    ])
    context5 = ObservabilityContext(config5)
    context5.start()
    
    # Generate burst pattern
    import time
    for i in range(3):
        for j in range(5):
            context5.emit("burst.event", f"Burst {i}-{j}")
        time.sleep(0.1)  # Pause between bursts
    
    # Analyze patterns
    events = analysis_buffer.get_events()
    print(f"\n   Captured {len(events)} events")
    
    # Find bursts by time delta
    bursts = []
    current_burst = []
    
    for event in events:
        delta_ns = event.get('time_delta_ns', 0)
        if delta_ns > 50_000_000:  # 50ms gap
            if current_burst:
                bursts.append(current_burst)
            current_burst = [event]
        else:
            current_burst.append(event)
    
    if current_burst:
        bursts.append(current_burst)
    
    print(f"   Detected {len(bursts)} bursts:")
    for i, burst in enumerate(bursts):
        print(f"     Burst {i+1}: {len(burst)} events")
    
    context5.stop()
    
    # Best practices
    print("\n8. Debugging observability best practices:")
    print("   - Use debug wrappers to trace flow")
    print("   - Inject handlers dynamically for troubleshooting")
    print("   - Create self-reporting handlers")
    print("   - Analyze buffer contents for patterns")
    print("   - Add time deltas for timing analysis")
    print("   - Use deterministic sampling for reproducibility")


if __name__ == '__main__':
    main()