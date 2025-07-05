#!/usr/bin/env python3
"""
Example 70: Web Framework Integration

Demonstrates:
- Flask/FastAPI integration patterns
- Request/response logging
- Automatic tracing
- Error tracking
- Performance monitoring
"""

import sys
import time
import json
from functools import wraps
from contextlib import contextmanager
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler, BufferHandler
from observability.domains.logging import Logger, INFO, ERROR
from observability.domains.tracing import Span
from observability.domains.metrics import Counter, Histogram


# Mock web framework classes (simulating Flask/FastAPI)
class Request:
    """Mock HTTP request."""
    def __init__(self, method='GET', path='/', headers=None, body=None):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.body = body
        self.args = {}

class Response:
    """Mock HTTP response."""
    def __init__(self, body, status_code=200, headers=None):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}


class ObservabilityMiddleware:
    """Web framework observability middleware."""

    def __init__(self, app, context, app_name="web_app"):
        self.app = app
        self.context = context
        self.app_name = app_name

        # Initialize domains
        self.logger = Logger(f"{app_name}.requests", context, INFO)
        self.request_counter = Counter(f"{app_name}_requests", context)
        self.error_counter = Counter(f"{app_name}_errors", context)
        self.response_time = Histogram(f"{app_name}_response_time", context)

    def __call__(self, request, handler):
        """Process request with observability."""
        # Start request span
        with Span(
            f"{request.method} {request.path}",
            self.context
        ) as span:
            span.set_attribute('http.method', request.method)
            span.set_attribute('http.path', request.path)
            span.set_attribute('http.user_agent', request.headers.get('User-Agent', 'unknown'))

            # Add trace ID to request
            request.trace_id = span.span_id

            # Log request
            self.logger.info(
                f"Incoming request: {request.method} {request.path}",
                extra={
                    'trace_id': span.span_id,
                    'method': request.method,
                    'path': request.path
                }
            )

            # Count request
            self.request_counter.increment(
                1.0,
                method=request.method,
                path=request.path
            )

            # Time the request
            start_time = time.time()

            try:
                # Call actual handler
                response = handler(request)

                # Log response
                self.logger.info(
                    f"Request completed: {response.status_code}",
                    extra={
                        'trace_id': span.span_id,
                        'status_code': response.status_code,
                        'duration': time.time() - start_time
                    }
                )

                # Track response time
                self.response_time.observe(
                    (time.time() - start_time) * 1000,  # milliseconds
                    method=request.method,
                    path=request.path,
                    status=str(response.status_code)
                )

                # Count errors
                if response.status_code >= 400:
                    self.error_counter.increment(
                        1.0,
                        method=request.method,
                        path=request.path,
                        status=str(response.status_code)
                    )

                # Add trace ID to response headers
                response.headers['X-Trace-Id'] = span.span_id

                return response

            except Exception as e:
                # Log error
                self.logger.error(
                    f"Request failed: {str(e)}",
                    extra={
                        'trace_id': span.span_id,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )

                # Count error
                self.error_counter.increment(
                    1.0,
                    method=request.method,
                    path=request.path,
                    error_type=type(e).__name__
                )

                # Re-raise
                raise


def observable_route(context, name=None):
    """Decorator for observable route handlers."""
    def decorator(func):
        logger = Logger(name or func.__name__, context, INFO)

        @wraps(func)
        def wrapper(*args, **kwargs):
            with Span(f"handler.{func.__name__}", context) as span:
                try:
                    logger.debug(f"Executing {func.__name__}")
                    result = func(*args, **kwargs)
                    logger.debug(f"Completed {func.__name__}")
                    return result
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {e}")
                    span.add_event("error", {'message': str(e)})
                    raise

        return wrapper
    return decorator


class WebApplication:
    """Mock web application."""

    def __init__(self, context):
        self.routes = {}
        self.middleware = ObservabilityMiddleware(self, context)
        self.context = context

    def route(self, path, methods=['GET']):
        """Route decorator."""
        def decorator(func):
            for method in methods:
                self.routes[(method, path)] = func
            return func
        return decorator

    def handle_request(self, request):
        """Handle HTTP request."""
        handler = self.routes.get((request.method, request.path))

        if not handler:
            return Response("Not Found", 404)

        # Apply middleware
        return self.middleware(request, handler)


def main():
    """Main example logic."""
    print("=== Example 70: Web Framework Integration ===\n")

    # Setup
    buffer = BufferHandler()
    config = ObservabilityConfig(handlers=[
        PrintHandler(sys.stdout, format="[{category}] {type}: {value}"),
        buffer
    ])
    context = ObservabilityContext(config)
    context.start()

    # Example 1: Basic web app integration
    print("1. Basic web application integration:")

    app = WebApplication(context)

    # Define routes
    @app.route('/api/users')
    @observable_route(context, "users_handler")
    def get_users(request):
        """Get users endpoint."""
        # Simulate database query
        time.sleep(0.05)
        return Response(json.dumps({'users': ['alice', 'bob']}))

    @app.route('/api/users/<id>')
    @observable_route(context, "user_detail_handler")
    def get_user(request, user_id=None):
        """Get user detail endpoint."""
        if user_id == '999':
            raise ValueError("User not found")

        time.sleep(0.03)
        return Response(json.dumps({'id': user_id, 'name': 'Alice'}))

    # Simulate requests
    requests = [
        Request('GET', '/api/users'),
        Request('GET', '/api/users/123'),
        Request('GET', '/api/users/999'),  # Will error
        Request('POST', '/api/users'),  # Not found
    ]

    for req in requests:
        try:
            resp = app.handle_request(req)
            print(f"   {req.method} {req.path} -> {resp.status_code}")
        except Exception as e:
            print(f"   {req.method} {req.path} -> ERROR: {e}")

    # Example 2: Request context pattern
    print("\n2. Request context pattern:")

    class RequestContext:
        """Store request-scoped data."""
        def __init__(self):
            self._data = {}

        def set(self, key, value):
            self._data[key] = value

        def get(self, key, default=None):
            return self._data.get(key, default)

        @contextmanager
        def request_scope(self, request):
            """Create request scope."""
            # Store request data
            self._data['request_id'] = request.headers.get('X-Request-Id', str(time.time()))
            self._data['user_id'] = request.headers.get('X-User-Id', 'anonymous')
            self._data['trace_id'] = getattr(request, 'trace_id', None)

            yield self

            # Clear request data
            self._data.clear()

    # Enhanced middleware with context
    class ContextualMiddleware(ObservabilityMiddleware):
        def __init__(self, app, context, request_context):
            super().__init__(app, context)
            self.request_context = request_context

        def __call__(self, request, handler):
            with self.request_context.request_scope(request):
                # Add context to logs
                self.logger = Logger(
                    f"{self.app_name}.requests",
                    self.context,
                    INFO,
                    extra={
                        'request_id': self.request_context.get('request_id'),
                        'user_id': self.request_context.get('user_id')
                    }
                )

                return super().__call__(request, handler)

    # Example 3: Database query tracing
    print("\n3. Database query tracing:")

    class DatabaseTracer:
        """Trace database queries."""
        def __init__(self, context):
            self.context = context
            self.logger = Logger("database", context, INFO)

        @contextmanager
        def query(self, sql, params=None):
            """Trace a query."""
            with Span("db.query", self.context) as span:
                span.set_attribute('db.statement', sql[:100])  # Truncate for safety
                span.set_attribute('db.type', 'sql')
                start = time.time()

                try:
                    # Simulate query execution
                    time.sleep(0.02)

                    duration = time.time() - start
                    self.logger.debug(
                        f"Query completed in {duration:.3f}s",
                        extra={'duration': duration, 'sql': sql[:50]}
                    )

                    yield  # Query executes here

                except Exception as e:
                    self.logger.error(f"Query failed: {e}")
                    span.add_event("error", {'message': str(e)})
                    raise

    db_tracer = DatabaseTracer(context)

    # Use in route
    @app.route('/api/data')
    def get_data(request):
        logger = Logger("api.data", context, INFO)
        logger.info("Fetching data")

        # Trace DB queries
        with db_tracer.query("SELECT * FROM users WHERE active = ?", [True]):
            pass  # Query executes

        with db_tracer.query("SELECT COUNT(*) FROM orders"):
            pass  # Another query

        return Response(json.dumps({'data': 'example'}))

    # Test
    app.handle_request(Request('GET', '/api/data'))

    # Example 4: Error tracking
    print("\n4. Enhanced error tracking:")

    class ErrorTracker:
        """Track and analyze errors."""
        def __init__(self, context):
            self.context = context
            self.logger = Logger("errors", context, ERROR)
            self.error_counter = Counter("app_errors", context)

        def track_error(self, error, request=None):
            """Track an error with context."""
            error_data = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': time.time()
            }

            if request:
                error_data.update({
                    'method': request.method,
                    'path': request.path,
                    'trace_id': getattr(request, 'trace_id', None)
                })

            # Log error
            self.logger.error(
                f"{error_data['error_type']}: {error_data['error_message']}",
                extra=error_data
            )

            # Count error
            self.error_counter.increment(
                1.0,
                error_type=error_data['error_type'],
                path=error_data.get('path', 'unknown')
            )

            # Emit error event
            self.context.emit({
                'type': 'error.tracked',
                'timestamp': time.time(),
                'category': 'error',
                'value': error_data
            })

    error_tracker = ErrorTracker(context)

    # Example 5: Performance monitoring
    print("\n5. Performance monitoring patterns:")

    # Analyze collected metrics
    events = buffer.get_events()

    # Response time analysis
    response_times = [
        e['measurement']
        for e in events
        if e['type'] == 'metric.histogram' and 'response_time' in e.get('name', '')
    ]

    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"\n   Average response time: {avg_time:.2f}ms")
        print(f"   Min: {min(response_times):.2f}ms")
        print(f"   Max: {max(response_times):.2f}ms")

    # Error rate
    total_requests = len([e for e in events if e['type'] == 'metric.counter' and 'requests' in str(e['value'])])
    total_errors = len([e for e in events if e['type'] == 'metric.counter' and 'errors' in str(e['value'])])

    if total_requests > 0:
        error_rate = (total_errors / total_requests) * 100
        print(f"\n   Error rate: {error_rate:.1f}%")

    # Best practices
    print("\n6. Web framework integration best practices:")
    print("   - Use middleware for automatic instrumentation")
    print("   - Add trace IDs to all requests")
    print("   - Track request/response metrics")
    print("   - Log with structured context")
    print("   - Trace database queries and external calls")
    print("   - Monitor error rates and types")
    print("   - Set performance budgets and alerts")
    print("   - Use request context for correlation")

    context.stop()


if __name__ == '__main__':
    main()
