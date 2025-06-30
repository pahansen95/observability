# ruff: noqa: F811
"""
Metrics domain for quantitative measurements.

Provides metric instruments for tracking quantitative data including counters,
gauges, and histograms. Metrics enable monitoring of application behavior
through numerical measurements that can be aggregated and analyzed.

The metrics domain implements three fundamental metric types:
- Counters: Monotonic values that only increase (requests, errors, bytes)
- Gauges: Point-in-time values that can go up or down (queue depth, temperature)
- Histograms: Distributions of values (latencies, sizes, scores)

Each metric supports static labels (defined at creation) and dynamic labels
(provided with each measurement) for dimensional analysis.

## Quick Start
    from observability import ObservabilityContext
    from observability.domains.metrics import Counter, Gauge, Histogram

    context = ObservabilityContext()

    # Count events
    requests = Counter('http_requests', context, unit='1')
    requests.increment(method='GET', path='/api/users')

    # Track current values
    connections = Gauge('db_connections', context)
    connections.set(42, pool='primary')

    # Measure distributions
    latency = Histogram('response_time', context, unit='s')
    latency.observe(0.123, endpoint='/api/users')

## Mental Model
Metrics flow as events through the observability pipeline, where handlers
can aggregate, export, or visualize them:

    Application → Metric.increment() → Event → Handlers
                                              ├─ PrometheusExporter
                                              ├─ StatsDAggregator
                                              └─ CloudWatchPublisher

Raw measurements are emitted as events, allowing flexible aggregation
strategies in handlers rather than fixed in-process accumulation.
"""

from __future__ import annotations
from typing import Any, Optional, Final, List
from ..types import ContextProvider

# =============================================================================
# API Type Aliases, Protocols, Enums
# =============================================================================

# =============================================================================
# API Core Types & Functionality
# =============================================================================

class Counter:
  """
  Monotonic counter for tracking cumulative values.

  Counters only increase, making them ideal for tracking cumulative
  measurements like total requests, errors, or bytes processed. Each
  increment emits an event through the observability pipeline.

  Static labels are defined at counter creation and included with every
  measurement. Dynamic labels can be provided per increment for additional
  dimensionality.

  Args:
      name: Metric name (e.g., 'http_requests_total')
      context: Observability context or callable returning one
      unit: Unit of measurement. Defaults to '1' (count).
      description: Human-readable description
      **static_labels: Labels always included with this counter

  Example:
      >>> # Create counter with static labels
      >>> requests = Counter('api_requests', context,
      ...                   service='user-api', version='2.0')
      >>>
      >>> # Increment with dynamic labels
      >>> requests.increment(method='GET', status='200')
      >>> requests.increment(method='POST', status='201')
      >>>
      >>> # Count errors
      >>> errors = Counter('api_errors', context)
      >>> try:
      ...     process_request()
      ... except Exception as e:
      ...     errors.increment(error_type=type(e).__name__)

  Note:
      Counters should never decrease. Use a Gauge for values that can
      go down. Counter names traditionally end with '_total'.
  """

  def __init__(
    self, name: str, context: ContextProvider, unit: str = "1", description: str = "", **static_labels: str
  ) -> None: ...
  @property
  def name(self) -> str:
    """Metric name."""
    ...

  def increment(self, value: float = 1.0, **labels: str) -> None:
    """
    Increase counter by specified value.

    Emits a metric event with type='metric.counter' containing the
    increment value and all labels (static + dynamic).

    Args:
        value: Amount to increment. Must be >= 0. Defaults to 1.0.
        **labels: Dynamic labels for this measurement

    Example:
        >>> requests.increment()  # Increment by 1
        >>> bytes_sent.increment(1024, host='server1')  # Add 1KB
    """
    ...

