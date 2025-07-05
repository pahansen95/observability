#!/usr/bin/env python3
"""
Example 21: Tracing Nested

Demonstrates:
- Creating parent span
- Using start_child() to create child spans
- Creating grandchild spans
- Verifying parent_id relationships
- Spans completing in reverse order
- Span tree visualization
"""

from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import BufferHandler, PrintHandler
from observability.domains.tracing import Span


def main():
    """Main example logic."""
    print("=== Example 21: Tracing Nested ===\n")

    # Create context with handlers
    print("1. Creating context with handlers")
    buffer_handler = BufferHandler()
    print_handler = PrintHandler(format="[{type}] {operation} (span_id={span_id}, parent_id={parent_id})")
    config = ObservabilityConfig(handlers=[buffer_handler, print_handler])
    context = ObservabilityContext(config)
    context.start()

    # Create parent span
    print("\n2. Creating parent span")
    with Span("http_request", context) as parent_span:
        print(f"   Parent span ID: {parent_span.span_id}")

        # Create child spans using start_child()
        print("\n3. Creating child spans with start_child()")

        # First child: authentication
        with parent_span.start_child("authenticate") as auth_span:
            print(f"   Auth span ID: {auth_span.span_id}")
            print(f"   Auth parent ID: {auth_span.parent_id}")
            auth_span.set_attribute("auth_method", "jwt")

            # Grandchild: token validation
            with auth_span.start_child("validate_token") as token_span:
                print(f"   Token span ID: {token_span.span_id}")
                print(f"   Token parent ID: {token_span.parent_id}")
                token_span.set_attribute("token_type", "bearer")

        # Second child: database query
        with parent_span.start_child("database_query") as db_span:
            db_span.set_attribute("query_type", "select")
            db_span.set_attribute("table", "users")

            # Grandchild: connection pool
            with db_span.start_child("get_connection") as conn_span:
                conn_span.set_attribute("pool_size", 10)

        # Third child: response formatting
        with parent_span.start_child("format_response") as format_span:
            format_span.set_attribute("format", "json")

    print("\n4. All spans completed (in reverse order)")

    # Examine span relationships
    print("\n5. Examining span relationships:")
    events = buffer_handler.get_events()
    span_starts = [e for e in events if e['type'] == 'trace.span.start']

    # Build span tree
    spans = {}
    for event in span_starts:
        span_id = event['span_id']
        parent_id = event.get('parent_id')
        operation = event['operation']
        spans[span_id] = {
            'operation': operation,
            'parent_id': parent_id,
            'children': []
        }

    # Link children to parents
    for span_id, span_info in spans.items():
        parent_id = span_info['parent_id']
        if parent_id and parent_id in spans:
            spans[parent_id]['children'].append(span_id)

    # Print span tree
    print("\n6. Span tree visualization:")
    def print_span_tree(span_id, indent=0):
        if span_id not in spans:
            return
        span = spans[span_id]
        print("   " + "  " * indent + f"└─ {span['operation']} ({span_id[:8]}...)")
        for child_id in span['children']:
            print_span_tree(child_id, indent + 1)

    # Find root span(s)
    root_spans = [sid for sid, info in spans.items() if not info['parent_id']]
    for root_id in root_spans:
        print_span_tree(root_id)

    # Verify parent-child relationships
    print("\n7. Parent-child relationship verification:")
    for span_id, span_info in spans.items():
        operation = span_info['operation']
        parent_id = span_info['parent_id']
        if parent_id:
            parent_op = spans[parent_id]['operation']
            print(f"   {operation} -> parent: {parent_op}")

    context.stop()


if __name__ == '__main__':
    main()
