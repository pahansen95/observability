"""
Core observability infrastructure.

Provides context-based event emission with immutable configuration. All observability
state is encapsulated within explicit context objects, eliminating global state and
enabling isolated testing.
"""

import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .types import EventDict, EventHandler, CategorySet


@dataclass(frozen=True)
class ObservabilityConfig:
  """
  Immutable configuration for observability context.

  Defines all aspects of observability behavior at initialization time.
  Runtime mutation is not supported - create a new context for different
  configuration.
  """

  handlers: List[EventHandler] = field(default_factory=list)
  sampling_rate: float = 1.0
  enabled_categories: Set[str] = field(default_factory=set)

  def __post_init__(self):
    """Validate configuration."""
    if not 0.0 <= self.sampling_rate <= 1.0:
      raise ValueError(f"Sampling rate must be between 0 and 1, got {self.sampling_rate}")


class ObservabilityContext:
  """
  Encapsulates all observability state in an explicit context.

  Provides zero-overhead event emission when no handlers are attached,
  thread-safe handler management, and category-based filtering.
  """

  __slots__ = (
    "_handlers",
    "_start_time_ns",
    "_lock",
    "_categories",
    "_sampling_rate",
    "_category_mode",
    "_category_cache",
    "_started",
    "_managed_handlers",
  )

  def __init__(self, config: Optional[ObservabilityConfig] = None):
    """
    Initialize context with optional configuration.

    Args:
        config: Configuration to apply, or None for defaults
    """
    self._handlers: List[EventHandler] = []
    self._start_time_ns = time.perf_counter_ns()
    self._lock = threading.Lock()
    self._categories: CategorySet = set()
    self._sampling_rate: float = 1.0
    self._category_mode: Optional[str] = None  # None | 'allow' | 'block'
    self._category_cache: Dict[str, str] = {}  # event_type -> category
    self._started = False
    self._managed_handlers: List[EventHandler] = []

    if config:
      self._apply_config(config)

  def _register_handler_unsafe(self, handler: EventHandler) -> None:
    """
    Register handler without locks. Must be called under lock or during init.

    Args:
        handler: EventHandler to register
    """
    self._handlers.append(handler)

    if hasattr(handler, "start") and hasattr(handler, "stop"):
      self._managed_handlers.append(handler)

  def _apply_config(self, config: ObservabilityConfig) -> None:
    """
    Apply configuration during initialization.

    Args:
        config: Configuration to apply
    """
    self._sampling_rate = config.sampling_rate

    if config.enabled_categories:
      self._category_mode = "allow"
      self._categories = config.enabled_categories.copy()

    # Register handlers - no lock needed during init
    for handler in config.handlers:
      self._register_handler_unsafe(handler)

  def emit(self, event_type: str, value: Any, **metadata: Any) -> None:
    """
    Emit an event through the observability pipeline.

    Zero overhead when no handlers are attached. Automatically enriches
    events with context from contextvars.

    Args:
        event_type: Dotted event identifier (e.g., 'log.error')
        value: Primary event payload
        **metadata: Additional event attributes
    """
    # Critical performance path - single check for zero overhead
    if not self._handlers:
      return

    # Category filtering
    if self._category_mode:
      category = self._get_category(event_type)
      if self._category_mode == "allow" and category not in self._categories:
        return
      elif self._category_mode == "block" and category in self._categories:
        return

    # Build event
    event: EventDict = {
      "type": event_type,
      "value": value,
      "timestamp_ns": time.perf_counter_ns() - self._start_time_ns,
    }

    # Add context from contextvars
    from . import trace_id, request_id, operation_id

    if trace_val := trace_id.get():
      event["trace_id"] = trace_val
    if request_val := request_id.get():
      event["request_id"] = request_val
    if operation_val := operation_id.get():
      event["operation_id"] = operation_val

    # Add metadata
    event.update(metadata)

    # Dispatch to handlers
    self._dispatch(event)

  def _dispatch(self, event: EventDict) -> None:
    """Dispatch event to all handlers with error isolation."""
    for handler in self._handlers:
      try:
        handler(event)
      except Exception:
        # Handler errors must not affect emission
        pass

  def _get_category(self, event_type: str) -> str:
    """Extract category with caching for performance."""
    if event_type not in self._category_cache:
      self._category_cache[event_type] = event_type.split(".", 1)[0]
    return self._category_cache[event_type]

  def attach_handler(self, handler: EventHandler) -> None:
    """
    Attach handler at runtime.

    Args:
        handler: Callable that processes events
    """
    with self._lock:
      self._register_handler_unsafe(handler)

      # Auto-start if context is running
      if self._started and hasattr(handler, "start"):
        try:
          handler.start()
        except Exception as e:
          if __debug__:
            print(f"Handler {handler} failed to start: {e}", file=sys.stderr)

  def start(self) -> None:
    """
    Initialize all managed handlers.

    Starts handlers in registration order. Safe to call multiple times.
    """
    with self._lock:
      if self._started:
        return

      self._started = True
      for handler in self._managed_handlers:
        try:
          handler.start()
        except Exception as e:
          # Log but continue - partial start is better than none
          if __debug__:
            print(f"Handler {handler} start failed: {e}", file=sys.stderr)

  def stop(self) -> None:
    """
    Shutdown handlers gracefully.

    Stops handlers in reverse registration order for proper cleanup.
    Safe to call multiple times.
    """
    with self._lock:
      if not self._started:
        return

      self._started = False
      # Reverse order for proper cleanup
      for handler in reversed(self._managed_handlers):
        try:
          handler.stop()
        except Exception as e:
          # Always continue shutdown
          if __debug__:
            print(f"Handler {handler} stop failed: {e}", file=sys.stderr)

  def has_handlers(self) -> bool:
    """Check if any handlers are attached for zero-cost optimization."""
    return bool(self._handlers)

  def enable_category(self, category: str) -> None:
    """Enable event category at runtime."""
    with self._lock:
      if self._category_mode is None:
        self._category_mode = "allow"
        self._categories = {category}
      elif self._category_mode == "allow":
        self._categories.add(category)
      elif self._category_mode == "block":
        self._categories.discard(category)

  def disable_category(self, category: str) -> None:
    """Disable event category at runtime."""
    with self._lock:
      if self._category_mode is None:
        self._category_mode = "block"
        self._categories = {category}
      elif self._category_mode == "block":
        self._categories.add(category)
      elif self._category_mode == "allow":
        self._categories.discard(category)
