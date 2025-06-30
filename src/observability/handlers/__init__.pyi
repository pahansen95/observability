# ruff: noqa: F811
"""
Event handlers for the observability pipeline.

Handlers consume events from the observability pipeline, producing side effects
like formatted output, storage, or transmission. They form a tree-based dispatch
system where events flow from root to leaves through control nodes.

Handlers are organized into three categories:
- Sink Handlers: Terminal consumers that perform I/O operations
- Control Handlers: Modify execution flow without consuming events  
- Composite Handlers: Coordinate multiple handlers for complex patterns

All handlers implement the EventHandler protocol, accepting EventDict instances
and performing their specific processing logic.

## Quick Start
    from observability import ObservabilityContext, ObservabilityConfig
    from observability.handlers import JsonHandler, filtered, ManagedFileHandler
    import sys
    
    # Create handler pipeline
    error_handler = filtered(
        lambda e: e.get('severity', 0) >= 40,
        ManagedFileHandler('errors.log')
    )
    
    config = ObservabilityConfig(handlers=[
        JsonHandler(sys.stderr),
        error_handler
    ])
    context = ObservabilityContext(config)
    context.start()

## Mental Model
Events propagate through handler trees:

    Event → Root
             ├─→ Filter(severity >= ERROR) → FileHandler("errors.log")
             ├─→ Sample(0.01) → NetworkHandler("metrics.local")
             └─→ Queue(10000) → BufferHandler(size=1000)

Control handlers wrap other handlers to modify behavior, while composite
handlers coordinate multiple child handlers for fan-out or failover patterns.
"""

from __future__ import annotations
from typing import Optional, List, IO, Protocol, Callable, Any
from pathlib import Path
from ..types import EventDict, EventHandler

# =============================================================================
# API Type Aliases, Protocols, Enums
# =============================================================================

HandlerChain = List[EventHandler]
HandlerPredicate = Callable[[EventDict], bool]

class LifecycleHandler(Protocol):
    """Handler with managed lifecycle operations."""
    def start(self) -> None: ...
    def stop(self) -> None: ...

class ManagedHandler(EventHandler, LifecycleHandler, Protocol):
    """Complete managed handler contract combining event handling and lifecycle."""
    pass

# =============================================================================
# API Core Types & Functionality
# =============================================================================

class PrintHandler:
    """
    Human-readable event output to text streams.
    
    Formats events as single-line text records suitable for console output
    or log files. Supports custom format strings with event field interpolation
    and optional context field inclusion.
    
    The handler writes synchronously to the provided stream with automatic
    flushing after each event. Thread-safe when the underlying stream is
    thread-safe.
    
    Args:
        stream: Text output stream (e.g., sys.stdout, file handle)
        format: Format string with {field} placeholders. Defaults to
                "{timestamp} {type}: {value}"
        include_context: Whether to append trace/request/operation IDs.
                        Defaults to False.
    
    Example:
        >>> handler = PrintHandler(sys.stdout, format="{type}: {value}")
        >>> handler({'type': 'log', 'value': 'Hello', 'timestamp': '2024-01-01T00:00:00Z'})
        log: Hello
        
    Note:
        Format strings can reference any EventDict field. Missing fields
        are rendered as empty strings. Special handling exists for timestamp
        formatting to human-readable ISO format.
    """
    
    def __init__(
        self, 
        stream: IO[str], 
        *, 
        format: str = "{timestamp} {type}: {value}", 
        include_context: bool = False
    ) -> None: ...
    
    def __call__(self, event: EventDict) -> None: ...

class JsonHandler:
    """
    Structured JSON event serialization.
    
    Outputs events as JSON objects, one per line (JSONL format), suitable
    for structured logging systems and machine processing. Preserves all
    event fields with configurable formatting options.
    
    The handler writes synchronously with automatic flushing. Thread-safe
    when the underlying stream is thread-safe.
    
    Args:
        stream: Text output stream for JSON data
        indent: JSON indentation level. None for compact output.
        sort_keys: Whether to sort object keys. Defaults to False.
    
    Example:
        >>> handler = JsonHandler(sys.stderr)
        >>> handler({'type': 'metric', 'name': 'latency', 'value': 0.123})
        {"type": "metric", "name": "latency", "value": 0.123}
    """
    
    def __init__(
        self, 
        stream: IO[str], 
        *, 
        indent: Optional[int] = None, 
        sort_keys: bool = False
    ) -> None: ...
    
    def __call__(self, event: EventDict) -> None: ...

class ManagedFileHandler:
    """
    Persistent file storage with lifecycle management.
    
    Writes events as JSON lines to rotating log files with configurable size
    limits and backup retention. Implements proper resource management through
    start/stop lifecycle methods.
    
    File rotation occurs when max_bytes is exceeded. Old files are renamed
    with numeric suffixes (.1, .2, etc.) up to backup_count. Thread-safe
    with internal locking.
    
    Args:
        filepath: Output file path (absolute or relative)
        max_bytes: Maximum file size before rotation. 0 disables rotation.
        backup_count: Number of backup files to keep. 0 keeps no backups.
        encoding: File encoding. Defaults to "utf-8".
    
    Example:
        >>> handler = ManagedFileHandler(
        ...     'app.log',
        ...     max_bytes=10*1024*1024,  # 10MB
        ...     backup_count=5
        ... )
        >>> handler.start()  # Opens file
        >>> handler({'type': 'log', 'message': 'Started'})
        >>> handler.stop()   # Closes file
        
    Note:
        Must call start() before use and stop() when done. The containing
        ObservabilityContext handles this automatically for attached handlers.
    """
    
    def __init__(
        self, 
        filepath: str | Path, 
        *, 
        max_bytes: int = 0, 
        backup_count: int = 0, 
        encoding: str = "utf-8"
    ) -> None: ...
    
    def start(self) -> None:
        """Initialize file resources."""
        ...
    
    def stop(self) -> None:
        """Release file resources."""
        ...
    
    def __call__(self, event: EventDict) -> None: ...

