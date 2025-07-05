# ruff: noqa: F811
"""
Tracing domain for distributed execution tracking.

Provides spans for tracking logical units of work with automatic timing,
parent-child relationships, and metadata attachment. Spans represent
operations in distributed systems and enable reconstruction of execution
flow across service boundaries.

The tracing domain implements a context-propagation model where spans
automatically detect their parent from ambient context, forming a tree
structure that represents the call graph of operations.

Key concepts:
- Spans: Timed operations with metadata and relationships
- Context propagation: Automatic parent detection via contextvars
- Distributed tracing: Correlation across process boundaries
- Zero overhead: No cost when handlers aren't attached

## Quick Start
    from observability import ObservabilityContext
    from observability.domains.tracing import Span

    context = ObservabilityContext()

    # Basic span usage
    with Span('process_request', context) as span:
        span.set_attribute('request_id', '123')
        # Process the request
        span.set_attribute('status_code', 200)

    # Nested spans form parent-child relationships
    with Span('api_call', context) as parent:
        with Span('database_query', context) as child:
            child.set_attribute('query', 'SELECT * FROM users')
            # child.parent_id == parent.span_id

## Mental Model
Spans form a tree structure representing the execution flow:

    process_request [200ms]
        ├─ authenticate_user [50ms]
        ├─ load_data [100ms]
        │   ├─ cache_lookup [10ms]
        │   └─ database_query [90ms]
        └─ render_response [50ms]

Each span tracks its own timing and attributes while maintaining
relationships that enable distributed system visualization.
"""

from __future__ import annotations
from typing import Any, Optional, Final, ContextManager
from contextvars import ContextVar
from ..types import ContextProvider

# =============================================================================
# API Type Aliases, Protocols, Enums
# =============================================================================

# =============================================================================
# API Core Types & Functionality
# =============================================================================

current_span: Final[ContextVar[Optional["Span"]]]

class Span(ContextManager["Span"]):
  """
  Execution span tracking timing and relationships.

  Spans represent logical units of work with automatic timing, parent-child
  relationships, and success/failure tracking. Each span emits start and end
  events, enabling reconstruction of execution flow across distributed systems.

  Spans automatically detect their parent from context variables, forming
  a tree structure without explicit relationship management. They track
  high-precision timing and support arbitrary metadata attachment.

  Features:
  - Automatic parent span detection via contextvars
  - Nanosecond precision timing
  - Success/failure status tracking
  - Arbitrary attribute attachment
  - Zero-overhead when no handlers attached

  Args:
      operation: Name describing the operation (e.g., 'http_request')
      context: Observability context or callable returning one
      **attributes: Initial span attributes

  Example:
      >>> # Simple span with timing
      >>> with Span('process_order', context) as span:
      ...     span.set_attribute('order_id', '12345')
      ...     process_order()
      ...     span.set_attribute('items_count', 3)
      >>>
      >>> # Nested spans with error handling
      >>> with Span('api_request', context) as span:
      ...     try:
      ...         with span.start_child('validate_input') as child:
      ...             validate()
      ...         result = make_request()
      ...     except Exception as e:
      ...         span.set_status(False, str(e))
      ...         raise

  Note:
      Spans are context managers and automatically emit start/end events.
      Exceptions during span execution automatically set failure status
      before propagating.
  """

  def __init__(self, operation: str, context: ContextProvider, **attributes: Any) -> None: ...
  @property
  def span_id(self) -> str:
    """
    Unique span identifier.

    Generated automatically on span creation. Used for parent-child
    relationships and correlation across systems.
    """
    ...

  @property
  def parent_id(self) -> Optional[str]:
    """
    Parent span ID if nested.

    Automatically detected from context variables. None for root spans.
    """
    ...

  @property
  def operation(self) -> str:
    """Operation name for this span."""
    ...

  def set_attribute(self, key: str, value: Any) -> None:
    """
    Attach metadata to span.

    Attributes are included in the span end event and can be used
    for filtering, grouping, and analysis. Common attributes include
    user IDs, request parameters, and result codes.

    Args:
        key: Attribute name
        value: Attribute value (must be JSON-serializable)

    Example:
        >>> span.set_attribute('user_id', '123')
        >>> span.set_attribute('cache_hit', True)
        >>> span.set_attribute('response_size', 1024)
    """
    ...

  def set_status(self, success: bool, message: Optional[str] = None) -> None:
    """
    Set span completion status.

    Explicitly marks span as successful or failed. If not called,
    success is inferred from exception handling in __exit__.

    Args:
        success: Whether the operation succeeded
        message: Optional status description

    Example:
        >>> if not data:
        ...     span.set_status(False, "No data found")
        >>> else:
        ...     span.set_status(True, f"Processed {len(data)} items")
    """
    ...

  def add_event(self, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
    """
    Add timestamped event within span.

    Events mark significant moments within a span's lifetime.
    They have their own timestamp and attributes but are associated
    with the containing span.

    Args:
        name: Event name (e.g., 'cache_miss', 'retry_attempted')
        attributes: Optional event metadata

    Example:
        >>> span.add_event('retry_attempted', {'attempt': 1, 'delay_ms': 100})
        >>> span.add_event('fallback_used', {'reason': 'timeout'})
    """
    ...

  def start_child(self, operation: str, **attributes: Any) -> "Span":
    """
    Create child span with automatic parent relationship.

    Convenience method that creates a new span with this span as
    its parent. The child span inherits context but has its own
    timing and attributes.

    Args:
        operation: Child operation name
        **attributes: Initial child attributes

    Returns:
        New span with parent_id set to this span's ID

    Example:
        >>> with Span('request', context) as parent:
        ...     with parent.start_child('auth') as auth_span:
        ...         authenticate()
        ...     with parent.start_child('process') as proc_span:
        ...         process_request()
    """
    ...

  def __enter__(self) -> "Span":
    """
    Start span and set as current in context.

    Emits span start event and pushes to context variable stack
    for automatic parent detection by child spans.
    """
    ...

  def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Any) -> None:
    """
    End span and restore previous context.

    Emits span end event with duration and final attributes.
    Automatically sets failure status if exception occurred.
    Never suppresses exceptions.
    """
    ...
