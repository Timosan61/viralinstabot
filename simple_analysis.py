#!/usr/bin/env python3
"""
Simple analysis of unused code in the codebase.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def analyze_simple():
    """Simple analysis focusing on key patterns."""
    src_dir = Path("/home/coder/Desktop/2202/Viralinstabot/src")
    python_files = list(src_dir.rglob("*.py"))
    
    print(f"Found {len(python_files)} Python files")
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    
    # 1. Check which files are imported in main.py
    main_py = src_dir / "bot" / "main.py"
    with open(main_py, 'r') as f:
        main_content = f.read()
    
    print("1. FILES IMPORTED IN MAIN.PY:")
    imported_in_main = []
    for line in main_content.split('\n'):
        if line.strip().startswith('from src.') or line.strip().startswith('import src.'):
            print(f"   {line.strip()}")
            # Extract module names
            if 'from src.' in line:
                module = line.split('from src.')[1].split(' import')[0].strip()
                imported_in_main.append(module)
    
    # 2. Check handlers_vision.py import issues
    handlers_vision = src_dir / "bot" / "handlers_vision.py"
    print("\n2. HANDLERS_VISION.PY IMPORT ISSUES:")
    with open(handlers_vision, 'r') as f:
        vision_content = f.read()
    
    # Look for undefined imports
    if "VisionAnalyzer" in vision_content and "from" not in vision_content[:500]:
        print("   VisionAnalyzer used but not imported properly")
    if "ScenarioGenerator" in vision_content and "from" not in vision_content[:500]:
        print("   ScenarioGenerator used but not imported properly")
    
    # 3. Check for commented out imports in main.py
    print("\n3. COMMENTED OUT IMPORTS IN MAIN.PY:")
    for line in main_content.split('\n'):
        if line.strip().startswith('#') and ('import' in line or 'from' in line):
            print(f"   {line.strip()}")
    
    # 4. Look for duplicate functionality
    print("\n4. POTENTIAL DUPLICATES:")
    
    # Two scenario generators
    scenario_gen1 = src_dir / "features" / "ai_scenarios" / "scenario_generator.py"
    scenario_gen2 = src_dir / "features" / "vision_analysis" / "scenario_generator.py"
    if scenario_gen1.exists() and scenario_gen2.exists():
        print("   Two ScenarioGenerator classes found:")
        print(f"     - {scenario_gen1.relative_to(src_dir)}")
        print(f"     - {scenario_gen2.relative_to(src_dir)}")
    
    # 5. Files that exist but are never imported
    print("\n5. FILES THAT MIGHT BE UNUSED:")
    
    all_content = ""
    for py_file in python_files:
        with open(py_file, 'r') as f:
            all_content += f.read() + "\n"
    
    potentially_unused = []
    for py_file in python_files:
        rel_path = py_file.relative_to(src_dir)
        if str(rel_path) == "__init__.py":
            continue
        
        # Check if file name appears in imports
        file_stem = rel_path.stem
        module_path = str(rel_path).replace('/', '.').replace('.py', '')
        
        # Simple check for import patterns
        import_patterns = [
            f"from {module_path}",
            f"import {module_path}",
            f"from src.{module_path}",
            f"import src.{module_path}",
            f".{file_stem} import",
        ]
        
        found_import = False
        for pattern in import_patterns:
            if pattern in all_content:
                found_import = True
                break
        
        if not found_import:
            potentially_unused.append(str(rel_path))
    
    for unused in potentially_unused[:10]:  # Show first 10
        print(f"   {unused}")
    
    # 6. Export functionality usage
    print("\n6. EXPORT FUNCTIONALITY:")
    export_files = list((src_dir / "features" / "export").glob("*.py"))
    for export_file in export_files:
        if "base_exporter" in str(export_file):
            continue
        rel_path = export_file.relative_to(src_dir)
        class_name = export_file.stem.replace('_', '').title() + "Exporter"
        
        if class_name in all_content:
            print(f"   {rel_path} - USED")
        else:
            print(f"   {rel_path} - NOT USED")
    
    print("\n" + "="*80)
    print("SUMMARY RECOMMENDATIONS")
    print("="*80)
    
    print("FILES TO CONSIDER REMOVING:")
    print("1. handlers_vision.py - has import errors and is commented out in main.py")
    print("2. Most files in features/export/ - only used in handlers_export.py")
    print("3. features/ai_scenarios/scenario_generator.py - superseded by vision_analysis version")
    print("4. Files that are never imported (see list above)")
    
    print("\nFILES TO FIX:")
    print("1. handlers_vision.py - fix imports or remove")
    print("2. main.py - uncomment vision router if needed")

if __name__ == "__main__":
    analyze_simple()