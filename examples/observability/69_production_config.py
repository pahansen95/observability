#!/usr/bin/env python3
"""
Example 69: Production Configuration

Demonstrates:
- Production-ready configuration patterns
- Environment-based configuration
- Handler chain optimization
- Resource limits and quotas
- Monitoring and alerting setup
"""

import os
import sys
import time
from pathlib import Path
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import (
    QueuedHandler, ManagedFileHandler,
    sampled, filtered
)
from observability.domains.logging import Logger, INFO, WARNING, ERROR
from observability.domains.metrics import Counter, Histogram



class ProductionConfig:
    """Production configuration builder."""

    def __init__(self, env='production'):
        self.env = env
        self.handlers = []

    def add_file_handler(self, base_path="/var/log/app"):
        """Add rotating file handler."""
        # Create separate files for different categories
        categories = {
            'log': 'app.log',
            'metric': 'metrics.log',
            'trace': 'traces.log',
            'audit': 'audit.log'
        }

        for category, filename in categories.items():
            handler = filtered(
                lambda e, cat=category: e.get('category') == cat,
                ManagedFileHandler(
                    str(Path(base_path) / filename)
                )
            )
            self.handlers.append(handler)

        return self

    def add_metrics_aggregator(self, flush_interval=60.0):
        """Add metrics aggregation handler."""
        class MetricsAggregator:
            def __init__(self):
                self.metrics = {}
                self.last_flush = time.time()
                self.flush_interval = flush_interval

            def __call__(self, event):
                if event['type'].startswith('metric.'):
                    # Aggregate metrics
                    metric_name = event['value'].get('name', 'unknown')
                    metric_type = event['type'].split('.')[1]

                    if metric_name not in self.metrics:
                        self.metrics[metric_name] = {
                            'type': metric_type,
                            'values': [],
                            'count': 0
                        }

                    self.metrics[metric_name]['values'].append(
                        event['value'].get('value', 0)
                    )
                    self.metrics[metric_name]['count'] += 1

                    # Check if we should flush
                    if time.time() - self.last_flush > self.flush_interval:
                        self.flush()

            def flush(self):
                """Flush aggregated metrics."""
                # In production, send to metrics backend
                print(f"Flushing {len(self.metrics)} metrics")
                self.metrics.clear()
                self.last_flush = time.time()

        self.handlers.append(MetricsAggregator())
        return self

    def add_error_alerting(self, webhook_url=None):
        """Add error alerting handler."""
        class ErrorAlerter:
            def __init__(self, webhook_url):
                self.webhook_url = webhook_url
                self.error_counts = {}
                self.alert_threshold = 10
                self.window_size = 300  # 5 minutes

            def __call__(self, event):
                # Check for errors
                if (event.get('level', 0) >= ERROR or
                    event.get('type', '').endswith('.error')):

                    # Track error rate
                    current_time = time.time()
                    self.error_counts = {
                        t: c for t, c in self.error_counts.items()
                        if current_time - t < self.window_size
                    }
                    self.error_counts[current_time] = 1

                    # Check threshold
                    if len(self.error_counts) >= self.alert_threshold:
                        self.send_alert(event)

            def send_alert(self, event):
                """Send alert (mock in example)."""
                print(f"🚨 ALERT: High error rate detected! Last error: {event}")
                # In production: requests.post(self.webhook_url, json=alert_data)

        if webhook_url or self.env != 'production':
            self.handlers.append(ErrorAlerter(webhook_url))

        return self

    def add_sampling(self, rates=None):
        """Add sampling for high-volume events."""
        default_rates = {
            'trace.span_start': 0.1,  # 10% of traces
            'metric.counter': 0.5,    # 50% of counters
            'log.debug': 0.01,        # 1% of debug logs
        }

        rates = rates or default_rates

        # Create sampled handler
        def should_sample(event):
            event_type = event.get('type', '')

            # Check specific rates
            for pattern, rate in rates.items():
                if event_type.startswith(pattern):
                    return hash(str(event)) % 100 < (rate * 100)

            # Default: don't sample
            return True

        # Create a custom sampling handler
        # Since sampled() only takes a rate, we need a different approach
        # We'll use filtered() with sampled() for each rate
        new_handlers = []

        for pattern, rate in rates.items():
            for handler in self.handlers:
                # Create filtered handler for this pattern with sampling
                pattern_handler = filtered(
                    sampled(rate, handler),
                    lambda e, p=pattern: e.get('type', '').startswith(p)
                )
                new_handlers.append(pattern_handler)

        # Add handler for unmatched events (no sampling)
        for handler in self.handlers:
            unmatched_handler = filtered(
                lambda e: not any(e.get('type', '').startswith(p) for p in rates.keys()),
                handler
            )
            new_handlers.append(unmatched_handler)

        self.handlers = new_handlers

        return self

    def add_queuing(self, max_queue_size=10000):
        """Add async queuing for performance."""
        # Queue critical handlers
        queued_handlers = []
        immediate_handlers = []

        for handler in self.handlers:
            # Keep error alerting immediate
            if hasattr(handler, '__name__') and 'ErrorAlerter' in str(handler):
                immediate_handlers.append(handler)
            else:
                queued_handlers.append(handler)

        # Create queued handler for non-critical
        if queued_handlers:
            # QueuedHandler can only wrap one handler, so use FanoutHandler if multiple
            if len(queued_handlers) > 1:
                from observability.handlers import FanoutHandler
                wrapped = FanoutHandler(*queued_handlers)
            else:
                wrapped = queued_handlers[0]

            queued = QueuedHandler(wrapped, queue_size=max_queue_size)
            self.handlers = immediate_handlers + [queued]

        return self

    def add_resource_limits(self):
        """Add resource protection."""
        class ResourceLimiter:
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.event_count = 0
                self.start_time = time.time()
                self.max_rate = 10000  # events per second

            def __call__(self, event):
                # Check rate limit
                self.event_count += 1
                elapsed = time.time() - self.start_time

                if elapsed > 1.0:
                    current_rate = self.event_count / elapsed
                    if current_rate > self.max_rate:
                        # Drop event if over limit
                        return

                    # Reset counter
                    self.event_count = 0
                    self.start_time = time.time()

                self.wrapped(event)

        # Wrap handlers with rate limiting
        self.handlers = [
            ResourceLimiter(handler)
            for handler in self.handlers
        ]

        return self

    def build(self):
        """Build configuration."""
        return ObservabilityConfig(handlers=self.handlers)


