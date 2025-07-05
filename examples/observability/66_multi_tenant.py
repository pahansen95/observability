#!/usr/bin/env python3
"""
Example 66: Multi-Tenant

Demonstrates:
- Context per tenant
- Isolation between contexts
- Tenant-specific handlers
- Adding tenant ID to events
- Concurrent tenant operations
"""

import sys
import threading
import time
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler, PrintHandler, filtered
from observability.domains.logging import Logger, INFO
from observability.domains.metrics import Counter


class TenantManager:
    """Manages observability contexts per tenant."""
    def __init__(self):
        self.tenants = {}
        self.lock = threading.Lock()

    def get_context(self, tenant_id):
        """Get or create context for tenant."""
        with self.lock:
            if tenant_id not in self.tenants:
                self.tenants[tenant_id] = self._create_tenant_context(tenant_id)
            return self.tenants[tenant_id]['context']

    def _create_tenant_context(self, tenant_id):
        """Create isolated context for tenant."""
        # Tenant-specific buffer
        buffer = BufferHandler()

        # Tenant-specific handler that adds tenant_id
        class TenantHandler:
            def __init__(self, tenant_id, wrapped):
                self.tenant_id = tenant_id
                self.wrapped = wrapped

            def __call__(self, event):
                # Add tenant_id to all events
                event['tenant_id'] = self.tenant_id
                self.wrapped(event)

        # Create handler pipeline
        tenant_handler = TenantHandler(
            tenant_id,
            PrintHandler(sys.stdout, format=f"[{tenant_id}] {{type}}: {{value}}")
        )

        # Create context
        config = ObservabilityConfig(handlers=[tenant_handler, buffer])
        context = ObservabilityContext(config)
        context.start()

        return {
            'context': context,
            'buffer': buffer,
            'tenant_id': tenant_id
        }

    def get_tenant_events(self, tenant_id):
        """Get events for specific tenant."""
        with self.lock:
            if tenant_id in self.tenants:
                return self.tenants[tenant_id]['buffer'].get_events()
            return []

    def shutdown_tenant(self, tenant_id):
        """Shutdown tenant context."""
        with self.lock:
            if tenant_id in self.tenants:
                self.tenants[tenant_id]['context'].stop()
                del self.tenants[tenant_id]


def simulate_tenant_activity(manager, tenant_id, duration=1.0):
    """Simulate activity for a tenant."""
    context = manager.get_context(tenant_id)
    logger = Logger(f"{tenant_id}.app", context, INFO)
    counter = Counter(f"{tenant_id}_requests", context)

    start_time = time.time()
    request_count = 0

    while time.time() - start_time < duration:
        # Log activity
        logger.info(f"Processing request {request_count}")

        # Update metrics
        counter.increment(1.0, endpoint="/api/data")

        # Simulate work
        time.sleep(0.1)
        request_count += 1

    logger.info(f"Completed {request_count} requests")


def main():
    """Main example logic."""
    print("=== Example 66: Multi-Tenant ===\n")

    # Create tenant manager
    manager = TenantManager()

    # Example 1: Basic multi-tenant usage
    print("1. Basic multi-tenant usage:")

    # Create contexts for different tenants
    context_a = manager.get_context("tenant-A")
    context_b = manager.get_context("tenant-B")

    # Use tenant-specific contexts
    logger_a = Logger("service", context_a, INFO)
    logger_b = Logger("service", context_b, INFO)

    logger_a.info("Activity from tenant A")
    logger_b.info("Activity from tenant B")
    logger_a.info("More activity from tenant A")

    print("\n2. Verifying tenant isolation:")

    # Check events are isolated
    events_a = manager.get_tenant_events("tenant-A")
    events_b = manager.get_tenant_events("tenant-B")

    print(f"   Tenant A events: {len(events_a)}")
    print(f"   Tenant B events: {len(events_b)}")

    # Verify tenant_id in events
    for event in events_a:
        assert event.get('tenant_id') == 'tenant-A'
    for event in events_b:
        assert event.get('tenant_id') == 'tenant-B'

    print("   ✓ Events properly isolated by tenant")

    # Example 3: Concurrent tenant operations
    print("\n3. Concurrent tenant operations:")

    threads = []
    tenants = ["tenant-X", "tenant-Y", "tenant-Z"]

    # Start concurrent activity
    for tenant_id in tenants:
        thread = threading.Thread(
            target=simulate_tenant_activity,
            args=(manager, tenant_id, 0.5)
        )
        thread.start()
        threads.append(thread)

    # Wait for completion
    for thread in threads:
        thread.join()

    # Check results
    print("\n   Activity summary:")
    for tenant_id in tenants:
        events = manager.get_tenant_events(tenant_id)
        log_events = [e for e in events if e['type'].startswith('log.')]
        metric_events = [e for e in events if e['type'].startswith('metric.')]
        print(f"   {tenant_id}: {len(log_events)} logs, {len(metric_events)} metrics")

    # Example 4: Tenant-specific configuration
    print("\n4. Tenant-specific handler configuration:")

    class TenantConfigManager(TenantManager):
        def _create_tenant_context(self, tenant_id):
            """Create context with tenant-specific config."""
            # Different configs for different tenant tiers
            if tenant_id.endswith("-premium"):
                # Premium tenants get detailed logging
                handlers = [
                    PrintHandler(sys.stdout, format="[PREMIUM-{tenant_id}] {type}: {value}"),
                    BufferHandler()  # No size limit
                ]
            else:
                # Free tenants get limited logging
                handlers = [
                    filtered(
                        lambda e: e.get('level', 0) >= 30,  # WARNING+
                        PrintHandler(sys.stdout, format="[FREE] {value}")
                    ),
                    BufferHandler(max_size=100)  # Limited buffer
                ]

            config = ObservabilityConfig(handlers=handlers)
            context = ObservabilityContext(config)
            context.start()

            return {'context': context, 'buffer': handlers[-1], 'tenant_id': tenant_id}

    config_manager = TenantConfigManager()

    # Test different tiers
    premium_ctx = config_manager.get_context("customer-premium")
    free_ctx = config_manager.get_context("customer-free")

    premium_logger = Logger("app", premium_ctx, INFO)
    free_logger = Logger("app", free_ctx, INFO)

    print("\n   Testing tier-based configuration:")
    premium_logger.info("Premium tenant info")
    free_logger.info("Free tenant info (filtered)")

    premium_logger.warning("Premium warning")
    free_logger.warning("Free tenant warning (shown)")

    # Example 5: Tenant lifecycle
    print("\n5. Tenant lifecycle management:")

    # Simulate tenant onboarding
    new_tenant = "tenant-NEW"
    print(f"\n   Onboarding {new_tenant}...")

    new_context = manager.get_context(new_tenant)
    new_logger = Logger("onboarding", new_context, INFO)
    new_logger.info("Tenant onboarded successfully")

    # Simulate tenant offboarding
    print(f"\n   Offboarding {new_tenant}...")

    # Final metrics
    events = manager.get_tenant_events(new_tenant)
    print(f"   Total events for {new_tenant}: {len(events)}")

    # Shutdown
    manager.shutdown_tenant(new_tenant)
    print(f"   {new_tenant} context shutdown complete")

    # Best practices
    print("\n6. Multi-tenant best practices:")
    print("   - One context per tenant for isolation")
    print("   - Add tenant_id to all events")
    print("   - Use tenant-specific handler configs")
    print("   - Monitor resource usage per tenant")
    print("   - Implement tenant quotas/limits")
    print("   - Clean up contexts on tenant departure")


if __name__ == '__main__':
    main()
