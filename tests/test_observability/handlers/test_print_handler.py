"""
Tests for PrintHandler implementation.

Validates that PrintHandler properly formats events as human-readable text
with configurable format strings and context inclusion.
"""

import io
import pytest
from observability.handlers import PrintHandler
from observability.types import EventDict


def test_print_handler_basic_formatting():
    """PrintHandler formats events with default format string."""
    output = io.StringIO()
    handler = PrintHandler(output)
    
    event: EventDict = {
        'type': 'log.info',
        'value': 'Application started',
        'timestamp_ns': 1609459200000000000  # 2021-01-01T00:00:00Z
    }
    
    handler(event)
    
    result = output.getvalue()
    assert 'log.info: Application started' in result
    # Should include formatted timestamp
    assert '2021-01-01T00:00:00' in result or '1609459200000000000' in result


def test_print_handler_custom_format():
    """PrintHandler supports custom format strings."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{type}: {value}")
    
    event: EventDict = {
        'type': 'metric.counter',
        'value': 'requests_total',
        'count': 42
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    # Context fields not in format string are included by default
    assert result == "metric.counter: requests_total (count=42)"


def test_print_handler_format_with_metadata():
    """PrintHandler includes metadata fields in format string."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{type} [{severity}]: {value} (user={user_id})")
    
    event: EventDict = {
        'type': 'log.error',
        'value': 'Authentication failed',
        'severity': 'ERROR',
        'user_id': 'user123'
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    expected = "log.error [ERROR]: Authentication failed (user=user123)"
    assert result == expected


def test_print_handler_missing_fields():
    """PrintHandler handles missing fields gracefully."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{type}: {value} - {missing_field}")
    
    event: EventDict = {
        'type': 'test',
        'value': 'data'
        # missing_field not provided
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    # Missing fields generate format error messages
    assert "Format error:" in result
    assert "missing_field" in result


def test_print_handler_context_inclusion():
    """PrintHandler includes context variables when enabled."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{type}: {value}", include_context=True)
    
    event: EventDict = {
        'type': 'test',
        'value': 'data',
        'trace_id': 'trace-123',
        'request_id': 'req-456'
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    # Should include context IDs when include_context=True
    assert 'trace-123' in result
    assert 'req-456' in result


def test_print_handler_context_exclusion():
    """PrintHandler excludes context variables when disabled."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{type}: {value}", include_context=False)
    
    event: EventDict = {
        'type': 'test',
        'value': 'data',
        'trace_id': 'trace-123',
        'request_id': 'req-456'
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    expected = "test: data"
    assert result == expected
    # Context IDs should not appear
    assert 'trace-123' not in result
    assert 'req-456' not in result


def test_print_handler_timestamp_formatting():
    """PrintHandler formats timestamps appropriately."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{timestamp_ns} {type}: {value}")
    
    event: EventDict = {
        'type': 'test',
        'value': 'data',
        'timestamp_ns': 1609459200123456789  # Specific nanosecond timestamp
    }
    
    handler(event)
    
    result = output.getvalue()
    # Should include the timestamp_ns value in the output
    assert '1609459200123456789' in result
    assert 'test: data' in result


def test_print_handler_complex_values():
    """PrintHandler handles complex data types in values."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{type}: {value}")
    
    # Test with various value types
    events = [
        {'type': 'test.dict', 'value': {'nested': 'data', 'count': 42}},
        {'type': 'test.list', 'value': [1, 2, 3, 'item']},
        {'type': 'test.none', 'value': None},
        {'type': 'test.bool', 'value': True},
    ]
    
    for event in events:
        handler(event)
    
    result = output.getvalue()
    # Should handle all value types without errors
    assert 'test.dict' in result
    assert 'test.list' in result
    assert 'test.none' in result
    assert 'test.bool' in result


def test_print_handler_stream_flushing():
    """PrintHandler uses print() which doesn't automatically flush."""
    
    class FlushTrackingStream(io.StringIO):
        def __init__(self):
            super().__init__()
            self.flush_count = 0
        
        def flush(self):
            self.flush_count += 1
            super().flush()
    
    output = FlushTrackingStream()
    handler = PrintHandler(output, format="{type}: {value}")
    
    event: EventDict = {'type': 'test', 'value': 'data'}
    
    # print() doesn't automatically flush, so no flush calls expected
    initial_flush_count = output.flush_count
    handler(event)
    
    # Event should be written to stream even without flushing
    assert output.getvalue()
    assert 'test: data' in output.getvalue()
    # Flush count should remain the same since print() doesn't flush
    assert output.flush_count == initial_flush_count


