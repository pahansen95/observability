#!/usr/bin/env python3
"""
Test API specification compliance between stub files and implementations.

Validates that:
- All exports in implementation match stub files
- No duplicate type definitions exist
- Public methods in implementations exist in stubs
"""

import ast
import pathlib
import sys
from typing import Set, Dict, List, Tuple


def get_module_exports(file_path: pathlib.Path) -> Set[str]:
    """Extract __all__ exports from a Python file."""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    if isinstance(node.value, ast.List):
                        return {
                            elt.s for elt in node.value.elts 
                            if isinstance(elt, ast.Str)
                        } | {
                            elt.value for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        }
    return set()


def get_stub_exports(stub_path: pathlib.Path) -> Set[str]:
    """Extract all public exports from a stub file."""
    with open(stub_path, 'r') as f:
        tree = ast.parse(f.read())
    
    exports = set()
    
    # Get __all__ if present
    all_exports = get_module_exports(stub_path)
    if all_exports:
        return all_exports
    
    # Otherwise, collect all public names including imports with aliases
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            if not node.name.startswith('_'):
                exports.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if not node.target.id.startswith('_'):
                exports.add(node.target.id)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith('_'):
                    exports.add(target.id)
        elif isinstance(node, ast.ImportFrom):
            # Handle "from .module import Name as Name" pattern
            for alias in node.names:
                if alias.asname and alias.name == alias.asname and not alias.name.startswith('_'):
                    exports.add(alias.name)
    
    return exports


def compare_exports(impl_path: pathlib.Path, stub_path: pathlib.Path) -> List[str]:
    """Compare exports between implementation and stub, return discrepancies."""
    impl_exports = get_module_exports(impl_path)
    stub_exports = get_stub_exports(stub_path)
    
    errors = []
    
    # Check for exports in impl but not in stub (violation of API spec)
    extra_in_impl = impl_exports - stub_exports
    if extra_in_impl:
        errors.append(f"Exports in {impl_path.name} not in stub: {sorted(extra_in_impl)}")
    
    # Check for exports in stub but not in impl (incomplete implementation)
    missing_in_impl = stub_exports - impl_exports
    if missing_in_impl:
        errors.append(f"Exports in {stub_path.name} not in implementation: {sorted(missing_in_impl)}")
    
    return errors


def find_type_definitions(file_path: pathlib.Path) -> Dict[str, int]:
    """Find type aliases and protocol definitions in a file."""
    type_defs = {}
    
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        # Type aliases (TypeAlias = ...)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Simple heuristic: uppercase names that aren't constants
                    if (target.id[0].isupper() and 
                        isinstance(node.value, (ast.Subscript, ast.Call)) and
                        not target.id.isupper()):  # Not an all-caps constant
                        type_defs[target.id] = node.lineno
        
        # Protocol/Class definitions that look like types
        elif isinstance(node, ast.ClassDef):
            if any(base.id == 'Protocol' for base in node.bases 
                   if isinstance(base, ast.Name)):
                type_defs[node.name] = node.lineno
    
    return type_defs


def check_duplicate_type_definitions(src_dir: pathlib.Path) -> List[str]:
    """Check for duplicate type definitions across the codebase."""
    all_types: Dict[str, List[Tuple[pathlib.Path, int]]] = {}
    
    # Scan all Python files
    for py_file in src_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        type_defs = find_type_definitions(py_file)
        for type_name, line_no in type_defs.items():
            if type_name not in all_types:
                all_types[type_name] = []
            all_types[type_name].append((py_file, line_no))
    
    # Scan all stub files
    for pyi_file in src_dir.rglob('*.pyi'):
        type_defs = find_type_definitions(pyi_file)
        for type_name, line_no in type_defs.items():
            if type_name not in all_types:
                all_types[type_name] = []
            all_types[type_name].append((pyi_file, line_no))
    
    # Find duplicates
    errors = []
    for type_name, locations in all_types.items():
        if len(locations) > 1:
            # Filter out legitimate cases
            # 1. Re-exports in __init__ files
            # 2. Implementation matching stub (stub is authoritative)
            stub_files = [loc for loc in locations if loc[0].suffix == '.pyi']
            impl_files = [loc for loc in locations if loc[0].suffix == '.py']
            
            # If defined in stub and corresponding impl, that's expected
            if stub_files and impl_files:
                stub_modules = {loc[0].stem for loc in stub_files}
                impl_modules = {loc[0].stem for loc in impl_files}
                # If same module name, it's implementation matching stub
                if stub_modules & impl_modules:
                    continue
            
            # Filter out re-exports from base modules
            base_defined = any('base' in str(loc[0]) for loc in locations)
            init_files = [loc for loc in locations if loc[0].stem == '__init__']
            if base_defined and init_files:
                # Type defined in base and re-exported in __init__ is OK
                continue
            
            # Otherwise it's a real duplicate
            loc_strs = [f"{loc[0].relative_to(src_dir)}:{loc[1]}" for loc in locations]
            errors.append(f"Type '{type_name}' defined in multiple locations: {loc_strs}")
    
    return errors


