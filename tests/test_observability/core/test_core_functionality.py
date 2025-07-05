"""
Core functionality tests for observability package.

Tests basic event emission, context variable propagation, and handler lifecycle
management according to the behavioral test plan.
"""

import pytest
import time
from observability import (
    ObservabilityContext,
    ObservabilityConfig,
    trace_id,
    request_id,
    operation_id,
)


def test_basic_event_emission():
    """Events flow from context to handlers."""
    received = []

    context = ObservabilityContext()
    context.attach_handler(lambda e: received.append(e))

    context.emit('test.event', 'hello', custom='metadata')

    assert len(received) == 1
    assert received[0]['type'] == 'test.event'
    assert received[0]['value'] == 'hello'
    assert received[0]['custom'] == 'metadata'
    assert 'timestamp_ns' in received[0]


def test_zero_overhead_when_no_handlers():
    """No overhead when no handlers are attached."""
    context = ObservabilityContext()

    # Should not raise any errors and should be very fast
    start = time.perf_counter_ns()
    for _ in range(10000):
        context.emit('test.event', 'value')
    duration = time.perf_counter_ns() - start

    # Should be fast (less than 10ms for 10k emissions)
    assert duration < 10_000_000


def test_context_variables_flow():
    """Context variables automatically attach to events."""
    captured = {}

    context = ObservabilityContext()
    context.attach_handler(lambda e: captured.update(e))

    # Set context variables
    trace_id.set('trace-123')
    request_id.set('req-456')
    operation_id.set('op-789')

    context.emit('test', 'value')

    assert captured['trace_id'] == 'trace-123'
    assert captured['request_id'] == 'req-456'
    assert captured['operation_id'] == 'op-789'


def test_context_variables_isolation():
    """Context variables are isolated between contexts."""
    events1 = []
    events2 = []

    context1 = ObservabilityContext()
    context1.attach_handler(lambda e: events1.append(e))

    context2 = ObservabilityContext()
    context2.attach_handler(lambda e: events2.append(e))

    # Set context variables and emit in first context
    trace_id.set('trace-111')
    context1.emit('test', 'value1')

    # Change context variables and emit in second context
    trace_id.set('trace-222')
    context2.emit('test', 'value2')

    assert events1[0]['trace_id'] == 'trace-111'
    assert events2[0]['trace_id'] == 'trace-222'


def test_handler_lifecycle():
    """Stateful handlers start and stop properly."""
    lifecycle = []

    class ManagedHandler:
        def start(self):
            lifecycle.append('started')
        def stop(self):
            lifecycle.append('stopped')
        def __call__(self, event):
            lifecycle.append('called')

    context = ObservabilityContext()
    context.attach_handler(ManagedHandler())

    context.start()
    context.emit('test', 'value')
    context.stop()

    assert lifecycle == ['started', 'called', 'stopped']


def test_handler_lifecycle_auto_start():
    """Handlers attached after start() are automatically started."""
    lifecycle = []

    class ManagedHandler:
        def start(self):
            lifecycle.append('started')
        def stop(self):
            lifecycle.append('stopped')
        def __call__(self, event):
            lifecycle.append('called')

    context = ObservabilityContext()
    context.start()  # Start context first

    # Attach handler after context is started
    context.attach_handler(ManagedHandler())
    context.emit('test', 'value')
    context.stop()

    assert lifecycle == ['started', 'called', 'stopped']


def test_handler_error_isolation():
    """Handler errors don't affect other handlers or emission."""
    results = {'good': [], 'bad': False}

    def good_handler(event):
        results['good'].append(event['value'])

    def bad_handler(event):
        results['bad'] = True
        raise RuntimeError("Handler error")

    context = ObservabilityContext()
    context.attach_handler(bad_handler)
    context.attach_handler(good_handler)

    # Should not raise despite bad handler
    context.emit('test', 'value1')
    context.emit('test', 'value2')

    assert results['bad'] is True
    assert results['good'] == ['value1', 'value2']


def test_handler_lifecycle_error_tolerance():
    """Lifecycle continues despite individual handler failures."""
    lifecycle = []

    class FailingStartHandler:
        def start(self):
            lifecycle.append('bad-start')
            raise RuntimeError("Start failed")
        def stop(self):
            lifecycle.append('bad-stop')
        def __call__(self, event):
            lifecycle.append('bad-called')

    class GoodHandler:
        def start(self):
            lifecycle.append('good-start')
        def stop(self):
            lifecycle.append('good-stop')
        def __call__(self, event):
            lifecycle.append('good-called')

    context = ObservabilityContext()
    context.attach_handler(FailingStartHandler())
    context.attach_handler(GoodHandler())

    context.start()
    context.emit('test', 'value')
    context.stop()

    # Bad handler fails to start but good handler continues
    assert 'bad-start' in lifecycle
    assert 'good-start' in lifecycle
    assert 'bad-called' in lifecycle  # Still called despite start failure
    assert 'good-called' in lifecycle
    assert 'good-stop' in lifecycle
    assert 'bad-stop' in lifecycle  # Stop still called for cleanup