def get_production_config():
    """Get production configuration based on environment."""
    env = os.environ.get('APP_ENV', 'development')

    config_builder = ProductionConfig(env)

    if env == 'production':
        # Production settings
        config_builder.add_file_handler('/var/log/myapp')
        config_builder.add_metrics_aggregator(flush_interval=60.0)
        config_builder.add_error_alerting(
            webhook_url=os.environ.get('ALERT_WEBHOOK')
        )
        config_builder.add_sampling({
            'trace.span_start': 0.05,  # 5% sampling
            'metric.histogram': 0.1,    # 10% sampling
            'log.info': 0.5,           # 50% sampling
            'log.debug': 0.0,          # No debug logs
        })
        config_builder.add_queuing(max_queue_size=100000)
        config_builder.add_resource_limits()

    elif env == 'staging':
        # Staging settings
        config_builder.add_file_handler('/tmp/logs')
        config_builder.add_metrics_aggregator(flush_interval=30.0)
        config_builder.add_error_alerting()
        config_builder.add_sampling({
            'trace.span_start': 0.5,
            'log.debug': 0.1,
        })
        config_builder.add_queuing(max_queue_size=10000)

    else:
        # Development settings
        from observability.handlers import PrintHandler
        config_builder.handlers.append(
            PrintHandler(sys.stdout, format="[{category}] {type}: {value}")
        )
        config_builder.add_error_alerting()

    return config_builder.build()


