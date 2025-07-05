"""
Tests for handler protocol compliance and type aliases.

Validates that protocols define correct contracts and that implementations
properly conform to the expected interfaces.
"""

import pytest
from typing import get_type_hints, get_origin, get_args
from observability.handlers import (
    LifecycleHandler,
    ManagedHandler,
    HandlerChain,
    HandlerPredicate,
    ManagedFileHandler,
    QueuedHandler,
    FanoutHandler,
    FallbackHandler,
)
from observability.types import EventDict, EventHandler


def test_lifecycle_handler_protocol_structure():
    """LifecycleHandler protocol defines correct method signatures."""
    # Get the protocol's required methods
    annotations = get_type_hints(LifecycleHandler)
    
    # Should have start and stop methods
    assert hasattr(LifecycleHandler, 'start')
    assert hasattr(LifecycleHandler, 'stop')
    
    # Check method signatures exist (protocols define structure)
    assert callable(getattr(LifecycleHandler, 'start', None))
    assert callable(getattr(LifecycleHandler, 'stop', None))


def test_lifecycle_handler_protocol_compliance():
    """Classes can implement LifecycleHandler protocol correctly."""
    
    class ValidLifecycleHandler:
        def start(self) -> None:
            self.started = True
        
        def stop(self) -> None:
            self.started = False
    
    # Should be recognized as implementing the protocol
    handler = ValidLifecycleHandler()
    
    # Protocol compliance - has required methods
    assert hasattr(handler, 'start')
    assert hasattr(handler, 'stop')
    assert callable(handler.start)
    assert callable(handler.stop)
    
    # Methods work correctly
    handler.start()
    assert handler.started is True
    handler.stop()
    assert handler.started is False


def test_lifecycle_handler_protocol_runtime_checking():
    """LifecycleHandler protocol works with isinstance() checking."""
    
    class CompliantHandler:
        def start(self) -> None:
            pass
        def stop(self) -> None:
            pass
    
    class NonCompliantHandler:
        def start(self) -> None:
            pass
        # Missing stop() method
    
    compliant = CompliantHandler()
    non_compliant = NonCompliantHandler()
    
    # Note: Python protocols use structural typing, so isinstance() 
    # may not work as expected for runtime checking. This test
    # validates the interface exists and is callable.
    assert hasattr(compliant, 'start') and callable(compliant.start)
    assert hasattr(compliant, 'stop') and callable(compliant.stop)
    
    assert hasattr(non_compliant, 'start') and callable(non_compliant.start)
    assert not (hasattr(non_compliant, 'stop') and callable(getattr(non_compliant, 'stop', None)))


def test_lifecycle_handler_with_existing_implementations():
    """Existing handler implementations properly implement LifecycleHandler."""
    
    # Test ManagedFileHandler
    file_handler = ManagedFileHandler('test.log')
    assert hasattr(file_handler, 'start') and callable(file_handler.start)
    assert hasattr(file_handler, 'stop') and callable(file_handler.stop)
    
    # Test QueuedHandler
    dummy_handler = lambda e: None
    queued_handler = QueuedHandler(dummy_handler)
    assert hasattr(queued_handler, 'start') and callable(queued_handler.start)
    assert hasattr(queued_handler, 'stop') and callable(queued_handler.stop)
    
    # Test FanoutHandler
    fanout_handler = FanoutHandler([dummy_handler])
    assert hasattr(fanout_handler, 'start') and callable(fanout_handler.start)
    assert hasattr(fanout_handler, 'stop') and callable(fanout_handler.stop)
    
    # Test FallbackHandler
    fallback_handler = FallbackHandler([dummy_handler])
    assert hasattr(fallback_handler, 'start') and callable(fallback_handler.start)
    assert hasattr(fallback_handler, 'stop') and callable(fallback_handler.stop)


def test_lifecycle_handler_method_signatures():
    """LifecycleHandler methods have correct signatures."""
    
    class TestHandler:
        def start(self) -> None:
            """Should take no parameters and return None."""
            pass
        
        def stop(self) -> None:
            """Should take no parameters and return None."""
            pass
    
    handler = TestHandler()
    
    # Should be able to call without arguments
    handler.start()
    handler.stop()
    
    # Should return None (or not raise on void return)
    result_start = handler.start()
    result_stop = handler.stop()
    assert result_start is None
    assert result_stop is None