def filtered(predicate: HandlerPredicate, handler: EventHandler) -> EventHandler:
    """
    Create conditional event processor.
    
    Wraps a handler with a filtering predicate, only forwarding events that
    match the condition. Useful for routing specific event types or severities
    to specialized handlers.
    
    The predicate is called for each event before the handler. False results
    skip the handler entirely with minimal overhead.
    
    Args:
        predicate: Function returning True to forward event, False to skip
        handler: Wrapped handler to conditionally invoke
        
    Returns:
        New handler that filters events
        
    Example:
        >>> # Only errors to file
        >>> error_handler = filtered(
        ...     lambda e: e.get('severity', 0) >= 40,
        ...     ManagedFileHandler('errors.log')
        ... )
        >>> 
        >>> # Only metrics to aggregator
        >>> metric_handler = filtered(
        ...     lambda e: e.get('type') == 'metric',
        ...     MetricsAggregator()
        ... )
    """
    ...

def sampled(rate: float, handler: EventHandler, *, seed: Optional[int] = None) -> EventHandler:
    """
    Create statistical sampling handler.
    
    Randomly samples events at the specified rate, reducing volume while
    maintaining statistical properties. Useful for high-volume telemetry
    or expensive handlers.
    
    Uses thread-safe random sampling with optional deterministic seeding
    for reproducible behavior in tests.
    
    Args:
        rate: Sampling rate between 0.0 and 1.0. 0.1 means 10% of events.
        handler: Wrapped handler for sampled events
        seed: Optional random seed for deterministic sampling
        
    Returns:
        New handler that samples events
        
    Example:
        >>> # Send 1% of events to expensive handler
        >>> sampled_handler = sampled(0.01, NetworkHandler('telemetry.server'))
        >>> 
        >>> # Deterministic sampling for tests
        >>> test_handler = sampled(0.5, BufferHandler(), seed=12345)
    """
    ...

# =============================================================================
# API Supporting Types & Functionality
# =============================================================================

class BufferHandler:
    """
    In-memory event storage for testing and analysis.
    
    Captures events in a thread-safe buffer for later inspection. Useful for
    unit tests, debugging, and temporary event accumulation.
    
    Args:
        max_size: Maximum events to store. None for unlimited.
                 Oldest events are dropped when limit reached.
    """
    
    def __init__(self, max_size: Optional[int] = None) -> None: ...
    
    def __call__(self, event: EventDict) -> None: ...
    
    def get_events(self) -> List[EventDict]:
        """Retrieve captured events (defensive copy)."""
        ...
    
    def clear(self) -> None:
        """Clear event buffer."""
        ...

class QueuedHandler:
    """
    Asynchronous event processing with background worker.
    
    Decouples event emission from handler processing using a queue and worker
    thread. Prevents slow handlers from blocking the emission path.
    
    Args:
        wrapped_handler: Handler to run in background thread
        queue_size: Maximum queued events before blocking
        timeout: Queue put timeout in seconds. None blocks forever.
    """
    
    def __init__(
        self, 
        wrapped_handler: EventHandler, 
        *, 
        queue_size: int = 10000, 
        timeout: Optional[float] = None
    ) -> None: ...
    
    def start(self) -> None:
        """Initialize worker thread."""
        ...
    
    def stop(self) -> None:
        """Terminate worker thread gracefully."""
        ...
    
    def __call__(self, event: EventDict) -> None: ...

class TimeDeltaHandler:
    """
    Event enrichment with time delta measurements.
    
    Adds time_delta_ns field showing nanoseconds since previous event.
    Useful for performance analysis and event timing patterns.
    
    Args:
        wrapped_handler: Handler to receive enriched events
    """
    
    def __init__(self, wrapped_handler: EventHandler) -> None: ...
    
    def __call__(self, event: EventDict) -> None: ...

class FanoutHandler:
    """
    Broadcast events to multiple handlers concurrently.
    
    Sends each event to all child handlers, continuing even if some fail.
    Manages lifecycle of all children as a group.
    
    Args:
        handlers: List of handlers to receive all events
    """
    
    def __init__(self, handlers: HandlerChain) -> None: ...
    
    def start(self) -> None:
        """Initialize all child handlers."""
        ...
    
    def stop(self) -> None:
        """Terminate all child handlers."""
        ...
    
    def __call__(self, event: EventDict) -> None: ...

class FallbackHandler:
    """
    Sequential failover with error isolation.
    
    Tries handlers in order until one succeeds. Provides resilience against
    individual handler failures.
    
    Args:
        handlers: Ordered list of handlers to try
    """
    
    def __init__(self, handlers: HandlerChain) -> None: ...
    
    def start(self) -> None:
        """Initialize all fallback handlers."""
        ...
    
    def stop(self) -> None:
        """Terminate all fallback handlers."""
        ...
    
    def __call__(self, event: EventDict) -> None: ...