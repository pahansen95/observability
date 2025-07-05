#!/usr/bin/env python3
"""
Example 65: Migration Pattern

Demonstrates:
- Migration from Python logging
- Adapter for existing code
- Gradual migration approach
- Compatibility patterns
- Backward compatibility maintenance
"""

import logging
import sys
from observability import ObservabilityContext, ObservabilityConfig, SharedContext
from observability.handlers import PrintHandler, BufferHandler
from observability.domains.logging import Logger, DEBUG, INFO, WARNING, ERROR, CRITICAL


class LoggingCompatHandler(logging.Handler):
    """Adapter to route Python logging to observability."""
    def __init__(self, obs_context):
        super().__init__()
        self.obs_context = obs_context
        
    def emit(self, record):
        # Map logging levels
        level_map = {
            logging.DEBUG: DEBUG,
            logging.INFO: INFO,
            logging.WARNING: WARNING,
            logging.ERROR: ERROR,
            logging.CRITICAL: CRITICAL
        }
        
        # Emit to observability
        self.obs_context.emit(
            f"log.{record.levelno}",
            record.getMessage(),
            logger=record.name,
            level=level_map.get(record.levelno, INFO),
            module=record.module,
            lineno=record.lineno
        )


def main():
    """Main example logic."""
    print("=== Example 65: Migration Pattern ===\n")
    
    # Step 1: Set up observability
    print("1. Setting up observability framework:")
    
    config = ObservabilityConfig(handlers=[
        PrintHandler(sys.stdout, format="[OBS] {logger}: {value}"),
        BufferHandler()
    ])
    SharedContext.setup(config)
    context = SharedContext.get()
    
    print("   Observability framework initialized")
    
    # Step 2: Create compatibility bridge
    print("\n2. Creating Python logging compatibility bridge:")
    
    # Add observability handler to root logger
    obs_handler = LoggingCompatHandler(context)
    logging.root.addHandler(obs_handler)
    logging.root.setLevel(logging.DEBUG)
    
    print("   Bridge installed - Python logging now routes to observability")
    
    # Step 3: Existing code continues to work
    print("\n3. Existing Python logging code:")
    
    # Old style logging
    old_logger = logging.getLogger("legacy.module")
    old_logger.info("Legacy code still works!")
    old_logger.warning("This is a warning from old code")
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        old_logger.exception("Error in legacy code")
    
    # Step 4: New code uses observability
    print("\n4. New code using observability directly:")
    
    new_logger = Logger("modern.module", context, INFO)
    new_logger.info("New code uses observability", 
                   feature="native",
                   performance="better")
    
    # Step 5: Gradual migration example
    print("\n5. Gradual migration approach:")
    
    class MigratableComponent:
        def __init__(self, use_new_logging=False):
            if use_new_logging:
                self.logger = Logger("component", context, INFO)
                self._log_info = lambda msg, **kw: self.logger.info(msg, **kw)
                self._log_error = lambda msg, **kw: self.logger.error(msg, **kw)
            else:
                self.logger = logging.getLogger("component")
                self._log_info = lambda msg, **kw: self.logger.info(msg)
                self._log_error = lambda msg, **kw: self.logger.error(msg)
                
        def process(self):
            self._log_info("Processing started")
            # Do work
            self._log_info("Processing completed", items_processed=10)
    
    # Old way
    old_component = MigratableComponent(use_new_logging=False)
    old_component.process()
    
    # New way
    new_component = MigratableComponent(use_new_logging=True)
    new_component.process()
    
    # Step 6: Feature comparison
    print("\n6. Feature comparison:")
    
    print("\n   Python logging:")
    logging.info("Simple message")
    
    print("\n   Observability with structured data:")
    obs_logger = Logger("comparison", context, INFO)
    obs_logger.info("Enhanced message",
                   user_id=123,
                   action="purchase",
                   amount=99.99,
                   items=["book", "pen"])
    
    # Step 7: Migration utilities
    print("\n7. Migration utilities:")
    
    def create_logger(name, legacy=False):
        """Factory function for gradual migration."""
        if legacy or not SharedContext.get_context():
            return logging.getLogger(name)
        else:
            return Logger(name, SharedContext.get(), INFO)
    
    # Works with both systems
    flexible_logger = create_logger("flexible.module")
    
    if isinstance(flexible_logger, Logger):
        flexible_logger.info("Using new observability system")
    else:
        flexible_logger.info("Using legacy logging")
    
    # Step 8: Best practices
    print("\n8. Migration best practices:")
    print("   - Install compatibility bridge early")
    print("   - Migrate high-value components first")
    print("   - Use feature flags for gradual rollout")
    print("   - Keep both systems during transition")
    print("   - Monitor both streams during migration")
    print("   - Remove bridge after full migration")
    
    SharedContext.teardown()


if __name__ == '__main__':
    main()