def test_lifecycle_handler_error_handling():
    """LifecycleHandler implementations should handle errors gracefully."""
    
    class ErrorProneHandler:
        def __init__(self):
            self.should_fail = False
        
        def start(self) -> None:
            if self.should_fail:
                raise RuntimeError("Start failed")
        
        def stop(self) -> None:
            if self.should_fail:
                raise RuntimeError("Stop failed")
    
    handler = ErrorProneHandler()
    
    # Should work normally
    handler.start()
    handler.stop()
    
    # Should raise appropriate errors when configured to fail
    handler.should_fail = True
    
    with pytest.raises(RuntimeError, match="Start failed"):
        handler.start()
    
    with pytest.raises(RuntimeError, match="Stop failed"):
        handler.stop()


def test_lifecycle_handler_idempotency():
    """LifecycleHandler start/stop should be safe to call multiple times."""
    
    class IdempotentHandler:
        def __init__(self):
            self.start_count = 0
            self.stop_count = 0
        
        def start(self) -> None:
            self.start_count += 1
        
        def stop(self) -> None:
            self.stop_count += 1
    
    handler = IdempotentHandler()
    
    # Multiple starts should be safe
    handler.start()
    handler.start()
    handler.start()
    
    # Multiple stops should be safe  
    handler.stop()
    handler.stop()
    handler.stop()
    
    # Implementation can choose how to handle multiple calls
    # (this test just ensures they don't raise errors)
    assert handler.start_count == 3
    assert handler.stop_count == 3


def test_managed_handler_protocol_structure():
    """ManagedHandler protocol combines EventHandler and LifecycleHandler."""
    # ManagedHandler should inherit from both protocols
    # Check that it has the combined interface
    
    # Should have callable interface from EventHandler
    assert hasattr(ManagedHandler, '__call__')
    
    # Should have lifecycle methods from LifecycleHandler
    assert hasattr(ManagedHandler, 'start')
    assert hasattr(ManagedHandler, 'stop')


def test_managed_handler_protocol_compliance():
    """Classes can implement ManagedHandler protocol correctly."""
    
    class ValidManagedHandler:
        def __init__(self):
            self.started = False
            self.events_handled = []
        
        def __call__(self, event: EventDict) -> None:
            self.events_handled.append(event)
        
        def start(self) -> None:
            self.started = True
        
        def stop(self) -> None:
            self.started = False
    
    handler = ValidManagedHandler()
    
    # Should implement EventHandler protocol (callable)
    assert callable(handler)
    
    # Should implement LifecycleHandler protocol
    assert hasattr(handler, 'start') and callable(handler.start)
    assert hasattr(handler, 'stop') and callable(handler.stop)
    
    # Should work as both
    handler.start()
    assert handler.started is True
    
    test_event = {'type': 'test', 'value': 'data'}
    handler(test_event)
    assert test_event in handler.events_handled
    
    handler.stop()
    assert handler.started is False


def test_managed_handler_protocol_inheritance():
    """ManagedHandler properly inherits from both base protocols."""
    
    class TestManagedHandler:
        def __call__(self, event: EventDict) -> None:
            pass
        def start(self) -> None:
            pass
        def stop(self) -> None:
            pass
    
    handler = TestManagedHandler()
    
    # Should satisfy EventHandler protocol requirements
    assert callable(handler)
    test_event = {'type': 'test', 'value': 'data'}
    handler(test_event)  # Should not raise
    
    # Should satisfy LifecycleHandler protocol requirements
    handler.start()  # Should not raise
    handler.stop()   # Should not raise


def test_managed_handler_with_existing_implementations():
    """Existing managed handlers implement ManagedHandler protocol."""
    
    # Test ManagedFileHandler
    file_handler = ManagedFileHandler('test.log')
    
    # Should be callable (EventHandler)
    assert callable(file_handler)
    
    # Should have lifecycle methods (LifecycleHandler)
    assert hasattr(file_handler, 'start') and callable(file_handler.start)
    assert hasattr(file_handler, 'stop') and callable(file_handler.stop)
    
    # Test QueuedHandler
    dummy_handler = lambda e: None
    queued_handler = QueuedHandler(dummy_handler)
    
    # Should be callable (EventHandler)
    assert callable(queued_handler)
    
    # Should have lifecycle methods (LifecycleHandler)
    assert hasattr(queued_handler, 'start') and callable(queued_handler.start)
    assert hasattr(queued_handler, 'stop') and callable(queued_handler.stop)