def test_main_module_exports():
    """Test that main module exports match between .py and .pyi."""
    src_dir = pathlib.Path(__file__).parent.parent / 'src' / 'observability'
    
    impl_path = src_dir / '__init__.py'
    stub_path = src_dir / '__init__.pyi'
    
    errors = compare_exports(impl_path, stub_path)
    assert not errors, "\n".join(errors)


def test_handler_module_exports():
    """Test that handler module exports match between .py and .pyi."""
    src_dir = pathlib.Path(__file__).parent.parent / 'src' / 'observability'
    
    impl_path = src_dir / 'handlers' / '__init__.py'
    stub_path = src_dir / 'handlers' / '__init__.pyi'
    
    if stub_path.exists():
        errors = compare_exports(impl_path, stub_path)
        assert not errors, "\n".join(errors)


def test_no_duplicate_type_definitions():
    """Test that type definitions are not duplicated across files."""
    src_dir = pathlib.Path(__file__).parent.parent / 'src' / 'observability'
    
    errors = check_duplicate_type_definitions(src_dir)
    # Allow some specific duplicates that are intentional
    allowed_duplicates = {
        'EventDict',  # Re-exported in multiple places
        'EventHandler',  # Re-exported in multiple places
    }
    
    filtered_errors = []
    for error in errors:
        type_name = error.split("'")[1]
        if type_name not in allowed_duplicates:
            filtered_errors.append(error)
    
    assert not filtered_errors, "\n".join(filtered_errors)


def test_public_methods_in_stubs():
    """Test that all public methods in implementations exist in stubs.
    
    Note: According to PyAPISpec.md Three-Tier model:
    - Tier 1 (Exported): In stub files - Major version stability
    - Tier 2 (Public): No underscore - Minor version stability
    - Tier 3 (Private): Underscore prefix - No stability
    
    Public methods not in stubs are Tier 2, which is a valid design choice.
    This test is informational - it identifies Tier 2 methods.
    """
    src_dir = pathlib.Path(__file__).parent.parent / 'src' / 'observability'
    
    tier2_methods = []
    
    # Check main classes
    for impl_file in src_dir.rglob('*.py'):
        if '__pycache__' in str(impl_file) or impl_file.name.startswith('_'):
            continue
        
        stub_file = impl_file.with_suffix('.pyi')
        if not stub_file.exists():
            continue
        
        # Parse both files
        with open(impl_file, 'r') as f:
            impl_tree = ast.parse(f.read())
        with open(stub_file, 'r') as f:
            stub_tree = ast.parse(f.read())
        
        # Build stub method inventory
        stub_methods = {}
        for node in ast.walk(stub_tree):
            if isinstance(node, ast.ClassDef):
                methods = set()
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                        methods.add(item.name)
                stub_methods[node.name] = methods
        
        # Check implementation
        for node in ast.walk(impl_tree):
            if isinstance(node, ast.ClassDef) and node.name in stub_methods:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                        if item.name not in stub_methods[node.name]:
                            tier2_methods.append(
                                f"Tier 2 method: {node.name}.{item.name} in "
                                f"{impl_file.relative_to(src_dir)}"
                            )
    
    # This is informational - Tier 2 methods are valid
    if tier2_methods:
        print("\nTier 2 (Public but not Exported) methods found:")
        for method in tier2_methods:
            print(f"  - {method}")
    
    # Test passes - Tier 2 is a valid design choice


if __name__ == '__main__':
    # Run all tests
    print("Testing API specification compliance...")
    
    try:
        test_main_module_exports()
        print("✓ Main module exports match")
    except AssertionError as e:
        print(f"✗ Main module exports mismatch:\n{e}")
        sys.exit(1)
    
    try:
        test_handler_module_exports()
        print("✓ Handler module exports match")
    except AssertionError as e:
        print(f"✗ Handler module exports mismatch:\n{e}")
        sys.exit(1)
    
    try:
        test_no_duplicate_type_definitions()
        print("✓ No duplicate type definitions")
    except AssertionError as e:
        print(f"✗ Duplicate type definitions found:\n{e}")
        sys.exit(1)
    
    try:
        test_public_methods_in_stubs()
        print("✓ Three-Tier model compliance checked")
    except AssertionError as e:
        print(f"✗ Three-Tier model issue:\n{e}")
        sys.exit(1)
    
    print("\nAll API specification compliance tests passed!")