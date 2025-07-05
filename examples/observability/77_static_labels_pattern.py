#!/usr/bin/env python3
"""
Example 77: Static Labels Pattern

Demonstrates:
- Using static labels with metric constructors
- Kwargs as metric labels
- Label inheritance patterns  
- Multi-dimensional metrics
- Best practices for label usage
"""

import sys
import random
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import JsonHandler, BufferHandler
from observability.domains.metrics import Counter, Gauge, Histogram


def create_service_metrics(context, service_name, environment):
    """Create metrics with static service labels."""
    # Counter with static labels
    request_counter = Counter(
        "requests_total",
        context,
        unit="1",
        description="Total number of requests",
        # Static labels as kwargs
        service=service_name,
        environment=environment,
        version="2.1.0"
    )

    # Gauge with static labels
    memory_gauge = Gauge(
        "memory_usage_bytes",
        context,
        unit="bytes",
        description="Current memory usage",
        service=service_name,
        environment=environment,
        host="server-01"
    )

    # Histogram with static labels
    response_histogram = Histogram(
        "response_time_ms",
        context,
        buckets=[10, 25, 50, 100, 250, 500, 1000],
        unit="milliseconds",
        description="Response time distribution",
        service=service_name,
        environment=environment,
        datacenter="us-east-1"
    )

    return request_counter, memory_gauge, response_histogram


def simulate_multi_service_traffic(context):
    """Simulate traffic across multiple services with consistent labeling."""
    services = [
        ("api-gateway", "production"),
        ("api-gateway", "staging"),
        ("auth-service", "production"),
        ("auth-service", "staging"),
        ("data-service", "production")
    ]

    # Create metrics for each service
    service_metrics = {}
    for service, env in services:
        metrics = create_service_metrics(context, service, env)
        service_metrics[(service, env)] = metrics

    # Simulate traffic
    print("   Simulating traffic for services:")
    for _ in range(20):
        # Pick random service
        service, env = random.choice(services)
        request_counter, memory_gauge, response_histogram = service_metrics[(service, env)]

        # Increment requests with dynamic labels
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        path = random.choice(["/users", "/orders", "/products"])
        status_code = random.choices([200, 400, 500], weights=[0.9, 0.08, 0.02])[0]

        request_counter.increment(
            1.0,
            # Dynamic labels added to static ones
            method=method,
            path=path,
            status_code=status_code
        )

        # Update memory
        memory_gauge.set(
            random.randint(100_000_000, 500_000_000),
            # Can add dynamic labels here too
            gc_count=random.randint(0, 100)
        )

        # Record response time
        response_time = random.uniform(10, 200)
        response_histogram.observe(
            response_time,
            method=method,
            path=path,
            cache_hit=random.choice([True, False])
        )

    print(f"   Generated metrics for {len(services)} service/environment combinations")


def demonstrate_label_patterns(context):
    """Demonstrate various label patterns and best practices."""
    # Pattern 1: Hierarchical labels
    print("\n3. Hierarchical label organization:")

    api_requests = Counter(
        "api_requests",
        context,
        # High-level static labels
        component="frontend",
        tier="web",
        region="us-east"
    )

    # Add more specific labels dynamically
    api_requests.increment(1.0,
        # Mid-level labels
        service="user-api",
        version="v2",
        # Low-level labels
        endpoint="/users/{id}",
        client_type="mobile"
    )

    # Pattern 2: Environment-specific metrics
    print("\n4. Environment-specific metric creation:")

    # Development metrics with debug labels
    if True:  # In dev environment
        db_connections = Gauge(
            "database_connections",
            context,
            environment="development",
            debug_enabled=True,
            connection_pool="hikari",
            max_pool_size=10
        )
    else:
        # Production metrics with minimal labels
        db_connections = Gauge(
            "database_connections",
            context,
            environment="production"
        )

    # Pattern 3: Multi-tenant metrics
    print("\n5. Multi-tenant metric patterns:")

    tenant_usage = Counter(
        "tenant_api_usage",
        context,
        unit="requests",
        # Platform-level labels
        platform="saas",
        deployment="multi-tenant"
    )

    # Track per-tenant usage
    tenants = ["acme-corp", "globex-inc", "init-tech"]
    for tenant in tenants:
        for _ in range(random.randint(5, 15)):
            tenant_usage.increment(1.0,
                tenant_id=tenant,
                plan=random.choice(["free", "pro", "enterprise"]),
                feature=random.choice(["api", "ui", "reports"])
            )


def analyze_label_cardinality(buffer):
    """Analyze label combinations from captured metrics."""
    events = buffer.get_events()

    # Extract unique label combinations
    label_combinations = {}

    for event in events:
        if event['type'].startswith('metric.'):
            labels = event.get('labels', {})
            value = event.get('value', {})
            metric_name = value.get('name', 'unknown') if isinstance(value, dict) else 'unknown'

            if metric_name not in label_combinations:
                label_combinations[metric_name] = set()

            # Create label combination key
            label_key = tuple(sorted(labels.items()))
            label_combinations[metric_name].add(label_key)

    print("\n6. Label cardinality analysis:")
    for metric, combinations in sorted(label_combinations.items()):
        print(f"   {metric}: {len(combinations)} unique label combinations")

        # Show sample combinations
        for combo in list(combinations)[:3]:
            label_str = ", ".join([f"{k}={v}" for k, v in combo])
            print(f"     - {{{label_str}}}")

        if len(combinations) > 3:
            print(f"     ... and {len(combinations) - 3} more")


def main():
    """Main example logic."""
    print("=== Example 77: Static Labels Pattern ===\n")

    # Setup
    buffer = BufferHandler()
    config = ObservabilityConfig(handlers=[
        JsonHandler(sys.stdout, indent=2),
        buffer
    ])
    context = ObservabilityContext(config)
    context.start()

    # Example 1: Basic static labels
    print("1. Creating metrics with static labels:")

    # Service-level metrics with consistent labels
    api_requests = Counter(
        "http_requests_total",
        context,
        unit="1",
        description="Total HTTP requests",
        # Static labels for service identification
        service="api",
        environment="production",
        instance="api-prod-001",
        datacenter="us-east-1"
    )

    # Use the counter with additional dynamic labels
    api_requests.increment(1.0, method="GET", path="/health", status=200)
    api_requests.increment(1.0, method="POST", path="/users", status=201)
    api_requests.increment(1.0, method="GET", path="/users/123", status=404)

    print("   Created counter with static service labels")

    # Example 2: Multi-service simulation
    print("\n2. Multi-service metrics with consistent labeling:")
    simulate_multi_service_traffic(context)

    # Example 3-5: Label patterns
    demonstrate_label_patterns(context)

    # Example 6: Analyze cardinality
    analyze_label_cardinality(buffer)

    # Best practices
    print("\n7. Static label best practices:")
    print("   - Use static labels for deployment context (service, env, region)")
    print("   - Keep static label cardinality low")
    print("   - Use consistent label names across metrics")
    print("   - Document label schemas for your organization")
    print("   - Consider label hierarchy (general → specific)")
    print("   - Monitor total cardinality to avoid explosion")
    print("   - Use static labels for grouping/filtering")
    print("   - Dynamic labels for request-specific context")

    context.stop()


if __name__ == '__main__':
    main()
