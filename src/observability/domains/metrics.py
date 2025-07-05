"""
# Metrics Domain

A quantitative measurement system that transforms numeric observations into events
for statistical aggregation. The domain provides counter, gauge, and histogram
primitives that emit measurement events, enabling flexible aggregation strategies
through specialized handlers.

## Mental Model

Metrics capture the vital signs of your application:

```
Application Measurements      Event Stream           Handler Aggregation
counter.increment() ────→ metric.counter ────→ Sum over time window
gauge.set(42) ─────────→ metric.gauge ──────→ Current value tracking
histogram.observe(0.1) ─→ metric.histogram ──→ Distribution buckets
```

Like a heartbeat monitor that shows beats per minute rather than individual heartbeats,
metrics summarize continuous activity into meaningful statistics. The separation between
measurement and aggregation allows the same data to feed multiple monitoring systems
simultaneously.
"""

from typing import Dict, Final, List, Optional, Tuple
import time

from ..core import ObservabilityContext

# Event schema
METRIC_PREFIX: Final[str] = "metric"
METRIC_COUNTER: Final[str] = f"{METRIC_PREFIX}.counter"
METRIC_GAUGE: Final[str] = f"{METRIC_PREFIX}.gauge"
METRIC_HISTOGRAM: Final[str] = f"{METRIC_PREFIX}.histogram"

# Label validation
MAX_LABEL_KEY_LENGTH: Final[int] = 100
MAX_LABEL_VALUE_LENGTH: Final[int] = 200
MAX_LABELS_PER_METRIC: Final[int] = 10


class Counter:
  """
  Monotonically increasing counter metric.

  Counters track cumulative values that only increase over time,
  such as total requests processed or bytes transmitted.
  """

  __slots__ = ("_name", "_context", "_description", "_labels", "_unit")

  def __init__(self, name: str, context: ObservabilityContext, unit: str = "1", description: str = "", **labels: str):
    """
    Initialize counter.

    Args:
        name: Metric name
        context: ObservabilityContext to emit through
        unit: Unit of measurement. Defaults to '1' (count)
        description: Human-readable description
        **labels: Static labels
    """
    self._name = name
    self._context = context
    self._unit = unit
    self._description = description
    self._labels = self._validate_labels(labels)

  @property
  def name(self) -> str:
    """Metric name."""
    return self._name

  def _validate_labels(self, labels: Dict[str, str]) -> Dict[str, str]:
    """Validate label constraints."""
    if len(labels) > MAX_LABELS_PER_METRIC:
      raise ValueError(f"Too many labels: {len(labels)} > {MAX_LABELS_PER_METRIC}")

    for key, value in labels.items():
      if len(key) > MAX_LABEL_KEY_LENGTH:
        raise ValueError(f"Label key too long: {key}")
      if len(value) > MAX_LABEL_VALUE_LENGTH:
        raise ValueError(f"Label value too long: {value}")

    return labels

  def increment(self, value: float = 1.0, **labels: str) -> None:
    """
    Increment counter by value.

    Args:
        value: Amount to increment (default 1.0)
        **labels: Dynamic labels for this measurement
    """
    if value < 0:
      raise ValueError("Counter increment must be non-negative")

    if not self._context.has_handlers():
      return

    # Merge static and dynamic labels
    combined_labels = {**self._labels, **labels}

    self._context.emit(
      METRIC_COUNTER,
      value,
      name=self._name,
      measurement=value,
      metric_type="counter",
      unit=self._unit,
      help=self._description,
      **combined_labels
    )


