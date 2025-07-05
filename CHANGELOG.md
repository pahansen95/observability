# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-07-05

### Added
- Comprehensive API test coverage - improved from 85-90% to 89.91% overall coverage
- 103 new test cases covering all exported API elements
- Test coverage for edge cases, error handling, and thread safety
- Performance benchmarks for zero-overhead guarantee validation
- Comprehensive examples demonstrating all framework capabilities
- `__version__` attribute for runtime version inspection

### Changed
- Simplified observability API implementation for better usability
- Improved handler lifecycle management with unified registration tracking
- Converted composite handlers to synchronous lifecycle management
- Enhanced API specification compliance for consistency

### Fixed
- Fixed ManagedFileHandler deadlock issue by using reentrant locks
- Resolved handler registration tracking for proper lifecycle management
- Fixed various API specification compliance issues

### Technical Details
- Added tests for handler protocols and type aliases
- Enhanced domain integration tests (logging, metrics, tracing)
- Added custom domain implementation tests
- Improved thread safety in resource handlers
- Added extensive handler edge case testing

## [0.1.0] - Initial Release

### Added
- Core observability framework with context-based architecture
- Zero-overhead guarantee when no handlers attached
- Logging, metrics, and tracing domains
- Multiple handler implementations (Print, JSON, File, Buffer, Queued)
- Handler composition patterns (filtered, sampled, fanout, fallback)
- Context variables for distributed tracing (trace_id, request_id, operation_id)
- Shared context singleton for convenience
- Thread-safe handler lifecycle management

[0.2.0]: https://github.com/pahansen95/observability/compare/v0.1.0...v0.2.0