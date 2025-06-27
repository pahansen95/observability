"""
Tests for resource-based handlers.

Validates that ManagedFileHandler, BufferHandler, and QueuedHandler
properly manage resources and lifecycle.
"""

import pytest
import tempfile
import os
import json
import time
import threading
from observability import ObservabilityContext
from observability.handlers import (
    ManagedFileHandler,
    BufferHandler,
    QueuedHandler,
)


def test_resource_handlers():
    """Resource-based handlers manage lifecycle."""
    # File handler
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filepath = tmp.name
    
    file_handler = ManagedFileHandler(filepath, format='json')
    
    # Buffer handler
    buffer = BufferHandler(max_size=100)
    
    # Queued handler wraps file handler
    queued = QueuedHandler(file_handler)
    
    context = ObservabilityContext()
    context.attach_handler(buffer)
    context.attach_handler(queued)
    
    context.start()
    
    # Emit events
    for i in range(5):
        context.emit('test', f'event_{i}')
    
    context.stop()
    
    # Buffer should have all events
    assert len(buffer.get_events()) == 5
    
    # File should have events (after queue drain)
    assert os.path.exists(filepath)
    with open(filepath) as f:
        content = f.read()
        assert 'event_0' in content
    
    os.unlink(filepath)


def test_buffer_handler():
    """BufferHandler stores events in memory."""
    buffer = BufferHandler(max_size=3)
    
    context = ObservabilityContext()
    context.attach_handler(buffer)
    
    context.start()
    
    # Emit events
    context.emit('test', 'event1')
    context.emit('test', 'event2')
    context.emit('test', 'event3')
    
    events = buffer.get_events()
    assert len(events) == 3
    assert events[0]['value'] == 'event1'
    assert events[1]['value'] == 'event2'
    assert events[2]['value'] == 'event3'
    
    # Emit more events - should overflow
    context.emit('test', 'event4')
    context.emit('test', 'event5')
    
    events = buffer.get_events()
    assert len(events) == 3  # Still max_size
    assert buffer.get_overflow_count() == 2
    
    # Clear buffer
    buffer.clear()
    assert len(buffer.get_events()) == 0
    assert buffer.get_overflow_count() == 0  # Reset on clear
    
    context.stop()


