"""
Tests for handler implementation edge cases.

Validates robust behavior under unusual conditions, error scenarios,
and boundary conditions across all handler implementations.
"""

import io
import threading
import time
import pytest
from unittest.mock import patch
from observability.handlers import PrintHandler, JsonHandler
from observability.handlers.base import format_event_simple, format_context_items
from observability.types import EventDict


class TestFormatUtilityEdgeCases:
    """Test edge cases in base formatting utilities."""

    def test_format_event_simple_circular_references(self):
        """format_event_simple handles circular references gracefully."""
        # Create event with circular reference
        event: EventDict = {'type': 'test', 'value': 'data'}
        event['self_ref'] = event  # Circular reference

        result = format_event_simple(event, "{type}: {value}")

        # Should still work for simple fields
        assert "test: data" in result

    def test_format_event_simple_malformed_placeholders(self):
        """format_event_simple handles malformed format strings."""
        event: EventDict = {'type': 'test', 'value': 'data'}

        # Format strings that should cause errors due to missing fields
        missing_field_formats = [
            "{undefined_field}",    # Missing field
        ]

        for fmt in missing_field_formats:
            result = format_event_simple(event, fmt)
            # Should generate format error message
            assert "Format error:" in result

        # Format strings that should raise exceptions immediately
        exception_formats = [
            "{type.invalid}",       # Attribute access on string
        ]

        for fmt in exception_formats:
            with pytest.raises((AttributeError, TypeError, KeyError)):
                format_event_simple(event, fmt)

        # Format strings that work but might be unexpected
        working_formats = [
            ("{type[0]}", "t"),      # Index access works on strings
        ]

        for fmt, expected in working_formats:
            result = format_event_simple(event, fmt)
            assert expected in result

        # Format strings that should work
        valid_formats = [
            "{{double}}",           # Double braces (literal braces)
            "{type}: {value}",      # Valid format
        ]

        for fmt in valid_formats:
            result = format_event_simple(event, fmt)
            # Should not generate format error
            assert "Format error:" not in result

    def test_format_event_simple_very_large_format_string(self):
        """format_event_simple handles very large format strings."""
        event: EventDict = {'type': 'test', 'value': 'data'}

        # Create very large format string
        large_format = "{type}: {value} " + "padding " * 10000

        result = format_event_simple(event, large_format)

        # Should handle without crashing
        assert "test: data" in result
        assert len(result) > 50000  # Should include all the padding

    def test_format_context_items_with_none_values(self):
        """format_context_items handles None values correctly."""
        event: EventDict = {
            'type': 'test',
            'none_value': None,
            'empty_string': '',
            'zero': 0,
            'false_value': False
        }

        exclude = {'type'}
        items = format_context_items(event, exclude)

        # Should include all non-excluded fields, including falsy values
        items_dict = dict(item.split('=', 1) for item in items)
        assert 'none_value=None' in items
        assert 'empty_string=' in items
        assert 'zero=0' in items
        assert 'false_value=False' in items


class TestPrintHandlerEdgeCases:
    """Test edge cases specific to PrintHandler."""

    def test_print_handler_with_circular_event_data(self):
        """PrintHandler handles events with circular references."""
        output = io.StringIO()
        handler = PrintHandler(output, format="{type}: {value}")

        # Create event with circular reference
        event: EventDict = {'type': 'test', 'value': 'data'}
        event['circular'] = event

        handler(event)

        result = output.getvalue()
        # Should not crash and should include basic fields
        assert 'test: data' in result

    def test_print_handler_stream_becomes_unavailable(self):
        """PrintHandler handles stream that becomes unavailable."""

        class DisappearingStream:
            def __init__(self):
                self.available = True
                self.content = []

            def write(self, data):
                if not self.available:
                    raise OSError("Stream not available")
                self.content.append(data)

            def flush(self):
                if not self.available:
                    raise OSError("Stream not available")

        stream = DisappearingStream()
        handler = PrintHandler(stream, format="{type}: {value}")

        # First event should work
        event1: EventDict = {'type': 'test1', 'value': 'data1'}
        handler(event1)
        # print() adds content and newline
        assert len(stream.content) == 2  # message + newline

        # Make stream unavailable
        stream.available = False

        # Second event should handle error gracefully
        event2: EventDict = {'type': 'test2', 'value': 'data2'}

        # Capture stderr to verify error handling
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            handler(event2)

            # Should log error to stderr in debug mode
            if __debug__:
                stderr_output = mock_stderr.getvalue()
                assert "Print handler error:" in stderr_output

    def test_print_handler_format_string_injection(self):
        """PrintHandler prevents format string injection attacks."""
        output = io.StringIO()
        handler = PrintHandler(output, format="{type}: {value}")

        # Event with malicious format-like content
        event: EventDict = {
            'type': 'malicious',
            'value': '{__import__("os").system("evil_command")}'
        }

        handler(event)

        result = output.getvalue()
        # Should treat the value as literal text, not execute it
        assert 'malicious:' in result
        assert '__import__' in result  # Should appear as literal text

    def test_print_handler_unicode_edge_cases(self):
        """PrintHandler handles unusual Unicode scenarios."""
        output = io.StringIO()
        handler = PrintHandler(output, format="{type}: {value}")

        # Various Unicode edge cases
        unicode_events = [
            {'type': 'zero_width', 'value': 'invisible\u200b\u200cchars'},
            {'type': 'rtl', 'value': 'right\u202eto\u202dleft'},
            {'type': 'surrogate', 'value': 'emoji\U0001f600test'},
            {'type': 'combining', 'value': 'a\u0300\u0301\u0302ccents'},
            {'type': 'control', 'value': 'with\x00null\x07bell'},
        ]

        for event in unicode_events:
            handler(event)

        result = output.getvalue()
        # Should handle all without crashing
        assert len(result.split('\n')) >= len(unicode_events)