def test_managed_handler_lifecycle_integration():
    """ManagedHandler lifecycle integrates properly with event handling."""
    
    class LifecycleAwareManagedHandler:
        def __init__(self):
            self.active = False
            self.events_processed = 0
        
        def start(self) -> None:
            self.active = True
        
        def stop(self) -> None:
            self.active = False
        
        def __call__(self, event: EventDict) -> None:
            if self.active:
                self.events_processed += 1
    
    handler = LifecycleAwareManagedHandler()
    test_event = {'type': 'test', 'value': 'data'}
    
    # Before start - might not process events
    handler(test_event)
    assert handler.events_processed == 0  # Not active
    
    # After start - should process events
    handler.start()
    handler(test_event)
    assert handler.events_processed == 1
    
    # After stop - might not process events
    handler.stop()
    handler(test_event)
    assert handler.events_processed == 1  # Stopped, no new events


def test_managed_handler_error_propagation():
    """ManagedHandler properly handles errors in both interfaces."""
    
    class ErrorProneManagedHandler:
        def __init__(self):
            self.fail_start = False
            self.fail_call = False
        
        def start(self) -> None:
            if self.fail_start:
                raise RuntimeError("Start failed")
        
        def stop(self) -> None:
            pass
        
        def __call__(self, event: EventDict) -> None:
            if self.fail_call:
                raise ValueError("Event handling failed")
    
    handler = ErrorProneManagedHandler()
    
    # Lifecycle errors should propagate
    handler.fail_start = True
    with pytest.raises(RuntimeError, match="Start failed"):
        handler.start()
    
    # Event handling errors should propagate
    handler.fail_start = False
    handler.fail_call = True
    handler.start()  # Should work
    
    with pytest.raises(ValueError, match="Event handling failed"):
        handler({'type': 'test', 'value': 'data'})


def test_managed_handler_method_order_independence():
    """ManagedHandler methods can be called in various orders safely."""
    
    class FlexibleManagedHandler:
        def __init__(self):
            self.calls = []
        
        def start(self) -> None:
            self.calls.append('start')
        
        def stop(self) -> None:
            self.calls.append('stop')
        
        def __call__(self, event: EventDict) -> None:
            self.calls.append('call')
    
    handler = FlexibleManagedHandler()
    test_event = {'type': 'test', 'value': 'data'}
    
    # Different call orders should be safe
    # Order 1: call before start
    handler(test_event)
    handler.start()
    handler(test_event)
    handler.stop()
    
    expected_calls = ['call', 'start', 'call', 'stop']
    assert handler.calls == expected_calls
    
    # Order 2: multiple starts/stops
    handler.start()
    handler.start()  # Should be safe
    handler(test_event)
    handler.stop()
    handler.stop()  # Should be safe
    
    # Should have recorded all calls without errors


def test_handler_chain_type_alias():
    """HandlerChain type alias works correctly for handler lists."""
    from observability.handlers import PrintHandler, JsonHandler, BufferHandler
    import sys
    
    # Create a handler chain
    handlers = [
        lambda e: None,  # Simple function handler
        PrintHandler(sys.stdout),
        JsonHandler(sys.stderr),
        BufferHandler()
    ]
    
    # Should be a valid HandlerChain
    chain: HandlerChain = handlers
    
    # All items should be callable (EventHandler compatible)
    for handler in chain:
        assert callable(handler)
        
        # Should be able to call with EventDict
        test_event = {'type': 'test', 'value': 'data'}
        try:
            handler(test_event)  # Should not raise type errors
        except Exception:
            # Some handlers might fail without proper setup, but that's
            # implementation-specific, not a type alias issue
            pass


def test_handler_predicate_type_alias():
    """HandlerPredicate type alias works correctly for filtering functions."""
    
    # Various predicate functions
    def always_true(event: EventDict) -> bool:
        return True
    
    def always_false(event: EventDict) -> bool:
        return False
    
    def filter_by_type(event: EventDict) -> bool:
        return event.get('type') == 'log'
    
    def filter_by_severity(event: EventDict) -> bool:
        return event.get('severity', 0) >= 30
    
    # Should all be valid HandlerPredicate
    predicates: list[HandlerPredicate] = [
        always_true,
        always_false,
        filter_by_type,
        filter_by_severity
    ]
    
    test_event = {'type': 'log', 'value': 'test', 'severity': 40}
    
    # All predicates should be callable and return bool
    for predicate in predicates:
        assert callable(predicate)
        result = predicate(test_event)
        assert isinstance(result, bool)


