# Python API Specification Standard

## Executive Summary

### The Prescription Principle

API Specifications prescribe how users SHOULD interact with libraries, not describe what they CAN access. This fundamental principle drives all design decisions in this standard.

### Three-Tier Stability Model

```
├── Tier 1: EXPORTED (in .pyi)  → Major version stability
├── Tier 2: PUBLIC (no _)       → Minor version stability  
└── Tier 3: PRIVATE (_name)     → No stability guarantees
```

### Stability Commitment Ladder

| Access Level | Stability Guarantee | User Impact |
|-------------|-------------------|-------------|
| Exported | Major version | Safe for production |
| Public | Minor version | Use with caution |
| Private | None | Use at own risk |

## 1. Concepts and Mental Model

### 1.1 Purpose

This standard defines requirements for Python API Specifications - prescriptive contracts between library maintainers and users. API Specifications establish supported interfaces, guide correct usage, and provide stability guarantees.

### 1.2 The Prescription Principle

API Specifications serve three interconnected purposes:

1. **Contractual Boundary**: Defines stable interfaces with explicit versioning guarantees
2. **Prescriptive Guide**: Directs users toward successful integration patterns  
3. **Self-Contained Reference**: Provides complete understanding without external resources

The specification prescribes intended usage patterns rather than documenting all technical possibilities.

### 1.3 Three-Tier Access Model

Python's open nature means all code is technically accessible. API Specifications establish three access tiers:

**Tier 1: Exported API** (Documented in `.pyi` files)
- Explicit design decision to support
- Major version stability guarantee
- Full documentation and examples
- Primary user interface

**Tier 2: Public Implementation** (No underscore prefix)
- Available but not guaranteed
- May change in minor versions
- Limited or no documentation
- Power user territory

**Tier 3: Private Implementation** (Underscore prefix)
- Internal use only
- Changes without notice
- No documentation
- Use violates design intent

### 1.4 Design Philosophy

**Explicit over Discovered**: Exported names are deliberately chosen, not automatically derived from implementation availability.

**Prescriptive over Descriptive**: Specifications guide users toward correct patterns rather than cataloging all possibilities.

**Progressive Disclosure**: APIs reveal complexity in layers, guiding users from simple to advanced usage.

**Examples as Contract**: Usage examples demonstrate guaranteed behaviors, not just suggestions.

### 1.5 Key Terminology

- **API Specification**: A `.pyi` stub file documenting exported names
- **Export**: To include in a specification, granting major version stability
- **Exported Name**: A public name included in an API specification
- **Public Name**: An identifier without underscore prefix
- **Private Name**: An identifier with underscore prefix
- **Import Point**: A module path users should import from
- **Internal Module**: Implementation module not intended for direct import

### 1.6 Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" are interpreted as described in RFC 2119.

## 2. Quick Start Guide

### 2.1 Minimal Example

```python
# library/__init__.py - Implementation
from .engine import Engine
from .utils import helper  # Available but not exported

# library/__init__.pyi - API Specification
"""Data processing library."""

class Engine:
    """Primary processing engine."""
    def __init__(self, config: dict[str, Any]) -> None: ...
    def process(self, data: bytes) -> str: ...

# Note: helper deliberately not exported - design decision
```

### 2.2 Export Decision Flowchart

```
Should this name be exported?
├─ Does it require implementation knowledge? → NO EXPORT
├─ Will it remain stable across major versions? → CONSIDER
├─ Does it provide clear user value? → CONSIDER
└─ All conditions met? → EXPORT
```

### 2.3 Documentation Depth Matrix

| Component Type | Documentation Required | Typical Length |
|---------------|----------------------|----------------|
| Type Alias | Purpose statement | 1 line |
| Simple Method | Purpose + parameters | 3-5 lines |
| Core Class | Full behavioral spec | 15-30 lines |
| Protocol | Contract definition | 10-20 lines |
| Complex Function | Complete guide | 20-40 lines |

## 3. Specification Engineering