def test_has_handlers():
    """has_handlers() correctly reports handler presence."""
    context = ObservabilityContext()

    assert not context.has_handlers()

    context.attach_handler(lambda e: None)

    assert context.has_handlers()

    context.attach_handler(lambda e: None)

    assert context.has_handlers()


def test_configuration_applied():
    """Configuration properly initializes context."""
    events = []
    handler = lambda e: events.append(e)

    config = ObservabilityConfig(
        handlers=[handler],
        sampling_rate=1.0,
        enabled_categories={'log', 'metric'}
    )

    context = ObservabilityContext(config)

    # Should have handler attached
    context.emit('log.info', 'test')
    assert len(events) == 1

    # Category filtering works
    context.emit('trace.span', 'filtered')
    assert len(events) == 1  # Not increased

    context.emit('metric.counter', 'allowed')
    assert len(events) == 2


def test_category_filtering_allow_mode():
    """Category filtering in allow mode."""
    events = []

    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    context.enable_category('log')
    context.enable_category('metric')

    # Allowed categories pass through
    context.emit('log.info', 'pass1')
    context.emit('metric.gauge', 'pass2')

    # Blocked categories are filtered
    context.emit('trace.span', 'blocked1')
    context.emit('custom.event', 'blocked2')

    assert len(events) == 2
    assert events[0]['value'] == 'pass1'
    assert events[1]['value'] == 'pass2'


def test_category_filtering_block_mode():
    """Category filtering in block mode."""
    events = []

    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    context.disable_category('trace')
    context.disable_category('debug')

    # Blocked categories are filtered
    context.emit('trace.span', 'blocked1')
    context.emit('debug.info', 'blocked2')

    # Other categories pass through
    context.emit('log.info', 'pass1')
    context.emit('metric.gauge', 'pass2')

    assert len(events) == 2
    assert events[0]['value'] == 'pass1'
    assert events[1]['value'] == 'pass2'



def test_sampling_rate_config():
    """Invalid sampling rate raises ValueError."""
    with pytest.raises(ValueError):
        ObservabilityConfig(sampling_rate=-0.1)

    with pytest.raises(ValueError):
        ObservabilityConfig(sampling_rate=1.1)

    # Valid rates should work
    ObservabilityConfig(sampling_rate=0.0)
    ObservabilityConfig(sampling_rate=0.5)
    ObservabilityConfig(sampling_rate=1.0)


def test_event_timestamp():
    """Events include relative timestamp from context creation."""
    events = []

    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))

    # Small delay to ensure measurable time difference
    time.sleep(0.001)

    context.emit('test1', 'value1')
    time.sleep(0.001)
    context.emit('test2', 'value2')

    # Timestamps should be monotonically increasing
    assert events[0]['timestamp_ns'] > 0
    assert events[1]['timestamp_ns'] > events[0]['timestamp_ns']


def test_metadata_merging():
    """Metadata properly merges with event data."""
    events = []

    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))

    context.emit('test', 'value',
                 custom1='metadata1',
                 custom2='metadata2',
                 level='info')

    event = events[0]
    assert event['type'] == 'test'
    assert event['value'] == 'value'
    assert event['custom1'] == 'metadata1'
    assert event['custom2'] == 'metadata2'
    assert event['level'] == 'info'


def test_multiple_contexts_independent():
    """Multiple contexts operate independently."""
    events1 = []
    events2 = []

    context1 = ObservabilityContext()
    context1.attach_handler(lambda e: events1.append(e))

    context2 = ObservabilityContext()
    context2.attach_handler(lambda e: events2.append(e))

    context1.emit('test1', 'value1')
    context2.emit('test2', 'value2')

    assert len(events1) == 1
    assert len(events2) == 1
    assert events1[0]['type'] == 'test1'
    assert events2[0]['type'] == 'test2'


def test_handler_stop_reverse_order():
    """Handlers stop in reverse order of registration."""
    lifecycle = []

    class OrderedHandler:
        def __init__(self, name):
            self.name = name

        def start(self):
            lifecycle.append(f'{self.name}-start')

        def stop(self):
            lifecycle.append(f'{self.name}-stop')

        def __call__(self, event):
            pass

    context = ObservabilityContext()
    context.attach_handler(OrderedHandler('first'))
    context.attach_handler(OrderedHandler('second'))
    context.attach_handler(OrderedHandler('third'))

    context.start()
    context.stop()

    # Start in order
    assert lifecycle[:3] == ['first-start', 'second-start', 'third-start']
    # Stop in reverse order
    assert lifecycle[3:] == ['third-stop', 'second-stop', 'first-stop']
