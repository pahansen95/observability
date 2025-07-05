"""
Tests for JsonHandler implementation.

Validates that JsonHandler properly serializes events as JSON
with configurable formatting options and stream handling.
"""

import io
import json
import pytest
from observability.handlers import JsonHandler
from observability.types import EventDict


def test_json_handler_basic_serialization():
    """JsonHandler serializes events as JSON with default settings."""
    output = io.StringIO()
    handler = JsonHandler(output)
    
    event: EventDict = {
        'type': 'log.info',
        'value': 'Application started',
        'timestamp_ns': 1609459200000000000
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    parsed = json.loads(result)
    
    assert parsed['type'] == 'log.info'
    assert parsed['value'] == 'Application started'
    assert parsed['timestamp_ns'] == 1609459200000000000


def test_json_handler_pretty_printing():
    """JsonHandler supports pretty printing with indentation."""
    output = io.StringIO()
    handler = JsonHandler(output, pretty=True)
    
    event: EventDict = {
        'type': 'test',
        'value': 'data',
        'nested': {'key': 'value', 'count': 42}
    }
    
    handler(event)
    
    result = output.getvalue()
    # Should contain newlines and indentation when pretty=True
    assert '\n' in result
    assert '  ' in result  # Indentation
    
    # Should still be valid JSON
    parsed = json.loads(result)
    assert parsed['type'] == 'test'
    assert parsed['nested']['key'] == 'value'


def test_json_handler_compact_output():
    """JsonHandler produces compact JSON by default."""
    output = io.StringIO()
    handler = JsonHandler(output, pretty=False)
    
    event: EventDict = {
        'type': 'test',
        'value': 'data',
        'nested': {'key': 'value'}
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    # Should not contain extra whitespace
    assert result.count('\n') == 0  # No internal newlines
    assert result.count('  ') == 0  # No indentation
    
    # Should still be valid JSON
    parsed = json.loads(result)
    assert parsed['type'] == 'test'


def test_json_handler_indent_parameter():
    """JsonHandler supports custom indentation levels."""
    output = io.StringIO()
    handler = JsonHandler(output, indent=4)
    
    event: EventDict = {
        'type': 'test',
        'nested': {'key': 'value'}
    }
    
    handler(event)
    
    result = output.getvalue()
    # Should use 4-space indentation
    assert '    ' in result  # 4 spaces
    assert '  ' in result    # But not just 2 spaces at top level
    
    # Should be valid JSON
    parsed = json.loads(result)
    assert parsed['type'] == 'test'


def test_json_handler_sort_keys():
    """JsonHandler supports key sorting for consistent output."""
    output = io.StringIO()
    handler = JsonHandler(output, sort_keys=True)
    
    event: EventDict = {
        'zebra': 'last',
        'alpha': 'first',
        'beta': 'middle'
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    parsed = json.loads(result)
    
    # Keys should be sorted alphabetically
    keys = list(parsed.keys())
    assert keys == ['alpha', 'beta', 'zebra']


def test_json_handler_ensure_ascii():
    """JsonHandler controls ASCII encoding behavior."""
    # Test with ensure_ascii=True (default)
    output_ascii = io.StringIO()
    handler_ascii = JsonHandler(output_ascii, ensure_ascii=True)
    
    event: EventDict = {
        'type': 'test.unicode',
        'value': 'Hello 世界 🌍'
    }
    
    handler_ascii(event)
    result_ascii = output_ascii.getvalue().strip()
    
    # Should escape non-ASCII characters
    assert '\\u' in result_ascii
    
    # Test with ensure_ascii=False
    output_unicode = io.StringIO()
    handler_unicode = JsonHandler(output_unicode, ensure_ascii=False)
    
    handler_unicode(event)
    result_unicode = output_unicode.getvalue().strip()
    
    # Should preserve Unicode characters
    assert '世界' in result_unicode
    assert '🌍' in result_unicode


def test_json_handler_complex_data_types():
    """JsonHandler handles complex data types using str() conversion."""
    from datetime import datetime
    
    output = io.StringIO()
    handler = JsonHandler(output)
    
    # Test with various complex types
    event: EventDict = {
        'type': 'test.complex',
        'datetime': datetime(2021, 1, 1, 12, 0, 0),
        'set_data': {1, 2, 3},  # Sets are not JSON serializable
        'bytes_data': b'binary data',
        'none_value': None,
        'nested': {'inner': datetime(2021, 1, 1)}
    }
    
    handler(event)
    
    result = output.getvalue().strip()
    parsed = json.loads(result)
    
    # Complex types should be converted to strings
    assert isinstance(parsed['datetime'], str)
    assert isinstance(parsed['set_data'], str)
    assert isinstance(parsed['bytes_data'], str)
    assert parsed['none_value'] is None  # None should remain None
    assert isinstance(parsed['nested']['inner'], str)


def test_json_handler_multiple_events():
    """JsonHandler handles multiple events with proper separation."""
    output = io.StringIO()
    handler = JsonHandler(output)
    
    events = [
        {'type': 'event1', 'value': 'first'},
        {'type': 'event2', 'value': 'second'},
        {'type': 'event3', 'value': 'third'}
    ]
    
    for event in events:
        handler(event)
    
    result = output.getvalue()
    lines = result.strip().split('\n')
    
    # Should have one JSON object per line
    assert len(lines) == 3
    
    # Each line should be valid JSON
    for i, line in enumerate(lines):
        parsed = json.loads(line)
        assert parsed['type'] == f'event{i+1}'
        assert parsed['value'] == ['first', 'second', 'third'][i]


def test_json_handler_stream_flushing():
    """JsonHandler flushes output after each event."""
    
    class FlushTrackingStream(io.StringIO):
        def __init__(self):
            super().__init__()
            self.flush_count = 0
        
        def flush(self):
            self.flush_count += 1
            super().flush()
    
    output = FlushTrackingStream()
    handler = JsonHandler(output)
    
    event: EventDict = {'type': 'test', 'value': 'data'}
    
    initial_flush_count = output.flush_count
    handler(event)
    
    # Should flush after each event
    assert output.flush_count > initial_flush_count


def test_json_handler_parameter_precedence():
    """JsonHandler parameter precedence: indent takes precedence over pretty."""
    
    # Test indent=0 sets pretty=False (since indent > 0 is False)
    output1 = io.StringIO()
    handler1 = JsonHandler(output1, pretty=True, indent=0)
    
    event = {'type': 'test', 'nested': {'key': 'value'}}
    handler1(event)
    result1 = output1.getvalue()
    
    # Should be compact (indent=0 means pretty=False)
    assert handler1.pretty is False
    assert handler1.indent == 0
    
    # Test indent=4 overrides pretty=False  
    output2 = io.StringIO()
    handler2 = JsonHandler(output2, pretty=False, indent=4)
    
    handler2(event)
    result2 = output2.getvalue()
    
    # Should be formatted despite pretty=False
    assert handler2.pretty is True  # indent > 0 sets pretty=True
    assert '    ' in result2  # 4-space indentation


def test_json_handler_newline_behavior():
    """JsonHandler adds newlines after each JSON object."""
    output = io.StringIO()
    handler = JsonHandler(output)
    
    events = [
        {'type': 'line1'},
        {'type': 'line2'}
    ]
    
    for event in events:
        handler(event)
    
    result = output.getvalue()
    # Should end with newline and have proper line separation
    assert result.endswith('\n')
    lines = result.strip().split('\n')
    assert len(lines) == 2


def test_json_handler_error_handling():
    """JsonHandler handles serialization errors gracefully."""
    import sys
    from io import StringIO
    
    output = io.StringIO()
    handler = JsonHandler(output)
    
    # Create an event with truly unserializable data
    class UnserializableObject:
        def __str__(self):
            raise ValueError("Cannot convert to string")
    
    event: EventDict = {
        'type': 'test',
        'bad_data': UnserializableObject()
    }
    
    # Capture stderr to check for error message
    old_stderr = sys.stderr
    stderr_capture = StringIO()
    sys.stderr = stderr_capture
    
    try:
        handler(event)
        
        # Should handle error gracefully
        stderr_output = stderr_capture.getvalue()
        assert "JSON handler error:" in stderr_output
        
    finally:
        sys.stderr = old_stderr


def test_json_handler_stream_error_handling():
    """JsonHandler handles stream write errors appropriately."""
    import sys
    from io import StringIO
    
    class FailingStream:
        def write(self, data):
            raise IOError("Stream write failed")
        
        def flush(self):
            pass
    
    failing_output = FailingStream()
    handler = JsonHandler(failing_output)
    
    event: EventDict = {'type': 'test', 'value': 'data'}
    
    # Capture stderr
    old_stderr = sys.stderr
    stderr_capture = StringIO()
    sys.stderr = stderr_capture
    
    try:
        handler(event)
        
        # Should handle stream errors gracefully
        stderr_output = stderr_capture.getvalue()
        assert "JSON handler error:" in stderr_output
        assert "Stream write failed" in stderr_output
        
    finally:
        sys.stderr = old_stderr


def test_json_handler_thread_safety():
    """JsonHandler is thread-safe when underlying stream is thread-safe."""
    import threading
    import time
    
    output = io.StringIO()
    handler = JsonHandler(output)
    
    def write_events(thread_id):
        for i in range(10):
            event = {'thread': f'thread-{thread_id}', 'event': f'event-{i}'}
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
    
    # Each line should be valid JSON
    parsed_events = []
    for line in lines:
        parsed = json.loads(line)
        parsed_events.append(parsed)
    
    # Each thread should have contributed 10 events
    thread0_events = [e for e in parsed_events if e['thread'] == 'thread-0']
    thread1_events = [e for e in parsed_events if e['thread'] == 'thread-1']
    thread2_events = [e for e in parsed_events if e['thread'] == 'thread-2']
    
    assert len(thread0_events) == 10
    assert len(thread1_events) == 10
    assert len(thread2_events) == 10


@pytest.mark.asyncio
async def test_json_handler_lifecycle():
    """JsonHandler supports proper lifecycle management."""
    output = io.StringIO()
    handler = JsonHandler(output)
    
    # Should start in uninitialized state
    assert not handler._is_initialized
    
    # Initialize
    await handler.initialize()
    assert handler._is_initialized
    
    # Should process events when initialized
    event: EventDict = {'type': 'test', 'value': 'data'}
    handler(event)
    
    result = output.getvalue()
    assert result.strip()
    parsed = json.loads(result.strip())
    assert parsed['type'] == 'test'
    
    # Shutdown
    await handler.shutdown()
    assert not handler._is_initialized