#!/usr/bin/env python3
"""
Example 68: Custom Domain

Demonstrates:
- Creating custom event domains
- Domain-specific event types
- Custom domain configuration
- Domain event validation
- Integration with existing domains
"""

import sys
import time
from observability import ObservabilityContext, ObservabilityConfig
from observability.handlers import PrintHandler, BufferHandler



class AuditDomain:
    """Custom domain for audit events."""

    # Audit event types
    CREATED = "audit.created"
    UPDATED = "audit.updated"
    DELETED = "audit.deleted"
    ACCESSED = "audit.accessed"
    PERMISSION_CHANGED = "audit.permission_changed"
    LOGIN = "audit.login"
    LOGOUT = "audit.logout"

    def __init__(self, context):
        self.context = context

    def _emit_audit_event(self, event_type, resource, action, user, details=None):
        """Emit an audit event."""
        value = {
            'resource': resource,
            'action': action,
            'user': user,
            'details': details or {}
        }

        # Emit with audit-specific metadata
        self.context.emit(
            event_type,
            value,
            category="audit",
            audit_version="1.0",
            compliance=True
        )

    def created(self, resource, user, **details):
        """Log resource creation."""
        self._emit_audit_event(
            self.CREATED,
            resource,
            "create",
            user,
            details
        )

    def updated(self, resource, user, changes=None, **details):
        """Log resource update."""
        details['changes'] = changes or {}
        self._emit_audit_event(
            self.UPDATED,
            resource,
            "update",
            user,
            details
        )

    def deleted(self, resource, user, **details):
        """Log resource deletion."""
        self._emit_audit_event(
            self.DELETED,
            resource,
            "delete",
            user,
            details
        )

    def accessed(self, resource, user, permission, **details):
        """Log resource access."""
        details['permission'] = permission
        self._emit_audit_event(
            self.ACCESSED,
            resource,
            "access",
            user,
            details
        )

    def permission_changed(self, resource, user, old_perms, new_perms, **details):
        """Log permission changes."""
        details['old_permissions'] = old_perms
        details['new_permissions'] = new_perms
        self._emit_audit_event(
            self.PERMISSION_CHANGED,
            resource,
            "permission_change",
            user,
            details
        )

    def login(self, user, ip_address, success=True, **details):
        """Log login attempt."""
        details['ip_address'] = ip_address
        details['success'] = success
        self._emit_audit_event(
            self.LOGIN,
            "auth_system",
            "login",
            user,
            details
        )

    def logout(self, user, **details):
        """Log logout."""
        self._emit_audit_event(
            self.LOGOUT,
            "auth_system",
            "logout",
            user,
            details
        )


class SecurityDomain:
    """Custom domain for security events."""

    # Security event types
    THREAT_DETECTED = "security.threat_detected"
    SCAN_COMPLETED = "security.scan_completed"
    VULNERABILITY_FOUND = "security.vulnerability_found"
    INCIDENT_CREATED = "security.incident_created"

    # Severity levels
    CRITICAL = 50
    HIGH = 40
    MEDIUM = 30
    LOW = 20
    INFO = 10

    def __init__(self, context):
        self.context = context

    def threat_detected(self, threat_type, source, severity, details=None):
        """Log detected threat."""
        value = {
            'threat_type': threat_type,
            'source': source,
            'severity': severity,
            'severity_name': self._severity_name(severity),
            'details': details or {}
        }

        # Add alerting hint for critical threats
        metadata = {
            'category': 'security'
        }
        if severity >= self.CRITICAL:
            metadata['alert'] = True
            metadata['priority'] = 'immediate'

        self.context.emit(self.THREAT_DETECTED, value, **metadata)

    def scan_completed(self, scan_type, target, findings):
        """Log security scan completion."""
        value = {
            'scan_type': scan_type,
            'target': target,
            'findings_count': len(findings),
            'findings': findings
        }

        self.context.emit(self.SCAN_COMPLETED, value, category="security")

    def _severity_name(self, severity):
        """Get severity name."""
        if severity >= self.CRITICAL:
            return "CRITICAL"
        elif severity >= self.HIGH:
            return "HIGH"
        elif severity >= self.MEDIUM:
            return "MEDIUM"
        elif severity >= self.LOW:
            return "LOW"
        else:
            return "INFO"


