# ruff: noqa: F811
"""Type stubs for observability package."""

from typing import Any, Optional, Final, List, Set, Dict, Callable, Protocol, Union, TypedDict
from contextvars import ContextVar

# =============================================================================
# Base Types, Aliases & Protocols
# =============================================================================

class EventDict(TypedDict, total=False):
    """Structured event data flowing through the observability pipeline."""
    # Required fields
    type: str
    value: Any
    timestamp_ns: int
    # Optional context fields
    trace_id: Optional[str]
    request_id: Optional[str]
    operation_id: Optional[str]

class EventHandler(Protocol):
    """Core contract for event processing."""
    def __call__(self, event: EventDict) -> None: ...

class HandlerFilter(Protocol):
    """Event filtering predicate contract."""
    def __call__(self, event: EventDict) -> bool: ...

class HandlerTransform(Protocol):
    """Event transformation contract."""
    def __call__(self, event: EventDict) -> EventDict: ...

# Type aliases for semantic clarity
HandlerFactory = Callable[..., EventHandler]
HandlerList = List[EventHandler]
CategorySet = Set[str]
ContextValue = Union[str, int, float, bool, None]
Labels = Dict[str, str]
CapturedEvents = List[EventDict]
ContextProvider = Union['ObservabilityContext', Callable[[], Optional['ObservabilityContext']]]

# =============================================================================
# Context Variables
# =============================================================================

trace_id: Final[ContextVar[Optional[str]]]
request_id: Final[ContextVar[Optional[str]]]
operation_id: Final[ContextVar[Optional[str]]]

# =============================================================================
# Core Implementation
# =============================================================================

class ObservabilityContext:
    """
    Encapsulates observability state with zero-overhead event emission.
    
    Provides thread-safe event routing to attached handlers with built-in
    category filtering and lifecycle management. When no handlers are
    attached, reduces to a single boolean check for zero runtime cost.
    """
    
    def __init__(self, config: Optional[ObservabilityConfig] = None) -> None: ...
    
    def emit(self, event_type: str, value: Any, **metadata: Any) -> None:
        """Route event to all attached handlers."""
        ...
    
    def attach_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        ...
    
    def has_handlers(self) -> bool:
        """Check if any handlers are registered."""
        ...
    
    def start(self) -> None:
        """Initialize managed handlers."""
        ...
    
    def stop(self) -> None:
        """Shutdown managed handlers."""
        ...
    
    def enable_category(self, category: str) -> None:
        """Enable events for specific category."""
        ...
    
    def disable_category(self, category: str) -> None:
        """Disable events for specific category."""
        ...

class ObservabilityConfig:
    """
    Immutable configuration for observability contexts.
    
    Defines handler pipeline, sampling rates, and category filters
    at initialization time. Runtime mutation is not supported -
    create new contexts for different configurations.
    """
    
    def __init__(
        self,
        *,
        handlers: Optional[List[EventHandler]] = None,
        sampling_rate: float = 1.0,
        enabled_categories: Optional[Set[str]] = None,
        enabled: bool = True,
    ) -> None: ...
    
    @property
    def handlers(self) -> List[EventHandler]: ...
    
    @property
    def sampling_rate(self) -> float: ...
    
    @property
    def enabled_categories(self) -> Optional[Set[str]]: ...
    
    @property
    def enabled(self) -> bool: ...

class SharedContext:
    """
    Thread-safe singleton for ambient observability access.
    
    Enables module-level domain declarations with lazy context binding.
    Provides automatic lifecycle management through atexit registration
    for graceful shutdown without explicit cleanup code.
    """
    
    @classmethod
    def setup(cls, config: Optional[ObservabilityConfig] = None) -> None:
        """Initialize shared context with configuration."""
        ...
    
    @classmethod
    def get_context(cls) -> Optional[ObservabilityContext]:
        """Get context for lazy dependency injection."""
        ...
    
    @classmethod
    def get(cls) -> ObservabilityContext:
        """Get context, raising if not initialized."""
        ...
    
    @classmethod
    def teardown(cls) -> None:
        """Explicitly shutdown shared context."""
        ...
    
    @classmethod
    def attach_handler(cls, handler: EventHandler) -> None:
        """Register handler on shared context."""
        ...
    
    @classmethod
    def start(cls) -> None:
        """Initialize shared context handlers."""
        ...
    
    @classmethod
    def stop(cls) -> None:
        """Shutdown shared context handlers."""
        ...
    
    @classmethod
    def emit(cls, event_type: str, value: Any, **metadata: Any) -> None:
        """Emit event through shared context."""
        ...