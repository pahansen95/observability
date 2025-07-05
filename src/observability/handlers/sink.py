"""
Sink handlers for event output.

Terminal event consumers that write events to external destinations.
"""

import json
import sys
from typing import TextIO

from ..types import EventDict
from .base import format_event_simple, format_context_items, STANDARD_EXCLUSIONS


class PrintHandler:
  """Console output handler with lifecycle support."""

  def __init__(
    self,
    stream: TextIO = sys.stdout,
    format: str = "{timestamp_ns:16d}ns {type}: {value}",
    include_context: bool = True,
  ):
    self.stream = stream
    self.format = format
    self.include_context = include_context
    self._is_initialized = False

  async def initialize(self) -> None:
    """Initialize handler (no-op for print handler)."""
    self._is_initialized = True

  async def shutdown(self) -> None:
    """Flush stream on shutdown."""
    if hasattr(self.stream, "flush"):
      self.stream.flush()
    self._is_initialized = False

  def __call__(self, event: EventDict) -> None:
    """Process event."""
    try:
      # Format primary message
      message = format_event_simple(event, self.format)

      # Add context if requested
      if self.include_context:
        exclude = STANDARD_EXCLUSIONS.copy()
        # Add fields already in format to exclusions
        for field in event.keys():
          if f"{{{field}}}" in self.format:
            exclude.add(field)

        context_items = format_context_items(event, exclude)
        if context_items:
          message += f" ({', '.join(context_items)})"

      print(message, file=self.stream)

    except Exception as e:
      if __debug__:
        print(f"Print handler error: {e}", file=sys.stderr)


class JsonHandler:
  """JSON output handler with lifecycle support."""

  def __init__(self, stream: TextIO = sys.stdout, pretty: bool = None, ensure_ascii: bool = True,
               indent: int = None, sort_keys: bool = False):
    self.stream = stream
    # Handle parameter mapping - indent takes precedence over pretty
    if indent is not None:
      self.indent = indent
      self.pretty = indent > 0  # For backward compatibility
    elif pretty is not None:
      self.pretty = pretty
      self.indent = 2 if pretty else None
    else:
      self.pretty = False
      self.indent = None
    
    self.ensure_ascii = ensure_ascii
    self.sort_keys = sort_keys
    self._is_initialized = False

  async def initialize(self) -> None:
    """Initialize handler."""
    self._is_initialized = True

  async def shutdown(self) -> None:
    """Flush stream on shutdown."""
    if hasattr(self.stream, "flush"):
      self.stream.flush()
    self._is_initialized = False

  def __call__(self, event: EventDict) -> None:
    """Process event as JSON."""
    try:
      json.dump(event, self.stream, default=str, indent=self.indent, 
                ensure_ascii=self.ensure_ascii, sort_keys=self.sort_keys)

      self.stream.write("\n")
      self.stream.flush()

    except Exception as e:
      if __debug__:
        print(f"JSON handler error: {e}", file=sys.stderr)


# No factory functions - use classes directly