### 3.1 File Organization

#### 3.1.1 Stub File Placement

API specifications use `.pyi` stub files placed according to import patterns:

```python
# If users import: from library import Thing
# Then create: library/__init__.pyi defining Thing

# If users import: from library.module import Other
# Then create: library/module.pyi defining Other
```

**Key Principle**: The presence of a stub file endorses that import path. Absence signals "not part of designed interface."

#### 3.1.2 Three-Tier Model in Practice

```python
library/
├── __init__.py       # from .engine import Engine
├── __init__.pyi      # class Engine: ... (EXPORTED - Tier 1)
├── engine.py         # PUBLIC module (Tier 2)
├── utils.py          # PUBLIC but no stub (Tier 2)
└── _internal.py      # PRIVATE module (Tier 3)
```

This structure communicates:
- `Engine` via `library` import: Stable, supported
- `engine.py` module: Available but less stable
- `utils.py` functions: Use with caution
- `_internal.py`: Hands off

### 3.2 Specification Structure Template

API specifications SHOULD follow this five-section template:

```python
# ruff: noqa: F811
"""
1. API SPECIFICATION OVERVIEW
Single-line summary.

Extended description of functionality, guarantees, and use cases.

## Quick Start
    from library import MainClass
    result = MainClass().process(data)

## Mental Model
Conceptual framework for understanding the API.
"""

# 2. IMPORTS
from __future__ import annotations  # ALWAYS first
from typing import Protocol, TypeAlias
import external_dependency

# =============================================================================
# API Type Aliases, Protocols, Enums
# =============================================================================

# 3. TYPE DEFINITIONS
ConfigDict: TypeAlias = dict[str, Any]
"""Configuration parameters."""

class ProcessMode(Enum):
    """Processing strategies."""
    FAST = "fast"
    ACCURATE = "accurate"

# =============================================================================
# API Core Types & Functionality
# =============================================================================

# 4. CORE API
class MainClass:
    """Primary user interface."""
    def __init__(self, config: ConfigDict) -> None: ...
    def process(self, data: bytes) -> Result: ...

# =============================================================================
# API Supporting Types & Functionality
# =============================================================================

# 5. SUPPORTING API
def create_default_config() -> ConfigDict:
    """Generate standard configuration."""
    ...
```

### 3.3 Documentation Standards

#### 3.3.1 Depth by Component Type

Documentation depth matches component complexity and user needs:

**Minimal Documentation** (Properties, simple methods):
```python
@property
def name(self) -> str:
    """Entity name (read-only)."""
```

**Standard Documentation** (Core functions):
```python
def process(data: bytes, *, validate: bool = True) -> str:
    """
    Convert raw bytes to normalized string.
    
    Args:
        data: UTF-8 encoded bytes
        validate: Whether to check encoding
        
    Returns:
        Normalized string, whitespace trimmed
        
    Example:
        >>> process(b'  hello  ')
        'hello'
    """
```

**Comprehensive Documentation** (Complex patterns):
```python
class DataProcessor:
    """
    High-performance data transformation engine.
    
    Processes data through configurable pipeline stages with
    automatic parallelization and error recovery. Thread-safe
    after initialization.
    
    The processor maintains internal state for optimization
    but presents a stateless interface to users.
    
    Args:
        config: Configuration with keys:
            - 'mode': ProcessMode selection
            - 'threads': Worker count (1-32)
            - 'timeout': Max seconds per operation
        
    Example:
        >>> processor = DataProcessor({'mode': ProcessMode.FAST})
        >>> results = processor.batch_process(items)
        
    Note:
        Instances are thread-safe but not process-safe.
        Use multiprocessing.Queue for IPC.
    """
```

#### 3.3.2 Examples as Specification

Examples define guaranteed behaviors:

```python
def batch_process(items: list[T]) -> list[Result[T]]:
    """
    Process items preserving order.
    
    Example:
        >>> # Order preservation is GUARANTEED
        >>> results = batch_process([a, b, c])
        >>> assert results[0].source == a
        >>> assert results[1].source == b
        >>> assert results[2].source == c
    """
```

