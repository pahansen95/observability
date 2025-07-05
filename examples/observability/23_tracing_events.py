#!/usr/bin/env python3
"""
Example 23: Tracing Events

Demonstrates:
- Emitting custom events within spans
- Events with attributes
- Tracking span success/failure through attributes
- Exception handling in spans
- Examining span end events
"""

from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler, JsonHandler
from observability.domains.tracing import Span
import sys


def main():
    """Main example logic."""
    print("=== Example 23: Tracing Events ===\n")

    # Create context with handlers
    print("1. Creating context with BufferHandler and JsonHandler")
    buffer_handler = BufferHandler()
    json_handler = JsonHandler(sys.stdout)
    config = ObservabilityConfig(handlers=[buffer_handler, json_handler])
    context = ObservabilityContext(config)
    context.start()

    # Create span and emit events manually
    print("\n2. Creating span and emitting events:")
    with Span("process_order", context) as span:
        span.set_attribute("order_id", "ORD-12345")

        # Emit event with no attributes
        context.emit("order.received", "order_received", span_id=span.span_id)
        print("   Emitted event: order_received")

        # Emit event with attributes
        context.emit("payment.processed", "payment_processed",
                    span_id=span.span_id,
                    amount=99.99,
                    currency="USD",
                    payment_method="credit_card")
        print("   Emitted event: payment_processed with attributes")

        # Emit multiple events
        context.emit("inventory.checked", "inventory_checked",
                    span_id=span.span_id,
                    items_available=True)
        context.emit("shipping.calculated", "shipping_calculated",
                    span_id=span.span_id,
                    shipping_cost=5.99,
                    estimated_days=3)
        print("   Emitted events: inventory_checked, shipping_calculated")

        # Track success through attributes
        span.set_attribute("status", "success")
        print("   Set status attribute: success")

    # Create span with failure status
    print("\n3. Creating span with failure status:")
    with Span("validate_input", context) as span:
        context.emit("validation.started", "validation_started", span_id=span.span_id)

        # Simulate validation failure
        validation_errors = ["missing_field: email", "invalid_format: phone"]
        context.emit("validation.failed", "validation_failed",
                    span_id=span.span_id,
                    errors=validation_errors,
                    error_count=len(validation_errors))

        # Track failure through attributes
        span.set_attribute("status", "failed")
        span.set_attribute("status_message", "Validation failed with 2 errors")
        print("   Set status attributes: failed with reason")

    # Demonstrate exception handling
    print("\n4. Demonstrating exception in span:")
    try:
        with Span("risky_operation", context) as span:
            context.emit("operation.started", "operation_started", span_id=span.span_id)

            # Simulate some work
            context.emit("checkpoint.reached", "checkpoint_1_reached",
                        span_id=span.span_id, checkpoint=1)

            # Raise an exception
            raise ValueError("Something went wrong!")

    except ValueError as e:
        print(f"   Exception caught: {e}")
        print("   Note: Span automatically tracks error in end event")

    # Create span with mixed events and status changes
    print("\n5. Span with multiple status changes:")
    with Span("retry_operation", context) as span:
        # First attempt
        context.emit("attempt.started", "attempt_1_started",
                    span_id=span.span_id, attempt=1)
        context.emit("attempt.failed", "attempt_1_failed",
                    span_id=span.span_id, attempt=1, reason="timeout")
        span.set_attribute("attempt_1_status", "failed")

        # Second attempt
        context.emit("attempt.started", "attempt_2_started",
                    span_id=span.span_id, attempt=2)
        context.emit("attempt.succeeded", "attempt_2_succeeded",
                    span_id=span.span_id, attempt=2)
        span.set_attribute("final_status", "success")
        print("   Multiple attempts with final success status")

    # Examine captured events
    print("\n6. Examining span events and custom events:")
    events = buffer_handler.get_events()

    # Find different event types
    span_starts = [e for e in events if e['type'] == 'span.start']
    span_ends = [e for e in events if e['type'] == 'span.end']
    custom_events = [e for e in events if e['type'] not in ['span.start', 'span.end']]

    print(f"   Total span starts: {len(span_starts)}")
    print(f"   Total span ends: {len(span_ends)}")
    print(f"   Total custom events: {len(custom_events)}")

    # Show custom event details
    print("\n7. Custom event details:")
    for i, event in enumerate(custom_events[:3]):
        print(f"   Event {i+1}:")
        print(f"     Type: {event.get('type')}")
        print(f"     Name: {event.get('name')}")
        if 'span_id' in event:
            print(f"     Span ID: {event.get('span_id')}")
        # Show other attributes
        for key, value in event.items():
            if key not in ['type', 'name', 'span_id', 'timestamp', 'category']:
                print(f"     {key}: {value}")

    # Show span end information
    print("\n8. Span end information:")
    for end_event in span_ends:
        operation = end_event.get('name')
        success = end_event.get('success')
        error = end_event.get('error')
        duration_ns = end_event.get('duration_ns', 0)
        print(f"   {operation}:")
        print(f"     Success: {success}")
        if error:
            print(f"     Error: {error}")
        print(f"     Duration: {duration_ns / 1_000_000:.2f}ms")

    context.stop()


if __name__ == '__main__':
    main()