def test_print_handler_multiple_events():
    """PrintHandler handles multiple events correctly."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{type}: {value}")
    
    events = [
        {'type': 'event1', 'value': 'first'},
        {'type': 'event2', 'value': 'second'},
        {'type': 'event3', 'value': 'third'},
    ]
    
    for event in events:
        handler(event)
    
    result = output.getvalue()
    lines = result.strip().split('\n')
    
    assert len(lines) == 3
    assert 'event1: first' in lines[0]
    assert 'event2: second' in lines[1]
    assert 'event3: third' in lines[2]


def test_print_handler_unicode_support():
    """PrintHandler handles Unicode characters correctly."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{type}: {value}")
    
    event: EventDict = {
        'type': 'test.unicode',
        'value': 'Hello 世界 🌍 café naïve résumé',
        'emoji': '🚀💻🔧'
    }
    
    handler(event)
    
    result = output.getvalue()
    assert 'Hello 世界 🌍 café naïve résumé' in result


def test_print_handler_format_error_handling():
    """PrintHandler handles format string errors gracefully."""
    output = io.StringIO()
    
    # Invalid format string with undefined field
    handler = PrintHandler(output, format="{type}: {value} {undefined_field}")
    
    event: EventDict = {
        'type': 'test',
        'value': 'data'
    }
    
    # Should handle format errors gracefully, not crash
    handler(event)
    result = output.getvalue()
    # Should generate format error message
    assert "Format error:" in result
    assert "undefined_field" in result


def test_print_handler_newline_behavior():
    """PrintHandler adds appropriate newlines between events."""
    output = io.StringIO()
    handler = PrintHandler(output, format="{value}")
    
    events = [
        {'value': 'line1'},
        {'value': 'line2'}
    ]
    
    for event in events:
        handler(event)
    
    result = output.getvalue()
    # Should have newlines separating events
    assert 'line1\n' in result
    assert 'line2\n' in result or result.endswith('line2')


def test_print_handler_stream_error_handling():
    """PrintHandler handles stream write errors appropriately."""
    import sys
    from io import StringIO
    
    class FailingStream:
        def write(self, data):
            raise IOError("Stream write failed")
        
        def flush(self):
            pass
    
    failing_output = FailingStream()
    handler = PrintHandler(failing_output)
    
    event: EventDict = {'type': 'test', 'value': 'data'}
    
    # Capture stderr to check for error message
    old_stderr = sys.stderr
    stderr_capture = StringIO()
    sys.stderr = stderr_capture
    
    try:
        # Should handle the error gracefully and print to stderr
        handler(event)
        
        # Check that error was logged to stderr
        stderr_output = stderr_capture.getvalue()
        assert "Print handler error:" in stderr_output
        assert "Stream write failed" in stderr_output
    finally:
        sys.stderr = old_stderr


def test_print_handler_thread_safety():
    """PrintHandler is thread-safe when underlying stream is thread-safe."""
    import threading
    import time
    
    output = io.StringIO()
    handler = PrintHandler(output, format="{thread}: {value}")
    
    results = []
    
    def write_events(thread_id):
        for i in range(10):
            event = {'thread': f'thread-{thread_id}', 'value': f'event-{i}'}
            handler(event)
            time.sleep(0.001)  # Small delay to encourage interleaving
    
    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=write_events, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    result = output.getvalue()
    lines = result.strip().split('\n')
    
    # Should have 30 total events (3 threads × 10 events)
    assert len(lines) == 30
    
    # Each thread should have contributed events
    thread0_events = [line for line in lines if 'thread-0' in line]
    thread1_events = [line for line in lines if 'thread-1' in line]
    thread2_events = [line for line in lines if 'thread-2' in line]
    
    assert len(thread0_events) == 10
    assert len(thread1_events) == 10
    assert len(thread2_events) == 10