"""
Base protocol definitions for the observability package.

Defines the core contracts that all components must follow:
- EventDict: Standard event structure  
- EventHandler: Handler protocol for event processing
- ManagedHandler: Handler with lifecycle management
- ContextProvider: Lazy context resolution type
"""

from typing import Any, Dict, Protocol, TypedDict, Callable, Union, Optional

__all__ = [
    "EventDict",
    "EventHandler", 
    "ManagedHandler",
    "ContextProvider",
]


class EventDict(TypedDict, total=False):
    """
    Standard event structure for all observability events.
    
    Required fields:
    - category: Event category (e.g., "log", "trace", "metric")
    - event_type: Full event type identifier (e.g., "log.info")
    - timestamp: ISO-8601 timestamp string
    - value: Primary event payload
    
    Optional fields:
    - name: Component or logger name
    - message: Human-readable message
    - level: Severity level
    - attributes: Additional structured data
    - span_id: Trace span identifier
    - parent_span_id: Parent span identifier
    - duration: Operation duration in seconds
    - status: Operation status
    - tags: Metric tags
    - metadata: Arbitrary event metadata
    """
    # Required fields
    category: str
    event_type: str
    timestamp: str
    value: Any
    
    # Optional fields
    name: str
    message: str
    level: str
    attributes: Dict[str, Any]
    span_id: str
    parent_span_id: str
    duration: float
    status: str
    tags: Dict[str, str]
    metadata: Dict[str, Any]


class EventHandler(Protocol):
    """
    Base protocol for event handlers.
    
    Handlers process events emitted by the observability context.
    Simple handlers only need to implement __call__.
    """
    
    def __call__(self, event: EventDict) -> None:
        """Process an event."""
        ...


class ManagedHandler(EventHandler):
    """
    Handler protocol with explicit resource lifecycle management.
    
    Managed handlers control resources that need initialization
    and cleanup (files, network connections, threads, etc).
    
    Lifecycle:
    1. Handler created
    2. start() called before first event
    3. __call__() processes events
    4. stop() called during shutdown
    """
    
    def start(self) -> None:
        """
        Initialize handler resources.
        
        Called once before the first event is processed.
        Must be idempotent - safe to call multiple times.
        
        Raises:
            Exception: Initialization failures should be raised
                      to prevent handler use.
        """
        ...
    
    def stop(self) -> None:
        """
        Release handler resources.
        
        Called once during context shutdown.
        Must be idempotent - safe to call multiple times.
        Should not raise exceptions.
        """
        ...


# Forward reference to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import ObservabilityContext


# Type for lazy context resolution
ContextProvider = Union[
    'ObservabilityContext', 
    Callable[[], Optional['ObservabilityContext']]
]
"""
Type for context dependency injection.

Domain objects accept either:
- Direct context instance
- Callable returning context (for lazy resolution)

This enables module-level object creation before context initialization.
"""