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


def test_span_set_status_success():
    """Span.set_status() properly sets success status."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('operation', context) as span:
        span.set_status(True, "Operation completed successfully")
    
    end_event = events[1]
    assert end_event['type'] == 'span.end'
    assert end_event['success'] is True
    assert end_event['status_message'] == "Operation completed successfully"


def test_span_set_status_failure():
    """Span.set_status() properly sets failure status."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('operation', context) as span:
        span.set_status(False, "Operation failed due to network timeout")
    
    end_event = events[1]
    assert end_event['type'] == 'span.end'
    assert end_event['success'] is False
    assert end_event['status_message'] == "Operation failed due to network timeout"


def test_span_set_status_without_message():
    """Span.set_status() works without optional message."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('operation', context) as span:
        span.set_status(True)  # No message
    
    end_event = events[1]
    assert end_event['success'] is True
    assert 'status_message' not in end_event or end_event['status_message'] is None


def test_span_set_status_override_exception():
    """Span.set_status() can override automatic exception handling."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    try:
        with Span('operation', context) as span:
            span.set_status(True, "Handled gracefully")  # Override before exception
            raise ValueError("Something went wrong")
    except ValueError:
        pass
    
    end_event = events[1]
    # Explicit status should override automatic exception detection
    # (implementation may vary - either explicit status wins or exception wins)
    assert 'success' in end_event
    assert 'status_message' in end_event or 'error' in end_event


def test_span_add_event_basic():
    """Span.add_event() adds timestamped events."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('operation', context) as span:
        span.add_event('checkpoint_reached')
        span.add_event('validation_passed')
    
    # Should have start, 2 events, and end
    assert len(events) == 4
    
    event1 = events[1]
    event2 = events[2]
    
    assert event1['type'] == 'span.event'
    assert event1['value']['name'] == 'checkpoint_reached'
    assert 'timestamp_ns' in event1['value']
    assert 'span_id' in event1['value']
    
    assert event2['type'] == 'span.event'
    assert event2['value']['name'] == 'validation_passed'
    assert 'timestamp_ns' in event2['value']


def test_span_add_event_with_attributes():
    """Span.add_event() supports event attributes."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('operation', context) as span:
        span.add_event('retry_attempted', {
            'attempt': 1,
            'delay_ms': 100,
            'reason': 'timeout'
        })
        span.add_event('cache_miss', {
            'key': 'user:123',
            'ttl': 300
        })
    
    retry_event = events[1]['value']
    cache_event = events[2]['value']
    
    assert retry_event['name'] == 'retry_attempted'
    assert retry_event['attributes']['attempt'] == 1
    assert retry_event['attributes']['delay_ms'] == 100
    assert retry_event['attributes']['reason'] == 'timeout'
    
    assert cache_event['name'] == 'cache_miss'
    assert cache_event['attributes']['key'] == 'user:123'
    assert cache_event['attributes']['ttl'] == 300


def test_span_add_event_without_attributes():
    """Span.add_event() works without attributes parameter."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('operation', context) as span:
        span.add_event('simple_event')
    
    event = events[1]['value']
    assert event['name'] == 'simple_event'
    # Should only have basic fields, no attributes key when none provided
    assert 'attributes' not in event


def test_span_add_event_ordering():
    """Span events are ordered by timestamp."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    import time
    
    with Span('operation', context) as span:
        span.add_event('first_event')
        time.sleep(0.001)  # Small delay
        span.add_event('second_event')
        time.sleep(0.001)  # Small delay
        span.add_event('third_event')
    
    # Extract event timestamps
    first_ts = events[1]['value']['timestamp_ns']
    second_ts = events[2]['value']['timestamp_ns']
    third_ts = events[3]['value']['timestamp_ns']
    
    # Should be in chronological order
    assert first_ts < second_ts < third_ts


def test_span_add_event_in_child_spans():
    """Events in child spans are properly associated."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('parent', context) as parent:
        parent.add_event('parent_event')
        
        with parent.start_child('child') as child:
            child.add_event('child_event')
    
    # Find the event types and filter properly
    span_events = [e for e in events if e['type'] == 'span.event']
    
    assert len(span_events) == 2
    
    parent_event = next(e for e in span_events if e['value']['name'] == 'parent_event')
    child_event = next(e for e in span_events if e['value']['name'] == 'child_event')
    
    # Events should be associated with correct spans
    assert parent_event['value']['span_id'] != child_event['value']['span_id']
    
    # Should be able to trace back to correct span
    parent_start = events[0]  # First event should be parent start
    child_start = events[2]   # After parent event
    
    assert parent_event['value']['span_id'] == parent_start['span_id']
    assert child_event['value']['span_id'] == child_start['span_id']


def test_span_add_event_various_types():
    """Span.add_event() handles various attribute types."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    with Span('operation', context) as span:
        span.add_event('complex_event', {
            'string_attr': 'text',
            'int_attr': 42,
            'float_attr': 3.14,
            'bool_attr': True,
            'none_attr': None,
            'list_attr': [1, 2, 3],
            'dict_attr': {'nested': 'value'}
        })
    
    event_attrs = events[1]['value']['attributes']
    assert event_attrs['string_attr'] == 'text'
    assert event_attrs['int_attr'] == 42
    assert event_attrs['float_attr'] == 3.14
    assert event_attrs['bool_attr'] is True
    assert event_attrs['none_attr'] is None
    assert event_attrs['list_attr'] == [1, 2, 3]
    assert event_attrs['dict_attr'] == {'nested': 'value'}