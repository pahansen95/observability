"""
Tests for observability configuration.

Validates ObservabilityConfig and SharedContext functionality.
"""

import pytest
import sys
import io
from observability import (
    ObservabilityContext,
    ObservabilityConfig,
    SharedContext,
    PrintHandler,
    JsonHandler,
)


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


def test_config_validation():
    """Configuration validates parameters."""
    # Valid configs
    ObservabilityConfig(sampling_rate=0.0)
    ObservabilityConfig(sampling_rate=0.5)
    ObservabilityConfig(sampling_rate=1.0)
    
    # Invalid sampling rates
    with pytest.raises(ValueError):
        ObservabilityConfig(sampling_rate=-0.1)
    
    with pytest.raises(ValueError):
        ObservabilityConfig(sampling_rate=1.1)


def test_config_with_multiple_handlers():
    """Configuration can have multiple handlers."""
    events1 = []
    events2 = []
    
    config = ObservabilityConfig(
        handlers=[
            lambda e: events1.append(e),
            lambda e: events2.append(e),
        ]
    )
    
    context = ObservabilityContext(config)
    context.emit('test', 'value')
    
    assert len(events1) == 1
    assert len(events2) == 1


def test_config_immutable():
    """Configuration is immutable after creation."""
    handler = lambda e: None
    config = ObservabilityConfig(handlers=[handler])
    
    # Should not be able to modify handlers list
    with pytest.raises(AttributeError):
        config.handlers = []
    
    # The list itself is still mutable (Python limitation)
    # but this doesn't affect the context since it copies during init


def test_shared_context():
    """SharedContext provides singleton access."""
    events = []
    config = ObservabilityConfig(handlers=[lambda e: events.append(e)])
    
    # Reset for test
    SharedContext._ctx = None
    SharedContext.setup(config)
    
    # Get context
    ctx = SharedContext.get()
    assert ctx is not None
    
    # Should be same instance
    assert SharedContext.get() is ctx
    
    # Can emit through context
    ctx.emit('test', 'value')
    assert len(events) == 1
    
    # Cleanup
    SharedContext.teardown()


def test_shared_context_lazy_binding():
    """SharedContext supports lazy binding pattern."""
    from observability.domains.logging import Logger
    
    events = []
    
    # Create logger with lazy binding before context exists
    logger = Logger('service', SharedContext.get_context)
    
    # Now setup context
    config = ObservabilityConfig(handlers=[lambda e: events.append(e)])
    SharedContext._ctx = None
    SharedContext.setup(config)
    
    # Logger should work
    logger.info("Using shared context")
    
    assert len(events) == 1
    assert events[0]['value'] == "Using shared context"
    
    SharedContext.teardown()


def test_shared_context_direct_emit():
    """SharedContext provides direct emit method."""
    events = []
    config = ObservabilityConfig(handlers=[lambda e: events.append(e)])
    
    SharedContext._ctx = None
    SharedContext.setup(config)
    
    # Direct emit
    SharedContext.emit('custom', 'event')
    
    assert len(events) == 1
    assert events[0]['type'] == 'custom'
    
    SharedContext.teardown()


def test_shared_context_attach_handler():
    """SharedContext allows attaching handlers after setup."""
    events1 = []
    events2 = []
    
    config = ObservabilityConfig(handlers=[lambda e: events1.append(e)])
    
    SharedContext._ctx = None
    SharedContext.setup(config)
    
    # Attach additional handler
    SharedContext.attach_handler(lambda e: events2.append(e))
    
    SharedContext.emit('test', 'value')
    
    assert len(events1) == 1
    assert len(events2) == 1
    
    SharedContext.teardown()


def test_shared_context_not_initialized():
    """SharedContext raises error when not initialized."""
    SharedContext._ctx = None
    
    with pytest.raises(RuntimeError, match="not initialized"):
        SharedContext.get()
    
    with pytest.raises(RuntimeError, match="not initialized"):
        SharedContext.emit('test', 'value')


def test_shared_context_default_config():
    """SharedContext uses sensible defaults when no config provided."""
    output = io.StringIO()
    
    # Monkey-patch stderr for test
    old_stderr = sys.stderr
    sys.stderr = output
    
    try:
        SharedContext._ctx = None
        SharedContext.setup()  # No config provided
        
        # Should have default handler
        SharedContext.emit('test', 'value')
        
        output_str = output.getvalue()
        assert 'test: value' in output_str
        
    finally:
        sys.stderr = old_stderr
        SharedContext.teardown()


def test_shared_context_lifecycle():
    """SharedContext manages handler lifecycle."""
    lifecycle = []
    
    class ManagedHandler:
        def start(self):
            lifecycle.append('started')
        def stop(self):
            lifecycle.append('stopped')
        def __call__(self, event):
            lifecycle.append('called')
    
    config = ObservabilityConfig(handlers=[ManagedHandler()])
    
    SharedContext._ctx = None
    SharedContext.setup(config)  # Should auto-start
    
    assert 'started' in lifecycle
    
    SharedContext.emit('test', 'value')
    assert 'called' in lifecycle
    
    SharedContext.teardown()
    assert 'stopped' in lifecycle


def test_shared_context_reinitialization():
    """SharedContext can be re-initialized with new config."""
    events1 = []
    events2 = []
    
    # First initialization
    config1 = ObservabilityConfig(handlers=[lambda e: events1.append(e)])
    SharedContext._ctx = None
    SharedContext.setup(config1)
    
    SharedContext.emit('test', 'event1')
    assert len(events1) == 1
    
    # Re-initialize with new config
    config2 = ObservabilityConfig(handlers=[lambda e: events2.append(e)])
    SharedContext.setup(config2)
    
    SharedContext.emit('test', 'event2')
    assert len(events1) == 1  # Old handler not called
    assert len(events2) == 1  # New handler called
    
    SharedContext.teardown()


def test_config_enabled_categories():
    """Configuration respects enabled_categories."""
    events = []
    
    # Only allow specific categories
    config = ObservabilityConfig(
        handlers=[lambda e: events.append(e)],
        enabled_categories={'log', 'custom'}
    )
    
    context = ObservabilityContext(config)
    
    # These should pass
    context.emit('log.info', 'pass1')
    context.emit('log.error', 'pass2')
    context.emit('custom.event', 'pass3')
    
    # These should be filtered
    context.emit('metric.counter', 'blocked1')
    context.emit('trace.span', 'blocked2')
    
    assert len(events) == 3
    values = [e['value'] for e in events]
    assert 'pass1' in values
    assert 'pass2' in values
    assert 'pass3' in values