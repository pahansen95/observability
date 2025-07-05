"""
Tests for the logging domain integration.

Validates that the Logger class properly emits structured log events
through the observability context.
"""

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
    logger.min_level = WARNING

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
    child = parent.get_child('module')
    grandchild = child.get_child('submodule')

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


def test_logger_is_enabled_for():
    """Logger.is_enabled_for() correctly checks minimum level."""
    context = ObservabilityContext()
    logger = Logger('test', context)

    # Default min_level is DEBUG (10)
    assert logger.is_enabled_for(DEBUG) is True
    assert logger.is_enabled_for(INFO) is True
    assert logger.is_enabled_for(WARNING) is True
    assert logger.is_enabled_for(ERROR) is True
    assert logger.is_enabled_for(CRITICAL) is True
    assert logger.is_enabled_for(5) is False  # Below DEBUG

    # Set min_level to WARNING
    logger.min_level = WARNING
    assert logger.is_enabled_for(DEBUG) is False
    assert logger.is_enabled_for(INFO) is False
    assert logger.is_enabled_for(WARNING) is True
    assert logger.is_enabled_for(ERROR) is True
    assert logger.is_enabled_for(CRITICAL) is True
    assert logger.is_enabled_for(25) is False  # Between INFO and WARNING
    assert logger.is_enabled_for(35) is True   # Between WARNING and ERROR


def test_logger_is_enabled_for_performance_optimization():
    """Logger.is_enabled_for() enables performance optimization patterns."""
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))

    logger = Logger('test', context)
    logger.min_level = ERROR  # Only errors and critical

    expensive_called = False
    def expensive_computation():
        nonlocal expensive_called
        expensive_called = True
        return "expensive result"

    # Performance optimization pattern - check before expensive work
    if logger.is_enabled_for(DEBUG):
        logger.debug("Debug info: %s", expensive_computation())

    if logger.is_enabled_for(INFO):
        logger.info("Info: %s", expensive_computation())

    if logger.is_enabled_for(ERROR):
        logger.error("Error: %s", expensive_computation())

    # Only the ERROR case should have run expensive computation
    assert expensive_called is True
    assert len(events) == 1
    assert events[0]['level'] == ERROR


def test_logger_is_enabled_for_child_logger():
    """Child loggers have independent is_enabled_for() behavior."""
    context = ObservabilityContext()

    parent = Logger('app', context)
    child = parent.get_child('module')

    # Parent set to WARNING
    parent.min_level = WARNING
    # Child set to DEBUG
    child.min_level = DEBUG

    # Parent should only allow WARNING and above
    assert parent.is_enabled_for(DEBUG) is False
    assert parent.is_enabled_for(INFO) is False
    assert parent.is_enabled_for(WARNING) is True

    # Child should allow DEBUG and above (independent setting)
    assert child.is_enabled_for(DEBUG) is True
    assert child.is_enabled_for(INFO) is True
    assert child.is_enabled_for(WARNING) is True


def test_logger_is_enabled_for_various_levels():
    """Logger.is_enabled_for() works with custom numeric levels."""
    context = ObservabilityContext()
    logger = Logger('test', context)

    # Set to custom level between INFO (20) and WARNING (30)
    logger.min_level = 25

    assert logger.is_enabled_for(10) is False  # DEBUG
    assert logger.is_enabled_for(20) is False  # INFO
    assert logger.is_enabled_for(24) is False  # Just below threshold
    assert logger.is_enabled_for(25) is True   # Exact threshold
    assert logger.is_enabled_for(26) is True   # Just above threshold
    assert logger.is_enabled_for(30) is True   # WARNING
    assert logger.is_enabled_for(40) is True   # ERROR
    assert logger.is_enabled_for(50) is True   # CRITICAL
