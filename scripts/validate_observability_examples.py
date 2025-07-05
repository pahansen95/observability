#!/usr/bin/env python3
"""
Validate observability examples against API specifications.

This script analyzes all observability examples to ensure they correctly
use the API as defined in the Python stub files (.pyi).
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict


class StubParser:
    """Parse Python stub files to extract API definitions."""
    
    def __init__(self):
        self.classes: Dict[str, Dict] = {}
        self.functions: Dict[str, Dict] = {}
        
    def parse_file(self, filepath: Path) -> None:
        """Parse a single stub file."""
        content = filepath.read_text()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._parse_class(node)
            elif isinstance(node, ast.FunctionDef):
                self._parse_function(node, is_method=False)
                
    def _parse_class(self, node: ast.ClassDef) -> None:
        """Parse class definition."""
        class_info = {
            'methods': {},
            'properties': set(),
            'constructor': None
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == '__init__':
                    class_info['constructor'] = self._parse_function(item, is_method=True)
                else:
                    class_info['methods'][item.name] = self._parse_function(item, is_method=True)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Property definition
                class_info['properties'].add(item.target.id)
                
        self.classes[node.name] = class_info
        
    def _parse_function(self, node: ast.FunctionDef, is_method: bool) -> Dict:
        """Parse function/method definition."""
        params = []
        defaults = []
        
        # Extract parameters
        args = node.args
        start_idx = 1 if is_method else 0  # Skip 'self' for methods
        
        for i, arg in enumerate(args.args[start_idx:]):
            param_info = {
                'name': arg.arg,
                'has_default': False,
                'default_value': None
            }
            
            # Check if has default
            defaults_offset = len(args.args[start_idx:]) - len(args.defaults)
            if i >= defaults_offset:
                param_info['has_default'] = True
                
            params.append(param_info)
            
        return {
            'name': node.name,
            'params': params,
            'param_order': [p['name'] for p in params]
        }


class ExampleAnalyzer:
    """Analyze example files for API usage."""
    
    def __init__(self, stub_parser: StubParser):
        self.stub_parser = stub_parser
        self.divergences: List[Dict] = []
        self.api_usage: Dict[str, Set[str]] = defaultdict(set)
        
    def analyze_file(self, filepath: Path) -> None:
        """Analyze a single example file."""
        content = filepath.read_text()
        tree = ast.parse(content)
        
        self.current_file = filepath.name
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_call(node)
            elif isinstance(node, ast.Attribute):
                self._check_attribute(node)
                
    def _check_call(self, node: ast.Call) -> None:
        """Check method/function calls."""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            
            # Check for known method name issues
            if method_name == 'getChild':
                self.divergences.append({
                    'file': self.current_file,
                    'line': node.lineno,
                    'type': 'method_name',
                    'found': 'getChild',
                    'expected': 'get_child'
                })
            elif method_name == 'setLevel':
                self.divergences.append({
                    'file': self.current_file,
                    'line': node.lineno,
                    'type': 'method_name',
                    'found': 'setLevel',
                    'expected': 'min_level (property assignment)'
                })
                
            # Track API usage
            self.api_usage[method_name].add(self.current_file)
            
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Check filtered() parameter order
            if func_name == 'filtered' and len(node.args) >= 2:
                # Check if first arg is a handler (contains 'Handler')
                first_arg_str = ast.unparse(node.args[0])
                if 'Handler' in first_arg_str and 'lambda' not in first_arg_str:
                    self.divergences.append({
                        'file': self.current_file,
                        'line': node.lineno,
                        'type': 'parameter_order',
                        'found': 'filtered(handler, predicate)',
                        'expected': 'filtered(predicate, handler)'
                    })
                    
            self.api_usage[func_name].add(self.current_file)
            
    def _check_attribute(self, node: ast.Attribute) -> None:
        """Check attribute access."""
        attr_name = node.attr
        
        # Check for private attribute access
        if attr_name.startswith('_') and not attr_name.startswith('__'):
            self.divergences.append({
                'file': self.current_file,
                'line': node.lineno,
                'type': 'private_attribute',
                'found': attr_name,
                'expected': attr_name[1:]  # Remove underscore
            })


def generate_coverage_matrix(stub_parser: StubParser, analyzer: ExampleAnalyzer) -> str:
    """Generate API coverage matrix in Markdown format."""
    lines = ["# API Coverage Matrix\n"]
    lines.append("Generated from observability examples analysis.\n")
    
    # Collect all API methods from stubs
    all_methods = set()
    for class_name, class_info in stub_parser.classes.items():
        for method_name in class_info['methods']:
            all_methods.add(f"{class_name}.{method_name}")
            
    # Calculate coverage
    covered_methods = set()
    for method_name, files in analyzer.api_usage.items():
        if files:
            covered_methods.add(method_name)
            
    coverage_percent = (len(covered_methods) / len(all_methods) * 100) if all_methods else 0
    
    lines.append(f"## Summary\n")
    lines.append(f"- Total API methods: {len(all_methods)}\n")
    lines.append(f"- Covered methods: {len(covered_methods)}\n")
    lines.append(f"- Coverage: {coverage_percent:.1f}%\n")
    
    lines.append("\n## Coverage Details\n")
    lines.append("| Class.Method | Used In Examples | Coverage |\n")
    lines.append("|--------------|------------------|----------|\n")
    
    for class_name in sorted(stub_parser.classes.keys()):
        class_info = stub_parser.classes[class_name]
        for method_name in sorted(class_info['methods'].keys()):
            full_name = f"{class_name}.{method_name}"
            examples = analyzer.api_usage.get(method_name, set())
            coverage = "✓" if examples else "✗"
            examples_str = ", ".join(sorted(examples)[:3])
            if len(examples) > 3:
                examples_str += f" (+{len(examples)-3} more)"
            lines.append(f"| {full_name} | {examples_str} | {coverage} |\n")
            
    return "".join(lines)


def main():
    """Main validation logic."""
    print("Validating observability examples against API specifications...")
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    stub_dir = project_root / "src" / "observability"
    examples_dir = project_root / "examples" / "observability"
    output_dir = project_root / ".cache" / "tmp" / "observability-api-alignment"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse stub files
    print("\n1. Parsing stub files...")
    stub_parser = StubParser()
    
    stub_files = list(stub_dir.rglob("*.pyi"))
    for stub_file in stub_files:
        print(f"   - {stub_file.relative_to(project_root)}")
        stub_parser.parse_file(stub_file)
        
    print(f"   Found {len(stub_parser.classes)} classes")
    
    # Analyze examples
    print("\n2. Analyzing example files...")
    analyzer = ExampleAnalyzer(stub_parser)
    
    example_files = sorted(examples_dir.glob("*.py"))
    for example_file in example_files:
        if example_file.name.startswith(('0', '1', '2', '3', '4', '5', '6', '7')):
            analyzer.analyze_file(example_file)
            
    print(f"   Analyzed {len(example_files)} examples")
    print(f"   Found {len(analyzer.divergences)} divergences")
    
    # Write divergence report
    print("\n3. Writing divergence report...")
    report_path = output_dir / "divergence_report.json"
    with open(report_path, 'w') as f:
        json.dump(analyzer.divergences, f, indent=2)
    print(f"   Written to {report_path.relative_to(project_root)}")
    
    # Write coverage matrix
    print("\n4. Writing API coverage matrix...")
    matrix_path = output_dir / "api_coverage.md"
    matrix_content = generate_coverage_matrix(stub_parser, analyzer)
    matrix_path.write_text(matrix_content)
    print(f"   Written to {matrix_path.relative_to(project_root)}")
    
    # Summary statistics
    print("\n5. Summary Statistics:")
    print(f"   - Total divergences: {len(analyzer.divergences)}")
    
    divergence_types = defaultdict(int)
    affected_files = set()
    for div in analyzer.divergences:
        divergence_types[div['type']] += 1
        affected_files.add(div['file'])
        
    print("   - Divergences by type:")
    for div_type, count in sorted(divergence_types.items()):
        print(f"     * {div_type}: {count}")
        
    print(f"   - Affected files: {len(affected_files)}")
    
    # Print specific examples
    if analyzer.divergences:
        print("\n6. Example divergences:")
        for div in analyzer.divergences[:5]:
            print(f"   - {div['file']}:{div['line']} - {div['type']}: {div['found']} → {div['expected']}")
        if len(analyzer.divergences) > 5:
            print(f"   ... and {len(analyzer.divergences) - 5} more")
    
    print("\nValidation complete!")
    return 0 if not analyzer.divergences else 1


if __name__ == "__main__":
    exit(main())