# ruff: noqa: F811
"""Type stubs for logging domain."""

from typing import Any, Final, Optional, Dict
from ..types import ContextProvider

# =============================================================================
# Base Types, Aliases & Protocols
# =============================================================================

# Severity level constants
CRITICAL: Final[int] = 50
ERROR: Final[int] = 40
WARNING: Final[int] = 30
INFO: Final[int] = 20
DEBUG: Final[int] = 10

# Type aliases
LogRecord = Dict[str, Any]

# =============================================================================
# Logging Domain Implementation
# =============================================================================

class Logger:
    """
    Hierarchical structured logger emitting events through observability pipeline.
    
    Provides familiar logging interface while producing structured events
    that flow to all attached handlers. Supports dot-separated hierarchical
    names and severity-based filtering at the logger level.
    
    Logger hierarchy enables granular control:
    - 'app' - Root application logger
    - 'app.database' - Database subsystem logger
    - 'app.database.connection' - Connection pool logger
    
    Events include automatic context enrichment from contextvars
    and support arbitrary structured metadata through kwargs.
    """
    
    def __init__(
        self,
        name: str,
        context: ContextProvider,
        min_level: int = DEBUG
    ) -> None: ...
    
    @property
    def name(self) -> str:
        """Logger hierarchical name."""
        ...
    
    @property
    def min_level(self) -> int:
        """Minimum severity level for emission."""
        ...
    
    @min_level.setter
    def min_level(self, level: int) -> None:
        """Update minimum severity level."""
        ...
    
    def log(self, level: int, msg: str, **kwargs: Any) -> None:
        """Emit log event at specified severity level."""
        ...
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log at DEBUG level (10)."""
        ...
    
    def info(self, msg: str, **kwargs: Any) -> None:
        """Log at INFO level (20)."""
        ...
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log at WARNING level (30)."""
        ...
    
    def error(self, msg: str, **kwargs: Any) -> None:
        """Log at ERROR level (40)."""
        ...
    
    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log at CRITICAL level (50)."""
        ...
    
    def is_enabled_for(self, level: int) -> bool:
        """Check if logger would emit at given level."""
        ...
    
    def get_child(self, suffix: str) -> 'Logger':
        """Create child logger with dot-separated name."""
        ...