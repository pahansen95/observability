#!/usr/bin/env python3
"""
Example 62: Error Handling

Demonstrates:
- Creating failing handlers
- Error isolation between handlers
- Handler recovery patterns
- Context continues despite errors
- Lifecycle error handling
"""

import sys
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import (
    FanoutHandler, FallbackHandler, PrintHandler, 
    BufferHandler, QueuedHandler
)
from observability.domains.logging import Logger, ERROR


class ErrorTracker:
    """Track errors across handlers."""
    def __init__(self):
        self.errors = []
        
    def record(self, handler_name, error):
        self.errors.append({
            'handler': handler_name,
            'error': str(error),
            'type': type(error).__name__
        })


def main():
    """Main example logic."""
    print("=== Example 62: Error Handling ===\n")
    
    error_tracker = ErrorTracker()
    
    # Pattern 1: Handler with intermittent failures
    print("1. Handler with intermittent failures:")
    
    class FlakeyHandler:
        def __init__(self, name, fail_every_n=3):
            self.name = name
            self.fail_every_n = fail_every_n
            self.call_count = 0
            self.success_count = 0
            self.error_count = 0
            
        def __call__(self, event):
            self.call_count += 1
            
            if self.call_count % self.fail_every_n == 0:
                self.error_count += 1
                error = ValueError(f"{self.name}: Simulated failure on call {self.call_count}")
                error_tracker.record(self.name, error)
                raise error
            
            self.success_count += 1
            print(f"[{self.name}] Processed event {self.call_count}")
    
    flakey1 = FlakeyHandler("Flakey1", fail_every_n=3)
    flakey2 = FlakeyHandler("Flakey2", fail_every_n=5)
    reliable = PrintHandler(sys.stdout, format="[RELIABLE] {type}: {value}")
    
    # Use FanoutHandler for isolation
    isolated_fanout = FanoutHandler([flakey1, flakey2, reliable])
    
    config = ObservabilityConfig(handlers=[isolated_fanout])
    context = ObservabilityContext(config)
    context.start()
    
    print("\n   Emitting 10 events to multiple handlers:")
    for i in range(10):
        context.emit("test.event", f"Event {i}")
    
    print(f"\n   Results:")
    print(f"   Flakey1: {flakey1.success_count} success, {flakey1.error_count} errors")
    print(f"   Flakey2: {flakey2.success_count} success, {flakey2.error_count} errors")
    print(f"   Reliable handler processed all events")
    
    context.stop()
    
    # Pattern 2: Recovery with FallbackHandler
    print("\n2. Recovery pattern with FallbackHandler:")
    
    class NetworkHandler:
        def __init__(self, name, available=True):
            self.name = name
            self.available = available
            self.attempts = 0
            
        def __call__(self, event):
            self.attempts += 1
            if not self.available:
                raise ConnectionError(f"{self.name}: Service unavailable")
            print(f"[{self.name}] Sent event successfully")
    
    primary = NetworkHandler("Primary", available=False)
    secondary = NetworkHandler("Secondary", available=False)
    local_buffer = BufferHandler()
    
    recovery_chain = FallbackHandler([primary, secondary, local_buffer])
    
    config2 = ObservabilityConfig(handlers=[recovery_chain])
    context2 = ObservabilityContext(config2)
    context2.start()
    
    print("\n   Emitting events with all network handlers down:")
    logger = Logger("recovery.test", context2, ERROR)
    
    logger.error("Critical error 1")
    logger.error("Critical error 2")
    
    print(f"   Primary attempts: {primary.attempts}")
    print(f"   Secondary attempts: {secondary.attempts}")
    print(f"   Events in buffer: {len(local_buffer.get_events())}")
    
    # Simulate recovery
    print("\n   Secondary service recovers:")
    secondary.available = True
    
    logger.error("Critical error 3")
    
    print(f"   Secondary now handling events")
    print(f"   Total events in buffer: {len(local_buffer.get_events())}")
    
    context2.stop()
    
    # Pattern 3: Error handling in lifecycle
    print("\n3. Lifecycle error handling:")
    
    class LifecycleErrorHandler:
        def __init__(self, name, fail_start=False, fail_stop=False, fail_emit=False):
            self.name = name
            self.fail_start = fail_start
            self.fail_stop = fail_stop
            self.fail_emit = fail_emit
            self.started = False
            
        def start(self):
            print(f"[{self.name}] Starting...")
            if self.fail_start:
                raise RuntimeError(f"{self.name}: Failed to start")
            self.started = True
            print(f"[{self.name}] Started successfully")
            
        def stop(self):
            print(f"[{self.name}] Stopping...")
            if self.fail_stop:
                raise RuntimeError(f"{self.name}: Failed to stop")
            self.started = False
            print(f"[{self.name}] Stopped successfully")
            
        def __call__(self, event):
            if self.fail_emit:
                raise RuntimeError(f"{self.name}: Failed to process event")
            print(f"[{self.name}] Processed event")
    
    # Handler that fails on start
    fail_start = LifecycleErrorHandler("FailStart", fail_start=True)
    # Handler that works
    good_handler = LifecycleErrorHandler("GoodHandler")
    # Handler that fails on stop
    fail_stop = LifecycleErrorHandler("FailStop", fail_stop=True)
    
    handlers = [fail_start, good_handler, fail_stop]
    
    print("\n   Testing lifecycle with errors:")
    
    # Manual lifecycle management to show error handling
    for handler in handlers:
        try:
            handler.start()
        except Exception as e:
            print(f"   ERROR: {e}")
            error_tracker.record(handler.name, e)
    
    # Emit events - only good_handler and fail_stop should process
    print("\n   Emitting event:")
    test_event = {"type": "lifecycle.test", "value": "test"}
    
    for handler in handlers:
        if getattr(handler, 'started', False):
            try:
                handler(test_event)
            except Exception as e:
                print(f"   ERROR: {e}")
                error_tracker.record(handler.name, e)
    
    # Stop all handlers
    print("\n   Stopping handlers:")
    for handler in reversed(handlers):  # Stop in reverse order
        try:
            handler.stop()
        except Exception as e:
            print(f"   ERROR: {e}")
            error_tracker.record(handler.name, e)
    
    # Pattern 4: Error isolation with QueuedHandler
    print("\n4. Error isolation with QueuedHandler:")
    
    class PoisonPillHandler:
        def __init__(self):
            self.processed = 0
            
        def __call__(self, event):
            self.processed += 1
            if event.get('poison', False):
                raise ValueError("Poison pill detected!")
            print(f"   Processed event {self.processed}")
    
    poison_handler = PoisonPillHandler()
    queued = QueuedHandler(poison_handler)
    
    config3 = ObservabilityConfig(handlers=[queued])
    context3 = ObservabilityContext(config3)
    queued.start()
    context3.start()
    
    print("\n   Sending normal and poison events:")
    context3.emit("normal.event", "Event 1")
    context3.emit("poison.event", "Event 2", poison=True)
    context3.emit("normal.event", "Event 3")
    
    import time
    time.sleep(0.1)  # Let queue process
    
    print(f"   Handler processed {poison_handler.processed} events before error")
    
    context3.stop()
    queued.stop()
    
    # Pattern 5: Custom error handling wrapper
    print("\n5. Custom error handling wrapper:")
    
    class ErrorHandlingWrapper:
        def __init__(self, handler, on_error=None):
            self.handler = handler
            self.on_error = on_error or self._default_error_handler
            self.error_count = 0
            
        def _default_error_handler(self, event, error):
            self.error_count += 1
            print(f"   ERROR in handler: {error}")
            error_tracker.record("wrapper", error)
            
        def __call__(self, event):
            try:
                self.handler(event)
            except Exception as e:
                self.on_error(event, e)
                
        def __getattr__(self, name):
            # Delegate lifecycle methods
            return getattr(self.handler, name)
    
    # Wrap a failing handler
    always_fails = lambda e: (_ for _ in ()).throw(RuntimeError("Always fails!"))
    
    wrapped = ErrorHandlingWrapper(
        always_fails,
        on_error=lambda e, err: print(f"   Handled error: {err}")
    )
    
    config4 = ObservabilityConfig(handlers=[wrapped])
    context4 = ObservabilityContext(config4)
    context4.start()
    
    print("\n   Emitting events to wrapped handler:")
    context4.emit("wrapped.test", "Event 1")
    context4.emit("wrapped.test", "Event 2")
    
    print(f"   Total errors handled: {wrapped.error_count}")
    
    context4.stop()
    
    # Summary of errors
    print("\n6. Error summary:")
    print(f"   Total errors recorded: {len(error_tracker.errors)}")
    
    error_types = {}
    for error in error_tracker.errors:
        error_type = error['type']
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    print("\n   Errors by type:")
    for error_type, count in error_types.items():
        print(f"   - {error_type}: {count}")
    
    # Best practices
    print("\n7. Error handling best practices:")
    print("   - Use FanoutHandler for error isolation")
    print("   - Use FallbackHandler for recovery chains")
    print("   - Wrap handlers for custom error handling")
    print("   - Log errors but don't crash the application")
    print("   - Monitor error rates in production")
    print("   - Consider circuit breakers for network handlers")


if __name__ == '__main__':
    main()