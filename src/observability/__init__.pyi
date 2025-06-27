# ruff: noqa: F811
"""Type stubs for observability package."""

from typing import Any, Optional, Final, List, Set
from contextvars import ContextVar
from .types import EventHandler
from .core import ObservabilityContext, ObservabilityConfig
from .shared import SharedContext
from .handlers import (
  PrintHandler as PrintHandler,
  JsonHandler as JsonHandler,
  ManagedFileHandler as ManagedFileHandler,
  BufferHandler as BufferHandler,
  QueuedHandler as QueuedHandler,
  TimeDeltaHandler as TimeDeltaHandler,
  FanoutHandler as FanoutHandler,
  FallbackHandler as FallbackHandler,
  filtered as filtered,
  sampled as sampled,
)

# Context variables
trace_id: Final[ContextVar[Optional[str]]]
request_id: Final[ContextVar[Optional[str]]]
operation_id: Final[ContextVar[Optional[str]]]

# Core exports

class ObservabilityContext:
  """Context encapsulating all observability state and configuration."""

  def __init__(self, config: Optional[ObservabilityConfig] = None) -> None: ...
  def emit(self, event_type: str, value: Any, **metadata: Any) -> None:
    """Emit an event through attached handlers."""
    ...

  def attach_handler(self, handler: EventHandler) -> None:
    """Attach an event handler to this context."""
    ...

  def has_handlers(self) -> bool:
    """Check if any handlers are attached."""
    ...

  def start(self) -> None:
    """Start managed handlers."""
    ...

  def stop(self) -> None:
    """Stop managed handlers."""
    ...

  def enable_category(self, category: str) -> None:
    """Enable events for a specific category."""
    ...

  def disable_category(self, category: str) -> None:
    """Disable events for a specific category."""
    ...

class ObservabilityConfig:
  """Immutable configuration for observability contexts."""

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
  """Singleton providing shared observability context."""

  @classmethod
  def setup(cls, config: Optional[ObservabilityConfig] = None) -> None:
    """Initialize the shared context."""
    ...

  @classmethod
  def get_context(cls) -> Optional[ObservabilityContext]:
    """Get shared context for lazy dependency injection."""
    ...

  @classmethod
  def get(cls) -> ObservabilityContext:
    """Get shared context, failing if not initialized."""
    ...

  @classmethod
  def teardown(cls) -> None:
    """Explicitly teardown the shared context."""
    ...

  @classmethod
  def attach_handler(cls, handler: EventHandler) -> None:
    """Attach a handler to the shared context."""
    ...

  @classmethod
  def start(cls) -> None:
    """Start the shared context."""
    ...

  @classmethod
  def stop(cls) -> None:
    """Stop the shared context."""
    ...

  @classmethod
  def emit(cls, event_type: str, value: Any, **metadata: Any) -> None:
    """Emit event using the shared context."""
    ...
