"""
Tests for multi-domain integration.

Validates that multiple domains can work together sharing the same
context and context variables.
"""

import pytest
from observability import ObservabilityContext, trace_id
from observability.domains.logging import Logger
from observability.domains.tracing import Span
from observability.domains.metrics import Counter


def test_domains_work_together():
    """Multiple domains share context and handlers."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('webapp', context)
    counter = Counter('requests', context)
    
    # Simulate request handling
    trace_id.set('abc-123')
    
    with Span('handle_request', context):
        logger.info("Request started")
        counter.increment()
        
        with Span('database_query', context):
            logger.debug("Querying database")
        
        logger.info("Request completed")
    
    # All events should have the trace ID
    for event in events:
        assert event.get('trace_id') == 'abc-123'
    
    # Should have mixed event types
    event_types = [e['type'] for e in events]
    assert any(t.startswith('log.') for t in event_types)
    assert any(t.startswith('span.') for t in event_types)
    assert any(t.startswith('metric.') for t in event_types)


def test_domains_event_ordering():
    """Events from different domains maintain order."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('test', context)
    
    with Span('operation', context) as span:
        logger.info("Step 1")
        span.set_attribute('checkpoint', 1)
        logger.info("Step 2")
    
    # Events should be in order:
    # 1. span.start
    # 2. log (Step 1)
    # 3. log (Step 2)
    # 4. span.end
    
    assert events[0]['type'] == 'span.start'
    assert events[1]['type'] == 'log.20'
    assert events[1]['value'] == "Step 1"
    assert events[2]['type'] == 'log.20'
    assert events[2]['value'] == "Step 2"
    assert events[3]['type'] == 'span.end'
    assert events[3]['checkpoint'] == 1


def test_domains_shared_metadata():
    """Domains can share metadata through context variables."""
    from observability import request_id, operation_id
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('app', context)
    counter = Counter('operations', context)
    
    # Set shared context
    trace_id.set('trace-shared')
    request_id.set('req-shared')
    operation_id.set('op-shared')
    
    # Use different domains
    with Span('process', context):
        logger.info("Processing")
        counter.increment()
    
    # All events should have all context variables
    for event in events:
        assert event['trace_id'] == 'trace-shared'
        assert event['request_id'] == 'req-shared'
        assert event['operation_id'] == 'op-shared'


def test_domains_error_tracking():
    """Error tracking across domains."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('app', context)
    error_counter = Counter('errors', context, severity='error')
    
    try:
        with Span('failing_operation', context):
            logger.info("Starting operation")
            raise ValueError("Operation failed")
    except ValueError:
        logger.error("Operation failed", exc_type='ValueError')
        error_counter.increment()
    
    # Should have span with error
    span_end = next(e for e in events if e['type'] == 'span.end')
    assert span_end['success'] is False
    assert 'Operation failed' in span_end['error']
    
    # Should have error log
    error_log = next(e for e in events if e['type'] == 'log.40')
    assert error_log['exc_type'] == 'ValueError'
    
    # Should have error metric
    error_metric = next(e for e in events if e['type'] == 'metric.counter' and e.get('severity') == 'error')
    assert error_metric['measurement'] == 1.0


def test_domains_filtering():
    """Domain events respect category filtering."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    # Only allow logs and metrics
    context.enable_category('log')
    context.enable_category('metric')
    
    logger = Logger('app', context)
    counter = Counter('count', context)
    
    with Span('filtered_span', context):  # This should be filtered
        logger.info("This passes")  # This should pass
        counter.increment()  # This should pass
    
    # Should only have log and metric events
    event_types = [e['type'] for e in events]
    assert all(t.startswith('log.') or t.startswith('metric.') for t in event_types)
    assert not any(t.startswith('span.') for t in event_types)


def test_nested_spans_with_logging():
    """Nested spans with interleaved logging."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('app', context)
    
    with Span('outer', context) as outer:
        logger.info("Outer started")
        
        with outer.start_child('middle') as middle:
            logger.info("Middle started")
            
            with middle.start_child('inner'):
                logger.info("Inner started")
                logger.info("Inner completed")
            
            logger.info("Middle completed")
        
        logger.info("Outer completed")
    
    # Count event types
    span_starts = sum(1 for e in events if e['type'] == 'span.start')
    span_ends = sum(1 for e in events if e['type'] == 'span.end')
    logs = sum(1 for e in events if e['type'].startswith('log.'))
    
    assert span_starts == 3  # outer, middle, inner
    assert span_ends == 3
    assert logs == 6  # 2 per span level