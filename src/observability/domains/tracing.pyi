# ruff: noqa: F811
"""Type stubs for tracing domain."""

from typing import Any, Optional, Final, Dict, ContextManager
from contextvars import ContextVar
from ..core import ObservabilityContext

# =============================================================================
# Base Types, Aliases & Protocols
# =============================================================================

# Type aliases
SpanId = str
ParentId = Optional[str]
OperationName = str
SpanAttributes = Dict[str, Any]

# Context variables
current_span: Final[ContextVar[Optional['Span']]]

# =============================================================================
# Tracing Domain Implementation
# =============================================================================

class Span(ContextManager['Span']):
    """
    Distributed execution tracking for operations and workflows.
    
    Spans represent logical units of work with automatic timing, parent-child
    relationships, and success/failure tracking. Each span emits start and end
    events, enabling reconstruction of execution flow across distributed systems.
    
    Features:
    - Automatic parent span detection via contextvars
    - Nanosecond precision timing
    - Success/failure status tracking
    - Arbitrary attribute attachment
    - Zero-overhead when no handlers attached
    
    Usage:
        with Span('database_query', context) as span:
            span.set_attribute('query', 'SELECT * FROM users')
            # Perform operation
            span.set_attribute('row_count', 42)
    """
    
    def __init__(
        self,
        operation: OperationName,
        context: ObservabilityContext,
        **attributes: Any
    ) -> None: ...
    
    @property
    def span_id(self) -> SpanId:
        """Unique span identifier."""
        ...
    
    @property
    def parent_id(self) -> ParentId:
        """Parent span ID if nested."""
        ...
    
    @property
    def operation(self) -> str:
        """Operation name for this span."""
        ...
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Attach metadata to span."""
        ...
    
    def set_status(self, success: bool, message: Optional[str] = None) -> None:
        """Set span completion status."""
        ...
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add timestamped event within span."""
        ...
    
    def start_child(self, operation: str, **attributes: Any) -> 'Span':
        """Create child span with automatic parent relationship."""
        ...
    
    def __enter__(self) -> 'Span': ...
    
    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any]
    ) -> None: ...

class Tracer:
    """
    High-level span creation and management interface.
    
    Provides convenience methods for span creation and ensures
    proper context propagation across async boundaries.
    """
    
    def __init__(self, context: ObservabilityContext) -> None: ...
    
    def start_span(self, operation: str, **attributes: Any) -> Span:
        """Create and start a new span."""
        ...
    
    def span(self, operation: str, **attributes: Any) -> Span:
        """Create span for use as context manager."""
        ...