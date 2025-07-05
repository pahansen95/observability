# ruff: noqa: F811
"""
Observability infrastructure for Python applications.

A unified event emission infrastructure that provides zero-overhead instrumentation
for logging, tracing, and metrics collection. The package implements a context-based
architecture where all observability state is encapsulated in explicit context objects.

When no handlers are attached, the entire system reduces to a single boolean check,
ensuring production code pays no performance penalty for unused instrumentation.

## Quick Start
    from observability import ObservabilityContext, ObservabilityConfig
    from observability.handlers import JsonHandler
    import sys

    # Create configured context
    config = ObservabilityConfig(handlers=[JsonHandler(sys.stderr)])
    context = ObservabilityContext(config)
    context.start()

    # Or use shared context for convenience
    from observability import SharedContext
    SharedContext.setup(config)

    # Use with domain interfaces
    from observability.domains.logging import Logger
    logger = Logger('myapp', context)
    logger.info('Application started')

## Mental Model
The observability system uses explicit contexts to manage state and configuration:

    Application Code
        ↓
    ObservabilityContext ←── SharedContext.get()
        ↓ emit()
    Handler Pipeline
        ├─→ Logging Handler → File/Console
        ├─→ Metrics Handler → Aggregation/Export
        └─→ Trace Handler   → Span Collection

All state lives within context objects, eliminating global state and ensuring
clean dependency injection patterns.
"""

from __future__ import annotations
from typing import Any, Optional, Final, List, Set
from contextvars import ContextVar

# =============================================================================
# API Type Aliases, Protocols, Enums
# =============================================================================

from .types import (
  EventDict as EventDict,
  EventHandler as EventHandler,
  ContextProvider as ContextProvider,
)

# =============================================================================
# API Core Types & Functionality
# =============================================================================

# Context variables
trace_id: Final[ContextVar[Optional[str]]]
request_id: Final[ContextVar[Optional[str]]]
operation_id: Final[ContextVar[Optional[str]]]

# Version
__version__: Final[str]

class ObservabilityContext:
  """
  Encapsulates observability state with zero-overhead event emission.

  Provides thread-safe event routing to attached handlers with built-in
  category filtering and lifecycle management. When no handlers are
  attached, reduces to a single boolean check for zero runtime cost.

  The context serves as the central hub for all observability domains
  (logging, tracing, metrics) and manages handler lifecycles. It ensures
  proper resource cleanup and provides category-based filtering to control
  which events flow through the pipeline.

  Args:
      config: Optional configuration defining handlers, sampling, and filters.
              If None, creates an empty context with no handlers.

  Example:
      >>> config = ObservabilityConfig(handlers=[handler])
      >>> context = ObservabilityContext(config)
      >>> context.start()  # Initialize handlers
      >>> context.emit('log', {'message': 'Hello'})
      >>> context.stop()   # Cleanup handlers

  Note:
      Contexts are thread-safe but handlers may have their own threading
      constraints. Always call start() before emitting events and stop()
      when done to ensure proper resource management.
  """

  def __init__(self, config: Optional[ObservabilityConfig] = None) -> None: ...
  def emit(self, event_type: str, value: Any, **metadata: Any) -> None:
    """
    Route event to all attached handlers.

    Creates an EventDict with type, value, timestamp, and context fields,
    then passes it through the handler pipeline. Events are only processed
    if handlers are attached and the event's category is enabled.

    Args:
        event_type: Event classification (e.g., 'log', 'metric', 'span')
        value: Primary event payload
        **metadata: Additional event attributes
    """
    ...

  def attach_handler(self, handler: EventHandler) -> None:
    """
    Register an event handler.

    Handlers are invoked in registration order. Attaching handlers after
    start() is called is supported but the new handler won't be initialized.

    Args:
        handler: Callable accepting EventDict
    """
    ...

  def has_handlers(self) -> bool:
    """Check if any handlers are registered."""
    ...

  def start(self) -> None:
    """
    Initialize managed handlers.

    Calls start() on handlers that implement the ManagedHandler protocol.
    Safe to call multiple times - only first call has effect.
    """
    ...

  def stop(self) -> None:
    """
    Shutdown managed handlers.

    Calls stop() on handlers that implement the ManagedHandler protocol.
    Safe to call multiple times - only first call has effect.
    """
    ...

  def enable_category(self, category: str) -> None:
    """
    Enable events for specific category.

    Categories provide coarse-grained filtering. Common categories include
    'logging', 'tracing', 'metrics'. By default all categories are enabled
    unless explicitly configured otherwise.

    Args:
        category: Category name to enable
    """
    ...

  def disable_category(self, category: str) -> None:
    """
    Disable events for specific category.

    Disabled categories are filtered before handler invocation for
    maximum efficiency.

    Args:
        category: Category name to disable
    """
    ...

