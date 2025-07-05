# Observability Examples Maintainer Notes

This document provides guidance for maintaining the observability examples and ensuring ongoing API compliance.

## Validation Process

The examples are validated against the API specifications defined in the Python stub files (`.pyi`). A validation script checks for:

1. **Method naming** - Ensures methods match stub definitions
2. **Parameter ordering** - Verifies correct parameter positions
3. **Property access** - Checks for proper public API usage
4. **API coverage** - Tracks which APIs are demonstrated

### Running Validation

```bash
# Run from project root
python scripts/validate_observability_examples.py

# Check specific example
python scripts/validate_observability_examples.py --file examples/observability/10_logging_basics.py
```

### Understanding Output

The script generates:
- `.cache/tmp/observability-api-alignment/divergence_report.json` - List of all divergences
- `.cache/tmp/observability-api-alignment/api_coverage.md` - API usage matrix

## Common Validation Issues

### Private Attribute Access

Examples may use private attributes (prefixed with `_`) for demonstration purposes. These are flagged but may be acceptable if:
- They demonstrate internal behavior
- They're used in advanced/debugging examples
- They're clearly marked as internal

### Implementation vs Specification

Some divergences exist between implementation and specification:
- `TimeDeltaHandler` adds `delta_ns` (implementation) vs `time_delta_ns` (spec)
- Some methods may not be implemented yet

Document these in the example with comments.

## Adding New Examples

When adding examples:

1. **Check API coverage** first:
   ```bash
   python scripts/validate_observability_examples.py
   grep "✗" .cache/tmp/observability-api-alignment/api_coverage.md
   ```

2. **Follow naming convention**: `NN_category_description.py`
   - 01-09: Basic setup
   - 10-39: Domain examples  
   - 40-59: Handler examples
   - 60-72: Advanced patterns
   - 73+: Extended coverage

3. **Include proper structure**:
   ```python
   #!/usr/bin/env python3
   """
   Example NN: Title
   
   Demonstrates:
   - Feature 1
   - Feature 2
   """
   ```

4. **Test the example**:
   ```bash
   cd examples/observability
   python NN_example_name.py
   ```

5. **Update README**:
   - Add to the example index table
   - Update API coverage section if needed

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/validate-observability.yml`) runs on:
- Push to main/master
- Pull requests
- Changes to examples or API files

The workflow will fail if any divergences are found.

## Handling API Changes

When the API changes:

1. **Update stub files** first (`.pyi` files)
2. **Run validation** to identify affected examples
3. **Update examples** to match new API
4. **Update migration guide** with the changes
5. **Tag old examples** if maintaining compatibility

## Performance Considerations

- Examples should complete in < 1 second (except performance demos)
- Use small data sets and short delays
- Test with `time python example.py`

## Debugging Validation Failures

1. **Check the specific divergence**:
   ```bash
   cat .cache/tmp/observability-api-alignment/divergence_report.json | jq '.[] | select(.file=="failing_example.py")'
   ```

2. **Compare with stub**:
   ```bash
   grep "method_name" src/observability/**/*.pyi
   ```

3. **Test the fix**:
   ```python
   # In the example
   print(f"DEBUG: {method.__name__}")  # Check actual method name
   print(f"DEBUG: {inspect.signature(method)}")  # Check signature
   ```

## Review Checklist

For PR reviews:

- [ ] Validation script passes
- [ ] Examples execute without errors
- [ ] API usage matches stubs
- [ ] README is updated
- [ ] No unnecessary dependencies
- [ ] Clear demonstration of concepts
- [ ] Appropriate for example category
- [ ] Performance is acceptable

## Known Issues

1. **Private attributes in advanced examples** - Some examples legitimately use private attributes for demonstration. These can be ignored if documented.

2. **Async examples** - May have longer execution times due to event loops.

3. **Platform differences** - File paths may need adjustment on Windows.

## Future Improvements

- Add example categories to validation
- Create example templates
- Add performance benchmarks to CI
- Generate coverage reports automatically
- Add interactive example runner