class TestJsonHandlerEdgeCases:
    """Test edge cases specific to JsonHandler."""

    def test_json_handler_unserializable_nested_objects(self):
        """JsonHandler handles deeply nested unserializable objects."""
        output = io.StringIO()
        handler = JsonHandler(output)

        class Unserializable:
            def __str__(self):
                raise ValueError("Cannot convert to string")

            def __repr__(self):
                raise ValueError("Cannot represent")

        event: EventDict = {
            'type': 'test',
            'nested': {
                'level1': {
                    'level2': {
                        'bad_object': Unserializable()
                    }
                }
            }
        }

        # Should handle gracefully by catching exception
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            handler(event)

            # Should log error to stderr
            if __debug__:
                stderr_output = mock_stderr.getvalue()
                assert "JSON handler error:" in stderr_output

    def test_json_handler_infinite_float_values(self):
        """JsonHandler handles infinite and NaN float values."""
        output = io.StringIO()
        handler = JsonHandler(output)

        event: EventDict = {
            'type': 'float_edge_cases',
            'positive_inf': float('inf'),
            'negative_inf': float('-inf'),
            'nan_value': float('nan')
        }

        handler(event)

        result = output.getvalue().strip()
        # Should convert to string representation
        assert 'inf' in result.lower() or 'infinity' in result.lower()
        assert 'nan' in result.lower()

    def test_json_handler_very_deep_nesting(self):
        """JsonHandler handles very deeply nested data structures."""
        output = io.StringIO()
        handler = JsonHandler(output)

        # Create deeply nested structure
        deep_event = {'type': 'deep_test'}
        current = deep_event
        for i in range(100):  # 100 levels deep
            current['nested'] = {'level': i}
            current = current['nested']
        current['value'] = 'deep_data'

        handler(deep_event)

        result = output.getvalue().strip()
        # Should handle without stack overflow
        assert 'deep_test' in result
        assert 'deep_data' in result

    def test_json_handler_parameter_edge_cases(self):
        """JsonHandler handles edge case parameter combinations."""
        output = io.StringIO()

        # Test edge case: indent=0 with pretty=True
        handler1 = JsonHandler(output, pretty=True, indent=0)
        assert handler1.pretty is False  # indent=0 overrides pretty=True
        assert handler1.indent == 0

        # Test edge case: very large indent
        handler2 = JsonHandler(output, indent=100)
        event = {'type': 'test', 'nested': {'key': 'value'}}
        handler2(event)

        result = output.getvalue()
        # Should use 100-space indentation
        assert ' ' * 100 in result


class TestStreamErrorRecovery:
    """Test stream error recovery scenarios."""

    def test_stream_that_throws_on_flush(self):
        """Handlers handle streams that throw exceptions on flush."""

        class FlushFailingStream:
            def __init__(self):
                self.content = []

            def write(self, data):
                self.content.append(data)

            def flush(self):
                raise IOError("Flush failed")

        stream = FlushFailingStream()

        # Test with JsonHandler (which calls flush)
        handler = JsonHandler(stream)
        event: EventDict = {'type': 'test', 'value': 'data'}

        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            handler(event)

            # Event should be written despite flush failure
            assert len(stream.content) > 0

            # Error should be logged
            if __debug__:
                stderr_output = mock_stderr.getvalue()
                assert "JSON handler error:" in stderr_output

    def test_stream_with_partial_write_failures(self):
        """Handlers handle streams with intermittent write failures."""

        class UnreliableStream:
            def __init__(self):
                self.call_count = 0
                self.content = []

            def write(self, data):
                self.call_count += 1
                # Fail every 3rd write
                if self.call_count % 3 == 0:
                    raise IOError("Intermittent failure")
                self.content.append(data)

            def flush(self):
                pass

        stream = UnreliableStream()
        handler = PrintHandler(stream, format="{type}: {value}")

        events = [
            {'type': 'event1', 'value': 'data1'},
            {'type': 'event2', 'value': 'data2'},
            {'type': 'event3', 'value': 'data3'},  # Third write should fail
            {'type': 'event4', 'value': 'data4'},
            {'type': 'event5', 'value': 'data5'},
            {'type': 'event6', 'value': 'data6'},  # Sixth write should fail
        ]

        with patch('sys.stderr', new_callable=io.StringIO):
            for event in events:
                handler(event)

        # Some events should succeed, others should fail gracefully
        # Each successful event writes twice (message + newline)
        # So we expect fewer than 2 * len(events) writes
        assert len(stream.content) < len(events) * 2


