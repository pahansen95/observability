"""Type stubs for tracing domain."""

from typing import Any, Optional, Final, Dict, ContextManager
from contextvars import ContextVar
from ..core import ObservabilityContext

# Context variable for current span
current_span: Final[ContextVar[Optional["Span"]]]

class Span(ContextManager["Span"]):
  """Execution span tracking timing and relationships."""

  def __init__(self, operation: str, context: ObservabilityContext, **attributes: Any) -> None: ...
  @property
  def span_id(self) -> str:
    """Get unique span identifier."""
    ...

  @property
  def parent_id(self) -> Optional[str]:
    """Get parent span ID if nested."""
    ...

  @property
  def operation(self) -> str:
    """Get operation name."""
    ...

  def set_attribute(self, key: str, value: Any) -> None:
    """Set span attribute."""
    ...

  def set_status(self, success: bool, message: Optional[str] = None) -> None:
    """Set span completion status."""
    ...

  def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Add event within span."""
    ...

  def start_child(self, operation: str, **attributes: Any) -> "Span":
    """Start child span."""
    ...

  def __enter__(self) -> "Span": ...
  def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None: ...

class Tracer:
  """High-level tracer for creating spans."""

  def __init__(self, context: ObservabilityContext) -> None: ...
  def start_span(self, operation: str, **attributes: Any) -> Span:
    """Start a new span."""
    ...

  def span(self, operation: str, **attributes: Any) -> Span:
    """Create span context manager."""
    ...