class Gauge:
  """
  Arbitrary value tracker for point-in-time measurements.

  Gauges can increase or decrease, suitable for measurements that
  fluctuate like queue depths, active connections, or resource usage.
  Each value change emits an event through the observability pipeline.

  Provides both direct value setting and increment/decrement helpers
  for convenience when tracking deltas.

  Args:
      name: Metric name (e.g., 'memory_usage_bytes')
      context: Observability context or callable returning one
      unit: Unit of measurement. Defaults to '1'.
      description: Human-readable description
      **static_labels: Labels always included with this gauge

  Example:
      >>> # Track connection pool
      >>> connections = Gauge('db_connections', context, pool='primary')
      >>> connections.set(10)
      >>> connections.increment(5)  # New connections
      >>> connections.decrement(2)  # Closed connections
      >>>
      >>> # Monitor resource usage
      >>> memory = Gauge('memory_usage', context, unit='bytes')
      >>> memory.set(get_memory_usage(), process='worker')
  """

  def __init__(
    self, name: str, context: ContextProvider, unit: str = "1", description: str = "", **static_labels: str
  ) -> None: ...
  @property
  def name(self) -> str:
    """Metric name."""
    ...

  def set(self, value: float, **labels: str) -> None:
    """
    Set gauge to specific value.

    Emits a metric event with type='metric.gauge' containing the
    current value and all labels.

    Args:
        value: New gauge value (can be negative)
        **labels: Dynamic labels for this measurement
    """
    ...

  def increment(self, value: float = 1.0, **labels: str) -> None:
    """
    Increase gauge by value.

    Convenience method that tracks the delta. Handlers may optimize
    incremental updates differently than absolute sets.

    Args:
        value: Amount to add. Defaults to 1.0.
        **labels: Dynamic labels for this measurement
    """
    ...

  def decrement(self, value: float = 1.0, **labels: str) -> None:
    """
    Decrease gauge by value.

    Convenience method that tracks the delta as a negative increment.

    Args:
        value: Amount to subtract. Defaults to 1.0.
        **labels: Dynamic labels for this measurement
    """
    ...

class Histogram:
  """
  Distribution tracker for measuring value ranges and percentiles.

  Histograms capture the statistical distribution of values like response
  times, request sizes, or score distributions. Each observation emits an
  event containing the raw value, allowing handlers to compute aggregations.

  Bucket boundaries define histogram bins for efficient percentile estimation.
  The default buckets are suitable for latencies in seconds.

  Args:
      name: Metric name (e.g., 'http_response_duration')
      context: Observability context or callable returning one
      unit: Unit of measurement. Defaults to '1'.
      description: Human-readable description
      buckets: Bucket boundaries for distribution. Uses DEFAULT_BUCKETS if None.
      **static_labels: Labels always included with this histogram

  Example:
      >>> # Track response times
      >>> latency = Histogram('api_latency', context, unit='s',
      ...                    buckets=[0.01, 0.05, 0.1, 0.5, 1.0])
      >>>
      >>> start = time.time()
      >>> process_request()
      >>> latency.observe(time.time() - start, endpoint='/users')
      >>>
      >>> # Use Timer helper
      >>> with Timer(latency, endpoint='/orders'):
      ...     process_order()
  """

  # Default bucket boundaries (seconds) - common latency ranges
  DEFAULT_BUCKETS: Final[tuple[float, ...]] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

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
  def name(self) -> str:
    """Metric name."""
    ...

  @property
  def buckets(self) -> List[float]:
    """Bucket boundaries for distribution."""
    ...

  def observe(self, value: float, **labels: str) -> None:
    """
    Record an observation.

    Emits a metric event with type='metric.histogram' containing the
    observed value, bucket boundaries, and all labels.

    Args:
        value: Observed measurement
        **labels: Dynamic labels for this observation

    Example:
        >>> latency.observe(0.123, method='GET', status='200')
        >>> sizes.observe(1024, content_type='json')
    """
    ...

# =============================================================================
# API Supporting Types & Functionality
# =============================================================================

class Timer:
  """
  Context manager for timing operations using histograms.

  Convenience wrapper that automatically records operation duration
  to a histogram upon context exit. Measures time in seconds with
  high precision.

  Args:
      histogram: Histogram to record duration to
      **labels: Labels to include with the observation

  Example:
      >>> latency = Histogram('db_query_duration', context, unit='s')
      >>>
      >>> with Timer(latency, query='SELECT *'):
      ...     results = database.query('SELECT * FROM users')
      >>> # Duration automatically recorded to histogram
  """

  def __init__(self, histogram: Histogram, **labels: str) -> None: ...
  def __enter__(self) -> "Timer":
    """Start timing."""
    ...

  def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Any) -> None:
    """Stop timing and record duration."""
    ...
