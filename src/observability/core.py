"""
Core observability context implementation.

The ObservabilityContext is the central coordination point for event emission
and handler management. It provides:
- Zero-overhead event emission when disabled
- Thread-safe handler attachment/detachment
- Lifecycle management for managed handlers
- Ordered startup and shutdown sequences
"""

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import EventDict, EventHandler, ManagedHandler
from .config import ObservabilityConfig

__all__ = ["ObservabilityContext"]


class ObservabilityContext:
    """
    Central context for observability event emission and handler management.
    
    The context coordinates all observability operations:
    - Emits events to attached handlers
    - Manages handler lifecycle (start/stop)
    - Provides zero-overhead when no handlers attached
    - Ensures thread-safe operations
    
    Example:
        ctx = ObservabilityContext(config)
        ctx.attach_handler(FileHandler("app.log"))
        ctx.start()  # Initialize managed handlers
        
        ctx.emit("app.started", {"version": "1.0"})
        
        ctx.stop()  # Cleanup managed handlers
    """
    
    def __init__(self, config: Optional[ObservabilityConfig] = None):
        """
        Initialize observability context.
        
        Args:
            config: Configuration options. Defaults to enabled context.
        """
        self.config = config or ObservabilityConfig()
        
        # Handler management
        self._handlers: List[EventHandler] = []
        self._managed_handlers: List[ManagedHandler] = []
        
        # Lifecycle state
        self._started = False
        self._lock = threading.Lock()
        
        # Event metadata caching
        self._category_cache: Dict[str, str] = {}
    
    def attach_handler(self, handler: EventHandler) -> None:
        """
        Attach an event handler to this context.
        
        Handlers are called in attachment order for each event.
        Managed handlers are tracked for lifecycle management.
        
        If the context is already started, managed handlers
        are immediately started.
        
        Args:
            handler: Handler to attach
            
        Thread-safe: Can be called from any thread.
        """
        with self._lock:
            self._handlers.append(handler)
            
            # Track managed handlers for lifecycle
            if isinstance(handler, ManagedHandler):
                self._managed_handlers.append(handler)
                
                # Start if context already running
                if self._started:
                    try:
                        handler.start()
                    except Exception as e:
                        # Log but continue - partial availability
                        if __debug__:
                            import sys
                            print(f"Handler {handler} failed to start: {e}", 
                                  file=sys.stderr)
    
    def detach_handler(self, handler: EventHandler) -> None:
        """
        Remove a handler from this context.
        
        If the handler is managed and the context is running,
        it will be stopped before removal.
        
        Args:
            handler: Handler to remove
            
        Thread-safe: Can be called from any thread.
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
                
            if isinstance(handler, ManagedHandler) and handler in self._managed_handlers:
                self._managed_handlers.remove(handler)
                
                # Stop if context is running
                if self._started:
                    try:
                        handler.stop()
                    except Exception:
                        pass  # Suppress stop errors
    
    def start(self) -> None:
        """
        Start all managed handlers.
        
        Handlers are started in attachment order. If a handler
        fails to start, the error is logged but startup continues
        to ensure partial availability.
        
        This method is idempotent - multiple calls are safe.
        
        Thread-safe: Can be called from any thread.
        """
        with self._lock:
            if self._started:
                return
            
            for handler in self._managed_handlers:
                try:
                    handler.start()
                except Exception as e:
                    # Log error but continue with other handlers
                    if __debug__:
                        import sys
                        print(f"Handler {handler} failed to start: {e}", 
                              file=sys.stderr)
            
            self._started = True
    
    def stop(self) -> None:
        """
        Stop all managed handlers.
        
        Handlers are stopped in reverse attachment order (LIFO).
        Stop errors are suppressed to ensure all handlers are
        given a chance to clean up.
        
        This method is idempotent - multiple calls are safe.
        
        Thread-safe: Can be called from any thread.
        """
        with self._lock:
            if not self._started:
                return
            
            # Stop in reverse order - last attached, first stopped
            for handler in reversed(self._managed_handlers):
                try:
                    handler.stop()
                except Exception:
                    # Suppress all stop errors
                    pass
            
            self._started = False
    
    def emit(self, event_type: str, value: Any, **metadata: Any) -> None:
        """
        Emit an event to all attached handlers.
        
        This is the primary event emission interface. When no handlers
        are attached, this method returns immediately with zero overhead.
        
        Args:
            event_type: Event type identifier (e.g., "log.info", "metric.counter")
            value: Primary event payload
            **metadata: Additional event metadata
            
        The event is enriched with:
        - category: Extracted from event_type prefix
        - timestamp: Current UTC time in ISO format
        - All provided metadata
        
        Handler errors are isolated - one handler failure doesn't affect others.
        """
        # Zero-overhead check - single boolean test
        if not self._handlers:
            return
        
        # Only construct event if handlers exist
        event = self._create_event(event_type, value, metadata)
        self._dispatch(event)
    
    def _create_event(self, event_type: str, value: Any, metadata: Dict[str, Any]) -> EventDict:
        """
        Create a complete event dictionary.
        
        Enriches the event with standard fields:
        - category: Cached extraction from event_type
        - timestamp: Current UTC time
        - event_type: Full event identifier
        - value: Event payload
        - Additional metadata
        """
        # Cache category extraction for performance
        if event_type not in self._category_cache:
            self._category_cache[event_type] = event_type.split(".", 1)[0]
        
        # Construct event with all fields
        event: EventDict = {
            "category": self._category_cache[event_type],
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": value,
            **metadata  # type: ignore
        }
        
        return event
    
    def _dispatch(self, event: EventDict) -> None:
        """
        Dispatch event to all handlers with error isolation.
        
        Each handler is called with the event. Handler errors are
        caught and suppressed to ensure all handlers are invoked.
        """
        for handler in self._handlers:
            try:
                handler(event)
            except Exception:
                # Handler errors must not affect emission or other handlers
                pass
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"ObservabilityContext("
            f"handlers={len(self._handlers)}, "
            f"started={self._started})"
        )