def main():
    """Main example logic."""
    print("=== Example 68: Custom Domain ===\n")

    # Setup
    buffer = BufferHandler()
    config = ObservabilityConfig(handlers=[
        PrintHandler(sys.stdout, format="[{category}] {type}: {value}"),
        buffer
    ])
    context = ObservabilityContext(config)
    context.start()

    # Example 1: Audit domain usage
    print("1. Audit domain usage:")

    audit = AuditDomain(context)

    # Simulate user actions
    audit.login("user123", "192.168.1.100", success=True)

    audit.created(
        resource="document/12345",
        user="user123",
        title="Quarterly Report",
        size=1024
    )

    audit.accessed(
        resource="document/12345",
        user="user456",
        permission="read"
    )

    audit.updated(
        resource="document/12345",
        user="user123",
        changes={
            'title': {'old': 'Quarterly Report', 'new': 'Q4 Report'},
            'updated_at': time.time()
        }
    )

    audit.permission_changed(
        resource="document/12345",
        user="admin",
        old_perms={'user456': ['read']},
        new_perms={'user456': ['read', 'write']}
    )

    audit.logout("user123", session_duration=3600)

    # Example 2: Security domain usage
    print("\n2. Security domain usage:")

    security = SecurityDomain(context)

    # Simulate security events
    security.threat_detected(
        threat_type="sql_injection",
        source="api/users?id=1 OR 1=1",
        severity=security.HIGH,
        details={
            'ip': '10.0.0.50',
            'user_agent': 'suspicious-bot/1.0'
        }
    )

    security.scan_completed(
        scan_type="vulnerability",
        target="web-app-v2.1",
        findings=[
            {'type': 'outdated_dependency', 'package': 'requests==2.20.0'},
            {'type': 'weak_crypto', 'location': 'auth.py:45'}
        ]
    )

    security.threat_detected(
        threat_type="brute_force",
        source="login_endpoint",
        severity=security.CRITICAL,
        details={
            'attempts': 1000,
            'time_window': 60,
            'blocked': True
        }
    )

    # Example 3: Custom domain with validation
    print("\n3. Custom domain with validation:")

    class ValidatedDomain:
        """Domain with event validation."""

        def __init__(self, context):
            self.context = context
            self.schema = {
                'required_fields': ['entity_id', 'action', 'timestamp'],
                'valid_actions': ['create', 'read', 'update', 'delete']
            }

        def emit_validated(self, event_type, data):
            """Emit event with validation."""
            # Validate required fields
            for field in self.schema['required_fields']:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate action
            if 'action' in data and data['action'] not in self.schema['valid_actions']:
                raise ValueError(f"Invalid action: {data['action']}")

            # Emit validated event
            self.context.emit(
                event_type,
                data,
                category="validated",
                validated=True
            )

    validated = ValidatedDomain(context)

    try:
        # Valid event
        validated.emit_validated("validated.event", {
            'entity_id': 'user-789',
            'action': 'update',
            'timestamp': time.time(),
            'fields': ['email', 'profile']
        })
        print("   ✓ Valid event emitted")

        # Invalid event (missing field)
        validated.emit_validated("validated.event", {
            'action': 'update'
        })
    except ValueError as e:
        print(f"   ✗ Validation error: {e}")

    # Example 4: Domain composition
    print("\n4. Domain composition pattern:")

    class BusinessDomain:
        """Composite domain using multiple domains."""

        def __init__(self, context):
            self.audit = AuditDomain(context)
            self.security = SecurityDomain(context)
            self.context = context

        def sensitive_operation(self, user, resource, operation):
            """Perform operation with full observability."""
            # Audit the access
            self.audit.accessed(resource, user, operation)

            # Check for security concerns
            if operation == "delete" and resource.startswith("critical/"):
                self.security.threat_detected(
                    threat_type="critical_deletion_attempt",
                    source=f"{user}@{resource}",
                    severity=self.security.MEDIUM,
                    details={'operation': operation}
                )

            # Business event
            value = {
                'user': user,
                'resource': resource,
                'operation': operation,
                'risk_score': self._calculate_risk(user, resource, operation)
            }

            self.context.emit(
                "business.sensitive_operation",
                value,
                category="business"
            )

        def _calculate_risk(self, user, resource, operation):
            """Calculate risk score."""
            score = 0
            if resource.startswith("critical/"):
                score += 50
            if operation in ["delete", "modify_permissions"]:
                score += 30
            if user.startswith("external_"):
                score += 20
            return min(score, 100)

    business = BusinessDomain(context)
    business.sensitive_operation("external_contractor", "critical/database", "delete")

    # Example 5: Analyzing custom domain events
    print("\n5. Custom domain event analysis:")

    events = buffer.get_events()

    # Count by category
    by_category = {}
    for event in events:
        category = event.get('category', 'unknown')
        by_category[category] = by_category.get(category, 0) + 1

    print("\n   Events by category:")
    for category, count in by_category.items():
        print(f"   - {category}: {count} events")

    # Find critical events
    critical_events = [
        e for e in events
        if e.get('alert') or e.get('value', {}).get('severity', 0) >= 40
    ]

    print(f"\n   Critical events: {len(critical_events)}")
    for event in critical_events:
        print(f"   - {event['type']}: {event.get('value', {}).get('threat_type', 'N/A')}")

    # Best practices
    print("\n6. Custom domain best practices:")
    print("   - Define clear event types and schemas")
    print("   - Include domain-specific metadata")
    print("   - Validate events before emission")
    print("   - Use composition for complex domains")
    print("   - Document domain semantics")
    print("   - Consider domain-specific handlers")

    context.stop()


if __name__ == '__main__':
    main()
