# Observability API Closure - Adhoc Phase Plan

## Overview

This adhoc phase addresses critical gaps between the API specification (`.pyi` files) and the current implementation. The API specification is authoritative, and all implementations must conform to it.

## Goals

1. Implement missing Span methods (`add_event()` and `set_status()`)
2. Add missing ObservabilityConfig property accessors
3. Add unit parameter support to metrics
4. Fix remaining type mismatches
5. Ensure 100% API specification compliance

## Phases

### Phase 1: Span Methods Implementation
**Priority: Critical**
**Timeline: 30 minutes**

#### Tasks:
1. **Implement Span.add_event()**
   - Add method to `src/observability/domains/tracing.py`
   - Match signature: `add_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None`
   - Emit `span.event` with proper structure
   - Update internal span state tracking

2. **Implement Span.set_status()**
   - Add method to `src/observability/domains/tracing.py`
   - Match signature: `set_status(ok: bool, message: str = "") -> None`
   - Store status in span attributes
   - Include status in span end event

3. **Add context manager support**
   - Ensure `__enter__` and `__exit__` are properly implemented
   - Match the protocol defined in the stub

#### Success Criteria:
- Example 73 runs without workarounds
- Span events are properly emitted and captured
- Status is included in span end events

### Phase 2: ObservabilityConfig Properties
**Priority: High**
**Timeline: 20 minutes**

#### Tasks:
1. **Add property accessors**
   - `handlers` property returning handler list
   - `sampling_rate` property (float between 0.0 and 1.0)
   - `enabled_categories` property (set of enabled categories)
   - `enabled` property (global enable/disable flag)

2. **Ensure immutability**
   - Properties should return copies/views, not direct references
   - Document property behavior in docstrings

#### Success Criteria:
- All config properties accessible as defined in stub
- Properties return appropriate types
- Config remains effectively immutable

### Phase 3: Metrics Unit Parameter
**Priority: Medium**
**Timeline: 15 minutes**

#### Tasks:
1. **Update metric constructors**
   - Add `unit` parameter to Counter, Gauge, and Histogram
   - Default to "1" as specified
   - Include unit in emitted events

2. **Update event emissions**
   - Ensure unit is included in all metric events
   - Maintain backward compatibility

#### Success Criteria:
- All metrics accept unit parameter
- Unit information preserved in events
- Examples using units work correctly

### Phase 4: Type Alignment
**Priority: Medium**
**Timeline: 15 minutes**

#### Tasks:
1. **Fix property return types**
   - Span properties should not be Optional
   - Histogram.buckets should return List[float] not tuple

2. **Fix method signatures**
   - Ensure all parameters match stub definitions
   - Fix any remaining parameter name mismatches

3. **Update type annotations**
   - Ensure implementation matches stub annotations
   - Add missing type hints

#### Success Criteria:
- No type checker errors when validating against stubs
- All return types match specifications
- Parameter types properly annotated

### Phase 5: Validation and Testing
**Priority: High**
**Timeline: 20 minutes**

#### Tasks:
1. **Run validation script**
   - Execute the API divergence checker
   - Ensure zero divergences reported

2. **Update examples**
   - Remove all workarounds from examples 73-77
   - Ensure examples use proper API methods

3. **Run comprehensive tests**
   - All examples must pass
   - No API divergence warnings

#### Success Criteria:
- Zero API divergences
- All examples run successfully
- No deprecation warnings

## Implementation Notes

### Key Principles:
1. **API Spec is Authoritative**: The `.pyi` files define the contract
2. **Backward Compatibility**: Maintain support for existing usage patterns
3. **Event Consistency**: Ensure event structures remain consistent
4. **Type Safety**: All implementations must be type-safe

### Technical Considerations:

1. **Span Events**:
   - Events should be ordered by timestamp
   - Event names should follow consistent naming patterns
   - Attributes should be properly typed

2. **Config Properties**:
   - Use `@property` decorators
   - Return immutable views where applicable
   - Cache computed values if expensive

3. **Metrics Units**:
   - Follow Prometheus unit conventions where applicable
   - Document standard units (seconds, bytes, etc.)
   - Include unit in metric help text

### Risk Mitigation:
- Create comprehensive test coverage before changes
- Use deprecation warnings for any breaking changes
- Document migration path for users

## Verification

After implementation:
1. Run `scripts/validate_observability_examples.py`
2. Ensure API coverage report shows 100% for new methods
3. Run all examples with `test_all_examples_concurrent.py`
4. Check for any deprecation warnings
5. Verify event structures in integration tests

## Next Steps

After this adhoc phase:
1. Update documentation with new API features
2. Create migration guide for users
3. Consider performance optimizations
4. Plan for additional API extensions