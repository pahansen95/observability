"""
Tests for the logging domain integration.

Validates that the Logger class properly emits structured log events
through the observability context.
"""

import pytest
from observability import ObservabilityContext
from observability.domains.logging import Logger, DEBUG, INFO, WARNING, ERROR, CRITICAL


def test_logger_domain():
    """Logger domain emits structured log events."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('myapp', context)
    logger.info("Application started", version='1.0')
    logger.error("Connection failed", retry_count=3)
    
    assert len(events) == 2
    assert events[0]['type'] == 'log.20'  # INFO level
    assert events[0]['value'] == "Application started"
    assert events[0]['version'] == '1.0'
    assert events[0]['logger'] == 'myapp'
    assert events[0]['level'] == INFO
    
    assert events[1]['type'] == 'log.40'  # ERROR level
    assert events[1]['value'] == "Connection failed"
    assert events[1]['retry_count'] == 3
    assert events[1]['logger'] == 'myapp'
    assert events[1]['level'] == ERROR


def test_logger_level_filtering():
    """Logger respects minimum level setting."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('test', context)
    logger.setLevel(WARNING)
    
    # These should be filtered
    logger.debug("Debug message")
    logger.info("Info message")
    
    # These should pass through
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    assert len(events) == 3
    assert events[0]['value'] == "Warning message"
    assert events[1]['value'] == "Error message"
    assert events[2]['value'] == "Critical message"


def test_logger_all_levels():
    """Logger supports all standard log levels."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('test', context)
    
    logger.debug("Debug")
    logger.info("Info")
    logger.warning("Warning")
    logger.error("Error")
    logger.critical("Critical")
    
    assert len(events) == 5
    assert events[0]['type'] == 'log.10'  # DEBUG
    assert events[1]['type'] == 'log.20'  # INFO
    assert events[2]['type'] == 'log.30'  # WARNING
    assert events[3]['type'] == 'log.40'  # ERROR
    assert events[4]['type'] == 'log.50'  # CRITICAL


def test_logger_with_args():
    """Logger preserves positional arguments."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('test', context)
    logger.info("User %s logged in from %s", "alice", "192.168.1.1")
    
    event = events[0]
    assert event['value'] == "User %s logged in from %s"
    assert event['args'] == ("alice", "192.168.1.1")


def test_logger_child():
    """Child loggers have extended names."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    parent = Logger('myapp', context)
    child = parent.getChild('module')
    grandchild = child.getChild('submodule')
    
    parent.info("Parent log")
    child.info("Child log")
    grandchild.info("Grandchild log")
    
    assert events[0]['logger'] == 'myapp'
    assert events[1]['logger'] == 'myapp.module'
    assert events[2]['logger'] == 'myapp.module.submodule'


def test_logger_zero_overhead():
    """Logger has zero overhead when no handlers attached."""
    context = ObservabilityContext()
    logger = Logger('test', context)
    
    # Should not raise and should be very fast
    import time
    start = time.perf_counter_ns()
    for _ in range(10000):
        logger.info("Message")
    duration = time.perf_counter_ns() - start
    
    # Should be extremely fast
    assert duration < 10_000_000  # Less than 10ms for 10k logs


def test_logger_lazy_context():
    """Logger supports lazy context resolution."""
    events = []
    
    # Create logger with lambda that will resolve later
    logger = Logger('test', lambda: context)
    
    # Now create context and attach handler
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    # Should work
    logger.info("Lazy context works")
    
    assert len(events) == 1
    assert events[0]['value'] == "Lazy context works"


def test_logger_log_method():
    """Logger.log() accepts explicit level."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('test', context)
    logger.log(INFO, "Info via log()")
    logger.log(ERROR, "Error via log()")
    
    assert events[0]['type'] == 'log.20'
    assert events[0]['level'] == INFO
    assert events[1]['type'] == 'log.40'
    assert events[1]['level'] == ERROR


def test_logger_custom_metadata():
    """Logger forwards all keyword arguments as metadata."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('test', context)
    logger.info("User action", 
                user_id=123,
                action="login",
                ip_address="10.0.0.1",
                session_id="abc-123")
    
    event = events[0]
    assert event['user_id'] == 123
    assert event['action'] == "login"
    assert event['ip_address'] == "10.0.0.1"
    assert event['session_id'] == "abc-123"


def test_logger_inherits_context_variables():
    """Logger events include context variables."""
    from observability import trace_id, request_id
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    logger = Logger('test', context)
    
    trace_id.set('trace-789')
    request_id.set('req-456')
    
    logger.info("With context vars")
    
    event = events[0]
    assert event['trace_id'] == 'trace-789'
    assert event['request_id'] == 'req-456'