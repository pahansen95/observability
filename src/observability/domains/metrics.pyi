"""Type stubs for metrics domain."""

from typing import Any, Optional, List
from ..types import ContextProvider

class Counter:
  """Monotonic counter that only increases."""

  def __init__(
    self, name: str, context: ContextProvider, unit: str = "1", description: str = "", **static_labels: str
  ) -> None: ...
  @property
  def name(self) -> str: ...
  def increment(self, value: float = 1.0, **labels: str) -> None:
    """Increment counter by value."""
    ...

class Gauge:
  """Gauge that can increase or decrease."""

  def __init__(
    self, name: str, context: ContextProvider, unit: str = "1", description: str = "", **static_labels: str
  ) -> None: ...
  @property
  def name(self) -> str: ...
  def set(self, value: float, **labels: str) -> None:
    """Set gauge to specific value."""
    ...

  def increment(self, value: float = 1.0, **labels: str) -> None:
    """Increase gauge by value."""
    ...

  def decrement(self, value: float = 1.0, **labels: str) -> None:
    """Decrease gauge by value."""
    ...

class Histogram:
  """Distribution of measurements."""

  def __init__(
    self,
    name: str,
    context: ContextProvider,
    unit: str = "1",
    description: str = "",
    buckets: Optional[List[float]] = None,
    **static_labels: str,
  ) -> None: ...
  @property
  def name(self) -> str: ...
  @property
  def buckets(self) -> List[float]: ...
  def observe(self, value: float, **labels: str) -> None:
    """Record an observation."""
    ...

class Timer:
  """Context manager for timing operations."""

  def __init__(self, histogram: Histogram, **labels: str) -> None: ...
  def __enter__(self) -> "Timer": ...
  def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None: ...

class MetricsRegistry:
  """Registry for metric instances."""

  def __init__(self, context: ContextProvider) -> None: ...
  def counter(self, name: str, unit: str = "1", description: str = "", **static_labels: str) -> Counter:
    """Get or create counter."""
    ...

  def gauge(self, name: str, unit: str = "1", description: str = "", **static_labels: str) -> Gauge:
    """Get or create gauge."""
    ...

  def histogram(
    self, name: str, unit: str = "1", description: str = "", buckets: Optional[List[float]] = None, **static_labels: str
  ) -> Histogram:
    """Get or create histogram."""
    ...

  def clear(self) -> None:
    """Clear all registered metrics."""
    ...
