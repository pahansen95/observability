"""
# Shared Context Module

Provides a thread-safe singleton pattern for ambient observability access. The SharedContext
enables convenient access to observability features without explicit parameter passing,
while maintaining the option for isolated contexts where needed.

## Design Rationale

Many applications need observability at module level for infrastructure concerns (caching,
database connections, system health). The SharedContext provides this ambient access while
preserving the ability to create isolated contexts for testing and domain logic.

## Usage Pattern

```python
# Initialize once at application entry
from observability import SharedContext, ObservabilityConfig
from observability.handlers import JsonHandler

config = ObservabilityConfig(handlers=[JsonHandler(sys.stderr)])
SharedContext.setup(config)

# Use throughout application
from observability.domains.logging import Logger
logger = Logger(__name__, SharedContext.get_context())
```

## Thread Safety

The SharedContext uses thread-safe initialization with proper locking to ensure
safe concurrent access. Automatic cleanup is registered via atexit for graceful
shutdown.
"""

from typing import Optional, Any
import threading
import sys
import atexit

from .core import ObservabilityConfig, ObservabilityContext
from .handlers import PrintHandler, TimeDeltaHandler
from .types import EventHandler


class SharedContext:
  """Singleton providing a shared observability context with lifecycle management."""

  _ctx: Optional[ObservabilityContext] = None
  _lock: threading.Lock = threading.Lock()
  _cleanup_registered: bool = False

  @classmethod
  def setup(cls, config: Optional[ObservabilityConfig] = None) -> None:
    """Initialize the shared context.

    Args:
        config: Optional configuration. If None, uses default stderr output.

    Raises:
        RuntimeError: If already initialized.
    """
    with cls._lock:
      if cls._ctx is not None:
        # Stop existing context before creating new one
        cls._ctx.stop()

      # Use provided config or create default
      if config is None:
        base_handler = PrintHandler(
          sys.stderr, format="{timestamp_ms:10.1f}ms (+{delta_us:3.0f}μs) {type}: {value}", include_context=True
        )
        config = ObservabilityConfig(handlers=[TimeDeltaHandler(base_handler)], sampling_rate=1.0)

      # Create and start context
      cls._ctx = ObservabilityContext(config)
      cls._ctx.start()

      # Register cleanup only once
      if not cls._cleanup_registered:
        atexit.register(cls._shutdown)
        cls._cleanup_registered = True

  @classmethod
  def get_context(cls) -> Optional[ObservabilityContext]:
    """Get the shared context for lazy dependency injection.

    Returns:
        The shared context instance or None if not initialized.
        This supports the lazy injection pattern where domain objects
        can defer context resolution until first use.
    """
    return cls._ctx

  @classmethod
  def get(cls) -> ObservabilityContext:
    """Get the shared context, failing fast if not initialized.

    Returns:
        The shared context instance.

    Raises:
        RuntimeError: If not initialized.
    """
    if cls._ctx is None:
      raise RuntimeError("Shared context not initialized. Call SharedContext.setup() first.")
    return cls._ctx

  @classmethod
  def teardown(cls) -> None:
    """Explicitly teardown the shared context."""
    with cls._lock:
      if cls._ctx is not None:
        cls._ctx.stop()
        cls._ctx = None

    # Deregister from cleanup
    atexit.unregister(cls._shutdown)

  @classmethod
  def _shutdown(cls) -> None:
    """Automatic cleanup on process exit."""
    with cls._lock:
      if cls._ctx is not None:
        try:
          cls._ctx.stop()
        except Exception:
          # Suppress shutdown errors
          pass
        cls._ctx = None

  @classmethod
  def attach_handler(cls, handler: EventHandler) -> None:
    """Attach a handler to the shared context.

    Args:
        handler: EventHandler to attach

    Raises:
        RuntimeError: If context not initialized
    """
    ctx = cls.get()
    ctx.attach_handler(handler)

  @classmethod
  def start(cls) -> None:
    """Explicitly start the shared context.

    Useful when setup was called without auto-start.

    Raises:
        RuntimeError: If context not initialized
    """
    ctx = cls.get()
    ctx.start()

  @classmethod
  def stop(cls) -> None:
    """Explicitly stop the shared context.

    Raises:
        RuntimeError: If context not initialized
    """
    ctx = cls.get()
    ctx.stop()

  @classmethod
  def emit(cls, event_type: str, value: Any, **metadata) -> None:
    """Emit event using the shared context.

    Convenience method that delegates to the context.
    """
    cls.get().emit(event_type, value, **metadata)


__all__ = [
  "SharedContext",
]