class Gauge:
  """
  Point-in-time value metric.

  Gauges represent current state measurements that can go up or down,
  such as active connections or memory usage.
  """

  __slots__ = ("_name", "_context", "_description", "_labels", "_unit")

  def __init__(self, name: str, context: ObservabilityContext, unit: str = "1", description: str = "", **labels: str):
    """
    Initialize gauge.

    Args:
        name: Metric name
        context: ObservabilityContext to emit through
        unit: Unit of measurement. Defaults to '1'
        description: Human-readable description
        **labels: Static labels
    """
    self._name = name
    self._context = context
    self._unit = unit
    self._description = description
    self._labels = labels

  @property
  def name(self) -> str:
    """Metric name."""
    return self._name

  def set(self, value: float, **labels: str) -> None:
    """
    Set gauge to value.

    Args:
        value: Current measurement
        **labels: Dynamic labels for this measurement
    """
    if not self._context.has_handlers():
      return

    combined_labels = {**self._labels, **labels}

    self._context.emit(
      METRIC_GAUGE,
      value,
      name=self._name,
      measurement=value,
      metric_type="gauge",
      unit=self._unit,
      help=self._description,
      **combined_labels
    )

  def increment(self, value: float = 1.0, **labels: str) -> None:
    """
    Increment gauge by value.

    Args:
        value: Amount to increment
        **labels: Dynamic labels
    """
    # Note: In a real implementation, this would need to track current value
    # For event-based system, we emit the delta
    if not self._context.has_handlers():
      return

    combined_labels = {**self._labels, **labels}

    self._context.emit(
      METRIC_GAUGE,
      value,
      name=self._name,
      measurement=value,
      metric_type="gauge",
      delta=True,
      unit=self._unit,
      help=self._description,
      **combined_labels
    )

  def decrement(self, value: float = 1.0, **labels: str) -> None:
    """
    Decrement gauge by value.

    Args:
        value: Amount to decrement
        **labels: Dynamic labels
    """
    self.increment(-value, **labels)


class Histogram:
  """
  Distribution of values metric.

  Histograms track the distribution of observed values over time,
  such as request latencies or response sizes.
  """

  __slots__ = ("_name", "_context", "_description", "_labels", "_buckets", "_unit")

  # Default bucket boundaries (in seconds, suitable for latencies)
  DEFAULT_BUCKETS: Final[Tuple[float, ...]] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

  def __init__(
    self,
    name: str,
    context: ObservabilityContext,
    unit: str = "1",
    description: str = "",
    buckets: Optional[List[float]] = None,
    **labels: str,
  ):
    """
    Initialize histogram.

    Args:
        name: Metric name
        context: ObservabilityContext to emit through
        unit: Unit of measurement. Defaults to '1'
        description: Human-readable description
        buckets: Bucket boundaries for observations
        **labels: Static labels
    """
    self._name = name
    self._context = context
    self._unit = unit
    self._description = description
    self._labels = labels
    self._buckets = buckets or list(self.DEFAULT_BUCKETS)

  @property
  def name(self) -> str:
    """Metric name."""
    return self._name

  @property
  def buckets(self) -> List[float]:
    """Bucket boundaries for distribution."""
    return self._buckets

  def observe(self, value: float, **labels: str) -> None:
    """
    Record an observation.

    Args:
        value: Observed measurement
        **labels: Dynamic labels for this measurement
    """
    if not self._context.has_handlers():
      return

    combined_labels = {**self._labels, **labels}

    self._context.emit(
      METRIC_HISTOGRAM,
      value,
      name=self._name,
      measurement=value,
      metric_type="histogram",
      unit=self._unit,
      help=self._description,
      buckets=self._buckets,
      **combined_labels,
    )

  def time(self, **labels: str):
    """
    Context manager for timing operations.

    Args:
        **labels: Dynamic labels for this measurement

    Returns:
        Timer context manager
    """
    return Timer(self, **labels)


# Export DEFAULT_BUCKETS at module level for convenience
DEFAULT_BUCKETS = Histogram.DEFAULT_BUCKETS


class Timer:
  """Context manager for histogram timing."""

  __slots__ = ("_histogram", "_labels", "_start")

  def __init__(self, histogram: Histogram, **labels: str):
    self._histogram = histogram
    self._labels = labels
    self._start: Optional[float] = None

  def __enter__(self):
    self._start = time.perf_counter()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if self._start is not None:
      duration = time.perf_counter() - self._start
      self._histogram.observe(duration, **self._labels)
