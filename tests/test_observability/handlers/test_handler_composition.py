"""
Tests for handler composition patterns.

Validates that handlers compose through standard patterns like
filtering, sampling, fanout, and fallback.
"""

from observability import ObservabilityContext
from observability.handlers import (
    filtered,
    sampled,
    FanoutHandler,
    FallbackHandler,
    TimeDeltaHandler,
)


def test_handler_composition():
    """Handlers compose through standard patterns."""
    results = {'all': [], 'errors': [], 'sampled': []}

    # All events
    all_handler = lambda e: results['all'].append(e['value'])

    # Only errors
    error_handler = filtered(
        lambda e: e.get('level') == 'error',
        lambda e: results['errors'].append(e['value'])
    )

    # 10% sample with fixed seed for deterministic test
    sampled_handler = sampled(
        0.1,
        lambda e: results['sampled'].append(e['value']),
        seed=42
    )

    fanout = FanoutHandler(all_handler, error_handler, sampled_handler)

    context = ObservabilityContext()
    context.attach_handler(fanout)

    # Emit various events
    context.emit('log', 'info1', level='info')
    context.emit('log', 'error1', level='error')
    context.emit('log', 'info2', level='info')
    context.emit('log', 'error2', level='error')

    # More events to test sampling
    for i in range(20):
        context.emit('log', f'event{i}', level='info')

    assert results['all'] == ['info1', 'error1', 'info2', 'error2'] + [f'event{i}' for i in range(20)]
    assert results['errors'] == ['error1', 'error2']
    # With seed=42 and 0.1 rate, should sample roughly 10%
    assert 0 < len(results['sampled']) < 10  # Should be around 2-3 events


def test_filtered_handler():
    """Filtered handler only processes matching events."""
    results = []

    # Filter for high-priority events
    high_priority_handler = filtered(
        lambda e: e.get('priority', 0) >= 8,
        lambda e: results.append(e)
    )

    context = ObservabilityContext()
    context.attach_handler(high_priority_handler)

    context.emit('event', 'low', priority=1)
    context.emit('event', 'medium', priority=5)
    context.emit('event', 'high', priority=8)
    context.emit('event', 'critical', priority=10)
    context.emit('event', 'no_priority')  # No priority field

    assert len(results) == 2
    assert results[0]['value'] == 'high'
    assert results[1]['value'] == 'critical'


def test_filtered_handler_error_tolerance():
    """Filter predicate errors don't affect event processing."""
    results = []

    def buggy_predicate(event):
        if event.get('crash'):
            raise RuntimeError("Predicate error")
        return event.get('should_pass', False)

    filtered_handler = filtered(buggy_predicate, lambda e: results.append(e['value']))

    context = ObservabilityContext()
    context.attach_handler(filtered_handler)

    context.emit('test', 'skip1')  # No 'should_pass' field
    context.emit('test', 'crash1', crash=True)  # Predicate crashes
    context.emit('test', 'pass1', should_pass=True)  # Should pass
    context.emit('test', 'crash2', crash=True, should_pass=True)  # Crashes even with should_pass=True
    context.emit('test', 'pass2', should_pass=True)  # Should pass

    assert results == ['pass1', 'pass2']


def test_sampled_handler():
    """Sampled handler processes events at specified rate."""
    results = []

    # 50% sampling rate with fixed seed
    half_sampled = sampled(0.5, lambda e: results.append(e['value']), seed=123)

    context = ObservabilityContext()
    context.attach_handler(half_sampled)

    # Emit many events
    for i in range(100):
        context.emit('test', i)

    # Should have roughly 50% of events (35-65 with high probability)
    assert 35 <= len(results) <= 65

    # Check that sampling is deterministic with seed
    results2 = []
    half_sampled2 = sampled(0.5, lambda e: results2.append(e['value']), seed=123)
    context2 = ObservabilityContext()
    context2.attach_handler(half_sampled2)

    for i in range(100):
        context2.emit('test', i)

    assert results == results2  # Same seed produces same results


def test_sampled_edge_cases():
    """Sampled handler handles edge case rates."""
    # 0% sampling - no events
    never_results = []
    never_sampled = sampled(0.0, lambda e: never_results.append(e))

    # 100% sampling - all events
    always_results = []
    always_sampled = sampled(1.0, lambda e: always_results.append(e))

    context = ObservabilityContext()
    context.attach_handler(never_sampled)
    context.attach_handler(always_sampled)

    for i in range(10):
        context.emit('test', i)

    assert len(never_results) == 0
    assert len(always_results) == 10


def test_fanout_handler():
    """FanoutHandler broadcasts to multiple handlers."""
    results = {'h1': [], 'h2': [], 'h3': []}

    handler1 = lambda e: results['h1'].append(e['value'])
    handler2 = lambda e: results['h2'].append(e['value'])
    handler3 = lambda e: results['h3'].append(e['value'])

    fanout = FanoutHandler(handler1, handler2, handler3)

    context = ObservabilityContext()
    context.attach_handler(fanout)

    context.emit('test', 'event1')
    context.emit('test', 'event2')

    assert results['h1'] == ['event1', 'event2']
    assert results['h2'] == ['event1', 'event2']
    assert results['h3'] == ['event1', 'event2']


def test_fanout_error_isolation():
    """FanoutHandler isolates errors between handlers."""
    results = {'good1': [], 'good2': []}

    def good_handler1(event):
        results['good1'].append(event['value'])

    def bad_handler(event):
        raise RuntimeError("Handler error")

    def good_handler2(event):
        results['good2'].append(event['value'])

    fanout = FanoutHandler(good_handler1, bad_handler, good_handler2)

    context = ObservabilityContext()
    context.attach_handler(fanout)

    # Should not raise despite bad handler
    context.emit('test', 'value1')
    context.emit('test', 'value2')

    assert results['good1'] == ['value1', 'value2']
    assert results['good2'] == ['value1', 'value2']


