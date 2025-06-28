# ruff: noqa: F811
"""Type stubs for observability handlers."""

from typing import Optional, List, IO, Protocol, Callable
from pathlib import Path
from ..types import EventDict, EventHandler, HandlerFilter

# =============================================================================
# Base Types, Aliases & Protocols
# =============================================================================

class LifecycleHandler(Protocol):
    """Handler with managed lifecycle operations."""
    def start(self) -> None: ...
    def stop(self) -> None: ...

class ManagedHandler(EventHandler, LifecycleHandler, Protocol):
    """Complete managed handler contract combining event handling and lifecycle."""
    pass

# Type aliases for semantic clarity
HandlerChain = List[EventHandler]
HandlerPredicate = Callable[[EventDict], bool]

# =============================================================================
# Handler Concrete Implementations
# =============================================================================

# --- Sink Handlers ---

class PrintHandler:
    """Human-readable event output to text streams."""
    
    def __init__(
        self, 
        stream: IO[str], 
        *, 
        format: str = "{timestamp} {type}: {value}", 
        include_context: bool = False
    ) -> None: ...
    
    def __call__(self, event: EventDict) -> None: ...

class JsonHandler:
    """Structured JSON event serialization."""
    
    def __init__(
        self, 
        stream: IO[str], 
        *, 
        indent: Optional[int] = None, 
        sort_keys: bool = False
    ) -> None: ...
    
    def __call__(self, event: EventDict) -> None: ...

class BufferHandler:
    """In-memory event storage for testing and analysis."""
    
    def __init__(self, max_size: Optional[int] = None) -> None: ...
    
    def __call__(self, event: EventDict) -> None: ...
    
    def get_events(self) -> List[EventDict]:
        """Retrieve captured events."""
        ...
    
    def clear(self) -> None:
        """Clear event buffer."""
        ...

# --- Resource Handlers ---

class ManagedFileHandler:
    """Persistent file storage with lifecycle management."""
    
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

class QueuedHandler:
    """Asynchronous event processing with background worker."""
    
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
        """Terminate worker thread."""
        ...
    
    def __call__(self, event: EventDict) -> None: ...

# --- Control Handlers ---

class TimeDeltaHandler:
    """Event enrichment with time delta measurements."""
    
    def __init__(self, wrapped_handler: EventHandler) -> None: ...
    
    def __call__(self, event: EventDict) -> None: ...

# --- Composite Handlers ---

class FanoutHandler:
    """Broadcast events to multiple handlers concurrently."""
    
    def __init__(self, handlers: HandlerChain) -> None: ...
    
    def start(self) -> None:
        """Initialize all child handlers."""
        ...
    
    def stop(self) -> None:
        """Terminate all child handlers."""
        ...
    
    def __call__(self, event: EventDict) -> None: ...

class FallbackHandler:
    """Sequential failover with error isolation."""
    
    def __init__(self, handlers: HandlerChain) -> None: ...
    
    def start(self) -> None:
        """Initialize all fallback handlers."""
        ...
    
    def stop(self) -> None:
        """Terminate all fallback handlers."""
        ...
    
    def __call__(self, event: EventDict) -> None: ...

# --- Handler Factories ---

def filtered(predicate: HandlerPredicate, handler: EventHandler) -> EventHandler:
    """Create conditional event processor."""
    ...

def sampled(rate: float, handler: EventHandler) -> EventHandler:
    """Create statistical sampling handler."""
    ...