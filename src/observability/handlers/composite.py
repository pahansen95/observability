"""
Composite handlers for event distribution.

Handlers that coordinate multiple sub-handlers, enabling sophisticated event
routing patterns while maintaining failure isolation between components.
"""

import sys

from ..types import EventDict, EventHandler
from .base import get_handler_name, safe_handler_call


class FanoutHandler:
  """
  Broadcast events to multiple handlers with lifecycle support.

  Forwards each event to all provided handlers independently.
  Handler failures are isolated - an error in one handler does
  not prevent others from receiving the event.
  """

  def __init__(self, *handlers: EventHandler):
    """
    Initialize fanout handler.

    Args:
        *handlers: Variable number of handlers to receive events
    """
    self.handlers = list(handlers)

  def start(self) -> None:
    """Start all sub-handlers that support lifecycle."""
    for handler in self.handlers:
      if hasattr(handler, "start"):
        try:
          handler.start()
        except Exception as e:
          safe_handler_call(f"FanoutHandler.{get_handler_name(handler)}", "starting", e)

  def stop(self) -> None:
    """Stop all sub-handlers that support lifecycle."""
    # Stop in reverse order
    for handler in reversed(self.handlers):
      if hasattr(handler, "stop"):
        try:
          handler.stop()
        except Exception:
          # Suppress shutdown errors
          pass

  def __call__(self, event: EventDict) -> None:
    """Forward event to all handlers."""
    for handler in self.handlers:
      try:
        handler(event)
      except Exception as e:
        safe_handler_call(f"fanout.{get_handler_name(handler)}", "processing", e)


class FallbackHandler:
  """
  Try handlers in order until one succeeds.

  Attempts to process each event with the primary handler.
  If it fails, tries each backup handler in order until one
  succeeds. Useful for ensuring event delivery with multiple
  fallback options.
  """

  def __init__(self, primary: EventHandler, *backups: EventHandler):
    """
    Initialize fallback handler.

    Args:
        primary: Primary handler to try first
        *backups: Backup handlers to try on primary failure
    """
    self.primary = primary
    self.backups = list(backups)
    self.all_handlers = [primary] + self.backups

  def start(self) -> None:
    """Start all handlers that support lifecycle."""
    for handler in self.all_handlers:
      if hasattr(handler, "start"):
        try:
          handler.start()
        except Exception as e:
          safe_handler_call(f"FallbackHandler.{get_handler_name(handler)}", "starting", e)

  def stop(self) -> None:
    """Stop all handlers that support lifecycle."""
    # Stop in reverse order
    for handler in reversed(self.all_handlers):
      if hasattr(handler, "stop"):
        try:
          handler.stop()
        except Exception:
          # Suppress shutdown errors
          pass

  def __call__(self, event: EventDict) -> None:
    """Try handlers until one succeeds."""
    # Try primary first
    try:
      self.primary(event)
      return
    except Exception as e:
      safe_handler_call(f"fallback.primary.{get_handler_name(self.primary)}", "processing", e)

    # Try backups in order
    for i, handler in enumerate(self.backups):
      try:
        handler(event)
        return  # Success - stop trying
      except Exception as e:
        safe_handler_call(f"fallback.backup[{i}].{get_handler_name(handler)}", "processing", e)

    # All handlers failed - report in debug mode
    if __debug__:
      print(f"All handlers failed for event type: {event.get('type', 'unknown')}", file=sys.stderr)