def main():
    """Main example logic."""
    print("=== Example 69: Production Configuration ===\n")

    # Example 1: Environment-based config
    print("1. Environment-based configuration:")

    # Simulate different environments
    for env in ['development', 'staging', 'production']:
        os.environ['APP_ENV'] = env
        config = get_production_config()
        print(f"   {env}: {len(config.handlers)} handlers configured")

    # Use development for rest of example
    os.environ['APP_ENV'] = 'development'

    # Example 2: Production monitoring setup
    print("\n2. Production monitoring setup:")

    # Build production-like config
    prod_config = (ProductionConfig('demo')
        .add_metrics_aggregator(flush_interval=5.0)
        .add_error_alerting()
        .add_sampling({
            'log.info': 0.5,
            'metric.counter': 0.3
        })
        .build()
    )

    context = ObservabilityContext(prod_config)
    context.start()

    # Simulate application
    logger = Logger("app", context, INFO)
    counter = Counter("requests", context)
    errors = Counter("errors", context)

    print("\n   Simulating application load...")

    # Generate events
    for i in range(100):
        logger.info(f"Processing request {i}")
        counter.increment(1.0)

        # Simulate occasional errors
        if i % 20 == 0:
            logger.error(f"Error processing request {i}")
            errors.increment(1.0)

    # Example 3: Health monitoring
    print("\n3. Health monitoring pattern:")

    class HealthMonitor:
        """Monitor application health."""

        def __init__(self, context):
            self.context = context
            self.checks = {}

        def register_check(self, name, check_fn):
            """Register health check."""
            self.checks[name] = check_fn

        def run_checks(self):
            """Run all health checks."""
            results = {}
            healthy = True

            for name, check_fn in self.checks.items():
                try:
                    result = check_fn()
                    results[name] = {
                        'status': 'healthy' if result else 'unhealthy',
                        'checked_at': time.time()
                    }
                    if not result:
                        healthy = False
                except Exception as e:
                    results[name] = {
                        'status': 'error',
                        'error': str(e),
                        'checked_at': time.time()
                    }
                    healthy = False

            # Emit health event
            event = {
                'type': 'health.check',
                'timestamp': time.time(),
                'category': 'health',
                'value': {
                    'healthy': healthy,
                    'checks': results
                }
            }
            self.context.emit(event['type'], event['value'])

            return healthy, results

    health = HealthMonitor(context)

    # Register checks
    health.register_check('database', lambda: True)  # Mock
    health.register_check('cache', lambda: True)     # Mock
    health.register_check('disk_space', lambda: os.statvfs('/').f_bavail > 1000000)

    # Run health checks
    healthy, results = health.run_checks()
    print(f"   Health status: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
    for check, result in results.items():
        print(f"   - {check}: {result['status']}")

    # Example 4: Performance budgets
    print("\n4. Performance budget monitoring:")

    class PerformanceBudget:
        """Monitor performance against budgets."""

        def __init__(self, context):
            self.context = context
            self.histogram = Histogram("response_time", context)
            self.budgets = {
                'p50': 100,  # 50th percentile < 100ms
                'p95': 500,  # 95th percentile < 500ms
                'p99': 1000  # 99th percentile < 1000ms
            }

        def record_request(self, duration_ms):
            """Record request duration."""
            self.histogram.observe(duration_ms)

            # Check against budgets (simplified)
            if duration_ms > self.budgets['p99']:
                logger = Logger("perf", self.context, WARNING)
                logger.warning(
                    f"Request exceeded p99 budget: {duration_ms}ms > {self.budgets['p99']}ms"
                )

    perf_budget = PerformanceBudget(context)

    # Simulate requests
    import random
    for _ in range(50):
        # Simulate response times (mostly fast, some slow)
        duration = random.choices(
            [50, 100, 200, 500, 1500],
            weights=[50, 30, 15, 4, 1]
        )[0]
        perf_budget.record_request(duration)

    # Example 5: Configuration validation
    print("\n5. Configuration validation:")

    def validate_config(config):
        """Validate production configuration."""
        issues = []

        # Check handlers
        if not config.handlers:
            issues.append("No handlers configured")

        # Check for error handling
        has_error_handler = any(
            hasattr(h, '__name__') and 'error' in str(h).lower()
            for h in config.handlers
        )
        if not has_error_handler:
            issues.append("No error handler configured")

        # Check for queuing in production
        if os.environ.get('APP_ENV') == 'production':
            has_queue = any(
                isinstance(h, QueuedHandler)
                for h in config.handlers
            )
            if not has_queue:
                issues.append("No queuing configured for production")

        return len(issues) == 0, issues

    # Validate configs
    for env in ['development', 'production']:
        os.environ['APP_ENV'] = env
        config = get_production_config()
        valid, issues = validate_config(config)

        print(f"\n   {env} config: {'✓ Valid' if valid else '✗ Invalid'}")
        if issues:
            for issue in issues:
                print(f"     - {issue}")

    # Best practices
    print("\n6. Production configuration best practices:")
    print("   - Use environment-based configuration")
    print("   - Implement sampling for high-volume events")
    print("   - Add queuing for better performance")
    print("   - Set up error alerting and monitoring")
    print("   - Monitor resource usage and set limits")
    print("   - Validate configuration before deployment")
    print("   - Use structured logging for easy parsing")
    print("   - Implement health checks and metrics")

    context.stop()


if __name__ == '__main__':
    main()
