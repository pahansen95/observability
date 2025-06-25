# SharedContext

SharedContext provides application-wide coordination for observability infrastructure. It serves as the central configuration point that bridges application lifecycle with the observability subsystem, enabling ambient access to logging, tracing, and metrics throughout an application.

## Architectural Role

SharedContext represents the application's single point of control for observability configuration and lifecycle. It addresses the fundamental challenge of making observability universally accessible while maintaining proper initialization and shutdown sequences.

Key responsibilities:
- Application-wide observability configuration
- Lifecycle coordination between application and handlers
- Ambient service provision for cross-cutting concerns
- Resource management at process boundaries

## Design Implementation

### Lazy Dependency Injection

SharedContext implements a lazy dependency injection pattern that separates object creation from context binding. Domain objects accept a context provider rather than a concrete context:

```python
# Context provider type accepts either concrete context or provider function
ContextProvider = Union[ObservabilityContext, Callable[[], Optional[ObservabilityContext]]]

# Domain objects use lazy resolution
class Logger:
    def __init__(self, name: str, context: ContextProvider):
        self._context_provider = context
        self._resolved_context = None
    
    def _get_context(self):
        # Resolve context on first use
        if self._resolved_context is None:
            if callable(self._context_provider):
                self._resolved_context = self._context_provider()
            else:
                self._resolved_context = self._context_provider
        return self._resolved_context
```

This design enables module-level declarations while deferring context resolution until first use, solving initialization ordering challenges.

### Lifecycle Management

SharedContext coordinates handler lifecycle at the application level:

- **Initialization**: Accepts configuration and creates ObservabilityContext
- **Handler Registration**: Manages handler attachment and lifecycle state
- **Startup**: Coordinates handler initialization in proper order
- **Shutdown**: Ensures clean handler termination on application exit

## Usage Guidelines

SharedContext is designed for scenarios where observability serves as ambient infrastructure - universally available throughout an application without explicit propagation. Understanding when to use SharedContext versus custom contexts is crucial for maintaining clean architectural boundaries.

### Appropriate Use Cases

SharedContext excels when observability requirements align with application boundaries. Use it when:

**Unified Application Observability**: The entire application shares common observability configuration and handlers. All components emit events to the same destinations with consistent formatting and processing rules.

**Library Integration**: Packages and frameworks need to participate in the host application's observability strategy without imposing their own configuration. Libraries using SharedContext automatically inherit the host's observability settings.

**Cross-Cutting Infrastructure**: Observability serves as a true infrastructure concern that spans all application layers. Business logic remains unaware of specific observability configuration while still having access to logging, tracing, and metrics.

### Custom Context Scenarios

Create dedicated ObservabilityContext instances when isolation or specialized handling is required:

**Isolated Subsystems**: Components requiring independent observability configuration, such as data pipelines with specialized event formats or dedicated storage backends. Each subsystem maintains its own handlers and lifecycle.

**Multi-Tenant Architectures**: Systems where observability data must be strictly separated by tenant, customer, or security boundary. Each context ensures complete isolation of events and handlers.

**Specialized Processing Requirements**: Scenarios demanding unique event processing, filtering, or routing that differs from application-wide policies. Custom contexts provide fine-grained control over the entire observability pipeline.

### Decision Framework

Choose SharedContext when:
- Observability configuration is uniform across the application
- Components should inherit ambient observability settings
- Simplified configuration management is prioritized

Choose custom contexts when:
- Isolation between components is required
- Specialized handling or routing is needed
- Independent lifecycle management is necessary

## Integration Patterns

### Application Bootstrap

Configure SharedContext during application initialization:

```python
def main():
    # Parse configuration from environment/CLI
    config = parse_config()
    
    # Initialize observability
    SharedContext.setup(config.observability)
    SharedContext.attach_handler(FileHandler("app.log"))
    SharedContext.start()
    
    # Run application
    run_application()
```

### Module-Level Integration

Modules declare observability needs at import time:

```python
# business_logic.py
from observability.shared import SharedContext
from observability.logging import Logger

logger = Logger('business.logic', SharedContext.get_context)

def process_order(order):
    logger.info("Processing order", order_id=order.id)
    # Business logic here
```

### Testing Integration

Tests can provide isolated contexts while maintaining natural usage patterns:

```python
def test_business_logic():
    # Setup test observability
    SharedContext.setup(ObservabilityConfig(enabled=True))
    buffer = BufferHandler()
    SharedContext.attach_handler(buffer)
    
    # Run test
    process_order(test_order)
    
    # Verify observability
    events = buffer.get_events()
    assert any(e["message"] == "Processing order" for e in events)
```

## Design Principles

**Ambient Accessibility**: Observability infrastructure should be available throughout the application without explicit propagation.

**Deferred Initialization**: Support natural Python patterns while accommodating late configuration binding.

**Single Configuration Point**: Centralize all observability decisions in one application-controlled location.

**Zero-Overhead When Disabled**: Ensure no performance impact when observability is turned off.

## Architectural Constraints

**Process Boundary**: SharedContext operates within a single process and does not coordinate across process boundaries.

**Configuration Stability**: Core configuration remains immutable after initialization.

**Handler Autonomy**: Individual handlers manage their own resources; SharedContext only coordinates lifecycle.

**Thread Safety**: All operations are thread-safe for concurrent access.

## Summary

SharedContext provides a pragmatic solution for application-wide observability coordination. Through lazy dependency injection, it enables natural usage patterns while maintaining proper initialization order. The design acknowledges observability as ambient infrastructure, making it universally accessible without polluting business logic with infrastructure concerns.