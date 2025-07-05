#!/usr/bin/env python3
"""
Example 72: Monitoring Dashboard

Demonstrates:
- Real-time monitoring dashboard
- Metric aggregation and visualization
- Alert conditions and thresholds
- Performance indicators
- System health monitoring
"""

import time
import threading
from collections import defaultdict, deque
from datetime import datetime
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler
from observability.domains.logging import Logger, INFO, ERROR
from observability.domains.metrics import Counter, Gauge, Histogram



class MetricsAggregator:
    """Aggregate metrics for dashboard display."""

    def __init__(self, window_size=60):
        self.window_size = window_size
        self.metrics = defaultdict(lambda: deque(maxlen=window_size))
        self.lock = threading.Lock()

    def add_metric(self, name, value, timestamp):
        """Add metric observation."""
        with self.lock:
            self.metrics[name].append((timestamp, value))

    def get_current(self, name):
        """Get current metric value."""
        with self.lock:
            if name in self.metrics and self.metrics[name]:
                return self.metrics[name][-1][1]
        return 0

    def get_rate(self, name, duration=60):
        """Calculate rate over duration."""
        with self.lock:
            if name not in self.metrics:
                return 0

            now = time.time()
            cutoff = now - duration

            values = [v for t, v in self.metrics[name] if t >= cutoff]
            if len(values) < 2:
                return 0

            return len(values) / duration

    def get_percentile(self, name, percentile=95):
        """Get percentile value."""
        with self.lock:
            if name not in self.metrics:
                return 0

            values = sorted([v for _, v in self.metrics[name]])
            if not values:
                return 0

            index = int(len(values) * (percentile / 100))
            return values[min(index, len(values) - 1)]


