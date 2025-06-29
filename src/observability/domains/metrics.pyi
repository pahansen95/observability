# ruff: noqa: F811
"""Type stubs for metrics domain."""

from typing import Any, Dict, Optional, List, Union
from ..types import ContextProvider, Labels

# =============================================================================
# Base Types, Aliases & Protocols
# =============================================================================

# Type aliases
MetricName = str
MetricValue = Union[int, float]
MetricUnit = str
MetricDescription = str
BucketBoundaries = List[float]
StaticLabels = Dict[str, str]

# Default histogram buckets (seconds)
DEFAULT_BUCKETS: Final[List[float]] = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

# =============================================================================
# Metrics Domain Implementation
# =============================================================================

class Counter:
    """
    Monotonic counter for tracking cumulative values.
    
    Counters only increase, making them ideal for tracking:
    - Request counts
    - Error counts
    - Bytes processed
    - Events occurred
    
    Static labels are defined at creation, while dynamic labels
    can be provided with each increment operation.
    """
    
    def __init__(
        self,
        name: MetricName,
        context: ContextProvider,
        unit: MetricUnit = "1",
        description: MetricDescription = "",
        **static_labels: str
    ) -> None: ...
    
    @property
    def name(self) -> str:
        """Metric name."""
        ...
    
    def increment(self, value: float = 1.0, **labels: str) -> None:
        """Increase counter by specified value."""
        ...

class Gauge:
    """
    Arbitrary value tracker for point-in-time measurements.
    
    Gauges can increase or decrease, suitable for:
    - Queue depths
    - Active connections
    - Memory usage
    - Temperature readings
    
    Provides increment/decrement helpers alongside direct set.
    """
    
    def __init__(
        self,
        name: MetricName,
        context: ContextProvider,
        unit: MetricUnit = "1",
        description: MetricDescription = "",
        **static_labels: str
    ) -> None: ...
    
    @property
    def name(self) -> str:
        """Metric name."""
        ...
    
    def set(self, value: MetricValue, **labels: str) -> None:
        """Set gauge to specific value."""
        ...
    
    def increment(self, value: float = 1.0, **labels: str) -> None:
        """Increase gauge by value."""
        ...
    
    def decrement(self, value: float = 1.0, **labels: str) -> None:
        """Decrease gauge by value."""
        ...

class Histogram:
    """
    Distribution tracker for measuring value ranges and percentiles.
    
    Histograms capture the statistical distribution of values:
    - Response times
    - Request sizes
    - Processing durations
    - Score distributions
    
    Events contain raw observations, allowing handlers to compute
    aggregations using configurable bucket boundaries.
    """
    
    def __init__(
        self,
        name: MetricName,
        context: ContextProvider,
        unit: MetricUnit = "1",
        description: MetricDescription = "",
        buckets: Optional[BucketBoundaries] = None,
        **static_labels: str
    ) -> None: ...
    
    @property
    def name(self) -> str:
        """Metric name."""
        ...
    
    @property
    def buckets(self) -> List[float]:
        """Bucket boundaries for distribution."""
        ...
    
    def observe(self, value: MetricValue, **labels: str) -> None:
        """Record an observation."""
        ...

class Timer:
    """
    Context manager for timing operations using histograms.
    
    Convenience wrapper that automatically records operation
    duration to a histogram upon context exit.
    """
    
    def __init__(self, histogram: Histogram, **labels: str) -> None: ...
    
    def __enter__(self) -> 'Timer': ...
    
    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any]
    ) -> None: ...

class MetricsRegistry:
    """
    Central registry for metric instances with singleton guarantees.
    
    Ensures single metric instance per name/label combination,
    preventing duplicate registrations and providing efficient
    metric lookup for high-frequency operations.
    """
    
    def __init__(self, context: ContextProvider) -> None: ...
    
    def counter(
        self,
        name: MetricName,
        unit: MetricUnit = "1",
        description: MetricDescription = "",
        **static_labels: str
    ) -> Counter:
        """Get or create counter instance."""
        ...
    
    def gauge(
        self,
        name: MetricName,
        unit: MetricUnit = "1",
        description: MetricDescription = "",
        **static_labels: str
    ) -> Gauge:
        """Get or create gauge instance."""
        ...
    
    def histogram(
        self,
        name: MetricName,
        unit: MetricUnit = "1",
        description: MetricDescription = "",
        buckets: Optional[BucketBoundaries] = None,
        **static_labels: str
    ) -> Histogram:
        """Get or create histogram instance."""
        ...
    
    def clear(self) -> None:
        """Clear all registered metrics."""
        ...