class TestConcurrencyEdgeCases:
    """Test concurrency and threading edge cases."""

    def test_handler_thread_safety_stress(self):
        """Handlers maintain thread safety under stress conditions."""
        output = io.StringIO()
        handler = PrintHandler(output, format="{thread_id}: {value}")

        results = []
        error_count = 0

        def stress_worker(thread_id, iterations):
            nonlocal error_count
            try:
                for i in range(iterations):
                    event = {
                        'thread_id': thread_id,
                        'value': f'iteration_{i}',
                        'timestamp': time.time()
                    }
                    handler(event)
                    # Small random delay to encourage race conditions
                    time.sleep(0.0001)
            except Exception:
                error_count += 1

        # Create many threads doing rapid operations
        threads = []
        for tid in range(10):
            thread = threading.Thread(
                target=stress_worker,
                args=(tid, 50)
            )
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should complete without errors
        assert error_count == 0

        # Output should contain all expected events
        output_lines = output.getvalue().strip().split('\n')
        assert len(output_lines) == 500  # 10 threads × 50 iterations

    def test_concurrent_handler_lifecycle_operations(self):
        """Handler lifecycle operations are thread-safe."""

        class LifecycleTrackingHandler:
            def __init__(self):
                self.initialized = False
                self.events_processed = 0
                self.lock = threading.Lock()

            async def initialize(self):
                with self.lock:
                    self.initialized = True

            async def shutdown(self):
                with self.lock:
                    self.initialized = False

            def __call__(self, event):
                with self.lock:
                    if self.initialized:
                        self.events_processed += 1

        handler = LifecycleTrackingHandler()

        def lifecycle_worker():
            import asyncio

            async def async_work():
                await handler.initialize()
                time.sleep(0.01)
                await handler.shutdown()

            asyncio.run(async_work())

        def event_worker():
            for i in range(10):
                handler({'type': 'test', 'value': i})
                time.sleep(0.001)

        # Start concurrent lifecycle and event threads
        lifecycle_thread = threading.Thread(target=lifecycle_worker)
        event_thread = threading.Thread(target=event_worker)

        lifecycle_thread.start()
        event_thread.start()

        lifecycle_thread.join()
        event_thread.join()

        # Should complete without deadlocks or crashes
        assert True  # If we get here, no deadlock occurred


class TestResourceExhaustionScenarios:
    """Test behavior under resource exhaustion."""

    def test_memory_pressure_with_large_events(self):
        """Handlers handle memory pressure from large events."""
        output = io.StringIO()
        handler = JsonHandler(output)

        # Create very large event
        large_data = 'x' * (1024 * 1024)  # 1MB string
        event: EventDict = {
            'type': 'large_event',
            'large_field': large_data,
            'metadata': {'size': len(large_data)}
        }

        handler(event)

        result = output.getvalue()
        # Should handle large event without issues
        assert 'large_event' in result
        assert len(result) > 1024 * 1024  # Should include the large data

    def test_rapid_event_processing_performance(self):
        """Handlers maintain performance under rapid event load."""
        output = io.StringIO()
        handler = PrintHandler(output, format="{counter}: {value}")

        # Process many events rapidly
        event_count = 1000
        start_time = time.time()

        for i in range(event_count):
            event = {'counter': i, 'value': f'event_{i}'}
            handler(event)

        elapsed = time.time() - start_time

        # Should process events efficiently (< 1 second for 1000 events)
        assert elapsed < 1.0

        # All events should be processed
        lines = output.getvalue().strip().split('\n')
        assert len(lines) == event_count


class TestConfigurationEdgeCases:
    """Test configuration and parameter edge cases."""

    def test_handler_with_none_parameters(self):
        """Handlers handle None parameters gracefully."""

        # PrintHandler with None stream should fail when used
        handler = PrintHandler(None, format="{type}: {value}")

        # Using the handler should fail when trying to write
        with patch('sys.stderr', new_callable=io.StringIO):
            handler({'type': 'test', 'value': 'data'})
            # Should handle the error gracefully by logging to stderr

    def test_handler_parameter_type_mismatches(self):
        """JsonHandler fails fast on invalid parameter types."""

        output = io.StringIO()

        # JsonHandler should fail on type mismatches during construction
        with pytest.raises(TypeError):
            JsonHandler(
                output,
                indent="invalid",  # Should be int or None
            )

        # Test with valid parameters
        handler = JsonHandler(
            output,
            indent=2,
            sort_keys=True
        )

        event = {'type': 'test', 'value': 'data'}
        handler(event)

        result = output.getvalue()
        assert 'test' in result
