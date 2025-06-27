"""Type stubs for observability handlers."""

from typing import Optional, List, IO, Protocol
from pathlib import Path
from ..types import EventDict, EventHandler, HandlerFilter

# Base handlers

class PrintHandler:
  """Handler that prints events to a stream."""

  def __init__(
    self, stream: IO[str], *, format: str = "{timestamp} {type}: {value}", include_context: bool = False
  ) -> None: ...
  def __call__(self, event: EventDict) -> None: ...

class JsonHandler:
  """Handler that writes JSON-formatted events."""

  def __init__(self, stream: IO[str], *, indent: Optional[int] = None, sort_keys: bool = False) -> None: ...
  def __call__(self, event: EventDict) -> None: ...

class BufferHandler:
  """Handler that stores events in memory for testing."""

  def __init__(self, max_size: Optional[int] = None) -> None: ...
  def __call__(self, event: EventDict) -> None: ...
  def get_events(self) -> List[EventDict]:
    """Get captured events."""
    ...

  def clear(self) -> None:
    """Clear captured events."""
    ...

# Managed handlers

class ManagedFileHandler:
  """File handler with rotation and lifecycle management."""

  def __init__(
    self, filepath: str | Path, *, max_bytes: int = 0, backup_count: int = 0, encoding: str = "utf-8"
  ) -> None: ...
  def start(self) -> None:
    """Open file handle."""
    ...

  def stop(self) -> None:
    """Close file handle."""
    ...

  def __call__(self, event: EventDict) -> None: ...

class QueuedHandler:
  """Async handler using queue for non-blocking emission."""

  def __init__(
    self, wrapped_handler: EventHandler, *, queue_size: int = 10000, timeout: Optional[float] = None
  ) -> None: ...
  def start(self) -> None:
    """Start background thread."""
    ...

  def stop(self) -> None:
    """Stop background thread."""
    ...

  def __call__(self, event: EventDict) -> None: ...

# Composition handlers

class TimeDeltaHandler:
  """Add time delta between events."""

  def __init__(self, wrapped_handler: EventHandler) -> None: ...
  def __call__(self, event: EventDict) -> None: ...

class FanoutHandler:
  """Distribute events to multiple handlers."""

  def __init__(self, handlers: List[EventHandler]) -> None: ...
  def start(self) -> None:
    """Start all managed handlers."""
    ...

  def stop(self) -> None:
    """Stop all managed handlers."""
    ...

  def __call__(self, event: EventDict) -> None: ...

class FallbackHandler:
  """Try handlers in order until one succeeds."""

  def __init__(self, handlers: List[EventHandler]) -> None: ...
  def start(self) -> None:
    """Start all managed handlers."""
    ...

  def stop(self) -> None:
    """Stop all managed handlers."""
    ...

  def __call__(self, event: EventDict) -> None: ...

# Handler factories

def filtered(predicate: HandlerFilter, handler: EventHandler) -> EventHandler:
  """Create handler that only processes matching events."""
  ...

def sampled(rate: float, handler: EventHandler) -> EventHandler:
  """Create handler that samples events."""
  ...

# Additional utility types

class HandlerProtocol(Protocol):
  """Protocol for custom handlers."""

  def __call__(self, event: EventDict) -> None: ...

class ManagedHandlerProtocol(HandlerProtocol, Protocol):
  """Protocol for handlers with lifecycle."""

  def start(self) -> None: ...
  def stop(self) -> None: ...