The example establishes order preservation as a contractual guarantee, not mere implementation detail.

### 3.4 Export Design

#### 3.4.1 The Fundamental Constraint

API specifications MUST only export names that exist in the implementation. Stubs document the designed subset of existing functionality.

```python
# implementation.py
class Engine: ...
EngineConfig = dict[str, Any]

# implementation.pyi
class Engine: ...  # ✓ Exists in implementation
EngineConfig: TypeAlias = dict[str, Any]  # ✓ Documents existing alias

# WRONG: Creating new names
EngineOptions: TypeAlias = dict[str, Any]  # ✗ Not in implementation
```

#### 3.4.2 Three-Tier Model as Decision Framework

Export decisions create different stability commitments:

```python
# Tier 1: Export with major version guarantee
class DataProcessor:  # In .pyi file
    """Core functionality users depend on."""
    
# Tier 2: Public but not exported  
def optimize_internals():  # In .py only
    """Useful but may change."""
    
# Tier 3: Private implementation
def _parse_config():  # In .py only
    """Implementation detail."""
```

**Evolution Pattern**: Features migrate upward through tiers as they stabilize:
```
_experimental_feature → feature → exported feature
```

#### 3.4.3 Progressive Disclosure

APIs guide users through complexity layers:

```python
"""
## Basic Usage (Start here)
    from library import process
    result = process(data)

## Advanced Usage (When needed)
    from library import Process
    proc = Process(custom_config)
    result = proc.run(data)

## Extension (Power users)
    from library.core import BaseProcessor  # No stub
    class Custom(BaseProcessor): ...
"""
```

#### 3.4.4 Export Categories

**Primary Exports** (Always include):
- Core functionality users directly interact with
- Configuration and initialization patterns
- Context managers for resource handling
- Type definitions clarifying contracts

**Secondary Exports** (Include when valuable):
- Convenience functions and helpers
- Alternative constructors
- Specialized error types
- Advanced configuration options

**Non-Exports** (Exclude even if public):
- Implementation base classes
- Internal helpers (even without underscore)
- Debugging utilities
- Complex overloads

## 4. Technical Requirements

### 4.1 Type Annotations

#### 4.1.1 Completeness

All exported names MUST have complete type annotations:

```python
# Complete annotations required
def process(data: bytes, *, timeout: float = 30.0) -> Result: ...

# Type variables for generics
T = TypeVar('T')
ConfigT = TypeVar('ConfigT', bound=BaseConfig)
```

#### 4.1.2 Type Aliases as Documentation

Type aliases clarify complex types without runtime overhead:

```python
# Cognitive simplification
JsonDict: TypeAlias = dict[str, Union[str, int, float, bool, None]]
"""JSON-serializable dictionary."""

# Domain expression
Port: TypeAlias = int
"""Network port (0-65535)."""
```

### 4.2 Import Requirements

All specifications begin with:

```python
from __future__ import annotations  # REQUIRED first line

# Standard library types
from typing import Protocol, TypeAlias, Any
from collections.abc import Sequence, Mapping

# External dependencies
import numpy as np

# Own package (absolute imports only)
from mypackage.types import SharedType  # Never: from .types
```

### 4.3 Validation Requirements

Specifications MUST:
- Pass `mypy --strict` without errors
- Include all exported names from implementation
- Provide documentation for every export
- Demonstrate key usage patterns

Design quality metrics:
- Export surface minimized
- Each export has single clear purpose
- Progressive complexity layers maintained
- Static analysis fully supported

### 4.4 Formatting Standards

#### Section Ordering

Within each section, order by dependency and complexity:

**Type Definitions Section**:
1. Simple type aliases
2. Enums
3. Complex type aliases (using other types)
4. Protocols (simplest to most complex)

