"""
Control handlers for event flow modification.

Handlers that modify event processing flow without consuming events directly.
"""

import random
import threading
import warnings
from typing import Callable, Optional

from ..types import EventDict, EventHandler
from .base import get_handler_name, safe_handler_call


def filtered(predicate: Callable[[EventDict], bool], handler: EventHandler) -> EventHandler:
  """
  Process events only when predicate returns True.

  Args:
      predicate: Function returning True for events to process
      handler: Handler to receive matching events

  Returns:
      Filtered handler
  """

  def filtered_handler(event: EventDict) -> None:
    try:
      if predicate(event):
        handler(event)
    except Exception as e:
      safe_handler_call("Filter", "predicate evaluation", e)

  filtered_handler.__name__ = f"filtered({predicate.__name__} -> {get_handler_name(handler)})"

  return filtered_handler


def sampled(rate: float, handler: EventHandler, seed: Optional[int] = None) -> EventHandler:
  """
  Process events at specified sampling rate.

  Args:
      rate: Sampling rate (0.0 to 1.0)
      handler: Handler for sampled events
      seed: Random seed for reproducible sampling

  Returns:
      Sampling handler
  """
  if not 0.0 <= rate <= 1.0:
    raise ValueError(f"Rate must be 0.0 to 1.0, got {rate}")

  rng = random.Random(seed)

  def sampling_handler(event: EventDict) -> None:
    if rng.random() < rate:
      handler(event)

  sampling_handler.__name__ = f"sampled({rate:.1%} -> {get_handler_name(handler)})"

  return sampling_handler

class TimeDeltaHandler:
  """
  Enriches events with microsecond timestamps and time deltas.

  Adds computed fields to each event:
  - timestamp_us: Absolute time in microseconds since start
  - timestamp_ms: Absolute time in milliseconds since start
  - delta_ns: Nanoseconds since previous event
  - delta_us: Microseconds since previous event (for display)
  - delta_ms: Milliseconds since previous event

  Thread-safe for use across multiple threads emitting to the same handler.
  Create separate instances if tracking independent event streams.
  """

  def __init__(self, wrapped_handler: EventHandler):
    """
    Initialize with wrapped handler.

    Args:
        wrapped_handler: Handler to receive enriched events
    """
    self.wrapped_handler = wrapped_handler
    self.last_timestamp_ns: Optional[int] = None
    self._lock = threading.Lock()

  def __call__(self, event: EventDict) -> None:
    """
    Process event with time enrichment.

    Adds timing fields and forwards to wrapped handler.
    """
    # Calculate deltas thread-safely
    current_ns = event["timestamp_ns"]

    with self._lock:
      if self.last_timestamp_ns is None:
        delta_ns = 0  # First event baseline
      else:
        delta_ns = current_ns - self.last_timestamp_ns

      self.last_timestamp_ns = current_ns

    # Create enriched event
    enriched = event.copy()
    enriched["delta_ns"] = delta_ns
    enriched["delta_us"] = delta_ns / 1_000
    enriched["delta_ms"] = delta_ns / 1_000_000
    enriched["timestamp_us"] = current_ns / 1_000
    enriched["timestamp_ms"] = current_ns / 1_000_000

    # Forward to wrapped handler
    self.wrapped_handler(enriched)

  def reset(self) -> None:
    """Reset delta tracking for new trace session."""
    with self._lock:
      self.last_timestamp_ns = None