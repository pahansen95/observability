"""
Tests for the metrics domain integration.

Validates that Counter, Gauge, and Histogram classes properly emit
measurement events through the observability context.
"""

import pytest
import time
from observability import ObservabilityContext
from observability.domains.metrics import Counter, Gauge, Histogram, Timer, DEFAULT_BUCKETS


def test_metrics_domain():
    """Metrics domain emits measurement events."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    # Counter usage
    counter = Counter('api_requests', context, endpoint='/users')
    counter.increment()
    counter.increment(5)
    
    # Gauge usage
    gauge = Gauge('queue_size', context)
    gauge.set(42)
    
    # Histogram usage
    histogram = Histogram('response_time', context)
    histogram.observe(0.123)
    
    assert len(events) == 4
    assert events[0]['type'] == 'metric.counter'
    assert events[0]['name'] == 'api_requests'
    assert events[0]['value'] == 1.0
    assert events[0]['measurement'] == 1.0
    assert events[0]['endpoint'] == '/users'
    
    assert events[1]['type'] == 'metric.counter'
    assert events[1]['value'] == 5
    assert events[1]['measurement'] == 5
    
    assert events[2]['type'] == 'metric.gauge'
    assert events[2]['name'] == 'queue_size'
    assert events[2]['value'] == 42
    assert events[2]['measurement'] == 42
    
    assert events[3]['type'] == 'metric.histogram'
    assert events[3]['name'] == 'response_time'
    assert events[3]['value'] == 0.123
    assert events[3]['measurement'] == 0.123


def test_counter_increment():
    """Counter only allows positive increments."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    counter = Counter('test_counter', context)
    
    # Valid increments
    counter.increment()  # Default 1.0
    counter.increment(10)
    counter.increment(0.5)
    
    # Invalid increment should raise
    with pytest.raises(ValueError):
        counter.increment(-1)
    
    assert len(events) == 3
    assert events[0]['measurement'] == 1.0
    assert events[1]['measurement'] == 10
    assert events[2]['measurement'] == 0.5


def test_gauge_operations():
    """Gauge supports set, increment, and decrement."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    gauge = Gauge('active_connections', context)
    
    gauge.set(10)
    gauge.increment(3)
    gauge.decrement(2)
    gauge.set(0)
    
    assert len(events) == 4
    
    # Set operations
    assert events[0]['measurement'] == 10
    assert 'delta' not in events[0]
    
    # Increment
    assert events[1]['measurement'] == 3
    assert events[1]['delta'] is True
    
    # Decrement (emits negative value)
    assert events[2]['measurement'] == -2
    assert events[2]['delta'] is True
    
    # Another set
    assert events[3]['measurement'] == 0
    assert 'delta' not in events[3]


def test_histogram_buckets():
    """Histogram includes bucket configuration."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    # Default buckets
    hist1 = Histogram('latency', context)
    hist1.observe(0.05)
    
    # Custom buckets
    custom_buckets = [0.1, 0.5, 1.0, 5.0]
    hist2 = Histogram('custom_latency', context, buckets=custom_buckets)
    hist2.observe(0.75)
    
    assert events[0]['buckets'] == hist1._buckets  # Default buckets
    assert events[1]['buckets'] == custom_buckets


def test_metric_labels():
    """Metrics support static and dynamic labels."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    # Static labels from constructor
    counter = Counter('requests', context, service='api', version='1.0')
    
    # Dynamic labels on method calls
    counter.increment(endpoint='/users', method='GET')
    counter.increment(endpoint='/posts', method='POST')
    
    # Labels should merge
    assert events[0]['service'] == 'api'
    assert events[0]['version'] == '1.0'
    assert events[0]['endpoint'] == '/users'
    assert events[0]['method'] == 'GET'
    
    assert events[1]['service'] == 'api'
    assert events[1]['version'] == '1.0'
    assert events[1]['endpoint'] == '/posts'
    assert events[1]['method'] == 'POST'



def test_histogram_timer():
    """Histogram timer measures duration."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    histogram = Histogram('operation_time', context)
    
    with histogram.time(operation='test'):
        time.sleep(0.01)  # 10ms
    
    event = events[0]
    assert event['type'] == 'metric.histogram'
    assert event['name'] == 'operation_time'
    assert event['operation'] == 'test'
    
    # Should be at least 10ms
    assert event['measurement'] >= 0.01
    # But less than 20ms
    assert event['measurement'] < 0.02


def test_timer_context_manager():
    """Timer works as standalone context manager."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    histogram = Histogram('timer_test', context)
    timer = Timer(histogram, stage='processing')
    
    with timer:
        time.sleep(0.005)
    
    event = events[0]
    assert event['stage'] == 'processing'
    assert event['measurement'] >= 0.005


def test_metrics_zero_overhead():
    """Metrics have zero overhead when no handlers attached."""
    context = ObservabilityContext()
    
    counter = Counter('test', context)
    gauge = Gauge('test', context)
    histogram = Histogram('test', context)
    
    # Should be very fast
    start = time.perf_counter_ns()
    for _ in range(10000):
        counter.increment()
        gauge.set(42)
        histogram.observe(0.123)
    duration = time.perf_counter_ns() - start
    
    # Should be fast (less than 20ms for 30k operations)
    assert duration < 20_000_000


def test_metrics_help_text():
    """Metrics include help text in events."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    counter = Counter('total_errors', context, description='Total number of errors')
    counter.increment()
    
    gauge = Gauge('temperature', context, description='Current temperature in Celsius')
    gauge.set(25.5)
    
    assert events[0]['help'] == 'Total number of errors'
    assert events[1]['help'] == 'Current temperature in Celsius'


def test_metric_type_field():
    """Metrics include metric_type field."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    Counter('c', context).increment()
    Gauge('g', context).set(1)
    Histogram('h', context).observe(1)
    
    assert events[0]['metric_type'] == 'counter'
    assert events[1]['metric_type'] == 'gauge'
    assert events[2]['metric_type'] == 'histogram'


def test_metrics_context_variables():
    """Metric events include context variables."""
    from observability import trace_id, request_id
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    trace_id.set('trace-metrics')
    request_id.set('req-metrics')
    
    counter = Counter('test', context)
    counter.increment()
    
    event = events[0]
    assert event['trace_id'] == 'trace-metrics'
    assert event['request_id'] == 'req-metrics'


def test_default_buckets_constant():
    """DEFAULT_BUCKETS constant is properly defined and accessible."""
    # Should be accessible at module level
    assert DEFAULT_BUCKETS is not None
    assert isinstance(DEFAULT_BUCKETS, tuple)
    
    # Should contain expected bucket values suitable for latency measurements
    expected_buckets = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    assert DEFAULT_BUCKETS == expected_buckets
    
    # Should be in ascending order
    assert list(DEFAULT_BUCKETS) == sorted(DEFAULT_BUCKETS)
    
    # Should be same as Histogram.DEFAULT_BUCKETS
    assert DEFAULT_BUCKETS == Histogram.DEFAULT_BUCKETS
    
    # Should be used as default when no buckets specified
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    histogram = Histogram('test', context)
    histogram.observe(0.1)
    
    # Event should contain default buckets
    assert events[0]['buckets'] == list(DEFAULT_BUCKETS)