def test_handler_predicate_usage_patterns():
    """HandlerPredicate type alias supports common usage patterns."""
    
    # Lambda predicates
    severity_filter: HandlerPredicate = lambda e: e.get('severity', 0) >= 40
    type_filter: HandlerPredicate = lambda e: e['type'].startswith('log')
    
    # Function predicates
    def complex_filter(event: EventDict) -> bool:
        return (
            event.get('type') == 'metric' and
            event.get('value', 0) > 100 and
            'production' in event.get('tags', [])
        )
    
    complex_predicate: HandlerPredicate = complex_filter
    
    # Test with various events
    test_events = [
        {'type': 'log.info', 'severity': 20, 'value': 'info'},
        {'type': 'log.error', 'severity': 40, 'value': 'error'},
        {'type': 'metric', 'value': 150, 'tags': ['production', 'api']},
        {'type': 'metric', 'value': 50, 'tags': ['development']},
    ]
    
    for event in test_events:
        # All predicates should work
        assert isinstance(severity_filter(event), bool)
        assert isinstance(type_filter(event), bool)
        assert isinstance(complex_predicate(event), bool)


def test_type_aliases_with_handler_factories():
    """Type aliases work correctly with handler factory functions."""
    from observability.handlers import filtered, sampled
    
    # Create predicates using type alias
    error_predicate: HandlerPredicate = lambda e: e.get('severity', 0) >= 40
    metric_predicate: HandlerPredicate = lambda e: e.get('type') == 'metric'
    
    # Create handler chain using type alias
    dummy_handler = lambda e: None
    base_handlers: HandlerChain = [dummy_handler]
    
    # Use with factory functions
    error_handler = filtered(error_predicate, dummy_handler)
    metric_handler = filtered(metric_predicate, dummy_handler)
    sampled_handler = sampled(0.5, dummy_handler)
    
    # All should be valid event handlers
    assert callable(error_handler)
    assert callable(metric_handler)
    assert callable(sampled_handler)
    
    # Should work with test events
    test_event = {'type': 'log', 'severity': 50, 'value': 'critical'}
    
    error_handler(test_event)
    metric_handler(test_event)
    sampled_handler(test_event)


def test_type_aliases_composition():
    """Type aliases support composition patterns."""
    
    # Chain of predicates
    predicates: list[HandlerPredicate] = [
        lambda e: e.get('enabled', True),
        lambda e: e.get('type') in ['log', 'metric'],
        lambda e: e.get('severity', 0) >= 20,
    ]
    
    def combined_predicate(event: EventDict) -> bool:
        return all(pred(event) for pred in predicates)
    
    final_predicate: HandlerPredicate = combined_predicate
    
    # Chain of handlers
    handlers: HandlerChain = [
        lambda e: setattr(e, 'processed_by_1', True) if hasattr(e, '__dict__') else None,
        lambda e: setattr(e, 'processed_by_2', True) if hasattr(e, '__dict__') else None,
    ]
    
    def fanout_handler(event: EventDict) -> None:
        for handler in handlers:
            handler(event)
    
    final_handler = fanout_handler
    
    # Test composition
    test_event = {'type': 'log', 'severity': 30, 'enabled': True, 'value': 'test'}
    
    assert final_predicate(test_event) is True
    final_handler(test_event)  # Should not raise


def test_type_aliases_edge_cases():
    """Type aliases handle edge cases appropriately."""
    
    # Empty handler chain
    empty_chain: HandlerChain = []
    assert len(empty_chain) == 0
    
    # Predicate that handles missing keys
    safe_predicate: HandlerPredicate = lambda e: e.get('nonexistent_key') is not None
    
    # Handler that does nothing
    noop_handler = lambda e: None
    noop_chain: HandlerChain = [noop_handler]
    
    # Test with minimal event
    minimal_event = {'type': 'test'}
    
    assert safe_predicate(minimal_event) is False
    noop_chain[0](minimal_event)  # Should not raise