class Dashboard:
    """Real-time monitoring dashboard."""

    def __init__(self, context):
        self.context = context
        self.aggregator = MetricsAggregator()
        self.alerts = []
        self.health_checks = {}

        # Track various metrics
        self.request_count = 0
        self.error_count = 0
        self.active_spans = {}

        # Start dashboard handler
        self._setup_handler()

    def _setup_handler(self):
        """Setup dashboard event handler."""
        def dashboard_handler(event):
            # Process metrics
            if event['type'].startswith('metric.'):
                metric_type = event['type'].split('.')[1]
                value = event.get('measurement', 0)
                name = event.get('value', 'unknown')  # metric name is in 'value' field

                if metric_type in ['counter', 'gauge']:
                    self.aggregator.add_metric(name, value, event.get('timestamp_ns', 0))
                elif metric_type == 'histogram':
                    self.aggregator.add_metric(f"{name}_value", value, event.get('timestamp_ns', 0))

            # Track requests
            elif event['type'] == 'log.info' and 'request' in str(event['value']):
                self.request_count += 1

            # Track errors
            elif event.get('level', 0) >= ERROR or 'error' in event['type']:
                self.error_count += 1
                self._check_error_rate()

            # Track spans
            elif event['type'] == 'trace.span_start':
                span_id = event['value'].get('span_id')
                self.active_spans[span_id] = event['timestamp']
            elif event['type'] == 'trace.span_end':
                span_id = event['value'].get('span_id')
                if span_id in self.active_spans:
                    duration = event['timestamp'] - self.active_spans[span_id]
                    self.aggregator.add_metric('span_duration', duration * 1000, event['timestamp'])
                    del self.active_spans[span_id]

        # Store handler for external use
        self.handler = dashboard_handler

    def _check_error_rate(self):
        """Check error rate and alert if needed."""
        error_rate = self.aggregator.get_rate('errors', 60)
        if error_rate > 10:  # More than 10 errors per minute
            self.add_alert('HIGH_ERROR_RATE', f"Error rate: {error_rate:.1f}/min", 'critical')

    def add_alert(self, alert_type, message, severity='warning'):
        """Add alert to dashboard."""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': time.time()
        }
        self.alerts.append(alert)

        # Keep only recent alerts
        cutoff = time.time() - 300  # 5 minutes
        self.alerts = [a for a in self.alerts if a['timestamp'] > cutoff]

    def register_health_check(self, name, check_fn):
        """Register health check."""
        self.health_checks[name] = check_fn

    def get_system_health(self):
        """Get overall system health."""
        health_status = {}
        all_healthy = True

        for name, check_fn in self.health_checks.items():
            try:
                result = check_fn()
                health_status[name] = {'status': 'healthy' if result else 'unhealthy'}
                if not result:
                    all_healthy = False
            except Exception as e:
                health_status[name] = {'status': 'error', 'error': str(e)}
                all_healthy = False

        return all_healthy, health_status

    def render(self):
        """Render dashboard display."""
        print("\n" + "="*60)
        print(f"📊 MONITORING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # System Health
        print("\n🏥 System Health:")
        healthy, health_status = self.get_system_health()
        status_icon = "✅" if healthy else "❌"
        print(f"   Overall: {status_icon} {'Healthy' if healthy else 'Unhealthy'}")

        for check, status in health_status.items():
            icon = "✓" if status['status'] == 'healthy' else "✗"
            print(f"   {icon} {check}: {status['status']}")

        # Request Metrics
        print("\n📈 Request Metrics:")
        request_rate = self.aggregator.get_rate('requests', 60)
        print(f"   Request Rate: {request_rate:.1f} req/min")
        print(f"   Total Requests: {self.request_count}")

        response_p50 = self.aggregator.get_percentile('response_time', 50)
        response_p95 = self.aggregator.get_percentile('response_time', 95)
        response_p99 = self.aggregator.get_percentile('response_time', 99)

        print(f"   Response Time (p50): {response_p50:.1f}ms")
        print(f"   Response Time (p95): {response_p95:.1f}ms")
        print(f"   Response Time (p99): {response_p99:.1f}ms")

        # Error Metrics
        print("\n🚨 Error Metrics:")
        error_rate = self.aggregator.get_rate('errors', 60)
        error_percentage = (self.error_count / max(self.request_count, 1)) * 100

        print(f"   Error Rate: {error_rate:.1f} errors/min")
        print(f"   Error Percentage: {error_percentage:.2f}%")
        print(f"   Total Errors: {self.error_count}")

        # Performance Metrics
        print("\n⚡ Performance Metrics:")
        print(f"   Active Spans: {len(self.active_spans)}")

        span_p50 = self.aggregator.get_percentile('span_duration', 50)
        span_p95 = self.aggregator.get_percentile('span_duration', 95)

        print(f"   Span Duration (p50): {span_p50:.1f}ms")
        print(f"   Span Duration (p95): {span_p95:.1f}ms")

        # Resource Metrics
        print("\n💾 Resource Metrics:")
        memory_usage = self.aggregator.get_current('memory_usage_mb')
        cpu_usage = self.aggregator.get_current('cpu_usage_percent')
        active_connections = self.aggregator.get_current('active_connections')

        print(f"   Memory Usage: {memory_usage:.1f} MB")
        print(f"   CPU Usage: {cpu_usage:.1f}%")
        print(f"   Active Connections: {int(active_connections)}")

        # Active Alerts
        if self.alerts:
            print("\n🔔 Active Alerts:")
            for alert in self.alerts[-5:]:  # Show last 5 alerts
                severity_icon = {
                    'critical': '🔴',
                    'warning': '🟡',
                    'info': '🔵'
                }.get(alert['severity'], '⚪')

                age = int(time.time() - alert['timestamp'])
                print(f"   {severity_icon} [{alert['type']}] {alert['message']} ({age}s ago)")

        print("\n" + "="*60)


def simulate_application_load(context, dashboard, duration=10):
    """Simulate application load for dashboard."""
    logger = Logger("app", context, INFO)

    # Metrics
    requests = Counter("requests", context)
    errors = Counter("errors", context)
    response_time = Histogram("response_time", context)
    memory_usage = Gauge("memory_usage_mb", context)
    cpu_usage = Gauge("cpu_usage_percent", context)
    connections = Gauge("active_connections", context)

    start_time = time.time()
    request_count = 0

    while time.time() - start_time < duration:
        # Simulate request
        from observability.domains.tracing import Span
        with Span("handle_request", context) as span:
            request_count += 1

            # Log request
            logger.info(f"Processing request {request_count}")
            requests.increment(1.0)

            # Simulate processing time
            import random
            processing_time = random.uniform(1, 10)  # 1-10ms (reduced)

            # Occasionally slow requests
            if random.random() < 0.1:
                processing_time = random.uniform(20, 50)  # 20-50ms (reduced)

            time.sleep(processing_time / 1000)

            # Record response time
            response_time.observe(processing_time)

            # Simulate errors
            if random.random() < 0.05:  # 5% error rate
                logger.error(f"Error processing request {request_count}")
                errors.increment(1.0)
                dashboard.add_alert('REQUEST_ERROR', f"Request {request_count} failed")

            # Update resource metrics
            memory_usage.set(random.uniform(100, 500))
            cpu_usage.set(random.uniform(10, 80))
            connections.set(random.randint(10, 50))

        # Small delay between requests
        time.sleep(0.01)  # 10ms between requests (reduced)


def main():
    """Main example logic."""
    print("=== Example 72: Monitoring Dashboard ===\n")

    # Create dashboard first (without context)
    class DashboardWrapper:
        """Wrapper to integrate dashboard as a handler."""
        def __init__(self):
            self.dashboard = None

        def __call__(self, event):
            if self.dashboard and hasattr(self.dashboard, 'handler'):
                self.dashboard.handler(event)

    dashboard_wrapper = DashboardWrapper()

    # Setup with dashboard handler
    buffer = BufferHandler()
    config = ObservabilityConfig(handlers=[buffer, dashboard_wrapper])
    context = ObservabilityContext(config)
    context.start()

    # Create dashboard with context and link it
    dashboard = Dashboard(context)
    dashboard_wrapper.dashboard = dashboard

    # Example 1: Register health checks
    print("1. Setting up health checks:")

    dashboard.register_health_check(
        'database',
        lambda: True  # Mock: always healthy
    )

    dashboard.register_health_check(
        'cache',
        lambda: time.time() % 10 > 2  # Mock: occasionally unhealthy
    )

    dashboard.register_health_check(
        'api_endpoint',
        lambda: True
    )

    print("   ✓ Health checks registered")

    # Example 2: Simulate load and monitor
    print("\n2. Starting application simulation...")
    print("   (Dashboard will update every 2 seconds)")

    # Start load simulation in background
    load_thread = threading.Thread(
        target=simulate_application_load,
        args=(context, dashboard, 1)  # Run for 1 second
    )
    load_thread.daemon = True
    load_thread.start()

    # Update dashboard periodically (reduced for faster execution)
    for i in range(3):
        time.sleep(0.3)  # 300ms intervals, 0.9s total
        dashboard.render()

    # Example 3: Alert patterns
    print("\n3. Alert pattern examples:")

    # Simulate various alerts
    dashboard.add_alert('MEMORY_HIGH', 'Memory usage above 80%', 'warning')
    dashboard.add_alert('LATENCY_SPIKE', 'p99 latency > 500ms', 'critical')
    dashboard.add_alert('DEPLOYMENT', 'New version deployed', 'info')

    dashboard.render()

    # Example 4: Custom metrics
    print("\n4. Custom metric tracking:")

    # Add custom business metrics
    orders = Counter("orders_placed", context)
    revenue = Counter("revenue_usd", context)
    cart_size = Histogram("cart_size", context)

    # Simulate business events
    for _ in range(20):
        orders.increment(1.0)
        revenue.increment(random.uniform(10, 200))
        cart_size.observe(random.randint(1, 10))

    print("   ✓ Custom metrics tracked")

    # Example 5: Performance analysis
    print("\n5. Performance analysis:")

    events = buffer.get_events()

    # Analyze trace data
    spans = [e for e in events if e['type'] == 'trace.span_end']
    if spans:
        durations = []
        for span in spans:
            start_events = [
                e for e in events
                if e['type'] == 'trace.span_start' and
                e['value'].get('span_id') == span['value'].get('span_id')
            ]
            if start_events:
                duration = span['timestamp'] - start_events[0]['timestamp']
                durations.append(duration * 1000)  # Convert to ms

        if durations:
            avg_duration = sum(durations) / len(durations)
            print(f"\n   Average span duration: {avg_duration:.2f}ms")
            print(f"   Total spans: {len(durations)}")

    # Best practices
    print("\n6. Dashboard monitoring best practices:")
    print("   - Track key business and technical metrics")
    print("   - Set up meaningful health checks")
    print("   - Define clear alert thresholds")
    print("   - Monitor percentiles, not just averages")
    print("   - Track error rates and types")
    print("   - Include resource utilization metrics")
    print("   - Keep historical data for trends")
    print("   - Make dashboards actionable")

    context.stop()


if __name__ == '__main__':
    import random
    main()
