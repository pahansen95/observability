# Observability Framework Examples

This directory contains comprehensive examples demonstrating all capabilities of the Observability Framework. The examples are organized in a progressive learning path from basic usage to advanced production patterns.

## Table of Contents

- [Quick Start](#quick-start)
- [Example Categories](#example-categories)
- [Learning Path](#learning-path)
- [Running Examples](#running-examples)
- [Example Index](#example-index)
- [API Coverage](#api-coverage)
- [Troubleshooting](#troubleshooting)

## Quick Start

```bash
# Run a basic example
python examples/observability/01_basic_setup.py

# Run with the virtual environment
.venv/bin/python3 examples/observability/01_basic_setup.py
```

## Example Categories

### 🏗️ Foundation (01-06)
Core concepts and basic usage of ObservabilityContext.

### 📊 Domains (10-33)
Logging, tracing, and metrics domain functionality.

### 🔧 Handlers (40-51)
All handler types and composition patterns.

### 🚀 Advanced (60-72)
Production patterns, performance, and integrations.

## Learning Path

### Beginner Path
1. Start with `01_basic_setup.py` - Context lifecycle
2. Move to `10_logging_basics.py` - Simple logging
3. Try `30_metrics_counter.py` - Basic metrics
4. Explore `40_handler_print.py` - Output handling

### Intermediate Path
1. Study `20_tracing_basics.py` - Distributed tracing
2. Learn `45_handler_filtered.py` - Event filtering
3. Practice `51_handler_composition.py` - Complex pipelines
4. Review `63_testing_patterns.py` - Testing approach

### Advanced Path
1. Analyze `60_zero_overhead_proof.py` - Performance
2. Implement `66_multi_tenant.py` - Isolation patterns
3. Deploy `69_production_config.py` - Production setup
4. Integrate `70_integration_web_framework.py` - Web apps

## Running Examples

### Prerequisites
- Python 3.8+
- Observability package installed
- No external dependencies required

### Basic Execution
```bash
# Run any example directly
python examples/observability/XX_example_name.py

# Import path setup (if needed)
export PYTHONPATH="${PYTHONPATH}:./src"
```

### Expected Output
Each example produces console output demonstrating its features:
- Clear section headers
- Explanatory messages
- Actual framework output
- Summary of concepts

## Example Index

### Foundation Examples (01-06)

| Example | Description | Key Concepts |
|---------|-------------|--------------|
| 01_basic_setup.py | Context lifecycle management | ObservabilityContext, start/stop |
| 02_configuration.py | Configuration options | ObservabilityConfig, immutability |
| 03_shared_context.py | Singleton context pattern | SharedContext, global access |
| 04_context_variables.py | Context propagation | trace_id, request_id, operation_id |
| 05_event_emission.py | Event emission patterns | emit(), metadata, has_handlers() |
| 06_category_filtering.py | Category-based filtering | enable_category(), disable_category() |

### Logging Domain (10-12)

| Example | Description | Key Concepts |
|---------|-------------|--------------|
| 10_logging_basics.py | Logger fundamentals | Severity levels, filtering |
| 11_logging_hierarchical.py | Logger hierarchy | getChild(), inheritance |
| 12_logging_structured.py | Structured logging | kwargs, metadata |

### Tracing Domain (20-23)

| Example | Description | Key Concepts |
|---------|-------------|--------------|
| 20_tracing_basics.py | Span lifecycle | Context manager, attributes |
| 21_tracing_nested.py | Parent-child spans | start_child(), relationships |
| 22_tracing_async.py | Async tracing | asyncio support, concurrency |
| 23_tracing_events.py | Span events | add_event(), set_status() |

### Metrics Domain (30-33)

| Example | Description | Key Concepts |
|---------|-------------|--------------|
| 30_metrics_counter.py | Monotonic counters | increment(), labels |
| 31_metrics_gauge.py | Gauge metrics | set(), increment(), decrement() |
| 32_metrics_histogram.py | Distribution tracking | observe(), buckets |
| 33_metrics_timer.py | Duration measurement | Timer context manager |

### Handler Examples (40-51)

| Example | Description | Key Concepts |
|---------|-------------|--------------|
| 40_handler_print.py | Console output | Format strings, include_context |
| 41_handler_json.py | JSON serialization | indent, sort_keys |
| 42_handler_file.py | File writing | Rotation, lifecycle |
| 43_handler_buffer.py | Memory buffer | max_size, get_events() |
| 44_handler_queued.py | Async processing | Worker threads, queue_size |
| 45_handler_filtered.py | Event filtering | Predicates, lambda filters |
| 46_handler_sampled.py | Statistical sampling | Rate, deterministic seed |
| 47_handler_timedelta.py | Time enrichment | time_delta_ns field |
| 48_handler_fanout.py | Multi-handler broadcast | Error isolation |
| 49_handler_fallback.py | Error recovery | Fallback chains |
| 50_handler_lifecycle.py | Start/stop management | Lifecycle ordering |
| 51_handler_composition.py | Complex pipelines | Multi-level trees |

### Advanced Examples (60-72)

| Example | Description | Key Concepts |
|---------|-------------|--------------|
| 60_zero_overhead_proof.py | Performance validation | <1ns overhead proof |
| 61_high_volume_patterns.py | High throughput | Batching, sampling |
| 62_error_handling.py | Error resilience | Isolation, recovery |
| 63_testing_patterns.py | Testing approach | BufferHandler, assertions |
| 64_debugging_observability.py | Self-inspection | Debug handlers, flow tracing |
| 65_migration_pattern.py | Python logging migration | Compatibility bridge |
| 66_multi_tenant.py | Tenant isolation | Per-tenant contexts |
| 67_correlation_patterns.py | Request correlation | Trace propagation |
| 68_custom_domain.py | Domain extension | Custom event types |
| 69_production_config.py | Production setup | Complete configuration |
| 70_integration_web_framework.py | Web integration | Middleware patterns |
| 71_integration_async_app.py | Async integration | AsyncIO patterns |
| 72_monitoring_dashboard.py | Live monitoring | Real-time aggregation |

### Extended API Coverage (73-77)
| Example | Description | Key API Features |
|---------|-------------|------------------|
| 73_span_events_status.py | Span events and status | add_event(), set_status() |
| 74_logger_enabled_check.py | Conditional logging | is_enabled_for() |
| 75_timer_proper_usage.py | Timer measurement | Timer class |
| 76_handler_protocols.py | Protocol implementation | EventHandler, ManagedHandler |
| 77_static_labels_pattern.py | Metric static labels | kwargs labels |

## API Coverage

### Core Module (`observability`)
- ✅ ObservabilityContext: All methods demonstrated
- ✅ ObservabilityConfig: All parameters shown
- ✅ SharedContext: Complete singleton usage
- ✅ Context variables: trace_id, request_id, operation_id

### Handlers Module (`observability.handlers`)
- ✅ PrintHandler: Format customization
- ✅ JsonHandler: Serialization options
- ✅ ManagedFileHandler: File rotation
- ✅ BufferHandler: Event capture
- ✅ QueuedHandler: Async processing
- ✅ filtered(): Predicate filtering
- ✅ sampled(): Statistical sampling
- ✅ TimeDeltaHandler: Time enrichment
- ✅ FanoutHandler: Multi-handler dispatch
- ✅ FallbackHandler: Error recovery

### Domain Modules
- ✅ Logger: All severity methods, hierarchical naming
- ✅ Span: Context manager, parent-child, attributes
- ✅ Counter, Gauge, Histogram: All metric types
- ✅ Timer: Duration measurement

## Performance Characteristics

Based on `60_zero_overhead_proof.py`:
- **No handlers**: <1ns per call (single boolean check)
- **With handler**: ~100ns per call
- **Suitable for**: Hot path instrumentation

## Troubleshooting

### Import Errors
```bash
# Set Python path
export PYTHONPATH="${PYTHONPATH}:./src"

# Or run from project root
python -m examples.observability.01_basic_setup
```

### Missing Dependencies
The examples only require the observability package and Python standard library.

### API Differences
Some examples have been adapted to work with implementation differences from the API specification. See comments in individual examples for details.

## Contributing

When adding new examples:
1. Follow the numbering scheme
2. Include clear docstrings
3. Add to this README index
4. Test with both Python 3.8+
5. Keep external dependencies to zero

## License

These examples are part of the Observability Framework and follow the same license terms.