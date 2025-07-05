#!/usr/bin/env python3
"""
Example 73: Span Events and Status

Demonstrates:
- Adding events to spans with add_event()
- Setting span status with set_status()
- Tracking operation progress
- Error status reporting patterns
- Event attributes and metadata
"""

import sys
import time
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import JsonHandler, BufferHandler
from observability.domains.tracing import Span


def process_payment(amount, currency, context):
    """Simulate payment processing with detailed event tracking."""
    with Span("payment_process", context) as span:
        # Add initial event
        span.add_event("payment_initiated", {
            "amount": amount,
            "currency": currency,
            "timestamp": time.time()
        })
        
        # Simulate validation
        time.sleep(0.01)
        span.add_event("payment_validated", {
            "validation_result": "passed",
            "rules_checked": ["amount_limit", "fraud_detection", "account_status"]
        })
        
        # Simulate authorization
        time.sleep(0.02)
        auth_code = "ABC123"
        span.add_event("payment_authorized", {
            "auth_code": auth_code,
            "processor": "stripe",
            "response_time_ms": 20
        })
        
        # Simulate capture
        time.sleep(0.01)
        transaction_id = "TXN-20240105-001"
        span.add_event("payment_captured", {
            "transaction_id": transaction_id,
            "final_amount": amount,
            "fees": amount * 0.029  # 2.9% fee
        })
        
        # Set success status
        span.set_status(True, "Payment completed successfully")
        
        return transaction_id


def process_payment_with_error(amount, context):
    """Simulate payment processing that fails."""
    with Span("payment_process_failed", context) as span:
        # Add initial event
        span.add_event("payment_initiated", {
            "amount": amount,
            "currency": "USD"
        })
        
        # Simulate validation
        time.sleep(0.01)
        
        # Simulate authorization failure
        span.add_event("payment_authorization_failed", {
            "error_code": "INSUFFICIENT_FUNDS",
            "error_message": "The card has insufficient funds",
            "decline_reason": "generic_decline"
        })
        
        # Set error status
        span.set_status(False, "Payment authorization failed: INSUFFICIENT_FUNDS")
        
        return None


def track_order_fulfillment(order_id, context):
    """Track order fulfillment with multiple stages."""
    with Span("order_fulfillment", context) as span:
        span.set_attribute("order_id", order_id)
        
        # Order received
        span.add_event("order_received", {
            "order_id": order_id,
            "items_count": 3,
            "total_value": 149.99
        })
        
        # Inventory check
        time.sleep(0.01)
        span.add_event("inventory_checked", {
            "all_items_available": True,
            "warehouse": "EAST-1"
        })
        
        # Payment processing (nested span)
        with span.start_child("process_payment") as payment_span:
            payment_span.add_event("payment_started", {"method": "credit_card"})
            time.sleep(0.02)
            payment_span.add_event("payment_completed", {"transaction_id": "TXN-123"})
            payment_span.set_status(True, "Payment successful")
        
        # Shipping label
        time.sleep(0.01)
        span.add_event("shipping_label_created", {
            "carrier": "UPS",
            "tracking_number": "1Z999AA10123456784",
            "estimated_delivery": "2024-01-08"
        })
        
        # Order complete
        span.add_event("order_completed", {
            "final_status": "ready_to_ship",
            "processing_time_ms": 50
        })
        
        span.set_status(True, f"Order {order_id} processed successfully")


def main():
    """Main example logic."""
    print("=== Example 73: Span Events and Status ===\n")
    
    # Setup
    buffer = BufferHandler()
    config = ObservabilityConfig(handlers=[
        JsonHandler(sys.stdout, indent=2),
        buffer
    ])
    context = ObservabilityContext(config)
    context.start()
    
    # Example 1: Successful payment with events
    print("1. Processing successful payment with detailed events:")
    txn_id = process_payment(99.99, "USD", context)
    print(f"   Transaction completed: {txn_id}")
    
    # Example 2: Failed payment with error status
    print("\n2. Processing payment that fails:")
    failed_txn = process_payment_with_error(1999.99, context)
    print(f"   Transaction result: {failed_txn}")
    
    # Example 3: Complex order fulfillment tracking
    print("\n3. Tracking order fulfillment with nested operations:")
    track_order_fulfillment("ORD-2024-0105", context)
    
    # Example 4: Analyze span events
    print("\n4. Analyzing span events from buffer:")
    events = buffer.get_events()
    
    span_events = [e for e in events if 'span.event' in e['type']]
    print(f"   Total span events: {len(span_events)}")
    
    # Group events by span
    events_by_span = {}
    for event in span_events:
        value = event.get('value', {})
        span_id = value.get('span_id', 'unknown') if isinstance(value, dict) else 'unknown'
        if span_id not in events_by_span:
            events_by_span[span_id] = []
        events_by_span[span_id].append(event)
    
    print(f"   Events per span:")
    for span_id, span_events in events_by_span.items():
        event_names = [e.get('value', {}).get('name', 'unnamed') for e in span_events]
        print(f"     - Span {span_id[:8]}: {', '.join(event_names)}")
    
    # Check status events
    status_events = [e for e in events if e['type'] == 'span.end']
    print(f"\n   Span statuses:")
    for event in status_events:
        value = event.get('value', {})
        if isinstance(value, str):
            # Simple string value, use as operation name
            operation = value
            status = {}
            ok = True  # Assume success if no explicit status
            message = ''
        else:
            # Complex value with details
            operation = value.get('operation', 'unknown')
            status = value.get('status', {})
            ok = status.get('ok', True)  # Default to success
            message = status.get('message', '')
        print(f"     - {operation}: {'✓' if ok else '✗'} {message}")
    
    # Best practices
    print("\n5. Best practices for span events and status:")
    print("   - Use add_event() for significant operation milestones")
    print("   - Include relevant attributes in event data")
    print("   - Set meaningful status messages for debugging")
    print("   - Use False status for any operation failures")
    print("   - Track both success and failure paths")
    print("   - Nest spans for sub-operations")
    
    context.stop()


if __name__ == '__main__':
    main()