**Core API Section**:
1. Primary classes/functions users interact with most
2. Essential data structures
3. Main processing functions
4. Configuration classes

**Supporting API Section**:
1. Factory functions for core types
2. Utility functions
3. Helper classes
4. Advanced/specialized functionality

### 4.5 Tooling Integration

Libraries SHOULD:
- Include `py.typed` marker for type checking
- Validate import paths match stub locations
- Test that public imports work as documented

**Testing Specifications**:
```python
# Test that exports match implementation
def test_exports_exist():
    from library import Process  # From stub
    assert hasattr(library, 'Process')  # In implementation

# Test behavioral contracts
def test_order_preservation():
    # Based on example in API spec
    results = batch_process([a, b, c])
    assert results[0].input == a  # Guaranteed by spec
```

## 5. API Evolution

### 5.1 Progressive Exposure Strategy

Start minimal, expand based on demonstrated need:

1. **Initial Release**: Export core functionality only
2. **User Feedback**: Identify missing conveniences
3. **Incremental Growth**: Add exports based on actual usage
4. **Avoid Speculation**: Don't export "might be useful" features

### 5.2 Stability Migration

Moving between tiers:

**Private → Public**: Remove underscore, document behavior
```python
# v1.0: _helper() is private
# v1.1: helper() becomes public (no stub yet)
```

**Public → Exported**: Add to stub with full documentation
```python
# v2.0: helper() added to stub (major version for new export)
```

**Exported → Deprecated**: Mark in stub, provide migration
```python
# v3.0: @deprecated("Use new_helper")
# v4.0: Removed from stub
# v5.0: Made private or removed entirely
```

### 5.3 Breaking Change Management

Handle breaking changes through clear communication:

```python
# v2.x - Add deprecation
@deprecated("Parameter 'old' renamed to 'new' in v3.0")
def function(old: str = None, new: str = None) -> None:
    """..."""

# v3.0 - Remove deprecated parameter
def function(new: str) -> None:
    """..."""
```

## 6. Patterns and Examples

### 6.1 Special Cases

#### 6.1.1 Properties

```python
@property
def timeout(self) -> float:
    """Request timeout in seconds (0.1-300.0)."""
    ...

@timeout.setter
def timeout(self, value: float) -> None: ...
```

#### 6.1.2 Context Managers

```python
def __enter__(self) -> Self:
    """Acquire resources and return self."""
    ...

def __exit__(self, *args: Any) -> None:
    """Release resources, never suppresses exceptions."""
    ...
```

#### 6.1.3 Alternative Constructors

```python
@classmethod
def from_json(cls, data: str) -> Self:
    """
    Construct from JSON string.
    
    Args:
        data: Valid JSON matching schema
        
    Raises:
        JSONDecodeError: Malformed JSON
        ValidationError: Schema violation
    """
    ...
```

#### 6.1.4 Operator Overloading

Export operators only for types where they're naturally expected:

```python
# Good: Mathematical type
class Vector:
    def __add__(self, other: Vector) -> Vector:
        """Vector addition."""
        ...

# Avoid: Domain type without natural operators
class User:
    # Don't export __add__ for arbitrary types
    ...
```

### 6.2 Complete Example

Demonstrating all concepts in practice:

