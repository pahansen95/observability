"""Type stubs for logging domain."""

from typing import Any, Final
from ..types import ContextProvider

# Severity levels
CRITICAL: Final[int]
ERROR: Final[int]
WARNING: Final[int]
INFO: Final[int]
DEBUG: Final[int]

class Logger:
  """Named logger that emits structured log events."""

  def __init__(self, name: str, context: ContextProvider, min_level: int = DEBUG) -> None: ...
  @property
  def name(self) -> str: ...
  @property
  def min_level(self) -> int: ...
  @min_level.setter
  def min_level(self, level: int) -> None: ...
  def log(self, level: int, msg: str, **kwargs: Any) -> None:
    """Emit log event at specified level."""
    ...

  def debug(self, msg: str, **kwargs: Any) -> None:
    """Log at DEBUG level."""
    ...

  def info(self, msg: str, **kwargs: Any) -> None:
    """Log at INFO level."""
    ...

  def warning(self, msg: str, **kwargs: Any) -> None:
    """Log at WARNING level."""
    ...

  def error(self, msg: str, **kwargs: Any) -> None:
    """Log at ERROR level."""
    ...

  def critical(self, msg: str, **kwargs: Any) -> None:
    """Log at CRITICAL level."""
    ...

  def is_enabled_for(self, level: int) -> bool:
    """Check if logger would emit at given level."""
    ...

  def get_child(self, suffix: str) -> "Logger":
    """Create child logger with dot-separated name."""
    ...
