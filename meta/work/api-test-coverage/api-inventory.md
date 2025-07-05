# API Inventory - Exported Elements from Stub Files

## Overview
This document provides a comprehensive inventory of all exported API elements from the observability package stub files (.pyi files).

## observability/__init__.pyi

### Type Aliases
- `EventDict` (from .types)
- `EventHandler` (from .types)
- `ContextProvider` (from .types)

### Context Variables
- `trace_id: Final[ContextVar[Optional[str]]]`
- `request_id: Final[ContextVar[Optional[str]]]`
- `operation_id: Final[ContextVar[Optional[str]]]`

### Core Classes

#### ObservabilityContext
- `__init__(self, config: Optional[ObservabilityConfig] = None) -> None`
- `emit(self, event_type: str, value: Any, **metadata: Any) -> None`
- `attach_handler(self, handler: EventHandler) -> None`
- `has_handlers(self) -> bool`
- `start(self) -> None`
- `stop(self) -> None`
- `enable_category(self, category: str) -> None`
- `disable_category(self, category: str) -> None`

#### ObservabilityConfig
- `handlers: List[EventHandler]`
- `sampling_rate: float`
- `enabled_categories: Optional[Set[str]]`
- `enabled: bool`
- `__init__(self, *, handlers: Optional[List[EventHandler]] = None, sampling_rate: float = 1.0, enabled_categories: Optional[Set[str]] = None, enabled: bool = True) -> None`

#### SharedContext
- `setup(cls, config: Optional[ObservabilityConfig] = None) -> None` (classmethod)
- `get_context(cls) -> Optional[ObservabilityContext]` (classmethod)
- `get(cls) -> ObservabilityContext` (classmethod)
- `teardown(cls) -> None` (classmethod)
- `attach_handler(cls, handler: EventHandler) -> None` (classmethod)
- `start(cls) -> None` (classmethod)
- `stop(cls) -> None` (classmethod)
- `emit(cls, event_type: str, value: Any, **metadata: Any) -> None` (classmethod)

## handlers/__init__.pyi

### Type Aliases
- `HandlerChain = List[EventHandler]`
- `HandlerPredicate = Callable[[EventDict], bool]`

### Protocols
- `LifecycleHandler` (Protocol)
  - `start(self) -> None`
  - `stop(self) -> None`
- `ManagedHandler` (Protocol - extends EventHandler, LifecycleHandler)

### Core Handler Classes

#### PrintHandler
- `__init__(self, stream: IO[str], *, format: str = "{timestamp} {type}: {value}", include_context: bool = False) -> None`
- `__call__(self, event: EventDict) -> None`

#### JsonHandler
- `__init__(self, stream: IO[str], *, indent: Optional[int] = None, sort_keys: bool = False) -> None`
- `__call__(self, event: EventDict) -> None`

#### ManagedFileHandler
- `__init__(self, filepath: str | Path, *, max_bytes: int = 0, backup_count: int = 0, encoding: str = "utf-8") -> None`
- `start(self) -> None`
- `stop(self) -> None`
- `__call__(self, event: EventDict) -> None`

### Handler Factory Functions
- `filtered(predicate: HandlerPredicate, handler: EventHandler) -> EventHandler`
- `sampled(rate: float, handler: EventHandler, *, seed: Optional[int] = None) -> EventHandler`

### Supporting Handler Classes

#### BufferHandler
- `__init__(self, max_size: Optional[int] = None) -> None`
- `__call__(self, event: EventDict) -> None`
- `get_events(self) -> List[EventDict]`
- `clear(self) -> None`

#### QueuedHandler
- `__init__(self, wrapped_handler: EventHandler, *, queue_size: int = 10000, timeout: Optional[float] = None) -> None`
- `start(self) -> None`
- `stop(self) -> None`
- `__call__(self, event: EventDict) -> None`

#### TimeDeltaHandler
- `__init__(self, wrapped_handler: EventHandler) -> None`
- `__call__(self, event: EventDict) -> None`

#### FanoutHandler
- `__init__(self, handlers: HandlerChain) -> None`
- `start(self) -> None`
- `stop(self) -> None`
- `__call__(self, event: EventDict) -> None`

