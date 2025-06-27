"""
Tests for custom domain implementation.

Demonstrates how to create custom observability domains that integrate
with the system.
"""

import pytest
import contextvars
from typing import Final, Optional, Dict, Any
from observability import ObservabilityContext, request_id


def test_custom_domain_implementation():
    """Custom domains integrate with the system."""
    # Define custom domain
    class SecurityAuditor:
        """Custom domain for security events."""
        
        AUDIT_PREFIX: Final[str] = "security.audit"
        
        def __init__(self, context):
            self._context = context
        
        def login_attempt(self, username: str, success: bool):
            if not self._context.has_handlers():
                return
            
            self._context.emit(
                f"{self.AUDIT_PREFIX}.login",
                {"username": username, "success": success},
                severity="info" if success else "warning"
            )
        
        def permission_check(self, user: str, resource: str, granted: bool):
            if not self._context.has_handlers():
                return
                
            self._context.emit(
                f"{self.AUDIT_PREFIX}.permission",
                {"user": user, "resource": resource, "granted": granted}
            )
    
    # Use custom domain
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    auditor = SecurityAuditor(context)
    auditor.login_attempt("alice", True)
    auditor.permission_check("alice", "/admin", False)
    
    assert len(events) == 2
    assert events[0]['type'] == 'security.audit.login'
    assert events[0]['value']['username'] == 'alice'
    assert events[0]['severity'] == 'info'
    assert events[1]['type'] == 'security.audit.permission'
    assert events[1]['value']['granted'] is False


def test_custom_domain_with_context():
    """Custom domains can use context variables."""
    # Custom context variable
    user_id = contextvars.ContextVar('user_id', default=None)
    
    class APITracker:
        def __init__(self, context):
            self._context = context
        
        def track_call(self, method: str, path: str):
            if not self._context.has_handlers():
                return
            
            # Capture custom context
            metadata = {"method": method, "path": path}
            if uid := user_id.get():
                metadata['user_id'] = uid
            
            self._context.emit("api.call", metadata)
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    tracker = APITracker(context)
    
    # Set context and track
    request_id.set('req-789')
    user_id.set('user-123')
    tracker.track_call('GET', '/api/profile')
    
    event = events[0]
    assert event['request_id'] == 'req-789'
    assert event['value']['user_id'] == 'user-123'
    assert event['value']['method'] == 'GET'


def test_custom_domain_specific_handler():
    """Custom handlers can process domain-specific events."""
    
    class BusinessMetricsHandler:
        """Handler that only processes business metrics."""
        
        def __init__(self):
            self.revenue_total = 0.0
            self.order_count = 0
        
        def __call__(self, event):
            if event['type'] == 'business.order.completed':
                self.order_count += 1
                self.revenue_total += event['value']['amount']
            elif event['type'] == 'business.refund.processed':
                self.revenue_total -= event['value']['amount']
    
    # Business domain
    class BusinessTracker:
        def __init__(self, context):
            self._context = context
        
        def order_completed(self, order_id: str, amount: float):
            self._context.emit(
                'business.order.completed',
                {'order_id': order_id, 'amount': amount}
            )
        
        def refund_processed(self, order_id: str, amount: float):
            self._context.emit(
                'business.refund.processed',
                {'order_id': order_id, 'amount': amount}
            )
    
    # Wire together
    handler = BusinessMetricsHandler()
    context = ObservabilityContext()
    context.attach_handler(handler)
    
    tracker = BusinessTracker(context)
    
    # Track business events
    tracker.order_completed('ORD-001', 99.99)
    tracker.order_completed('ORD-002', 150.00)
    tracker.refund_processed('ORD-001', 99.99)
    
    assert handler.order_count == 2
    assert handler.revenue_total == 150.00


def test_custom_cache_domain():
    """Example: Cache monitoring domain."""
    
    class CacheMonitor:
        """Domain for cache operation monitoring."""
        
        def __init__(self, cache_name: str, context):
            self._cache_name = cache_name
            self._context = context
        
        def hit(self, key: str, latency_ms: float):
            if not self._context.has_handlers():
                return
            
            self._context.emit(
                'cache.hit',
                {
                    'cache': self._cache_name,
                    'key': key,
                    'latency_ms': latency_ms
                }
            )
        
        def miss(self, key: str, latency_ms: float):
            if not self._context.has_handlers():
                return
                
            self._context.emit(
                'cache.miss',
                {
                    'cache': self._cache_name,
                    'key': key,
                    'latency_ms': latency_ms
                }
            )
        
        def eviction(self, key: str, reason: str):
            if not self._context.has_handlers():
                return
                
            self._context.emit(
                'cache.eviction',
                {
                    'cache': self._cache_name,
                    'key': key,
                    'reason': reason
                }
            )
    
    # Use cache monitor
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    monitor = CacheMonitor('user_cache', context)
    
    # Simulate cache operations
    monitor.hit('user:123', 0.5)
    monitor.miss('user:456', 1.2)
    monitor.eviction('user:789', 'ttl_expired')
    
    assert len(events) == 3
    assert events[0]['type'] == 'cache.hit'
    assert events[0]['value']['latency_ms'] == 0.5
    assert events[1]['type'] == 'cache.miss'
    assert events[2]['type'] == 'cache.eviction'
    assert events[2]['value']['reason'] == 'ttl_expired'