def test_buffer_handler_thread_safety():
    """BufferHandler is thread-safe."""
    buffer = BufferHandler(max_size=1000)
    context = ObservabilityContext()
    context.attach_handler(buffer)
    
    def emit_events(thread_id):
        for i in range(100):
            context.emit('test', f'thread{thread_id}_event{i}')
    
    # Start multiple threads
    threads = []
    for i in range(10):
        t = threading.Thread(target=emit_events, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Should have all events (no race conditions)
    events = buffer.get_events()
    assert len(events) == 1000
    assert buffer.get_overflow_count() == 0


def test_managed_file_handler_json():
    """ManagedFileHandler writes JSON format."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filepath = tmp.name
    
    handler = ManagedFileHandler(filepath, format='json')
    
    context = ObservabilityContext()
    context.attach_handler(handler)
    
    context.start()
    
    context.emit('test.event', 'value1', custom='metadata')
    context.emit('test.event', 'value2', count=42)
    
    # Force flush
    handler.flush()
    
    # Read and verify JSON
    with open(filepath) as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    
    event1 = json.loads(lines[0])
    assert event1['type'] == 'test.event'
    assert event1['value'] == 'value1'
    assert event1['custom'] == 'metadata'
    
    event2 = json.loads(lines[1])
    assert event2['value'] == 'value2'
    assert event2['count'] == 42
    
    context.stop()
    os.unlink(filepath)


def test_managed_file_handler_text():
    """ManagedFileHandler writes text format."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filepath = tmp.name
    
    handler = ManagedFileHandler(filepath, format='text')
    
    context = ObservabilityContext()
    context.attach_handler(handler)
    
    context.start()
    
    context.emit('log.info', 'Application started')
    context.emit('log.error', 'Connection failed', retry_count=3)
    
    handler.flush()
    
    # Read and verify text
    with open(filepath) as f:
        content = f.read()
    
    assert 'log.info: Application started' in content
    assert 'log.error: Connection failed' in content
    assert 'retry_count=3' in content
    
    context.stop()
    os.unlink(filepath)


def test_managed_file_handler_auto_flush():
    """ManagedFileHandler auto-flushes based on count."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filepath = tmp.name
    
    # Flush every 2 events
    handler = ManagedFileHandler(filepath, format='text', flush_interval=2)
    
    context = ObservabilityContext()
    context.attach_handler(handler)
    
    context.start()
    
    # First event - no flush yet
    context.emit('test', 'event1')
    with open(filepath) as f:
        content = f.read()
        assert content == ''  # Not flushed yet
    
    # Second event - should trigger flush
    context.emit('test', 'event2')
    with open(filepath) as f:
        content = f.read()
        assert 'event1' in content
        assert 'event2' in content
    
    context.stop()
    os.unlink(filepath)


def test_queued_handler():
    """QueuedHandler processes events asynchronously."""
    events = []
    
    def slow_handler(event):
        time.sleep(0.001)  # Simulate slow processing
        events.append(event['value'])
    
    queued = QueuedHandler(slow_handler, max_queued=10)
    
    context = ObservabilityContext()
    context.attach_handler(queued)
    
    context.start()
    
    # Emit events quickly
    start = time.time()
    for i in range(5):
        context.emit('test', f'event{i}')
    emit_time = time.time() - start
    
    # Emission should be fast (not blocked by slow handler)
    assert emit_time < 0.01  # Should be much less than 5ms
    
    # Wait for processing
    time.sleep(0.01)
    
    # Get stats
    stats = queued.get_stats()
    assert stats['processed'] == 5
    assert stats['dropped'] == 0
    assert stats['queued'] == 0
    
    context.stop()
    
    # All events should be processed
    assert events == ['event0', 'event1', 'event2', 'event3', 'event4']


def test_queued_handler_overflow():
    """QueuedHandler drops events when queue is full."""
    events = []
    block_event = threading.Event()
    
    def blocking_handler(event):
        if event['value'] == 'block':
            block_event.wait()  # Block until released
        events.append(event['value'])
    
    # Small queue that will overflow
    queued = QueuedHandler(blocking_handler, max_queued=3)
    
    context = ObservabilityContext()
    context.attach_handler(queued)
    
    context.start()
    
    # First event blocks the handler
    context.emit('test', 'block')
    time.sleep(0.01)  # Let handler start processing
    
    # Fill the queue
    for i in range(10):
        context.emit('test', f'event{i}')
    
    # Release the block
    block_event.set()
    
    # Let processing complete
    time.sleep(0.05)
    
    stats = queued.get_stats()
    assert stats['dropped'] > 0  # Some events were dropped
    assert stats['processed'] < 11  # Not all events processed
    
    context.stop()


def test_queued_handler_drain_on_stop():
    """QueuedHandler drains queue on stop."""
    events = []
    
    def handler(event):
        events.append(event['value'])
    
    queued = QueuedHandler(handler, drain_on_stop=True)
    
    context = ObservabilityContext()
    context.attach_handler(queued)
    
    context.start()
    
    # Emit events
    for i in range(5):
        context.emit('test', f'event{i}')
    
    # Stop immediately (queue might not be empty)
    context.stop()
    
    # All events should be processed due to drain_on_stop
    assert len(events) == 5


def test_queued_handler_no_drain():
    """QueuedHandler can skip drain on stop."""
    events = []
    process_delay = threading.Event()
    
    def slow_handler(event):
        process_delay.wait()  # Wait for signal
        events.append(event['value'])
    
    queued = QueuedHandler(slow_handler, drain_on_stop=False)
    
    context = ObservabilityContext()
    context.attach_handler(queued)
    
    context.start()
    
    # Emit events
    for i in range(5):
        context.emit('test', f'event{i}')
    
    # Stop without draining
    context.stop()
    
    # Events might not be processed
    assert len(events) < 5
    
    # Signal won't help now - handler is stopped
    process_delay.set()
    time.sleep(0.01)
    assert len(events) < 5


def test_handler_close_method():
    """Handlers with close() method release resources."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filepath = tmp.name
    
    handler = ManagedFileHandler(filepath, format='text')
    
    context = ObservabilityContext()
    context.attach_handler(handler)
    
    context.start()
    context.emit('test', 'event')
    
    # Close should release file handle
    handler.close()
    
    # File should still exist with content
    assert os.path.exists(filepath)
    with open(filepath) as f:
        assert 'event' in f.read()
    
    os.unlink(filepath)