#### FallbackHandler
- `__init__(self, handlers: HandlerChain) -> None`
- `start(self) -> None`
- `stop(self) -> None`
- `__call__(self, event: EventDict) -> None`

## domains/logging.pyi

### Constants
- `DEBUG: Final[int] = 10`
- `INFO: Final[int] = 20`
- `WARNING: Final[int] = 30`
- `ERROR: Final[int] = 40`
- `CRITICAL: Final[int] = 50`

### Core Classes

#### Logger
- `__init__(self, name: str, context: ContextProvider, min_level: int = DEBUG) -> None`
- `name: str` (property)
- `min_level: int` (property + setter)
- `log(self, level: int, msg: str, **kwargs: Any) -> None`
- `debug(self, msg: str, **kwargs: Any) -> None`
- `info(self, msg: str, **kwargs: Any) -> None`
- `warning(self, msg: str, **kwargs: Any) -> None`
- `error(self, msg: str, **kwargs: Any) -> None`
- `critical(self, msg: str, **kwargs: Any) -> None`
- `is_enabled_for(self, level: int) -> bool`
- `get_child(self, suffix: str) -> "Logger"`

## domains/metrics.pyi

### Core Classes

#### Counter
- `__init__(self, name: str, context: ContextProvider, unit: str = "1", description: str = "", **static_labels: str) -> None`
- `name: str` (property)
- `increment(self, value: float = 1.0, **labels: str) -> None`

#### Gauge
- `__init__(self, name: str, context: ContextProvider, unit: str = "1", description: str = "", **static_labels: str) -> None`
- `name: str` (property)
- `set(self, value: float, **labels: str) -> None`
- `increment(self, value: float = 1.0, **labels: str) -> None`
- `decrement(self, value: float = 1.0, **labels: str) -> None`

#### Histogram
- `DEFAULT_BUCKETS: Final[tuple[float, ...]] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)`
- `__init__(self, name: str, context: ContextProvider, unit: str = "1", description: str = "", buckets: Optional[List[float]] = None, **static_labels: str) -> None`
- `name: str` (property)
- `buckets: List[float]` (property)
- `observe(self, value: float, **labels: str) -> None`

#### Timer
- `__init__(self, histogram: Histogram, **labels: str) -> None`
- `__enter__(self) -> "Timer"`
- `__exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Any) -> None`

## domains/tracing.pyi

### Context Variables
- `current_span: Final[ContextVar[Optional["Span"]]]`

### Core Classes

#### Span
- `__init__(self, operation: str, context: ContextProvider, **attributes: Any) -> None`
- `span_id: str` (property)
- `parent_id: Optional[str]` (property)
- `operation: str` (property)
- `set_attribute(self, key: str, value: Any) -> None`
- `set_status(self, success: bool, message: Optional[str] = None) -> None`
- `add_event(self, name: str, attributes: Optional[dict[str, Any]] = None) -> None`
- `start_child(self, operation: str, **attributes: Any) -> "Span"`
- `__enter__(self) -> "Span"`
- `__exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Any) -> None`

## Summary

### Total API Elements by Category:
- **Core Classes**: 4 (ObservabilityContext, ObservabilityConfig, SharedContext, Logger, Counter, Gauge, Histogram, Timer, Span)
- **Handler Classes**: 9 (PrintHandler, JsonHandler, ManagedFileHandler, BufferHandler, QueuedHandler, TimeDeltaHandler, FanoutHandler, FallbackHandler)
- **Protocols**: 2 (LifecycleHandler, ManagedHandler)
- **Factory Functions**: 2 (filtered, sampled)
- **Constants**: 6 (DEBUG, INFO, WARNING, ERROR, CRITICAL, DEFAULT_BUCKETS)
- **Context Variables**: 4 (trace_id, request_id, operation_id, current_span)
- **Type Aliases**: 5 (EventDict, EventHandler, ContextProvider, HandlerChain, HandlerPredicate)

### Total Methods/Properties to Test:
- **Core Methods**: 47+ individual methods/properties across all classes
- **Class Methods**: 8 (SharedContext class methods)
- **Special Methods**: 6 (__init__, __call__, __enter__, __exit__ implementations)

This inventory serves as the foundation for identifying test coverage gaps and planning comprehensive test implementation.