class ObservabilityConfig:
  """
  Immutable configuration for observability contexts.

  Defines handler pipeline, sampling rates, and category filters
  at initialization time. Runtime mutation is not supported -
  create new contexts for different configurations.

  The configuration serves as a template for creating contexts with
  consistent settings. It ensures all contexts created from the same
  config share identical behavior.

  Args:
      handlers: Event processing pipeline. Defaults to empty list.
      sampling_rate: Fraction of events to process (0.0-1.0). Defaults to 1.0.
      enabled_categories: Categories to enable, None enables all. Defaults to None.
      enabled: Master switch for all event processing. Defaults to True.

  Example:
      >>> from observability.handlers import JsonHandler
      >>> import sys
      >>> config = ObservabilityConfig(
      ...     handlers=[JsonHandler(sys.stderr)],
      ...     sampling_rate=0.1,  # Process 10% of events
      ...     enabled_categories={'logging', 'metrics'}
      ... )
      >>> context = ObservabilityContext(config)
  """

  handlers: List[EventHandler]
  sampling_rate: float
  enabled_categories: Optional[Set[str]]
  enabled: bool

  def __init__(
    self,
    *,
    handlers: Optional[List[EventHandler]] = None,
    sampling_rate: float = 1.0,
    enabled_categories: Optional[Set[str]] = None,
    enabled: bool = True,
  ) -> None: ...

# =============================================================================
# API Supporting Types & Functionality
# =============================================================================

class SharedContext:
  """
  Thread-safe singleton for ambient observability access.

  Enables module-level domain declarations with lazy context binding.
  Provides automatic lifecycle management through atexit registration
  for graceful shutdown without explicit cleanup code.

  The shared context pattern supports two use cases:
  1. Simple applications that want a single global context
  2. Libraries that need to declare domains before context exists

  For dependency injection patterns, prefer passing explicit contexts.

  Example:
      >>> # Application initialization
      >>> SharedContext.setup(config)
      >>>
      >>> # Anywhere in the codebase
      >>> logger = Logger('myapp', SharedContext.get)
      >>> logger.info('Ready')

  Note:
      The shared context registers an atexit handler for automatic
      cleanup. Call teardown() explicitly for deterministic shutdown.
  """

  @classmethod
  def setup(cls, config: Optional[ObservabilityConfig] = None) -> None:
    """
    Initialize shared context with configuration.

    Creates and starts a new context, replacing any existing one.
    Registers atexit handler for automatic cleanup.

    Args:
        config: Context configuration. None creates empty context.
    """
    ...

  @classmethod
  def get_context(cls) -> Optional[ObservabilityContext]:
    """
    Get context for lazy dependency injection.

    Returns None if not initialized. Used by domains to support
    declaration before initialization.

    Returns:
        Current context or None
    """
    ...

  @classmethod
  def get(cls) -> ObservabilityContext:
    """
    Get context, raising if not initialized.

    For use when context is required to exist.

    Returns:
        Current context

    Raises:
        RuntimeError: If setup() not called
    """
    ...

  @classmethod
  def teardown(cls) -> None:
    """
    Explicitly shutdown shared context.

    Stops context and clears singleton. Safe to call without setup().
    """
    ...

  @classmethod
  def attach_handler(cls, handler: EventHandler) -> None:
    """
    Register handler on shared context.

    Convenience method equivalent to get().attach_handler(handler).

    Args:
        handler: Event processing callable

    Raises:
        RuntimeError: If not initialized
    """
    ...

  @classmethod
  def start(cls) -> None:
    """
    Initialize shared context handlers.

    Convenience method equivalent to get().start().

    Raises:
        RuntimeError: If not initialized
    """
    ...

  @classmethod
  def stop(cls) -> None:
    """
    Shutdown shared context handlers.

    Convenience method equivalent to get().stop().

    Raises:
        RuntimeError: If not initialized
    """
    ...

  @classmethod
  def emit(cls, event_type: str, value: Any, **metadata: Any) -> None:
    """
    Emit event through shared context.

    Convenience method equivalent to get().emit(...).

    Args:
        event_type: Event classification
        value: Event payload
        **metadata: Additional attributes

    Raises:
        RuntimeError: If not initialized
    """
    ...