def test_fanout_lifecycle():
    """FanoutHandler manages sub-handler lifecycle."""
    lifecycle = []

    class ManagedHandler:
        def __init__(self, name):
            self.name = name

        def start(self):
            lifecycle.append(f'{self.name}-start')

        def stop(self):
            lifecycle.append(f'{self.name}-stop')

        def __call__(self, event):
            lifecycle.append(f'{self.name}-called')

    fanout = FanoutHandler(
        ManagedHandler('h1'),
        ManagedHandler('h2'),
        ManagedHandler('h3')
    )

    context = ObservabilityContext()
    context.attach_handler(fanout)

    context.start()
    context.emit('test', 'value')
    context.stop()

    # All handlers should start
    assert 'h1-start' in lifecycle
    assert 'h2-start' in lifecycle
    assert 'h3-start' in lifecycle

    # All should be called
    assert 'h1-called' in lifecycle
    assert 'h2-called' in lifecycle
    assert 'h3-called' in lifecycle

    # All should stop (in reverse order)
    stop_events = [e for e in lifecycle if e.endswith('-stop')]
    assert stop_events == ['h3-stop', 'h2-stop', 'h1-stop']


def test_fallback_handler():
    """FallbackHandler provides automatic failover."""
    results = {'primary': [], 'backup1': [], 'backup2': []}
    call_count = {'primary': 0}

    def primary_handler(event):
        call_count['primary'] += 1
        # Fail on first two calls
        if call_count['primary'] <= 2:
            raise RuntimeError("Primary failed")
        results['primary'].append(event['value'])

    def backup1_handler(event):
        # Always fails
        raise RuntimeError("Backup1 failed")

    def backup2_handler(event):
        results['backup2'].append(event['value'])

    fallback = FallbackHandler(primary_handler, backup1_handler, backup2_handler)

    context = ObservabilityContext()
    context.attach_handler(fallback)

    # First two events should go to backup2
    context.emit('test', 'event1')
    context.emit('test', 'event2')

    # Third event should succeed with primary
    context.emit('test', 'event3')
    context.emit('test', 'event4')

    assert results['primary'] == ['event3', 'event4']
    assert results['backup1'] == []  # Always fails
    assert results['backup2'] == ['event1', 'event2']


def test_fallback_all_fail():
    """FallbackHandler handles case where all handlers fail."""
    def failing_handler(name):
        def handler(event):
            raise RuntimeError(f"{name} failed")
        return handler

    fallback = FallbackHandler(
        failing_handler('primary'),
        failing_handler('backup1'),
        failing_handler('backup2')
    )

    context = ObservabilityContext()
    context.attach_handler(fallback)

    # Should not raise even when all handlers fail
    context.emit('test', 'value')


def test_time_delta_handler():
    """TimeDeltaHandler enriches events with timing info."""
    events = []

    base_handler = lambda e: events.append(e)
    delta_handler = TimeDeltaHandler(base_handler)

    context = ObservabilityContext()
    context.attach_handler(delta_handler)

    # Emit events with small delays
    import time
    context.emit('test', 'event1')
    time.sleep(0.001)  # 1ms
    context.emit('test', 'event2')
    time.sleep(0.002)  # 2ms
    context.emit('test', 'event3')

    # First event might have delta_ns=0 (implementation specific)
    if 'delta_ns' in events[0]:
        assert events[0]['delta_ns'] == 0
    assert 'timestamp_us' in events[0]
    assert 'timestamp_ms' in events[0]

    # Subsequent events have deltas
    assert events[1]['delta_ns'] >= 1_000_000  # At least 1ms
    assert events[1]['delta_us'] >= 1_000
    assert events[1]['delta_ms'] >= 1

    assert events[2]['delta_ns'] >= 2_000_000  # At least 2ms
    assert events[2]['delta_us'] >= 2_000
    assert events[2]['delta_ms'] >= 2


def test_time_delta_reset():
    """TimeDeltaHandler reset() clears delta tracking."""
    events = []

    base_handler = lambda e: events.append(e)
    delta_handler = TimeDeltaHandler(base_handler)

    context = ObservabilityContext()
    context.attach_handler(delta_handler)

    context.emit('test', 'event1')
    context.emit('test', 'event2')

    # Reset delta tracking
    delta_handler.reset()

    context.emit('test', 'event3')
    context.emit('test', 'event4')

    # Event after reset might have delta_ns=0
    assert 'delta_ns' in events[1]  # event2 has delta
    if 'delta_ns' in events[2]:  # event3 after reset
        assert events[2]['delta_ns'] == 0
    assert 'delta_ns' in events[3]  # event4 has delta again


def test_nested_composition():
    """Handlers can be deeply nested."""
    results = {'filtered_sampled': [], 'all': []}

    # Complex composition: Filter errors, then sample 50%, then fanout
    error_filter = filtered(
        lambda e: e.get('level') == 'error',
        sampled(
            0.5,
            lambda e: results['filtered_sampled'].append(e['value']),
            seed=99
        )
    )

    all_handler = lambda e: results['all'].append(e['value'])

    fanout = FanoutHandler(error_filter, all_handler)

    context = ObservabilityContext()
    context.attach_handler(fanout)

    # Emit mix of events
    for i in range(20):
        level = 'error' if i % 3 == 0 else 'info'
        context.emit('test', f'event{i}', level=level)

    # All events go to all_handler
    assert len(results['all']) == 20

    # Only errors that pass sampling go to filtered_sampled
    error_count = sum(1 for i in range(20) if i % 3 == 0)
    assert 0 < len(results['filtered_sampled']) < error_count
