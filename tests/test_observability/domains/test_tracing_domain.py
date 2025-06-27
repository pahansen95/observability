"""
Tests for the tracing domain integration.

Validates that the Span class properly tracks execution flow
and emits trace events through the observability context.
"""

import pytest
import time
from observability import ObservabilityContext
from observability.domains.tracing import Span


def test_tracing_domain():
    """Span domain tracks execution flow."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('process_request', context) as span:
        span.set_attribute('user_id', 12345)
        span.set_attribute('endpoint', '/api/users')
    
    assert len(events) == 2
    assert events[0]['type'] == 'span.start'
    assert events[0]['value'] == 'process_request'
    assert 'span_id' in events[0]
    assert events[0]['parent_id'] is None
    
    assert events[1]['type'] == 'span.end'
    assert events[1]['span_id'] == events[0]['span_id']
    assert events[1]['user_id'] == 12345
    assert events[1]['endpoint'] == '/api/users'
    assert 'duration_ns' in events[1]
    assert events[1]['success'] is True


def test_span_with_error():
    """Span captures exception information."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    try:
        with Span('failing_operation', context):
            raise ValueError("Something went wrong")
    except ValueError:
        pass  # Expected
    
    end_event = events[1]
    assert end_event['type'] == 'span.end'
    assert end_event['success'] is False
    assert end_event['error'] == "Something went wrong"


def test_span_parent_child():
    """Spans track parent-child relationships."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('parent', context) as parent_span:
        parent_id = events[0]['span_id']
        
        with parent_span.start_child('child1') as child1:
            child1_id = events[1]['span_id']
            
            with child1.start_child('grandchild'):
                grandchild_id = events[2]['span_id']
    
    # Check parent-child relationships
    assert events[0]['parent_id'] is None  # Parent has no parent
    assert events[1]['parent_id'] == parent_id  # Child1's parent is parent
    assert events[2]['parent_id'] == child1_id  # Grandchild's parent is child1
    
    # All spans should have ended
    assert len(events) == 6  # 3 starts + 3 ends


def test_span_attributes():
    """Span attributes are preserved through lifecycle."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('operation', context, initial_attr='value1') as span:
        span.set_attribute('attr2', 'value2')
        span.set_attribute('attr3', 123)
        span.set_attribute('attr4', {'nested': 'value'})
    
    start_event = events[0]
    end_event = events[1]
    
    # Initial attributes might be in start event
    # (implementation specific)
    
    # All attributes in end event
    assert end_event['initial_attr'] == 'value1'
    assert end_event['attr2'] == 'value2'
    assert end_event['attr3'] == 123
    assert end_event['attr4'] == {'nested': 'value'}


def test_span_duration():
    """Span measures duration accurately."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('timed_operation', context):
        time.sleep(0.01)  # 10ms
    
    end_event = events[1]
    duration_ns = end_event['duration_ns']
    
    # Should be at least 10ms (10_000_000 nanoseconds)
    assert duration_ns >= 10_000_000
    # But less than 20ms (reasonable upper bound)
    assert duration_ns < 20_000_000


def test_span_zero_overhead():
    """Span has zero overhead when no handlers attached."""
    context = ObservabilityContext()
    
    # Should not raise and should be very fast
    start = time.perf_counter_ns()
    for _ in range(1000):
        with Span('fast_op', context):
            pass
    duration = time.perf_counter_ns() - start
    
    # Should be fast (less than 10ms for 1k spans)
    assert duration < 10_000_000


def test_span_context_variables():
    """Span events include context variables."""
    from observability import trace_id, operation_id
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    trace_id.set('trace-123')
    operation_id.set('op-456')
    
    with Span('operation', context):
        pass
    
    for event in events:
        assert event['trace_id'] == 'trace-123'
        assert event['operation_id'] == 'op-456'


def test_span_nested_context_isolation():
    """Nested spans maintain proper context isolation."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('outer', context) as outer:
        outer.set_attribute('level', 'outer')
        
        with outer.start_child('inner') as inner:
            inner.set_attribute('level', 'inner')
            inner.set_attribute('inner_only', True)
    
    # Find end events
    outer_end = next(e for e in events if e['type'] == 'span.end' and e.get('level') == 'outer')
    inner_end = next(e for e in events if e['type'] == 'span.end' and e.get('level') == 'inner')
    
    # Outer should not have inner's attributes
    assert 'inner_only' not in outer_end
    
    # Inner should have its own attributes
    assert inner_end['inner_only'] is True


def test_span_exception_propagation():
    """Exceptions propagate through span context managers."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    class CustomError(Exception):
        pass
    
    with pytest.raises(CustomError):
        with Span('failing', context):
            raise CustomError("Test error")
    
    # Span should still emit end event with error
    end_event = events[1]
    assert end_event['success'] is False
    assert 'Test error' in end_event['error']


def test_span_unique_ids():
    """Each span gets a unique ID."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    span_ids = set()
    
    for i in range(100):
        with Span(f'span_{i}', context):
            pass
    
    # Collect all span IDs
    for event in events:
        if 'span_id' in event:
            span_ids.add(event['span_id'])
    
    # Should have 100 unique IDs
    assert len(span_ids) == 100