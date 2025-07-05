"""
# Tracing Domain

A distributed execution tracking system that captures the flow of operations through spans.
The domain emits structured events representing the start and end of logical work units,
enabling visualization and analysis of execution paths through complex systems.

## Mental Model

Traces capture the journey of operations through your system:

```
Operation Flow           Event Stream              Handler Processing
with span('http_request'):
    ├─ emit start ────→ span.start ─────────→ Build trace tree
    ├─ child work                               Track relationships
    └─ emit end ──────→ span.end ──────────→ Calculate duration
```

Each span represents a logical unit of work with automatic timing, parent-child relationships,
and success/failure tracking. The separation of span events from trace assembly allows flexible
visualization and analysis strategies.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Final, Iterator, Optional
import time
import threading

from ..core import ObservabilityContext

# Event schema
SPAN_PREFIX: Final[str] = "span"
SPAN_START: Final[str] = f"{SPAN_PREFIX}.start"
SPAN_END: Final[str] = f"{SPAN_PREFIX}.end"
SPAN_EVENT: Final[str] = f"{SPAN_PREFIX}.event"

# Context variables for span correlation
current_span: Final[ContextVar[Optional["Span"]]] = ContextVar("current_span", default=None)

# Span ID generation
_span_counter: int = 0
_counter_lock = threading.Lock()


def _generate_span_id() -> str:
  """Generate unique span ID efficiently."""
  global _span_counter
  with _counter_lock:
    _span_counter += 1
    return f"{_span_counter:x}"


class Span:
  """
  Execution span tracking timing and relationships.

  Spans form a tree structure through parent-child relationships,
  automatically tracking duration and success/failure status.
  """

  __slots__ = ("_operation", "_context", "_attributes", "_span_id", "_parent_id", "_start_ns", "_token", "_status", "_status_message")

  def __init__(self, operation: str, context: ObservabilityContext, **attributes: Any):
    """
    Initialize span.

    Args:
        operation: Operation name
        context: ObservabilityContext to emit through
        **attributes: Additional span attributes
    """
    self._operation = operation
    self._context = context
    self._attributes = attributes
    self._span_id = _generate_span_id()
    self._parent_id: Optional[str] = None
    self._start_ns: Optional[int] = None
    self._token: Optional[Any] = None
    self._status: Optional[bool] = None
    self._status_message: Optional[str] = None

    # Capture parent from context
    parent = current_span.get()
    if parent:
      self._parent_id = parent._span_id

  @property
  def operation(self) -> str:
    """Operation name for this span."""
    return self._operation

  @property
  def span_id(self) -> str:
    """Get span ID."""
    return self._span_id

  @property
  def parent_id(self) -> Optional[str]:
    """Get parent span ID."""
    return self._parent_id

  def set_attribute(self, key: str, value: Any) -> None:
    """
    Set span attribute.

    Args:
        key: Attribute name
        value: Attribute value
    """
    self._attributes[key] = value

  def set_status(self, success: bool, message: Optional[str] = None) -> None:
    """
    Set span completion status.

    Explicitly marks span as successful or failed. If not called,
    success is inferred from exception handling in __exit__.

    Args:
        success: Whether the operation succeeded
        message: Optional status description
    """
    self._status = success
    self._status_message = message

  def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Add timestamped event within span.

    Events mark significant moments within a span's lifetime.
    They have their own timestamp and attributes but are associated
    with the containing span.

    Args:
        name: Event name (e.g., 'cache_miss', 'retry_attempted')
        attributes: Optional event metadata
    """
    if not self._context.has_handlers():
      return

    event_data = {
      "span_id": self._span_id,
      "name": name,
      "timestamp_ns": time.perf_counter_ns()
    }
    
    if attributes:
      event_data["attributes"] = attributes
    
    self._context.emit(SPAN_EVENT, event_data)

  def __enter__(self) -> "Span":
    """Start span execution."""
    # Early exit if no handlers
    if not self._context.has_handlers():
      return self

    # Record start time
    self._start_ns = time.perf_counter_ns()

    # Set as current span
    self._token = current_span.set(self)

    # Emit start event
    self._context.emit(
      SPAN_START, self._operation, span_id=self._span_id, parent_id=self._parent_id, **self._attributes
    )

    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    """Complete span execution."""
    # Early exit if no handlers or not started
    if not self._context.has_handlers() or self._start_ns is None:
      return

    # Calculate duration
    duration_ns = time.perf_counter_ns() - self._start_ns

    # Determine final status
    if self._status is not None:
      # Explicit status set by user
      success = self._status
      status_message = self._status_message
    else:
      # Infer from exception
      success = exc_type is None
      status_message = str(exc_val) if exc_val else None

    # Build end event data
    end_event_data = {
      "span_id": self._span_id,
      "duration_ns": duration_ns,
      "success": success,
      **self._attributes
    }
    
    if status_message:
      end_event_data["status_message"] = status_message
    
    if exc_val:
      end_event_data["error"] = str(exc_val)

    # Emit end event
    self._context.emit(SPAN_END, self._operation, **end_event_data)

    # Reset current span
    if self._token:
      current_span.reset(self._token)

  @contextmanager
  def start_child(self, operation: str, **attributes: Any) -> Iterator["Span"]:
    """
    Start a child span.

    Args:
        operation: Child operation name
        **attributes: Child span attributes

    Yields:
        Child span
    """
    child = Span(operation, self._context, **attributes)
    with child:
      yield child
