#!/usr/bin/env python3
"""
Analyze the codebase to find unused files and functions.
"""

import os
import ast
import re
from pathlib import Path
from collections import defaultdict

def extract_imports_and_definitions(file_path):
    """Extract imports, function definitions, and class definitions from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        imports = []
        function_defs = []
        class_defs = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")
            elif isinstance(node, ast.FunctionDef):
                function_defs.append(node.name)
            elif isinstance(node, ast.ClassDef):
                class_defs.append(node.name)
        
        return imports, function_defs, class_defs
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return [], [], []

def find_usage_in_files(search_term, files_to_search):
    """Find usage of a term in files."""
    usage_files = []
    for file_path in files_to_search:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if search_term in content:
                    # Count occurrences
                    count = content.count(search_term)
                    usage_files.append((file_path, count))
        except Exception:
            continue
    return usage_files

def analyze_codebase(src_dir):
    """Analyze the entire codebase."""
    src_path = Path(src_dir)
    python_files = list(src_path.rglob("*.py"))
    
    # Storage for analysis
    all_imports = defaultdict(list)
    all_functions = defaultdict(list)
    all_classes = defaultdict(list)
    file_imports = {}
    
    print(f"Found {len(python_files)} Python files")
    print("\n" + "="*80)
    print("ANALYZING IMPORTS, FUNCTIONS, AND CLASSES")
    print("="*80)
    
    # Extract definitions from each file
    for file_path in python_files:
        rel_path = file_path.relative_to(src_path)
        imports, functions, classes = extract_imports_and_definitions(file_path)
        
        file_imports[str(rel_path)] = imports
        
        for func in functions:
            all_functions[func].append(str(rel_path))
        
        for cls in classes:
            all_classes[cls].append(str(rel_path))
        
        for imp in imports:
            all_imports[imp].append(str(rel_path))
    
    # Analyze usage
    print("\n" + "="*80)
    print("FUNCTION USAGE ANALYSIS")
    print("="*80)
    
    unused_functions = []
    for func_name, defined_in in all_functions.items():
        if func_name.startswith('_'):  # Skip private functions
            continue
        
        usage = find_usage_in_files(func_name, python_files)
        # Filter out the definition files
        usage_files = [u for u in usage if Path(u[0]) not in [src_path / f for f in defined_in]]
        
        if not usage_files:
            unused_functions.append((func_name, defined_in))
        
        print(f"Function '{func_name}':")
        print(f"  Defined in: {', '.join(defined_in)}")
        if usage_files:
            usage_file_names = []
            for u, c in usage_files:
                try:
                    usage_file_names.append(str(Path(u).relative_to(src_path)))
                except:
                    usage_file_names.append(str(u))
            print(f"  Used in: {', '.join(usage_file_names)}")
        else:
            print(f"  Used in: NOT USED")
        print()
    
    print("\n" + "="*80)
    print("CLASS USAGE ANALYSIS")
    print("="*80)
    
    unused_classes = []
    for class_name, defined_in in all_classes.items():
        usage = find_usage_in_files(class_name, python_files)
        # Filter out the definition files
        usage_files = [u for u in usage if Path(u[0]) not in [src_path / f for f in defined_in]]
        
        if not usage_files:
            unused_classes.append((class_name, defined_in))
        
        print(f"Class '{class_name}':")
        print(f"  Defined in: {', '.join(defined_in)}")
        if usage_files:
            usage_file_names = []
            for u, c in usage_files:
                try:
                    usage_file_names.append(str(Path(u).relative_to(src_path)))
                except:
                    usage_file_names.append(str(u))
            print(f"  Used in: {', '.join(usage_file_names)}")
        else:
            print(f"  Used in: NOT USED")
        print()
    
    print("\n" + "="*80)
    print("FILE IMPORT ANALYSIS")
    print("="*80)
    
    # Check which files are never imported
    never_imported = []
    for file_path in python_files:
        rel_path = file_path.relative_to(src_path)
        file_stem = str(rel_path).replace('/', '.').replace('.py', '')
        
        # Check if this file is imported anywhere
        imported = False
        for imports_list in file_imports.values():
            for imp in imports_list:
                if file_stem in imp or str(rel_path.stem) in imp:
                    imported = True
                    break
            if imported:
                break
        
        if not imported and str(rel_path) != '__init__.py':
            never_imported.append(str(rel_path))
    
    print("Files that are never imported:")
    for file_path in never_imported:
        print(f"  {file_path}")
    
    print("\n" + "="*80)
    print("SUMMARY OF UNUSED CODE")
    print("="*80)
    
    print("UNUSED FUNCTIONS:")
    for func_name, defined_in in unused_functions:
        print(f"  {func_name} (in {', '.join(defined_in)})")
    
    print("\nUNUSED CLASSES:")
    for class_name, defined_in in unused_classes:
        print(f"  {class_name} (in {', '.join(defined_in)})")
    
    print("\nNEVER IMPORTED FILES:")
    for file_path in never_imported:
        print(f"  {file_path}")
    
    return {
        'unused_functions': unused_functions,
        'unused_classes': unused_classes,
        'never_imported': never_imported,
        'all_functions': dict(all_functions),
        'all_classes': dict(all_classes),
        'file_imports': file_imports
    }

if __name__ == "__main__":
    src_directory = "/home/coder/Desktop/2202/Viralinstabot/src"
    result = analyze_codebase(src_directory)