```python
# library/processor.py - Full implementation
"""Data processing implementation."""

from typing import Protocol
import json

class Validator(Protocol):
    """Validation protocol."""
    def validate(self, data: str) -> bool: ...

class Processor:
    """Main processing class."""
    
    def __init__(self, validator: Validator) -> None:
        self._validator = validator
    
    def process(self, data: bytes) -> str:
        """Process data with validation."""
        result = self._parse(data)
        if not self._validator.validate(result):
            raise ValueError("Validation failed")
        return result
    
    def _parse(self, data: bytes) -> str:
        """Internal parsing logic."""
        return data.decode('utf-8').strip()

def create_processor() -> Processor:
    """Factory with default validator."""
    from ._validators import DefaultValidator
    return Processor(DefaultValidator())

# library/__init__.pyi - API Specification
"""
Data processing library with validation.

## Quick Start
    from library import process
    result = process(b'raw data')
"""

from __future__ import annotations
from typing import Protocol

class Validator(Protocol):
    """Contract for data validators."""
    def validate(self, data: str) -> bool: ...

class Processor:
    """
    Data processor with pluggable validation.
    
    Args:
        validator: Validation implementation
        
    Example:
        >>> proc = Processor(CustomValidator())
        >>> proc.process(b'data')
    """
    def __init__(self, validator: Validator) -> None: ...
    
    def process(self, data: bytes) -> str:
        """
        Process bytes to validated string.
        
        Raises:
            ValueError: Validation failure
        """
        ...

def process(data: bytes) -> str:
    """
    Simple processing with default validation.
    
    Example:
        >>> process(b'  hello  ')
        'hello'
    """
    ...
```

### 6.3 Anti-patterns

**Avoid Creating stubs for non-exported public modules**:
```python
# WRONG: Not an intended import point
library/
├── __init__.pyi      # def process(): ...
├── data.py           # Public module
└── data.pyi          # WRONG: Stub without design intent
```

**Avoid Documenting public but non-exported names**:
```python
# library/__init__.pyi
def process(): ...    # Exported
def validate(): ...   # WRONG: Public but not in __init__.py
```

**Avoid Exposing internal structure**:
```python
# __init__.pyi  
from ._internal import InternalClass  # Never expose private modules
```

**Avoid Creating stubs without clear import intent**:
```python
library/
└── utils/
    ├── helpers.py    # Public module
    └── helpers.pyi   # Only if users should import from library.utils.helpers
```

### 6.4 Export Curation Example

Implementation contains many names, but exports are curated:

```python
# processor.py - Implementation
class Processor: ...                  # Core class
class ProcessorConfig: ...           # Configuration  
class ProcessorError(Exception): ... # Public error
def create_processor(): ...          # Factory
def validate_config(): ...           # Helper
def _internal_helper(): ...          # Private
class ProcessorBase: ...             # Implementation base
def debug_processor(): ...           # Debug utility

# __init__.pyi - Curated exports
class Processor: ...                 # EXPORTED - Primary interface
def create_processor() -> Processor: ... # EXPORTED - Construction
class ProcessorError(Exception): ... # EXPORTED - User-facing error

# Deliberately excluded:
# - ProcessorConfig: Use dict instead
# - validate_config: Internal validation  
# - ProcessorBase: Implementation detail
# - debug_processor: Not for production use
```

## 7. Reference

### 7.1 Conformance Checklist

- [ ] All exported names exist in implementation
- [ ] Complete type annotations on all exports
- [ ] Documentation for every exported name
- [ ] Examples demonstrate key patterns
- [ ] Passes `mypy --strict`
- [ ] Progressive disclosure structure
- [ ] Three-tier model applied consistently
- [ ] `py.typed` marker included
- [ ] Section formatting follows standard

### 7.2 Quick Reference

| Concept | Implementation |
|---------|---------------|
| Export name | Include in `.pyi` file |
| Hide name | Omit from `.pyi` file |
| Private name | Prefix with underscore |
| Type alias | `TypeAlias` annotation |
| Protocol | `Protocol` base class |
| Stability | Major version guarantee |
| Section separator | `# ===...===` |
| Import order | future → typing → stdlib → external → package |

### 7.3 Glossary

**Export**: Include name in API specification, granting major version stability

**Internal Module**: Implementation module not intended for direct import

**Prescriptive**: Defining intended usage rather than available functionality

**Progressive Disclosure**: Revealing complexity in guided layers

**Stub File**: `.pyi` file containing API specifications

**Three-Tier Model**: Private/Public/Exported access levels with different guarantees

### 7.4 References

- PEP 484 - Type Hints
- PEP 561 - Distributing Type Information  
- PEP 3119 - Protocol Classes
- RFC 2119 - Requirement Levels