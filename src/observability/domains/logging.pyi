# ruff: noqa: F811
"""
Logging domain for structured message recording.

Provides a hierarchical logger interface that emits structured events through
the observability pipeline. Loggers support dot-separated hierarchical names
for granular control and severity-based filtering.

The logging domain bridges traditional logging patterns with modern observability
by producing structured events that flow to all attached handlers while maintaining
familiar severity levels and hierarchical organization.

Logger names form a hierarchy that enables configuration inheritance:
- 'app' - Root application logger
- 'app.database' - Database subsystem logger  
- 'app.database.connection' - Connection pool logger

Each logger can have its own minimum severity level, and child loggers can be
created dynamically to organize subsystem logging.

## Quick Start
    from observability import ObservabilityContext
    from observability.domains.logging import Logger, INFO
    
    context = ObservabilityContext()
    logger = Logger('myapp', context, min_level=INFO)
    
    # Simple logging
    logger.info("Application started")
    logger.error("Connection failed", host="db.example.com", port=5432)
    
    # Child loggers for subsystems
    db_logger = logger.get_child('database')
    db_logger.debug("Query executed", duration_ms=123)

## Mental Model
Loggers form a tree structure based on dot-separated names, with each logger
having its own severity threshold. Events flow through the observability pipeline
only if they meet the logger's minimum severity level.

    Logger('app') → min_level=INFO
        ├─ Logger('app.api') → min_level=DEBUG
        └─ Logger('app.database') → min_level=WARNING

Events include automatic context enrichment from contextvars (trace_id, request_id, etc.)
and support arbitrary structured metadata through keyword arguments.
"""

from __future__ import annotations
from typing import Any, Final
from ..types import ContextProvider

# =============================================================================
# API Type Aliases, Protocols, Enums
# =============================================================================

# Severity level constants matching Python logging
DEBUG: Final[int] = 10
INFO: Final[int] = 20
WARNING: Final[int] = 30
ERROR: Final[int] = 40
CRITICAL: Final[int] = 50

# =============================================================================
# API Core Types & Functionality
# =============================================================================

class Logger:
    """
    Hierarchical structured logger emitting events through observability pipeline.
    
    Provides familiar logging interface while producing structured events
    that flow to all attached handlers. Supports dot-separated hierarchical
    names and severity-based filtering at the logger level.
    
    Logger hierarchy enables granular control over logging verbosity by
    subsystem. Child loggers inherit their parent's context but can override
    the minimum severity level for their subtree.
    
    Events automatically include:
    - Timestamp in nanoseconds
    - Logger name and severity level
    - Context variables (trace_id, request_id, operation_id)
    - Custom structured fields from kwargs
    
    Args:
        name: Dot-separated hierarchical name (e.g., 'app.database')
        context: Observability context or callable returning one
        min_level: Minimum severity for emission. Defaults to DEBUG (10).
    
    Example:
        >>> logger = Logger('app', context)
        >>> logger.info("Server started", port=8080, workers=4)
        >>> 
        >>> # Create subsystem logger
        >>> db_logger = logger.get_child('database')
        >>> db_logger.min_level = WARNING  # Only warnings and above
        >>> 
        >>> # Structured error logging
        >>> try:
        ...     connect()
        ... except Exception as e:
        ...     logger.error("Connection failed", 
        ...                  error=str(e),
        ...                  host="db.example.com",
        ...                  retry_count=3)
    
    Note:
        Loggers are lightweight and can be created freely. The hierarchical
        name is purely organizational - there's no global registry or
        parent-child message propagation.
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
        """
        Emit log event at specified severity level.
        
        Creates a structured event with type='log' containing the message,
        severity level, logger name, and any additional fields. Events below
        min_level are discarded without processing.
        
        Args:
            level: Numeric severity (use constants like INFO, ERROR)
            msg: Primary log message
            **kwargs: Additional structured fields
            
        Example:
            >>> logger.log(INFO, "Request processed",
            ...            method="GET",
            ...            path="/api/users",
            ...            duration_ms=45)
        """
        ...
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        """
        Log at DEBUG level (10).
        
        For detailed diagnostic information, typically only of interest
        when diagnosing problems.
        
        Args:
            msg: Debug message
            **kwargs: Additional structured fields
        """
        ...
    
    def info(self, msg: str, **kwargs: Any) -> None:
        """
        Log at INFO level (20).
        
        For informational messages that highlight progress of the application
        at a coarse-grained level.
        
        Args:
            msg: Informational message
            **kwargs: Additional structured fields
        """
        ...
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        """
        Log at WARNING level (30).
        
        For potentially harmful situations that should be addressed but don't
        prevent the application from functioning.
        
        Args:
            msg: Warning message
            **kwargs: Additional structured fields
        """
        ...
    
    def error(self, msg: str, **kwargs: Any) -> None:
        """
        Log at ERROR level (40).
        
        For error events that might still allow the application to continue
        running but should be investigated.
        
        Args:
            msg: Error message
            **kwargs: Additional structured fields
        """
        ...
    
    def critical(self, msg: str, **kwargs: Any) -> None:
        """
        Log at CRITICAL level (50).
        
        For very serious errors that will likely lead the application to abort.
        
        Args:
            msg: Critical error message
            **kwargs: Additional structured fields
        """
        ...
    
    def is_enabled_for(self, level: int) -> bool:
        """
        Check if logger would emit at given level.
        
        Useful for avoiding expensive message construction when logging
        is disabled at the specified level.
        
        Args:
            level: Severity level to check
            
        Returns:
            True if events at this level would be emitted
            
        Example:
            >>> if logger.is_enabled_for(DEBUG):
            ...     logger.debug("Expensive info: %s", compute_debug_info())
        """
        ...
    
    def get_child(self, suffix: str) -> 'Logger':
        """
        Create child logger with dot-separated name.
        
        Child loggers share the parent's context but can have independent
        minimum severity levels. The child name is formed by appending the
        suffix with a dot separator.
        
        Args:
            suffix: Name component to append (no dots)
            
        Returns:
            New logger with name '{parent.name}.{suffix}'
            
        Example:
            >>> app_logger = Logger('myapp', context)
            >>> db_logger = app_logger.get_child('database')
            >>> # db_logger.name == 'myapp.database'
        """
        ...