def test_custom_database_domain():
    """Example: Database query monitoring domain."""
    
    class DatabaseMonitor:
        """Domain for database query monitoring."""
        
        def __init__(self, db_name: str, context):
            self._db_name = db_name
            self._context = context
            self._query_stack = []
        
        def query_start(self, query: str, params: Optional[Dict] = None):
            if not self._context.has_handlers():
                return
            
            import time
            query_id = f"{self._db_name}_{len(self._query_stack)}_{int(time.time() * 1000)}"
            
            self._query_stack.append({
                'id': query_id,
                'start_time': time.perf_counter()
            })
            
            self._context.emit(
                'db.query.start',
                {
                    'database': self._db_name,
                    'query_id': query_id,
                    'query': query,
                    'params': params or {}
                }
            )
            
            return query_id
        
        def query_end(self, query_id: str, rows_affected: int = 0, error: Optional[str] = None):
            if not self._context.has_handlers():
                return
            
            import time
            # Find and remove query from stack
            query_info = None
            for i, q in enumerate(self._query_stack):
                if q['id'] == query_id:
                    query_info = self._query_stack.pop(i)
                    break
            
            if not query_info:
                return
            
            duration_ms = (time.perf_counter() - query_info['start_time']) * 1000
            
            self._context.emit(
                'db.query.end',
                {
                    'database': self._db_name,
                    'query_id': query_id,
                    'duration_ms': duration_ms,
                    'rows_affected': rows_affected,
                    'success': error is None,
                    'error': error
                }
            )
    
    # Use database monitor
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    monitor = DatabaseMonitor('users_db', context)
    
    # Simulate query
    query_id = monitor.query_start("SELECT * FROM users WHERE id = ?", {'id': 123})
    import time
    time.sleep(0.01)  # Simulate query time
    monitor.query_end(query_id, rows_affected=1)
    
    assert len(events) == 2
    assert events[0]['type'] == 'db.query.start'
    assert events[0]['value']['query'] == "SELECT * FROM users WHERE id = ?"
    assert events[1]['type'] == 'db.query.end'
    assert events[1]['value']['success'] is True
    assert events[1]['value']['duration_ms'] >= 10


def test_custom_domain_with_filtering():
    """Custom domains work with category filtering."""
    
    class FeatureFlagMonitor:
        """Domain for feature flag evaluation monitoring."""
        
        def __init__(self, context):
            self._context = context
        
        def flag_evaluated(self, flag_name: str, user: str, result: bool):
            if not self._context.has_handlers():
                return
            
            self._context.emit(
                'feature.flag.evaluated',
                {
                    'flag': flag_name,
                    'user': user,
                    'result': result
                }
            )
    
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    # Enable only 'feature' category
    context.enable_category('feature')
    
    monitor = FeatureFlagMonitor(context)
    
    # These should pass
    monitor.flag_evaluated('new_ui', 'user123', True)
    monitor.flag_evaluated('beta_api', 'user456', False)
    
    # Try to emit other category (should be filtered)
    context.emit('log.info', 'This is filtered')
    
    assert len(events) == 2
    assert all(e['type'].startswith('feature.') for e in events)


def test_custom_domain_composability():
    """Multiple custom domains can work together."""
    
    # Performance monitoring domain
    class PerformanceMonitor:
        def __init__(self, context):
            self._context = context
        
        def operation_timing(self, operation: str, duration_ms: float):
            if not self._context.has_handlers():
                return
            
            self._context.emit(
                'perf.timing',
                {
                    'operation': operation,
                    'duration_ms': duration_ms,
                    'slow': duration_ms > 100
                }
            )
    
    # Error tracking domain
    class ErrorTracker:
        def __init__(self, context):
            self._context = context
        
        def exception_caught(self, error_type: str, message: str, stack_trace: str):
            if not self._context.has_handlers():
                return
            
            self._context.emit(
                'error.exception',
                {
                    'type': error_type,
                    'message': message,
                    'stack_trace': stack_trace
                }
            )
    
    # Use both domains together
    events = []
    context = ObservabilityContext()
    context.attach_handler(lambda e: events.append(e))
    
    perf = PerformanceMonitor(context)
    errors = ErrorTracker(context)
    
    # Simulate slow operation with error
    perf.operation_timing('database_query', 250.5)
    errors.exception_caught('TimeoutError', 'Query timeout', 'stack trace here...')
    perf.operation_timing('cache_lookup', 0.5)
    
    assert len(events) == 3
    assert events[0]['type'] == 'perf.timing'
    assert events[0]['value']['slow'] is True
    assert events[1]['type'] == 'error.exception'
    assert events[2]['value']['slow'] is False